# MIDI → OBS Scene Controller

Listens for MIDI input and switches OBS scenes based on a configurable note map.
Supports looping, static scenes, pause/resume, and multi-step sequences.

---

## Config Builder GUI

The easiest way to build your `config.json` is the web GUI — available at the GitHub Pages deployment or run it locally from the **repo root**:

```bash
cd gui
npm install
npm run dev
```

Open the app, connect your MIDI device, press pads in listen mode to map them, browse your live OBS scene list, then export the file directly into `app/`.

See [gui/README.md](gui/README.md) for full GUI documentation.

---

## Python App Setup

> **Requires Python 3.12.** Python 3.13+ is not supported — `pygame` has no pre-built wheels for it and will fail to install. Download Python 3.12 from [python.org](https://www.python.org/downloads/release/python-31210/) if needed.

Run these commands from the **repo root**:

**macOS / Linux:**

```bash
cd app
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Windows (PowerShell):**

```powershell
cd app
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

> **Note:** If you get a PowerShell execution policy error, run
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` first.

**Windows (Command Prompt):**

```cmd
cd app
py -3.12 -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
```

---

## Configuration

### OBS connection

Copy `.env.example` to `app/.env` and set your OBS WebSocket credentials:

```
OBS_HOST=localhost
OBS_PORT=4455
OBS_PASSWORD=your_password
```

### MIDI map

Copy the example config and edit it, or use the GUI to generate it:

```bash
cp app/config.example.json app/config.json
```

The JSON file maps MIDI note numbers (as strings) to action objects:

```json
{
  "48": {"action": "loop", "prefix": "LOOP_A_", "style": "cycle", "bpm": 120, "steps": 4},
  "43": {"action": "static", "scene": "STATIC_1"}
}
```

> `config.json` is gitignored — your personal config won't be committed.

If you place multiple `*.json` files in `app/`, the script will show an arrow-key picker on startup so you can choose between them.

### Action types

**Loop** — cycle through all OBS scenes matching a prefix:

```json
{"action": "loop", "prefix": "LOOP_A_", "style": "cycle", "bpm": 120, "steps": 4}
```

- `bpm` — tempo in beats per minute
- `steps` — number of beats per scene switch
- Scene switch interval = `(60 / bpm) * steps` seconds (e.g. 120 BPM, 4 steps = 2.0s)

**Static** — stop any running loop and switch to a static scene:

```json
{"action": "static", "scene": "STATIC_1"}
```

**Stop** — end a sequence without changing the scene:

```json
{"action": "stop"}
```

**Pause** — hold the current scene until resumed:

```json
{"action": "pause"}
{"action": "pause", "resume_note": 42}
```

By default the resume note is the same MIDI note that started the sequence. Use `resume_note` to override. Pressing any other mapped note cancels the sequence.

**Sequence** — run a series of loop/static/stop/pause steps in order:

```json
{
  "action": "sequence",
  "steps": [
    {"action": "loop", "prefix": "LOOP_A_", "style": "cycle",  "bpm": 120, "steps": 4, "repeats": 3},
    {"action": "pause"},
    {"action": "loop", "prefix": "LOOP_A_", "style": "bounce", "bpm": 120, "steps": 2, "repeats": 2},
    {"action": "static", "scene": "STATIC_1"}
  ]
}
```

- `repeats` controls how many full cycles a step runs before advancing (default: 1)
- Sequences loop continuously — omit a terminal action to repeat forever
- `static` as the last step ends the sequence and switches to that scene
- `stop` as the last step ends the sequence silently (holds the last scene)

### Loop styles

| Style | Behaviour |
|---|---|
| `cycle` | Forward loop: 1, 2, 3, 1, 2, 3 … |
| `bounce` | Ping-pong: 1, 2, 3, 2, 1, 2, 3 … |
| `reverse` | Backward loop: 3, 2, 1, 3, 2, 1 … |
| `once` | Play forward then hold on last scene |
| `random` | Random scene each beat |
| `random_no_repeat` | Random, never the same scene twice in a row |
| `strobe` | Alternate between first and last scene |
| `shuffle` | Randomize order once, then cycle that order |

---

## Usage

1. Open OBS and enable the WebSocket server (Tools → WebSocket Server Settings).
2. From the **repo root**, activate the venv and run the script:

**macOS / Linux:**
```bash
cd app
source .venv/bin/activate
python main.py
```

**Windows (PowerShell):**
```powershell
cd app
.\.venv\Scripts\Activate.ps1
python main.py
```

**Windows (Command Prompt):**
```cmd
cd app
.venv\Scripts\activate.bat
python main.py
```

3. If multiple `*.json` config files are present in `app/`, use the arrow keys to select one.
4. Press a mapped MIDI note to **start** the corresponding action.
5. Press a different note to **switch** (the previous loop stops automatically).

### Debug / test flags

Edit the flags at the top of `app/main.py`:

| Variable | Effect |
|---|---|
| `MIDI_DEBUG = True` | Skip OBS connection, log all raw MIDI input — useful for finding note numbers |
| `TEST_MODE = True` | Skip MIDI, immediately start the first loop action — useful for testing scene switching |

---

## Building the exe

From the **repo root** with the venv activated:

```powershell
cd app
pip install pyinstaller
pyinstaller midi-obs-controller.spec
```

Output: `app/dist/midi-obs-controller.exe` — runs without Python installed.

The CI `release` job also builds and publishes the exe automatically to the **Latest** GitHub Release on every push to `main`.

---

## Tests

From the **repo root**:

```bash
cd app
python -m pytest test_main.py -v
```
