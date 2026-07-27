"""Retarget Quest hand landmarks to the six hardware joint commands."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from numpy.typing import NDArray
import yaml
from dex_retargeting import RetargetingConfig


FloatArray = NDArray[np.float64]
HARDWARE_JOINT_NAMES = {
    "left": (
        "L_pinky_proximal_joint",
        "L_ring_proximal_joint",
        "L_middle_proximal_joint",
        "L_index_proximal_joint",
        "L_thumb_proximal_pitch_joint",
        "L_thumb_proximal_yaw_joint",
    ),
    "right": (
        "R_pinky_proximal_joint",
        "R_ring_proximal_joint",
        "R_middle_proximal_joint",
        "R_index_proximal_joint",
        "R_thumb_proximal_pitch_joint",
        "R_thumb_proximal_yaw_joint",
    ),
}
HARDWARE_JOINT_LIMITS = np.array(
    ((0.0, 1.7),) * 4 + ((0.0, 0.5), (-0.1, 1.3)),
    dtype=np.float64,
)


def normalize_hardware_targets(targets: FloatArray) -> FloatArray:
    """Convert retargeting radians to the device's 0-closed/1-open scale."""

    radians = np.asarray(targets, dtype=np.float64)
    if radians.shape != (6,) or not np.isfinite(radians).all():
        raise ValueError("hand targets must contain six finite values")
    minimum = HARDWARE_JOINT_LIMITS[:, 0]
    maximum = HARDWARE_JOINT_LIMITS[:, 1]
    return np.clip((maximum - radians) / (maximum - minimum), 0.0, 1.0)


def denormalize_hardware_targets(targets: FloatArray) -> FloatArray:
    """Convert 0-closed/1-open hardware commands back to model radians."""

    normalized = np.asarray(targets, dtype=np.float64)
    if normalized.shape != (6,) or not np.isfinite(normalized).all():
        raise ValueError("normalized hand targets must contain six finite values")
    minimum = HARDWARE_JOINT_LIMITS[:, 0]
    maximum = HARDWARE_JOINT_LIMITS[:, 1]
    return maximum - np.clip(normalized, 0.0, 1.0) * (maximum - minimum)


class HandRetargeting:
    """Build the left and right retargeters from this module's local assets."""

    def __init__(self, config_path: Path | None = None) -> None:
        module_dir = Path(__file__).resolve().parent
        assets_dir = module_dir / "assets"
        config_path = config_path or assets_dir / "hand_model" / "retargeting.yml"
        RetargetingConfig.set_default_urdf_dir(str(assets_dir))

        with config_path.open(encoding="utf-8") as config_file:
            config = yaml.safe_load(config_file)
        if not isinstance(config, dict) or "left" not in config or "right" not in config:
            raise ValueError("Retargeting configuration must contain left and right sections")

        self.left_retargeting = RetargetingConfig.from_dict(config["left"]).build()
        self.right_retargeting = RetargetingConfig.from_dict(config["right"]).build()
        self.left_indices = self.left_retargeting.optimizer.target_link_human_indices
        self.right_indices = self.right_retargeting.optimizer.target_link_human_indices

        left_joint_names = self.left_retargeting.joint_names
        right_joint_names = self.right_retargeting.joint_names
        self.left_dex_retargeting_to_hardware = [
            left_joint_names.index(name) for name in HARDWARE_JOINT_NAMES["left"]
        ]
        self.right_dex_retargeting_to_hardware = [
            right_joint_names.index(name) for name in HARDWARE_JOINT_NAMES["right"]
        ]

    def retarget(self, side: str, landmarks: FloatArray) -> FloatArray:
        """Run the production Quest-to-Inspire mapping for one hand."""

        if side not in HARDWARE_JOINT_NAMES:
            raise ValueError(f"unknown hand side: {side!r}")
        points = np.asarray(landmarks, dtype=np.float64)
        if points.shape != (25, 3) or not np.isfinite(points).all():
            raise ValueError("hand landmarks must have shape (25, 3) and be finite")
        indices = getattr(self, f"{side}_indices")
        retargeting = getattr(self, f"{side}_retargeting")
        joint_order = getattr(self, f"{side}_dex_retargeting_to_hardware")
        reference = points[indices[1, :]] - points[indices[0, :]]
        radians = np.asarray(
            retargeting.retarget(reference)[joint_order],
            dtype=np.float64,
        )
        if radians.shape != (6,) or not np.isfinite(radians).all():
            raise ValueError("retargeting produced invalid hand targets")
        return radians

    def retarget_normalized(self, side: str, landmarks: FloatArray) -> FloatArray:
        """Return the exact normalized command used by the real hand."""

        return normalize_hardware_targets(self.retarget(side, landmarks))
