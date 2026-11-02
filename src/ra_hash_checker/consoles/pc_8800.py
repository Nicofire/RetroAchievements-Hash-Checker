from ..models import ConsoleSpec

CONSOLE = ConsoleSpec("pc_8800", "PC-8001 / PC-8801", 47, (".d88", ".d98", ".dsk", ".88d"), ("pc8800", "pc8001", "pc8801"))
calculate_hash = CONSOLE.calculate_hash