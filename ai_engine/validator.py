import logging
import re
from typing import TYPE_CHECKING

from fastapi import HTTPException

try:
    from .security import enforce_result_limit
except ImportError:  # pragma: no cover
    from security import enforce_result_limit

if TYPE_CHECKING:
    try:
        from .db import Database
    except ImportError:  # pragma: no cover
        from db import Database


security_logger = logging.getLogger("queryease.sql_security")

ALLOWED_SELECT_PATTERN = re.compile(r"^\s*(select|with)\b", re.IGNORECASE | re.DOTALL)
BLOCKED_SQL_PATTERN = re.compile(
    r"\b(delete|update|insert|drop|alter|truncate|create|replace|grant|revoke|merge|call)\b",
    re.IGNORECASE,
)
MULTI_STATEMENT_PATTERN = re.compile(r";")


def validate_sql_security(sql: str) -> str:
    normalized_sql = sql.strip()

    if not normalized_sql:
        security_logger.warning("Blocked empty SQL query.")
        raise HTTPException(status_code=400, detail={"message": "SQL query cannot be empty."})

    if BLOCKED_SQL_PATTERN.search(normalized_sql):
        security_logger.warning("Blocked SQL query containing restricted keywords.", extra={"sql": normalized_sql})
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Blocked query: only SELECT statements are allowed.",
                "sql": normalized_sql,
            },
        )

    cleaned = normalized_sql.rstrip(";").strip()

    if MULTI_STATEMENT_PATTERN.search(cleaned):
        security_logger.warning("Blocked SQL query containing multiple statements.", extra={"sql": normalized_sql})
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Blocked query: multiple SQL statements are not allowed.",
                "sql": normalized_sql,
            },
        )

    if not ALLOWED_SELECT_PATTERN.match(cleaned):
        security_logger.warning("Blocked non-SELECT SQL query.", extra={"sql": normalized_sql})
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Blocked query: only SELECT statements are allowed.",
                "sql": normalized_sql,
            },
        )

    return cleaned


class SqlValidator:
    def __init__(self, database: "Database") -> None:
        self.database = database

    def validate(self, sql: str, max_rows: int) -> str:
        safe_sql = validate_sql_security(sql)
        self.database.dry_run(safe_sql)
        return enforce_result_limit(safe_sql, max_rows)
