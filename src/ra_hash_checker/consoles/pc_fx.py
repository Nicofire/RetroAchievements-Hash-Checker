from ..models import ConsoleSpec

CONSOLE = ConsoleSpec("pc_fx", "PC-FX", 49, (".cue", ".iso", ".bin"), ("pcfx",))
calculate_hash = CONSOLE.calculate_hash