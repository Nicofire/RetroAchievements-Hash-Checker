import os
import re
import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from .models import ConsoleSpec, Status
from .registry import CONSOLES, DISC_CONSOLES, UNSUPPORTED_EXTENSIONS


@dataclass(frozen=True)
class RomCandidate:
    path: Path
    console: ConsoleSpec | None = None
    candidates: tuple[str, ...] = ()
    status: Status | None = None
    message: str = ""


def descriptor_references(path: Path) -> list[Path]:
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    names: list[str] = []
    if path.suffix.lower() == ".cue":
        for line in text.splitlines():
            match = re.match(r'^\s*FILE\s+(?:"([^"]+)"|(\S+))\s+', line, re.IGNORECASE)
            if match:
                names.append(match.group(1) or match.group(2))
    else:
        for line in text.splitlines()[1:]:
            fields = shlex.split(line, posix=False)
            if fields:
                if len(fields) != 6:
                    raise ValueError("Invalid GDI track descriptor.")
                names.append(fields[4].strip('"'))
    if not names:
        raise ValueError("Disc descriptor does not reference any track files.")
    return [(path.parent / name.replace("\\", "/")).resolve() for name in names]


def scan(paths: tuple[Path, ...], consoles: tuple[ConsoleSpec, ...], arcade_explicit: bool = False) -> Iterator[RomCandidate]:
    files: dict[Path, Path] = {}
    errors: list[RomCandidate] = []

    def scan_error(error: OSError) -> None:
        errors.append(RomCandidate(Path(error.filename or "?"), status=Status.SCAN_ERROR, message="Directory could not be read."))

    for root in paths:
        if not root.is_dir():
            errors.append(RomCandidate(root, status=Status.SCAN_ERROR, message="Search directory does not exist or is not accessible."))
            continue
        for folder, directories, filenames in os.walk(root, followlinks=False, onerror=scan_error):
            directories[:] = sorted(name for name in directories if not (Path(folder) / name).is_symlink())
            for name in sorted(filenames):
                path = Path(folder) / name
                try:
                    files.setdefault(path.resolve(), path)
                except (OSError, RuntimeError):
                    errors.append(RomCandidate(path, status=Status.SCAN_ERROR, message="File path could not be resolved."))
    referenced: set[Path] = set()
    descriptor_errors: dict[Path, str] = {}
    disc_selected = any(console.console_id in DISC_CONSOLES for console in consoles)
    if disc_selected:
        for resolved, path in files.items():
            if path.suffix.lower() in {".cue", ".gdi"}:
                try:
                    tracks = descriptor_references(path)
                    referenced.update(tracks)
                    if any(not track.is_file() for track in tracks):
                        descriptor_errors[resolved] = "At least one referenced track file is missing."
                except (OSError, ValueError):
                    descriptor_errors[resolved] = "Disc descriptor could not be read."
    yield from errors
    all_extensions = {extension for console in CONSOLES for extension in console.extensions}
    for resolved in sorted(files, key=lambda value: str(value).casefold()):
        path = files[resolved]
        extension = path.suffix.lower()
        if resolved in referenced:
            continue
        if path.name.lower().endswith(".nkit.iso"):
            yield RomCandidate(path, status=Status.FORMAT_UNSUPPORTED, message="NKit containers are not supported; an uncompressed image is required.")
            continue
        matches = tuple(console for console in consoles if extension in console.extensions)
        if extension in {".zip", ".7z"} and not arcade_explicit:
            yield RomCandidate(path, status=Status.FORMAT_UNSUPPORTED, message="Archive filename hashing requires an explicit Arcade console selection.")
            continue
        if not matches:
            if extension in UNSUPPORTED_EXTENSIONS:
                yield RomCandidate(path, status=Status.FORMAT_UNSUPPORTED, message="Container/format is not supported by this build; no conversion is performed.")
            elif extension not in all_extensions:
                continue
            continue
        names = tuple(console.slug for console in matches)
        if len(matches) > 1:
            yield RomCandidate(path, candidates=names, status=Status.AMBIGUOUS_CONSOLE, message="Select a single matching console with --consoles.")
        elif resolved in descriptor_errors:
            yield RomCandidate(path, matches[0], names, Status.HASH_ERROR, descriptor_errors[resolved])
        else:
            yield RomCandidate(path, matches[0], names)