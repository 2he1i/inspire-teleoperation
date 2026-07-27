"""Safe, six-axis YAM Pro simulation module for Quest teleoperation."""

from __future__ import annotations

from dataclasses import dataclass, field
from importlib.resources import files
from pathlib import Path
from typing import Any, Literal

import numpy as np
import yaml
from numpy.typing import NDArray

from .api import ModuleStatus, TeleopFrame
from .yam_calibration import QuestToYamCalibration
from .yam_kinematics import IKResult, YamKinematics, rotation_error_radians


FloatArray = NDArray[np.float64]
HandSide = Literal["left", "right"]
HAND_BONES = (
    (0, 1),
    (1, 2),
    (2, 3),
    (3, 4),
) + tuple(
    bone
    for finger_start in (5, 10, 15, 20)
    for bone in (
        (0, finger_start),
        (finger_start, finger_start + 1),
        (finger_start + 1, finger_start + 2),
        (finger_start + 2, finger_start + 3),
        (finger_start + 3, finger_start + 4),
    )
)


def _vector(value: Any, *, name: str, size: int) -> FloatArray:
    result = np.asarray(value, dtype=np.float64)
    if result.shape != (size,) or not np.isfinite(result).all():
        raise ValueError(f"{name} must contain {size} finite values")
    return result.copy()


@dataclass(slots=True)
class YamSimArmConfig:
    hand: HandSide = "right"
    initial_q: FloatArray = field(
        default_factory=lambda: np.array([0.0, 0.2, 0.3, 0.0, 0.0, 0.0])
    )
    zero_capture_delay: float = 3.0
    tracking_loss_grace: float = 0.5
    workspace_min: FloatArray = field(
        default_factory=lambda: np.array([-0.75, -0.75, -0.20])
    )
    workspace_max: FloatArray = field(
        default_factory=lambda: np.array([0.75, 0.75, 0.95])
    )
    max_joint_step: float = 0.045
    low_pass_alpha: float = 0.35
    ik_max_iters: int = 35
    calibration: QuestToYamCalibration = field(default_factory=QuestToYamCalibration)

    def __post_init__(self) -> None:
        if self.hand not in ("left", "right"):
            raise ValueError("hand must be 'left' or 'right'")
        self.initial_q = _vector(self.initial_q, name="initial_q", size=6)
        self.workspace_min = _vector(self.workspace_min, name="workspace_min", size=3)
        self.workspace_max = _vector(self.workspace_max, name="workspace_max", size=3)
        if np.any(self.workspace_min >= self.workspace_max):
            raise ValueError("workspace_min must be less than workspace_max")
        if not np.isfinite(self.zero_capture_delay) or self.zero_capture_delay < 0.0:
            raise ValueError("zero_capture_delay must be non-negative")
        if not np.isfinite(self.tracking_loss_grace) or self.tracking_loss_grace < 0.0:
            raise ValueError("tracking_loss_grace must be non-negative")
        if not np.isfinite(self.max_joint_step) or self.max_joint_step <= 0.0:
            raise ValueError("max_joint_step must be positive")
        if not 0.0 < self.low_pass_alpha <= 1.0:
            raise ValueError("low_pass_alpha must be in (0, 1]")
        if self.ik_max_iters <= 0:
            raise ValueError("ik_max_iters must be positive")

    @classmethod
    def from_yaml(cls, path: str | Path | None = None) -> "YamSimArmConfig":
        config_path = (
            Path(path)
            if path is not None
            else Path(
                str(
                    files("inspire_teleoperation").joinpath(
                        "assets", "yam_pro", "default_sim.yml"
                    )
                )
            )
        )
        with config_path.open("r", encoding="utf-8") as stream:
            values = yaml.safe_load(stream) or {}
        calibration = QuestToYamCalibration(
            axis_rotation=values.pop("axis_rotation", np.eye(3)),
            translation_scale=values.pop("translation_scale", np.ones(3)),
            wrist_to_tcp=values.pop("wrist_to_tcp", np.eye(4)),
        )
        return cls(calibration=calibration, **values)


class YamSimArmModule:
    """Consume one Quest wrist and update a headless or visible MuJoCo arm."""

    name = "yam_sim_arm"

    def __init__(
        self,
        *,
        config: YamSimArmConfig | None = None,
        kinematics: YamKinematics | None = None,
        model_path: str | Path | None = None,
        viewer: bool = False,
    ) -> None:
        self.config = config or YamSimArmConfig.from_yaml()
        self.kinematics = kinematics
        self.model_path = model_path
        self.viewer_enabled = bool(viewer)
        self._viewer: Any | None = None
        self._sim_data: Any | None = None
        self._hand_visual_ids: dict[str, tuple[int, np.ndarray, np.ndarray]] = {}
        self._hand_visualized = {"left": False, "right": False}
        self._fixed_camera_id = -1
        self._started = False
        self._q_target = self.config.initial_q.copy()
        self._tcp_pose: FloatArray | None = None
        self._quest_target: FloatArray | None = None
        self._hold_reason = "not started"
        self._rate_limited = False
        self._ik_attempts = 0
        self._ik_successes = 0
        self._position_error = 0.0
        self._orientation_error = 0.0
        self._last_ik_detail = ""
        self._last_sequence = 0

    @property
    def q_target(self) -> FloatArray:
        return self._q_target.copy()

    @property
    def tcp_pose(self) -> FloatArray:
        if self._tcp_pose is None:
            raise RuntimeError("YAM simulation module has not been started")
        return self._tcp_pose.copy()

    def start(self) -> None:
        if self._started:
            return
        if self.kinematics is None:
            self.kinematics = YamKinematics(self.model_path)
        if not self.kinematics.within_limits(self._q_target):
            raise ValueError("initial_q is outside the YAM model joint limits")
        self._tcp_pose = self.kinematics.fk(self._q_target)
        self._hold_reason = "waiting_for_tracking"
        self.config.calibration.reset()
        self._start_simulation()
        self._sync_simulation(self._tcp_pose)
        self._started = True

    def _start_simulation(self) -> None:
        if not hasattr(self.kinematics, "model"):
            if self.viewer_enabled:
                raise ValueError("viewer requires a MuJoCo-backed YamKinematics")
            return
        import mujoco

        assert self.kinematics is not None
        self._sim_data = mujoco.MjData(self.kinematics.model)
        self._cache_scene_ids()
        if self.viewer_enabled:
            from mujoco import viewer

            self._viewer = viewer.launch_passive(
                self.kinematics.model,
                self._sim_data,
                show_left_ui=False,
                show_right_ui=False,
            )
            self._apply_fixed_camera()

    def _cache_scene_ids(self) -> None:
        if self.kinematics is None:
            return
        import mujoco

        model = self.kinematics.model
        self._fixed_camera_id = mujoco.mj_name2id(
            model, mujoco.mjtObj.mjOBJ_CAMERA, "fixed_table_view"
        )
        for side in ("left", "right"):
            body_id = mujoco.mj_name2id(
                model, mujoco.mjtObj.mjOBJ_BODY, f"{side}_hand_visual"
            )
            mocap_id = int(model.body_mocapid[body_id])
            site_ids = np.array(
                [
                    mujoco.mj_name2id(
                        model,
                        mujoco.mjtObj.mjOBJ_SITE,
                        f"{side}_hand_joint_{index:02d}",
                    )
                    for index in range(25)
                ],
                dtype=np.int32,
            )
            geom_ids = np.array(
                [
                    mujoco.mj_name2id(
                        model,
                        mujoco.mjtObj.mjOBJ_GEOM,
                        f"{side}_hand_bone_{index:02d}",
                    )
                    for index in range(len(HAND_BONES))
                ],
                dtype=np.int32,
            )
            # These visuals are deliberately repositioned at runtime. MuJoCo
            # marks zero-offset sites/geoms as same-frame during compilation;
            # clear that optimization so mj_forward uses the updated offsets.
            for site_id in site_ids:
                model.site_sameframe[site_id] = mujoco.mjtSameFrame.mjSAMEFRAME_NONE
            for geom_id in geom_ids:
                model.geom_sameframe[geom_id] = mujoco.mjtSameFrame.mjSAMEFRAME_NONE
            self._hand_visual_ids[side] = (mocap_id, site_ids, geom_ids)

    def _apply_fixed_camera(self) -> None:
        if self._viewer is None or self._fixed_camera_id < 0:
            return
        import mujoco

        self._viewer.cam.type = mujoco.mjtCamera.mjCAMERA_FIXED
        self._viewer.cam.fixedcamid = self._fixed_camera_id

    def _tracking_wrist(self, frame: TeleopFrame) -> FloatArray | None:
        hand = frame.right_hand if self.config.hand == "right" else frame.left_hand
        if not frame.motion_data_ready or hand is None or hand.wrist is None:
            return None
        wrist = hand.wrist.matrix
        return wrist.copy() if np.isfinite(wrist).all() else None

    def _hold(self, reason: str, *, reset_clutch: bool) -> None:
        self._hold_reason = reason
        self._rate_limited = False
        if reset_clutch:
            self.config.calibration.reset()
            self._hide_hand_visuals()
        if self._tcp_pose is not None:
            target = (
                self._quest_target if self._quest_target is not None else self._tcp_pose
            )
            self._sync_simulation(target)

    def request_clutch(self) -> None:
        """Hold and recapture both Quest and TCP origins on the next valid frame."""

        self.config.calibration.reset()
        self._hide_hand_visuals()
        self._hold_reason = "clutch_requested"
        self._rate_limited = False

    def update(self, frame: TeleopFrame, *, enabled: bool) -> None:
        if not self._started or self.kinematics is None or self._tcp_pose is None:
            raise RuntimeError("YAM simulation module has not been started")
        self._last_sequence = frame.sequence
        if not enabled:
            self._hold("disabled", reset_clutch=True)
            return
        wrist = self._tracking_wrist(frame)
        if wrist is None:
            self._hold("tracking_lost", reset_clutch=True)
            return
        if not self.config.calibration.captured:
            self.config.calibration.capture(wrist, self._tcp_pose)
            self._quest_target = self._tcp_pose.copy()
            self._update_hand_visuals(frame)
            self._hold("clutch_captured", reset_clutch=False)
            return

        try:
            target = self.config.calibration.target(wrist)
        except (TypeError, ValueError, np.linalg.LinAlgError) as error:
            self._last_ik_detail = str(error)
            self._hold("invalid_target", reset_clutch=True)
            return
        self._quest_target = target.copy()
        self._update_hand_visuals(frame)
        position = target[:3, 3]
        if (
            not np.isfinite(target).all()
            or np.any(position < self.config.workspace_min)
            or np.any(position > self.config.workspace_max)
        ):
            self._hold("target_outside_workspace", reset_clutch=True)
            return

        self._ik_attempts += 1
        result: IKResult = self.kinematics.ik(
            target,
            init_q=self._q_target,
            max_iters=self.config.ik_max_iters,
        )
        self._last_ik_detail = result.detail
        if (
            not result.success
            or not np.isfinite(result.q).all()
            or not self.kinematics.within_limits(result.q, tolerance=1e-6)
        ):
            self._hold("ik_failed", reset_clutch=True)
            return

        filtered = self._q_target + self.config.low_pass_alpha * (
            result.q - self._q_target
        )
        delta = filtered - self._q_target
        limited_delta = np.clip(
            delta, -self.config.max_joint_step, self.config.max_joint_step
        )
        self._rate_limited = not np.allclose(delta, limited_delta, atol=1e-12)
        candidate = self.kinematics.clamp_to_limits(
            self._q_target + limited_delta
        )
        if not self.kinematics.within_limits(candidate):
            self._hold("joint_limit_violation", reset_clutch=True)
            return

        self._q_target = candidate
        self._tcp_pose = self.kinematics.fk(candidate)
        self._position_error = float(
            np.linalg.norm(target[:3, 3] - self._tcp_pose[:3, 3])
        )
        self._orientation_error = rotation_error_radians(self._tcp_pose, target)
        self._ik_successes += 1
        self._hold_reason = ""
        self._sync_simulation(target)

    @staticmethod
    def _rotation_quaternion(rotation: FloatArray) -> FloatArray:
        import mujoco

        quaternion = np.empty(4, dtype=np.float64)
        mujoco.mju_mat2Quat(quaternion, rotation.ravel())
        return quaternion

    @classmethod
    def _bone_pose(
        cls, start: FloatArray, end: FloatArray
    ) -> tuple[FloatArray, FloatArray, float]:
        direction = end - start
        length = float(np.linalg.norm(direction))
        if length <= 1e-9:
            return (start.copy(), np.array([1.0, 0.0, 0.0, 0.0]), 1e-5)
        z_axis = direction / length
        reference = np.array([0.0, 0.0, 1.0])
        if abs(float(z_axis @ reference)) > 0.95:
            reference = np.array([0.0, 1.0, 0.0])
        x_axis = np.cross(reference, z_axis)
        x_axis /= np.linalg.norm(x_axis)
        y_axis = np.cross(z_axis, x_axis)
        rotation = np.column_stack((x_axis, y_axis, z_axis))
        return (
            0.5 * (start + end),
            cls._rotation_quaternion(rotation),
            length,
        )

    def _update_hand_visuals(self, frame: TeleopFrame) -> None:
        if (
            self._sim_data is None
            or self.kinematics is None
            or not self.config.calibration.captured
        ):
            return
        raw_by_side = frame.extras.get("raw_openxr_hand_landmarks", {})
        for side in ("left", "right"):
            hand = frame.left_hand if side == "left" else frame.right_hand
            if hand is None or hand.wrist is None:
                self._hide_hand_visual(side)
                continue
            wrist = hand.wrist.matrix
            try:
                hand_target = self.config.calibration.target(wrist)
            except (RuntimeError, TypeError, ValueError, np.linalg.LinAlgError):
                self._hide_hand_visual(side)
                continue

            raw = raw_by_side.get(side) if hasattr(raw_by_side, "get") else None
            if raw is not None:
                points = np.asarray(raw, dtype=np.float64)
                if points.shape != (25, 3) or not np.isfinite(points).all():
                    self._hide_hand_visual(side)
                    continue
                local_points = (wrist[:3, :3].T @ (points - wrist[:3, 3]).T).T
            else:
                local_points = np.asarray(hand.landmarks, dtype=np.float64)

            mapped_points = (self.config.calibration.axis_rotation @ local_points.T).T
            self._set_hand_visual(side, hand_target, mapped_points)

    def _set_hand_visual(
        self, side: str, target: FloatArray, local_points: FloatArray
    ) -> None:
        if (
            self._sim_data is None
            or self.kinematics is None
            or side not in self._hand_visual_ids
        ):
            return
        mocap_id, site_ids, geom_ids = self._hand_visual_ids[side]
        model = self.kinematics.model
        self._sim_data.mocap_pos[mocap_id] = target[:3, 3]
        self._sim_data.mocap_quat[mocap_id] = self._rotation_quaternion(target[:3, :3])
        for site_id, point in zip(site_ids, local_points, strict=True):
            model.site_pos[site_id] = point
        for geom_id, (start_index, end_index) in zip(geom_ids, HAND_BONES, strict=True):
            position, quaternion, length = self._bone_pose(
                local_points[start_index], local_points[end_index]
            )
            model.geom_pos[geom_id] = position
            model.geom_quat[geom_id] = quaternion
            model.geom_size[geom_id, 0] = 0.004
            model.geom_size[geom_id, 1] = max(0.5 * length, 1e-5)
        self._hand_visualized[side] = True

    def _hide_hand_visual(self, side: str) -> None:
        if self._sim_data is None or side not in self._hand_visual_ids:
            return
        mocap_id, _, _ = self._hand_visual_ids[side]
        self._sim_data.mocap_pos[mocap_id] = (0.0, 0.0, -10.0)
        self._sim_data.mocap_quat[mocap_id] = (1.0, 0.0, 0.0, 0.0)
        self._hand_visualized[side] = False

    def _hide_hand_visuals(self) -> None:
        for side in ("left", "right"):
            self._hide_hand_visual(side)

    def _sync_simulation(self, target: FloatArray) -> None:
        if self._sim_data is None or self.kinematics is None:
            return
        import mujoco

        self._sim_data.qpos[:] = self._q_target
        target_body = mujoco.mj_name2id(
            self.kinematics.model,
            mujoco.mjtObj.mjOBJ_BODY,
            "quest_target_body",
        )
        mocap_id = self.kinematics.model.body_mocapid[target_body]
        if mocap_id >= 0:
            self._sim_data.mocap_pos[mocap_id] = target[:3, 3]
            quaternion = np.empty(4, dtype=np.float64)
            mujoco.mju_mat2Quat(quaternion, target[:3, :3].ravel())
            self._sim_data.mocap_quat[mocap_id] = quaternion
        mujoco.mj_forward(self.kinematics.model, self._sim_data)
        if self._viewer is not None and self._viewer.is_running():
            self._apply_fixed_camera()
            self._viewer.sync()

    def status(self) -> ModuleStatus:
        success_rate = (
            self._ik_successes / self._ik_attempts if self._ik_attempts else 0.0
        )
        return ModuleStatus(
            name=self.name,
            ready=self._started,
            detail=self._hold_reason,
            telemetry={
                "hand": self.config.hand,
                "sequence": self._last_sequence,
                "mode": "hold" if self._hold_reason else "tracking",
                "hold_reason": self._hold_reason,
                "clutch_captured": self.config.calibration.captured,
                "q_target": self._q_target.tolist(),
                "tcp_pose": (
                    self._tcp_pose.tolist() if self._tcp_pose is not None else None
                ),
                "quest_target": (
                    self._quest_target.tolist()
                    if self._quest_target is not None
                    else None
                ),
                "ik_attempts": self._ik_attempts,
                "ik_successes": self._ik_successes,
                "ik_success_rate": success_rate,
                "ik_detail": self._last_ik_detail,
                "position_error_m": self._position_error,
                "orientation_error_rad": self._orientation_error,
                "rate_limited": self._rate_limited,
                "hands_visualized": dict(self._hand_visualized),
                "joint_limits": (
                    self.kinematics.joint_limits.tolist()
                    if self.kinematics is not None
                    else None
                ),
            },
        )

    def close(self) -> None:
        self.config.calibration.reset()
        self._hold_reason = "closed"
        if self._viewer is not None:
            self._viewer.close()
            self._viewer = None
        self._sim_data = None
        self._hand_visual_ids.clear()
        self._hand_visualized = {"left": False, "right": False}
        self._started = False
