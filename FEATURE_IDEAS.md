# Feature Ideas

A backlog of ideas for future development.

## Planned

_Nothing here yet — move ideas up from below when ready to build._

## Ideas

- **MIDI CC for dynamic VJ parameters** — use MIDI CC (continuous controller) messages to control real-time parameters in OBS (e.g. filter opacity, source transforms, colour correction) rather than just note-on triggers for scene switching
- **OBS configuration scripting** — store video assets (via Git LFS), scene collection configs, and other OBS resources in the repo. Provide a setup script that places them in the correct OS-specific OBS directories so the full live set can be imported to OBS on a fresh machine
- **Configurable MIDI ports / multiple controllers** — support specifying which MIDI port(s) to listen to (e.g. by name or device ID) and/or accept input from multiple controllers at once (e.g. pad controller for scenes + keyboard for CC)

## Project ideas

- **MIDI sequencer integration for visuals timed to music** — run this controller alongside a MIDI sequencer (e.g. DAW or hardware) so scene changes, loops, and sequences are triggered in time with the music rather than only manually
