from ..models import ConsoleSpec

CONSOLE = ConsoleSpec("atari_lynx", "Atari Lynx", 13, (".lnx",), ("lynx",))
calculate_hash = CONSOLE.calculate_hash