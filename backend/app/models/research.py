from pydantic import BaseModel, Field
from typing import Optional, List
from app.core.config import settings

class ResearchRequest(BaseModel):
    query: str
    model: str = settings.OLLAMA_MODEL
    max_iterations: int = 3

class ResearchStartResponse(BaseModel):
    session_id: str
    websocket_url: str

class PlanApprovalRequest(BaseModel):
    human_feedback: str = Field(..., description="'approved' | 'edit'")
    approved_plan: List[str]

class ResearchStatusResponse(BaseModel):
    session_id: str
    status: str
    iteration: int = 0
    max_iterations: int = 0
    query: str
    plan: Optional[List[str]] = None
    approved_plan: Optional[List[str]] = None
    summary: Optional[str] = None

class ResearchResponse(BaseModel):
    success: bool = True
    query: str
    model: str
    plan: List[str]
    summary: str

class ErrorResponse(BaseModel):
    success: bool = False
    stage: str
    message: str
    details: str