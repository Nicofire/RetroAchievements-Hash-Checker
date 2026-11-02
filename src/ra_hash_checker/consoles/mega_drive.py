from ..models import ConsoleSpec

CONSOLE = ConsoleSpec("mega_drive", "Mega Drive / Genesis", 1, (".md", ".gen", ".bin"), ("genesis", "megadrive", "md"))
calculate_hash = CONSOLE.calculate_hash