from typing import TypedDict, List, Optional, Dict, Any


class AnalysisState(TypedDict):
    dna_sequence: str
    mutation_position: int
    gene_name: Optional[str]

    ml_label: Optional[str]
    ml_confidence: Optional[float]
    ml_probabilities: Optional[Dict[str, float]]

    sequence_analysis: Optional[Dict[str, Any]]
    clinvar_entries: Optional[List[Dict]]
    pubmed_refs: Optional[List[Dict]]
    tavily_results: Optional[List[Dict]]

    supervisor_note: Optional[str]
    final_report: Optional[str]

    next_agent: Optional[str]
    iteration_count: int
    errors: List[str]
