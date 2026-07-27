"""MuJoCo adapter for the production Inspire-hand retargeting pipeline."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Callable

import numpy as np
from numpy.typing import NDArray

from .api import TeleopFrame
from .hand_retargeting import (
    HandRetargeting,
    denormalize_hardware_targets,
    normalize_hardware_targets,
)


FloatArray = NDArray[np.float64]
HAND_MODEL_JOINT_SUFFIXES = (
    "thumb_proximal_yaw_joint",
    "thumb_proximal_pitch_joint",
    "thumb_intermediate_joint",
    "thumb_distal_joint",
    "index_proximal_joint",
    "index_intermediate_joint",
    "middle_proximal_joint",
    "middle_intermediate_joint",
    "ring_proximal_joint",
    "ring_intermediate_joint",
    "pinky_proximal_joint",
    "pinky_intermediate_joint",
)
HAND_MODEL_JOINT_LIMITS = np.array(
    (
        (-0.1, 1.3),
        (0.0, 0.5),
        (0.0, 0.8),
        (0.0, 1.2),
        *((0.0, 1.7),) * 8,
    ),
    dtype=np.float64,
)


def hand_model_joint_names(side: str) -> tuple[str, ...]:
    """Return attached-model joint names in MuJoCo qpos order."""

    if side not in {"left", "right"}:
        raise ValueError(f"unknown hand side: {side!r}")
    prefix = "L" if side == "left" else "R"
    return tuple(f"{prefix}_{suffix}" for suffix in HAND_MODEL_JOINT_SUFFIXES)


def expand_hardware_radians(radians: FloatArray) -> FloatArray:
    """Expand six hardware joints to the URDF's twelve including mimics."""

    hardware = np.asarray(radians, dtype=np.float64)
    if hardware.shape != (6,) or not np.isfinite(hardware).all():
        raise ValueError("hand radians must contain six finite values")
    pinky, ring, middle, index, thumb_pitch, thumb_yaw = hardware
    expanded = np.array(
        [
            thumb_yaw,
            thumb_pitch,
            1.6 * thumb_pitch,
            2.4 * thumb_pitch,
            index,
            index,
            middle,
            middle,
            ring,
            ring,
            pinky,
            pinky,
        ],
        dtype=np.float64,
    )
    return np.clip(
        expanded,
        HAND_MODEL_JOINT_LIMITS[:, 0],
        HAND_MODEL_JOINT_LIMITS[:, 1],
    )


@dataclass(slots=True)
class InspireHandSimState:
    """Instantaneous simulated state in the real hand's six-joint schema."""

    side: str
    normalized_action: FloatArray
    radians_action: FloatArray
    hold_reason: str = "waiting_for_tracking"
    updates: int = 0
    failures: int = 0
    last_error: str = ""


class InspireHandSimulation:
    """Run the existing real-hand retargeter without opening Modbus sockets."""

    def __init__(
        self,
        *,
        retargeting_factory: Callable[[], Any] | None = None,
    ) -> None:
        self._retargeting_factory = retargeting_factory or HandRetargeting
        self._retargeting: Any | None = None
        self._executor: ThreadPoolExecutor | None = None
        self.states: dict[str, InspireHandSimState] = {}
        self._started = False
        self._last_sequence = 0

    def start(self) -> None:
        if self._started:
            return
        open_action = np.ones(6, dtype=np.float64)
        open_radians = denormalize_hardware_targets(open_action)
        self.states = {
            side: InspireHandSimState(
                side=side,
                normalized_action=open_action.copy(),
                radians_action=open_radians.copy(),
            )
            for side in ("left", "right")
        }
        self._retargeting = self._retargeting_factory()
        self._executor = ThreadPoolExecutor(
            max_workers=2,
            thread_name_prefix="inspire-hand-sim",
        )
        self._started = True

    def _retarget_side(
        self,
        side: str,
        landmarks: FloatArray,
    ) -> tuple[FloatArray, FloatArray]:
        if self._retargeting is None:
            raise RuntimeError("Inspire hand retargeter is not running")
        radians = np.asarray(
            self._retargeting.retarget(side, landmarks),
            dtype=np.float64,
        )
        normalized = normalize_hardware_targets(radians)
        # The real hand receives the clipped normalized command. Convert that
        # command back to radians so the simulation matches the hardware path
        # even when the optimizer overshoots a limit by numerical tolerance.
        commanded_radians = denormalize_hardware_targets(normalized)
        return commanded_radians, normalized

    def update(self, frame: TeleopFrame, *, enabled: bool) -> None:
        if not self._started or self._executor is None:
            raise RuntimeError("Inspire hand simulation has not been started")
        self._last_sequence = frame.sequence
        if not enabled:
            for state in self.states.values():
                state.hold_reason = "disabled"
            return
        if not frame.motion_data_ready:
            for state in self.states.values():
                state.hold_reason = "tracking_lost"
            return

        futures = {}
        for side, hand in (
            ("left", frame.left_hand),
            ("right", frame.right_hand),
        ):
            if hand is None:
                self.states[side].hold_reason = "tracking_lost"
                continue
            futures[side] = self._executor.submit(
                self._retarget_side,
                side,
                hand.landmarks,
            )

        for side, future in futures.items():
            state = self.states[side]
            try:
                radians, normalized = future.result()
            except (
                TypeError,
                ValueError,
                RuntimeError,
                np.linalg.LinAlgError,
            ) as error:
                state.failures += 1
                state.hold_reason = "retargeting_failed"
                state.last_error = str(error)
                continue
            state.radians_action = radians
            state.normalized_action = normalized
            state.updates += 1
            state.hold_reason = ""
            state.last_error = ""

    def model_qpos(self, side: str) -> FloatArray:
        return expand_hardware_radians(self.states[side].radians_action)

    def telemetry(self) -> dict[str, object]:
        return {
            "sequence": self._last_sequence,
            "execution": "parallel",
            "hardware_schema": [
                "pinky",
                "ring",
                "middle",
                "index",
                "thumb_bend",
                "thumb_rotation",
            ],
            "hands": {
                side: {
                    "mode": "hold" if state.hold_reason else "tracking",
                    "hold_reason": state.hold_reason,
                    "state": state.normalized_action.tolist(),
                    "action": state.normalized_action.tolist(),
                    "radians": state.radians_action.tolist(),
                    "updates": state.updates,
                    "failures": state.failures,
                    "last_error": state.last_error,
                }
                for side, state in self.states.items()
            },
        }

    def close(self) -> None:
        if self._executor is not None:
            self._executor.shutdown(wait=True, cancel_futures=True)
            self._executor = None
        self._retargeting = None
        self.states.clear()
        self._started = False
        self._last_sequence = 0
