import re

from fastapi import HTTPException


COMMENT_PATTERN = re.compile(r"(--[^\n]*$)|(#.*$)|(/\*.*?\*/)", re.MULTILINE | re.DOTALL)
FORBIDDEN_PATTERN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE|REPLACE|GRANT|REVOKE|MERGE|CALL)\b",
    re.IGNORECASE,
)
RISKY_FUNCTION_PATTERN = re.compile(r"\b(SLEEP|BENCHMARK|LOAD_FILE|INTO\s+OUTFILE|INTO\s+DUMPFILE)\b", re.IGNORECASE)
LIMIT_PATTERN = re.compile(r"\blimit\s+\d+(\s*,\s*\d+)?(\s+offset\s+\d+)?\s*$", re.IGNORECASE)
SELECT_LIKE_PATTERN = re.compile(r"^\s*(select|with)\b", re.IGNORECASE | re.DOTALL)


def strip_sql_comments(sql: str) -> str:
    return COMMENT_PATTERN.sub("", sql)


def ensure_safe_select(sql: str) -> str:
    normalized = strip_sql_comments(sql).strip().rstrip(";")
    lowered = normalized.lower()

    if not normalized:
        raise HTTPException(status_code=400, detail={"message": "Generated SQL was empty."})

    if FORBIDDEN_PATTERN.search(normalized):
        raise HTTPException(
            status_code=400,
            detail={"message": "Only read-only SELECT statements are allowed.", "sql": normalized},
        )

    if RISKY_FUNCTION_PATTERN.search(normalized):
        raise HTTPException(
            status_code=400,
            detail={"message": "Potentially unsafe SQL functions were detected.", "sql": normalized},
        )

    if ";" in normalized:
        raise HTTPException(
            status_code=400,
            detail={"message": "Only a single SQL statement is allowed.", "sql": normalized},
        )

    if not SELECT_LIKE_PATTERN.match(normalized):
        raise HTTPException(
            status_code=400,
            detail={"message": "QueryEase only allows SELECT statements.", "sql": normalized},
        )

    return normalized


def enforce_result_limit(sql: str, max_rows: int) -> str:
    safe_sql = ensure_safe_select(sql)
    if LIMIT_PATTERN.search(safe_sql):
        return safe_sql
    return f"{safe_sql} LIMIT {max_rows}"
