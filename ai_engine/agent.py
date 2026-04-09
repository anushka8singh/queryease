from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from fastapi import HTTPException

try:
    from .config import Settings
    from .db import Database
    from .logger import QueryLogger
    from .models import AgentState, QueryRequest, QueryResponse
    from .semantic_mapper import SemanticMapper
    from .sql_generator import SqlGenerator
    from .validator import SqlValidator
except ImportError:  # pragma: no cover
    from config import Settings
    from db import Database
    from logger import QueryLogger
    from models import AgentState, QueryRequest, QueryResponse
    from semantic_mapper import SemanticMapper
    from sql_generator import SqlGenerator
    from validator import SqlValidator


class WorkflowNode(Protocol):
    name: str

    def run(self, state: AgentState, logger: QueryLogger) -> AgentState:
        ...


@dataclass
class WorkflowContext:
    settings: Settings
    database: Database
    semantic_mapper: SemanticMapper
    generator: SqlGenerator
    validator: SqlValidator


def _has_feedback_retry_remaining(state: AgentState) -> bool:
    return state.attempts < 2


class InputNode:
    name = "input"

    def __init__(self, context: WorkflowContext) -> None:
        self.context = context

    def run(self, state: AgentState, logger: QueryLogger) -> AgentState:
        logger.add(
            "input_node",
            "Preparing workflow state from the incoming request.",
            provider=state.provider,
            query=state.query,
        )

        try:
            state.schema_overview = self.context.database.get_schema_overview(
                self.context.settings.schema_sample_limit,
            )
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail={"message": "Failed to inspect the database schema.", "error": str(exc)},
            ) from exc

        if not state.schema_overview:
            fallback_message = self.context.database.last_schema_status or "Database is empty or schema not accessible"
            logger.add(
                "schema_unavailable",
                "Schema discovery returned no tables, so the workflow stopped before SQL generation.",
                fallback_message=fallback_message,
            )
            raise HTTPException(
                status_code=503,
                detail={
                    "message": fallback_message,
                    "logs": [entry.model_dump(mode="json") for entry in logger.entries()],
                },
            )

        state.semantic_matches = self.context.semantic_mapper.match(state.query)
        state.semantic_summary = self.context.semantic_mapper.describe(state.semantic_matches)
        state.next_node = SQLGeneratorNode.name

        logger.add(
            "schema_loaded",
            "Schema loaded",
            table_count=len(state.schema_overview),
            semantic_matches=state.semantic_matches,
        )
        return state


class SQLGeneratorNode:
    name = "sql_generator"

    def __init__(self, context: WorkflowContext) -> None:
        self.context = context

    def run(self, state: AgentState, logger: QueryLogger) -> AgentState:
        state.attempts += 1
        if state.provider == "gemini":
            logger.add(
                "prompt_sent",
                "Prompt sent to Gemini",
                attempt=state.attempts,
                schema_tables=[table.get("table", "unknown_table") for table in state.schema_overview],
            )

        generated = self.context.generator.generate(
            user_query=state.query,
            provider=state.provider,
            semantic_summary=state.semantic_summary,
            schema_overview=state.schema_overview,
            context=state.context,
        )

        if state.provider == "gemini":
            logger.add(
                "response_received",
                "Response received",
                attempt=state.attempts,
            )

        state.current_sql = generated.sql
        state.assumptions = generated.assumptions
        state.last_error = ""
        state.next_node = ValidatorNode.name

        logger.add(
            "sql_generated",
            "SQL generated",
            attempt=state.attempts,
            sql=state.current_sql,
            assumptions=state.assumptions,
            schema_tables=[table.get("table", "unknown_table") for table in state.schema_overview],
        )
        return state


class ValidatorNode:
    name = "validator"

    def __init__(self, context: WorkflowContext) -> None:
        self.context = context

    def run(self, state: AgentState, logger: QueryLogger) -> AgentState:
        logger.add(
            "validator_node",
            "Validating generated SQL before execution.",
            attempt=state.attempts,
            sql=state.current_sql,
        )

        try:
            state.validated_sql = self.context.validator.validate(
                state.current_sql,
                self.context.settings.max_result_rows,
            )
            state.next_node = ExecutorNode.name
            logger.add(
                "validation_passed",
                "Validation passed",
                attempt=state.attempts,
                sql=state.validated_sql,
            )
            return state
        except HTTPException as exc:
            state.last_error = str(exc.detail)
        except Exception as exc:
            state.last_error = str(exc)

        logger.add(
            "validation_failed",
            "Validation failed, attempting fix",
            attempt=state.attempts,
            sql=state.current_sql,
            error=state.last_error,
        )

        if not _has_feedback_retry_remaining(state):
            state.next_node = "failed"
            return state

        logger.add(
            "feedback_triggered",
            "Feedback loop triggered",
            attempt=state.attempts,
        )

        state.next_node = FixerNode.name
        return state


class FixerNode:
    name = "fixer"

    def __init__(self, context: WorkflowContext) -> None:
        self.context = context

    def run(self, state: AgentState, logger: QueryLogger) -> AgentState:
        state.attempts += 1
        logger.add(
            "fixer_node",
            "Repairing SQL after validation or execution failure.",
            attempt=state.attempts,
            failed_sql=state.current_sql,
            error=state.last_error,
        )
        if state.provider == "gemini":
            logger.add(
                "prompt_sent",
                "Prompt sent to Gemini",
                attempt=state.attempts,
                failed_sql=state.current_sql,
            )

        repaired = self.context.generator.repair(
            user_query=state.query,
            provider=state.provider,
            failed_sql=state.current_sql,
            error_message=state.last_error,
            semantic_summary=state.semantic_summary,
            schema_overview=state.schema_overview,
            context=state.context,
        )

        if state.provider == "gemini":
            logger.add(
                "response_received",
                "Response received",
                attempt=state.attempts,
            )

        state.current_sql = repaired.sql
        state.assumptions = repaired.assumptions
        state.next_node = ValidatorNode.name

        logger.add(
            "sql_corrected",
            "SQL corrected",
            attempt=state.attempts,
            sql=state.current_sql,
            assumptions=state.assumptions,
        )
        logger.add(
            "feedback_applied",
            "Feedback applied",
            attempt=state.attempts,
        )
        return state


class ExecutorNode:
    name = "executor"

    def __init__(self, context: WorkflowContext) -> None:
        self.context = context

    def run(self, state: AgentState, logger: QueryLogger) -> AgentState:
        logger.add(
            "executor_node",
            "Executing validated SQL against the database.",
            attempt=state.attempts,
            sql=state.validated_sql,
        )

        try:
            state.result = self.context.database.execute_query(
                state.validated_sql,
                self.context.settings.max_result_rows,
            )
            if not state.result and _has_feedback_retry_remaining(state):
                state.last_error = "empty result"
                logger.add(
                    "feedback_triggered",
                    "Feedback loop triggered",
                    attempt=state.attempts,
                    reason="empty result",
                )
                state.next_node = FixerNode.name
                return state
            state.success = True
            state.next_node = "completed"
            logger.add(
                "query_executed",
                "Query executed successfully",
                attempt=state.attempts,
                row_count=len(state.result),
            )
            return state
        except Exception as exc:
            state.last_error = str(exc)
            logger.add(
                "executor_failed",
                "Executor node failed to run the SQL query.",
                attempt=state.attempts,
                sql=state.validated_sql,
                error=state.last_error,
            )

            if not _has_feedback_retry_remaining(state):
                state.next_node = "failed"
                return state

            logger.add(
                "feedback_triggered",
                "Feedback loop triggered",
                attempt=state.attempts,
                reason="execution failure",
            )

            state.next_node = FixerNode.name
            return state


class QueryAgent:
    def __init__(self, settings: Settings, database: Database) -> None:
        mapping_path = Path(__file__).with_name("semantic_map.json")
        context = WorkflowContext(
            settings=settings,
            database=database,
            semantic_mapper=SemanticMapper(mapping_path),
            generator=SqlGenerator(settings=settings),
            validator=SqlValidator(database),
        )
        self.settings = settings
        self.nodes: dict[str, WorkflowNode] = {
            InputNode.name: InputNode(context),
            SQLGeneratorNode.name: SQLGeneratorNode(context),
            ValidatorNode.name: ValidatorNode(context),
            FixerNode.name: FixerNode(context),
            ExecutorNode.name: ExecutorNode(context),
        }

    def handle_query(self, request: QueryRequest) -> QueryResponse:
        logger = QueryLogger()
        state = AgentState(
            query=request.query,
            context=request.context,
            provider=(request.provider or self.settings.default_provider).lower(),
        )

        logger.add(
            "workflow_start",
            "Starting agent workflow",
            entry_node=state.next_node,
            max_retries=1,
        )

        while state.next_node not in {"completed", "failed"}:
            current_node_name = state.next_node
            node = self.nodes.get(current_node_name)
            if node is None:
                raise HTTPException(
                    status_code=500,
                    detail={"message": f"Unknown workflow node '{current_node_name}'."},
                )
            state = node.run(state, logger)

        if state.success:
            logger.add(
                "workflow_complete",
                "Structured agent workflow completed successfully.",
                attempts=state.attempts,
                final_node=state.next_node,
            )
            return QueryResponse(
                sql=state.validated_sql,
                result=state.result,
                logs=logger.entries(),
            )

        logger.add(
            "workflow_failed",
            "Structured agent workflow exhausted retries without success.",
            attempts=state.attempts,
            last_error=state.last_error,
            sql=state.current_sql,
        )
        raise HTTPException(
            status_code=422,
            detail={
                "message": "The agent workflow could not produce a valid SQL query within the retry limit.",
                "sql": state.current_sql,
                "logs": [entry.model_dump(mode="json") for entry in logger.entries()],
            },
        )
