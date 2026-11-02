from ..models import ConsoleSpec

CONSOLE = ConsoleSpec("wasm4", "WASM-4", 72, (".wasm",), ("wasm_4", "wasm-4"))
calculate_hash = CONSOLE.calculate_hash