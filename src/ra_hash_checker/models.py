from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Status(StrEnum):
    SUPPORTED = "SUPPORTED"
    NO_ACHIEVEMENTS = "NO_ACHIEVEMENTS"
    UNKNOWN_HASH = "UNKNOWN_HASH"
    UNCHECKED = "UNCHECKED"
    HASH_ERROR = "HASH_ERROR"
    FORMAT_UNSUPPORTED = "FORMAT_UNSUPPORTED"
    AMBIGUOUS_CONSOLE = "AMBIGUOUS_CONSOLE"
    SCAN_ERROR = "SCAN_ERROR"


@dataclass(frozen=True)
class ConsoleSpec:
    slug: str
    name: str
    console_id: int
    extensions: tuple[str, ...]
    aliases: tuple[str, ...] = ()
    api_console_id: int | None = None

    @property
    def api_id(self) -> int:
        return self.console_id if self.api_console_id is None else self.api_console_id

    def calculate_hash(self, path: Path) -> str:
        from .native import calculate_hash

        return calculate_hash(path, self.console_id)


@dataclass(frozen=True)
class GameInfo:
    game_id: int
    title: str
    achievements: int

    @property
    def url(self) -> str:
        return f"https://retroachievements.org/game/{self.game_id}"


@dataclass
class CheckResult:
    path: str
    console: str | None
    status: Status
    hash: str | None = None
    games: list[GameInfo] = field(default_factory=list)
    message: str = ""
    candidates: list[str] = field(default_factory=list)
    catalog_source: str | None = None
    catalog_fetched_at: str | None = None


@dataclass
class RunReport:
    options: dict[str, object]
    started_at: str = field(default_factory=utc_now)
    ended_at: str | None = None
    completed: bool = True
    results: list[CheckResult] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def counts(self) -> dict[str, int]:
        return dict(sorted(Counter(result.status.value for result in self.results).items()))

    @property
    def exit_code(self) -> int:
        if not self.completed:
            return 130
        successful = {Status.SUPPORTED, Status.NO_ACHIEVEMENTS, Status.UNKNOWN_HASH}
        return int(bool(self.warnings) or any(result.status not in successful for result in self.results))