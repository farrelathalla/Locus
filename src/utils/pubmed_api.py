import requests

NCBI_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
TIMEOUT = 10


def query_pubmed(gene: str, max_results: int = 3) -> list[dict]:
    if not gene:
        return []

    term = f"{gene}[gene] AND pathogenicity[tiab] AND variant[tiab]"

    try:
        r = requests.get(
            f"{NCBI_BASE}/esearch.fcgi",
            params={
                "db": "pubmed",
                "term": term,
                "retmax": max_results,
                "retmode": "json",
                "sort": "relevance",
            },
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        ids = r.json().get("esearchresult", {}).get("idlist", [])

        if not ids:
            return []

        r2 = requests.get(
            f"{NCBI_BASE}/efetch.fcgi",
            params={"db": "pubmed", "id": ",".join(ids), "retmode": "text", "rettype": "abstract"},
            timeout=TIMEOUT,
        )
        r2.raise_for_status()

        return [{"pmids": ids, "abstracts_text": r2.text[:3000]}]

    except Exception as exc:
        return [{"error": str(exc)}]
