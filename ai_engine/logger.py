from datetime import datetime, timezone

try:
    from .models import LogEntry
except ImportError:  # pragma: no cover
    from models import LogEntry


class QueryLogger:
    def __init__(self) -> None:
        self._entries: list[LogEntry] = []

    def clear(self) -> None:
        self._entries = []

    def add(self, step: str, message: str, **metadata) -> None:
        self._entries.append(
            LogEntry(
                step=step,
                message=message,
                timestamp=datetime.now(timezone.utc),
                metadata=metadata,
            ),
        )

    def entries(self) -> list[LogEntry]:
        return list(self._entries)
