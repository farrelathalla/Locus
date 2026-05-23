from src.graph.state import AnalysisState
from src.utils.clinvar_api import query_clinvar
from src.utils.pubmed_api import query_pubmed
from src.utils.tavily_search import query_tavily


def literature_agent(state: AnalysisState) -> AnalysisState:
    gene = state.get("gene_name") or ""
    position = state.get("mutation_position")

    try:
        clinvar_entries = query_clinvar(gene, position)
    except Exception as exc:
        clinvar_entries = [{"error": str(exc)}]
        state["errors"].append(f"ClinVar query failed: {exc}")

    try:
        pubmed_refs = query_pubmed(gene)
    except Exception as exc:
        pubmed_refs = [{"error": str(exc)}]
        state["errors"].append(f"PubMed query failed: {exc}")

    try:
        tavily_results = query_tavily(gene)
    except Exception as exc:
        tavily_results = [{"error": str(exc)}]
        state["errors"].append(f"Tavily search failed: {exc}")

    state["clinvar_entries"] = clinvar_entries
    state["pubmed_refs"] = pubmed_refs
    state["tavily_results"] = tavily_results
    state["next_agent"] = "supervisor"
    return state
