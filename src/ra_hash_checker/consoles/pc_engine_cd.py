from ..models import ConsoleSpec

CONSOLE = ConsoleSpec("pc_engine_cd", "PC Engine CD / TurboGrafx-CD", 76, (".cue", ".iso", ".bin"), ("pce_cd", "tgcd"))
calculate_hash = CONSOLE.calculate_hash