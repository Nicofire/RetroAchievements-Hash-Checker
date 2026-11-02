from ..models import ConsoleSpec

CONSOLE = ConsoleSpec("nintendo_ds", "Nintendo DS", 18, (".nds",), ("nds", "ds"))
calculate_hash = CONSOLE.calculate_hash