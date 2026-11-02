from ..models import ConsoleSpec

CONSOLE = ConsoleSpec("pc_engine", "PC Engine / TurboGrafx-16 / SuperGrafx", 8, (".pce", ".sgx"), ("pce", "tg16", "supergrafx"))
calculate_hash = CONSOLE.calculate_hash