# Locus — DNA Variant Pathogenicity Analyzer

Sistem end-to-end untuk mengklasifikasi patogenisitas varian DNA menggunakan genomic language model dan pipeline multi-agent LLM.

Dibangun untuk mata kuliah **IF3211 Domain-Specific Computation**, Institut Teknologi Bandung.

| NIM | Nama | Kontribusi |
| --- | ---- | ---------- |
| 13523062 | Aliya Husna Fayyaza | ML model, training pipeline, evaluasi, koordinasi |
| 13523113 | Kefas Kurnia Jonathan | Backend fixes, LangGraph pipeline, FastAPI |
| 13523118 | Farrel Athalla Putra | System ideation and design, frontend, integration testing, PDF export |

---

## Gambaran Sistem

Setiap manusia memiliki jutaan varian genetik dibandingkan genom referensi. Mengklasifikasikan apakah suatu varian bersifat patogenik atau benign secara manual membutuhkan waktu lama dan keahlian mendalam. Sistem ini mengotomasi proses tersebut.

**Komponen ML:** DNABERT-2 (117M parameter) yang di-fine-tune pada dataset ClinVar. Model menerima dua sekuens (referensi + alternatif) dan menghasilkan prediksi biner: **Benign** atau **Pathogenic**.

**Komponen Multi-Agent:** Pipeline LangGraph empat node yang menganalisis sekuens, mencari literatur klinis, memvalidasi konsistensi, lalu menghasilkan laporan klinis terstruktur.

```
Input: Sekuens ALT (dengan mutasi) + Sekuens REF (referensi) + posisi mutasi
              |
        DNABERT-2 Encoder
         /           \
   mean_pool(alt)  mean_pool(ref)
         \           /
       diff_emb = alt - ref  ← 768-dim
              |
    Classification Head → Benign / Pathogenic + confidence
              |
       LangGraph Pipeline
         ├── Sequence Analyst   — GC content, motif regulatori, lokasi genomik
         ├── Literature Agent   — query ClinVar dan PubMed (NCBI E-utilities)
         ├── Supervisor Agent   — validasi konsistensi ML vs ClinVar via LLM
         └── Report Synthesizer — laporan klinis Bahasa Indonesia via LLM
              |
Output: Laporan Klinis Terstruktur
```

---

## Stack Teknologi

| Komponen               | Teknologi                                           |
| ---------------------- | --------------------------------------------------- |
| Genomic Language Model | DNABERT-2 (`zhihan1996/DNABERT-2-117M`)             |
| ML Framework           | PyTorch + HuggingFace Transformers                  |
| Agent Framework        | LangGraph                                           |
| LLM (development)      | Groq API (`llama-3.3-70b-versatile`)                |
| LLM (production)       | Anthropic Claude API (`claude-sonnet-4-6`)          |
| Web Search             | Tavily Search API (literatur klinis terkini)        |
| Backend API            | FastAPI                                             |
| Frontend               | Next.js 14 App Router + shadcn/ui                   |
| PDF Export             | jsPDF (standar ACMG/AMP 2015)                       |
| Dataset                | InstaDeepAI/genomics-long-range-benchmark (ClinVar) |

---

## Prasyarat

- Python 3.10+
- Node.js 18+
- API key [Groq](https://console.groq.com) (gratis) atau Anthropic (berbayar)
- GPU minimal 8 GB VRAM untuk training (tidak diperlukan untuk mode mock)

---

## Instalasi

### 1. Setup environment Python

```bash
conda create -n locus python=3.10
conda activate locus
pip install -r requirements.txt
```

### 2. Konfigurasi environment

```bash
copy .env.example .env
```

Edit `.env`:

```env
PRODUCTION=false        # false → Groq | true → Anthropic Claude
GROQ_API_KEY=gsk_...    # diperlukan jika PRODUCTION=false
# ANTHROPIC_API_KEY=sk-ant-...  # diperlukan jika PRODUCTION=true
TAVILY_API_KEY=tvly-... # opsional — aktifkan web search di tab Literatur

MOCK_ML=true            # true → skip model, pakai prediksi deterministik (untuk dev)
```

### 3. Install dependensi frontend

```bash
cd web && npm install && cd ..
```

---

## Menjalankan Aplikasi

### Windows

Dua pilihan script tersedia tergantung bagaimana Python terinstall:

| Script             | Kapan dipakai                                                     |
| ------------------ | ----------------------------------------------------------------- |
| `start_novenv.bat` | Python sudah ada di PATH global (conda, system Python, pyenv)     |
| `start.bat`        | Menggunakan virtual environment (`venv/`) di dalam folder project |

```bat
# Jika Python di PATH global (conda, system install, dll.)
start_novenv.bat

# Jika menggunakan venv di folder project
start.bat
```

Kedua script membuka dua terminal: API server (port 8000) dan web server (port 3000).

### Manual

> **PYTHONPATH:** uvicorn menggunakan `multiprocessing.spawn` di Windows untuk mode `--reload`, yang memulai subprocess baru tanpa mewarisi working directory. Tanpa `PYTHONPATH`, subprocess tidak bisa menemukan modul `api` dan akan crash dengan `ModuleNotFoundError: No module named 'api'`. Selalu set `PYTHONPATH` sebelum menjalankan uvicorn secara manual.

```bat
# Terminal 1 — API server (dari folder Locus/)
set PYTHONPATH=%CD%
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 — Web server
cd web && npm run dev
```

Akses:

- **Web:** http://localhost:3000
- **API Docs (Swagger):** http://localhost:8000/docs

---

## Penggunaan via Web

Form input memerlukan dua sekuens:

| Field             | Deskripsi                                                                |
| ----------------- | ------------------------------------------------------------------------ |
| **Sekuens ALT**   | Sekuens DNA _dengan_ mutasi (dari kolom `alt_forward_sequence` dataset)  |
| **Sekuens REF**   | Sekuens DNA referensi _tanpa_ mutasi (dari kolom `ref_forward_sequence`) |
| **Posisi Mutasi** | Indeks posisi mutasi di sekuens ALT (0-indexed)                          |
| **Nama Gen**      | Opsional, contoh: `BRCA1`, `TP53`                                        |

Klik **"Muat Contoh BRCA1"** untuk mengisi otomatis dengan pasangan sekuens contoh.

---

## Training Model

Disarankan download model yang telah disediakan.

### Opsi 1: Download Trained Model (Rekomendasi)

[Download dnabert2_finetuned.pt via Google Drive](https://drive.google.com/drive/folders/1ei9ulpXymL507Ht-ztsdrcRFIlUGxKV5?usp=sharing)

### Opsi 2: Kaggle

1. Upload `notebooks/fine-tune-notebook.ipynb` ke [kaggle.com/code](https://kaggle.com/code)
2. Aktifkan GPU: **Settings > Accelerator > GPU T4 x2 atau P100**
3. Jalankan semua cell (**Run All**)
4. Unduh model dari tab **Output**

File output di Kaggle:

```
/kaggle/working/models/
├── dnabert2_finetuned.pt      ← ini yang dipakai sistem
├── dnabert2_encoder_hf/       ← encoder format HuggingFace
├── metrics.json               ← accuracy, F1, AUC-ROC
├── training_config.json       ← konfigurasi + metodologi lengkap
├── learning_curve.png
├── confusion_matrix.png
└── class_distribution.png
```

5. Taruh `dnabert2_finetuned.pt` di folder `models/` (root project)
6. Set `MOCK_ML=false` di `.env`
7. Restart API server

### Opsi 3: Training lokal (butuh GPU)

```bash
python scripts/train.py
```

### Evaluasi model

```bash
python scripts/evaluate.py
# Output: results/metrics/eval_metrics.json + confusion_matrix.png
```

---

## Tavily Web Search

Jika `TAVILY_API_KEY` diisi di `.env`, sistem akan otomatis mencari literatur klinis terkini dari web untuk setiap analisis. Hasil muncul di tab **Literatur** bagian "Web Search (Tavily)" dan juga digunakan oleh LLM saat menyusun laporan klinis.

Domain yang diprioritaskan: `ncbi.nlm.nih.gov`, `omim.org`, `gnomad.broadinstitute.org`, `nature.com`, `nejm.org`, `jamanetwork.com`.

Daftar API key di [app.tavily.com](https://app.tavily.com) (tersedia plan gratis).

---

## Export PDF Laporan Klinis

Tombol **Export PDF** tersedia di tab Laporan Klinis. PDF dihasilkan langsung di browser (tanpa upload ke server) menggunakan `jsPDF`.

**Format mengikuti standar ACMG/AMP 2015** — _Standards and Guidelines for the Interpretation of Sequence Variants_ (Richards et al., Genetics in Medicine, 2015. doi:10.1038/gim.2015.30):

| Bagian                    | Konten                                     |
| ------------------------- | ------------------------------------------ |
| Informasi Spesimen        | Gen target, posisi mutasi, metode analisis |
| Klasifikasi Patogenisitas | Label DNABERT-2, confidence, probabilitas  |
| Analisis Sekuens          | GC content, tipe mutasi, motif regulatori  |
| Evidensi ClinVar          | Entri dan signifikansi klinis dari NCBI    |
| Referensi PubMed          | Abstrak literatur relevan                  |
| Literatur Web             | Hasil Tavily search (jika tersedia)        |
| Interpretasi Klinis       | Laporan naratif dari LLM                   |
| Disclaimer                | Peringatan penggunaan non-klinis           |

---

## Demo via Terminal

```bash
python scripts/run_pipeline.py
# Output: results/reports/variant_report.txt
```

---

## API Reference

### POST `/api/analyze`

**Request:**

```json
{
  "dna_sequence": "ATGGATTTATCTGCTCTTCGCGTTGAAGAAGTACAAAATGTCATTAATGCTATGCAG...",
  "ref_sequence": "ATGGATTTATCTGCTCTTCGCGTTGAAGAAGTACAAAATGTCATTGATGCTATGCAG...",
  "mutation_position": 45,
  "gene_name": "BRCA1"
}
```

`dna_sequence` = sekuens alt (dengan mutasi), `ref_sequence` = sekuens referensi (tanpa mutasi).

**Response:**

```json
{
  "gene_name": "BRCA1",
  "mutation_position": 45,
  "ml_prediction": {
    "label": "Pathogenic",
    "confidence": 0.87,
    "probabilities": { "Benign": 0.13, "Pathogenic": 0.87 }
  },
  "sequence_analysis": {
    "gc_content": 0.42,
    "mutation_type": "missense_variant",
    "genomic_region": "exon",
    "nearby_motifs": ["Kozak_sequence"],
    "context_sequence": "GCGTTGAAGAAGTACAAAAT..."
  },
  "clinvar_entries": [...],
  "pubmed_refs": [...],
  "supervisor_note": "KONSISTEN. Prediksi model sesuai dengan data ClinVar...",
  "final_report": "## Ringkasan Eksekutif\n...",
  "errors": []
}
```

### GET `/api/status`

```json
{
  "production_mode": false,
  "llm_provider": "groq",
  "llm_model": "llama-3.3-70b-versatile",
  "mock_ml": true,
  "model_loaded": false
}
```

### GET `/api/health`

```json
{ "status": "ok" }
```

---

## Arsitektur Model

**Strategi embedding (Feng et al., Nature Communications 2025):**

Untuk SNV (Single Nucleotide Variant) pada sekuens 512 bp, perbedaan hanya 1 nukleotida menghasilkan `alt_emb - ref_emb ≈ 0`. Model menggunakan sinyal diferensial ini sebagai representasi varian:

```
ref_forward_sequence → DNABERT-2 → mean_pool → ref_emb  [768]
alt_forward_sequence → DNABERT-2 → mean_pool → alt_emb  [768]
                                                    ↓
                              diff_emb = alt_emb - ref_emb  [768]
                                                    ↓
                            Linear(768 → 512) → ReLU → Dropout(0.1)
                                                    ↓
                                       Linear(512 → 2) → Benign / Pathogenic
```

**Training:**

- Fase 1 (1 epoch): Encoder dibekukan, hanya classifier head yang dilatih
- Fase 2 (5 epoch): Full fine-tuning seluruh model
- Loss: CrossEntropyLoss dengan class weights `[2.5, 1.0]` (Benign lebih diprioritaskan)
- Optimizer: AdamW, lr=2e-5, weight_decay=0.01

---

## Dataset

**InstaDeepAI/genomics-long-range-benchmark** — task `variant_effect_pathogenic_clinvar`

|                 |                                                            |
| --------------- | ---------------------------------------------------------- |
| Sumber          | HuggingFace Hub                                            |
| Asal data       | ClinVar (NIH) + gnomAD v3.1.2                              |
| Genome assembly | GRCh38                                                     |
| Train split     | ~38.634 sampel (kromosom 1–7, 9–22, X, Y)                  |
| Test split      | ~1.018 sampel (kromosom 8)                                 |
| Label           | `0` = Benign (gnomAD MAF > 5%), `1` = Pathogenic (ClinVar) |
| Kolom input     | `ref_forward_sequence`, `alt_forward_sequence`             |
| Panjang sekuens | 512 bp (default, dikonfigurasi saat load dataset)          |

---

## Struktur Kode

```
Locus/
├── src/
│   ├── config.py                   ← satu sumber env vars dan konstanta global
│   ├── data/
│   │   ├── dataset.py              ← DNAVariantDataset (PyTorch Dataset)
│   │   └── preprocessing.py        ← utilitas preprocessing sekuens
│   ├── models/
│   │   └── classifier.py           ← DNAVariantClassifier (DNABERT-2 + diff head)
│   ├── agents/
│   │   ├── sequence_analyst.py     ← GC content, motif, lokasi genomik
│   │   ├── literature.py           ← ClinVar + PubMed via NCBI E-utilities
│   │   ├── supervisor.py           ← validasi konsistensi via LLM
│   │   └── report_synthesizer.py   ← laporan klinis via LLM
│   ├── graph/
│   │   ├── state.py                ← AnalysisState TypedDict
│   │   └── pipeline.py             ← LangGraph StateGraph
│   └── utils/
│       ├── clinvar_api.py          ← NCBI E-utilities wrapper
│       ├── pubmed_api.py           ← PubMed API wrapper
│       └── tavily_search.py        ← Tavily web search wrapper
├── api/
│   ├── main.py                     ← FastAPI app + ML inference
│   └── models.py                   ← Pydantic request/response schemas
├── scripts/
│   ├── train.py                    ← training loop lokal
│   ├── evaluate.py                 ← evaluasi + confusion matrix
│   └── run_pipeline.py             ← demo end-to-end dari terminal
├── web/
│   ├── app/                        ← Next.js App Router
│   ├── components/
│   │   ├── ui/                     ← shadcn/ui components (ditulis manual)
│   │   ├── sequence-input.tsx      ← form input ALT + REF sequence
│   │   ├── analysis-result.tsx     ← ML prediction card + confidence bar
│   │   ├── sequence-analysis-panel.tsx
│   │   ├── literature-panel.tsx
│   │   └── clinical-report.tsx
│   └── lib/
│       ├── api.ts                  ← typed fetch wrappers ke FastAPI
│       └── utils.ts                ← cn() utility
├── .env.example
├── requirements.txt
├── start.bat             ← jalankan dengan venv
└── start_novenv.bat      ← jalankan tanpa venv (Python di PATH global)
```

---

## Referensi

1. Feng et al. (2025). Benchmarking DNA foundation models for genomic and genetic tasks. _Nature Communications_, 16, 10780. https://doi.org/10.1038/s41467-025-65823-8
2. Zhou et al. (2024). DNABERT-2: Efficient Foundation Model and Benchmark For Multi-Species Genome. _ICLR 2024_. https://arxiv.org/abs/2306.15006
3. Landrum et al. (2018). ClinVar: improving access to variant interpretations and supporting evidence. _Nucleic Acids Research_.

---

> Proyek akademis IF3211 Domain-Specific Computation, ITB. Tidak untuk penggunaan klinis.
