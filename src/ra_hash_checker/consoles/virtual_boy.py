from ..models import ConsoleSpec

CONSOLE = ConsoleSpec("virtual_boy", "Virtual Boy", 28, (".vb", ".vboy"), ("vb",))
calculate_hash = CONSOLE.calculate_hash