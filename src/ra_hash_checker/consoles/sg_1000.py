from ..models import ConsoleSpec

CONSOLE = ConsoleSpec("sg_1000", "SG-1000", 33, (".sg",), ("sg1000",))
calculate_hash = CONSOLE.calculate_hash