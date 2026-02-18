"""Unit tests for loop styles, static-scene logic, and config loading."""

import json
import os
import pytest
import random
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import main


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SCENES = ["S_1", "S_2", "S_3", "S_4"]


def run_scene_loop(sequence: list[str], style: str, ticks: int,
                   max_repeats=None) -> list[str]:
    """Run scene_loop for a given number of ticks and return the scene names
    that were set on the mock OBS client.

    We patch stop_event.wait to count iterations and signal stop
    after *ticks* iterations so the loop exits cleanly.
    """
    client = MagicMock()
    call_count = 0

    def fake_wait(_duration):
        nonlocal call_count
        call_count += 1
        if call_count >= ticks:
            main.stop_event.set()

    main.stop_event.clear()
    with patch.object(main.stop_event, "wait", side_effect=fake_wait):
        main.scene_loop(client, sequence, tick=0.1, style=style,
                        max_repeats=max_repeats)

    return [c.args[0] for c in client.set_current_program_scene.call_args_list]


# ---------------------------------------------------------------------------
# build_sequence tests
# ---------------------------------------------------------------------------

class TestBuildSequence:

    def test_cycle_returns_scenes_unchanged(self):
        result = main.build_sequence(SCENES, "cycle")
        assert result == ["S_1", "S_2", "S_3", "S_4"]

    def test_bounce_creates_ping_pong(self):
        result = main.build_sequence(SCENES, "bounce")
        assert result == ["S_1", "S_2", "S_3", "S_4", "S_3", "S_2"]

    def test_bounce_with_two_scenes_returns_unchanged(self):
        # bounce needs >2 scenes to ping-pong, otherwise falls through
        result = main.build_sequence(["S_1", "S_2"], "bounce")
        assert result == ["S_1", "S_2"]

    def test_reverse_reverses_order(self):
        result = main.build_sequence(SCENES, "reverse")
        assert result == ["S_4", "S_3", "S_2", "S_1"]

    def test_strobe_uses_first_and_last(self):
        result = main.build_sequence(SCENES, "strobe")
        assert result == ["S_1", "S_4"]

    def test_strobe_with_single_scene_returns_unchanged(self):
        result = main.build_sequence(["S_1"], "strobe")
        assert result == ["S_1"]

    def test_shuffle_contains_same_scenes(self):
        random.seed(42)
        result = main.build_sequence(SCENES, "shuffle")
        assert sorted(result) == sorted(SCENES)

    def test_once_returns_scenes_unchanged(self):
        # "once" behaviour is in scene_loop, build_sequence just passes through
        result = main.build_sequence(SCENES, "once")
        assert result == ["S_1", "S_2", "S_3", "S_4"]

    def test_random_returns_scenes_unchanged(self):
        result = main.build_sequence(SCENES, "random")
        assert result == ["S_1", "S_2", "S_3", "S_4"]

    def test_random_no_repeat_returns_scenes_unchanged(self):
        result = main.build_sequence(SCENES, "random_no_repeat")
        assert result == ["S_1", "S_2", "S_3", "S_4"]


# ---------------------------------------------------------------------------
# scene_loop tests
# ---------------------------------------------------------------------------

class TestSceneLoopCycle:

    def test_cycles_through_scenes_in_order(self):
        seq = main.build_sequence(SCENES, "cycle")
        played = run_scene_loop(seq, "cycle", ticks=8)
        assert played == ["S_1", "S_2", "S_3", "S_4", "S_1", "S_2", "S_3", "S_4"]

    def test_wraps_around(self):
        seq = main.build_sequence(SCENES, "cycle")
        played = run_scene_loop(seq, "cycle", ticks=6)
        assert played == ["S_1", "S_2", "S_3", "S_4", "S_1", "S_2"]


class TestSceneLoopBounce:

    def test_bounce_ping_pongs(self):
        seq = main.build_sequence(SCENES, "bounce")
        # sequence is [S_1, S_2, S_3, S_4, S_3, S_2] repeating
        played = run_scene_loop(seq, "bounce", ticks=8)
        assert played == ["S_1", "S_2", "S_3", "S_4", "S_3", "S_2", "S_1", "S_2"]


class TestSceneLoopReverse:

    def test_reverse_plays_backwards(self):
        seq = main.build_sequence(SCENES, "reverse")
        played = run_scene_loop(seq, "reverse", ticks=6)
        assert played == ["S_4", "S_3", "S_2", "S_1", "S_4", "S_3"]


class TestSceneLoopStrobe:

    def test_strobe_alternates_first_and_last(self):
        seq = main.build_sequence(SCENES, "strobe")
        played = run_scene_loop(seq, "strobe", ticks=6)
        assert played == ["S_1", "S_4", "S_1", "S_4", "S_1", "S_4"]


class TestSceneLoopShuffle:

    def test_shuffle_cycles_shuffled_order(self):
        random.seed(42)
        seq = main.build_sequence(SCENES, "shuffle")
        played = run_scene_loop(seq, "shuffle", ticks=8)
        # Should repeat the same shuffled order
        assert played[:4] == seq
        assert played[4:8] == seq


class TestSceneLoopOnce:

    def test_once_plays_through_then_stops(self):
        seq = main.build_sequence(SCENES, "once")
        # Give more ticks than scenes — should stop after 4
        played = run_scene_loop(seq, "once", ticks=10)
        assert played == ["S_1", "S_2", "S_3", "S_4"]


class TestSceneLoopRandom:

    def test_random_plays_from_sequence(self):
        random.seed(42)
        seq = main.build_sequence(SCENES, "random")
        played = run_scene_loop(seq, "random", ticks=6)
        assert len(played) == 6
        assert all(s in SCENES for s in played)


class TestSceneLoopRandomNoRepeat:

    def test_no_consecutive_duplicates(self):
        random.seed(42)
        seq = main.build_sequence(SCENES, "random_no_repeat")
        played = run_scene_loop(seq, "random_no_repeat", ticks=20)
        for i in range(1, len(played)):
            assert played[i] != played[i - 1], (
                f"Consecutive repeat at index {i}: {played[i]}"
            )

    def test_all_scenes_from_sequence(self):
        random.seed(42)
        seq = main.build_sequence(SCENES, "random_no_repeat")
        played = run_scene_loop(seq, "random_no_repeat", ticks=10)
        assert all(s in SCENES for s in played)


# ---------------------------------------------------------------------------
# switch_to_static_scene tests
# ---------------------------------------------------------------------------

class TestSwitchToStaticScene:

    def test_switch_to_static_scene_sets_scene(self):
        client = MagicMock()
        main.stop_event.clear()
        main.switch_to_static_scene(client, "STATIC_1")
        client.set_current_program_scene.assert_called_once_with("STATIC_1")
        assert main.stop_event.is_set()

    def test_switch_to_static_scene_handles_missing_scene(self):
        client = MagicMock()
        client.set_current_program_scene.side_effect = Exception("Scene not found")
        # Should not raise
        main.switch_to_static_scene(client, "DOES_NOT_EXIST")
        client.set_current_program_scene.assert_called_once_with("DOES_NOT_EXIST")


# ---------------------------------------------------------------------------
# natural_sort_key tests
# ---------------------------------------------------------------------------

class TestNaturalSort:

    def test_numeric_ordering(self):
        names = ["LOOP_A_10", "LOOP_A_2", "LOOP_A_1", "LOOP_A_20"]
        result = sorted(names, key=main.natural_sort_key)
        assert result == ["LOOP_A_1", "LOOP_A_2", "LOOP_A_10", "LOOP_A_20"]


# ---------------------------------------------------------------------------
# load_config tests
# ---------------------------------------------------------------------------

class TestLoadConfig:

    def test_falls_back_to_default_when_no_file(self):
        result = main.load_config("/nonexistent/path/config.json")
        assert result == main.DEFAULT_MIDI_MAP

    def test_loads_config_from_json_file(self):
        config_data = {
            "60": {"action": "loop", "prefix": "TEST_A_", "style": "cycle", "tick": 1.0},
            "61": {"action": "static", "scene": "MY_STATIC"},
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            tmp_path = f.name
        try:
            result = main.load_config(tmp_path)
            assert result == {
                60: {"action": "loop", "prefix": "TEST_A_", "style": "cycle", "tick": 1.0},
                61: {"action": "static", "scene": "MY_STATIC"},
            }
        finally:
            os.unlink(tmp_path)

    def test_keys_are_converted_to_integers(self):
        config_data = {
            "48": {"action": "loop", "prefix": "X_", "style": "cycle", "tick": 2.0},
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            tmp_path = f.name
        try:
            result = main.load_config(tmp_path)
            assert all(isinstance(k, int) for k in result.keys())
            assert 48 in result
        finally:
            os.unlink(tmp_path)

    def test_raises_on_invalid_json(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("not valid json {{{")
            tmp_path = f.name
        try:
            raised = False
            try:
                main.load_config(tmp_path)
            except json.JSONDecodeError:
                raised = True
            assert raised, "Expected JSONDecodeError for invalid JSON"
        finally:
            os.unlink(tmp_path)

    def test_empty_config_returns_empty_map(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({}, f)
            tmp_path = f.name
        try:
            result = main.load_config(tmp_path)
            assert result == {}
        finally:
            os.unlink(tmp_path)

    def test_default_is_not_mutated(self):
        """Ensure load_config returns a copy, not the original DEFAULT_MIDI_MAP."""
        result = main.load_config("/nonexistent/path/config.json")
        result[999] = {"action": "static", "scene": "HACK"}
        assert 999 not in main.DEFAULT_MIDI_MAP


# ---------------------------------------------------------------------------
# max_repeats tests
# ---------------------------------------------------------------------------

class TestSceneLoopMaxRepeats:

    def test_cycle_stops_after_max_repeats(self):
        seq = main.build_sequence(SCENES, "cycle")
        # 4 scenes, 2 repeats = 8 scenes played, give plenty of ticks
        played = run_scene_loop(seq, "cycle", ticks=100, max_repeats=2)
        assert played == ["S_1", "S_2", "S_3", "S_4", "S_1", "S_2", "S_3", "S_4"]

    def test_bounce_stops_after_max_repeats(self):
        seq = main.build_sequence(SCENES, "bounce")
        # bounce sequence is [S_1, S_2, S_3, S_4, S_3, S_2], 1 repeat = 6 scenes
        played = run_scene_loop(seq, "bounce", ticks=100, max_repeats=1)
        assert played == ["S_1", "S_2", "S_3", "S_4", "S_3", "S_2"]

    def test_single_repeat(self):
        seq = main.build_sequence(SCENES, "cycle")
        played = run_scene_loop(seq, "cycle", ticks=100, max_repeats=1)
        assert played == ["S_1", "S_2", "S_3", "S_4"]

    def test_none_repeats_loops_until_stopped(self):
        seq = main.build_sequence(SCENES, "cycle")
        # max_repeats=None, should run until ticks limit
        played = run_scene_loop(seq, "cycle", ticks=6, max_repeats=None)
        assert played == ["S_1", "S_2", "S_3", "S_4", "S_1", "S_2"]

    def test_random_stops_after_max_repeats(self):
        random.seed(42)
        seq = main.build_sequence(SCENES, "random")
        # 4 scenes, 2 repeats = 8 random picks
        played = run_scene_loop(seq, "random", ticks=100, max_repeats=2)
        assert len(played) == 8
        assert all(s in SCENES for s in played)

    def test_once_ignores_max_repeats(self):
        seq = main.build_sequence(SCENES, "once")
        # "once" stops naturally, max_repeats shouldn't matter
        played = run_scene_loop(seq, "once", ticks=100, max_repeats=5)
        assert played == ["S_1", "S_2", "S_3", "S_4"]


# ---------------------------------------------------------------------------
# run_sequence tests
# ---------------------------------------------------------------------------

def make_mock_client(scene_names: list[str]):
    """Create a mock OBS client that returns the given scene names."""
    client = MagicMock()
    resp = MagicMock()
    resp.scenes = [{"sceneName": s} for s in scene_names]
    client.get_scene_list.return_value = resp
    return client


class TestRunSequence:

    def test_sequence_runs_steps_in_order(self):
        client = make_mock_client(["P_1", "P_2", "P_3"])
        steps = [
            {"action": "loop", "prefix": "P_", "style": "cycle", "bpm": 6000, "steps": 1, "repeats": 1},
            {"action": "loop", "prefix": "P_", "style": "reverse", "bpm": 6000, "steps": 1, "repeats": 1},
            {"action": "stop"},
        ]

        main.stop_event.clear()
        with patch.object(main.stop_event, "wait"):
            main.run_sequence(client, steps)

        calls = [c.args[0] for c in client.set_current_program_scene.call_args_list]
        # Step 1: cycle 1 repeat = P_1, P_2, P_3
        # Step 2: reverse 1 repeat = P_3, P_2, P_1
        # Step 3: stop
        assert calls == ["P_1", "P_2", "P_3", "P_3", "P_2", "P_1"]

    def test_sequence_with_static_step(self):
        """Static as the last step — no infinite loop, runs to completion."""
        client = make_mock_client(["P_1", "P_2"])
        steps = [
            {"action": "loop", "prefix": "P_", "style": "cycle", "bpm": 6000, "steps": 1, "repeats": 1},
            {"action": "static", "scene": "STATIC_1"},
        ]

        main.stop_event.clear()
        with patch.object(main.stop_event, "wait"):
            main.run_sequence(client, steps)

        calls = [c.args[0] for c in client.set_current_program_scene.call_args_list]
        # Step 1: cycle P_1, P_2 (1 repeat)
        # Step 2: static → STATIC_1
        assert calls == ["P_1", "P_2", "STATIC_1"]

    def test_sequence_cancelled_by_stop_event(self):
        client = make_mock_client(["P_1", "P_2"])
        steps = [
            {"action": "loop", "prefix": "P_", "style": "cycle", "bpm": 6000, "steps": 1, "repeats": 1},
            {"action": "loop", "prefix": "P_", "style": "cycle", "bpm": 6000, "steps": 1, "repeats": 1},
        ]

        # Set stop_event before running — should abort immediately
        main.stop_event.set()
        main.run_sequence(client, steps)

        client.set_current_program_scene.assert_not_called()

    def test_sequence_cancel_mid_loop(self):
        client = make_mock_client(["P_1", "P_2", "P_3"])
        steps = [
            {"action": "loop", "prefix": "P_", "style": "cycle", "bpm": 6000, "steps": 1, "repeats": 2},
            {"action": "static", "scene": "SHOULD_NOT_REACH"},
        ]
        call_count = 0

        def fake_wait(_duration):
            nonlocal call_count
            call_count += 1
            # Cancel after 2 scenes (mid first repeat)
            if call_count >= 2:
                main.stop_event.set()

        main.stop_event.clear()
        with patch.object(main.stop_event, "wait", side_effect=fake_wait):
            main.run_sequence(client, steps)

        calls = [c.args[0] for c in client.set_current_program_scene.call_args_list]
        # Should have played 2 scenes then stopped, never reaching the static step
        assert len(calls) == 2
        assert "SHOULD_NOT_REACH" not in calls

    def test_sequence_loops_continuously(self):
        """Without a terminal action, sequence wraps back to step 1."""
        client = make_mock_client(["P_1", "P_2"])
        steps = [
            {"action": "loop", "prefix": "P_", "style": "cycle", "bpm": 6000, "steps": 1, "repeats": 1},
        ]
        call_count = 0

        def fake_wait(_duration):
            nonlocal call_count
            call_count += 1
            # Let it loop through 2 full passes (2 scenes each) then stop
            if call_count >= 4:
                main.stop_event.set()

        main.stop_event.clear()
        with patch.object(main.stop_event, "wait", side_effect=fake_wait):
            main.run_sequence(client, steps)

        calls = [c.args[0] for c in client.set_current_program_scene.call_args_list]
        # Pass 1: P_1, P_2 — Pass 2: P_1, P_2
        assert calls == ["P_1", "P_2", "P_1", "P_2"]

    def test_stop_action_terminates_sequence(self):
        """Stop action ends the sequence without switching scenes."""
        client = make_mock_client(["P_1", "P_2"])
        steps = [
            {"action": "loop", "prefix": "P_", "style": "cycle", "bpm": 6000, "steps": 1, "repeats": 1},
            {"action": "stop"},
        ]

        main.stop_event.clear()
        with patch.object(main.stop_event, "wait"):
            main.run_sequence(client, steps)

        calls = [c.args[0] for c in client.set_current_program_scene.call_args_list]
        # Loop plays P_1, P_2 then stop — no extra scene switch
        assert calls == ["P_1", "P_2"]

    def test_sequence_multiple_repeats_then_next_step(self):
        """Non-last loop steps respect their repeats count before advancing."""
        client = make_mock_client(["P_1", "P_2"])
        steps = [
            {"action": "loop", "prefix": "P_", "style": "cycle", "bpm": 6000, "steps": 1, "repeats": 2},
            {"action": "static", "scene": "DONE"},
        ]

        main.stop_event.clear()
        with patch.object(main.stop_event, "wait"):
            main.run_sequence(client, steps)

        calls = [c.args[0] for c in client.set_current_program_scene.call_args_list]
        # 2 repeats of [P_1, P_2] = 4 scenes, then static
        assert calls == ["P_1", "P_2", "P_1", "P_2", "DONE"]

    def test_pause_resumes_and_continues(self):
        """Pause waits for resume_event, then continues to the next step."""
        client = make_mock_client(["P_1", "P_2"])
        steps = [
            {"action": "loop", "prefix": "P_", "style": "cycle", "bpm": 6000, "steps": 1, "repeats": 1},
            {"action": "pause"},
            {"action": "static", "scene": "DONE"},
        ]

        def fake_resume_wait(timeout):
            """Simulate the resume arriving immediately."""
            main.resume_event.set()

        main.stop_event.clear()
        main.resume_event.clear()
        main.pause_resume_note = None

        with patch.object(main.stop_event, "wait"), \
             patch.object(main.resume_event, "wait", side_effect=fake_resume_wait):
            main.run_sequence(client, steps, trigger_note=36)

        calls = [c.args[0] for c in client.set_current_program_scene.call_args_list]
        # Loop: P_1, P_2 → pause (resumed) → static: DONE
        assert calls == ["P_1", "P_2", "DONE"]

    def test_pause_cancelled_by_stop_event(self):
        """Stop event during pause cancels the sequence."""
        client = make_mock_client(["P_1", "P_2"])
        steps = [
            {"action": "loop", "prefix": "P_", "style": "cycle", "bpm": 6000, "steps": 1, "repeats": 1},
            {"action": "pause"},
            {"action": "static", "scene": "SHOULD_NOT_REACH"},
        ]

        def fake_resume_wait(timeout):
            """Simulate cancellation arriving during pause."""
            main.stop_event.set()

        main.stop_event.clear()
        main.resume_event.clear()
        main.pause_resume_note = None

        with patch.object(main.stop_event, "wait"), \
             patch.object(main.resume_event, "wait", side_effect=fake_resume_wait):
            main.run_sequence(client, steps, trigger_note=36)

        calls = [c.args[0] for c in client.set_current_program_scene.call_args_list]
        # Loop: P_1, P_2 → pause (cancelled) — static never reached
        assert calls == ["P_1", "P_2"]
        assert "SHOULD_NOT_REACH" not in calls

    def test_pause_uses_trigger_note_by_default(self):
        """Pause sets pause_resume_note to the trigger note."""
        client = make_mock_client(["P_1"])
        steps = [
            {"action": "pause"},
            {"action": "stop"},
        ]

        resume_notes_seen = []

        def fake_resume_wait(timeout):
            resume_notes_seen.append(main.pause_resume_note)
            main.resume_event.set()

        main.stop_event.clear()
        main.resume_event.clear()
        main.pause_resume_note = None

        with patch.object(main.resume_event, "wait", side_effect=fake_resume_wait):
            main.run_sequence(client, steps, trigger_note=42)

        assert resume_notes_seen[0] == 42
        # pause_resume_note should be cleared after pause exits
        assert main.pause_resume_note is None

    def test_pause_uses_custom_resume_note(self):
        """Pause respects a custom resume_note override."""
        client = make_mock_client(["P_1"])
        steps = [
            {"action": "pause", "resume_note": 99},
            {"action": "stop"},
        ]

        resume_notes_seen = []

        def fake_resume_wait(timeout):
            resume_notes_seen.append(main.pause_resume_note)
            main.resume_event.set()

        main.stop_event.clear()
        main.resume_event.clear()
        main.pause_resume_note = None

        with patch.object(main.resume_event, "wait", side_effect=fake_resume_wait):
            main.run_sequence(client, steps, trigger_note=36)

        assert resume_notes_seen[0] == 99


# ---------------------------------------------------------------------------
# calc_tick tests
# ---------------------------------------------------------------------------

class TestCalcTick:

    def test_120_bpm_4_steps(self):
        # (60/120) * 4 = 2.0s
        assert main.calc_tick(120, 4) == 2.0

    def test_120_bpm_1_step(self):
        # (60/120) * 1 = 0.5s
        assert main.calc_tick(120, 1) == 0.5

    def test_60_bpm_1_step(self):
        # (60/60) * 1 = 1.0s
        assert main.calc_tick(60, 1) == 1.0

    def test_140_bpm_2_steps(self):
        # (60/140) * 2 ≈ 0.857s
        result = main.calc_tick(140, 2)
        assert abs(result - (60.0 / 140 * 2)) < 0.001

    def test_high_bpm_fast_tick(self):
        # 240 BPM, 1 step = 0.25s
        assert main.calc_tick(240, 1) == 0.25


# ---------------------------------------------------------------------------
# find_config_files tests
# ---------------------------------------------------------------------------

class TestFindConfigFiles:

    def test_empty_directory(self, tmp_path):
        result = main.find_config_files(str(tmp_path))
        assert result == []

    def test_finds_json_files(self, tmp_path):
        (tmp_path / "config.json").touch()
        (tmp_path / "show.json").touch()
        result = main.find_config_files(str(tmp_path))
        assert len(result) == 2

    def test_excludes_example_config(self, tmp_path):
        (tmp_path / "config.example.json").touch()
        (tmp_path / "config.json").touch()
        result = main.find_config_files(str(tmp_path))
        assert len(result) == 1
        assert all("config.example.json" not in r for r in result)

    def test_excludes_non_json_files(self, tmp_path):
        (tmp_path / "config.json").touch()
        (tmp_path / "readme.txt").touch()
        result = main.find_config_files(str(tmp_path))
        assert len(result) == 1

    def test_returns_sorted_paths(self, tmp_path):
        (tmp_path / "z.json").touch()
        (tmp_path / "a.json").touch()
        (tmp_path / "m.json").touch()
        result = main.find_config_files(str(tmp_path))
        assert result == sorted(result)

    def test_returns_absolute_paths(self, tmp_path):
        (tmp_path / "config.json").touch()
        result = main.find_config_files(str(tmp_path))
        assert all(os.path.isabs(p) for p in result)


# ---------------------------------------------------------------------------
# pick_config_file tests
# ---------------------------------------------------------------------------

class TestPickConfigFile:

    def test_no_files_returns_none(self):
        assert main.pick_config_file([]) is None

    def test_single_file_returns_it(self, tmp_path):
        f = str(tmp_path / "config.json")
        assert main.pick_config_file([f]) == f

    def test_multiple_files_prompts_and_returns_chosen(self, tmp_path, monkeypatch):
        files = [str(tmp_path / "a.json"), str(tmp_path / "b.json")]
        mock_result = MagicMock()
        mock_result.ask.return_value = "a.json"
        monkeypatch.setattr("questionary.select", lambda *a, **kw: mock_result)
        result = main.pick_config_file(files)
        assert result == files[0]

    def test_multiple_files_none_selection_exits(self, tmp_path, monkeypatch):
        files = [str(tmp_path / "a.json"), str(tmp_path / "b.json")]
        mock_result = MagicMock()
        mock_result.ask.return_value = None
        monkeypatch.setattr("questionary.select", lambda *a, **kw: mock_result)
        with pytest.raises(SystemExit):
            main.pick_config_file(files)
