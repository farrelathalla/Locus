import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { SequenceAnalysis } from "@/lib/api";

function regionColor(region: string) {
  if (region.includes("exon")) return "outline";
  if (region.includes("intron")) return "secondary";
  return "outline";
}

interface Props {
  data: SequenceAnalysis;
}

export function SequenceAnalysisPanel({ data }: Props) {
  const rows = [
    { label: "GC Content", value: `${(data.gc_content * 100).toFixed(1)}%` },
    { label: "Tipe Mutasi", value: data.mutation_type },
    { label: "Lokasi Genomik", value: data.genomic_region },
  ];

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-semibold">Analisis Sekuens</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <dl className="grid grid-cols-1 gap-2 text-sm sm:grid-cols-3">
          {rows.map(({ label, value }) => (
            <div key={label} className="rounded-md border border-border bg-muted/30 px-3 py-2">
              <dt className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">
                {label}
              </dt>
              <dd className="mt-0.5 font-medium text-foreground text-xs">{value}</dd>
            </div>
          ))}
        </dl>

        {data.nearby_motifs.length > 0 && (
          <div>
            <p className="text-xs font-medium text-muted-foreground mb-2 uppercase tracking-wide">
              Motif regulatori terdeteksi
            </p>
            <div className="flex flex-wrap gap-1.5">
              {data.nearby_motifs.map((m) => (
                <Badge key={m} variant="secondary" className="text-xs font-mono">
                  {m}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {data.context_sequence && (
          <div>
            <p className="text-xs font-medium text-muted-foreground mb-2 uppercase tracking-wide">
              Sekuens konteks (+/-50 bp)
            </p>
            <p className="font-mono-dna text-xs text-foreground break-all leading-relaxed rounded-md border border-border bg-muted/20 p-3">
              {data.context_sequence}
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
