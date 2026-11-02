"""Regenerate documentation previews with synthetic data and the real renderer."""

import argparse
import io
from pathlib import Path

from rich.console import Console

from ra_hash_checker.models import CheckResult, GameInfo, RunReport, Status
from ra_hash_checker.output import print_report, render_text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Check that previews are up to date.")
    args = parser.parse_args()
    report = RunReport(
        {"paths": ["demo-roms"]},
        results=[
            CheckResult(
                "demo-roms/Example Adventure.gba", "game_boy_advance", Status.SUPPORTED,
                "1234567890abcdef1234567890abcdef",
                [GameInfo(100001, "Example Adventure", 42)],
            ),
            CheckResult(
                "demo-roms/Example Puzzle.gba", "game_boy_advance", Status.NO_ACHIEVEMENTS,
                "abcdef0123456789abcdef0123456789",
                [GameInfo(100002, "Example Puzzle", 0)],
            ),
            CheckResult(
                "demo-roms/Example Quest.nds", "nintendo_ds", Status.UNKNOWN_HASH,
                "fedcba9876543210fedcba9876543210",
            ),
        ],
    )
    console = Console(file=io.StringIO(), width=120, record=True, force_terminal=True)
    print_report(report, console)
    preview = console.export_svg(
        title="RetroAchievements Hash Checker | Synthetic demo",
        unique_id="ra-hash-checker-demo",
    )
    examples = f"""# Terminal Examples

[Back to the README](../README.md#terminal-preview)

These previews use the application's actual terminal renderer with **synthetic
data**. Filenames, hashes, game IDs, titles, and achievement counts are illustrative,
not real catalog entries or scan results. No ROMs, API key, personal paths, or
network access are needed to generate them.

## Standard Terminal

Each console has its own table. This 120-column example shows a supported game,
a known game without achievements, and an unknown hash.

![Terminal tables with supported, no-achievement, and unknown-hash examples](images/terminal-preview.svg)

Copyable plain-text output (120 columns):

```text
{render_text(report, 120).rstrip()}
```

`SUPPORTED` includes the achievement count. Both a known game without achievements
and an unknown hash display `NOT SUPPORTED`, with a different explanation below.
An unknown hash does not mean the ROM is invalid.

## Narrow Terminal

Below 80 columns, the same results become a compact list. This 54-column example
keeps every 32-character hash intact:

```text
{render_text(report, 54).rstrip()}
```

The summary counts refer to the JSON status names. These three example statuses
all allow exit code `0`; errors and incomplete checks are documented in
[Results and Reports](../README.md#results-and-reports).

## Try It on Your Library

After [installation and configuration](../README.md#quick-start), run:

```bash
ra-hash-checker --paths "roms" --consoles gba ds
```

This command scans your own files; it does not recreate the synthetic results above.
By default, it also writes plain-text and JSON reports into `log/`.

## Regenerate the Previews

From the repository root, with the project installed and its virtual environment
activated:

```bash
python docs/render_examples.py
python docs/render_examples.py --check
```

The generator calls `print_report` and `render_text` from the application. It only
writes this page and the SVG preview, never reads `.env`, and never scans ROM folders
or contacts RetroAchievements. The SVG is a vector terminal capture, not a desktop
screenshot. Changes to the renderer or the installed Rich version can change it.
"""
    directory = Path(__file__).resolve().parent
    outputs = {
        directory / "images" / "terminal-preview.svg": preview,
        directory / "examples.md": examples,
    }
    for path, content in outputs.items():
        if args.check:
            if not path.is_file() or path.read_text(encoding="utf-8") != content:
                print(f"Out of date: {path.relative_to(directory)}")
                return 1
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8", newline="\n")
    print("Documentation previews are up to date." if args.check else "Documentation previews generated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())