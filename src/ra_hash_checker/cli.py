from pathlib import Path
from typing import Sequence

from rich.console import Console
from rich.text import Text

from .config import load_settings, parser
from .models import utc_now
from .output import print_report
from .registry import CONSOLES, select_consoles
from .reports import write_reports
from .runner import run
from .tables import literal_text


def main(argv: Sequence[str] | None = None) -> int:
    argument_parser = parser()
    args = argument_parser.parse_args(argv)
    console = Console()
    if args.list_consoles:
        for spec in CONSOLES:
            console.print(Text(f"{spec.slug}: {spec.name}\n  {', '.join(spec.extensions)}; Aliases: {', '.join(spec.aliases) or '-'}"))
        return 0
    try:
        settings = load_settings(args)
        select_consoles(settings.consoles)
    except (ValueError, OSError):
        console.print("Invalid configuration. Check paths, the RA_ROM_PATHS JSON list and console names.", style="red")
        return 2
    try:
        from . import _rcheevos
    except ImportError:
        console.print("Native hash engine is missing. Install the package with pip install -e .", style="red")
        return 2
    report = run(settings)
    locations: tuple[Path, Path] | None = None
    if settings.log_enabled:
        for attempt in range(2):
            try:
                locations = write_reports(report, settings.log_dir, console.width)
                break
            except OSError:
                report.warnings.append("Text/JSON reports could not be written.")
                break
            except KeyboardInterrupt:
                report.completed = False
                report.ended_at = utc_now()
                if attempt:
                    report.warnings.append("Report writing was interrupted again.")
    print_report(report, console)
    if locations:
        console.print(literal_text("Reports: " + ", ".join(str(path) for path in locations)))
    return report.exit_code