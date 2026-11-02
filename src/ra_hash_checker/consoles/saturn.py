from ..models import ConsoleSpec

CONSOLE = ConsoleSpec("saturn", "Sega Saturn", 39, (".cue", ".iso", ".bin"), ("sega_saturn",))
calculate_hash = CONSOLE.calculate_hash