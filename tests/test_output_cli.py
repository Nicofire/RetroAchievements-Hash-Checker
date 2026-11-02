import json

import pytest

from ra_hash_checker.cache import Catalog
from ra_hash_checker.cli import main
from ra_hash_checker.config import Settings
from ra_hash_checker.models import CheckResult, GameInfo, RunReport, Status
from ra_hash_checker.output import render_text
from ra_hash_checker.reports import report_payload, write_reports
from ra_hash_checker.runner import run
from ra_hash_checker.tables import status_text

HASH = "1234567890abcdef" * 2


def sample_report():
    report = RunReport({"paths": ["/games"]})
    report.results = [
        CheckResult("/games/[red]ROM[/red].nds", "nintendo_ds", Status.SUPPORTED, HASH,
                    [GameInfo(1, "A very long [bold]title[/bold] " * 5, 100)]),
        CheckResult("/games/other.gb", "game_boy", Status.UNKNOWN_HASH, HASH),
    ]
    return report


@pytest.mark.parametrize("width", [40, 80, 120, 180])
def test_render_complete_hash_and_no_escapes(width):
    text = render_text(sample_report(), width)
    assert text.count(HASH) == 2
    assert "\x1b" not in text
    assert max(map(len, text.splitlines())) <= width
    assert "Nintendo DS - RetroAchievements" in text
    assert "Game Boy - RetroAchievements" in text
    if width == 180:
        assert "[red]" in text
        assert "[bold]title[/bold]" in text


@pytest.mark.parametrize("status,label", [
    (Status.SUPPORTED, "SUPPORTED\n100 Achievements"),
    (Status.NO_ACHIEVEMENTS, "NOT SUPPORTED\nNo achievements"),
    (Status.UNKNOWN_HASH, "NOT SUPPORTED\nUnknown hash"),
    (Status.UNCHECKED, "NOT CHECKED"),
    (Status.HASH_ERROR, "HASH ERROR"),
    (Status.FORMAT_UNSUPPORTED, "UNSUPPORTED FORMAT"),
    (Status.AMBIGUOUS_CONSOLE, "AMBIGUOUS CONSOLE"),
    (Status.SCAN_ERROR, "SCAN ERROR"),
])
def test_status_labels_are_english(status, label):
    result = sample_report().results[0]
    result.status = status
    assert status_text(result).plain == label


def test_english_report_headings_and_summaries():
    text = render_text(sample_report(), 120)
    assert all(heading in text for heading in ("ROM File", "RA Hash", "RA Status", "RA Game"))
    assert "Completed: 2 files" in text
    report = RunReport({"paths": []}, completed=False, warnings=["Example warning."])
    text = render_text(report)
    assert "No matching ROM files found." in text
    assert "Warning: Example warning." in text
    assert "Aborted: 0 files" in text


def test_report_json_and_collision_safety(tmp_path):
    report = sample_report()
    first = write_reports(report, tmp_path)
    second = write_reports(report, tmp_path)
    assert first != second
    payload = json.loads(first[1].read_text(encoding="utf-8"))
    assert payload["counts"] == report.counts
    assert payload["results"][0]["games"][0]["url"].endswith("/game/1")
    assert "api_key" not in str(payload)
    assert "\x1b" not in first[0].read_text(encoding="utf-8")


class FakeStore:
    def __init__(self):
        self.calls = []

    def get(self, console_id):
        self.calls.append(console_id)
        return Catalog({}, "cache", "2026-01-01T00:00:00+00:00")


def test_runner_only_needed_catalogs(tmp_path):
    (tmp_path / "game.gb").write_bytes(b"test ROM")
    (tmp_path / "ambiguous.iso").touch()
    (tmp_path / "invalid.nds").write_bytes(b"bad")
    settings = Settings(tmp_path, (tmp_path,), log_enabled=False)
    store = FakeStore()
    report = run(settings, store)
    assert store.calls == [4]
    assert report.counts == {"AMBIGUOUS_CONSOLE": 1, "HASH_ERROR": 1, "UNKNOWN_HASH": 1}
    assert report.exit_code == 1


def test_runner_abort_keeps_partial_results(tmp_path):
    (tmp_path / "game.gb").write_bytes(b"data")

    class AbortedStore:
        def get(self, console_id):
            raise KeyboardInterrupt

    report = run(Settings(tmp_path, (tmp_path,)), AbortedStore())
    assert report.exit_code == 130
    assert report.results[0].hash is not None
    assert not report.completed
    assert report_payload(report)["aborted"]


def test_help_and_list_have_no_side_effects(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert main(["--list-consoles", "--env-file", "missing"]) == 0
    with pytest.raises(SystemExit) as result:
        main(["--help"])
    assert result.value.code == 0
    assert not list(tmp_path.iterdir())


def test_cli_no_log_and_empty_run(tmp_path, monkeypatch):
    monkeypatch.delenv("RA_API_KEY", raising=False)
    assert main(["--project-dir", str(tmp_path), "--paths", str(tmp_path), "--no-log", "--offline"]) == 0
    assert not (tmp_path / "log").exists()


def test_cli_reports_and_usage_error(tmp_path):
    assert main(["--project-dir", str(tmp_path), "--paths", str(tmp_path), "--offline"]) == 0
    assert len(list((tmp_path / "log").glob("*.json"))) == 1
    assert main(["--consoles", "3ds"]) == 2


def test_cli_report_failure_changes_exit(tmp_path, monkeypatch):
    def fail(*args):
        raise PermissionError("test")

    monkeypatch.setattr("ra_hash_checker.cli.write_reports", fail)
    assert main(["--project-dir", str(tmp_path), "--paths", str(tmp_path)]) == 1


def test_abort_during_reporting_writes_aborted_report(tmp_path, monkeypatch):
    calls = []

    def interrupt_once(*args):
        calls.append(1)
        if len(calls) == 1:
            raise KeyboardInterrupt
        return write_reports(*args)

    monkeypatch.setattr("ra_hash_checker.cli.write_reports", interrupt_once)
    assert main(["--project-dir", str(tmp_path), "--paths", str(tmp_path)]) == 130
    payload = json.loads(next((tmp_path / "log").glob("*.json")).read_text(encoding="utf-8"))
    assert payload["aborted"]


@pytest.mark.parametrize("width", [40, 80, 120])
def test_incoming_control_characters_cannot_control_terminal(width):
    report = sample_report()
    report.results[0].path = "/games/evil\x1b[31m.nds"
    report.results[0].games = [GameInfo(1, "title\x1b]8;;https://invalid\x07\x9b31m", 1)]
    report.warnings.append("warning\x1b[2J")
    text = render_text(report, width)
    assert not any(character in text for character in ["\x1b", "\x07", "\x9b"])