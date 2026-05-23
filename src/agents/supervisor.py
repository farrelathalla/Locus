from src.config import PRODUCTION, LLM_MODEL, ANTHROPIC_API_KEY, GROQ_API_KEY
from src.graph.state import AnalysisState


def _call_llm(prompt: str) -> str:
    if PRODUCTION:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        msg = client.messages.create(
            model=LLM_MODEL,
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text
    else:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        resp = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.1,
        )
        return resp.choices[0].message.content


def supervisor_agent(state: AnalysisState) -> AnalysisState:
    ml_label = state.get("ml_label", "Unknown")
    ml_conf = (state.get("ml_confidence") or 0) * 100

    clinvar_entries = state.get("clinvar_entries") or []
    clinvar_sig = next(
        (e.get("clinical_significance", "") for e in clinvar_entries if "error" not in e and e.get("clinical_significance")),
        None,
    )

    if clinvar_sig:
        prompt = f"""Evaluasi singkat konsistensi data varian DNA ini:
- Prediksi model ML: {ml_label} (confidence {ml_conf:.0f}%)
- Status ClinVar yang ditemukan: {clinvar_sig}

Apakah ada inkonsistensi yang perlu dicatat klinisi? Jawab dalam 1-2 kalimat Bahasa Indonesia, formal.
Mulai jawaban dengan kata KONSISTEN atau PERLU PERHATIAN."""

        try:
            note = _call_llm(prompt).strip()
        except Exception as exc:
            note = f"Validasi supervisor tidak tersedia: {exc}"
    else:
        note = "Tidak ada data ClinVar untuk validasi silang. Interpretasi didasarkan pada prediksi model dan analisis sekuens."

    state["supervisor_note"] = note
    state["next_agent"] = "report_synthesizer"
    return state
