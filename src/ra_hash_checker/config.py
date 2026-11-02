import argparse
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

from dotenv import dotenv_values


@dataclass(frozen=True)
class Settings:
    project_dir: Path
    paths: tuple[Path, ...]
    consoles: tuple[str, ...] = ("all",)
    api_key: str = field(default="", repr=False)
    log_enabled: bool = True
    log_dir: Path = Path("log")
    cache_dir: Path = Path("cache")
    offline: bool = False
    refresh_cache: bool = False
    default_roms: bool = False

    def public_options(self) -> dict[str, object]:
        return {
            "project_dir": str(self.project_dir),
            "paths": [str(path) for path in self.paths],
            "consoles": list(self.consoles),
            "log_enabled": self.log_enabled,
            "log_dir": str(self.log_dir),
            "cache_dir": str(self.cache_dir),
            "offline": self.offline,
            "refresh_cache": self.refresh_cache,
        }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Identify ROMs using official RetroAchievements hashes.")
    result.add_argument("--paths", nargs="+", action="extend", metavar="PATH",
                        help="Folders to search recursively (repeatable; replaces configured paths).")
    result.add_argument("--consoles", nargs="+", action="extend", metavar="CONSOLE",
                        help="Console names or aliases (default: all; repeatable).")
    result.add_argument("--api-key", metavar="KEY",
                        help="Override RA_API_KEY; prefer .env to avoid exposing keys in shell history.")
    result.add_argument("--log", action=argparse.BooleanOptionalAction, default=None,
                        help="Write both text and JSON reports (default: enabled).")
    result.add_argument("--log-path", metavar="PATH", help="Report directory (default: log).")
    result.add_argument("--cache-dir", metavar="PATH", help="Catalog cache directory (default: cache).")
    result.add_argument("--project-dir", metavar="PATH", help="Base directory for default paths and .env lookup.")
    result.add_argument("--env-file", metavar="FILE", help="Read configuration from this file; it must exist.")
    mode = result.add_mutually_exclusive_group()
    mode.add_argument("--offline", action="store_true", help="Use fresh cached catalogs only; never contact the API.")
    mode.add_argument("--refresh-cache", action="store_true", help="Download fresh catalogs instead of using the cache.")
    result.add_argument("--list-consoles", action="store_true", help="List console names, formats and aliases, then exit.")
    return result


def resolve_path(value: str, base: Path) -> Path:
    path = Path(value).expanduser()
    return (path if path.is_absolute() else base / path).resolve()


def load_settings(args: argparse.Namespace, environ: Mapping[str, str] | None = None) -> Settings:
    environment = os.environ if environ is None else environ
    cwd = Path.cwd()
    checkout = Path(__file__).resolve().parents[2]
    source_root = checkout if (checkout / "pyproject.toml").is_file() else cwd
    project_dir = resolve_path(args.project_dir, cwd) if args.project_dir else source_root
    env_file = resolve_path(args.env_file, cwd) if args.env_file else project_dir / ".env"
    if args.env_file and not env_file.is_file():
        raise ValueError(f"Configuration file not found: {env_file}")
    values = dotenv_values(env_file, interpolate=False) if env_file.is_file() else {}

    def setting(cli_value: object, key: str, default: object) -> tuple[object, Path]:
        if cli_value is not None:
            return cli_value, cwd
        if key in environment:
            return environment[key], cwd
        if values.get(key) is not None:
            return values[key], env_file.parent
        return default, project_dir

    paths_value, paths_base = setting(args.paths, "RA_ROM_PATHS", ["roms"])
    if isinstance(paths_value, str):
        try:
            paths_value = json.loads(paths_value)
        except ValueError:
            raise ValueError('RA_ROM_PATHS must be a JSON list, for example ["roms"].') from None
    if not isinstance(paths_value, list) or not paths_value or any(
        not isinstance(value, str) or not value.strip() for value in paths_value
    ):
        raise ValueError("ROM paths must be a non-empty list of path strings.")
    enabled, _ = setting(args.log, "RA_LOG_ENABLED", True)
    if isinstance(enabled, str):
        normalized = enabled.strip().lower()
        if normalized not in {"true", "false", "1", "0", "yes", "no"}:
            raise ValueError("RA_LOG_ENABLED must be true or false.")
        enabled = normalized in {"true", "1", "yes"}
    log_dir, log_base = setting(args.log_path, "RA_LOG_DIR", "log")
    cache_dir, cache_base = setting(args.cache_dir, "RA_CACHE_DIR", "cache")
    key, _ = setting(args.api_key, "RA_API_KEY", "")
    return Settings(
        project_dir=project_dir,
        paths=tuple(resolve_path(value, paths_base) for value in paths_value),
        consoles=tuple(value.lower() for value in (args.consoles or ["all"])),
        api_key=str(key).strip(),
        log_enabled=bool(enabled),
        log_dir=resolve_path(str(log_dir), log_base),
        cache_dir=resolve_path(str(cache_dir), cache_base),
        offline=args.offline,
        refresh_cache=args.refresh_cache,
        default_roms=args.paths is None and "RA_ROM_PATHS" not in environment and values.get("RA_ROM_PATHS") is None,
    )