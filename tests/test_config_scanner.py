from pathlib import Path

import pytest

from ra_hash_checker.config import load_settings, parser


def test_defaults_and_cli(tmp_path):
    args = parser().parse_args(["--project-dir", str(tmp_path)])
    settings = load_settings(args, {})
    assert settings.paths == (tmp_path / "roms",)
    assert settings.log_dir == tmp_path / "log"
    assert settings.log_enabled
    args = parser().parse_args(["--paths", str(tmp_path), "--no-log", "--api-key", "private"])
    settings = load_settings(args, {})
    assert settings.paths == (tmp_path,)
    assert not settings.log_enabled
    assert "private" not in repr(settings)
    assert "private" not in str(settings.public_options())


def test_env_priority_and_path_base(tmp_path):
    env = tmp_path / ".env"
    env.write_text('RA_API_KEY=file-key\nRA_ROM_PATHS=["games"]\nRA_LOG_ENABLED=false\n', encoding="utf-8")
    args = parser().parse_args(["--env-file", str(env)])
    settings = load_settings(args, {"RA_API_KEY": "process-key"})
    assert settings.api_key == "process-key"
    assert settings.paths == (tmp_path / "games",)
    assert not settings.log_enabled


@pytest.mark.parametrize("value", ["x", '"roms"', "[]", "[false]", '[""]'])
def test_invalid_paths(value):
    with pytest.raises(ValueError):
        load_settings(parser().parse_args([]), {"RA_ROM_PATHS": value})


def test_cli_replaces_env_paths(tmp_path):
    args = parser().parse_args(["--paths", str(tmp_path), "--paths", str(tmp_path / "second")])
    settings = load_settings(args, {"RA_ROM_PATHS": "invalid"})
    assert settings.paths == (tmp_path, tmp_path / "second")


def test_missing_explicit_env(tmp_path):
    with pytest.raises(ValueError, match="Configuration file not found"):
        load_settings(parser().parse_args(["--env-file", str(tmp_path / "missing")]), {})


def test_help_is_english_and_describes_options():
    help_text = parser().format_help()
    assert "Identify ROMs using official RetroAchievements hashes." in help_text
    assert "Folders to search recursively" in help_text
    assert "--consoles CONSOLE" in help_text
    assert "--env-file FILE" in help_text
    assert "never contact the API" in help_text


def test_registry_scope_and_aliases():
    from ra_hash_checker.registry import CONSOLES, select_consoles

    assert len(CONSOLES) == 50
    assert select_consoles(("ds",))[0].console_id == 18
    assert len(select_consoles(("all",))) == 50
    assert len(select_consoles(("ds", "nds"))) == 1
    assert all(console.console_id not in {62, 78, 19} for console in CONSOLES)
    for names in [("all", "ds"), ("3ds",)]:
        with pytest.raises(ValueError):
            select_consoles(names)


def test_scanner_ambiguity_and_deduplication(tmp_path):
    from ra_hash_checker.models import Status
    from ra_hash_checker.registry import select_consoles
    from ra_hash_checker.scanner import scan

    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / "game.ISO").touch()
    (nested / "game.NDS").touch()
    results = list(scan((tmp_path, nested), select_consoles(("all",))))
    assert len(results) == 2
    assert results[0].status == Status.AMBIGUOUS_CONSOLE
    assert results[1].console.slug == "nintendo_ds"
    results = list(scan((tmp_path,), select_consoles(("ps2", "psp"))))
    assert results[0].status == Status.AMBIGUOUS_CONSOLE
    results = list(scan((tmp_path,), select_consoles(("ps2",))))
    assert results[0].console.slug == "playstation_2"


def test_scanner_tracks_and_missing_tracks(tmp_path):
    from ra_hash_checker.models import Status
    from ra_hash_checker.registry import select_consoles
    from ra_hash_checker.scanner import scan

    cue = tmp_path / "game.cue"
    cue.write_text('FILE "game track.bin" BINARY\n TRACK 01 MODE1/2352\n INDEX 01 00:00:00\n')
    (tmp_path / "game track.bin").touch()
    consoles = select_consoles(("ps1",))
    results = list(scan((tmp_path,), consoles))
    assert len(results) == 1
    assert results[0].path == cue
    assert results[0].status is None
    (tmp_path / "game track.bin").unlink()
    assert list(scan((tmp_path,), consoles))[0].status == Status.HASH_ERROR


def test_scanner_unsupported_and_arcade(tmp_path):
    from ra_hash_checker.models import Status
    from ra_hash_checker.registry import select_consoles
    from ra_hash_checker.scanner import scan

    (tmp_path / "game.chd").touch()
    (tmp_path / "galaga.zip").touch()
    results = list(scan((tmp_path,), select_consoles(("all",))))
    assert all(result.status == Status.FORMAT_UNSUPPORTED for result in results)
    results = list(scan((tmp_path,), select_consoles(("arcade",)), arcade_explicit=True))
    assert results[0].console.slug == "arcade"
    assert results[0].status is None


def test_scanner_missing_root(tmp_path):
    from ra_hash_checker.models import Status
    from ra_hash_checker.registry import select_consoles
    from ra_hash_checker.scanner import scan

    assert list(scan((tmp_path / "missing",), select_consoles(("ds",))))[0].status == Status.SCAN_ERROR


def test_nkit_not_treated_as_uncompressed_iso(tmp_path):
    from ra_hash_checker.models import Status
    from ra_hash_checker.registry import select_consoles
    from ra_hash_checker.scanner import scan

    (tmp_path / "game.nkit.iso").touch()
    result = list(scan((tmp_path,), select_consoles(("gamecube",))))[0]
    assert result.status == Status.FORMAT_UNSUPPORTED