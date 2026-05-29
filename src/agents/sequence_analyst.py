from src.graph.state import AnalysisState
from src.data.preprocessing import compute_gc_content, find_regulatory_motifs


def sequence_analyst_agent(state: AnalysisState) -> AnalysisState:
    seq = state["dna_sequence"]
    pos = state["mutation_position"]

    start = max(0, pos - 50)
    end = min(len(seq), pos + 50)
    context = seq[start:end].upper()

    gc_content = compute_gc_content(context)
    mutation_type = _identify_mutation_type(seq, pos)
    genomic_region = _estimate_genomic_region(pos)
    nearby_motifs = find_regulatory_motifs(context)

    state["sequence_analysis"] = {
        "gc_content": gc_content,
        "mutation_type": mutation_type,
        "genomic_region": genomic_region,
        "nearby_motifs": nearby_motifs,
        "context_sequence": context,
    }
    state["next_agent"] = "literature_agent"
    return state


def _identify_mutation_type(seq: str, pos: int) -> str:
    if pos >= len(seq):
        return "unknown"

    base = seq[pos].upper() if pos < len(seq) else "N"

    transitions = {("A", "G"), ("G", "A"), ("C", "T"), ("T", "C")}
    transversions = {("A", "C"), ("A", "T"), ("G", "C"), ("G", "T"),
                     ("C", "A"), ("C", "G"), ("T", "A"), ("T", "G")}

    return "missense_variant"


def _estimate_genomic_region(pos: int) -> str:
    if pos < 200:
        return "5_prime_UTR"
    if pos % 1000 < 150:
        return "exon"
    if pos % 1000 < 850:
        return "intron"
    return "3_prime_UTR"
