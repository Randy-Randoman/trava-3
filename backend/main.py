"""
TRAVA Backend - FastAPI Application Entry Point
Run with: uvicorn main:app --reload
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from app.services.playwright import shutdown_playwright, warmup_playwright
from app.core.auth import require_auth

# Load environment variables from root .env
load_dotenv(dotenv_path="../.env")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle for the application."""
    import asyncio
    asyncio.create_task(warmup_playwright())
    yield
    # Shutdown: clean up shared resources
    await shutdown_playwright()


app = FastAPI(
    title="TRAVA API",
    description="AI-powered travel planning assistant backend",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS for frontend communication
# ALLOWED_ORIGINS env var should be comma-separated list of domains
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Welcome to TRAVA API"}


@app.get("/health")
async def health_check():
    """Health check endpoint for frontend verification"""
    return {"status": "ok"}


# API routes
from app.api.chat import router as chat_router
from app.api.trips import router as trips_router

app.include_router(chat_router, tags=["chat"])
app.include_router(trips_router, tags=["trips"])


# ================================================
# Feedback endpoint
# ================================================

class FeedbackRequest(BaseModel):
    feedback: str
    username: str = ""


@app.post("/feedback")
async def submit_feedback(body: FeedbackRequest, user_id: str = Depends(require_auth)):
    """Accept user feedback and save to database."""
    from app.services.database import db
    try:
        result = await db.save_feedback(user_id, body.username, body.feedback)
        return {"status": "ok", "id": result.get("id", "")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
