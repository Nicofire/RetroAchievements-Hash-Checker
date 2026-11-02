from ..models import ConsoleSpec

CONSOLE = ConsoleSpec("arcade", "Arcade", 27, (".zip", ".7z"), ("mame", "fbneo"))
calculate_hash = CONSOLE.calculate_hash