from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    ANTHROPIC_API_KEY: str = ""
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    SECRET_KEY: str = "promptforge-dev-secret-key"
    GITHUB_TOKEN_ENCRYPTION_KEY: str = ""
    MCP_PORT: int = 8001
    MCP_HOST: str = "127.0.0.1"
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/promptforge.db"
    CORS_ORIGINS: str = "http://localhost:5199,http://localhost:4173"

    class Config:
        env_file = ".env"


settings = Settings()
