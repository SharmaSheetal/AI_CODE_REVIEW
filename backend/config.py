"""
config.py — Central settings loaded from environment variables.

All secrets (API keys, tokens) live in a .env file; this module reads them
via pydantic-settings so every other module imports from here, never from
os.environ directly. This makes secrets easy to test and impossible to leak
by accident into logs.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- GitHub ---
    github_token: str = ""               # Personal Access Token with 'repo' scope

    # --- LLM (choose Groq for cloud speed OR Ollama for local/free) ---
    llm_provider: str = "groq"           # "groq" | "ollama"
    groq_api_key: str = ""               # Groq cloud API key
    groq_model: str = "llama-3.1-8b-instant"  # Groq model — swap to llama-3.3-70b-versatile for higher quality
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"         # Model name as pulled in Ollama

    # --- FastAPI server ---
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = False

    # --- Confidence scoring ---
    min_confidence: float = 0.5          # Suggestions below this are filtered out

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


# Singleton — import `settings` everywhere instead of re-instantiating
settings = Settings()
