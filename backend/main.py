"""
TRAVA Backend - FastAPI Application Entry Point
Run with: uvicorn main:app --reload
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables from root .env
load_dotenv(dotenv_path="../.env")

app = FastAPI(
    title="TRAVA API",
    description="AI-powered travel planning assistant backend",
    version="0.1.0"
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
