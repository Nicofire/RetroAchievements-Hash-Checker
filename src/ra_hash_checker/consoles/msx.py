from ..models import ConsoleSpec

CONSOLE = ConsoleSpec("msx", "MSX / MSX2", 29, (".rom", ".mx1", ".mx2", ".dsk", ".cas"), ("msx2",))
calculate_hash = CONSOLE.calculate_hash