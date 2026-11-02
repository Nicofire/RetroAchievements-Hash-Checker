import json
import re
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from http.client import HTTPException
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from . import __version__
from .models import GameInfo


class ApiError(ValueError):
    pass


def build_hash_index(games: object) -> dict[str, list[GameInfo]]:
    if not isinstance(games, list):
        raise ApiError("RA catalog is not a game list.")
    index: dict[str, list[GameInfo]] = {}
    for game in games:
        if not isinstance(game, dict):
            raise ApiError("Invalid game entry in the RA catalog.")
        game_id = game.get("ID")
        title = game.get("Title")
        count = game.get("NumAchievements")
        hashes = game.get("Hashes")
        if (type(game_id) is not int or game_id <= 0 or not isinstance(title, str)
                or type(count) is not int or count < 0 or not isinstance(hashes, list)):
            raise ApiError("RA catalog contains invalid game fields.")
        info = GameInfo(game_id, title, count)
        for value in hashes:
            if not isinstance(value, str) or re.fullmatch(r"[0-9a-fA-F]{32}", value) is None:
                raise ApiError("RA catalog contains an invalid hash.")
            alternatives = index.setdefault(value.lower(), [])
            if info not in alternatives:
                alternatives.append(info)
    for alternatives in index.values():
        alternatives.sort(key=lambda game: (-game.achievements, game.game_id, game.title))
    return index


class RetroAchievementsAPI:
    def __init__(self, api_key: str, opener: Any = urlopen, sleeper: Any = time.sleep):
        self._api_key = api_key
        self._open = opener
        self._sleep = sleeper

    def _request(self, endpoint: str, parameters: dict[str, object]) -> object:
        if not self._api_key:
            raise ApiError("No RA API key configured; only the local hash was calculated.")
        query = urlencode({"y": self._api_key, **parameters})
        request = Request(
            f"https://retroachievements.org/API/{endpoint}?{query}",
            headers={"User-Agent": f"ra-hash-checker/{__version__}"},
        )
        for attempt in range(3):
            try:
                with self._open(request, timeout=30) as response:
                    payload = response.read(64 * 1024 * 1024 + 1)
                if len(payload) > 64 * 1024 * 1024:
                    raise ApiError("RA response is too large.")
                return json.loads(payload.decode("utf-8-sig"))
            except HTTPError as error:
                if error.code == 429 and attempt < 2:
                    delay = self._retry_delay(error.headers.get("Retry-After", "1"))
                    error.close()
                    if delay is not None:
                        self._sleep(delay)
                        continue
                code = error.code
                error.close()
                raise ApiError(f"RA request failed (HTTP {code}).") from None
            except (URLError, OSError, TimeoutError, HTTPException):
                raise ApiError("RA request failed (network error or timeout).") from None
            except (ValueError, UnicodeError):
                raise ApiError("RA did not return valid JSON.") from None
            raise ApiError("RA request limit reached.")

    @staticmethod
    def _retry_delay(value: str) -> float | None:
        try:
            delay = float(value)
        except ValueError:
            try:
                delay = (parsedate_to_datetime(value) - datetime.now(timezone.utc)).total_seconds()
            except (ValueError, TypeError, OverflowError):
                return None
        return max(0.0, delay) if 0 <= delay <= 5 else None

    def games(self, console_id: int) -> list[dict[str, object]]:
        if console_id == 81:
            consoles = self._request("API_GetConsoleIDs.php", {})
            if not isinstance(consoles, list) or not any(
                isinstance(console, dict) and type(console.get("ID")) is int and console["ID"] == 81
                for console in consoles
            ):
                raise ApiError("The server did not confirm FDS API ID 81; refusing to guess an NES catalog match.")
        games = self._request("API_GetGameList.php", {"i": console_id, "h": 1, "f": 0})
        build_hash_index(games)
        return games