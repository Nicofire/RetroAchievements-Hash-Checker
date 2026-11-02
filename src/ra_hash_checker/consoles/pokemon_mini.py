from ..models import ConsoleSpec

CONSOLE = ConsoleSpec("pokemon_mini", "Pokemon Mini", 24, (".min",), ("pokemini",))
calculate_hash = CONSOLE.calculate_hash