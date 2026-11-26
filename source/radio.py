"""Radio metadata fetcher for an independent, editable HaulFM overlay.

This is a reference implementation; it is NOT the original source of
the released HaulFM-Overlay.exe application.
"""
from __future__ import annotations

import json
import re
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ICECAST = "http://stream.haul.fm:8000/status-json.xsl"
STREAM = "http://stream.haul.fm:8000/haulmpfm.mp3"
MOUNT = "/haulmpfm.mp3"
USER_AGENT = "HaulFM-OpenSource-Reference/0.1"


def read_json(url: str, timeout: int = 8) -> dict:
    req = Request(url, headers={"Accept": "application/json", "User-Agent": USER_AGENT})
    with urlopen(req, timeout=timeout) as response:
        data = json.loads(response.read(400_000))
    if not isinstance(data, dict):
        raise ValueError("Expected a JSON object")
    return data


def parse_song(value: str, explicit_artist: str = "") -> tuple[str, str]:
    raw = " ".join(str(value or "").split()).strip()
    artist = " ".join(str(explicit_artist or "").split()).strip()
    if raw.casefold() in ("", "unknown", "-", "haul.fm", "haulfm"):
        return "", ""
    if artist and raw.casefold().startswith((artist + " - ").casefold()):
        raw = raw[len(artist) + 3:]
    elif not artist and " - " in raw:
        artist, raw = raw.split(" - ", 1)
    return artist[:150], raw.strip()[:200]


def parse_icecast(data: dict) -> tuple[str, str]:
    sources = (data.get("icestats") or {}).get("source") or []
    if isinstance(sources, dict):
        sources = [sources]
    if not isinstance(sources, list):
        return "", ""
    matching = [
        src for src in sources
        if isinstance(src, dict) and any(
            MOUNT in str(src.get(key) or "") for key in ("mount", "listenurl", "server_url")
        )
    ]
    if not matching and len(sources) == 1 and isinstance(sources[0], dict):
        matching = sources
    if not matching:
        return "", ""
    src = matching[0]
    return parse_song(src.get("song") or src.get("title") or "", src.get("artist") or "")


def icy_song() -> tuple[str, str]:
    """Read one ICY metadata frame; do not relay or save audio."""
    req = Request(STREAM, headers={"Icy-MetaData": "1", "User-Agent": USER_AGENT})
    with urlopen(req, timeout=10) as response:
        interval = int(response.headers.get("icy-metaint", "0"))
        if not 0 < interval <= 262144:
            return "", ""
        header = response.read(interval + 1)
        if len(header) < interval + 1:
            return "", ""
        length = header[interval] * 16
        if not 0 < length <= 4080:
            return "", ""
        frame = response.read(length).decode("utf-8", "replace")
    match = re.search(r"StreamTitle\s*=\s*(['\"])(.*?)\1", frame, re.IGNORECASE)
    return parse_song(match.group(2)) if match else ("", "")


def similarity(expected: str, actual: str) -> float:
    def words(v: str) -> set[str]:
        return set(re.sub(r"[^a-z0-9]+", " ", v.casefold()).split())
    a, b = words(expected), words(actual)
    return len(a & b) / max(len(a), len(b)) if a and b else 0.0


def lookup_artwork(artist: str, title: str) -> tuple[str | None, int | None]:
    """Optional iTunes match; no image/length is preferable to a wrong match."""
    if not artist or not title:
        return None, None
    url = "https://itunes.apple.com/search?" + urlencode({
        "term": artist + " " + title, "entity": "song", "limit": 8, "country": "fi"
    })
    try:
        results = read_json(url, timeout=6).get("results") or []
        matches = [
            (0.4 * similarity(artist, rec.get("artistName") or "")
             + 0.6 * similarity(title, rec.get("trackName") or ""), rec)
            for rec in results
            if isinstance(rec, dict)
            and similarity(artist, rec.get("artistName") or "") >= 0.78
            and similarity(title, rec.get("trackName") or "") >= 0.84
        ]
        if not matches:
            return None, None
        best = max(matches, key=lambda result: result[0])[1]
        art = best.get("artworkUrl100")
        art = re.sub(r"\d+x\d+bb", "600x600bb", art) if isinstance(art, str) else None
        if not (isinstance(art, str) and art.startswith("https://")):
            art = None
        length = round(float(best.get("trackTimeMillis") or 0) / 1000)
        return art, length if 30 <= length <= 1800 else None
    except (OSError, ValueError, TypeError, KeyError):
        return None, None


def parse_presenter(data: dict) -> dict:
    """Generic *optional* JSON presenter feed, NOT an official Haul.FM schema."""
    live = data.get("dj_live", data.get("is_live", data.get("live", False)))
    entry = data.get("presenter") or data.get("dj") or data.get("streamer") or ""
    if isinstance(entry, dict):
        name = entry.get("name") or entry.get("display_name") or ""
    else:
        name = str(entry or data.get("dj_name") or data.get("presenter_name") or "")
    show = data.get("show") or data.get("dj_show") or data.get("show_name") or ""
    if isinstance(show, dict):
        show = show.get("name", "")
    if not (live is True and isinstance(name, str) and name.strip()):
        return {"dj_live": False, "dj_name": "Auto DJ", "dj_show": ""}
    return {"dj_live": True, "dj_name": name.strip()[:80], "dj_show": str(show)[:100]}


class RadioClient:
    def __init__(self, dj_feed_url: str = ""):
        self.dj_feed_url = dj_feed_url
        self.last_track: tuple[str, str] = ("", "")
        self.started = 0
        self.artwork: str | None = None
        self.duration: int | None = None
        self.dj_data = {"dj_live": False, "dj_name": "Auto DJ", "dj_show": ""}
        self.dj_updated = 0

    def now_playing(self) -> dict:
        artist, title = "", ""
        try:
            artist, title = parse_icecast(read_json(ICECAST))
        except (OSError, ValueError, TypeError):
            pass
        if not title:
            try:
                artist, title = icy_song()
            except (OSError, ValueError, TypeError):
                pass
        stamp = int(time.time())
        if not title:
            return {
                "status": "unavailable", "artist": "", "title": "",
                "artwork": None, "duration": None,
                "first_seen": None, "last_checked": stamp,
            }
        key = (artist, title)
        if key != self.last_track:
            self.last_track = key
            self.started = stamp
            self.artwork, self.duration = lookup_artwork(artist, title)
        return {
            "status": "live", "artist": artist, "title": title,
            "artwork": self.artwork, "duration": self.duration,
            "first_seen": self.started, "last_checked": stamp,
        }

    def presenter(self) -> dict:
        """Return Auto DJ when an upstream presenter is unavailable or stale."""
        stamp = int(time.time())
        if self.dj_feed_url:
            try:
                if not self.dj_feed_url.startswith("https://"):
                    raise ValueError("DJ feed must be HTTPS")
                self.dj_data = parse_presenter(read_json(self.dj_feed_url))
                self.dj_updated = stamp
            except (OSError, ValueError, TypeError):
                if stamp - self.dj_updated > 90:
                    self.dj_data = {"dj_live": False, "dj_name": "Auto DJ", "dj_show": ""}
        return dict(self.dj_data)
