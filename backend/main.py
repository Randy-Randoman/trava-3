"""
TRAVA Backend - FastAPI Application Entry Point
Run with: uvicorn main:app --reload
"""

import os
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from app.services.playwright import shutdown_playwright

# Load environment variables from root .env
load_dotenv(dotenv_path="../.env")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle for the application."""
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

DEFAULT_USER_ID = "67e4c780-75fe-4c18-8329-2492cedb57cc"


class FeedbackRequest(BaseModel):
    feedback: str
    username: str = ""


@app.post("/feedback")
async def submit_feedback(body: FeedbackRequest, x_user_id: Optional[str] = Header(None)):
    """Accept user feedback and save to database."""
    from app.services.database import db

    user_id = x_user_id or DEFAULT_USER_ID
    try:
        result = await db.save_feedback(user_id, body.username, body.feedback)
        return {"status": "ok", "id": result.get("id", "")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
