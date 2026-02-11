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
py -3 -m venv .venv
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
| `MIDI_PORT_NAME` | `None` | MIDI input port (None = first available) |
| `MIDI_MAP` | see code | Maps MIDI note numbers to loop/kill actions |
| `TEST_MODE` | `False` | Skip MIDI, immediately start first loop |
| `MIDI_DEBUG` | `False` | Log all MIDI input, skip OBS connection |

## MIDI Map

The MIDI map controls which note triggers which action. You can configure it in two ways:

### Option 1: `config.json` (recommended)

Copy the example file and edit it:

```bash
cp config.example.json config.json
```

The JSON file maps MIDI note numbers (as strings) to action objects:

```json
{
  "48": {"action": "loop", "prefix": "LOOP_A_", "style": "cycle", "bpm": 120, "steps": 4},
  "43": {"action": "kill", "scene": "STATIC_1"}
}
```

The script loads `config.json` on startup. If the file doesn't exist, it falls back to the hardcoded default in `main.py`.

> `config.json` is gitignored so your personal config won't be committed.

### Option 2: Edit `DEFAULT_MIDI_MAP` in `main.py`

If you prefer not to use a separate file, edit the `DEFAULT_MIDI_MAP` dict directly in the code. This is used as the fallback when no `config.json` is present.

### Action types

**Loop** — cycle through all OBS scenes matching a prefix:

```json
{"action": "loop", "prefix": "LOOP_A_", "style": "cycle", "bpm": 120, "steps": 4}
```

- `bpm` — tempo in beats per minute
- `steps` — number of beats per scene switch
- Scene switch interval = `(60 / bpm) * steps` seconds (e.g. 120 BPM, 4 steps = 2.0s)

**Kill** — stop any running loop and switch to a static scene:

```json
{"action": "kill", "scene": "STATIC_1"}
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

**Sequence** — run a series of loop/kill/stop/pause steps in order:

Sequences loop continuously by default. After the last step, the sequence wraps back to step 1. Use a terminal action (`kill` or `stop`) as the last step to end the sequence instead.

```json
{
  "action": "sequence",
  "steps": [
    {"action": "loop", "prefix": "LOOP_A_", "style": "cycle",  "bpm": 120, "steps": 4, "repeats": 3},
    {"action": "pause"},
    {"action": "loop", "prefix": "LOOP_A_", "style": "bounce", "bpm": 120, "steps": 2, "repeats": 2},
    {"action": "kill", "scene": "STATIC_1"}
  ]
}
```

- `repeats` controls how many full cycles a step runs before advancing to the next step (default: 1)
- Sequences loop continuously — omit a terminal action to repeat forever
- `kill` as the last step ends the sequence and switches to a static scene
- `stop` as the last step ends the sequence silently (holds the last scene)
- `pause` holds the current scene until the resume note is pressed
- Pressing any other mapped MIDI note cancels the running sequence

## Loop Styles

| Style | Behaviour |
|---|---|
| `cycle` | Forward loop: 1, 2, 3, 1, 2, 3 … |
| `bounce` | Ping-pong: 1, 2, 3, 2, 1, 2, 3 … |
| `reverse` | Backward loop: 3, 2, 1, 3, 2, 1 … |
| `once` | Play forward then hold on last scene: 1, 2, 3 → stop |
| `random` | Random scene each beat |
| `random_no_repeat` | Random, never the same scene twice in a row |
| `strobe` | Alternate between first and last scene |
| `shuffle` | Randomize order once, then cycle that order |

Each entry has `bpm` and `steps` values so you can control the speed per loop in musical terms.

## Sequencer

Sequences let you chain multiple actions together. They loop continuously by default — after the last step, the sequence wraps back to step 1.

### Step types

| Action | Description |
|---|---|
| `loop` | Run a loop for a number of repeats (default: 1), then advance |
| `pause` | Hold the current scene until the resume note is pressed |
| `kill` | Switch to a static scene and **end** the sequence |
| `stop` | **End** the sequence without changing the scene |

`kill` and `stop` are **terminal actions** — the sequence ends when it reaches one. If the last step is a `loop`, the sequence wraps back to step 1 and keeps going.

### Example: loop forever

```json
{"action": "sequence", "steps": [
  {"action": "loop", "prefix": "LOOP_A_", "style": "cycle",  "bpm": 120, "steps": 4, "repeats": 2},
  {"action": "loop", "prefix": "LOOP_A_", "style": "bounce", "bpm": 120, "steps": 2, "repeats": 3}
]}
```

### Example: loop then end on a static scene

```json
{"action": "sequence", "steps": [
  {"action": "loop", "prefix": "LOOP_A_", "style": "cycle", "bpm": 120, "steps": 4, "repeats": 2},
  {"action": "kill", "scene": "STATIC_1"}
]}
```

### Example: pause mid-sequence

```json
{"action": "sequence", "steps": [
  {"action": "loop", "prefix": "LOOP_A_", "style": "cycle",  "bpm": 120, "steps": 4, "repeats": 2},
  {"action": "pause"},
  {"action": "loop", "prefix": "LOOP_A_", "style": "bounce", "bpm": 120, "steps": 2, "repeats": 2},
  {"action": "stop"}
]}
```

When the sequence hits `pause`, it holds the current scene and waits. Press the same MIDI note that started the sequence to resume. To use a different resume note, set `"resume_note"`:

```json
{"action": "pause", "resume_note": 42}
```

Pressing any other mapped MIDI note cancels the sequence entirely.

## Usage

1. Open OBS and enable the WebSocket server (Tools → WebSocket Server Settings).
2. Create scenes with a shared prefix, e.g. `LOOP_A_1`, `LOOP_A_2`, `LOOP_A_3`. Scenes are natural-sorted so numeric order is preserved.
3. Run the script:

```bash
python main.py
```

4. Press a mapped MIDI note to **start** cycling the corresponding scene set.
5. Press a different mapped note to **switch** to another loop (the previous loop stops automatically).
6. Press a kill switch note to **stop** cycling and switch to a static scene.

### MIDI Debug Mode

Set `MIDI_DEBUG = True` to skip the OBS connection and just log incoming MIDI messages. Useful for finding out which note numbers your controller sends.

### Test Mode

Set `TEST_MODE = True` to skip MIDI input and immediately start the first loop action from `MIDI_MAP`. Useful for verifying scene switching without a MIDI device.

## Tests

```bash
python -m pytest test_main.py -v
```
