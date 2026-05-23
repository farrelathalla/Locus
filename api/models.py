from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any


class AnalyzeRequest(BaseModel):
    dna_sequence: str = Field(..., min_length=10, description="Sekuens DNA alt — dengan mutasi (min 10 basa)")
    ref_sequence: str = Field(..., min_length=10, description="Sekuens DNA ref — tanpa mutasi (min 10 basa)")
    mutation_position: int = Field(..., ge=0, description="Posisi mutasi (0-indexed)")
    gene_name: Optional[str] = Field(None, description="Nama gen (opsional, contoh: BRCA1)")


class MLPrediction(BaseModel):
    label: str
    confidence: float
    probabilities: Dict[str, float]


class SequenceAnalysis(BaseModel):
    gc_content: float
    mutation_type: str
    genomic_region: str
    nearby_motifs: List[str]
    context_sequence: str


class AnalyzeResponse(BaseModel):
    gene_name: Optional[str]
    mutation_position: int
    ml_prediction: MLPrediction
    sequence_analysis: Optional[SequenceAnalysis]
    clinvar_entries: Optional[List[Dict[str, Any]]]
    pubmed_refs: Optional[List[Dict[str, Any]]]
    tavily_results: Optional[List[Dict[str, Any]]]
    supervisor_note: Optional[str]
    final_report: Optional[str]
    errors: List[str]


class StatusResponse(BaseModel):
    production_mode: bool
    llm_provider: str
    llm_model: str
    mock_ml: bool
    model_loaded: bool
