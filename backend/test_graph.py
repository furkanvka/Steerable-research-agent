import asyncio
import sys
import os
from unittest.mock import AsyncMock, patch

# Ensure app can be imported inside the container
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.graph.state import ResearchState

async def run_test():
    print("--- Starting LangGraph StateGraph Flow Test ---")
    
    session_id = "test-session-uuid"
    config = {"configurable": {"thread_id": session_id}}

    # Define mock sequences for Ollama generate calls
    # Call 1: planner
    # Call 2: summarize
    mock_generate_responses = [
        '["yapay zeka", "makine ogrenmesi"]',
        'Araştırma Özeti: Yapay zeka ve makine öğrenmesi konuları başarıyla özetlendi.'
    ]
    generate_call_idx = 0

    async def mock_generate(prompt, model=None):
        nonlocal generate_call_idx
        print(f"[MOCK LLM] Prompt received (first 100 chars): {prompt.strip()[:100]}...")
        resp = mock_generate_responses[generate_call_idx]
        print(f"[MOCK LLM] Returning: {resp}")
        generate_call_idx += 1
        return resp

    # Define mock search results for SearXNG
    async def mock_search(query):
        print(f"[MOCK SEARCH] Searching for: '{query}'")
        return [
            {
                "title": f"{query} Nedir?",
                "link": f"http://example.com/{query}",
                "content": f"{query} ile ilgili detaylı test makalesi içeriği."
            }
        ]

    # Patch the generate and search calls
    with patch("app.ollama.client.generate", side_effect=mock_generate), \
         patch("app.search.searxng.search", side_effect=mock_search):

        from app.orchestrator.graph import build_graph
        from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
        
        async with AsyncSqliteSaver.from_conn_string(":memory:") as checkpointer:
            app_graph = build_graph(checkpointer)
            
            # 1. Start the graph with initial state
            print("\n1. Initializing research session...")
            initial_state = {
                "query": "Yapay zeka teknolojileri",
                "model": "qwen3:8b",
                "findings": [],
                "status": "planning",
                "plan": [],
                "approved_plan": None,
                "human_feedback": None,
                "compressed_findings": None,
                "summary": None
            }
            await app_graph.aupdate_state(config, initial_state)

            # 2. Run until interrupt (human_review)
            print("\n2. Streaming graph execution (runs 'plan' then stops before 'human_review')...")
            async for event in app_graph.astream(None, config, stream_mode="values"):
                print(f"   [Stream Event] node status: {event.get('status')}, plan: {event.get('plan')}")

            state = await app_graph.aget_state(config)
            print(f"   Paused? {bool(state.next)}. Next nodes to run: {state.next}")
            print(f"   State Status: {state.values.get('status')}")
            print(f"   Generated Plan: {state.values.get('plan')}")

            # 3. Simulate human approving the plan
            print("\n3. Simulating human review: Approving plan...")
            await app_graph.aupdate_state(config, {
                "human_feedback": "approved",
                "approved_plan": state.values.get("plan"),
                "status": "searching"
            })

            # 4. Resume graph execution
            print("\n4. Resuming graph execution (should run search -> compress -> summarize)...")
            async for event in app_graph.astream(None, config, stream_mode="values"):
                print(f"   [Stream Event] node status: {event.get('status')}")

            final_state = await app_graph.aget_state(config)
            print("\n--- Graph Completed ---")
            print(f"Final Status: {final_state.values.get('status')}")
            print(f"Compressed Findings Chars: {len(final_state.values.get('compressed_findings') or '')}")
            print(f"Summary: {final_state.values.get('summary')}")

if __name__ == "__main__":
    asyncio.run(run_test())
