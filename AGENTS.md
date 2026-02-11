# MIDI OBS Controller — Project Brief

## What this is

A Python script that runs alongside OBS Studio during live music concerts. It lets a performer trigger visual loops and sequences on a projector via a MIDI controller (e.g. a pad controller or keyboard).

Press a MIDI note → OBS cycles through a set of scenes matching a prefix. Different notes trigger different visual sets, loop styles, and speeds. A kill switch stops cycling and locks to a static scene.

## Architecture

Single-file script (`main.py`) with no web server or UI. Connects to OBS via WebSocket (`obsws-python`) and listens for MIDI input (`mido` with `pygame` backend). All scene switching runs in a background thread controlled by a `threading.Event` for clean start/stop.

### Key concepts

- **MIDI_MAP** — dict mapping MIDI note numbers to actions (loop, kill, stop, or sequence)
- **Loop styles** — cycle, bounce, reverse, once, random, random_no_repeat, strobe, shuffle
- **Timing** — BPM + steps (beats per scene switch). `calc_tick(bpm, steps)` converts to seconds: `(60 / bpm) * steps`
- **Sequences** — ordered list of loop/kill/stop/pause steps with per-step repeat counts; loops continuously by default
- **Terminal actions** — `kill` (switch to static scene and end) or `stop` (end silently) to terminate a sequence
- **Pause** — holds the current scene until the resume note is pressed (defaults to trigger note, configurable via `resume_note`)
- **Kill switch** — stops any running loop and switches to a static scene
- **Config** — `config.json` (optional, gitignored) overrides `DEFAULT_MIDI_MAP` in code

### Files

| File | Purpose |
|---|---|
| `main.py` | All application logic |
| `config.json` | User MIDI map config (gitignored) |
| `config.example.json` | Template config committed to repo |
| `test_main.py` | Unit tests (pytest) |
| `requirements.txt` | Python dependencies |
| `.github/workflows/test.yml` | CI — runs tests on push/PR to main |

## Tech stack

- Python 3.9+
- `mido` + `pygame` — MIDI input (pure Python, no compiler needed)
- `obsws-python` — OBS WebSocket client
- `pytest` — testing

## Conventions

- All config lives at the top of `main.py` (OBS connection, MIDI port, debug flags)
- MIDI map can be configured via `config.json` or `DEFAULT_MIDI_MAP` in code
- Scene names use prefixes (e.g. `LOOP_A_1`, `LOOP_A_2`) and are natural-sorted
- Only one loop/sequence runs at a time — starting a new one cancels the previous
- Cross-platform: macOS, Windows, Linux
