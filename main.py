import json
import os
import random
import re
import time
import threading

import mido
mido.set_backend("mido.backends.pygame")
import obsws_python as obs

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# OBS WebSocket connection
OBS_HOST = "localhost"
OBS_PORT = 4455
OBS_PASSWORD = "HrCDuVNv7Sfxdxzi"

# Set to a specific port name, or None to pick the first available input
MIDI_PORT_NAME = None

# Set to True to skip MIDI and immediately start the first loop action
TEST_MODE = False

# Set to True to log all incoming MIDI messages and skip OBS connection
MIDI_DEBUG = False

# ---------------------------------------------------------------------------
# MIDI Note → Action mapping
# ---------------------------------------------------------------------------
# Each entry maps a MIDI note number to an action dict.
#
# --- Kill action (stop loop, switch to a static scene) ---
#   {"action": "kill", "scene": "STATIC_1"}
#
# --- Loop actions (cycle through scenes matching a prefix) ---
# Each loop action requires: action, prefix, style, tick
#
# "cycle" – loops forward: 1,2,3,1,2,3 …
#   {"action": "loop", "prefix": "LOOP_A_", "style": "cycle", "tick": 2.0}
#
# "bounce" – ping-pong: 1,2,3,2,1,2,3,2,1 …
#   {"action": "loop", "prefix": "LOOP_A_", "style": "bounce", "tick": 2.0}
#
# "reverse" – loops backward: 3,2,1,3,2,1 …
#   {"action": "loop", "prefix": "LOOP_A_", "style": "reverse", "tick": 2.0}
#
# "once" – plays forward then holds on last scene: 1,2,3 → stop
#   {"action": "loop", "prefix": "LOOP_A_", "style": "once", "tick": 2.0}
#
# "random" – picks a random scene each tick
#   {"action": "loop", "prefix": "LOOP_A_", "style": "random", "tick": 0.5}
#
# "random_no_repeat" – random, but never the same scene twice in a row
#   {"action": "loop", "prefix": "LOOP_A_", "style": "random_no_repeat", "tick": 0.5}
#
# "strobe" – alternates between first and last scene
#   {"action": "loop", "prefix": "LOOP_A_", "style": "strobe", "tick": 0.25}
#
# "shuffle" – randomizes scene order once, then cycles that order
#   {"action": "loop", "prefix": "LOOP_A_", "style": "shuffle", "tick": 2.0}
#
# Note numbers: C2=36 … C3=48 … (MIDI convention where C3 = 48)

DEFAULT_MIDI_MAP = {
    36: {"action": "loop", "prefix": "LOOP_A_", "style": "cycle",            "tick": 2.0},  # C2
    37: {"action": "loop", "prefix": "LOOP_A_", "style": "bounce",           "tick": 2.0},  # C#2
    38: {"action": "loop", "prefix": "LOOP_A_", "style": "reverse",          "tick": 2.0},  # D2
    39: {"action": "loop", "prefix": "LOOP_A_", "style": "once",             "tick": 2.0},  # D#2
    40: {"action": "loop", "prefix": "LOOP_A_", "style": "random",           "tick": 1.0},  # E2
    41: {"action": "loop", "prefix": "LOOP_A_", "style": "random_no_repeat", "tick": 1.0},  # F2
    42: {"action": "loop", "prefix": "LOOP_A_", "style": "strobe",           "tick": 0.5},  # F#2
    43: {"action": "loop", "prefix": "LOOP_A_", "style": "shuffle",          "tick": 2.0},  # G2
    44: {"action": "loop", "prefix": "LOOP_H_", "style": "cycle",            "tick": 2.0},  # G#2
    45: {"action": "loop", "prefix": "LOOP_I_", "style": "cycle",            "tick": 2.0},  # A2
    46: {"action": "loop", "prefix": "LOOP_J_", "style": "cycle",            "tick": 2.0},  # A#2
    47: {"action": "loop", "prefix": "LOOP_K_", "style": "cycle",            "tick": 2.0},  # B2
    48: {"action": "loop", "prefix": "LOOP_L_", "style": "cycle",            "tick": 2.0},  # C3
    49: {"action": "loop", "prefix": "LOOP_M_", "style": "bounce",           "tick": 1.5},  # C#3
    50: {"action": "loop", "prefix": "LOOP_N_", "style": "cycle",            "tick": 2.0},  # D3
    51: {"action": "kill", "scene": "STATIC_2"},                                             # D#3
}

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")


def load_config(path: str = CONFIG_PATH) -> dict[int, dict]:
    """Load MIDI_MAP from a JSON config file.

    The JSON file should have string keys (MIDI note numbers) mapping to
    action dicts. Keys are converted to integers on load.

    Returns DEFAULT_MIDI_MAP if the file does not exist.
    Raises on invalid JSON or malformed content.
    """
    if not os.path.exists(path):
        print(f"[config] No config file found at {path}, using defaults")
        return dict(DEFAULT_MIDI_MAP)

    with open(path, "r") as f:
        raw = json.load(f)

    midi_map = {int(k): v for k, v in raw.items()}

    print(f"[config] Loaded {len(midi_map)} mappings from {path}")
    return midi_map


MIDI_MAP = load_config()

# ---------------------------------------------------------------------------
# Globals
# ---------------------------------------------------------------------------

stop_event = threading.Event()   # set() to signal the loop to stop
loop_thread = None  # type: threading.Thread | None


def natural_sort_key(s: str):
    """Sort key that handles embedded numbers naturally (e.g. 2 before 10)."""
    return [int(c) if c.isdigit() else c.lower() for c in re.split(r"(\d+)", s)]


def get_scenes_by_prefix(client: obs.ReqClient, prefix: str) -> list[str]:
    """Return scene names that start with *prefix*, natural-sorted."""
    resp = client.get_scene_list()
    return sorted(
        (s["sceneName"] for s in resp.scenes if s["sceneName"].startswith(prefix)),
        key=natural_sort_key,
    )


def build_sequence(scenes: list[str], style: str) -> list[str]:
    """Build the playback sequence from a list of scenes and a loop style."""
    if style == "bounce" and len(scenes) > 2:
        return scenes + scenes[-2:0:-1]
    if style == "reverse":
        return list(reversed(scenes))
    if style == "strobe" and len(scenes) >= 2:
        return [scenes[0], scenes[-1]]
    if style == "shuffle":
        shuffled = list(scenes)
        random.shuffle(shuffled)
        return shuffled
    # "cycle", "random", "random_no_repeat", "once" use scenes as-is
    # (their special behaviour is handled in scene_loop)
    return list(scenes)


def scene_loop(client: obs.ReqClient, sequence: list[str], tick: float, style: str):
    """Cycle through *sequence* until stop_event is set."""
    idx = 0
    last_scene = None
    print(f"[loop] Starting {style} loop – {len(sequence)} steps, tick={tick}s")
    while not stop_event.is_set():
        # Pick the next scene based on style
        if style == "random":
            scene = random.choice(sequence)
        elif style == "random_no_repeat":
            choices = [s for s in sequence if s != last_scene] or sequence
            scene = random.choice(choices)
        elif style == "once":
            if idx >= len(sequence):
                print(f"[loop] Finished (once) – holding on {last_scene}")
                break
            scene = sequence[idx]
        else:
            # cycle, bounce, reverse, strobe, shuffle all just wrap around
            scene = sequence[idx % len(sequence)]

        print(f"[loop] -> {scene}")
        client.set_current_program_scene(scene)
        last_scene = scene
        idx += 1
        # Use wait() instead of sleep() so we can interrupt immediately
        stop_event.wait(tick)
    print("[loop] Stopped.")


def start_loop(client: obs.ReqClient, prefix: str, style: str, tick: float):
    """Stop any existing loop, fetch matching scenes, start a new one."""
    global loop_thread

    # Stop existing loop and wait for it to finish
    stop_loop()

    scenes = get_scenes_by_prefix(client, prefix)
    if not scenes:
        print(f"[warn] No scenes found with prefix '{prefix}'")
        return
    sequence = build_sequence(scenes, style)
    print(f"[info] Found scenes: {scenes} (style={style}, tick={tick}s)")

    stop_event.clear()
    loop_thread = threading.Thread(
        target=scene_loop, args=(client, sequence, tick, style), daemon=True
    )
    loop_thread.start()


def stop_loop():
    """Signal the loop thread to stop and wait for it to exit."""
    global loop_thread
    stop_event.set()
    if loop_thread is not None:
        loop_thread.join()
        loop_thread = None


def kill_switch(client: obs.ReqClient, scene_name: str):
    """Stop any running loop and switch to a specific static scene."""
    stop_loop()
    print(f"[kill] Switching to static scene: {scene_name}")
    try:
        client.set_current_program_scene(scene_name)
    except Exception as e:
        print(f"[kill] Failed to switch to '{scene_name}': {e}")


def handle_midi(msg, client: obs.ReqClient):
    """React to incoming MIDI messages using MIDI_MAP."""
    if msg.type != "note_on" or msg.velocity == 0:
        return

    entry = MIDI_MAP.get(msg.note)
    if entry is None:
        print(f"[midi] note {msg.note} – unmapped, ignoring")
        return

    kind = entry["action"]

    if kind == "loop":
        prefix = entry["prefix"]
        style = entry.get("style", "cycle")
        tick = entry.get("tick", 2.0)
        print(f"[midi] note {msg.note} – {style} loop (prefix={prefix}, tick={tick}s)")
        start_loop(client, prefix, style, tick)
    elif kind == "kill":
        scene = entry["scene"]
        print(f"[midi] note {msg.note} – kill switch (scene={scene})")
        kill_switch(client, scene)


def midi_debug_loop(port_name: str):
    """Open a MIDI port and log every incoming message."""
    NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    with mido.open_input(port_name) as inport:
        print(f"[debug] Listening on: {port_name}")
        print("[debug] Press keys on your MIDI device … (Ctrl+C to quit)")
        for msg in inport:
            if hasattr(msg, "note"):
                name = NOTE_NAMES[msg.note % 12] + str(msg.note // 12 - 1)
                print(f"[debug] {msg}  (note_name={name})")
            else:
                print(f"[debug] {msg}")


def main():
    # --- MIDI debug mode ---
    if MIDI_DEBUG:
        available = mido.get_input_names()
        print(f"[debug] Available MIDI inputs: {available}")
        port_name = MIDI_PORT_NAME or (available[0] if available else None)
        if port_name is None:
            print("[error] No MIDI input ports found. Exiting.")
            return
        try:
            midi_debug_loop(port_name)
        except KeyboardInterrupt:
            print("\n[debug] Done.")
        return

    # --- Connect to OBS ---
    print(f"[obs]  Connecting to {OBS_HOST}:{OBS_PORT} …")
    client = obs.ReqClient(host=OBS_HOST, port=OBS_PORT, password=OBS_PASSWORD, timeout=5)
    resp = client.get_version()
    print(f"[obs]  Connected – OBS {resp.obs_version}, WebSocket {resp.obs_web_socket_version}")

    if TEST_MODE:
        # Skip MIDI – run the first "loop" action from MIDI_MAP
        first = next((e for e in MIDI_MAP.values() if e["action"] == "loop"), None)
        if first:
            print(f"[test] TEST_MODE – starting loop (prefix={first['prefix']})")
            start_loop(client, first["prefix"], first.get("style", "cycle"), first.get("tick", 2.0))
        try:
            while True:
                time.sleep(0.5)
        except KeyboardInterrupt:
            print("\n[info] Shutting down.")
            stop_loop()
        return

    # --- Open MIDI port ---
    available = mido.get_input_names()
    print(f"[midi] Available inputs: {available}")

    port_name = MIDI_PORT_NAME or (available[0] if available else None)
    if port_name is None:
        print("[error] No MIDI input ports found. Exiting.")
        return

    print(f"[midi] Opening port: {port_name}")
    print(f"[midi] Mapped notes: {list(MIDI_MAP.keys())}")
    with mido.open_input(port_name) as inport:
        print("[midi] Listening for MIDI events … (press Ctrl+C to quit)")
        try:
            for msg in inport:
                handle_midi(msg, client)
        except KeyboardInterrupt:
            print("\n[info] Shutting down.")
            stop_loop()


if __name__ == "__main__":
    main()
