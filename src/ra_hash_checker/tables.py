from pathlib import Path

from rich import box
from rich.console import Console
from rich.table import Table
from rich.text import Text

from .models import CheckResult, Status
from .registry import BY_SLUG


def literal_text(value: str, style: str = "") -> Text:
    value = "".join(
        character.encode("unicode_escape").decode("ascii")
        if (ord(character) < 32 and character not in "\n\t") or 127 <= ord(character) <= 159
        else character
        for character in value
    )
    return Text(value, style=style)


def status_text(result: CheckResult) -> Text:
    if result.status == Status.SUPPORTED:
        count = result.games[0].achievements
        return Text(f"SUPPORTED\n{count} Achievements", style="green")
    labels = {
        Status.NO_ACHIEVEMENTS: ("NOT SUPPORTED\nNo achievements", "red"),
        Status.UNKNOWN_HASH: ("NOT SUPPORTED\nUnknown hash", "red"),
        Status.UNCHECKED: ("NOT CHECKED", "yellow"),
        Status.HASH_ERROR: ("HASH ERROR", "bold red"),
        Status.FORMAT_UNSUPPORTED: ("UNSUPPORTED FORMAT", "yellow"),
        Status.AMBIGUOUS_CONSOLE: ("AMBIGUOUS CONSOLE", "yellow"),
        Status.SCAN_ERROR: ("SCAN ERROR", "bold red"),
    }
    label, style = labels[result.status]
    return Text(label, style=style)


def game_text(result: CheckResult) -> Text:
    if result.games:
        game = result.games[0]
        text = literal_text(game.title, style=f"link {game.url}")
        text.append(f"\nID: {game.game_id}")
        return text
    if result.message:
        message = result.message
        if result.candidates and result.console is None:
            message += "\n" + ", ".join(result.candidates)
        return literal_text(message)
    return Text("-")


def display_path(result: CheckResult, roots: tuple[Path, ...]) -> str:
    path = Path(result.path)
    for root in roots:
        if path.is_relative_to(root):
            return str(path.relative_to(root))
    return str(path)


def print_table(console: Console, slug: str | None, results: list[CheckResult], roots: tuple[Path, ...]) -> None:
    name = BY_SLUG[slug].name if slug else "Unassigned"
    if console.width < 80:
        console.print(Text(f"{name} - RetroAchievements", style="bold cyan"))
        for result in results:
            console.print(literal_text(display_path(result, roots)))
            console.print(Text(result.hash or "-"))
            console.print(status_text(result))
            console.print(game_text(result))
            console.print()
        return
    table = Table(title=Text(f"{name} - RetroAchievements"), box=box.ASCII,
                  header_style="bold cyan", show_lines=True, expand=True)
    table.add_column("ROM File", min_width=9, overflow="fold")
    table.add_column("RA Hash", width=32, min_width=32, max_width=32, no_wrap=True)
    table.add_column("RA Status", width=18, min_width=18, overflow="fold")
    table.add_column("RA Game", min_width=8, overflow="fold")
    for result in results:
        table.add_row(literal_text(display_path(result, roots)), Text(result.hash or "-"), status_text(result), game_text(result))
    console.print(table)