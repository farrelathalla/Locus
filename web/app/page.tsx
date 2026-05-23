"use client";

import { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { SequenceInput } from "@/components/sequence-input";
import { AnalysisResult } from "@/components/analysis-result";
import { SequenceAnalysisPanel } from "@/components/sequence-analysis-panel";
import { LiteraturePanel } from "@/components/literature-panel";
import { ClinicalReport } from "@/components/clinical-report";
import type { AnalyzeResponse } from "@/lib/api";

function ResultSkeleton() {
  return (
    <div className="space-y-3">
      <Skeleton className="h-32 w-full" />
      <Skeleton className="h-48 w-full" />
      <Skeleton className="h-64 w-full" />
    </div>
  );
}

export default function Home() {
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function handleResult(data: unknown) {
    setResult(data as AnalyzeResponse);
    setLoading(false);
  }

  function handleError(msg: string) {
    if (msg) {
      setError(msg);
      setLoading(false);
    } else {
      setError("");
      setLoading(true);
    }
  }

  return (
    <div className="space-y-6">
      <div className="max-w-2xl">
        <h2 className="text-lg font-semibold tracking-tight text-foreground">Analisis Patogenisitas Varian</h2>
        <p className="text-sm text-muted-foreground mt-1">
          Masukkan sekuens DNA dan posisi mutasi untuk mendapatkan klasifikasi otomatis dan laporan klinis berbasis AI.
        </p>
      </div>

      <SequenceInput
        onResult={(data) => {
          setLoading(false);
          handleResult(data);
        }}
        onError={(msg) => {
          if (msg === "") {
            setLoading(true);
            setResult(null);
          } else {
            setLoading(false);
            setError(msg);
          }
        }}
      />

      {error && (
        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {loading && <ResultSkeleton />}

      {result && !loading && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-foreground">
              Hasil Analisis
              {result.gene_name && (
                <span className="ml-2 font-mono text-muted-foreground font-normal">
                  {result.gene_name}
                </span>
              )}
            </h3>
            <span className="text-xs text-muted-foreground tabular-nums">
              Posisi {result.mutation_position}
            </span>
          </div>

          <AnalysisResult data={result} />

          <Tabs defaultValue="sequence" className="w-full">
            <TabsList className="w-full justify-start">
              <TabsTrigger value="sequence">Sekuens</TabsTrigger>
              <TabsTrigger value="literature">Literatur</TabsTrigger>
              <TabsTrigger value="report">Laporan Klinis</TabsTrigger>
            </TabsList>

            <TabsContent value="sequence" className="mt-3">
              {result.sequence_analysis ? (
                <SequenceAnalysisPanel data={result.sequence_analysis} />
              ) : (
                <p className="text-sm text-muted-foreground">Data analisis sekuens tidak tersedia.</p>
              )}
            </TabsContent>

            <TabsContent value="literature" className="mt-3">
              <LiteraturePanel
                clinvarEntries={result.clinvar_entries}
                pubmedRefs={result.pubmed_refs}
                tavilyResults={result.tavily_results}
              />
            </TabsContent>

            <TabsContent value="report" className="mt-3">
              {result.final_report ? (
                <ClinicalReport report={result.final_report} result={result} />
              ) : (
                <p className="text-sm text-muted-foreground">Laporan klinis tidak tersedia.</p>
              )}
            </TabsContent>
          </Tabs>
        </div>
      )}

      {!result && !loading && !error && (
        <div className="rounded-lg border border-dashed border-border bg-muted/20 py-16 text-center">
          <p className="text-sm text-muted-foreground">
            Hasil analisis akan ditampilkan di sini setelah Anda mengirim input.
          </p>
        </div>
      )}
    </div>
  );
}
