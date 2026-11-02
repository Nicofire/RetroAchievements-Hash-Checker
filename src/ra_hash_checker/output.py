import io
from pathlib import Path

from rich.console import Console
from rich.text import Text

from .models import RunReport
from .registry import CONSOLES
from .tables import literal_text, print_table


def print_report(report: RunReport, console: Console) -> None:
    roots = tuple(Path(value) for value in report.options.get("paths", []))
    for slug in [*(spec.slug for spec in CONSOLES), None]:
        results = [result for result in report.results if result.console == slug]
        if results:
            print_table(console, slug, results, roots)
    if not report.results:
        console.print("No matching ROM files found.")
    for warning in report.warnings:
        console.print(literal_text("Warning: " + warning, style="yellow"))
    label = "Aborted" if not report.completed else "Completed"
    counts = ", ".join(f"{status}: {count}" for status, count in report.counts.items())
    console.print(Text(f"{label}: {len(report.results)} files" + (f" ({counts})" if counts else "")))


def render_text(report: RunReport, width: int = 120) -> str:
    stream = io.StringIO()
    console = Console(file=stream, width=width, force_terminal=False, color_system=None, no_color=True)
    print_report(report, console)
    return stream.getvalue()