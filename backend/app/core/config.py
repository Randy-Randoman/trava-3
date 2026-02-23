"""
Configuration module - Environment variable loader
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Find the .env file - check multiple possible locations
def find_env_file():
    """Find .env file in project root or parent directories"""
    current = Path(__file__).resolve()

    # Check up to 5 parent directories
    for _ in range(5):
        current = current.parent
        env_path = current / ".env"
        if env_path.exists():
            return env_path

    return None

env_path = find_env_file()
if env_path:
    load_dotenv(dotenv_path=env_path)
else:
    # Fallback to default load_dotenv behavior
    load_dotenv()


class Settings:
    """Application settings loaded from environment variables"""

    # Supabase
    SUPABASE_URL: str = os.getenv("NEXT_PUBLIC_SUPABASE_URL", "")
    # ANON_KEY: Not used in backend (used by frontend only)
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_SERVICE_KEY", "")
    # SERVICE_KEY: Used by backend to bypass RLS (required for MVP without auth)
    SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_KEY", "")

    # Google AI (for langchain-google-genai)
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")

    # Anthropic (swappable LLM)
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

    # Tavily Search
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")

    # CJ Affiliate (for affiliate links)
    CJ_PID: str = os.getenv("CJ_PID", "")
    CJ_AID: str = os.getenv("CJ_AID", "")

    # Application settings
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    DEFAULT_USER_ID: str = os.getenv("DEFAULT_USER_ID", "67e4c780-75fe-4c18-8329-2492cedb57cc")
    AUTH_ENABLED: bool = os.getenv("AUTH_ENABLED", "false").lower() == "true"

    # URLs
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://localhost:8000")
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")


settings = Settings()
