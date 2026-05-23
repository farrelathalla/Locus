import requests
from src.config import TAVILY_API_KEY

TAVILY_URL = "https://api.tavily.com/search"
TIMEOUT = 15


def query_tavily(gene: str, max_results: int = 3) -> list[dict]:
    """Search web for recent clinical literature about a gene variant using Tavily."""
    if not gene or not TAVILY_API_KEY:
        return []

    query = f"{gene} gene variant pathogenicity clinical significance genomics"

    try:
        resp = requests.post(
            TAVILY_URL,
            json={
                "api_key": TAVILY_API_KEY,
                "query": query,
                "search_depth": "basic",
                "max_results": max_results,
                "include_domains": [
                    "ncbi.nlm.nih.gov",
                    "clinvar.ncbi.nlm.nih.gov",
                    "pubmed.ncbi.nlm.nih.gov",
                    "omim.org",
                    "gnomad.broadinstitute.org",
                    "nature.com",
                    "nejm.org",
                    "jamanetwork.com",
                ],
            },
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
        return [
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "content": r.get("content", "")[:500],
                "score": r.get("score", 0),
            }
            for r in results
        ]
    except Exception as exc:
        return [{"error": str(exc)}]
