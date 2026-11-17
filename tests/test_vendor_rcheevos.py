import importlib.util
import io
from pathlib import Path
import tarfile
from urllib.error import URLError

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/vendor_rcheevos.py"
SPEC = importlib.util.spec_from_file_location("vendor_rcheevos", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
vendor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(vendor)
DOWNLOAD_SOURCES = vendor.download_sources
PIN = "1" * 40
NEW_PIN = "2" * 40


@pytest.fixture
def checkout(tmp_path, monkeypatch):
    package = tmp_path / vendor.PACKAGE
    (package / "_vendor").mkdir(parents=True)
    (package / "__init__.py").write_bytes(f'__version__ = "0.1.0"\r\nENGINE_COMMIT = "{PIN}"\r\n'.encode())
    (package / "_vendor/README.md").write_bytes(f"# Vendor\r\n\r\nPinned commit: `{PIN}`.\r\n".encode())
    sources = {name: f"upstream {name}\n".encode() for name in vendor.FILES}
    for name, content in sources.items():
        path = tmp_path / vendor.VENDOR / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    monkeypatch.setattr(vendor, "download_sources", lambda commit: sources)
    return tmp_path, sources


def snapshot(root):
    return {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()}


def test_check_matches_without_writing(checkout, capsys):
    root, _ = checkout
    before = snapshot(root)
    assert vendor.main(["--check"], root=root) == 0
    assert "vendored files match rcheevos" in capsys.readouterr().out
    assert snapshot(root) == before


def test_check_ignores_only_checkout_line_endings(checkout, capsys):
    root, sources = checkout
    for name, content in sources.items():
        (root / vendor.VENDOR / name).write_bytes(content.replace(b"\n", b"\r\n"))
    before = snapshot(root)
    assert vendor.main(["--check"], root=root) == 0
    assert "CRLF/LF ignored" in capsys.readouterr().out
    assert snapshot(root) == before
    (root / vendor.VENDOR / "LICENSE").write_bytes(b"upstream LICENSE \r\n")
    assert vendor.main(["--check"], root=root) == 1
    assert "CHANGED LICENSE" in capsys.readouterr().out


def test_default_check_reports_changed_missing_and_extra_files(checkout, capsys):
    root, _ = checkout
    (root / vendor.VENDOR / "LICENSE").write_bytes(b"modified")
    (root / vendor.VENDOR / "include/rc_hash.h").unlink()
    (root / vendor.VENDOR / "extra.c").touch()
    before = snapshot(root)
    assert vendor.main([], root=root) == 1
    output = capsys.readouterr().out
    assert "CHANGED LICENSE" in output
    assert "MISSING include/rc_hash.h" in output
    assert "UNEXPECTED extra.c" in output
    assert snapshot(root) == before


def test_update_sources_and_both_pins_preserving_metadata_format(checkout):
    root, sources = checkout
    before = snapshot(root)
    sources["LICENSE"] = b"new license\n"
    (root / vendor.VENDOR / "include/rc_hash.h").unlink()
    assert vendor.main(["--update", NEW_PIN], root=root) == 0
    for name, content in sources.items():
        assert (root / vendor.VENDOR / name).read_bytes() == content
    for relative in (vendor.PACKAGE / "__init__.py", vendor.PACKAGE / "_vendor/README.md"):
        assert (root / relative).read_bytes() == before[relative].replace(PIN.encode(), NEW_PIN.encode())
    assert vendor.main(["--check"], root=root) == 0


@pytest.mark.parametrize("mode", [["--check"], ["--update", NEW_PIN]])
def test_download_failure_never_changes_checkout(checkout, monkeypatch, capsys, mode):
    root, _ = checkout
    before = snapshot(root)

    def fail(commit):
        raise URLError("offline")

    monkeypatch.setattr(vendor, "download_sources", fail)
    assert vendor.main(mode, root=root) == 2
    assert "offline" in capsys.readouterr().err
    assert snapshot(root) == before


def test_inconsistent_pin_is_rejected_before_download(checkout, monkeypatch):
    root, _ = checkout
    (root / vendor.PACKAGE / "_vendor/README.md").write_text(f"Pinned commit: `{NEW_PIN}`.\n")
    monkeypatch.setattr(vendor, "download_sources", lambda commit: pytest.fail("Unexpected download"))
    before = snapshot(root)
    assert vendor.main(["--check"], root=root) == 2
    assert snapshot(root) == before


def test_update_refuses_unexpected_files(checkout):
    root, _ = checkout
    (root / vendor.VENDOR / "local.c").touch()
    before = snapshot(root)
    assert vendor.main(["--update", NEW_PIN], root=root) == 2
    assert snapshot(root) == before


@pytest.mark.parametrize("commit", ["main", "v1.0", "abc123", "g" * 40])
def test_update_requires_full_commit(commit, checkout):
    root, _ = checkout
    before = snapshot(root)
    with pytest.raises(SystemExit) as error:
        vendor.main(["--update", commit], root=root)
    assert error.value.code == 2
    assert snapshot(root) == before


def archive_bytes(commit, *, files=vendor.FILES, missing=None, symlink=None):
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        for name in files:
            if name == missing:
                continue
            entry = tarfile.TarInfo(f"rcheevos-{commit}/{name}")
            if name == symlink:
                entry.type = tarfile.SYMTYPE
                entry.linkname = "../../outside"
                archive.addfile(entry)
            else:
                content = f"content {name}\n".encode()
                entry.size = len(content)
                archive.addfile(entry, io.BytesIO(content))
    return buffer.getvalue()


@pytest.mark.parametrize("files", [vendor.FILES, vendor.MODERN_FILES])
def test_download_selects_exact_manifest(monkeypatch, files):
    def open_archive(url, timeout):
        assert url == f"https://codeload.github.com/RetroAchievements/rcheevos/tar.gz/{PIN}"
        assert timeout == 30
        return io.BytesIO(archive_bytes(PIN, files=files))

    monkeypatch.setattr(vendor, "urlopen", open_archive)
    sources = vendor.download_sources(PIN)
    assert set(sources) == set(files)
    assert sources["LICENSE"] == b"content LICENSE\n"


@pytest.mark.parametrize("files", [vendor.FILES, vendor.MODERN_FILES])
@pytest.mark.parametrize("problem", [{"missing": "LICENSE"}, {"symlink": "LICENSE"}])
def test_invalid_archive_never_changes_checkout(checkout, monkeypatch, problem, files):
    root, _ = checkout
    monkeypatch.setattr(vendor, "download_sources", DOWNLOAD_SOURCES)

    def open_archive(url, timeout):
        if url.endswith(PIN):
            return io.BytesIO(archive_bytes(PIN))
        return io.BytesIO(archive_bytes(NEW_PIN, files=files, **problem))

    monkeypatch.setattr(vendor, "urlopen", open_archive)
    before = snapshot(root)
    assert vendor.main(["--update", NEW_PIN], root=root) == 2
    assert snapshot(root) == before


@pytest.mark.parametrize("old_files,new_files", [(vendor.FILES, vendor.MODERN_FILES), (vendor.MODERN_FILES, vendor.FILES)])
def test_update_migrates_layout_and_check_uses_new_manifest(checkout, monkeypatch, old_files, new_files):
    root, _ = checkout
    for old_name, new_name in zip(vendor.FILES, old_files, strict=True):
        if old_name != new_name:
            destination = root / vendor.VENDOR / new_name
            destination.parent.mkdir(parents=True, exist_ok=True)
            (root / vendor.VENDOR / old_name).rename(destination)
    monkeypatch.setattr(vendor, "download_sources", DOWNLOAD_SOURCES)

    def open_archive(url, timeout):
        if url.endswith(PIN):
            return io.BytesIO(archive_bytes(PIN, files=old_files))
        assert url.endswith(NEW_PIN)
        return io.BytesIO(archive_bytes(NEW_PIN, files=new_files))

    monkeypatch.setattr(vendor, "urlopen", open_archive)
    assert vendor.main(["--update", NEW_PIN], root=root) == 0
    for name in new_files:
        assert (root / vendor.VENDOR / name).read_bytes() == f"content {name}\n".encode()
    for name in set(old_files) - set(new_files):
        assert not (root / vendor.VENDOR / name).exists()
    assert vendor.main(["--check"], root=root) == 0