import logging
from app.graph.state import ResearchState

logger = logging.getLogger(__name__)

def human_review_node(state: ResearchState) -> dict:
    feedback = state.get("human_feedback")
    logger.info(f"Human Review Node: Executing with feedback '{feedback}'")
    
    # Update the status based on user decision when resuming
    if feedback in ("approved", "edit"):
        return {"status": "searching"}
    else:
        return {"status": "planning"}
