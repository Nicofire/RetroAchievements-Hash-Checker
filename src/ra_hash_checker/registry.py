from .consoles import CONSOLES
from .models import ConsoleSpec

BY_SLUG = {console.slug: console for console in CONSOLES}
BY_ALIAS = {
    alias.lower(): console
    for console in CONSOLES
    for alias in (console.slug, *console.aliases)
}
DISC_CONSOLES = frozenset({43, 77, 40, 16, 76, 49, 56, 39, 9, 12, 21, 41})
UNSUPPORTED_EXTENSIONS = frozenset({".chd", ".cso", ".rvz", ".wbfs", ".pbp", ".ccd", ".m3u", ".smd", ".7z", ".zip", ".unf", ".unif", ".arduboy", ".gcz", ".ciso"})


def select_consoles(names: tuple[str, ...]) -> tuple[ConsoleSpec, ...]:
    if "all" in names:
        if set(names) != {"all"}:
            raise ValueError("'all' cannot be combined with individual consoles.")
        return CONSOLES
    chosen: set[str] = set()
    for name in names:
        console = BY_ALIAS.get(name.lower())
        if console is None:
            raise ValueError("Unknown console. Use --list-consoles to see available names.")
        chosen.add(console.slug)
    return tuple(console for console in CONSOLES if console.slug in chosen)