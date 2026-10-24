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
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    # SERVICE_KEY: Used by backend to bypass RLS (ownership is checked in the API layer)
    SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_KEY", "")

    # Google AI (for langchain-google-genai)
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")

    # Anthropic (swappable LLM)
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

    # Tavily Search
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")

    # LLM provider: "google" (default) or "anthropic"
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "google")


settings = Settings()
