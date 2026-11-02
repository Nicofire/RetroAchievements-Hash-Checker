from ..models import ConsoleSpec

CONSOLE = ConsoleSpec("nintendo_64", "Nintendo 64", 2, (".z64", ".v64", ".n64"), ("n64",))
calculate_hash = CONSOLE.calculate_hash