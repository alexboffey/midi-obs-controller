# MIDI → OBS Scene Controller

Listens for MIDI input and cycles through OBS scenes that match a given prefix.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuration

Edit the variables at the top of `main.py`:

| Variable | Default | Description |
|---|---|---|
| `OBS_HOST` | `localhost` | OBS WebSocket host |
| `OBS_PORT` | `4455` | OBS WebSocket port |
| `OBS_PASSWORD` | `""` | OBS WebSocket password |
| `SCENE_PREFIX` | `SONG_A_` | Only scenes starting with this are cycled |
| `TICK_RATE` | `2.0` | Seconds between scene switches |
| `MIDI_PORT_NAME` | `None` | MIDI input port (None = first available) |

## Usage

1. Open OBS and enable the WebSocket server (Tools → WebSocket Server Settings).
2. Create scenes with a shared prefix, e.g. `SONG_A_intro`, `SONG_A_verse`, `SONG_A_chorus`.
3. Run the script:

```bash
python main.py
```

4. Press any MIDI note to **start** looping through the matched scenes.
5. Press any MIDI note again to **stop** looping.
