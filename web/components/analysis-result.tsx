"use client";

import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import type { AnalyzeResponse } from "@/lib/api";

function labelVariant(label: string) {
  if (label === "Pathogenic") return "pathogenic";
  if (label === "Benign") return "benign";
  return "vus";
}

function labelIndicator(label: string) {
  if (label === "Pathogenic") return "bg-red-500";
  if (label === "Benign") return "bg-emerald-500";
  return "bg-amber-500";
}

function progressColor(label: string) {
  if (label === "Pathogenic") return "[&>div]:bg-red-500";
  if (label === "Benign") return "[&>div]:bg-emerald-500";
  return "[&>div]:bg-amber-500";
}

function labelId(label: string) {
  if (label === "Pathogenic") return "Patogenik";
  if (label === "Benign") return "Jinak (Benign)";
  return "Signifikansi Tidak Pasti (VUS)";
}

interface Props {
  data: AnalyzeResponse;
}

export function AnalysisResult({ data }: Props) {
  const { ml_prediction } = data;
  const pct = Math.round(ml_prediction.confidence * 100);

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-semibold">Hasil Klasifikasi ML</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center gap-3">
          <span className={`h-2.5 w-2.5 flex-none rounded-full ${labelIndicator(ml_prediction.label)}`} />
          <span className="text-sm font-medium">{labelId(ml_prediction.label)}</span>
          <Badge variant={labelVariant(ml_prediction.label) as "pathogenic" | "benign" | "vus"}>
            {ml_prediction.label}
          </Badge>
        </div>

        <div className="space-y-1.5">
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>Confidence</span>
            <span className="tabular-nums">{pct}%</span>
          </div>
          <Progress
            value={pct}
            className={`h-1.5 ${progressColor(ml_prediction.label)}`}
          />
        </div>

        <Separator />

        <div className="space-y-2">
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            Probabilitas per kelas
          </p>
          <div className="grid grid-cols-3 gap-2">
            {Object.entries(ml_prediction.probabilities).map(([cls, prob]) => (
              <div key={cls} className="rounded-md border border-border bg-muted/40 p-2 text-center">
                <p className="text-[10px] text-muted-foreground">{cls}</p>
                <p className="text-sm font-semibold tabular-nums">{(prob * 100).toFixed(1)}%</p>
              </div>
            ))}
          </div>
        </div>

        {data.supervisor_note && (
          <>
            <Separator />
            <div className="rounded-md bg-muted/50 px-3 py-2.5">
              <p className="text-xs font-medium text-muted-foreground mb-1">Catatan Supervisor</p>
              <p className="text-xs text-foreground leading-relaxed">{data.supervisor_note}</p>
            </div>
          </>
        )}

        {data.errors.length > 0 && (
          <div className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2.5">
            <p className="text-xs font-medium text-amber-700 mb-1">Peringatan Pipeline</p>
            {data.errors.map((e, i) => (
              <p key={i} className="text-xs text-amber-600">
                {e}
              </p>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
