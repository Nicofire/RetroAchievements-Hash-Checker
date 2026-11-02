from ..models import ConsoleSpec

CONSOLE = ConsoleSpec("neo_geo_pocket_color", "Neo Geo Pocket Color", 14, (".ngc",), ("ngpc",))
calculate_hash = CONSOLE.calculate_hash