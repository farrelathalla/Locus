import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import type { ClinvarEntry, PubmedRef, TavilyResult } from "@/lib/api";

function sigVariant(sig: string): "pathogenic" | "benign" | "vus" | "secondary" {
  const s = sig.toLowerCase();
  if (s.includes("pathogenic")) return "pathogenic";
  if (s.includes("benign")) return "benign";
  if (s.includes("uncertain")) return "vus";
  return "secondary";
}

interface Props {
  clinvarEntries: ClinvarEntry[] | null;
  pubmedRefs: PubmedRef[] | null;
  tavilyResults?: TavilyResult[] | null;
}

export function LiteraturePanel({ clinvarEntries, pubmedRefs, tavilyResults }: Props) {
  const validClinvar = (clinvarEntries ?? []).filter((e) => !e.error && e.clinical_significance);
  const errorClinvar = (clinvarEntries ?? []).filter((e) => e.error);
  const validPubmed = (pubmedRefs ?? []).filter((r) => !r.error);
  const validTavily = (tavilyResults ?? []).filter((r) => !r.error);

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-semibold">Evidensi Literatur</CardTitle>
      </CardHeader>
      <CardContent className="space-y-5">
        <section>
          <h4 className="text-xs font-medium uppercase tracking-wide text-muted-foreground mb-2">
            ClinVar ({validClinvar.length} entri)
          </h4>
          {validClinvar.length === 0 ? (
            <p className="text-xs text-muted-foreground">
              {errorClinvar.length > 0
                ? `Query ClinVar gagal: ${errorClinvar[0].error}`
                : "Tidak ada entri ClinVar dengan signifikansi klinis yang tersedia untuk gen ini."}
            </p>
          ) : (
            <div className="space-y-2">
              {validClinvar.map((entry, i) => (
                <div key={i} className="rounded-md border border-border bg-background p-3 space-y-1.5">
                  <p className="text-xs font-medium text-foreground leading-snug">{entry.title}</p>
                  <div className="flex flex-wrap items-center gap-2">
                    {entry.clinical_significance && (
                      <Badge variant={sigVariant(entry.clinical_significance)} className="text-[10px]">
                        {entry.clinical_significance}
                      </Badge>
                    )}
                    {entry.gene && (
                      <span className="text-[10px] text-muted-foreground font-mono">{entry.gene}</span>
                    )}
                    {entry.review_status && (
                      <span className="text-[10px] text-muted-foreground">{entry.review_status}</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        <Separator />

        <section>
          <h4 className="text-xs font-medium uppercase tracking-wide text-muted-foreground mb-2">
            PubMed
          </h4>
          {validPubmed.length === 0 ? (
            <p className="text-xs text-muted-foreground">
              Tidak ada referensi PubMed yang ditemukan.
            </p>
          ) : (
            <div className="space-y-3">
              {validPubmed.map((ref, i) => (
                <div key={i} className="space-y-1.5">
                  {ref.pmids && ref.pmids.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {ref.pmids.map((id) => (
                        <span key={id} className="font-mono text-[10px] text-muted-foreground bg-muted px-1.5 py-0.5 rounded">
                          PMID: {id}
                        </span>
                      ))}
                    </div>
                  )}
                  {ref.abstracts_text && (
                    <p className="text-xs text-foreground leading-relaxed line-clamp-6 whitespace-pre-line">
                      {ref.abstracts_text.slice(0, 800)}
                      {ref.abstracts_text.length > 800 ? "..." : ""}
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}
        </section>

        {tavilyResults !== undefined && (
          <>
            <Separator />
            <section>
              <h4 className="text-xs font-medium uppercase tracking-wide text-muted-foreground mb-2">
                Web Search
              </h4>
              {validTavily.length === 0 ? (
                <p className="text-xs text-muted-foreground">
                  {tavilyResults && tavilyResults.some((r) => r.error)
                    ? "Tavily search tidak tersedia (periksa TAVILY_API_KEY)."
                    : "Tidak ada hasil web search yang ditemukan."}
                </p>
              ) : (
                <div className="space-y-2">
                  {validTavily.map((r, i) => (
                    <div key={i} className="rounded-md border border-border bg-background p-3 space-y-1">
                      <a
                        href={r.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs font-medium text-foreground hover:underline leading-snug block"
                      >
                        {r.title}
                      </a>
                      {r.url && (
                        <p className="text-[10px] text-muted-foreground font-mono truncate">{r.url}</p>
                      )}
                      {r.content && (
                        <p className="text-xs text-muted-foreground leading-relaxed line-clamp-3">
                          {r.content}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </section>
          </>
        )}
      </CardContent>
    </Card>
  );
}
