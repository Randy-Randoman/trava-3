"""
Chat API - SSE streaming endpoint using LangGraph agent
"""

import json
from fastapi import APIRouter, Request
from starlette.responses import StreamingResponse, JSONResponse
from langchain_core.messages import HumanMessage, AIMessage

from app.models.chat import ChatRequest
from app.services.database import DatabaseService
from app.agent.graph import create_agent_graph
from app.core.config import settings

router = APIRouter(prefix="/chat", tags=["chat"])


def _sse_event(data: dict) -> str:
    """Format a dict as an SSE data line."""
    return f"data: {json.dumps(data)}\n\n"


def _extract_text(content) -> str:
    """Extract plain text from LangChain message content.

    Content can be a string or a list of content blocks (Gemini returns the latter).
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("text"):
                parts.append(block["text"])
        return "\n".join(parts)
    return str(content)


@router.post("/stream")
async def chat_stream(request: Request, body: ChatRequest):
    """
    Stream agent responses via Server-Sent Events.

    SSE event types:
      - status: progress updates (e.g. "Thinking...", "Using search...")
      - text: final assistant text response
      - canvas_updated: canvas was modified server-side
      - done: stream complete
      - error: something went wrong
    """
    user_message = body.message
    trip_id = body.trip_id

    # Resolve user_id from header, falling back to default
    user_id = request.headers.get("X-User-ID") or settings.DEFAULT_USER_ID

    async def event_generator():
        assistant_response = ""

        try:
            # 1. Send initial status
            yield _sse_event({"type": "status", "content": "Thinking..."})

            # 2. Load conversation history from DB
            db = DatabaseService()
            conv = await db.get_or_create_conversation(trip_id)
            conversation_id = conv["id"]
            db_messages = await db.load_messages(conversation_id, limit=50)

            # 3. Convert DB messages to LangChain format
            #    DB stores role as 'user' or 'model' (Gemini convention)
            messages = []
            for msg in db_messages:
                role = msg["role"]
                content = msg["content"]
                if role == "user":
                    messages.append(HumanMessage(content=content))
                else:
                    # 'model' or 'assistant' -> AIMessage
                    messages.append(AIMessage(content=content))

            # Add the new user message
            messages.append(HumanMessage(content=user_message))

            # 4. Create and stream the agent graph
            graph = create_agent_graph(trip_id, user_id)
            input_state = {
                "messages": messages,
                "trip_id": trip_id,
                "user_id": user_id,
            }

            async for event in graph.astream(input_state, stream_mode="updates"):
                for node_name, node_output in event.items():
                    if node_name == "agent":
                        last_msg = node_output["messages"][-1]
                        if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                            # Agent wants to call a tool
                            tool_name = last_msg.tool_calls[0]["name"]
                            yield _sse_event({"type": "status", "content": f"Using {tool_name}..."})
                        elif last_msg.content:
                            # Final text response from the agent
                            assistant_response = _extract_text(last_msg.content)
                            yield _sse_event({"type": "text", "content": assistant_response})
                    elif node_name == "tools":
                        # Tool finished executing -- could send status update
                        yield _sse_event({"type": "status", "content": "Processing results..."})

            # 5. Save messages to DB after successful completion
            #    DB uses 'model' role for assistant messages (Gemini convention)
            await db.save_message(conversation_id, "user", user_message)
            if assistant_response:
                await db.save_message(conversation_id, "model", assistant_response)

            # 6. Done
            yield _sse_event({"type": "done"})

        except Exception as e:
            print(f"[Chat] Error in stream: {e}")
            yield _sse_event({"type": "error", "content": str(e)})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/messages/{trip_id}")
async def get_messages(trip_id: str):
    """
    Load chat message history for a trip.

    Returns messages in the format the frontend expects:
    { "messages": [{ "role": "user"|"model", "content": "...", "created_at": "..." }] }
    """
    try:
        db = DatabaseService()
        conv = await db.get_or_create_conversation(trip_id)
        conversation_id = conv["id"]
        db_messages = await db.load_messages(conversation_id, limit=50)

        return {"messages": db_messages}

    except Exception as e:
        print(f"[Chat] Error loading messages: {e}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Failed to load messages: {str(e)}"},
        )
