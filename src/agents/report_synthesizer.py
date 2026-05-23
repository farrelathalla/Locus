from src.config import PRODUCTION, LLM_MODEL, ANTHROPIC_API_KEY, GROQ_API_KEY
from src.graph.state import AnalysisState


def _call_llm(prompt: str) -> str:
    if PRODUCTION:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        msg = client.messages.create(
            model=LLM_MODEL,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text
    else:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        resp = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.3,
        )
        return resp.choices[0].message.content


def report_synthesizer_agent(state: AnalysisState) -> AnalysisState:
    seq = state["dna_sequence"]
    seq_display = seq[:80] + "..." if len(seq) > 80 else seq

    seq_analysis = state.get("sequence_analysis") or {}
    clinvar = state.get("clinvar_entries") or []
    pubmed = state.get("pubmed_refs") or []
    tavily = state.get("tavily_results") or []
    probs = state.get("ml_probabilities") or {}
    supervisor_note = state.get("supervisor_note", "")

    clinvar_summary = "\n".join(
        f"- {e.get('title', 'N/A')} | Signifikansi: {e.get('clinical_significance', 'N/A')}"
        for e in clinvar
        if "error" not in e
    ) or "Tidak ada entri ClinVar yang relevan ditemukan."

    pubmed_summary = ""
    for ref in pubmed:
        if "error" not in ref:
            text = ref.get("abstracts_text", "")
            pubmed_summary = text[:1000] if text else ""
            break
    if not pubmed_summary:
        pubmed_summary = "Tidak ada referensi PubMed yang ditemukan."

    tavily_summary = "\n".join(
        f"- [{r.get('title', 'N/A')}]({r.get('url', '')}): {r.get('content', '')[:200]}"
        for r in tavily
        if "error" not in r
    ) or "Tidak ada hasil web search."

    motifs = ", ".join(seq_analysis.get("nearby_motifs") or []) or "Tidak ditemukan"

    prompt = f"""Anda adalah asisten genomik klinis yang membantu dokter dan peneliti menginterpretasi varian DNA.
Tulis laporan analisis varian dalam Bahasa Indonesia yang formal, informatif, dan dapat dipahami klinisi.
Jangan gunakan tanda hubung panjang (em dash). Jangan buat kalimat yang terdengar seperti AI.

=== DATA VARIAN ===
Gen: {state.get("gene_name") or "Tidak diketahui"}
Posisi mutasi: {state["mutation_position"]}
Sekuens DNA (cuplikan): {seq_display}

=== KLASIFIKASI DNABERT-2 ===
Label prediksi: {state.get("ml_label") or "N/A"}
Confidence: {(state.get("ml_confidence") or 0) * 100:.1f}%
Probabilitas: Benign={probs.get("Benign", 0):.3f} | Pathogenic={probs.get("Pathogenic", 0):.3f}

=== ANALISIS SEKUENS ===
GC content: {seq_analysis.get("gc_content", "N/A")}
Tipe mutasi: {seq_analysis.get("mutation_type", "N/A")}
Lokasi genomik (estimasi): {seq_analysis.get("genomic_region", "N/A")}
Motif regulatori terdeteksi: {motifs}

=== DATA CLINVAR ===
{clinvar_summary}

=== REFERENSI PUBMED ===
{pubmed_summary[:500]}

=== LITERATUR WEB (TAVILY SEARCH) ===
{tavily_summary}

=== CATATAN SUPERVISOR ===
{supervisor_note or "Tidak ada catatan."}

Tulis laporan dengan bagian-bagian berikut:

## Ringkasan Eksekutif
## Klasifikasi Patogenisitas
## Analisis Biologis
## Evidensi Literatur
## Interpretasi Klinis
## Rekomendasi
"""

    try:
        report_text = _call_llm(prompt)
    except Exception as exc:
        report_text = f"Gagal menghasilkan laporan otomatis: {exc}"

    state["final_report"] = report_text
    state["next_agent"] = "END"
    return state
