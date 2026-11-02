from ..models import ConsoleSpec

CONSOLE = ConsoleSpec("wonderswan", "WonderSwan", 53, (".ws",), ("ws",))
calculate_hash = CONSOLE.calculate_hash