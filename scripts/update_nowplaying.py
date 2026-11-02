#!/usr/bin/env python3
"""Read Haul.FM metadata and produce GitHub Pages static nowplaying.json."""
import json
import logging
import re
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "nowplaying.json"
STREAM = "http://stream.haul.fm:8000/haulmpfm.mp3"
STATUS = "http://stream.haul.fm:8000/status-json.xsl"
PREVIOUS = "https://walleyfire.github.io/haul-fm-stream-overlay/nowplaying.json"
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def get_bytes(url, headers=None, max_bytes=350000, timeout=8):
    request = Request(url, headers={"User-Agent": "HaulFM-OBS-Overlay/2.3", **(headers or {})})
    with urlopen(request, timeout=timeout) as response:
        return response.read(max_bytes)


def split_song(text):
    raw = re.sub(r"\s+", " ", str(text or "")).strip()[:300]
    if not raw or raw.lower() in ("-", "n/a", "unknown", "haulfm", "haul.fm", "haulmpfm"):
        return "", ""
    if " - " in raw:
        artist, title = raw.split(" - ", 1)
        return artist.strip()[:150], title.strip()[:180]
    return "", raw[:180]


def from_icecast(data):
    sources = (data.get("icestats") or {}).get("source") or []
    if isinstance(sources, dict):
        sources = [sources]
    if not isinstance(sources, list):
        return None
    # Never confuse another mount with Haul.FM.
    matches = [s for s in sources if isinstance(s, dict) and
               "/haulmpfm.mp3" in " ".join(str(s.get(k) or "") for k in ("listenurl", "mount", "server_url"))]
    if not matches and len(sources) == 1 and isinstance(sources[0], dict):
        matches = sources
    if not matches:
        return None
    src = matches[0]
    song = src.get("song") or src.get("title") or ""
    artist = str(src.get("artist") or "").strip()
    song = str(song or "").strip()
    if not song:
        return ""
    if artist and not song.casefold().startswith((artist + " - ").casefold()):
        return artist + " - " + song
    return song


def from_icy():
    request = Request(STREAM, headers={
        "Icy-MetaData": "1", "User-Agent": "HaulFM-OBS-Overlay/2.3"})
    with urlopen(request, timeout=12) as response:
        interval = int(response.headers.get("icy-metaint", "0"))
        if not 1 <= interval <= 262144:
            return ""
        audio = response.read(interval + 1)
        if len(audio) < interval + 1:
            return ""
        size = audio[interval] * 16
        if not 0 < size <= 4080:
            return ""
        metadata = response.read(size).decode("utf-8", errors="replace")
        match = re.search(r"StreamTitle\s*=\s*(['\"])(.*?)\1", metadata, flags=re.I)
        return match.group(2) if match else ""


def station():
    errors = []
    try:
        data = json.loads(get_bytes(STATUS, {"Accept": "application/json"}))
        song = from_icecast(data)
        if song:  # Non-empty title on the desired Icecast mount.
            return song, "icecast", ""
        errors.append("Icecast does not report a song for the required mount")
    except Exception as error:
        errors.append("Icecast " + type(error).__name__ + ": " + str(error)[:180])
    try:
        song = from_icy()
        if song:
            return song, "icy", ""
        errors.append("ICY stream has no StreamTitle metadata")
    except Exception as error:
        errors.append("ICY " + type(error).__name__ + ": " + str(error)[:180])
    return "", "unavailable", " | ".join(errors)[:420]


def normalized(text):
    return re.sub(r"[^a-z0-9]+", " ", str(text or "").casefold()).strip()


def score(a, b):
    a, b = normalized(a), normalized(b)
    if not a or not b:
        return 0
    if a == b:
        return 1
    aa, bb = set(a.split()), set(b.split())
    return len(aa & bb) / max(len(aa), len(bb))


def get_itunes(artist, title):
    if not artist or not title:
        return None, None
    try:
        url = "https://itunes.apple.com/search?" + urlencode({
            "term": artist + " " + title, "entity": "song", "limit": 8, "country": "fi"})
        results = json.loads(get_bytes(url, timeout=7)).get("results") or []
        candidates = [(score(artist, r.get("artistName")) * .4 + score(title, r.get("trackName")) * .6, r)
                      for r in results if score(artist, r.get("artistName")) >= .78
                      and score(title, r.get("trackName")) >= .84]
        if not candidates:
            return None, None
        rec = max(candidates, key=lambda c: c[0])[1]
        cover = rec.get("artworkUrl100")
        if isinstance(cover, str):
            cover = re.sub(r"\d+x\d+bb", "600x600bb", cover)
        if not isinstance(cover, str) or not cover.startswith("https://"):
            cover = None
        duration = round(float(rec.get("trackTimeMillis") or 0) / 1000)
        return cover, duration if 30 <= duration <= 1800 else None
    except Exception as error:
        logging.warning("Optional iTunes lookup failed: %s", error)
        return None, None


def read_previous(now):
    try:
        saved = json.loads(get_bytes(PREVIOUS + "?t=" + str(now), timeout=5))
        if not isinstance(saved, dict) or now - float(saved.get("last_checked") or 0) > 1200:
            return {}
        return saved
    except Exception as error:
        logging.warning("Previous Pages metadata unavailable: %s", error)
        return {}


def validate():
    assert split_song("Artist - Track") == ("Artist", "Track")
    assert split_song("Haul.FM") == ("", "")
    assert from_icecast({"icestats": {"source": [{"mount": "/other"}, {
        "listenurl": "http://radio:8000/haulmpfm.mp3", "artist": "A", "title": "B"}]}}) == "A - B"
    assert from_icecast({"icestats": {"source": {
        "listenurl": "/haulmpfm.mp3", "title": "C - D"}}}) == "C - D"
    print("Metadata parser tests passed")


def main():
    now = int(time.time())
    raw, source, reason = station()
    result = {
        "status": "offline", "artist": "", "title": "",
        "artwork": None, "duration": None, "first_seen": None,
        "last_checked": now, "source": source, "error": reason,
    }
    artist, title = split_song(raw)
    if title:
        prev = read_previous(now)
        same = prev.get("status") == "live" and prev.get("artist") == artist and prev.get("title") == title
        started = int(prev.get("first_seen") or now) if same else now
        if started > now or now - started > 3600:
            started = now
        artwork, duration = get_itunes(artist, title)
        if same:
            artwork = artwork or prev.get("artwork")
            duration = duration or prev.get("duration")
        result.update({
            "status": "live", "artist": artist, "title": title,
            "artwork": artwork, "duration": duration,
            "first_seen": started, "error": "",
        })
    elif source == "icecast" or source == "icy":
        result["status"] = "no_metadata"
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    logging.info("status=%s source=%s title=%r artist=%r", result["status"], source, title, artist)
    if reason:
        logging.warning("Stream diagnostic: %s", reason)


if __name__ == "__main__":
    import sys
    if "--self-test" in sys.argv:
        validate()
    else:
        main()
