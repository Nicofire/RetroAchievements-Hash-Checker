from ..models import ConsoleSpec

CONSOLE = ConsoleSpec("playstation", "PlayStation", 12, (".cue", ".iso", ".bin", ".exe"), ("ps1", "psx"))
calculate_hash = CONSOLE.calculate_hash