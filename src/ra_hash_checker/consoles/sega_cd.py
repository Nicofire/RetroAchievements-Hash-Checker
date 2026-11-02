from ..models import ConsoleSpec

CONSOLE = ConsoleSpec("sega_cd", "Sega CD", 9, (".cue", ".iso", ".bin"), ("megacd", "mega_cd"))
calculate_hash = CONSOLE.calculate_hash