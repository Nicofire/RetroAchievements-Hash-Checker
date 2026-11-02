from ..models import ConsoleSpec

CONSOLE = ConsoleSpec("gamecube", "GameCube", 16, (".iso", ".gcm"), ("gc", "ngc"))
calculate_hash = CONSOLE.calculate_hash