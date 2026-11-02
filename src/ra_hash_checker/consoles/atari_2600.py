from ..models import ConsoleSpec

CONSOLE = ConsoleSpec("atari_2600", "Atari 2600", 25, (".a26", ".bin"), ("a2600",))
calculate_hash = CONSOLE.calculate_hash