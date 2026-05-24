import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from contextlib import asynccontextmanager
from typing import Optional
import numpy as np
import torch

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from api.models import AnalyzeRequest, AnalyzeResponse, MLPrediction, StatusResponse
from src.config import (
    PRODUCTION, MOCK_ML, LLM_PROVIDER, LLM_MODEL,
    DNABERT_MODEL, MAX_SEQ_LENGTH, MODEL_DIR, API_HOST, API_PORT,
)
from src.graph.pipeline import run_full_pipeline

LABEL_NAMES = ["Benign", "Pathogenic"]
_model = None
_tokenizer = None
_device = None


def _load_model():
    global _model, _tokenizer, _device
    from transformers import AutoTokenizer
    from src.models.classifier import DNAVariantClassifier

    _device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model_path = MODEL_DIR / "dnabert2_finetuned.pt"

    if not model_path.exists():
        return False

    try:
        _tokenizer = AutoTokenizer.from_pretrained(DNABERT_MODEL, trust_remote_code=True)
        _model = DNAVariantClassifier(num_classes=2, hidden_dim=512).to(_device)
        _model.load_state_dict(torch.load(str(model_path), map_location=_device))
        _model.eval()
        return True
    except Exception as e:
        print(f"[ERROR] Gagal memuat model: {type(e).__name__}: {e}")
        return False


def _mock_predict(alt_sequence: str, ref_sequence: str) -> dict:
    import random
    random.seed(abs(hash(alt_sequence[:50])) % (2**31))
    raw = [random.random() for _ in range(2)]
    total = sum(raw)
    probs = [p / total for p in raw]
    idx = int(np.argmax(probs))
    return {
        "label": LABEL_NAMES[idx],
        "confidence": float(probs[idx]),
        "probabilities": {k: float(v) for k, v in zip(LABEL_NAMES, probs)},
    }


def _real_predict(alt_sequence: str, ref_sequence: str) -> dict:
    def _tok(seq: str):
        return _tokenizer(
            seq,
            max_length=MAX_SEQ_LENGTH,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )

    alt_enc = _tok(alt_sequence)
    ref_enc = _tok(ref_sequence)

    with torch.no_grad():
        logits = _model(
            alt_enc["input_ids"].to(_device),
            alt_enc["attention_mask"].to(_device),
            ref_enc["input_ids"].to(_device),
            ref_enc["attention_mask"].to(_device),
        )
        probs = torch.softmax(logits, dim=-1).cpu().numpy()[0]

    idx = int(np.argmax(probs))
    return {
        "label": LABEL_NAMES[idx],
        "confidence": float(probs[idx]),
        "probabilities": {k: float(v) for k, v in zip(LABEL_NAMES, probs)},
    }


model_loaded = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    global model_loaded
    if not MOCK_ML:
        model_loaded = _load_model()
        if model_loaded:
            print("Model DNABERT-2 berhasil dimuat.")
        else:
            print("Model belum tersedia - gunakan MOCK_ML=true atau latih model dahulu.")
    yield


app = FastAPI(
    title="DNA Mutation Pathogenicity Analyzer",
    description="API untuk analisis patogenisitas varian DNA menggunakan DNABERT-2 dan sistem multi-agent LLM",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/status", response_model=StatusResponse)
def status():
    return StatusResponse(
        production_mode=PRODUCTION,
        llm_provider=LLM_PROVIDER,
        llm_model=LLM_MODEL,
        mock_ml=MOCK_ML,
        model_loaded=model_loaded,
    )


@app.post("/api/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    if MOCK_ML or not model_loaded:
        ml_result = _mock_predict(req.dna_sequence, req.ref_sequence)
    else:
        try:
            ml_result = _real_predict(req.dna_sequence, req.ref_sequence)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"ML inference gagal: {exc}")

    try:
        final_state = run_full_pipeline(
            dna_sequence=req.dna_sequence,
            mutation_position=req.mutation_position,
            ml_label=ml_result["label"],
            ml_confidence=ml_result["confidence"],
            ml_probabilities=ml_result["probabilities"],
            gene_name=req.gene_name,
            ref_sequence=req.ref_sequence,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Pipeline gagal: {exc}")

    seq_analysis_raw = final_state.get("sequence_analysis")

    return AnalyzeResponse(
        gene_name=req.gene_name,
        mutation_position=req.mutation_position,
        ml_prediction=MLPrediction(**ml_result),
        sequence_analysis=seq_analysis_raw,
        clinvar_entries=final_state.get("clinvar_entries"),
        pubmed_refs=final_state.get("pubmed_refs"),
        tavily_results=final_state.get("tavily_results"),
        supervisor_note=final_state.get("supervisor_note"),
        final_report=final_state.get("final_report"),
        errors=final_state.get("errors", []),
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host=API_HOST, port=API_PORT, reload=True)
