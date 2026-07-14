import uuid
import logging
from fastapi import APIRouter, Request, HTTPException

from app.models.research import (
    ResearchRequest,
    ResearchStartResponse,
    ResearchStatusResponse,
    PlanApprovalRequest,
    ErrorResponse
)

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post(
    "/research/start",
    response_model=ResearchStartResponse,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    }
)
async def start_research(request: ResearchRequest, api_request: Request):
    try:
        session_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": session_id}}
        
        # Initialize graph state
        initial_state = {
            "query": request.query,
            "model": request.model,
            "findings": [],
            "status": "planning",
            "plan": [],
            "approved_plan": None,
            "human_feedback": None,
            "compressed_findings": None,
            "summary": None
        }
        
        await api_request.app.state.graph.aupdate_state(config, initial_state)
        
        # Build WebSocket URL
        scheme = "wss" if api_request.url.scheme == "https" else "ws"
        websocket_url = f"{scheme}://{api_request.url.netloc}/api/ws/research/{session_id}"
        
        logger.info(f"Started research session {session_id} with query '{request.query}'")
        
        return ResearchStartResponse(
            session_id=session_id,
            websocket_url=websocket_url
        )
    except Exception as e:
        logger.exception("Failed to start research session")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "stage": "backend",
                "message": "Failed to initialize research session.",
                "details": str(e)
            }
        )

@router.get(
    "/research/status/{session_id}",
    response_model=ResearchStatusResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Session Not Found"}
    }
)
async def get_research_status(session_id: str, api_request: Request):
    config = {"configurable": {"thread_id": session_id}}
    state = await api_request.app.state.graph.aget_state(config)
    
    if not state.values:
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "stage": "backend",
                "message": "Research session not found.",
                "details": f"No session found for ID {session_id}"
            }
        )
        
    return ResearchStatusResponse(
        session_id=session_id,
        status=state.values.get("status", "unknown"),
        iteration=state.values.get("iteration", 0),
        max_iterations=state.values.get("max_iterations", 3),
        query=state.values.get("query", ""),
        plan=state.values.get("plan"),
        approved_plan=state.values.get("approved_plan"),
        summary=state.values.get("summary")
    )

@router.post(
    "/research/resume/{session_id}",
    response_model=ResearchStatusResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Session Not Found"}
    }
)
async def resume_research(session_id: str, approval: PlanApprovalRequest, api_request: Request):
    config = {"configurable": {"thread_id": session_id}}
    state = await api_request.app.state.graph.aget_state(config)
    
    if not state.values:
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "stage": "backend",
                "message": "Research session not found.",
                "details": f"No session found for ID {session_id}"
            }
        )
        
    # Update graph state to resume execution
    await api_request.app.state.graph.aupdate_state(config, {
        "human_feedback": approval.human_feedback,
        "approved_plan": approval.approved_plan,
        "status": "searching" if approval.human_feedback == "approved" else "planning"
    })
    
    # Retrieve updated values to return
    updated_state = await api_request.app.state.graph.aget_state(config)
    
    return ResearchStatusResponse(
        session_id=session_id,
        status=updated_state.values.get("status", "unknown"),
        iteration=updated_state.values.get("iteration", 0),
        max_iterations=updated_state.values.get("max_iterations", 3),
        query=updated_state.values.get("query", ""),
        plan=updated_state.values.get("plan"),
        approved_plan=updated_state.values.get("approved_plan"),
        summary=updated_state.values.get("summary")
    )