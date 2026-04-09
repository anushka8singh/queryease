from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

try:
    from .agent import QueryAgent
    from .config import get_settings
    from .db import Database
    from .models import HealthResponse, QueryRequest, QueryResponse
except ImportError:  # pragma: no cover
    from agent import QueryAgent
    from config import get_settings
    from db import Database
    from models import HealthResponse, QueryRequest, QueryResponse

settings = get_settings()
database = Database(settings=settings)
agent = QueryAgent(settings=settings, database=database)

app = FastAPI(title="QueryEase AI Engine", version="1.0.0")


@app.on_event("startup")
def startup_event() -> None:
    try:
        database.initialize()
    except Exception:
        return


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="queryease-ai-engine",
        provider=settings.default_provider,
        database_connected=database.ping(),
    )


@app.post("/ai/query", response_model=QueryResponse)
@app.post("/ai", response_model=QueryResponse)
def run_query(request: QueryRequest) -> QueryResponse:
    try:
        return agent.handle_query(request=request)
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        raise HTTPException(
            status_code=500,
            detail={"message": "Unexpected AI engine failure.", "error": str(exc)},
        ) from exc


@app.exception_handler(HTTPException)
def http_exception_handler(_, exc: HTTPException) -> JSONResponse:
    detail = exc.detail
    if isinstance(detail, dict):
        return JSONResponse(status_code=exc.status_code, content=detail)
    return JSONResponse(status_code=exc.status_code, content={"message": str(detail)})
