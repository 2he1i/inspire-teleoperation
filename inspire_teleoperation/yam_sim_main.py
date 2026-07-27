"""Command-line entry point for stage-one, hardware-free YAM simulation."""

from __future__ import annotations

import argparse
import logging
import math
import os
import time
from pathlib import Path
from typing import Sequence

import numpy as np

from .api import HandTracking, RigidTransform, TeleopFrame
from .quest_source import QuestSource
from .runtime import TeleopRuntime
from .table_calibration import ThreePointTableCalibration
from .yam_dual_sim import DualYamSimArmModule
from .yam_sim_arm import YamSimArmConfig


logger = logging.getLogger(__name__)
NVIDIA_OFFLOAD_ENV = {
    "__NV_PRIME_RENDER_OFFLOAD": "1",
    "__GLX_VENDOR_LIBRARY_NAME": "nvidia",
    "__VK_LAYER_NV_optimus": "NVIDIA_only",
}


def _configure_gpu(mode: str) -> dict[str, str]:
    if mode == "nvidia":
        os.environ.update(NVIDIA_OFFLOAD_ENV)
        return NVIDIA_OFFLOAD_ENV.copy()
    if mode == "system":
        return {}
    raise ValueError(f"unknown GPU mode: {mode!r}")


def _arm_log_mode(telemetry: dict[str, object]) -> str:
    reason = str(telemetry["hold_reason"])
    if reason == "zero_pose_countdown":
        remaining = float(telemetry["zero_capture_remaining_s"])
        return f"zero in {remaining:.1f}s"
    return reason or "tracking"


def _demo_hand_landmarks(*, mirrored: bool) -> np.ndarray:
    """Create a recognizable 25-joint OpenXR-style hand in wrist axes."""

    points = np.zeros((25, 3), dtype=np.float64)
    points[1:5] = [
        [0.025, 0.012, 0.0],
        [0.040, 0.026, 0.0],
        [0.052, 0.041, 0.0],
        [0.062, 0.055, 0.0],
    ]
    for start, lateral, lengths in (
        (5, 0.027, (0.024, 0.048, 0.072, 0.094, 0.112)),
        (10, 0.010, (0.026, 0.054, 0.082, 0.107, 0.128)),
        (15, -0.009, (0.025, 0.052, 0.078, 0.101, 0.119)),
        (20, -0.027, (0.022, 0.044, 0.066, 0.085, 0.100)),
    ):
        for offset, length in enumerate(lengths):
            points[start + offset] = (lateral, length, 0.0)
    if mirrored:
        points[:, 0] *= -1.0
    return points


class DemoQuestSource:
    """Deterministic wrist trajectory for testing without a headset."""

    def __init__(self, *, hand: str, radius: float = 0.035) -> None:
        self.hand = hand
        self.radius = radius
        self._started_at: float | None = None
        self._sequence = 0

    def start(self) -> None:
        self._started_at = time.monotonic()

    def read(self) -> TeleopFrame:
        if self._started_at is None:
            raise RuntimeError("demo source has not been started")
        elapsed = time.monotonic() - self._started_at
        phase = 0.45 * elapsed
        pose = np.eye(4)
        pose[0, 3] = self.radius * math.sin(phase)
        pose[1, 3] = 0.5 * self.radius * math.sin(phase * 0.7)
        angle = math.radians(8.0) * math.sin(phase * 0.5)
        pose[:3, :3] = np.array(
            [
                [math.cos(angle), -math.sin(angle), 0.0],
                [math.sin(angle), math.cos(angle), 0.0],
                [0.0, 0.0, 1.0],
            ]
        )
        right_pose = pose
        left_pose = pose.copy()
        left_pose[0, 3] -= 0.18
        right_local = _demo_hand_landmarks(mirrored=False)
        left_local = _demo_hand_landmarks(mirrored=True)
        right_raw = (right_pose[:3, :3] @ right_local.T).T + right_pose[:3, 3]
        left_raw = (left_pose[:3, :3] @ left_local.T).T + left_pose[:3, 3]
        right = HandTracking(right_local, wrist=RigidTransform(right_pose))
        left = HandTracking(left_local, wrist=RigidTransform(left_pose))
        self._sequence += 1
        return TeleopFrame(
            sequence=self._sequence,
            timestamp=time.monotonic(),
            motion_data_ready=True,
            left_hand=left,
            right_hand=right,
            extras={
                "wrist_pose_convention": {
                    "left": "synthetic_openxr",
                    "right": "synthetic_openxr",
                },
                "raw_openxr_hand_landmarks": {
                    "left": left_raw,
                    "right": right_raw,
                },
                "hand_gestures": {
                    "left": {"pinch": False, "pinch_value": 0.0},
                    "right": {"pinch": False, "pinch_value": 0.0},
                },
            },
        )

    def close(self) -> None:
        self._started_at = None


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Quest left/right wrists to two independent six-axis YAM Pro "
            "MuJoCo arms and Quest landmarks to two attached Inspire hands. "
            "This command never connects to CAN or Modbus hardware."
        )
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="YAML calibration/safety config (default: packaged simulation config).",
    )
    parser.add_argument(
        "--model",
        type=Path,
        help=(
            "Single-arm MuJoCo XML used to build the dual scene "
            "(default: packaged YAM Pro + Inspire TCP model)."
        ),
    )
    parser.add_argument(
        "--frequency",
        type=float,
        default=60.0,
        help="Simulation update frequency in Hz (default: 60).",
    )
    parser.add_argument(
        "--duration",
        type=float,
        help="Stop after this many seconds; default runs until Ctrl-C.",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Use a synthetic wrist trajectory instead of starting Quest/TeleVuer.",
    )
    parser.add_argument(
        "--viewer",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Open MuJoCo passive viewer (default: enabled).",
    )
    parser.add_argument(
        "--gpu",
        choices=("nvidia", "system"),
        default="nvidia",
        help=(
            "OpenGL GPU selection: NVIDIA PRIME offload by default; "
            "'system' leaves GPU selection to the desktop."
        ),
    )
    parser.add_argument(
        "--hide-hand-markers",
        action="store_true",
        help="Hide Quest hand markers when using a headset.",
    )
    parser.add_argument(
        "--simulate-hands",
        action=argparse.BooleanOptionalAction,
        default=True,
        help=(
            "Attach and drive both Inspire hand models with the production "
            "retargeter (default: enabled; never opens Modbus connections)."
        ),
    )
    parser.add_argument(
        "--table-calibration",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "Capture table origin/forward/left with right-index pinch gestures. "
            "Enabled by default for Quest and disabled by default for --demo."
        ),
    )
    args = parser.parse_args(argv)
    if args.frequency <= 0.0:
        parser.error("--frequency must be positive")
    if args.duration is not None and args.duration <= 0.0:
        parser.error("--duration must be positive")
    return args


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    _configure_gpu(args.gpu)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    config = YamSimArmConfig.from_yaml(args.config)
    source = (
        DemoQuestSource(hand=config.hand)
        if args.demo
        else QuestSource(show_hand_markers=not args.hide_hand_markers)
    )
    table_calibration_enabled = (
        not args.demo
        if args.table_calibration is None
        else bool(args.table_calibration)
    )
    table_calibration = (
        ThreePointTableCalibration() if table_calibration_enabled else None
    )
    arm = DualYamSimArmModule(
        config=config,
        model_path=args.model,
        viewer=args.viewer,
        simulate_hands=args.simulate_hands,
        table_calibration=table_calibration,
    )
    runtime = TeleopRuntime(source, [arm])
    runtime.set_enabled(True)
    period = 1.0 / args.frequency
    started_at = time.monotonic()
    last_report = started_at
    table_completion_reported = False
    try:
        runtime.start()
        logger.info(
            "Dual YAM simulation active (%s, %s input). "
            "%s "
            "After detecting a hand, keep it at the desired zero pose for "
            "%.1f seconds; synchronization starts after capture. The viewer "
            "starts in Ego view using %s GPU selection; drag the mouse to "
            "rotate. Ctrl-C stops.",
            "dual Inspire hands" if args.simulate_hands else "arms only",
            "synthetic" if args.demo else "Quest",
            (
                "First calibrate the table with three right-index pinch-and-release "
                "captures: origin, forward, then left."
                if table_calibration_enabled
                else "Table calibration is disabled."
            ),
            config.zero_capture_delay,
            args.gpu,
        )
        while args.duration is None or time.monotonic() - started_at < args.duration:
            cycle_started = time.monotonic()
            runtime.step()
            now = time.monotonic()
            if (
                table_calibration is not None
                and table_calibration.calibrated
                and not table_completion_reported
            ):
                logger.info(
                    "table=3/3: 桌面坐标系标定完成；"
                    "前/左/上已映射到 YAM +X/+Y/+Z，开始双腕零位倒计时。"
                )
                table_completion_reported = True
            if now - last_report >= 1.0:
                status = arm.status()
                table_status = status.telemetry["table_calibration"]
                if (
                    table_status.get("enabled", True)
                    and not table_status["calibrated"]
                ):
                    error = table_status["last_error"]
                    logger.info(
                        "table=%d/3%s: %s%s",
                        table_status["captured_count"],
                        " pinching" if table_status["pinch_active"] else "",
                        table_status["instruction"],
                        f" Last attempt: {error}" if error else "",
                    )
                    last_report = now
                    remaining = period - (time.monotonic() - cycle_started)
                    if remaining > 0.0:
                        time.sleep(remaining)
                    continue
                arms = status.telemetry["arms"]
                left = arms["left"]
                right = arms["right"]
                hand_telemetry = status.telemetry["inspire_hands"]
                hand_summary = ""
                if "hands" in hand_telemetry:
                    hands = hand_telemetry["hands"]
                    hand_summary = (
                        " | hands "
                        f"L={hands['left']['hold_reason'] or 'tracking'} "
                        f"R={hands['right']['hold_reason'] or 'tracking'}"
                    )
                logger.info(
                    "left=%s IK=%d/%d err=%.4f m | "
                    "right=%s IK=%d/%d err=%.4f m%s",
                    _arm_log_mode(left),
                    left["ik_successes"],
                    left["ik_attempts"],
                    left["position_error_m"],
                    _arm_log_mode(right),
                    right["ik_successes"],
                    right["ik_attempts"],
                    right["position_error_m"],
                    hand_summary,
                )
                last_report = now
            remaining = period - (time.monotonic() - cycle_started)
            if remaining > 0.0:
                time.sleep(remaining)
    except KeyboardInterrupt:
        logger.info("Stopping YAM simulation.")
    finally:
        runtime.close()


if __name__ == "__main__":
    main()
