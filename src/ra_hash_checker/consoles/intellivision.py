from ..models import ConsoleSpec

CONSOLE = ConsoleSpec("intellivision", "Intellivision", 45, (".int", ".rom", ".bin"), ("intv",))
calculate_hash = CONSOLE.calculate_hash