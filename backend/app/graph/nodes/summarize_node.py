import logging
from app.ollama.summarizer import summarize
from app.graph.state import ResearchState
from app.core.config import settings

logger = logging.getLogger(__name__)

async def summarize_node(state: ResearchState) -> dict:
    query = state.get("query")
    model = state.get("model", settings.OLLAMA_MODEL)
    compressed_findings = state.get("compressed_findings", "")

    logger.info(f"Summarize Node: Running summarizer for query '{query}'")

    # Wrap the compressed findings into the structure expected by the original summarizer.py
    # to avoid modifying the original summarizer file.
    search_results_wrapper = [
        {
            "title": "Derlenmiş Araştırma Bulguları",
            "content": compressed_findings
        }
    ]

    summary = await summarize(
        query=query,
        search_results=search_results_wrapper,
        model=model
    )

    return {
        "status": "done",
        "summary": summary
    }
