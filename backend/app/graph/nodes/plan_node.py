import logging
from app.ollama.planner import create_plan
from app.graph.state import ResearchState
from app.core.config import settings

logger = logging.getLogger(__name__)

async def plan_node(state: ResearchState) -> dict:
    query = state.get("query")
    model = state.get("model", settings.OLLAMA_MODEL)
    
    logger.info(f"Plan Node: Generating research topics for query: '{query}'")

    plan = await create_plan(query, model=model)
    
    return {
        "plan": plan,
        "status": "awaiting_human",
        "human_feedback": None,
        "approved_plan": None
    }
