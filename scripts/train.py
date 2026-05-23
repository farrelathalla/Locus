import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import torch
from torch.utils.data import DataLoader
from torch.optim import AdamW
from transformers import get_linear_schedule_with_warmup
from datasets import load_dataset
from sklearn.metrics import f1_score, classification_report
from tqdm import tqdm
import numpy as np

from src.data.dataset import DNAVariantDataset
from src.models.classifier import DNAVariantClassifier
from src.config import (
    DNABERT_MODEL, MAX_SEQ_LENGTH,
    TRAIN_SIZE, TEST_SIZE, BATCH_SIZE, EPOCHS, LR,
    MODEL_DIR,
)


def train():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")
    if device.type == "cuda":
        print(f"GPU: {torch.cuda.get_device_name(0)}")

    print("Memuat dataset ClinVar (InstaDeepAI)...")
    raw = load_dataset(
        "InstaDeepAI/genomics-long-range-benchmark",
        task_name="variant_effect_pathogenic_clinvar",
        sequence_length=MAX_SEQ_LENGTH,
        trust_remote_code=True,
    )
    train_data = raw["train"].shuffle(seed=42).select(range(min(TRAIN_SIZE, len(raw["train"]))))
    test_data = raw["test"].shuffle(seed=42).select(range(min(TEST_SIZE, len(raw["test"]))))

    print("Membangun dataset dan dataloader...")
    train_ds = DNAVariantDataset(train_data, DNABERT_MODEL, MAX_SEQ_LENGTH)
    test_ds = DNAVariantDataset(test_data, DNABERT_MODEL, MAX_SEQ_LENGTH)

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True, num_workers=4, pin_memory=True)
    test_loader = DataLoader(test_ds, batch_size=BATCH_SIZE, num_workers=4, pin_memory=True)

    model = DNAVariantClassifier(DNABERT_MODEL, num_classes=2).to(device)

    label_array = np.array([item["label"] for item in train_data])
    class_counts = np.bincount(label_array, minlength=2).astype(float)
    class_weights_np = len(label_array) / (2 * class_counts)
    class_weights = torch.tensor(class_weights_np, dtype=torch.float32, device=device)
    print(f"Class weights: Benign={class_weights_np[0]:.3f}, Pathogenic={class_weights_np[1]:.3f}")
    criterion = torch.nn.CrossEntropyLoss(weight=class_weights)
    optimizer = AdamW(model.parameters(), lr=LR, weight_decay=0.01)

    total_steps = len(train_loader) * EPOCHS
    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=int(0.1 * total_steps),
        num_training_steps=total_steps,
    )

    for epoch in range(EPOCHS):
        if epoch < 2:
            model.freeze_encoder()
            mode_label = "classifier head only"
        else:
            model.unfreeze_encoder()
            mode_label = "full fine-tune"

        model.train()
        total_loss = 0.0
        all_preds, all_labels = [], []

        pbar = tqdm(train_loader, desc=f"Epoch {epoch+1}/{EPOCHS} [{mode_label}]")
        for batch in pbar:
            alt_ids   = batch["alt_input_ids"].to(device)
            alt_mask  = batch["alt_attention_mask"].to(device)
            ref_ids   = batch["ref_input_ids"].to(device)
            ref_mask  = batch["ref_attention_mask"].to(device)
            labels    = batch["label"].to(device)

            optimizer.zero_grad()
            logits = model(alt_ids, alt_mask, ref_ids, ref_mask)
            loss = criterion(logits, labels)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()

            total_loss += loss.item()
            preds = torch.argmax(logits, dim=-1).cpu().numpy()
            all_preds.extend(preds)
            all_labels.extend(labels.cpu().numpy())

            pbar.set_postfix({"loss": f"{loss.item():.4f}"})

        avg_loss = total_loss / len(train_loader)
        f1 = f1_score(all_labels, all_preds, average="macro", zero_division=0)
        print(f"  Train Loss: {avg_loss:.4f} | Train F1 (macro): {f1:.4f}")

    model.eval()
    all_preds, all_labels = [], []
    with torch.no_grad():
        for batch in tqdm(test_loader, desc="Evaluasi"):
            alt_ids  = batch["alt_input_ids"].to(device)
            alt_mask = batch["alt_attention_mask"].to(device)
            ref_ids  = batch["ref_input_ids"].to(device)
            ref_mask = batch["ref_attention_mask"].to(device)
            labels   = batch["label"].to(device)
            logits = model(alt_ids, alt_mask, ref_ids, ref_mask)
            preds = torch.argmax(logits, dim=-1).cpu().numpy()
            all_preds.extend(preds)
            all_labels.extend(labels.cpu().numpy())

    print("\n" + "=" * 55)
    print("Laporan Evaluasi")
    print("=" * 55)
    print(classification_report(all_labels, all_preds, target_names=["Benign", "Pathogenic"]))

    save_path = MODEL_DIR / "dnabert2_finetuned.pt"
    torch.save(model.state_dict(), save_path)
    print(f"Model disimpan: {save_path}")


if __name__ == "__main__":
    train()
