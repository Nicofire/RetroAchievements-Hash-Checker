from ..models import ConsoleSpec

CONSOLE = ConsoleSpec("snes", "SNES / Super Famicom / Satellaview / Sufami Turbo", 3, (".sfc", ".smc", ".swc", ".bs", ".st"), ("sfc", "super_famicom", "satellaview", "sufami_turbo"))
calculate_hash = CONSOLE.calculate_hash