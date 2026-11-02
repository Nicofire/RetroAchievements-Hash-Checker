from ..models import ConsoleSpec

CONSOLE = ConsoleSpec("game_boy_advance", "Game Boy Advance", 5, (".gba",), ("gba",))
calculate_hash = CONSOLE.calculate_hash