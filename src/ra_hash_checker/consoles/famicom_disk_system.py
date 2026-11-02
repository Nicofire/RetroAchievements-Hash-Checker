from ..models import ConsoleSpec

CONSOLE = ConsoleSpec("famicom_disk_system", "Famicom Disk System", 81, (".fds",), ("fds",))
calculate_hash = CONSOLE.calculate_hash