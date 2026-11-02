from ..models import ConsoleSpec

CONSOLE = ConsoleSpec("arduboy", "Arduboy", 71, (".hex",))
calculate_hash = CONSOLE.calculate_hash