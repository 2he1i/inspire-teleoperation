"""Configurable relative-pose mapping from Quest wrist tracking to YAM TCP."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
from numpy.typing import NDArray


FloatArray = NDArray[np.float64]


def _rotation(value: Any, *, name: str) -> FloatArray:
    rotation = np.asarray(value, dtype=np.float64)
    if rotation.shape != (3, 3):
        raise ValueError(f"{name} must have shape (3, 3)")
    if not np.isfinite(rotation).all():
        raise ValueError(f"{name} contains NaN or infinity")
    if not np.allclose(rotation.T @ rotation, np.eye(3), atol=1e-5):
        raise ValueError(f"{name} must be orthonormal")
    if not np.isclose(np.linalg.det(rotation), 1.0, atol=1e-5):
        raise ValueError(f"{name} must be right-handed")
    return rotation.copy()


def _transform(value: Any, *, name: str) -> FloatArray:
    transform = np.asarray(value, dtype=np.float64)
    if transform.shape != (4, 4):
        raise ValueError(f"{name} must have shape (4, 4)")
    if not np.isfinite(transform).all():
        raise ValueError(f"{name} contains NaN or infinity")
    if not np.allclose(transform[3], (0.0, 0.0, 0.0, 1.0), atol=1e-6):
        raise ValueError(f"{name} must be homogeneous")
    result = transform.copy()
    result[:3, :3] = _rotation(result[:3, :3], name=f"{name} rotation")
    return result


@dataclass(slots=True)
class QuestToYamCalibration:
    """Map wrist motion relative to a clutch capture into the YAM base frame.

    ``axis_rotation`` maps vectors expressed in the initial Quest wrist frame
    into YAM TCP axes. ``translation_scale`` is applied in Quest axes before
    that rotation. ``wrist_to_tcp`` is a fixed tool extrinsic and is applied by
    conjugation, so capturing the clutch never introduces an absolute jump.
    When a table reference is set, its forward/left/up axes instead map
    directly to the YAM base/world +X/+Y/+Z axes.
    """

    axis_rotation: FloatArray = field(default_factory=lambda: np.eye(3))
    translation_scale: FloatArray = field(default_factory=lambda: np.ones(3))
    wrist_to_tcp: FloatArray = field(default_factory=lambda: np.eye(4))
    _reference_frame: FloatArray | None = field(default=None, init=False, repr=False)
    _quest_origin: FloatArray | None = field(default=None, init=False, repr=False)
    _tcp_origin: FloatArray | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        self.axis_rotation = _rotation(self.axis_rotation, name="axis_rotation")
        scale = np.asarray(self.translation_scale, dtype=np.float64)
        if scale.ndim == 0:
            scale = np.repeat(scale, 3)
        if scale.shape != (3,) or not np.isfinite(scale).all():
            raise ValueError("translation_scale must be one or three finite values")
        if np.any(scale <= 0.0):
            raise ValueError("translation_scale values must be positive")
        self.translation_scale = scale.copy()
        self.wrist_to_tcp = _transform(self.wrist_to_tcp, name="wrist_to_tcp")

    @property
    def captured(self) -> bool:
        return self._quest_origin is not None and self._tcp_origin is not None

    def capture(self, quest_wrist: Any, yam_tcp: Any) -> None:
        self._quest_origin = _transform(quest_wrist, name="quest_wrist")
        self._tcp_origin = _transform(yam_tcp, name="yam_tcp")

    @property
    def reference_frame(self) -> FloatArray | None:
        """Return ``T_quest_reference`` used to express wrist deltas."""

        return (
            None
            if self._reference_frame is None
            else self._reference_frame.copy()
        )

    def set_reference_frame(self, reference_to_quest: Any) -> None:
        """Express future wrist motion in a stable world/table frame."""

        self._reference_frame = _transform(
            reference_to_quest,
            name="reference_to_quest",
        )
        self.reset()

    def clear_reference_frame(self) -> None:
        self._reference_frame = None
        self.reset()

    def reset(self) -> None:
        self._quest_origin = None
        self._tcp_origin = None

    def target(self, quest_wrist: Any) -> FloatArray:
        if not self.captured:
            raise RuntimeError("clutch has not been captured")
        current = _transform(quest_wrist, name="quest_wrist")
        assert self._quest_origin is not None
        assert self._tcp_origin is not None
        if self._reference_frame is not None:
            reference_rotation = self._reference_frame[:3, :3]
            delta_table = np.eye(4)
            delta_table[:3, 3] = reference_rotation.T @ (
                current[:3, 3] - self._quest_origin[:3, 3]
            )
            delta_table[:3, :3] = (
                reference_rotation.T
                @ current[:3, :3]
                @ self._quest_origin[:3, :3].T
                @ reference_rotation
            )
            # Table coordinates deliberately share the YAM base convention:
            # +X forward, +Y left and +Z up. Convert that base-frame delta
            # into the captured TCP's local axes before composing it.
            mapped = np.eye(4)
            tcp_rotation = self._tcp_origin[:3, :3]
            mapped[:3, :3] = (
                tcp_rotation.T @ delta_table[:3, :3] @ tcp_rotation
            )
            mapped[:3, 3] = tcp_rotation.T @ (
                self.translation_scale * delta_table[:3, 3]
            )
        else:
            delta_quest = np.linalg.inv(self._quest_origin) @ current
            mapped = np.eye(4)
            mapping = self.axis_rotation
            mapped[:3, :3] = mapping @ delta_quest[:3, :3] @ mapping.T
            mapped[:3, 3] = mapping @ (
                self.translation_scale * delta_quest[:3, 3]
            )

        extrinsic = self.wrist_to_tcp
        tcp_delta = np.linalg.inv(extrinsic) @ mapped @ extrinsic
        return self._tcp_origin @ tcp_delta

    def as_dict(self) -> dict[str, list[Any]]:
        return {
            "axis_rotation": self.axis_rotation.tolist(),
            "translation_scale": self.translation_scale.tolist(),
            "wrist_to_tcp": self.wrist_to_tcp.tolist(),
            "reference_frame": (
                self._reference_frame.tolist()
                if self._reference_frame is not None
                else None
            ),
        }
