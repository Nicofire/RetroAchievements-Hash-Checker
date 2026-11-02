from ..models import ConsoleSpec

CONSOLE = ConsoleSpec("three_do", "3DO Interactive Multiplayer", 43, (".cue", ".iso", ".bin"), ("3do",))
calculate_hash = CONSOLE.calculate_hash