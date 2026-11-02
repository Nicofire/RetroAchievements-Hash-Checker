from ..models import ConsoleSpec

CONSOLE = ConsoleSpec("colecovision", "ColecoVision", 44, (".col", ".rom", ".bin"), ("coleco",))
calculate_hash = CONSOLE.calculate_hash