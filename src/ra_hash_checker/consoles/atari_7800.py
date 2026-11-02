from ..models import ConsoleSpec

CONSOLE = ConsoleSpec("atari_7800", "Atari 7800", 51, (".a78", ".bin"), ("a7800",))
calculate_hash = CONSOLE.calculate_hash