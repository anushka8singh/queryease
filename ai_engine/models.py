from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class QueryRequest(BaseModel):
    query: str = Field(min_length=3, max_length=2000)
    context: dict[str, Any] = Field(default_factory=dict)
    provider: str | None = None

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip().lower()
        if normalized not in {"gemini", "rules"}:
            raise ValueError("provider must be either 'gemini' or 'rules'")
        return normalized


class LogEntry(BaseModel):
    step: str
    message: str
    timestamp: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class QueryResponse(BaseModel):
    sql: str
    result: list[dict[str, Any]]
    logs: list[LogEntry]


class HealthResponse(BaseModel):
    status: str
    service: str
    provider: str
    database_connected: bool


class SqlGenerationResult(BaseModel):
    sql: str
    assumptions: list[str] = Field(default_factory=list)
    semantic_matches: list[dict[str, Any]] = Field(default_factory=list)


class AgentState(BaseModel):
    query: str
    context: dict[str, Any] = Field(default_factory=dict)
    provider: str
    schema_overview: list[dict[str, Any]] = Field(default_factory=list)
    semantic_matches: list[dict[str, Any]] = Field(default_factory=list)
    semantic_summary: str = ""
    current_sql: str = ""
    validated_sql: str = ""
    result: list[dict[str, Any]] = Field(default_factory=list)
    attempts: int = 0
    last_error: str = ""
    success: bool = False
    next_node: str = "input"
    assumptions: list[str] = Field(default_factory=list)
