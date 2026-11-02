import hashlib
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import ra_hash_checker
from ra_hash_checker.cache import atomic_json
from ra_hash_checker.cli import main
from ra_hash_checker.native import calculate_hash


def smoke() -> None:
    package = Path(ra_hash_checker.__file__).resolve().parent
    assert "site-packages" in str(package)
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        roms = root / "roms"
        roms.mkdir()
        path = roms / "Synthetic.gb"
        path.write_bytes(b"synthetic Game Boy ROM")
        expected = hashlib.md5(path.read_bytes()).hexdigest()
        assert calculate_hash(path, 4) == expected
        atomic_json(root / "cache/console-4.json", {
            "schema_version": 1, "console_id": 4,
            "fetched_at": datetime.now(timezone.utc).isoformat(), "options": {"h": 1, "f": 0},
            "games": [{"ID": 1, "Title": "Synthetic Game", "NumAchievements": 10, "Hashes": [expected]}],
        })
        assert main(["--project-dir", str(root), "--paths", str(roms), "--offline"]) == 0
        reports = list((root / "log").glob("*.json"))
        assert len(reports) == 1
        report = json.loads(reports[0].read_text(encoding="utf-8"))
        assert report["counts"] == {"SUPPORTED": 1}
        assert report["results"][0]["hash"] == expected
        assert not any((package / name).exists() for name in ("roms", "log", "cache"))
    print("Installed wheel smoke test passed.")


if __name__ == "__main__":
    smoke()