from ..models import ConsoleSpec

CONSOLE = ConsoleSpec("psp", "PlayStation Portable", 41, (".iso",), ("playstation_portable",))
calculate_hash = CONSOLE.calculate_hash