import re
from typing import Optional


VALID_BASES = set("ACGTNacgtn")


def clean_sequence(seq: str) -> str:
    seq = seq.upper().strip()
    seq = re.sub(r"[^ACGTN]", "N", seq)
    return seq


def get_context_window(seq: str, position: int, window: int = 256) -> str:
    half = window // 2
    start = max(0, position - half)
    end = min(len(seq), position + half)
    return seq[start:end]


def compute_gc_content(seq: str) -> float:
    seq = seq.upper()
    if not seq:
        return 0.0
    gc = seq.count("G") + seq.count("C")
    return round(gc / len(seq), 4)


def find_regulatory_motifs(seq: str) -> list[str]:
    seq = seq.upper()
    motifs = []
    if "TATAAA" in seq or "TATATA" in seq:
        motifs.append("TATA_box")
    if "GCCGCC" in seq or "ACCATG" in seq:
        motifs.append("Kozak_sequence")
    if "AATAAA" in seq:
        motifs.append("poly-A_signal")
    if "GGAA" in seq or "GAAA" in seq:
        motifs.append("ETS_binding_site")
    if "CACGTG" in seq:
        motifs.append("E-box")
    if "CCAAT" in seq:
        motifs.append("CCAAT_box")
    return motifs


def normalize_label(raw: str) -> str:
    mapping = {
        "pathogenic": "Pathogenic",
        "likely_pathogenic": "Pathogenic",
        "pathogenic/likely_pathogenic": "Pathogenic",
        "benign": "Benign",
        "likely_benign": "Benign",
        "benign/likely_benign": "Benign",
        "uncertain_significance": "VUS",
        "vus": "VUS",
        "conflicting_interpretations_of_pathogenicity": "VUS",
    }
    return mapping.get(raw.lower().replace(" ", "_"), "VUS")
