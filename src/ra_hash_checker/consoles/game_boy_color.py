from ..models import ConsoleSpec

CONSOLE = ConsoleSpec("game_boy_color", "Game Boy Color", 6, (".gbc",), ("gbc",))
calculate_hash = CONSOLE.calculate_hash