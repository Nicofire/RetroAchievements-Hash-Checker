from ..models import ConsoleSpec

CONSOLE = ConsoleSpec("neo_geo_cd", "Neo Geo CD", 56, (".cue", ".iso", ".bin"), ("ngcd",))
calculate_hash = CONSOLE.calculate_hash