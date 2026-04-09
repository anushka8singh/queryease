import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field

dotenv_path = Path(__file__).with_name(".env")
load_dotenv(dotenv_path=dotenv_path)


class Settings(BaseModel):
    app_env: str = Field(default=os.getenv("APP_ENV", "development"))
    default_provider: str = Field(default=os.getenv("LLM_PROVIDER", "gemini"))
    gemini_api_key: str = Field(default=os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "")
    gemini_model: str = Field(default=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))
    mysql_host: str = Field(default=os.getenv("MYSQL_HOST", "127.0.0.1"))
    mysql_port: int = Field(default=int(os.getenv("MYSQL_PORT", "3306")))
    mysql_user: str = Field(default=os.getenv("MYSQL_USER", "readonly_user"))
    mysql_password: str = Field(default=os.getenv("MYSQL_PASSWORD", "readonly_password"))
    mysql_database: str = Field(default=os.getenv("MYSQL_DATABASE", "legacy_db"))
    mysql_schema: str | None = Field(default=os.getenv("MYSQL_SCHEMA"))
    max_agent_retries: int = Field(default=int(os.getenv("MAX_AGENT_RETRIES", "3")))
    max_result_rows: int = Field(default=int(os.getenv("MAX_RESULT_ROWS", "200")))
    request_timeout_seconds: int = Field(default=int(os.getenv("REQUEST_TIMEOUT_SECONDS", "60")))
    schema_sample_limit: int = Field(default=int(os.getenv("SCHEMA_SAMPLE_LIMIT", "20")))
    agent_temperature: float = Field(default=float(os.getenv("AGENT_TEMPERATURE", "0.1")))
    llm_max_retries: int = Field(default=int(os.getenv("LLM_MAX_RETRIES", "3")))
    llm_retry_base_delay_seconds: float = Field(default=float(os.getenv("LLM_RETRY_BASE_DELAY_SECONDS", "1.5")))
    llm_retry_max_delay_seconds: float = Field(default=float(os.getenv("LLM_RETRY_MAX_DELAY_SECONDS", "8.0")))
    llm_cache_ttl_seconds: int = Field(default=int(os.getenv("LLM_CACHE_TTL_SECONDS", "600")))
    schema_cache_ttl_seconds: int = Field(default=int(os.getenv("SCHEMA_CACHE_TTL_SECONDS", "300")))
    prompt_table_limit: int = Field(default=int(os.getenv("PROMPT_TABLE_LIMIT", "8")))
    prompt_column_limit: int = Field(default=int(os.getenv("PROMPT_COLUMN_LIMIT", "8")))
    max_query_length: int = Field(default=int(os.getenv("MAX_QUERY_LENGTH", "400")))

    @property
    def sqlalchemy_url(self) -> str:
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
        )

    def require_gemini_api_key(self) -> str:
        api_key = self.gemini_api_key.strip()
        if not api_key:
            raise RuntimeError(
                "Gemini API key is required. Set GEMINI_API_KEY or GOOGLE_API_KEY in ai_engine/.env or the process environment.",
            )
        return api_key


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
