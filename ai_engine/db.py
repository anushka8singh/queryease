from collections.abc import Sequence
from datetime import date, datetime
from decimal import Decimal
import logging
from typing import Any
import time
import os

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

try:
    from .config import Settings
    from .security import enforce_result_limit
    from .validator import validate_sql_security
except ImportError:  # pragma: no cover
    from config import Settings
    from security import enforce_result_limit
    from validator import validate_sql_security


db_logger = logging.getLogger("queryease.db")


class Database:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.engine: Engine | None = None
        self._schema_cache: list[dict[str, Any]] | None = None
        self._schema_cache_loaded_at = 0.0
        self._last_init_error = ""
        self._last_schema_status = ""

    @property
    def is_configured(self) -> bool:
        return self.engine is not None

    def initialize(self) -> None:
        engine = create_engine(
            self.settings.sqlalchemy_url,
            pool_pre_ping=True,
            pool_recycle=3600,
            connect_args={"connect_timeout": self.settings.request_timeout_seconds},
        )
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        self.engine = engine
        self._last_init_error = ""

    def _get_engine(self) -> Engine:
        if self.engine is None:
            try:
                self.initialize()
            except Exception as exc:
                self._last_init_error = str(exc)
                raise RuntimeError(
                    "Database connection is unavailable. Check MYSQL settings.",
                ) from exc
        return self.engine

    def ping(self) -> bool:
        try:
            with self._get_engine().connect() as connection:
                connection.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    def dry_run(self, sql: str) -> None:
        safe_sql = validate_sql_security(sql)
        try:
            with self._get_engine().connect() as connection:
                connection.execute(text(f"EXPLAIN {safe_sql}"))
        except SQLAlchemyError as exc:
            raise ValueError(str(exc)) from exc

    def execute_query(self, sql: str, max_rows: int) -> list[dict[str, Any]]:
        safe_sql = enforce_result_limit(validate_sql_security(sql), max_rows)

        try:
            with self._get_engine().connect() as connection:
                result = connection.execution_options(stream_results=True).execute(text(safe_sql))
                rows = result.fetchmany(max_rows)
                keys = list(result.keys())
        except SQLAlchemyError as exc:
            raise ValueError(str(exc)) from exc

        return [self._serialize_row(keys, row) for row in rows]

    # 🔥 FIXED FUNCTION
    def get_schema(self, table_limit: int) -> dict[str, list[str]] | dict[str, str]:
        schema_name = self.settings.mysql_schema or self.settings.mysql_database

        if not schema_name:
            raise RuntimeError("MYSQL_SCHEMA or MYSQL_DATABASE must be configured.")

        metadata_sql = text(
            """
            SELECT
                table_name,
                column_name
            FROM information_schema.columns
            WHERE table_schema = :schema
            ORDER BY table_name ASC, ordinal_position ASC
            """
        )

        try:
            with self._get_engine().connect() as connection:
                rows = connection.execute(
                    metadata_sql, {"schema": schema_name}
                ).fetchall()
        except SQLAlchemyError as exc:
            db_logger.warning("Schema lookup failed: %s", exc)
            return {
                "message": "Failed to load schema",
                "error": str(exc),
            }

        # 🔍 DEBUG
        print("Schema rows:", rows)

        if not rows:
            raise Exception("No tables found in schema")

        schema_map: dict[str, list[str]] = {}

        for row in rows:
            mapping = row._mapping  # ✅ SQLAlchemy v2 fix

            # 🔥 CASE-INSENSITIVE FIX
            table_name = mapping.get("table_name") or mapping.get("TABLE_NAME")
            column_name = mapping.get("column_name") or mapping.get("COLUMN_NAME")

            print("Row mapping:", mapping)  # debug

            if not table_name or not column_name:
                raise Exception(f"Unexpected schema row format: {mapping}")

            table_name = str(table_name)
            column_name = str(column_name)

            if table_name not in schema_map:
                if len(schema_map) >= table_limit:
                    continue
                schema_map[table_name] = []

            schema_map[table_name].append(column_name)

        if not schema_map:
            raise Exception("No tables found in schema")

        db_logger.info("Discovered tables: %s", list(schema_map))
        db_logger.info("Schema map: %s", schema_map)

        print(f"Discovered tables: {list(schema_map)}")
        print(f"Schema map: {schema_map}")

        return schema_map

    def get_schema_overview(self, table_limit: int) -> list[dict[str, Any]]:
        if (
            self._schema_cache is not None
            and time.time() - self._schema_cache_loaded_at < self.settings.schema_cache_ttl_seconds
        ):
            return self._schema_cache

        schema_map = self.get_schema(table_limit)

        if isinstance(schema_map, dict) and "message" in schema_map:
            return []

        overview = [
            {
                "table": table,
                "columns": [{"name": col} for col in cols],
            }
            for table, cols in schema_map.items()
        ]

        self._schema_cache = overview
        self._schema_cache_loaded_at = time.time()

        return overview

    def _serialize_row(self, keys: Sequence[str], row: Sequence[Any]) -> dict[str, Any]:
        return {
            key: self._serialize_value(value)
            for key, value in zip(keys, row, strict=False)
        }

    def _serialize_value(self, value: Any) -> Any:
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        return value