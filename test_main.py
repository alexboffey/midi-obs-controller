"""Unit tests for loop styles and kill switch logic."""

import random
from unittest.mock import MagicMock, patch, call

import main


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SCENES = ["S_1", "S_2", "S_3", "S_4"]


def run_scene_loop(sequence: list[str], style: str, ticks: int) -> list[str]:
    """Run scene_loop for a given number of ticks and return the scene names
    that were set on the mock OBS client.

    We patch time.sleep to count iterations and flip `looping` to False
    after *ticks* iterations so the loop exits cleanly.
    """
    client = MagicMock()
    call_count = 0

    def fake_sleep(_duration):
        nonlocal call_count
        call_count += 1
        if call_count >= ticks:
            main.looping = False

    with patch.object(main.time, "sleep", side_effect=fake_sleep):
        main.looping = True
        main.scene_loop(client, sequence, tick=0.1, style=style)

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
# kill_switch tests
# ---------------------------------------------------------------------------

class TestKillSwitch:

    def test_kill_switch_sets_scene(self):
        client = MagicMock()
        main.looping = True
        main.kill_switch(client, "STATIC_1")
        client.set_current_program_scene.assert_called_once_with("STATIC_1")
        assert main.looping is False

    def test_kill_switch_handles_missing_scene(self):
        client = MagicMock()
        client.set_current_program_scene.side_effect = Exception("Scene not found")
        # Should not raise
        main.kill_switch(client, "DOES_NOT_EXIST")
        client.set_current_program_scene.assert_called_once_with("DOES_NOT_EXIST")


# ---------------------------------------------------------------------------
# natural_sort_key tests
# ---------------------------------------------------------------------------

class TestNaturalSort:

    def test_numeric_ordering(self):
        names = ["LOOP_A_10", "LOOP_A_2", "LOOP_A_1", "LOOP_A_20"]
        result = sorted(names, key=main.natural_sort_key)
        assert result == ["LOOP_A_1", "LOOP_A_2", "LOOP_A_10", "LOOP_A_20"]
