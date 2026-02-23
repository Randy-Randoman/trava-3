from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/stream")
async def chat_stream():
    """Stub -- will be replaced with LangGraph SSE streaming."""
    return JSONResponse(status_code=501, content={"detail": "Not implemented yet"})

@router.get("/messages/{trip_id}")
async def get_messages(trip_id: str):
    """Stub -- will load messages from DB."""
    return JSONResponse(status_code=501, content={"detail": "Not implemented yet"})
