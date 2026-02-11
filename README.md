# MIDI → OBS Scene Controller

Listens for MIDI input and cycles through OBS scenes that match a given prefix.

## Setup

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Windows (PowerShell):**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

> **Note:** If you get a PowerShell execution policy error, run
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` first.

**Windows (Command Prompt):**

```cmd
python -m venv .venv

.venv\Scripts\activate.bat
pip install -r requirements.txt
```

## Configuration

Edit the variables at the top of `main.py`:

| Variable | Default | Description |
|---|---|---|
| `OBS_HOST` | `localhost` | OBS WebSocket host |
| `OBS_PORT` | `4455` | OBS WebSocket port |
| `OBS_PASSWORD` | `""` | OBS WebSocket password |
| `TICK_RATE` | `2.0` | Seconds between scene switches |
| `MIDI_PORT_NAME` | `None` | MIDI input port (None = first available) |
| `MIDI_MAP` | see code | Maps MIDI note numbers to loop/kill actions |
| `TEST_MODE` | `False` | Skip MIDI, immediately start first loop |
| `MIDI_DEBUG` | `False` | Log all MIDI input, skip OBS connection |

## Usage

1. Open OBS and enable the WebSocket server (Tools → WebSocket Server Settings).
2. Create scenes with a shared prefix, e.g. `SONG_A_intro`, `SONG_A_verse`, `SONG_A_chorus`.
3. Run the script:

```bash
python main.py
```

4. Press a mapped MIDI note to **start** cycling the corresponding scene set.
5. Press a kill switch note to **stop** cycling and switch to a static scene.
