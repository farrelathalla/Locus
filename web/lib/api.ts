const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface AnalyzeRequest {
  dna_sequence: string;
  ref_sequence: string;
  mutation_position: number;
  gene_name?: string;
}

export interface MLPrediction {
  label: "Pathogenic" | "Benign";
  confidence: number;
  probabilities: Record<string, number>;
}

export interface SequenceAnalysis {
  gc_content: number;
  mutation_type: string;
  genomic_region: string;
  nearby_motifs: string[];
  context_sequence: string;
}

export interface ClinvarEntry {
  id?: string;
  title?: string;
  clinical_significance?: string;
  gene?: string;
  variant_type?: string;
  review_status?: string;
  error?: string;
}

export interface PubmedRef {
  pmids?: string[];
  abstracts_text?: string;
  error?: string;
}

export interface TavilyResult {
  title?: string;
  url?: string;
  content?: string;
  score?: number;
  error?: string;
}

export interface AnalyzeResponse {
  gene_name: string | null;
  mutation_position: number;
  ml_prediction: MLPrediction;
  sequence_analysis: SequenceAnalysis | null;
  clinvar_entries: ClinvarEntry[] | null;
  pubmed_refs: PubmedRef[] | null;
  tavily_results: TavilyResult[] | null;
  supervisor_note: string | null;
  final_report: string | null;
  errors: string[];
}

export interface StatusResponse {
  production_mode: boolean;
  llm_provider: string;
  llm_model: string;
  mock_ml: boolean;
  model_loaded: boolean;
}

export async function analyzeVariant(req: AnalyzeRequest): Promise<AnalyzeResponse> {
  const res = await fetch(`${API_URL}/api/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });

  if (!res.ok) {
    const detail = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(detail.detail ?? "Analisis gagal");
  }

  return res.json();
}

export async function getStatus(): Promise<StatusResponse> {
  const res = await fetch(`${API_URL}/api/status`);
  if (!res.ok) throw new Error("Gagal mengambil status API");
  return res.json();
}
