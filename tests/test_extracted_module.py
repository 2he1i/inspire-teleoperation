from __future__ import annotations

import unittest
from multiprocessing import Array
from pathlib import Path
from unittest.mock import Mock

import numpy as np

from inspire_teleoperation.dexhand import Dexhand
from inspire_teleoperation.hand_controller import AdaptiveSpeedPlannerV2
from inspire_teleoperation.main import TeleopState, _copy_landmarks, parse_args
from inspire_teleoperation.web_ui import HandTeleoperationWebUI


class ExtractedModuleTests(unittest.TestCase):
    def test_default_cli_uses_right_hand(self) -> None:
        args = parse_args(["--no-browser"])
        self.assertEqual(args.right_hand_host, "192.168.11.210")
        self.assertFalse(args.browser)

    def test_landmarks_are_validated_and_copied(self) -> None:
        shared = Array("d", 75, lock=True)
        landmarks = np.arange(75, dtype=np.float64).reshape(25, 3)
        _copy_landmarks(shared, landmarks, "right")
        self.assertEqual(list(shared), landmarks.ravel().tolist())
        with self.assertRaises(ValueError):
            _copy_landmarks(shared, np.zeros((24, 3)), "right")

    def test_state_actions(self) -> None:
        state = TeleopState()
        state.apply_action("run")
        self.assertTrue(state.tracking_enabled)
        state.apply_action("pause")
        self.assertFalse(state.tracking_enabled)
        state.apply_action("quit")
        self.assertFalse(state.running)

    def test_web_assets_are_local(self) -> None:
        ui = HandTeleoperationWebUI(parse_args(["--no-browser"]))
        html, content_type = ui.asset("/")
        self.assertIn(b"Hand Teleoperation", html)
        self.assertIn("text/html", content_type)

    def test_speed_planner_returns_six_register_values(self) -> None:
        planner = AdaptiveSpeedPlannerV2()
        speeds = planner.compute([0.5] * 6, [0.0] * 6, now=1.0)
        self.assertEqual(len(speeds), 6)
        self.assertTrue(all(0 <= speed <= 1000 for speed in speeds))

    def test_controller_imports_local_dexhand(self) -> None:
        import inspire_teleoperation.hand_controller as controller

        source = Path(controller.__file__).read_text(encoding="utf-8")
        self.assertIn("from .dexhand import Dexhand", source)
        self.assertNotIn("from dexhand import", source)

    def test_dexhand_accepts_an_injected_client(self) -> None:
        client = Mock()
        client.connected = True
        hand = Dexhand(client=client)
        self.assertTrue(hand.is_connected)
        hand.close()
        client.close.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
