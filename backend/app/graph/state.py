from typing import TypedDict, Annotated, Optional
import operator
 
class ResearchState(TypedDict):
    query: str
    model: Optional[str]
    plan: list[str]
    approved_plan: Optional[list[str]]     # insan onayından geçmiş, düzenlenmiş hali
    findings: Annotated[list[dict], operator.add]   # her arama adımı buraya ekleme yapar
    human_feedback: Optional[str]          # "approved" | "edit" | "regenerate"
    status: str                            # "planning" | "awaiting_human" | "searching" | "compressing" | "done"
    compressed_findings: Optional[str]
    summary: Optional[str]
