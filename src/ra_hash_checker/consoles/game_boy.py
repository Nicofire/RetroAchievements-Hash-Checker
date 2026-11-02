from ..models import ConsoleSpec

CONSOLE = ConsoleSpec("game_boy", "Game Boy", 4, (".gb",), ("gb", "gameboy"))
calculate_hash = CONSOLE.calculate_hash