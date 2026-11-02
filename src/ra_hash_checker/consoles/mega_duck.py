from ..models import ConsoleSpec

CONSOLE = ConsoleSpec("mega_duck", "Mega Duck", 69, (".duck", ".bin"), ("megaduck",))
calculate_hash = CONSOLE.calculate_hash