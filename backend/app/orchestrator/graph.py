from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from app.graph.state import ResearchState
from app.graph.nodes.plan_node import plan_node
from app.graph.nodes.human_review_node import human_review_node
from app.graph.nodes.search_node import search_node
from app.graph.nodes.compress_node import compress_node
from app.graph.nodes.summarize_node import summarize_node
from app.graph.routing import route_after_human_review

def build_graph(checkpointer: AsyncSqliteSaver):
    g = StateGraph(ResearchState)
    
    # Register all nodes
    g.add_node("plan", plan_node)
    g.add_node("human_review", human_review_node)
    g.add_node("search", search_node)
    g.add_node("compress", compress_node)
    g.add_node("summarize", summarize_node)
 
    # Define flows and connections (completely linear structure)
    g.set_entry_point("plan")
    
    g.add_edge("plan", "human_review")
    g.add_conditional_edges("human_review", route_after_human_review)
    
    g.add_edge("search", "compress")
    g.add_edge("compress", "summarize")
    g.add_edge("summarize", END)
 
    # Compile the graph with checkpointer and human_review interrupt
    return g.compile(checkpointer=checkpointer, interrupt_before=["human_review"])
