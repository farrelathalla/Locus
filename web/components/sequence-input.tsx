"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Loader2 } from "lucide-react";

const EXAMPLE = {
  gene_name: "BRCA1",
  dna_sequence:
    "ATGGATTTATCTGCTCTTCGCGTTGAAGAAGTACAAAATGTCATTAATGCTATGCAGAAAATCTTAGAG" +
    "TGTCCCATCTGTCTGGAGTTGATCAAGGAACCTGTCTCCACAAAGTGTGACCACATATTTTGCAAATTTT" +
    "GCATGCTGAAACTTCTCAACCAGAAGAAAGGGCCTTCACAGTGTCCTTTATGTAAGAATGATATAACCAA",
  ref_sequence:
    "ATGGATTTATCTGCTCTTCGCGTTGAAGAAGTACAAAATGTCATTGATGCTATGCAGAAAATCTTAGAG" +
    "TGTCCCATCTGTCTGGAGTTGATCAAGGAACCTGTCTCCACAAAGTGTGACCACATATTTTGCAAATTTT" +
    "GCATGCTGAAACTTCTCAACCAGAAGAAAGGGCCTTCACAGTGTCCTTTATGTAAGAATGATATAACCAA",
  mutation_position: 45,
};

interface Props {
  onResult: (data: unknown) => void;
  onError: (msg: string) => void;
}

export function SequenceInput({ onResult, onError }: Props) {
  const [gene, setGene] = useState("");
  const [sequence, setSequence] = useState("");
  const [refSequence, setRefSequence] = useState("");
  const [position, setPosition] = useState<string>("");
  const [loading, setLoading] = useState(false);

  function loadExample() {
    setGene(EXAMPLE.gene_name);
    setSequence(EXAMPLE.dna_sequence);
    setRefSequence(EXAMPLE.ref_sequence);
    setPosition(String(EXAMPLE.mutation_position));
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    const pos = parseInt(position, 10);

    if (!sequence.trim()) {
      onError("Masukkan sekuens DNA alt (dengan mutasi).");
      return;
    }
    if (!refSequence.trim()) {
      onError("Masukkan sekuens DNA ref (tanpa mutasi).");
      return;
    }
    if (isNaN(pos) || pos < 0) {
      onError("Posisi mutasi harus angka non-negatif.");
      return;
    }
    if (pos >= sequence.length) {
      onError(`Posisi mutasi (${pos}) melebihi panjang sekuens alt (${sequence.length}).`);
      return;
    }

    setLoading(true);
    onError("");

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
      const res = await fetch(`${apiUrl}/api/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          dna_sequence: sequence.trim().toUpperCase(),
          ref_sequence: refSequence.trim().toUpperCase(),
          mutation_position: pos,
          gene_name: gene.trim() || undefined,
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail ?? "Analisis gagal");
      }

      onResult(await res.json());
    } catch (err: unknown) {
      onError(err instanceof Error ? err.message : "Terjadi kesalahan tak terduga.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-semibold">Input Varian</CardTitle>
        <CardDescription>
          Masukkan sekuens DNA dan posisi mutasi yang ingin dianalisis.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={submit} className="space-y-4">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label htmlFor="gene">Nama Gen (opsional)</Label>
              <Input
                id="gene"
                placeholder="Contoh: BRCA1, TP53"
                value={gene}
                onChange={(e) => setGene(e.target.value)}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="position">Posisi Mutasi (0-indexed)</Label>
              <Input
                id="position"
                type="number"
                placeholder="Contoh: 45"
                min={0}
                value={position}
                onChange={(e) => setPosition(e.target.value)}
                required
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="sequence">Sekuens DNA Alt — dengan mutasi</Label>
            <Textarea
              id="sequence"
              placeholder="Contoh: ATGGATTTATCTGCTCTTCGCGTT..."
              className="font-mono-dna h-28 resize-y text-xs"
              value={sequence}
              onChange={(e) => setSequence(e.target.value)}
              required
              spellCheck={false}
            />
            <p className="text-xs text-muted-foreground">
              Gunakan karakter A, T, G, C, N. Panjang:{" "}
              <span className="font-mono">{sequence.length}</span> basa.
            </p>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="ref-sequence">Sekuens DNA Ref — tanpa mutasi</Label>
            <Textarea
              id="ref-sequence"
              placeholder="Contoh: ATGGATTTATCTGCTCTTCGCGTT... (sekuens referensi)"
              className="font-mono-dna h-28 resize-y text-xs"
              value={refSequence}
              onChange={(e) => setRefSequence(e.target.value)}
              required
              spellCheck={false}
            />
            <p className="text-xs text-muted-foreground">
              Gunakan karakter A, T, G, C, N. Panjang:{" "}
              <span className="font-mono">{refSequence.length}</span> basa.
            </p>
          </div>

          <div className="flex items-center gap-3 pt-1">
            <Button type="submit" disabled={loading} size="sm">
              {loading && <Loader2 className="mr-2 h-3.5 w-3.5 animate-spin" />}
              {loading ? "Menganalisis..." : "Analisis"}
            </Button>
            <Button type="button" variant="ghost" size="sm" onClick={loadExample}>
              Muat Contoh BRCA1
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
