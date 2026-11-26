"""Community reference implementation of a Windows HaulFM Overlay.

NOT the original source used to build HaulFM-Overlay.exe v1.2.21.
See source/README.md for limitations and building instructions.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import time
import webbrowser
from pathlib import Path

import webview
from radio import RadioClient

PROJECT_URL = "https://github.com/Walleyfire/haul-fm-stream-overlay"
DEFAULTS = {"language": "fi", "width": 600, "height": 198, "x": None, "y": None}


def source_path(name: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / name


def settings_file() -> Path:
    base = Path(os.environ.get("LOCALAPPDATA") or Path.home())
    return base / "HaulFM Overlay Source" / "settings.json"


def load_settings() -> dict:
    config = dict(DEFAULTS)
    try:
        state = json.loads(settings_file().read_text(encoding="utf-8"))
        if isinstance(state, dict):
            config.update({k: state[k] for k in DEFAULTS if k in state})
    except (OSError, ValueError):
        pass
    try:
        file_config = json.loads(source_path("config.json").read_text(encoding="utf-8"))
        if isinstance(file_config, dict):
            if file_config.get("language") in ("fi", "en"):
                config["language"] = file_config["language"]
            feed = file_config.get("dj_feed_url", "")
            config["dj_feed_url"] = feed if isinstance(feed, str) else ""
    except (OSError, ValueError):
        pass
    config["width"] = max(420, min(1400, int(config.get("width") or 600)))
    config["height"] = max(160, min(480, int(config.get("height") or 198)))
    return config


class Bridge:
    def __init__(self, config: dict):
        self.config = config
        self.window = None
        self.radio = RadioClient(config.get("dj_feed_url", ""))
        self.stop = threading.Event()
        self.ready = threading.Event()
        self._save_lock = threading.Lock()

    def config_for_ui(self):
        return {"language": self.config.get("language", "fi")}

    def check_updates(self):
        # This prototype does not replace executable files or bypass release checks.
        webbrowser.open(PROJECT_URL)
        return True

    def close_window(self):
        self.stop.set()
        if self.window:
            self.window.destroy()
        return True

    def resize_window(self, width: int, height: int):
        width = max(420, min(1400, int(width)))
        height = max(160, min(480, int(height)))
        if self.window:
            self.window.resize(width, height)
        return True

    def save_geometry(self, *unused):
        if not self.window or not self.ready.is_set():
            return
        try:
            x, y = self.window.get_position()
            state = {
                "language": self.config.get("language", "fi"),
                "width": self.window.width,
                "height": self.window.height,
                "x": x,
                "y": y,
            }
            path = settings_file()
            path.parent.mkdir(parents=True, exist_ok=True)
            with self._save_lock:
                temp = path.with_suffix(".tmp")
                temp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
                temp.replace(path)
        except (OSError, TypeError, ValueError, AttributeError):
            pass

    def on_loaded(self, *unused):
        self.ready.set()

    def on_closed(self, *unused):
        self.stop.set()

    def run(self):
        """Network calls occur in a worker; the UI thread is never blocked."""
        while not self.stop.is_set():
            data = self.radio.now_playing()
            data.update(self.radio.presenter())
            if self.window and self.ready.is_set():
                try:
                    self.window.evaluate_js("window.updateOverlay(" + json.dumps(data) + ")")
                except (RuntimeError, AttributeError, TypeError):
                    pass
            self.stop.wait(15)


def main():
    if sys.platform != "win32":
        raise SystemExit("This reference implementation requires Windows + WebView2.")
    parser = argparse.ArgumentParser(description="HaulFM Overlay reference source")
    parser.add_argument("--language", choices=("fi", "en"), help="UI language")
    args = parser.parse_args()
    config = load_settings()
    if args.language:
        config["language"] = args.language
    bridge = Bridge(config)
    width = config["width"]
    height = config["height"]
    coords = {}
    if isinstance(config.get("x"), int) and isinstance(config.get("y"), int):
        coords = {"x": config["x"], "y": config["y"]}
    win = webview.create_window(
        "HaulFM Overlay — reference",
        url=source_path("ui.html").as_uri(),
        width=width, height=height,
        resizable=True, min_size=(420, 160),
        frameless=True, easy_drag=False,
        shadow=False, on_top=True,
        js_api=bridge, **coords,
    )
    bridge.window = win
    win.events.loaded += bridge.on_loaded
    win.events.moved += bridge.save_geometry
    win.events.resized += bridge.save_geometry
    win.events.closed += bridge.on_closed
    webview.start(bridge.run, debug=False)


if __name__ == "__main__":
    main()
