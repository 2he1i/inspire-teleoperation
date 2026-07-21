"""Quest/TeleVuer adapter for the hardware-agnostic teleoperation API."""

from __future__ import annotations

import time
from typing import Any, Callable

from .api import HandTracking, RigidTransform, TeleopFrame


class QuestSource:
    """Convert TeleVuer samples into validated immutable frames."""

    def __init__(
        self,
        *,
        binocular: bool = False,
        image_shape: tuple[int, int, int] = (480, 640, 3),
        display_mode: str = "pass-through",
        show_hand_markers: bool = True,
        wrapper_factory: Callable[..., Any] | None = None,
    ) -> None:
        self._options = {
            "use_hand_tracking": True,
            "binocular": binocular,
            "img_shape": image_shape,
            "display_mode": display_mode,
            "zmq": False,
            "webrtc": False,
            "arm_reference_mode": "head_yaw",
            "show_hand_markers": show_hand_markers,
        }
        self._wrapper_factory = wrapper_factory
        self._wrapper: Any | None = None
        self._sequence = 0

    def start(self) -> None:
        if self._wrapper is not None:
            return
        factory = self._wrapper_factory
        if factory is None:
            from televuer import TeleVuerWrapper

            factory = TeleVuerWrapper
        self._wrapper = factory(**self._options)

    @staticmethod
    def _transform(sample: Any, attribute: str) -> RigidTransform | None:
        value = getattr(sample, attribute, None)
        return None if value is None else RigidTransform(value)

    def read(self) -> TeleopFrame:
        if self._wrapper is None:
            raise RuntimeError("Quest source has not been started")
        sample = self._wrapper.get_tele_data()
        self._sequence += 1
        ready = bool(getattr(sample, "motion_data_ready", False))

        left = right = None
        if ready:
            left_landmarks = getattr(sample, "left_hand_pos", None)
            right_landmarks = getattr(sample, "right_hand_pos", None)
            left_wrist = self._transform(sample, "left_wrist_pose")
            right_wrist = self._transform(sample, "right_wrist_pose")
            if left_landmarks is not None:
                left = HandTracking(left_landmarks, wrist=left_wrist)
            if right_landmarks is not None:
                right = HandTracking(right_landmarks, wrist=right_wrist)

        return TeleopFrame(
            sequence=self._sequence,
            timestamp=time.monotonic(),
            motion_data_ready=ready,
            left_hand=left,
            right_hand=right,
            head=self._transform(sample, "head_pose") if ready else None,
        )

    def close(self) -> None:
        if self._wrapper is not None:
            self._wrapper.close()
            self._wrapper = None
