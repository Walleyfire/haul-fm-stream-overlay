# HaulFM Overlay — New source-code edition

This folder contains **the actual editable source code for a new HaulFM Overlay implementation**. It is not copied from TruckersFM, and it is not an attempted decompilation of the old binary.

> **Version distinction:** The existing precompiled `HaulFM-Overlay.exe` and `HaulFM Overlay installer.exe` in the repository root are the **v1.2.21 legacy release**. The files in this folder build a **separate new source-first release**, currently called **HaulFM-Overlay-New**. This project does not claim to reproduce the exact old EXE.

## Source files

| File | Purpose |
| --- | --- |
| `app.py` | Windows window, WebView2 presentation, 15-second refresh, dragging/resizing, bilingual settings and menu |
| `radio.py` | Icecast/ICY track metadata, album art and duration lookup, optional presenter feed and Auto DJ |
| `discord_presence.py` | Discord Rich Presence RPC: song, artist, presenter and artwork |
| `ui.html` | Complete editable overlay interface (HTML, CSS and JavaScript) |
| `config.example.json` | Example settings; copy to `config.json` |
| `requirements.txt` | Runtime dependency |
| `test_radio.py` | Offline data parsing tests |
| `test_discord_presence.py` | Offline Rich Presence formatting, fallback, reconnect and throttling tests |
| `build.ps1` | Builds the **new** Windows EXE from the files in this folder |
| `installer.iss` | Optional Inno Setup installer script for the **new** EXE |

## Run directly (Windows)

Requires Python 3.11 or later, plus Microsoft Edge WebView2 Runtime.

```powershell
cd source
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m unittest discover -s . -p "test_*.py"
python app.py --language fi
```

Use `--language en` for English labels. Right-click the overlay to access its menu. The window remembers its position and size under `%LOCALAPPDATA%\HaulFM Overlay Source\settings.json`.

The program does not play radio audio; like the current desktop release, it displays metadata. The progress bar is shown only when the duration of the current track is known. Song time is an estimate starting from first detection, **not** synchronized audio playback time.

## Build the new Windows EXE

In PowerShell, inside `source/`:

```powershell
.\build.ps1
```

The build produces:

```text
source/dist/HaulFM-Overlay-New.exe
```

The name intentionally differs from the old `HaulFM-Overlay.exe` so the existing user-installed release cannot be overwritten by accident. To create an installer, open `installer.iss` with Inno Setup 6 after building the EXE and compile it. The installer is also distinctly named.

The GitHub Actions workflow `.github/workflows/source-build.yml` runs the offline tests and builds the Windows EXE from **this exact committed source code**, then uploads the resulting build as an Actions artifact. The artifact is not automatically published as the legacy release.

## Discord Rich Presence

The new overlay can publish its current radio status to the **locally running Discord desktop app**:

- Activity type: **Listening to HaulFM Overlay New** (the Discord application name is set in the Developer Portal).
- Details: \`Herz ueber Kopf — JORIS\` (track and artist).
- State: \`LIVE DJ: John Penn\`, or \`Auto DJ\` when a live presenter has not been confirmed.
- Large image: the track's public HTTPS album art; fallback to the Haul.FM icon (\`https://haul.fm/brand/icon-96.webp\`).
- Small image: Haul.FM icon; hovering displays the DJ show title when known.

Discord supports **external image URLs** for its Rich Presence activity assets; Discord will load them through its media proxy. The URL must be publicly accessible, and Discord may fail to render certain images. Discord Rich Presence does **not** need a Discord bot token or user token.

### Setup (required once)

1. Open https://discord.com/developers/applications and select **New Application** (for example, *HaulFM Overlay New*).
2. In **General Information**, copy the numeric **Application ID**. This is a public application identifier, not the bot token or client secret.
3. In \`source/\`, copy \`config.example.json\` to \`config.json\` and set:

   \`\`\`json
   {
     "language": "fi",
     "dj_feed_url": "",
     "discord_rich_presence": true,
     "discord_application_id": "YOUR_NUMERIC_APPLICATION_ID"
   }
   \`\`\`

4. Run \`python app.py\` or build a new EXE with \`build.ps1\`. When running the EXE, put the \`config.json\` file **next to** \`HaulFM-Overlay-New.exe\` (not in the bundled EXE).
5. Open the Discord **desktop** app and enable **Activity Privacy / Share your activity** in Discord settings. Rich Presence cannot be displayed just by opening Discord in a browser.
6. Start the new overlay. Your Discord activity updates when a new song or live DJ is detected, with a minimum 15-second interval.

If Discord is closed, the overlay keeps running and retries the RPC connection roughly every 30 seconds. Closing the overlay closes its RPC session. Set \`discord_rich_presence\` to \`false\` to disable it, or leave \`discord_application_id\` empty to keep it inactive.

**Important limitations:** A real live presenter is shown only if the optional \`dj_feed_url\` provides confirmed DJ metadata. The correct Haul.FM presenter feed is not yet verified in this source repository, so without setting it, Rich Presence will display **Auto DJ**. The overlay shows metadata only; it does not itself play radio audio. Album cover images come from the song lookup and are not guaranteed for every track.

## Live presenter / Auto DJ

The new implementation displays **Auto DJ** unless an external feed confirms that a presenter is live. This avoids showing a stale or invented DJ name.

The legacy release apparently uses a Haul.FM presenter feed, but its exact endpoint and schema are not part of the available sources. The new version **does not yet have a verified official DJ endpoint**. When a compatible HTTPS JSON endpoint becomes available:

1. Copy `config.example.json` to `config.json`.
2. Set `dj_feed_url` to the known public endpoint, without secrets.
3. If its JSON field names differ, adjust `parse_presenter()` in `radio.py`.

The example parser recognizes `dj_live`, `dj`/`presenter` name, and `show` name, but these fields are an example protocol **not a claim about Haul.FM's real API**.

## Limitations

- The current, prebuilt v1.2.21 executable was not built from this folder. The new version must be built and tested separately before being considered a replacement.
- The generated EXE is not digitally signed. Windows may display a SmartScreen warning.
- Network access is required to fetch radio metadata and cover art.
- The HTML and Python parser code can be changed without modifying the existing binaries.
- No secrets or access tokens belong in the repository.

## Testing

```powershell
cd source
python -m unittest discover -s . -p "test_*.py"
```
