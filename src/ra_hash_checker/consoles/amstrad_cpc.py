from ..models import ConsoleSpec

CONSOLE = ConsoleSpec("amstrad_cpc", "Amstrad CPC", 37, (".dsk",), ("cpc",))
calculate_hash = CONSOLE.calculate_hash