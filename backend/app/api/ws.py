import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()
logger = logging.getLogger(__name__)

@router.websocket("/ws/research/{session_id}")
async def research_ws(websocket: WebSocket, session_id: str):
    await websocket.accept()
    config = {"configurable": {"thread_id": session_id}}
    logger.info(f"WebSocket connected for session: {session_id}")

    try:
        while True:
            # Check the current state of the graph
            state = await websocket.app.state.graph.aget_state(config)
            
            # If the graph has already finished, send the final state and close
            if not state.next and state.values.get("status") == "done":
                logger.info(f"Session {session_id} already completed. Sending final state.")
                await websocket.send_json({
                    "type": "state",
                    "state": state.values
                })
                break

            # Run or resume the graph stream
            logger.info(f"Streaming events for session: {session_id}")
            async for event in websocket.app.state.graph.astream(None, config, stream_mode="values"):
                await websocket.send_json({
                    "type": "state",
                    "state": event
                })

            # Check the state again after the stream run pauses or ends
            state = await websocket.app.state.graph.aget_state(config)
            
            # If the graph is waiting at an interrupt node
            if state.next:
                if state.values.get("status") == "awaiting_human":
                    logger.info(f"Session {session_id} is awaiting human feedback. Waiting for message...")
                    
                    # Block waiting for user decision via WebSocket
                    decision = await websocket.receive_json()
                    logger.info(f"Received human decision: {decision}")
                    
                    human_feedback = decision.get("human_feedback")
                    approved_plan = decision.get("approved_plan")
                    
                    # Update state to resume
                    await websocket.app.state.graph.aupdate_state(config, {
                        "human_feedback": human_feedback,
                        "approved_plan": approved_plan,
                        "status": "searching" if human_feedback == "approved" else "planning"
                    })
            else:
                logger.info(f"Session {session_id} has reached END.")
                break

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session: {session_id}")
    except Exception as e:
        logger.error(f"Error in WebSocket loop for session {session_id}: {e}", exc_info=True)
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
