from ..models import ConsoleSpec

CONSOLE = ConsoleSpec("dreamcast", "Dreamcast", 40, (".gdi", ".cue", ".bin"), ("dc",))
calculate_hash = CONSOLE.calculate_hash