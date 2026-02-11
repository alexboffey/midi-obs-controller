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

# Scene prefix to filter on (only scenes starting with this are cycled)
SCENE_PREFIX = "SONG_A_"

# Seconds between each scene switch (lower = faster looping)
TICK_RATE = 2.0

# Set to a specific port name, or None to pick the first available input
MIDI_PORT_NAME = None

# Set to True to skip MIDI and immediately start the scene loop
TEST_MODE = True

# ---------------------------------------------------------------------------
# Globals
# ---------------------------------------------------------------------------

looping = False
loop_lock = threading.Lock()


def get_scenes_by_prefix(client: obs.ReqClient, prefix: str) -> list[str]:
    """Return scene names that start with *prefix*, sorted alphabetically."""
    resp = client.get_scene_list()
    return sorted(s["sceneName"] for s in resp.scenes if s["sceneName"].startswith(prefix))


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
    """Fetch matching scenes and kick off the loop in a background thread."""
    global looping
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


def handle_midi(msg, client: obs.ReqClient):
    """React to incoming MIDI messages."""
    global looping

    # Ignore non-note messages
    if msg.type not in ("note_on", "note_off"):
        return

    # note_on with velocity > 0  -> toggle the scene loop
    if msg.type == "note_on" and msg.velocity > 0:
        with loop_lock:
            currently_looping = looping

        if currently_looping:
            print(f"[midi] note {msg.note} – stopping loop")
            stop_loop()
        else:
            print(f"[midi] note {msg.note} – starting loop (prefix={SCENE_PREFIX})")
            start_loop(client, SCENE_PREFIX, TICK_RATE)


def main():
    # --- Connect to OBS ---
    print(f"[obs]  Connecting to {OBS_HOST}:{OBS_PORT} …")
    client = obs.ReqClient(host=OBS_HOST, port=OBS_PORT, password=OBS_PASSWORD, timeout=5)
    resp = client.get_version()
    print(f"[obs]  Connected – OBS {resp.obs_version}, WebSocket {resp.obs_web_socket_version}")

    if TEST_MODE:
        # Skip MIDI – just start the loop and wait
        print("[test] TEST_MODE enabled – starting loop immediately")
        start_loop(client, SCENE_PREFIX, TICK_RATE)
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
