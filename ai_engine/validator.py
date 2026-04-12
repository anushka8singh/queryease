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
TABLE_REFERENCE_PATTERN = re.compile(
    r"\b(?:from|join)\s+[`\"]?([a-zA-Z_][a-zA-Z0-9_]*)[`\"]?",
    re.IGNORECASE,
)


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


def detect_table_from_query(query: str, schema_tables: list[str]) -> str | None:
    query = query.lower()
    for table in schema_tables:
        if table.lower() in query:
            return table
    return None


def validate_sql_tables(sql: str, schema_tables: list[str]) -> bool:
    sql_lower = sql.lower()
    for table in schema_tables:
        if table.lower() in sql_lower:
            return True
    return False


def extract_tables_from_sql(sql: str) -> list[str]:
    seen: list[str] = []
    for table_name in TABLE_REFERENCE_PATTERN.findall(sql):
        if table_name not in seen:
            seen.append(table_name)
    return seen


class SqlValidator:
    def __init__(self, database: "Database") -> None:
        self.database = database

    def validate(
        self,
        sql: str,
        max_rows: int,
        schema_tables: list[str],
        table_hint: str | None = None,
    ) -> str:
        safe_sql = validate_sql_security(sql)

        if not validate_sql_tables(safe_sql, schema_tables):
            security_logger.warning(
                "Blocked SQL query because it did not reference a known schema table.",
                extra={"sql": safe_sql, "schema_tables": schema_tables},
            )
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Invalid table detected in SQL",
                    "sql": safe_sql,
                },
            )

        extracted_tables = extract_tables_from_sql(safe_sql)
        if not extracted_tables:
            security_logger.warning(
                "Blocked SQL query because no executable table reference was found.",
                extra={"sql": safe_sql},
            )
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Invalid table detected in SQL",
                    "sql": safe_sql,
                },
            )

        allowed_tables = {table.lower() for table in schema_tables}
        invalid_tables = [table for table in extracted_tables if table.lower() not in allowed_tables]
        if invalid_tables:
            security_logger.warning(
                "Blocked SQL query because it referenced tables outside the schema.",
                extra={"sql": safe_sql, "invalid_tables": invalid_tables},
            )
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Invalid table detected in SQL",
                    "invalid_tables": invalid_tables,
                    "sql": safe_sql,
                },
            )

        if table_hint and table_hint.lower() not in {table.lower() for table in extracted_tables}:
            security_logger.warning(
                "Blocked SQL query because it did not use the required detected table.",
                extra={"sql": safe_sql, "required_table": table_hint},
            )
            raise HTTPException(
                status_code=400,
                detail={
                    "message": f"Expected SQL to use detected table '{table_hint}'.",
                    "sql": safe_sql,
                },
            )

        self.database.dry_run(safe_sql)
        return enforce_result_limit(safe_sql, max_rows)
