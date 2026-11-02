from ..models import ConsoleSpec

CONSOLE = ConsoleSpec("apple_ii", "Apple II", 38, (".dsk", ".do", ".po", ".nib"), ("apple2",))
calculate_hash = CONSOLE.calculate_hash