from ..models import ConsoleSpec

CONSOLE = ConsoleSpec("odyssey2", "Odyssey2", 23, (".o2", ".bin"), ("odyssey", "videopac"))
calculate_hash = CONSOLE.calculate_hash