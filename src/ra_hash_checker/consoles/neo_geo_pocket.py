from ..models import ConsoleSpec

CONSOLE = ConsoleSpec("neo_geo_pocket", "Neo Geo Pocket", 14, (".ngp",), ("ngp",))
calculate_hash = CONSOLE.calculate_hash