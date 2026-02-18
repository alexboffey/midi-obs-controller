# MIDI OBS Controller — Project Brief

## What this is

A Python script that runs alongside OBS Studio during live music concerts. It lets a performer trigger visual loops and sequences on a projector via a MIDI controller (e.g. a pad controller or keyboard).

Press a MIDI note → OBS cycles through a set of scenes matching a prefix. Different notes trigger different visual sets, loop styles, and speeds. A static-scene action stops cycling and switches to a static scene.

## Architecture

Single-file script (`app/main.py`) with no web server or UI. Connects to OBS via WebSocket (`obsws-python`) and listens for MIDI input (`mido` with `pygame` backend). All scene switching runs in a background thread controlled by a `threading.Event` for clean start/stop.

A companion web GUI (`gui/`) is a Svelte 5 + Vite app that uses the Web MIDI API to listen for MIDI input and build `config.json` files visually, then export them to `app/`.

### Key concepts

- **MIDI_MAP** — dict mapping MIDI note numbers to actions (loop, static, stop, or sequence)
- **Loop styles** — cycle, bounce, reverse, once, random, random_no_repeat, strobe, shuffle
- **Timing** — BPM + steps (beats per scene switch). `calc_tick(bpm, steps)` converts to seconds: `(60 / bpm) * steps`
- **Sequences** — ordered list of loop/static/stop/pause steps with per-step repeat counts; loops continuously by default
- **Terminal actions** — `static` (switch to static scene and end) or `stop` (end silently) to terminate a sequence
- **Pause** — holds the current scene until the resume note is pressed (defaults to trigger note, configurable via `resume_note`)
- **Static scene** — stops any running loop and switches to a static scene
- **Config** — `config.json` (optional, gitignored) overrides `DEFAULT_MIDI_MAP` in code. If multiple `*.json` files exist in `app/`, the user is prompted to pick one via `questionary`
- **Coloured logging** — all `print()` calls in `main.py` use `_log(colour, tag, msg)` with ANSI codes (disabled when stdout is not a TTY)

### Files

| File | Purpose |
|---|---|
| `app/main.py` | All application logic |
| `app/config.json` | User MIDI map config (gitignored) |
| `app/config.example.json` | Template config committed to repo |
| `app/test_main.py` | Unit tests (pytest) |
| `app/requirements.txt` | Python dependencies |
| `app/midi-obs-controller.spec` | PyInstaller build spec |
| `gui/` | Svelte 5 + Vite + TypeScript config-builder GUI (see `gui/README.md`) |
| `gui/src/lib/types.ts` | Shared TypeScript types for all action configs |
| `gui/src/lib/store.svelte.ts` | Reactive config store (`$state` rune) |
| `gui/src/lib/noteNames.ts` | MIDI note number → name helper |
| `gui/src/components/` | UI components: NoteList, NoteEditor, LoopEditor, StaticEditor, SequenceEditor, SequenceStepEditor |
| `.github/workflows/ci.yml` | CI — runs tests on push/PR to main; builds exe and publishes a "Latest" GitHub Release on push to main (after tests pass) |
| `.github/workflows/deploy-gui.yml` | Deploys GUI to GitHub Pages on push to main (path-filtered to `gui/**`) |

## Tech stack

**Python app (`app/`):**
- Python 3.9+
- `mido` + `pygame` — MIDI input (pure Python, no compiler needed)
- `obsws-python` — OBS WebSocket client
- `questionary` — arrow-key terminal selector for multi-config picker
- `pytest` — testing
- `pyinstaller` — builds a standalone `app/dist/midi-obs-controller.exe`

**GUI (`gui/`):**
- Svelte 5 + Vite + TypeScript — component framework with `$state` runes and `<script lang="ts">`
- Tailwind CSS v4 via `@tailwindcss/vite`
- Web MIDI API — browser MIDI device access (requires localhost or HTTPS)
- Deployed automatically to GitHub Pages via `.github/workflows/deploy-gui.yml`

## Conventions

- All config lives at the top of `app/main.py` (OBS connection, MIDI port, debug flags)
- MIDI map can be configured via `config.json` or `DEFAULT_MIDI_MAP` in code
- Scene names use prefixes (e.g. `LOOP_A_1`, `LOOP_A_2`) and are natural-sorted
- Only one loop/sequence runs at a time — starting a new one cancels the previous
- Cross-platform: macOS, Windows, Linux

## When making changes

- **Tests** — write or update unit tests in `app/test_main.py` for any new or changed behavior. Run `cd app && python -m pytest test_main.py -v` to verify.
- **Documentation** — update `README.md` when adding features, changing config format, or modifying behavior. Keep the action types, loop styles, and sequencer sections current.
- **AGENTS.md** — update this file if the architecture, key concepts, or conventions change.
- **GUI** — run `cd gui && npm install && npm run dev` to develop. TypeScript types live in `gui/src/lib/types.ts` — update them when the config format changes. Run `npm run check` for type checking.
