"""Offline tests for the independent radio metadata implementation."""
import unittest
from radio import parse_icecast, parse_presenter, parse_song, similarity


class RadioParsingTests(unittest.TestCase):
    def test_separate_artist(self):
        self.assertEqual(parse_song("Don't Start Now", "Dua Lipa"),
                         ("Dua Lipa", "Don't Start Now"))

    def test_embedded_artist(self):
        self.assertEqual(parse_song("JORIS - Herz ueber Kopf"),
                         ("JORIS", "Herz ueber Kopf"))

    def test_reject_station_name(self):
        self.assertEqual(parse_song("Haul.FM"), ("", ""))

    def test_select_correct_mount(self):
        data = {"icestats": {"source": [
            {"mount": "/other.mp3", "title": "Wrong - Song"},
            {"listenurl": "http://stream.haul.fm:8000/haulmpfm.mp3",
             "artist": "JORIS", "title": "Herz ueber Kopf"},
        ]}}
        self.assertEqual(parse_icecast(data), ("JORIS", "Herz ueber Kopf"))

    def test_no_wrong_mount_when_multiple_exist(self):
        data = {"icestats": {"source": [
            {"mount": "/other.mp3", "title": "Wrong - Song"},
            {"mount": "/different.mp3", "title": "Other - Track"},
        ]}}
        self.assertEqual(parse_icecast(data), ("", ""))

    def test_live_dj(self):
        data = {"dj_live": True, "dj": {"name": "John Penn"},
                "show": "Night Shift with John"}
        self.assertEqual(parse_presenter(data), {
            "dj_live": True, "dj_name": "John Penn", "dj_show": "Night Shift with John",
        })

    def test_autodj_without_live_info(self):
        self.assertEqual(parse_presenter({}), {
            "dj_live": False, "dj_name": "Auto DJ", "dj_show": "",
        })

    def test_no_fake_dj_from_name_when_not_live(self):
        self.assertEqual(parse_presenter({"dj_live": False, "dj": "John Penn"}), {
            "dj_live": False, "dj_name": "Auto DJ", "dj_show": "",
        })

    def test_reject_bad_artwork_match(self):
        self.assertLess(similarity("Don't Start Now", "An unrelated track"), .84)


if __name__ == "__main__":
    unittest.main()
