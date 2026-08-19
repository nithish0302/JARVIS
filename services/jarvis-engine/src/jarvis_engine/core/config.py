from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    JARVIS_HOST: str = "localhost"
    JARVIS_PORT: int = 8765
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:3b"
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "google/gemma-4-27b-it:free"
    TAVILY_API_KEY: str = ""
    TAVILY_MAX_RESULTS: int = 5
    SEARCH_PROVIDER: str = "tavily"
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "compound-beta"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    WAKE_WORD_MODEL_PATH: str = "models/wake_up_jarvis.onnx"
    DB_PATH: str = "data/jarvis.db"
    VERSION: str = "0.1.0"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
