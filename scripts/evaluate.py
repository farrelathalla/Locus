import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import torch
from torch.utils.data import DataLoader
from datasets import load_dataset
from sklearn.metrics import (
    classification_report, confusion_matrix, roc_auc_score, f1_score, accuracy_score,
)
from tqdm import tqdm
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import json

from src.data.dataset import DNAVariantDataset
from src.models.classifier import DNAVariantClassifier
from src.config import DNABERT_MODEL, MAX_SEQ_LENGTH, TEST_SIZE, BATCH_SIZE, MODEL_DIR, RESULTS_DIR


def evaluate(model_path: str | None = None):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    if model_path is None:
        model_path = str(MODEL_DIR / "dnabert2_finetuned.pt")

    print("Memuat model...")
    model = DNAVariantClassifier(DNABERT_MODEL, num_classes=2).to(device)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.eval()

    print("Memuat dataset test (InstaDeepAI ClinVar)...")
    raw = load_dataset(
        "InstaDeepAI/genomics-long-range-benchmark",
        task_name="variant_effect_pathogenic_clinvar",
        sequence_length=MAX_SEQ_LENGTH,
        trust_remote_code=True,
    )
    test_data = raw["test"].shuffle(seed=42).select(range(min(TEST_SIZE, len(raw["test"]))))
    test_ds = DNAVariantDataset(test_data, DNABERT_MODEL, MAX_SEQ_LENGTH)
    test_loader = DataLoader(test_ds, batch_size=BATCH_SIZE, num_workers=4, pin_memory=True)

    all_preds, all_labels, all_probs = [], [], []
    with torch.no_grad():
        for batch in tqdm(test_loader, desc="Evaluasi"):
            alt_ids  = batch["alt_input_ids"].to(device)
            alt_mask = batch["alt_attention_mask"].to(device)
            ref_ids  = batch["ref_input_ids"].to(device)
            ref_mask = batch["ref_attention_mask"].to(device)
            labels   = batch["label"].to(device)
            logits = model(alt_ids, alt_mask, ref_ids, ref_mask)
            probs = torch.softmax(logits, dim=-1).cpu().numpy()
            preds = np.argmax(probs, axis=-1)
            all_preds.extend(preds)
            all_labels.extend(labels.cpu().numpy())
            all_probs.extend(probs)

    all_probs = np.array(all_probs)
    label_names = ["Benign", "Pathogenic"]

    acc = accuracy_score(all_labels, all_preds)
    f1_macro = f1_score(all_labels, all_preds, average="macro", zero_division=0)

    try:
        auc = roc_auc_score(all_labels, all_probs[:, 1])  # biner: prob kelas 1
    except Exception:
        auc = float("nan")

    metrics = {"accuracy": float(acc), "f1_macro": float(f1_macro), "auc_roc": float(auc)}
    print(f"\nAccuracy: {acc:.4f} | F1 Macro: {f1_macro:.4f} | AUC-ROC: {auc:.4f}")
    print("\n" + classification_report(all_labels, all_preds, target_names=label_names))

    metrics_path = RESULTS_DIR / "metrics" / "eval_metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"Metrik disimpan: {metrics_path}")

    cm = confusion_matrix(all_labels, all_preds)
    fig, ax = plt.subplots(figsize=(7, 5))
    sns.heatmap(cm, annot=True, fmt="d", xticklabels=label_names, yticklabels=label_names,
                cmap="Blues", ax=ax)
    ax.set_xlabel("Prediksi")
    ax.set_ylabel("Label Aktual")
    ax.set_title("Confusion Matrix - DNABERT-2 Classifier")
    cm_path = RESULTS_DIR / "metrics" / "confusion_matrix.png"
    fig.savefig(cm_path, dpi=150, bbox_inches="tight")
    print(f"Confusion matrix disimpan: {cm_path}")
    plt.close(fig)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default=None, help="Path ke file .pt model")
    args = parser.parse_args()
    evaluate(args.model)
