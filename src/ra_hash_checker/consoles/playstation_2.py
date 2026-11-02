from ..models import ConsoleSpec

CONSOLE = ConsoleSpec("playstation_2", "PlayStation 2", 21, (".iso", ".cue", ".bin"), ("ps2",))
calculate_hash = CONSOLE.calculate_hash