"""Check or update the selected rcheevos sources using a full upstream commit."""

import argparse
import ast
import io
from pathlib import Path
import re
import sys
import tarfile
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = Path("src/ra_hash_checker")
VENDOR = PACKAGE / "_vendor/rcheevos"
FILES = (
    "LICENSE",
    "include/rc_consoles.h",
    "include/rc_export.h",
    "include/rc_hash.h",
    "src/rc_compat.c",
    "src/rc_compat.h",
    "src/rhash/cdreader.c",
    "src/rhash/hash_disc.c",
    "src/rhash/hash_rom.c",
    "src/rhash/hash.c",
    "src/rhash/md5.c",
    "src/rhash/md5.h",
    "src/rhash/rc_hash_internal.h",
    "test/test_framework.h",
    "test/rhash/data.c",
    "test/rhash/data.h",
    "test/rhash/mock_filereader.c",
    "test/rhash/mock_filereader.h",
    "test/rhash/test_cdreader.c",
    "test/rhash/test_hash_disc.c",
    "test/rhash/test_hash_rom.c",
    "test/rhash/test_hash.c",
)
MODERN_FILES = (
    "LICENSE",
    "include/rc_consoles.h",
    "include/rc_export.h",
    "include/rc_hash.h",
    "src/util/rc_compat.c",
    "src/util/rc_compat.h",
    "src/hash/rc_cdreader.c",
    "src/hash/rc_hash_disc.c",
    "src/hash/rc_hash_rom.c",
    "src/hash/rc_hash.c",
    "src/util/md5.c",
    "src/util/md5.h",
    "src/hash/rc_hash_internal.h",
    "test/test_framework.h",
    "test/hash/hash_data.c",
    "test/hash/hash_data.h",
    "test/hash/mock_filereader.c",
    "test/hash/mock_filereader.h",
    "test/hash/test_rc_cdreader.c",
    "test/hash/test_rc_hash_disc.c",
    "test/hash/test_rc_hash_rom.c",
    "test/hash/test_rc_hash.c",
)


def commit_sha(value: str) -> str:
    if not re.fullmatch(r"[0-9a-fA-F]{40}", value):
        raise argparse.ArgumentTypeError("Expected a full 40-character commit SHA.")
    return value.lower()


def load_metadata(root: Path) -> tuple[str, dict[Path, str]]:
    engine_path = root / PACKAGE / "__init__.py"
    readme_path = root / PACKAGE / "_vendor/README.md"
    engine = engine_path.read_bytes().decode("utf-8")
    readme = readme_path.read_bytes().decode("utf-8")
    pins = [
        node.value.value
        for node in ast.parse(engine).body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "ENGINE_COMMIT" for target in node.targets)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    ]
    documented = re.findall(r"(?m)^Pinned commit: `([0-9a-f]{40})`\.\r?$", readme)
    if len(pins) != 1 or not re.fullmatch(r"[0-9a-f]{40}", pins[0]):
        raise ValueError("ENGINE_COMMIT must contain one full commit SHA.")
    pin = pins[0]
    if documented != [pin]:
        raise ValueError("ENGINE_COMMIT and the vendor README pin must match.")
    metadata = {engine_path: engine, readme_path: readme}
    if any(text.count(pin) != 1 for text in metadata.values()):
        raise ValueError("Expected exactly one commit reference in each metadata file.")
    return pin, metadata


def download_sources(commit: str) -> dict[str, bytes]:
    url = f"https://codeload.github.com/RetroAchievements/rcheevos/tar.gz/{commit}"
    with urlopen(url, timeout=30) as response:
        archive_data = response.read()
    sources = {}
    with tarfile.open(fileobj=io.BytesIO(archive_data), mode="r:gz") as archive:
        prefix = f"rcheevos-{commit}/"
        files = MODERN_FILES if any(name.startswith(prefix + "src/hash/") for name in archive.getnames()) else FILES
        for name in files:
            try:
                member = archive.getmember(prefix + name)
            except KeyError:
                raise ValueError(f"Upstream archive is missing {name}.") from None
            if not member.isfile():
                raise ValueError(f"Upstream archive entry is not a regular file: {name}.")
            source = archive.extractfile(member)
            if source is None:
                raise ValueError(f"Cannot read upstream file: {name}.")
            with source:
                sources[name] = source.read()
    return sources


def run(root: Path, update: str | None) -> int:
    pin, metadata = load_metadata(root)
    vendor = root / VENDOR
    current_sources = download_sources(pin)
    extras = sorted(
        path.relative_to(vendor).as_posix()
        for path in vendor.rglob("*")
        if path.is_file() and path.relative_to(vendor).as_posix() not in current_sources
    )
    if update and extras:
        raise ValueError(f"Unexpected vendored files; review them before updating: {', '.join(extras)}")
    commit = update or pin
    sources = download_sources(commit) if commit != pin else current_sources
    if update:
        for name, content in sources.items():
            destination = vendor / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(content)
        for name in current_sources.keys() - sources.keys():
            (vendor / name).unlink(missing_ok=True)
        for path, text in metadata.items():
            path.write_bytes(text.replace(pin, commit).encode("utf-8"))
        print(f"Updated {len(sources)} vendored files to rcheevos {commit}.")
        print("Rebuild the native extension and run the Python and upstream C tests before committing.")
        return 0
    differences = [f"UNEXPECTED {name}" for name in extras]
    for name, content in sources.items():
        local = vendor / name
        if not local.is_file():
            differences.append(f"MISSING {name}")
        elif local.read_bytes().replace(b"\r\n", b"\n") != content.replace(b"\r\n", b"\n"):
            differences.append(f"CHANGED {name}")
    if differences:
        print("\n".join(differences))
        return 1
    print(f"OK: {len(sources)} vendored files match rcheevos {commit} (CRLF/LF ignored).")
    return 0


def main(argv: list[str] | None = None, *, root: Path = ROOT) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="Compare against the pinned commit without writing (default).")
    mode.add_argument("--update", type=commit_sha, metavar="COMMIT", help="Overwrite the selected sources and update both pins.")
    args = parser.parse_args(argv)
    try:
        return run(root, args.update)
    except (OSError, ValueError, SyntaxError, tarfile.TarError) as error:
        print(f"Vendor error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())