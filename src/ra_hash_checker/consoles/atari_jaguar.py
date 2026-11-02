from ..models import ConsoleSpec

CONSOLE = ConsoleSpec("atari_jaguar", "Atari Jaguar", 17, (".j64", ".jag", ".rom", ".abs", ".cof", ".bin"), ("jaguar",))
calculate_hash = CONSOLE.calculate_hash