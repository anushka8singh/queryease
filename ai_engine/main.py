from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class QueryRequest(BaseModel):
    query: str

@app.post("/ai")
def process_query(request: QueryRequest):
    return {
        "user_query": request.query,
        "sql": "SELECT * FROM table;",  # dummy
        "result": [],
        "log": ["Step 1: Received query"]
    }