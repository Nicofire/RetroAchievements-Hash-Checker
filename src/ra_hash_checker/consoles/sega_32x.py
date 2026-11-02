from ..models import ConsoleSpec

CONSOLE = ConsoleSpec("sega_32x", "Sega 32X", 10, (".32x", ".bin"), ("32x",))
calculate_hash = CONSOLE.calculate_hash