import hashlib
import json
import os
import struct
from pathlib import Path
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from rich import box
from rich.console import Console
from rich.table import Table
from rich.text import Text

def calculate_nds_ra_hash(filepath: str) -> str:
    with open(filepath, "rb") as f:
        rom = f.read()

    if len(rom) < 0x160:
        raise ValueError("Datei ist kleiner als der Mindest-NDS-Header (0x160 Bytes).")

    # 1. Header (0x160 Bytes)
    header = rom[0:0x160]

    # 2. Offsets und Größen aus dem Header auslesen (Little-Endian 32-Bit Unsigned Int)
    arm9_offset = struct.unpack("<I", rom[0x20:0x24])[0]
    arm9_size   = struct.unpack("<I", rom[0x2C:0x30])[0]

    arm7_offset = struct.unpack("<I", rom[0x30:0x34])[0]
    arm7_size   = struct.unpack("<I", rom[0x3C:0x40])[0]

    icon_offset = struct.unpack("<I", rom[0x68:0x6C])[0]
    icon_size   = 0xA00

    # 3. Code- und Metadatenblöcke extrahieren
    arm9_code = rom[arm9_offset : arm9_offset + arm9_size]
    arm7_code = rom[arm7_offset : arm7_offset + arm7_size]
    icon_data = rom[icon_offset : icon_offset + icon_size] if icon_offset > 0 else b""

    # 4. Payload exakt wie RetroAchievements zusammensetzen
    payload = header + arm9_code + arm7_code + icon_data

    # 5. MD5-Hash generieren (32-stellige Hex-Zeichenkette)
    return hashlib.md5(payload).hexdigest()


def build_ra_hash_index(games: object) -> dict[str, tuple[int, str, int]]:
    if not isinstance(games, list):
        raise ValueError("Ungueltige RA-Antwort: Spieleliste erwartet.")

    hash_index: dict[str, tuple[int, str, int]] = {}
    for game in games:
        if not isinstance(game, dict):
            raise ValueError("Ungueltiger Eintrag in der RA-Spieleliste.")
        game_id = game.get("ID")
        title = game.get("Title")
        achievements = game.get("NumAchievements")
        hashes = game.get("Hashes")
        if (
            not isinstance(game_id, int) or game_id <= 0
            or not isinstance(title, str)
            or not isinstance(achievements, int) or achievements < 0
            or not isinstance(hashes, list)
        ):
            raise ValueError("Unvollstaendiger Eintrag in der RA-Spieleliste.")
        for ra_hash in hashes:
            if (
                not isinstance(ra_hash, str) or len(ra_hash) != 32
                or any(character not in "0123456789abcdef" for character in ra_hash.lower())
            ):
                raise ValueError("Ungueltiger Hash in der RA-Spieleliste.")
            ra_hash = ra_hash.lower()
            previous = hash_index.get(ra_hash)
            if previous is None or achievements > previous[2]:
                hash_index[ra_hash] = (game_id, title, achievements)
    return hash_index


def load_ra_hashes(api_key: str, cache_path: Path) -> dict[str, tuple[int, str, int]]:
    try:
        cache_age = time.time() - cache_path.stat().st_mtime
        if 0 <= cache_age < 24 * 60 * 60:
            hash_index = build_ra_hash_index(json.loads(cache_path.read_text(encoding="utf-8")))
            print("RA-Daten: lokaler Cache (maximal 24 Stunden alt).\n")
            return hash_index
    except (OSError, ValueError):
        pass

    if not api_key:
        raise ValueError(
            "RA_API_KEY fehlt. Web-API-Key unter https://retroachievements.org/controlpanel.php "
            "abrufen und als Umgebungsvariable RA_API_KEY setzen."
        )

    print("Lade Nintendo-DS-Hashes von RetroAchievements ...")
    query = urlencode({"y": api_key, "i": 18, "h": 1, "f": 0})
    request = Request(
        f"https://retroachievements.org/API/API_GetGameList.php?{query}",
        headers={"User-Agent": "nds-hash/1.0", "Accept": "application/json"},
    )
    try:
        with urlopen(request, timeout=30) as response:
            games = json.load(response)
    except HTTPError as error:
        raise ValueError(f"RA-API: HTTP {error.code}. API-Key/Zugriff pruefen.") from None
    except (URLError, OSError):
        raise ValueError("RA-API nicht erreichbar (Netzwerkfehler oder Timeout).") from None
    except (ValueError, UnicodeError):
        raise ValueError("RA-API hat keine gueltige JSON-Antwort geliefert.") from None

    hash_index = build_ra_hash_index(games)
    try:
        cache_path.write_text(json.dumps(games), encoding="utf-8")
    except OSError:
        print("Hinweis: RA-Cache konnte nicht gespeichert werden.")
    print()
    return hash_index


def main() -> None:
    rom_dir = Path(__file__).resolve().parent / "roms"
    if not rom_dir.is_dir():
        print(f"ROM-Ordner nicht gefunden: {rom_dir}")
        return

    nds_files = sorted(
        path for path in rom_dir.rglob("*")
        if path.is_file() and path.suffix.lower() == ".nds"
    )
    if not nds_files:
        print(f"Keine .nds-Dateien gefunden: {rom_dir}")
        return

    ra_hashes = None
    try:
        ra_hashes = load_ra_hashes(
            os.environ.get("RA_API_KEY", "").strip(),
            Path(__file__).resolve().with_name(".ra_nds_games_cache.json"),
        )
    except (OSError, ValueError) as error:
        print(f"RA-Abgleich nicht moeglich: {error}\n")

    table = Table(
        title="Nintendo DS - RetroAchievements",
        box=box.ASCII,
        header_style="bold cyan",
        show_lines=True,
        expand=True,
    )
    table.add_column("ROM-Datei", min_width=9, overflow="fold")
    table.add_column("RA-Hash", width=32, min_width=32, no_wrap=True)
    table.add_column("RA-Status", width=18, min_width=18, overflow="fold")
    table.add_column("RA-Spiel", min_width=8, overflow="fold")

    for nds_file in nds_files:
        filename = Text(str(nds_file.relative_to(rom_dir)))
        try:
            ra_hash = calculate_nds_ra_hash(str(nds_file))
        except (OSError, ValueError) as error:
            table.add_row(filename, "-", Text("FEHLER", style="bold red"), Text(str(error)))
            continue
        if ra_hashes is None:
            table.add_row(filename, ra_hash, Text("NICHT GEPRUEFT", style="yellow"), "-")
            continue

        game = ra_hashes.get(ra_hash)
        if game is None:
            table.add_row(
                filename, ra_hash,
                Text("NICHT UNTERSTUETZT\nHash unbekannt", style="red"), "-",
            )
            continue

        game_id, title, achievements = game
        if achievements > 0:
            status = Text(f"UNTERSTUETZT\n{achievements} Achievements", style="green")
        else:
            status = Text("NICHT UNTERSTUETZT\nKeine Achievements", style="red")
        game_label = Text(title, style=f"link https://retroachievements.org/game/{game_id}")
        game_label.append(f"\nID: {game_id}")
        table.add_row(filename, ra_hash, status, game_label)

    Console().print(table)


if __name__ == "__main__":
    main()