from langgraph.graph import StateGraph, END

from src.graph.state import AnalysisState
from src.agents.sequence_analyst import sequence_analyst_agent
from src.agents.literature import literature_agent
from src.agents.supervisor import supervisor_agent
from src.agents.report_synthesizer import report_synthesizer_agent


def build_pipeline() -> StateGraph:
    graph = StateGraph(AnalysisState)

    graph.add_node("sequence_analyst", sequence_analyst_agent)
    graph.add_node("literature_agent", literature_agent)
    graph.add_node("supervisor", supervisor_agent)
    graph.add_node("report_synthesizer", report_synthesizer_agent)

    graph.set_entry_point("sequence_analyst")
    graph.add_edge("sequence_analyst", "literature_agent")
    graph.add_edge("literature_agent", "supervisor")
    graph.add_edge("supervisor", "report_synthesizer")
    graph.add_edge("report_synthesizer", END)

    return graph.compile()


def run_full_pipeline(
    dna_sequence: str,
    mutation_position: int,
    ml_label: str,
    ml_confidence: float,
    ml_probabilities: dict,
    gene_name: str | None = None,
) -> dict:
    pipeline = build_pipeline()

    initial_state: AnalysisState = {
        "dna_sequence": dna_sequence,
        "mutation_position": mutation_position,
        "gene_name": gene_name,
        "ml_label": ml_label,
        "ml_confidence": ml_confidence,
        "ml_probabilities": ml_probabilities,
        "sequence_analysis": None,
        "clinvar_entries": None,
        "pubmed_refs": None,
        "tavily_results": None,
        "supervisor_note": None,
        "final_report": None,
        "next_agent": "sequence_analyst",
        "iteration_count": 0,
        "errors": [],
    }

    return pipeline.invoke(initial_state)
