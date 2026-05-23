import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import torch
import numpy as np
from transformers import AutoTokenizer

from src.models.classifier import DNAVariantClassifier
from src.graph.pipeline import run_full_pipeline
from src.config import DNABERT_MODEL, MAX_SEQ_LENGTH, MODEL_DIR, RESULTS_DIR, MOCK_ML

LABEL_NAMES = ["Benign", "Pathogenic"]

# Sekuens ALT (dengan mutasi A→C di posisi 45)
EXAMPLE_ALT_SEQUENCE = (
    "ATGGATTTATCTGCTCTTCGCGTTGAAGAAGTACAAAATGTCATTAATGCTATGCAGAAAATCTTAGAG"
    "TGTCCCATCTGTCTGGAGTTGATCAAGGAACCTGTCTCCACAAAGTGTGACCACATATTTTGCAAATTTT"
    "GCATGCTGAAACTTCTCAACCAGAAGAAAGGGCCTTCACAGTGTCCTTTATGTAAGAATGATATAACCAA"
    "AAAGAGCCTACAAGAAAGTACGAGATTTAGTCAACTTGTTGAAGAGCTATTGAAAATCATTTGTGCTTTT"
)

# Sekuens REF (tanpa mutasi, posisi 45 = G)
EXAMPLE_REF_SEQUENCE = (
    "ATGGATTTATCTGCTCTTCGCGTTGAAGAAGTACAAAATGTCATTGATGCTATGCAGAAAATCTTAGAG"
    "TGTCCCATCTGTCTGGAGTTGATCAAGGAACCTGTCTCCACAAAGTGTGACCACATATTTTGCAAATTTT"
    "GCATGCTGAAACTTCTCAACCAGAAGAAAGGGCCTTCACAGTGTCCTTTATGTAAGAATGATATAACCAA"
    "AAAGAGCCTACAAGAAAGTACGAGATTTAGTCAACTTGTTGAAGAGCTATTGAAAATCATTTGTGCTTTT"
)


def mock_predict(alt_sequence: str, ref_sequence: str) -> dict:
    import random
    random.seed(len(alt_sequence))
    probs = [random.random() for _ in range(2)]
    total = sum(probs)
    probs = [p / total for p in probs]
    idx = np.argmax(probs)
    return {
        "label": LABEL_NAMES[idx],
        "confidence": float(probs[idx]),
        "probabilities": {k: float(v) for k, v in zip(LABEL_NAMES, probs)},
    }


def predict_variant(model, tokenizer, alt_sequence: str, ref_sequence: str, device) -> dict:
    model.eval()

    def _tok(seq: str):
        enc = tokenizer(
            seq,
            max_length=MAX_SEQ_LENGTH,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )
        return enc["input_ids"].to(device), enc["attention_mask"].to(device)

    alt_ids, alt_mask = _tok(alt_sequence)
    ref_ids, ref_mask = _tok(ref_sequence)

    with torch.no_grad():
        logits = model(alt_ids, alt_mask, ref_ids, ref_mask)
        probs = torch.softmax(logits, dim=-1).cpu().numpy()[0]

    idx = int(np.argmax(probs))
    return {
        "label": LABEL_NAMES[idx],
        "confidence": float(probs[idx]),
        "probabilities": {k: float(v) for k, v in zip(LABEL_NAMES, probs)},
    }


def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    if MOCK_ML:
        print("Mode MOCK_ML aktif - melewati load model DNABERT-2")
        ml_result = mock_predict(EXAMPLE_ALT_SEQUENCE, EXAMPLE_REF_SEQUENCE)
    else:
        model_path = MODEL_DIR / "dnabert2_finetuned.pt"
        if not model_path.exists():
            raise FileNotFoundError(f"Model tidak ditemukan di {model_path}. Jalankan scripts/train.py dahulu.")

        print("Memuat DNABERT-2 + classifier...")
        tokenizer = AutoTokenizer.from_pretrained(DNABERT_MODEL, trust_remote_code=True)
        model = DNAVariantClassifier(num_classes=2, hidden_dim=512).to(device)
        model.load_state_dict(torch.load(str(model_path), map_location=device))
        ml_result = predict_variant(model, tokenizer, EXAMPLE_ALT_SEQUENCE, EXAMPLE_REF_SEQUENCE, device)

    print("\n" + "=" * 55)
    print("ML Inference (DNABERT-2)")
    print("=" * 55)
    print(f"Label     : {ml_result['label']}")
    print(f"Confidence: {ml_result['confidence']*100:.1f}%")
    print(f"Probs     : {ml_result['probabilities']}")

    print("\n" + "=" * 55)
    print("Menjalankan LangGraph Multi-Agent Pipeline")
    print("=" * 55)

    final_state = run_full_pipeline(
        dna_sequence=EXAMPLE_ALT_SEQUENCE,
        mutation_position=45,
        ml_label=ml_result["label"],
        ml_confidence=ml_result["confidence"],
        ml_probabilities=ml_result["probabilities"],
        gene_name="BRCA1",
    )

    print("\n" + "=" * 55)
    print("Laporan Klinis Final")
    print("=" * 55)
    print(final_state["final_report"])

    report_path = RESULTS_DIR / "reports" / "variant_report.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(final_state["final_report"] or "")
    print(f"\nLaporan disimpan: {report_path}")

    if final_state.get("errors"):
        print("\nCatatan error pipeline:")
        for err in final_state["errors"]:
            print(f"  - {err}")


if __name__ == "__main__":
    main()
