import json
import os
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .api import ApiError, RetroAchievementsAPI, build_hash_index
from .models import GameInfo

SCHEMA_VERSION = 1
OPTIONS = {"h": 1, "f": 0}


@dataclass
class Catalog:
    index: dict[str, list[GameInfo]]
    source: str
    fetched_at: str
    warnings: list[str] = field(default_factory=list)


def timestamp(value: object) -> datetime:
    if not isinstance(value, str):
        raise ValueError("Timestamp is missing.")
    result = datetime.fromisoformat(value)
    if result.tzinfo is None:
        raise ValueError("Timezone is missing.")
    return result.astimezone(timezone.utc)


def fresh(fetched: datetime, now: datetime) -> bool:
    return timedelta(0) <= now - fetched < timedelta(hours=24)


def atomic_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: str | None = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as stream:
            temporary = stream.name
            json.dump(payload, stream, ensure_ascii=True, indent=2)
            stream.write("\n")
        os.replace(temporary, path)
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)


class CatalogStore:
    def __init__(self, directory: Path, api: RetroAchievementsAPI, *, offline: bool = False,
                 refresh: bool = False, legacy_cache: Path | None = None):
        self.directory = directory
        self.api = api
        self.offline = offline
        self.refresh = refresh
        self.legacy_cache = legacy_cache
        self._loaded: dict[int, Catalog | ApiError] = {}

    def _path(self, console_id: int) -> Path:
        return self.directory / f"console-{console_id}.json"

    def _envelope(self, console_id: int, games: object, fetched_at: str) -> dict[str, object]:
        return {"schema_version": SCHEMA_VERSION, "console_id": console_id,
                "fetched_at": fetched_at, "options": OPTIONS, "games": games}

    def _read(self, console_id: int, now: datetime) -> Catalog | None:
        try:
            payload = json.loads(self._path(console_id).read_text(encoding="utf-8"))
            options = payload.get("options") if isinstance(payload, dict) else None
            if (not isinstance(payload, dict) or type(payload.get("schema_version")) is not int
                    or payload["schema_version"] != SCHEMA_VERSION
                    or type(payload.get("console_id")) is not int or payload["console_id"] != console_id
                    or not isinstance(options, dict) or options != OPTIONS
                    or any(type(value) is not int for value in options.values())):
                return None
            fetched = timestamp(payload.get("fetched_at"))
            if not fresh(fetched, now):
                return None
            return Catalog(build_hash_index(payload.get("games")), "cache", fetched.isoformat())
        except (OSError, ValueError, UnicodeError, RecursionError):
            return None

    def _migrate(self, console_id: int, now: datetime) -> Catalog | None:
        if console_id != 18 or self.legacy_cache is None or self._path(18).exists():
            return None
        try:
            fetched = datetime.fromtimestamp(self.legacy_cache.stat().st_mtime, timezone.utc)
            if not fresh(fetched, now):
                return None
            games = json.loads(self.legacy_cache.read_text(encoding="utf-8"))
            catalog = Catalog(build_hash_index(games), "legacy-cache", fetched.isoformat())
            try:
                atomic_json(self._path(18), self._envelope(18, games, catalog.fetched_at))
            except OSError:
                catalog.warnings.append("The legacy DS cache is usable but could not be copied.")
            return catalog
        except (OSError, ValueError, UnicodeError, RecursionError):
            return None

    def get(self, console_id: int) -> Catalog:
        previous = self._loaded.get(console_id)
        if isinstance(previous, ApiError):
            raise previous
        if isinstance(previous, Catalog):
            return previous
        try:
            catalog = self._load(console_id)
        except ApiError as error:
            self._loaded[console_id] = error
            raise
        self._loaded[console_id] = catalog
        return catalog

    def _load(self, console_id: int) -> Catalog:
        now = datetime.now(timezone.utc)
        if not self.refresh:
            catalog = self._read(console_id, now) or self._migrate(console_id, now)
            if catalog:
                return catalog
        if self.offline:
            raise ApiError("Offline: no fresh, valid catalog is available for this console.")
        games = self.api.games(console_id)
        catalog = Catalog(build_hash_index(games), "api", datetime.now(timezone.utc).isoformat())
        try:
            atomic_json(self._path(console_id), self._envelope(console_id, games, catalog.fetched_at))
        except OSError:
            catalog.warnings.append("RA catalog downloaded, but the cache could not be written.")
        return catalog