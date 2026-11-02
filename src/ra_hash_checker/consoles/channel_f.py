from ..models import ConsoleSpec

CONSOLE = ConsoleSpec("channel_f", "Channel F", 57, (".chf", ".bin"), ("channelf",))
calculate_hash = CONSOLE.calculate_hash