from ..models import ConsoleSpec

CONSOLE = ConsoleSpec("nes", "NES / Famicom", 7, (".nes",), ("famicom",))
calculate_hash = CONSOLE.calculate_hash