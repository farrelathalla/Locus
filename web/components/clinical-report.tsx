"use client";

import { useState } from "react";
import { Streamdown } from "streamdown";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Copy, Check, FileDown } from "lucide-react";
import type { AnalyzeResponse } from "@/lib/api";

interface Props {
  report: string;
  result?: AnalyzeResponse;
}

export function ClinicalReport({ report, result }: Props) {
  const [copied, setCopied] = useState(false);
  const [exporting, setExporting] = useState(false);

  async function copy() {
    await navigator.clipboard.writeText(report);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  async function exportPdf() {
    setExporting(true);
    try {
      const { jsPDF } = await import("jspdf");
      const doc = new jsPDF({ unit: "mm", format: "a4", orientation: "portrait" });

      const pageW = doc.internal.pageSize.getWidth();
      const pageH = doc.internal.pageSize.getHeight();
      const marginL = 20;
      const marginR = 20;
      const contentW = pageW - marginL - marginR;
      const footerY = pageH - 14; // top of footer area
      const maxContentY = footerY - 4; // content must stop before footer

      const now = new Date();
      const reportDate = now.toLocaleDateString("id-ID", {
        day: "2-digit", month: "long", year: "numeric",
      });
      const reportId = `LOCUS-${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, "0")}${String(now.getDate()).padStart(2, "0")}-${Math.random().toString(36).slice(2, 7).toUpperCase()}`;

      let y = 20;

      function checkPage(needed = 10) {
        if (y + needed > maxContentY) {
          doc.addPage();
          y = 20;
        }
      }

      // line height: jsPDF mm-per-line for a given font size
      function lineH(size: number) { return size * 0.4 + 1.5; }

      function writeLine(
        text: string,
        opts: { size?: number; bold?: boolean; color?: [number, number, number]; indent?: number } = {}
      ) {
        const { size = 9, bold = false, color = [30, 30, 30], indent = 0 } = opts;
        doc.setFontSize(size);
        doc.setFont("helvetica", bold ? "bold" : "normal");
        doc.setTextColor(...color);
        const lines = doc.splitTextToSize(text, contentW - indent);
        checkPage(lines.length * lineH(size));
        doc.text(lines, marginL + indent, y);
        y += lines.length * lineH(size);
      }

      function writeBlock(label: string, value: string) {
        writeLine(label, { size: 8, bold: true, color: [80, 80, 80] });
        writeLine(value || "—", { size: 9, indent: 3 });
        y += 1.5;
      }

      function sectionHeader(title: string) {
        checkPage(14);
        y += 3;
        doc.setFillColor(240, 240, 240);
        doc.rect(marginL, y - 3, contentW, 7, "F");
        writeLine(title, { size: 9, bold: true, color: [20, 20, 20] });
        y += 2;
      }

      // ── HEADER ──────────────────────────────────────────────────────────
      doc.setFillColor(24, 24, 27);
      doc.rect(0, 0, pageW, 28, "F");

      doc.setFontSize(14);
      doc.setFont("helvetica", "bold");
      doc.setTextColor(255, 255, 255);
      doc.text("LAPORAN INTERPRETASI VARIAN GENETIK", marginL, 12);

      doc.setFontSize(8);
      doc.setFont("helvetica", "normal");
      doc.setTextColor(180, 180, 180);
      doc.text("Standar: ACMG/AMP 2015 Variant Classification Guidelines", marginL, 18);
      doc.text("Richards et al., Genetics in Medicine, 2015. doi:10.1038/gim.2015.30", marginL, 23);
      doc.text(`ID: ${reportId}`, pageW - marginR - 60, 18);
      doc.text(`Tanggal: ${reportDate}`, pageW - marginR - 60, 23);

      y = 36;

      // ── SECTION 1: Informasi Spesimen ─────────────────────────────────
      sectionHeader("1. INFORMASI SPESIMEN DAN ANALISIS");
      writeBlock("Gen Target", result?.gene_name ?? "Tidak diketahui");
      writeBlock("Posisi Mutasi", `${result?.mutation_position ?? "-"} (0-indexed, GRCh38)`);
      writeBlock("Metode Analisis", "Genomic Language Model (DNABERT-2, 117M parameters) + LangGraph Multi-Agent Pipeline");
      writeBlock("Platform", "Locus DNA Variant Pathogenicity Analyzer — IF3211 Domain-Specific Computation, ITB");

      // ── SECTION 2: Klasifikasi ACMG ───────────────────────────────────
      sectionHeader("2. KLASIFIKASI PATOGENISITAS (ACMG/AMP 2015)");
      const label = result?.ml_prediction?.label ?? "N/A";
      const conf = result?.ml_prediction?.confidence
        ? `${(result.ml_prediction.confidence * 100).toFixed(1)}%`
        : "N/A";
      const pProb = result?.ml_prediction?.probabilities?.["Pathogenic"];
      const bProb = result?.ml_prediction?.probabilities?.["Benign"];

      checkPage(12);
      doc.setFontSize(13);
      doc.setFont("helvetica", "bold");
      doc.setTextColor(label === "Pathogenic" ? 185 : 22, label === "Pathogenic" ? 28 : 101, label === "Pathogenic" ? 28 : 52);
      doc.text(label.toUpperCase(), marginL, y);
      y += 7;

      writeLine(`Confidence model: ${conf}`, { size: 9 });
      if (pProb !== undefined && bProb !== undefined) {
        writeLine(
          `Probabilitas — Pathogenic: ${(pProb * 100).toFixed(1)}%  |  Benign: ${(bProb * 100).toFixed(1)}%`,
          { size: 9 }
        );
      }
      y += 2;
      writeLine(
        "Klasifikasi di atas dihasilkan oleh model DNABERT-2 yang dilatih pada dataset ClinVar (InstaDeepAI). " +
        "Hasil ini bersifat prediktif dan harus divalidasi oleh ahli genetika klinis bersertifikat sebelum " +
        "digunakan untuk pengambilan keputusan klinis.",
        { size: 8, color: [100, 100, 100] }
      );

      // ── SECTION 3: Analisis Sekuens ───────────────────────────────────
      sectionHeader("3. ANALISIS SEKUENS DAN KARAKTERISASI VARIAN");
      const sa = result?.sequence_analysis;
      if (sa) {
        writeBlock("GC Content (konteks ±50 bp)", `${typeof sa.gc_content === "number" ? (sa.gc_content * 100).toFixed(1) : sa.gc_content}%`);
        writeBlock("Tipe Mutasi (prediksi)", sa.mutation_type);
        writeBlock("Lokasi Genomik (estimasi)", sa.genomic_region);
        writeBlock("Motif Regulatori Terdeteksi", sa.nearby_motifs?.join(", ") || "Tidak ditemukan");
        writeBlock("Konteks Sekuens", sa.context_sequence ?? "—");
      } else {
        writeLine("Data analisis sekuens tidak tersedia.", { size: 9, color: [120, 120, 120] });
      }

      // ── SECTION 4: Evidensi ClinVar ────────────────────────────────────
      sectionHeader("4. EVIDENSI DATABASE (ClinVar / NCBI E-utilities)");
      const clinvar = (result?.clinvar_entries ?? []).filter(
        (e) => !e.error && e.clinical_significance
      );
      if (clinvar.length === 0) {
        writeLine("Tidak ada entri ClinVar dengan signifikansi klinis yang relevan ditemukan.", { size: 9, color: [120, 120, 120] });
      } else {
        clinvar.forEach((e, i) => {
          checkPage(18);
          writeLine(`[${i + 1}] ${e.title ?? "N/A"}`, { size: 9, bold: true });
          writeLine(`Signifikansi Klinis: ${e.clinical_significance}  |  Review Status: ${e.review_status ?? "N/A"}`, { size: 8, color: [80, 80, 80], indent: 4 });
          y += 1.5;
        });
      }

      // ── SECTION 5: Referensi PubMed ────────────────────────────────────
      sectionHeader("5. REFERENSI LITERATUR (PubMed / NCBI)");
      const pubmed = (result?.pubmed_refs ?? []).filter((r) => !r.error);
      if (pubmed.length === 0) {
        writeLine("Tidak ada referensi PubMed yang ditemukan.", { size: 9, color: [120, 120, 120] });
      } else {
        pubmed.forEach((ref) => {
          checkPage(20);
          if (ref.pmids) {
            writeLine(`PMID: ${ref.pmids.join(", ")}`, { size: 8, bold: true });
          }
          if (ref.abstracts_text) {
            const excerpt = ref.abstracts_text.slice(0, 600) + (ref.abstracts_text.length > 600 ? "..." : "");
            writeLine(excerpt, { size: 8, color: [60, 60, 60], indent: 3 });
          }
          y += 2;
        });
      }

      // ── SECTION 6: Web Search ─────────────────────────────────────────
      const tavily = (result?.tavily_results ?? []).filter((r) => !r.error);
      let nextSectionNum = 6;
      if (tavily.length > 0) {
        sectionHeader("6. LITERATUR WEB TERKINI (Web Search)");
        nextSectionNum = 7;
        tavily.forEach((r, i) => {
          checkPage(20);
          writeLine(`[${i + 1}] ${r.title ?? "N/A"}`, { size: 9, bold: true });
          if (r.url) writeLine(r.url, { size: 7, color: [80, 100, 160], indent: 3 });
          if (r.content) writeLine(r.content.slice(0, 300), { size: 8, color: [60, 60, 60], indent: 3 });
          y += 1.5;
        });
      }

      // ── SECTION: Laporan Klinis LLM ───────────────────────────────────
      sectionHeader(`${nextSectionNum}. INTERPRETASI KLINIS (Dihasilkan oleh LLM)`);

      function renderMdTable(tableLines: string[]) {
        // Parse rows, drop separator lines (|---|---|)
        const rows = tableLines
          .filter((l) => !/^[\s|:\-]+$/.test(l))
          .map((l) =>
            l.split("|")
              .slice(1, -1)
              .map((c) => c.trim())
          )
          .filter((r) => r.length > 0);
        if (rows.length === 0) return;

        const colCount = Math.max(...rows.map((r) => r.length));
        const colW = contentW / colCount;
        const rowH = 6.5;
        checkPage(rows.length * rowH + 4);

        rows.forEach((row, ri) => {
          const isHeader = ri === 0;
          if (isHeader) {
            doc.setFillColor(220, 220, 220);
          } else if (ri % 2 === 0) {
            doc.setFillColor(248, 248, 248);
          } else {
            doc.setFillColor(255, 255, 255);
          }
          doc.rect(marginL, y, contentW, rowH, "F");
          doc.setDrawColor(200, 200, 200);
          doc.setLineWidth(0.2);
          doc.rect(marginL, y, contentW, rowH, "S");

          row.forEach((cell, ci) => {
            // vertical divider between columns
            if (ci > 0) {
              doc.line(marginL + ci * colW, y, marginL + ci * colW, y + rowH);
            }
            doc.setFontSize(8);
            doc.setFont("helvetica", isHeader ? "bold" : "normal");
            doc.setTextColor(isHeader ? 20 : 40, isHeader ? 20 : 40, isHeader ? 20 : 40);
            // truncate cell text to fit column
            const maxCellW = colW - 4;
            const truncated = doc.splitTextToSize(cell, maxCellW)[0] ?? cell;
            doc.text(truncated, marginL + ci * colW + 2, y + rowH * 0.68);
          });
          y += rowH;
        });
        y += 3;
      }

      const reportLines = report.split("\n");
      let li = 0;
      while (li < reportLines.length) {
        const line = reportLines[li];

        // Markdown table — collect all consecutive pipe lines then render
        if (line.trimStart().startsWith("|")) {
          const tableLines: string[] = [];
          while (li < reportLines.length && reportLines[li].trimStart().startsWith("|")) {
            tableLines.push(reportLines[li]);
            li++;
          }
          renderMdTable(tableLines);
          continue;
        }

        // Horizontal rule
        if (/^-{3,}\s*$/.test(line.trim())) {
          checkPage(6);
          doc.setDrawColor(200, 200, 200);
          doc.setLineWidth(0.3);
          doc.line(marginL, y + 1, pageW - marginR, y + 1);
          y += 5;
          li++;
          continue;
        }

        if (line.startsWith("## ")) {
          checkPage(12);
          y += 2;
          writeLine(line.replace(/^##\s*/, ""), { size: 9, bold: true });
          y += 0.5;
        } else if (line.startsWith("### ")) {
          checkPage(10);
          writeLine(line.replace(/^###\s*/, ""), { size: 8.5, bold: true });
        } else if (line.trim()) {
          writeLine(line.replace(/\*\*/g, ""), { size: 8.5 });
        } else {
          y += 2.5;
        }
        li++;
      }

      // ── FOOTER (fixed position, no y mutation) ────────────────────────
      const totalPages = (doc.internal as unknown as { getNumberOfPages: () => number }).getNumberOfPages();
      for (let p = 1; p <= totalPages; p++) {
        doc.setPage(p);
        doc.setDrawColor(210, 210, 210);
        doc.setLineWidth(0.3);
        doc.line(marginL, footerY - 1, pageW - marginR, footerY - 1);
        doc.setFontSize(7);
        doc.setFont("helvetica", "normal");
        doc.setTextColor(150, 150, 150);
        doc.text(
          "PERHATIAN: Laporan ini dihasilkan sistem AI untuk penelitian dan edukasi. BUKAN pengganti konsultasi ahli genetika klinis bersertifikat.",
          marginL,
          footerY + 3,
          { maxWidth: contentW - 32 }
        );
        doc.text(
          `Hal. ${p} / ${totalPages}  |  ${reportId}`,
          pageW - marginR,
          footerY + 3,
          { align: "right" }
        );
      }

      doc.save(`locus-variant-report-${result?.gene_name ?? "unknown"}-${now.toISOString().slice(0, 10)}.pdf`);
    } catch (err) {
      console.error("PDF export failed:", err);
    } finally {
      setExporting(false);
    }
  }

  return (
    <Card>
      <CardHeader className="pb-3 flex-row items-center justify-between space-y-0">
        <div>
          <CardTitle className="text-sm font-semibold">Laporan Klinis</CardTitle>
          <p className="text-[10px] text-muted-foreground mt-0.5">Format standar ACMG/AMP 2015</p>
        </div>
        <div className="flex items-center gap-1.5">
          <Button variant="ghost" size="sm" className="h-7 px-2" onClick={copy}>
            {copied ? (
              <Check className="h-3.5 w-3.5 text-emerald-600" />
            ) : (
              <Copy className="h-3.5 w-3.5" />
            )}
            <span className="ml-1.5 text-xs">{copied ? "Tersalin" : "Salin"}</span>
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="h-7 px-2"
            onClick={exportPdf}
            disabled={exporting}
          >
            <FileDown className="h-3.5 w-3.5" />
            <span className="ml-1.5 text-xs">{exporting ? "Membuat PDF..." : "Export PDF"}</span>
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="
          text-sm text-foreground leading-relaxed
          [&_h1]:text-base [&_h1]:font-semibold [&_h1]:mt-4 [&_h1]:mb-2
          [&_h2]:text-xs [&_h2]:font-semibold [&_h2]:uppercase [&_h2]:tracking-wide
          [&_h2]:text-muted-foreground [&_h2]:border-b [&_h2]:border-border
          [&_h2]:pb-1 [&_h2]:mt-5 [&_h2]:mb-2
          [&_h3]:text-xs [&_h3]:font-semibold [&_h3]:mt-3 [&_h3]:mb-1
          [&_p]:mb-2 [&_p]:leading-relaxed
          [&_strong]:font-semibold
          [&_ul]:list-disc [&_ul]:pl-5 [&_ul]:mb-2
          [&_ol]:list-decimal [&_ol]:pl-5 [&_ol]:mb-2
          [&_li]:mb-0.5
          [&_blockquote]:border-l-2 [&_blockquote]:border-border [&_blockquote]:pl-3 [&_blockquote]:text-muted-foreground
        ">
          <Streamdown mode="static">{report}</Streamdown>
        </div>
      </CardContent>
    </Card>
  );
}
