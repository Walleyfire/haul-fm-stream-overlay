"""Discord Rich Presence for the new, source-built HaulFM Overlay.

Uses the locally running Discord desktop client through pypresence RPC.
Never sends a bot token, user token, or password.
"""
from __future__ import annotations

import logging
import time
from typing import Any, Callable
from urllib.parse import urlsplit

LOGGER = logging.getLogger(__name__)

STATION_URL = "https://haul.fm"
FALLBACK_ARTWORK = "https://haul.fm/brand/icon-96.webp"
RETRY_SECONDS = 30
MIN_UPDATE_SECONDS = 15
MAX_DISCORD_TEXT = 128


def _short(value: Any, maximum: int = MAX_DISCORD_TEXT) -> str:
    """Avoid passing too-long or multiline text to Discord RPC."""
    cleaned = " ".join(str(value or "").split())
    return cleaned[:maximum]


def _image_url(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = urlsplit(value)
    except ValueError:
        return None
    if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
        return None
    if any(ord(ch) < 32 for ch in value):
        return None
    return value if len(value) <= 500 else None


def build_activity(metadata: dict) -> dict | None:
    """Return a complete Discord activity payload, or None for offline streams.

    Rich Presence has only two visible text lines: details + state. To show
    title, artist, and live presenter at once, the first line combines title
    and artist, and the second shows the presenter / Auto DJ.
    """
    if metadata.get("status") != "live" or not _short(metadata.get("title")):
        return None

    title = _short(metadata.get("title"), 115)
    artist = _short(metadata.get("artist"), 110)
    title_and_artist = f"{title} — {artist}" if artist else title
    if len(title_and_artist) > MAX_DISCORD_TEXT:
        available = MAX_DISCORD_TEXT - len(artist) - 3
        title_and_artist = (
            f"{title[:available].rstrip()} — {artist}"
            if available >= 5 else f"{title[:MAX_DISCORD_TEXT]}"
        )

    dj_name = _short(metadata.get("dj_name"), 100)
    dj_live = metadata.get("dj_live") is True and bool(dj_name) and dj_name.casefold() != "auto dj"
    presenter = f"LIVE DJ: {dj_name}" if dj_live else "Auto DJ"
    show_name = _short(metadata.get("dj_show"), 126)
    tooltip = f"{title} — {artist}" if artist else title

    cover = _image_url(metadata.get("artwork")) or FALLBACK_ARTWORK
    result = {
        "details": title_and_artist,
        "state": _short(presenter),
        "large_image": cover,
        "large_text": _short(tooltip),
        "small_image": FALLBACK_ARTWORK,
        "small_text": _short(show_name or ("Live DJ: " + dj_name if dj_live else "Haul.FM • Auto DJ")),
    }
    return result


class DiscordRichPresence:
    """Non-fatal, rate-limited local Discord RPC connection.

    Calls must all originate from the application's existing background radio
    worker thread. Discord errors never stop song data updates or the UI.
    """

    def __init__(
        self,
        application_id: str = "",
        enabled: bool = True,
        rpc_factory: Callable[[str], Any] | None = None,
        clock: Callable[[], float] = time.monotonic,
    ):
        self.application_id = str(application_id or "").strip()
        self.enabled = enabled and self.application_id.isdecimal() and len(self.application_id) >= 15
        self._factory = rpc_factory
        self._clock = clock
        self._rpc = None
        self._last_payload: dict | None = None
        self._last_update = float("-inf")
        self._retry_at = float("-inf")

        if enabled and not self.application_id:
            LOGGER.info("Discord Rich Presence is unconfigured; set discord_application_id in config.json.")
        elif enabled and not self.enabled:
            LOGGER.warning("discord_application_id must be a numeric Discord application ID.")

    def _close_client(self):
        rpc = self._rpc
        self._rpc = None
        if rpc is not None:
            try:
                rpc.close()
            except Exception:
                pass

    def _connect(self, now: float) -> bool:
        if not self.enabled or now < self._retry_at:
            return False
        if self._rpc is not None:
            return True
        try:
            if self._factory is None:
                from pypresence import Presence
                self._factory = Presence
            rpc = self._factory(self.application_id)
            rpc.connect()
            self._rpc = rpc
            self._last_payload = None
            LOGGER.info("Discord Rich Presence connected.")
            return True
        except Exception as exc:
            self._retry_at = now + RETRY_SECONDS
            LOGGER.info("Discord unavailable (will retry): %s", exc)
            return False

    def update(self, metadata: dict):
        if not self.enabled:
            return
        now = self._clock()
        activity = build_activity(metadata)

        # Discord activity should disappear when no current song is available.
        if activity is None:
            if self._rpc is not None and self._last_payload is not None:
                try:
                    self._rpc.clear()
                except Exception:
                    self._close_client()
                    self._retry_at = now + RETRY_SECONDS
                self._last_payload = None
            return

        if self._rpc is None and not self._connect(now):
            return
        if activity == self._last_payload:
            return
        if now - self._last_update < MIN_UPDATE_SECONDS:
            return

        try:
            # Type 2 ("Listening") is supported by modern pypresence. The
            # overlay only shows metadata; it does not itself play radio audio.
            from pypresence.types import ActivityType
            self._rpc.update(activity_type=ActivityType.LISTENING, **activity)
            self._last_payload = activity.copy()
            self._last_update = now
        except Exception as exc:
            LOGGER.info("Discord Rich Presence update failed (will retry): %s", exc)
            self._close_client()
            self._last_payload = None
            self._retry_at = now + RETRY_SECONDS

    def close(self):
        self._close_client()
        self._last_payload = None
