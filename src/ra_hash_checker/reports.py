import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from . import ENGINE_COMMIT, __version__
from .models import RunReport
from .output import render_text


def report_payload(report: RunReport) -> dict[str, object]:
    results = []
    for result in report.results:
        row = asdict(result)
        row["games"] = [{**asdict(game), "url": game.url} for game in result.games]
        results.append(row)
    return {
        "schema_version": 1,
        "tool_version": __version__,
        "engine": {"name": "rcheevos", "commit": ENGINE_COMMIT,
                   "features": ["ROM", "DISC"], "excluded": ["ENCRYPTED", "ZIP_CONTENTS"]},
        "started_at": report.started_at,
        "ended_at": report.ended_at,
        "completed": report.completed,
        "aborted": not report.completed,
        "exit_code": report.exit_code,
        "options": report.options,
        "counts": report.counts,
        "warnings": report.warnings,
        "results": results,
    }


def write_reports(report: RunReport, directory: Path, width: int = 120) -> tuple[Path, Path]:
    directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    name = f"run-{stamp}-{uuid4().hex[:8]}"
    text_path = directory / (name + ".log")
    json_path = directory / (name + ".json")
    created: list[Path] = []
    try:
        with text_path.open("x", encoding="utf-8") as stream:
            created.append(text_path)
            stream.write(render_text(report, width))
        with json_path.open("x", encoding="utf-8") as stream:
            created.append(json_path)
            json.dump(report_payload(report), stream, ensure_ascii=True, indent=2)
            stream.write("\n")
    except BaseException:
        for path in created:
            try:
                path.unlink()
            except OSError:
                pass
        raise
    return text_path, json_path