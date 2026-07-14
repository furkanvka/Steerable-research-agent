import asyncio
import logging
from app.search.searxng import search
from app.graph.state import ResearchState
from app.core.exceptions import PipelineException

logger = logging.getLogger(__name__)

async def search_node(state: ResearchState) -> dict:
    # Use approved_plan if available, otherwise fallback to the generated plan
    topics = state.get("approved_plan") or state.get("plan") or []
    feedback = state.get("human_feedback") or ""
    
    logger.info(f"Search Node: Starting search for topics: {topics} (feedback: '{feedback}')")

    if not topics:
        logger.warning("Search Node: No topics to search.")
        return {
            "status": "searching",
            "findings": []
        }

    # Execute searches in parallel
    tasks = [search(topic) for topic in topics]
    
    try:
        results_lists = await asyncio.gather(*tasks)
    except PipelineException as e:
        logger.error(f"Search Node: Parallel search failed: {e.detail}")
        raise

    # Flatten the results
    collected_findings = []
    for results in results_lists:
        if results:
            collected_findings.extend(results)

    logger.info(f"Search Node: Successfully collected {len(collected_findings)} findings.")

    return {
        "status": "searching",
        "findings": collected_findings
    }
