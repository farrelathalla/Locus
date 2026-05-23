import requests
from typing import Optional

NCBI_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
TIMEOUT = 10


def query_clinvar(gene: str, position: Optional[int] = None, max_results: int = 5) -> list[dict]:
    if not gene:
        return []

    term = f"{gene}[gene] AND single_nucleotide_variant[Type]"
    if position:
        term += f" AND {position}[Position]"

    try:
        r = requests.get(
            f"{NCBI_BASE}/esearch.fcgi",
            params={"db": "clinvar", "term": term, "retmax": max_results, "retmode": "json"},
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        ids = r.json().get("esearchresult", {}).get("idlist", [])

        if not ids:
            return []

        r2 = requests.get(
            f"{NCBI_BASE}/esummary.fcgi",
            params={"db": "clinvar", "id": ",".join(ids), "retmode": "json"},
            timeout=TIMEOUT,
        )
        r2.raise_for_status()
        result = r2.json().get("result", {})

        entries = []
        for uid in ids:
            if uid in result:
                entry = result[uid]
                gene_list = entry.get("genes", [{}])
                entries.append(
                    {
                        "id": uid,
                        "title": entry.get("title", ""),
                        "clinical_significance": entry.get("clinical_significance", {}).get("description", ""),
                        "gene": gene_list[0].get("symbol", "") if gene_list else "",
                        "variant_type": entry.get("obj_type", ""),
                        "review_status": entry.get("review_status", ""),
                    }
                )
        return entries

    except Exception as exc:
        return [{"error": str(exc)}]
