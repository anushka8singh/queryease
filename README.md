# QueryEase

QueryEase is a two-service application:

- `backend/` is an Express REST API that accepts user requests and forwards them to the AI engine.
- `ai_engine/` is a FastAPI service that turns natural language into safe SQL, validates it, retries on failure, and returns results plus structured logs.

## Request flow

1. Client sends a natural-language query to `POST /api/query`.
2. The Express backend validates the payload and forwards it to `POST /ai/query`.
3. The FastAPI agent inspects schema metadata, applies semantic mapping, generates SQL, performs a dry run with `EXPLAIN`, retries if needed, and then executes the query.
4. The AI engine returns `sql`, `result`, `logs`, `attempts`, and `success`.

## Run locally

### Backend

```powershell
cd backend
npm install
$env:AI_ENGINE_URL="http://127.0.0.1:8000"
npm start
```

### AI engine

```powershell
cd ai_engine
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
$env:LLM_PROVIDER="rules"
$env:MYSQL_HOST="127.0.0.1"
$env:MYSQL_PORT="3306"
$env:MYSQL_USER="readonly_user"
$env:MYSQL_PASSWORD="readonly_password"
$env:MYSQL_DATABASE="legacy_db"
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
