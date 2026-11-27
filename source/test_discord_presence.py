"""Offline tests for Discord Rich Presence payloads and connection management."""
import sys
import types
import unittest
from unittest.mock import patch

from discord_presence import (
    DiscordRichPresence, FALLBACK_ARTWORK, build_activity, MIN_UPDATE_SECONDS,
)


LIVE_TRACK = {
    "status": "live",
    "artist": "JORIS",
    "title": "Herz ueber Kopf",
    "artwork": "https://is1-ssl.mzstatic.com/album-cover.jpg",
    "dj_live": True,
    "dj_name": "John Penn",
    "dj_show": "Night Shift with John",
}


class FakePresence:
    def __init__(self, application_id):
        self.application_id = application_id
        self.connected = False
        self.updates = []
        self.cleared = 0
        self.closed = 0
        self.fail_update = False

    def connect(self):
        self.connected = True

    def update(self, **kwargs):
        if self.fail_update:
            raise OSError("Discord connection closed")
        self.updates.append(kwargs)

    def clear(self):
        self.cleared += 1

    def close(self):
        self.closed += 1


class DiscordPayloadTests(unittest.TestCase):
    def test_live_dj_track_and_cover(self):
        payload = build_activity(LIVE_TRACK)
        self.assertEqual(payload["details"], "Herz ueber Kopf — JORIS")
        self.assertEqual(payload["state"], "LIVE DJ: John Penn")
        self.assertEqual(payload["large_image"], LIVE_TRACK["artwork"])
        self.assertEqual(payload["small_image"], FALLBACK_ARTWORK)
        self.assertEqual(payload["small_text"], "Night Shift with John")

    def test_auto_dj_and_fallback_cover(self):
        payload = build_activity({
            **LIVE_TRACK, "dj_live": False, "dj_name": "John Penn",
            "dj_show": "", "artwork": None,
        })
        self.assertEqual(payload["state"], "Auto DJ")
        self.assertEqual(payload["large_image"], FALLBACK_ARTWORK)

    def test_unavailable_clears_activity(self):
        self.assertIsNone(build_activity({"status": "unavailable", "title": "Old song"}))
        self.assertIsNone(build_activity({"status": "live", "title": ""}))

    def test_cover_rejects_untrusted_schemes(self):
        for image in ("file:///C:/private/cover.png", "http://example.org/image.jpg",
                      "https://user:pass@example.com/image.jpg", "javascript:alert(1)"):
            payload = build_activity({**LIVE_TRACK, "artwork": image})
            self.assertEqual(payload["large_image"], FALLBACK_ARTWORK)

    def test_details_always_fit_discord_limits(self):
        payload = build_activity({**LIVE_TRACK, "title": "T" * 400, "artist": "A" * 400})
        self.assertLessEqual(len(payload["details"]), 128)
        self.assertLessEqual(len(payload["state"]), 128)

    def test_application_id_required(self):
        self.assertFalse(DiscordRichPresence("").enabled)
        self.assertFalse(DiscordRichPresence("not-an-id").enabled)

    def test_updates_throttle_and_clear(self):
        now = [100]
        clients = []
        def make_client(application_id):
            clients.append(FakePresence(application_id))
            return clients[-1]
        pretend_types = types.ModuleType("pypresence.types")
        pretend_types.ActivityType = types.SimpleNamespace(LISTENING=2)
        with patch.dict(sys.modules, {"pypresence.types": pretend_types}):
            rpc = DiscordRichPresence(
                "123456789012345678", rpc_factory=make_client, clock=lambda: now[0]
            )
            rpc.update(LIVE_TRACK)
            self.assertEqual(len(clients), 1)
            self.assertEqual(len(clients[0].updates), 1)
            self.assertEqual(clients[0].updates[0]["activity_type"], 2)
            rpc.update(LIVE_TRACK)
            self.assertEqual(len(clients[0].updates), 1)

            change = {**LIVE_TRACK, "title": "Different song", "artist": "Different artist"}
            now[0] += 10
            rpc.update(change)
            self.assertEqual(len(clients[0].updates), 1)
            now[0] += MIN_UPDATE_SECONDS
            rpc.update(change)
            self.assertEqual(len(clients[0].updates), 2)
            self.assertEqual(clients[0].updates[1]["details"],
                             "Different song — Different artist")

            rpc.update({"status": "unavailable"})
            self.assertEqual(clients[0].cleared, 1)
            rpc.close()
            self.assertEqual(clients[0].closed, 1)

    def test_retry_connection_when_discord_starts_later(self):
        now = [100.0]
        attempts = []
        clients = []
        def flaky(application_id):
            attempts.append(application_id)
            if len(attempts) == 1:
                raise ConnectionError("Discord is not running")
            client = FakePresence(application_id)
            clients.append(client)
            return client
        pretend_types = types.ModuleType("pypresence.types")
        pretend_types.ActivityType = types.SimpleNamespace(LISTENING=2)
        with patch.dict(sys.modules, {"pypresence.types": pretend_types}):
            rpc = DiscordRichPresence(
                "123456789012345678", rpc_factory=flaky, clock=lambda: now[0]
            )
            rpc.update(LIVE_TRACK)
            self.assertEqual(len(attempts), 1)
            now[0] += 10
            rpc.update(LIVE_TRACK)
            self.assertEqual(len(attempts), 1)
            now[0] += 30
            rpc.update(LIVE_TRACK)
            self.assertEqual(len(attempts), 2)
            self.assertEqual(len(clients[0].updates), 1)


if __name__ == "__main__":
    unittest.main()
