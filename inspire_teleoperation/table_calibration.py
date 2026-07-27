"""Three-point Quest table-frame calibration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import NDArray

from .api import TeleopFrame


FloatArray = NDArray[np.float64]
POINT_NAMES = ("origin", "forward", "left")
POINT_INSTRUCTIONS = (
    "右手食指触碰桌面原点，稳定捏合后松开。",
    "右手食指触碰原点前方至少 8 cm，稳定捏合后松开。",
    "右手食指触碰原点左方至少 8 cm，稳定捏合后松开。",
)


def table_frame_from_points(
    origin: Any,
    forward: Any,
    left: Any,
    *,
    up_hint: Any = (0.0, 1.0, 0.0),
    minimum_axis_length: float = 0.08,
    minimum_axis_sine: float = 0.25,
    minimum_up_alignment: float = 0.7,
) -> FloatArray:
    """Return ``T_quest_table`` from origin, forward and left table points."""

    if not 0.0 < minimum_up_alignment <= 1.0:
        raise ValueError("minimum_up_alignment must be in (0, 1]")
    points = []
    for name, value in zip(
        POINT_NAMES,
        (origin, forward, left),
        strict=True,
    ):
        point = np.asarray(value, dtype=np.float64)
        if point.shape != (3,) or not np.isfinite(point).all():
            raise ValueError(f"{name} point must contain three finite values")
        points.append(point)
    origin_point, forward_point, left_point = points
    forward_vector = forward_point - origin_point
    left_vector = left_point - origin_point
    forward_length = float(np.linalg.norm(forward_vector))
    left_length = float(np.linalg.norm(left_vector))
    if forward_length < minimum_axis_length:
        raise ValueError("forward point is too close to the table origin")
    if left_length < minimum_axis_length:
        raise ValueError("left point is too close to the table origin")

    x_axis = forward_vector / forward_length
    cross = np.cross(x_axis, left_vector / left_length)
    cross_length = float(np.linalg.norm(cross))
    if cross_length < minimum_axis_sine:
        raise ValueError("forward and left table directions are nearly collinear")
    z_axis = cross / cross_length

    up = np.asarray(up_hint, dtype=np.float64)
    if up.shape != (3,) or not np.isfinite(up).all():
        raise ValueError("up_hint must contain three finite values")
    up_length = float(np.linalg.norm(up))
    if up_length <= 1e-9:
        raise ValueError("up_hint must be non-zero")
    up /= up_length
    if abs(float(z_axis @ up)) < minimum_up_alignment:
        raise ValueError("captured plane is too far from the Quest horizontal plane")
    if float(z_axis @ up) < 0.0:
        z_axis *= -1.0

    y_axis = np.cross(z_axis, x_axis)
    y_axis /= np.linalg.norm(y_axis)
    x_axis = np.cross(y_axis, z_axis)
    x_axis /= np.linalg.norm(x_axis)

    transform = np.eye(4)
    transform[:3, :3] = np.column_stack((x_axis, y_axis, z_axis))
    transform[:3, 3] = origin_point
    return transform


@dataclass(slots=True)
class TableCalibrationConfig:
    hand: str = "right"
    fingertip_index: int = 9
    minimum_hold_s: float = 0.25
    maximum_hold_s: float = 2.0
    maximum_spread_m: float = 0.012
    minimum_axis_length_m: float = 0.08
    minimum_axis_sine: float = 0.25
    minimum_up_alignment: float = 0.7

    def __post_init__(self) -> None:
        if self.hand not in {"left", "right"}:
            raise ValueError("table calibration hand must be 'left' or 'right'")
        if not 0 <= self.fingertip_index < 25:
            raise ValueError("fingertip_index must be in the range 0..24")
        if self.minimum_hold_s <= 0.0:
            raise ValueError("minimum_hold_s must be positive")
        if self.maximum_hold_s < self.minimum_hold_s:
            raise ValueError("maximum_hold_s must be at least minimum_hold_s")
        if self.maximum_spread_m <= 0.0:
            raise ValueError("maximum_spread_m must be positive")
        if self.minimum_axis_length_m <= 0.0:
            raise ValueError("minimum_axis_length_m must be positive")
        if not 0.0 < self.minimum_axis_sine <= 1.0:
            raise ValueError("minimum_axis_sine must be in (0, 1]")
        if not 0.0 < self.minimum_up_alignment <= 1.0:
            raise ValueError("minimum_up_alignment must be in (0, 1]")


class ThreePointTableCalibration:
    """Capture three stable fingertip points using pinch-and-release."""

    def __init__(self, config: TableCalibrationConfig | None = None) -> None:
        self.config = config or TableCalibrationConfig()
        self._points: list[FloatArray] = []
        self._table_to_quest: FloatArray | None = None
        self._pinch_active = False
        self._await_release = False
        self._samples: list[FloatArray] = []
        self._sample_started_at: float | None = None
        self._last_error = ""
        self._revision = 0

    @property
    def calibrated(self) -> bool:
        return self._table_to_quest is not None

    @property
    def table_to_quest(self) -> FloatArray:
        if self._table_to_quest is None:
            raise RuntimeError("table frame has not been calibrated")
        return self._table_to_quest.copy()

    @property
    def captured_count(self) -> int:
        return len(self._points)

    @property
    def instruction(self) -> str:
        if self.calibrated:
            return "桌面坐标系标定完成。"
        return POINT_INSTRUCTIONS[len(self._points)]

    def reset(self) -> None:
        self._points.clear()
        self._table_to_quest = None
        self._pinch_active = False
        self._await_release = False
        self._samples.clear()
        self._sample_started_at = None
        self._last_error = ""
        self._revision += 1

    def capture_points(self, origin: Any, forward: Any, left: Any) -> FloatArray:
        transform = table_frame_from_points(
            origin,
            forward,
            left,
            minimum_axis_length=self.config.minimum_axis_length_m,
            minimum_axis_sine=self.config.minimum_axis_sine,
            minimum_up_alignment=self.config.minimum_up_alignment,
        )
        self._points = [
            np.asarray(point, dtype=np.float64).copy()
            for point in (origin, forward, left)
        ]
        self._table_to_quest = transform
        self._last_error = ""
        self._revision += 1
        return transform.copy()

    def _fingertip(self, frame: TeleopFrame) -> FloatArray | None:
        raw = frame.extras.get("raw_openxr_hand_landmarks", {})
        points = raw.get(self.config.hand) if hasattr(raw, "get") else None
        if points is None:
            return None
        landmarks = np.asarray(points, dtype=np.float64)
        if landmarks.shape != (25, 3) or not np.isfinite(landmarks).all():
            return None
        return landmarks[self.config.fingertip_index].copy()

    def _pinching(self, frame: TeleopFrame) -> bool:
        gestures = frame.extras.get("hand_gestures", {})
        hand = gestures.get(self.config.hand, {}) if hasattr(gestures, "get") else {}
        return bool(hand.get("pinch", False)) if hasattr(hand, "get") else False

    def _abort_sample(self, detail: str) -> None:
        self._pinch_active = False
        self._await_release = True
        self._samples.clear()
        self._sample_started_at = None
        self._last_error = detail
        self._revision += 1

    def _finish_sample(self, timestamp: float) -> None:
        started_at = self._sample_started_at
        samples = self._samples
        self._pinch_active = False
        self._samples = []
        self._sample_started_at = None
        if started_at is None or not samples:
            return
        duration = max(0.0, timestamp - started_at)
        if duration < self.config.minimum_hold_s:
            self._last_error = (
                f"Pinch was too short ({duration:.2f}s); hold for "
                f"{self.config.minimum_hold_s:.2f}s."
            )
            self._revision += 1
            return
        mean = np.mean(samples, axis=0)
        spread = float(np.max(np.linalg.norm(np.asarray(samples) - mean, axis=1)))
        if spread > self.config.maximum_spread_m:
            self._last_error = (
                f"Fingertip moved {spread * 1000.0:.0f}mm while pinching; "
                "hold it still and retry."
            )
            self._revision += 1
            return

        candidate = mean.astype(np.float64, copy=True)
        if len(self._points) == 1:
            distance = float(np.linalg.norm(candidate - self._points[0]))
            if distance < self.config.minimum_axis_length_m:
                self._last_error = "Forward point is too close to the origin."
                self._revision += 1
                return
        if len(self._points) == 2:
            try:
                transform = table_frame_from_points(
                    self._points[0],
                    self._points[1],
                    candidate,
                    minimum_axis_length=self.config.minimum_axis_length_m,
                    minimum_axis_sine=self.config.minimum_axis_sine,
                    minimum_up_alignment=self.config.minimum_up_alignment,
                )
            except ValueError as error:
                self._last_error = str(error)
                self._revision += 1
                return
            self._points.append(candidate)
            self._table_to_quest = transform
        else:
            self._points.append(candidate)
        self._last_error = ""
        self._revision += 1

    def update(self, frame: TeleopFrame) -> bool:
        """Consume one frame and return true only when calibration completes."""

        if self.calibrated:
            return False
        fingertip = self._fingertip(frame)
        pinching = self._pinching(frame)
        if self._await_release:
            if not pinching:
                self._await_release = False
            return False
        if fingertip is None:
            if self._pinch_active or pinching:
                self._abort_sample("Raw OpenXR fingertip tracking was lost.")
            return False

        was_calibrated = self.calibrated
        if pinching:
            if not self._pinch_active:
                self._pinch_active = True
                self._samples = []
                self._sample_started_at = frame.timestamp
            assert self._sample_started_at is not None
            if frame.timestamp - self._sample_started_at > self.config.maximum_hold_s:
                self._abort_sample("Pinch was held too long; release and retry.")
                return False
            self._samples.append(fingertip)
        elif self._pinch_active:
            self._finish_sample(frame.timestamp)
        return not was_calibrated and self.calibrated

    def telemetry(self) -> dict[str, object]:
        return {
            "enabled": True,
            "calibrated": self.calibrated,
            "captured_count": self.captured_count,
            "required_count": 3,
            "next_point": (
                None if self.calibrated else POINT_NAMES[self.captured_count]
            ),
            "instruction": self.instruction,
            "pinch_active": self._pinch_active,
            "await_release": self._await_release,
            "sample_count": len(self._samples),
            "last_error": self._last_error,
            "revision": self._revision,
            "table_to_quest": (
                self._table_to_quest.tolist()
                if self._table_to_quest is not None
                else None
            ),
            "point_names": list(POINT_NAMES),
            "points": [point.tolist() for point in self._points],
        }
