import logging
from app.graph.state import ResearchState

logger = logging.getLogger(__name__)

def route_after_human_review(state: ResearchState) -> str:
    logger.info("Routing after human review: moving directly to search node")
    return "search"
