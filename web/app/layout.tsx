import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import "streamdown/styles.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "DNA Pathogenicity Analyzer",
  description:
    "Analisis patogenisitas varian DNA berbasis DNABERT-2 dan sistem multi-agent LLM",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="id">
      <body
        className={`${inter.className} min-h-screen bg-background antialiased`}
      >
        <header className="border-b border-border bg-card">
          <div className="mx-auto max-w-6xl px-6 py-4">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-base font-semibold tracking-tight text-foreground">
                  DNA Pathogenicity Analyzer
                </h1>
                <p className="text-xs text-muted-foreground mt-0.5">
                  DNABERT-2 + Multi-Agent LLM untuk interpretasi varian klinis
                </p>
              </div>
              <StatusBadge />
            </div>
          </div>
        </header>
        <main className="mx-auto max-w-6xl px-6 py-8">{children}</main>
        <footer className="border-t border-border mt-16">
          <div className="mx-auto max-w-6xl px-6 py-4 text-xs text-muted-foreground">
            IF3211 Domain-Specific Computation — Hanya untuk keperluan
            penelitian dan edukasi.
          </div>
        </footer>
      </body>
    </html>
  );
}

async function StatusBadge() {
  return (
    <div className="flex items-center gap-2">
      <span className="inline-flex items-center gap-1.5 rounded-md border border-border bg-secondary px-2 py-1 text-xs text-muted-foreground">
        <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
        API
      </span>
    </div>
  );
}
