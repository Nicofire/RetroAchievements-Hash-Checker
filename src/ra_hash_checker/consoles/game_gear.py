from ..models import ConsoleSpec

CONSOLE = ConsoleSpec("game_gear", "Game Gear", 15, (".gg",), ("gg",))
calculate_hash = CONSOLE.calculate_hash