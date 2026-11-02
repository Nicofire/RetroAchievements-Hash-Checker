from ..models import ConsoleSpec

CONSOLE = ConsoleSpec("master_system", "Master System", 11, (".sms",), ("sms",))
calculate_hash = CONSOLE.calculate_hash