from ..models import ConsoleSpec

CONSOLE = ConsoleSpec("atari_jaguar_cd", "Atari Jaguar CD", 77, (".cue",), ("jaguar_cd",))
calculate_hash = CONSOLE.calculate_hash