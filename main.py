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

# Seconds between each scene switch (lower = faster looping)
TICK_RATE = 2.0

# Set to a specific port name, or None to pick the first available input
MIDI_PORT_NAME = None

# Set to True to skip MIDI and immediately start the first loop action
TEST_MODE = False

# Set to True to log all incoming MIDI messages and skip OBS connection
MIDI_DEBUG = False

# ---------------------------------------------------------------------------
# MIDI Note → Action mapping
# ---------------------------------------------------------------------------
# Each entry maps a MIDI note number to an action:
#   ("loop", "PREFIX_")   – stop any current loop, start cycling PREFIX_ scenes
#   ("kill", "SceneName") – stop any current loop, switch to a static scene
#
# Note numbers: C3=48, C#3=49, D3=50, D#3=51, E3=52, F3=53 ...
#               (using MIDI note convention where C3 = 48)

MIDI_MAP = {
    36: ("loop", "LOOP_A_"),   # C2
    37: ("loop", "LOOP_B_"),   # C#2
    38: ("loop", "LOOP_C_"),   # D2
    39: ("loop", "LOOP_D_"),   # D#2
    40: ("loop", "LOOP_E_"),   # E2
    41: ("loop", "LOOP_F_"),   # F2
    42: ("loop", "LOOP_G_"),   # F#2
    43: ("kill", "STATIC_1"),  # G2  → kill switch
    44: ("loop", "LOOP_H_"),   # G#2
    45: ("loop", "LOOP_I_"),   # A2
    46: ("loop", "LOOP_J_"),   # A#2
    47: ("loop", "LOOP_K_"),   # B2
    48: ("loop", "LOOP_L_"),   # C3
    49: ("loop", "LOOP_M_"),   # C#3
    50: ("loop", "LOOP_N_"),   # D3
    51: ("kill", "STATIC_2"),  # D#3 → kill switch
}

# ---------------------------------------------------------------------------
# Globals
# ---------------------------------------------------------------------------

looping = False
loop_lock = threading.Lock()


def get_scenes_by_prefix(client: obs.ReqClient, prefix: str) -> list[str]:
    """Return scene names that start with *prefix*, sorted alphabetically."""
    resp = client.get_scene_list()
    return sorted(
        s["sceneName"] for s in resp.scenes if s["sceneName"].startswith(prefix)
    )


def scene_loop(client: obs.ReqClient, scenes: list[str], tick: float):
    """Cycle through *scenes* on a timer until `looping` is set to False."""
    global looping
    idx = 0
    print(f"[loop] Starting scene loop – {len(scenes)} scenes, tick={tick}s")
    while True:
        with loop_lock:
            if not looping:
                break
        scene = scenes[idx % len(scenes)]
        print(f"[loop] -> {scene}")
        client.set_current_program_scene(scene)
        idx += 1
        time.sleep(tick)
    print("[loop] Stopped.")


def start_loop(client: obs.ReqClient, prefix: str, tick: float):
    """Stop any existing loop, fetch matching scenes, start a new loop."""
    global looping

    # Stop existing loop first
    stop_loop()
    time.sleep(tick + 0.1)  # give the old thread time to exit

    scenes = get_scenes_by_prefix(client, prefix)
    if not scenes:
        print(f"[warn] No scenes found with prefix '{prefix}'")
        return
    print(f"[info] Found scenes: {scenes}")
    with loop_lock:
        looping = True
    t = threading.Thread(target=scene_loop, args=(client, scenes, tick), daemon=True)
    t.start()


def stop_loop():
    """Signal the loop thread to stop."""
    global looping
    with loop_lock:
        looping = False


def kill_switch(client: obs.ReqClient, scene_name: str):
    """Stop any running loop and switch to a specific static scene."""
    stop_loop()
    print(f"[kill] Switching to static scene: {scene_name}")
    client.set_current_program_scene(scene_name)


def handle_midi(msg, client: obs.ReqClient):
    """React to incoming MIDI messages using MIDI_MAP."""
    if msg.type != "note_on" or msg.velocity == 0:
        return

    action = MIDI_MAP.get(msg.note)
    if action is None:
        print(f"[midi] note {msg.note} – unmapped, ignoring")
        return

    kind, target = action

    if kind == "loop":
        print(f"[midi] note {msg.note} – starting loop (prefix={target})")
        start_loop(client, target, TICK_RATE)
    elif kind == "kill":
        print(f"[midi] note {msg.note} – kill switch (scene={target})")
        kill_switch(client, target)


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
        first_loop = next((t for k, t in MIDI_MAP.values() if k == "loop"), None)
        if first_loop:
            print(f"[test] TEST_MODE – starting loop (prefix={first_loop})")
            start_loop(client, first_loop, TICK_RATE)
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
