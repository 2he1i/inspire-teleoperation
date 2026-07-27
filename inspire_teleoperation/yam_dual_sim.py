"""Independent left/right Quest control for a two-YAM MuJoCo scene."""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from .api import ModuleStatus, TeleopFrame
from .inspire_hand_sim import (
    InspireHandSimulation,
    hand_model_joint_names,
)
from .table_calibration import ThreePointTableCalibration
from .yam_calibration import QuestToYamCalibration
from .yam_dual_scene import (
    ARM_MOUNT_Y,
    build_dual_yam_scene_xml,
    dual_joint_names,
    simulated_hand_joint_name,
)
from .yam_kinematics import YamKinematics, rotation_error_radians
from .yam_sim_arm import HAND_BONES, YamSimArmConfig, YamSimArmModule


FloatArray = NDArray[np.float64]
HAND_TARGET_RGB = {
    "left": np.array([0.12, 0.55, 1.0]),
    "right": np.array([1.0, 0.35, 0.08]),
}
HAND_BLOCKED_RGB = np.array([1.0, 0.08, 0.05])
HAND_BLOCKED_REASONS = {
    "ik_failed",
    "invalid_target",
    "joint_limit_violation",
    "target_outside_workspace",
}


def _copy_calibration(source: QuestToYamCalibration) -> QuestToYamCalibration:
    calibration = QuestToYamCalibration(
        axis_rotation=source.axis_rotation.copy(),
        translation_scale=source.translation_scale.copy(),
        wrist_to_tcp=source.wrist_to_tcp.copy(),
    )
    if source.reference_frame is not None:
        calibration.set_reference_frame(source.reference_frame)
    return calibration


def _mount_transform(side: str) -> FloatArray:
    transform = np.eye(4)
    transform[1, 3] = ARM_MOUNT_Y[side]
    return transform


@dataclass(slots=True)
class _ArmState:
    side: str
    kinematics: YamKinematics
    calibration: QuestToYamCalibration
    mount: FloatArray
    q_target: FloatArray
    tcp_pose: FloatArray
    quest_target: FloatArray | None = None
    zero_capture_started_at: float | None = None
    zero_capture_remaining: float = 0.0
    last_valid_tracking_at: float | None = None
    tracking_loss_elapsed: float = 0.0
    hold_reason: str = "waiting_for_tracking"
    rate_limited: bool = False
    ik_attempts: int = 0
    ik_successes: int = 0
    position_error: float = 0.0
    orientation_error: float = 0.0
    last_ik_detail: str = ""


class _DualHandVisuals:
    """Mutable mocap-backed hand skeletons owned by one render model."""

    def __init__(self, model: Any, data: Any) -> None:
        import mujoco

        self.model = model
        self.data = data
        self.ids: dict[str, tuple[int, np.ndarray, np.ndarray, int]] = {}
        self.visible = {"left": False, "right": False}
        self.style = {"left": "hidden", "right": "hidden"}
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
            target_site_id = mujoco.mj_name2id(
                model,
                mujoco.mjtObj.mjOBJ_SITE,
                f"{side}_arm_target",
            )
            for site_id in site_ids:
                model.site_sameframe[site_id] = mujoco.mjtSameFrame.mjSAMEFRAME_NONE
            for geom_id in geom_ids:
                model.geom_sameframe[geom_id] = mujoco.mjtSameFrame.mjSAMEFRAME_NONE
            self.ids[side] = (
                mocap_id,
                site_ids,
                geom_ids,
                target_site_id,
            )

    def set(
        self,
        side: str,
        target: FloatArray,
        local_points: FloatArray,
        *,
        blocked: bool,
    ) -> None:
        mocap_id, site_ids, geom_ids, _ = self.ids[side]
        self.data.mocap_pos[mocap_id] = target[:3, 3]
        self.data.mocap_quat[mocap_id] = YamSimArmModule._rotation_quaternion(
            target[:3, :3]
        )
        for site_id, point in zip(site_ids, local_points, strict=True):
            self.model.site_pos[site_id] = point
        for geom_id, (start_index, end_index) in zip(geom_ids, HAND_BONES, strict=True):
            position, quaternion, length = YamSimArmModule._bone_pose(
                local_points[start_index], local_points[end_index]
            )
            self.model.geom_pos[geom_id] = position
            self.model.geom_quat[geom_id] = quaternion
            self.model.geom_size[geom_id, 0] = 0.004
            self.model.geom_size[geom_id, 1] = max(0.5 * length, 1e-5)
        self.visible[side] = True
        self.set_style(side, "blocked" if blocked else "target")

    def set_style(self, side: str, style: str) -> None:
        _, site_ids, geom_ids, target_site_id = self.ids[side]
        blocked = style == "blocked"
        rgb = HAND_BLOCKED_RGB if blocked else HAND_TARGET_RGB[side]
        self.model.site_rgba[site_ids, :3] = rgb
        self.model.site_rgba[site_ids, 3] = 0.82 if blocked else 0.48
        self.model.geom_rgba[geom_ids, :3] = rgb
        self.model.geom_rgba[geom_ids, 3] = 0.58 if blocked else 0.28
        self.model.site_rgba[target_site_id, :3] = rgb
        self.model.site_rgba[target_site_id, 3] = 0.92 if blocked else 0.62
        self.style[side] = style

    def hide(self, side: str) -> None:
        mocap_id, _, _, _ = self.ids[side]
        self.data.mocap_pos[mocap_id] = (0.0, 0.0, -10.0)
        self.data.mocap_quat[mocap_id] = (1.0, 0.0, 0.0, 0.0)
        self.visible[side] = False
        self.style[side] = "hidden"

    def hide_all(self) -> None:
        for side in ("left", "right"):
            self.hide(side)


class DualYamSimArmModule:
    """Drive two independent six-axis YAM simulations from Quest hands."""

    name = "yam_dual_sim_arm"

    def __init__(
        self,
        *,
        config: YamSimArmConfig | None = None,
        model_path: str | Path | None = None,
        viewer: bool = False,
        simulate_hands: bool = True,
        hand_retargeting_factory: Any | None = None,
        table_calibration: ThreePointTableCalibration | None = None,
    ) -> None:
        self.config = config or YamSimArmConfig.from_yaml()
        self.model_path = model_path
        self.viewer_enabled = bool(viewer)
        self.simulate_hands = bool(simulate_hands)
        self._hand_retargeting_factory = hand_retargeting_factory
        self.table_calibration = table_calibration
        self.states: dict[str, _ArmState] = {}
        self.render_model: Any | None = None
        self.render_data: Any | None = None
        self._viewer: Any | None = None
        self._hand_visuals: _DualHandVisuals | None = None
        self._qpos_addresses: dict[str, np.ndarray] = {}
        self._target_mocap_ids: dict[str, int] = {}
        self._hand_qpos_addresses: dict[str, np.ndarray] = {}
        self._hand_mount_mocap_ids: dict[str, int] = {}
        self._hand_geom_ids: dict[str, np.ndarray] = {}
        self._sim_hands: InspireHandSimulation | None = None
        self._control_executor: ThreadPoolExecutor | None = None
        self._window_platform = "none"
        self._started = False
        self._last_sequence = 0
        self._table_frame_applied = False

    def start(self) -> None:
        if self._started:
            return
        import mujoco

        for side in ("left", "right"):
            kinematics = YamKinematics(self.model_path)
            q_target = self.config.initial_q.copy()
            if not kinematics.within_limits(q_target):
                raise ValueError(f"{side} initial_q is outside YAM joint limits")
            mount = _mount_transform(side)
            tcp_pose = mount @ kinematics.fk(q_target)
            self.states[side] = _ArmState(
                side=side,
                kinematics=kinematics,
                calibration=_copy_calibration(self.config.calibration),
                mount=mount,
                q_target=q_target,
                tcp_pose=tcp_pose,
            )
            if (
                self.table_calibration is not None
                and self.table_calibration.calibrated
            ):
                self.states[side].calibration.set_reference_frame(
                    self.table_calibration.table_to_quest
                )
                self._table_frame_applied = True

        scene_xml = build_dual_yam_scene_xml(self.model_path)
        self.render_model = mujoco.MjModel.from_xml_string(scene_xml)
        self.render_data = mujoco.MjData(self.render_model)
        self._cache_render_ids()
        self._hand_visuals = _DualHandVisuals(self.render_model, self.render_data)
        if self.simulate_hands:
            self._sim_hands = InspireHandSimulation(
                retargeting_factory=self._hand_retargeting_factory,
            )
            self._sim_hands.start()
        self._sync_render()
        if self.viewer_enabled:
            self._window_platform = self._configure_glfw_platform()
            from mujoco import viewer

            self._viewer = viewer.launch_passive(
                self.render_model,
                self.render_data,
                show_left_ui=False,
                show_right_ui=False,
            )
            self._initialize_ego_camera()
        self._control_executor = ThreadPoolExecutor(
            max_workers=2,
            thread_name_prefix="yam-sim-control",
        )
        self._started = True

    @staticmethod
    def _configure_glfw_platform() -> str:
        """Prefer X11 for NVIDIA offload to avoid GLFW Wayland limitations."""

        if os.environ.get(
            "__GLX_VENDOR_LIBRARY_NAME"
        ) != "nvidia" or not os.environ.get("DISPLAY"):
            return "auto"
        import glfw

        glfw.init_hint(glfw.PLATFORM, glfw.PLATFORM_X11)
        return "x11"

    def _cache_render_ids(self) -> None:
        import mujoco

        assert self.render_model is not None
        for side in ("left", "right"):
            joint_ids = np.array(
                [
                    mujoco.mj_name2id(
                        self.render_model, mujoco.mjtObj.mjOBJ_JOINT, name
                    )
                    for name in dual_joint_names(side)
                ],
                dtype=np.int32,
            )
            self._qpos_addresses[side] = self.render_model.jnt_qposadr[joint_ids].copy()
            body_id = mujoco.mj_name2id(
                self.render_model,
                mujoco.mjtObj.mjOBJ_BODY,
                f"{side}_arm_target_body",
            )
            self._target_mocap_ids[side] = int(self.render_model.body_mocapid[body_id])
            hand_joint_ids = np.array(
                [
                    mujoco.mj_name2id(
                        self.render_model,
                        mujoco.mjtObj.mjOBJ_JOINT,
                        simulated_hand_joint_name(side, joint_name),
                    )
                    for joint_name in hand_model_joint_names(side)
                ],
                dtype=np.int32,
            )
            self._hand_qpos_addresses[side] = self.render_model.jnt_qposadr[
                hand_joint_ids
            ].copy()
            hand_mount_id = mujoco.mj_name2id(
                self.render_model,
                mujoco.mjtObj.mjOBJ_BODY,
                f"{side}_inspire_hand_mount",
            )
            self._hand_mount_mocap_ids[side] = int(
                self.render_model.body_mocapid[hand_mount_id]
            )
            geom_ids = []
            for geom_id, geom_body_id in enumerate(self.render_model.geom_bodyid):
                body_id = int(geom_body_id)
                while body_id:
                    if body_id == hand_mount_id:
                        geom_ids.append(geom_id)
                        break
                    body_id = int(self.render_model.body_parentid[body_id])
            self._hand_geom_ids[side] = np.asarray(geom_ids, dtype=np.int32)
            self.render_model.geom_rgba[self._hand_geom_ids[side], :3] = (
                HAND_TARGET_RGB[side]
            )
            self.render_model.geom_rgba[self._hand_geom_ids[side], 3] = 1.0
            self.render_model.geom_contype[self._hand_geom_ids[side]] = 0
            self.render_model.geom_conaffinity[self._hand_geom_ids[side]] = 0

    def _initialize_ego_camera(self) -> None:
        """Set the initial free camera once; mouse input remains authoritative."""

        if self._viewer is None:
            return
        import mujoco

        camera = self._viewer.cam
        camera.type = mujoco.mjtCamera.mjCAMERA_FREE
        camera.fixedcamid = -1
        camera.lookat[:] = (0.35, 0.0, 0.18)
        camera.distance = 0.85
        camera.azimuth = 0.0
        camera.elevation = -22.0

    @staticmethod
    def _tracked_hand(frame: TeleopFrame, side: str) -> Any | None:
        if not frame.motion_data_ready:
            return None
        return frame.left_hand if side == "left" else frame.right_hand

    def _hold(self, state: _ArmState, reason: str, *, reset_clutch: bool) -> None:
        state.hold_reason = reason
        state.rate_limited = False
        if reset_clutch:
            state.calibration.reset()
            state.zero_capture_started_at = None
            state.zero_capture_remaining = 0.0
            state.last_valid_tracking_at = None
            state.tracking_loss_elapsed = 0.0

    def _tracking_missing(
        self,
        state: _ArmState,
        timestamp: float,
        *,
        reason: str,
    ) -> None:
        if state.calibration.captured and state.last_valid_tracking_at is not None:
            state.tracking_loss_elapsed = max(
                0.0, timestamp - state.last_valid_tracking_at
            )
            if state.tracking_loss_elapsed <= self.config.tracking_loss_grace:
                self._hold(state, "tracking_dropout", reset_clutch=False)
                return
        self._hold(state, reason, reset_clutch=True)

    def request_clutch(self, side: str | None = None) -> None:
        sides = ("left", "right") if side is None else (side,)
        for selected in sides:
            if selected not in self.states:
                raise ValueError(f"unknown arm side: {selected!r}")
            self._hold(self.states[selected], "clutch_requested", reset_clutch=True)
            if self._hand_visuals is not None:
                self._hand_visuals.hide(selected)
        self._sync_render()

    def request_table_calibration(self) -> None:
        if self.table_calibration is None:
            raise RuntimeError("table calibration is not enabled")
        self.table_calibration.reset()
        self._table_frame_applied = False
        for state in self.states.values():
            state.calibration.clear_reference_frame()
            self._hold(
                state,
                "table_calibration_required",
                reset_clutch=True,
            )
        if self._hand_visuals is not None:
            self._hand_visuals.hide_all()
        self._sync_render()

    def set_table_calibration_enabled(self, enabled: bool) -> None:
        """Enable a fresh table calibration or return to the default frame."""

        if not self._started:
            raise RuntimeError("dual YAM simulation module has not been started")
        if enabled:
            if self.table_calibration is None:
                self.table_calibration = ThreePointTableCalibration()
            self.request_table_calibration()
            return

        self.table_calibration = None
        self._table_frame_applied = False
        for state in self.states.values():
            state.calibration.clear_reference_frame()
            self._hold(state, "clutch_requested", reset_clutch=True)
        if self._hand_visuals is not None:
            self._hand_visuals.hide_all()
        self._sync_render()

    def update(self, frame: TeleopFrame, *, enabled: bool) -> None:
        if not self._started:
            raise RuntimeError("dual YAM simulation module has not been started")
        self._last_sequence = frame.sequence
        if not enabled:
            for state in self.states.values():
                self._hold(state, "disabled", reset_clutch=True)
            if self._sim_hands is not None:
                self._sim_hands.update(frame, enabled=False)
            if self._hand_visuals is not None:
                self._hand_visuals.hide_all()
            self._sync_render()
            return

        if self.table_calibration is not None:
            if not self.table_calibration.calibrated:
                if self._table_frame_applied:
                    for state in self.states.values():
                        state.calibration.clear_reference_frame()
                    self._table_frame_applied = False
                self.table_calibration.update(frame)
            if not self.table_calibration.calibrated:
                if self._sim_hands is not None:
                    self._sim_hands.update(frame, enabled=True)
                for state in self.states.values():
                    self._hold(
                        state,
                        "table_calibration_required",
                        reset_clutch=True,
                    )
                if self._hand_visuals is not None:
                    self._hand_visuals.hide_all()
                self._sync_render()
                return
            if not self._table_frame_applied:
                table_to_quest = self.table_calibration.table_to_quest
                for state in self.states.values():
                    state.calibration.set_reference_frame(table_to_quest)
                    self._hold(
                        state,
                        "table_calibration_captured",
                        reset_clutch=True,
                    )
                self._table_frame_applied = True

        if self._control_executor is None:
            raise RuntimeError("dual YAM control executor is not running")
        futures = {
            side: self._control_executor.submit(
                self._update_arm,
                self.states[side],
                frame,
            )
            for side in ("left", "right")
        }
        # The hand retargeters use their own left/right workers. Running them
        # here overlaps hand control with both independent arm IK workers.
        if self._sim_hands is not None:
            self._sim_hands.update(frame, enabled=True)
        for future in futures.values():
            future.result()
        self._update_hand_visuals(frame)
        self._sync_render()

    def _update_arm(self, state: _ArmState, frame: TeleopFrame) -> None:
        hand = self._tracked_hand(frame, state.side)
        if hand is None or hand.wrist is None:
            self._tracking_missing(
                state,
                frame.timestamp,
                reason="tracking_lost",
            )
            return
        wrist = hand.wrist.matrix
        if not np.isfinite(wrist).all():
            self._tracking_missing(
                state,
                frame.timestamp,
                reason="invalid_tracking",
            )
            return
        state.last_valid_tracking_at = frame.timestamp
        state.tracking_loss_elapsed = 0.0
        if not state.calibration.captured:
            if state.zero_capture_started_at is None:
                state.zero_capture_started_at = frame.timestamp
            elapsed = max(0.0, frame.timestamp - state.zero_capture_started_at)
            state.zero_capture_remaining = max(
                0.0, self.config.zero_capture_delay - elapsed
            )
            state.quest_target = state.tcp_pose.copy()
            if state.zero_capture_remaining > 0.0:
                self._hold(
                    state,
                    "zero_pose_countdown",
                    reset_clutch=False,
                )
                return
            state.calibration.capture(wrist, state.tcp_pose)
            state.zero_capture_started_at = None
            self._hold(state, "clutch_captured", reset_clutch=False)
            return
        try:
            target_world = state.calibration.target(wrist)
        except (TypeError, ValueError, np.linalg.LinAlgError) as error:
            state.last_ik_detail = str(error)
            self._hold(state, "invalid_target", reset_clutch=False)
            return
        state.quest_target = target_world.copy()
        position = target_world[:3, 3]
        if (
            not np.isfinite(target_world).all()
            or np.any(position < self.config.workspace_min)
            or np.any(position > self.config.workspace_max)
        ):
            self._hold(state, "target_outside_workspace", reset_clutch=False)
            return

        target_local = np.linalg.inv(state.mount) @ target_world
        state.ik_attempts += 1
        result = state.kinematics.ik(
            target_local,
            init_q=state.q_target,
            max_iters=self.config.ik_max_iters,
        )
        state.last_ik_detail = result.detail
        if (
            not result.success
            or not np.isfinite(result.q).all()
            or not state.kinematics.within_limits(result.q, tolerance=1e-6)
        ):
            self._hold(state, "ik_failed", reset_clutch=False)
            return

        filtered = state.q_target + self.config.low_pass_alpha * (
            result.q - state.q_target
        )
        delta = filtered - state.q_target
        limited_delta = np.clip(
            delta, -self.config.max_joint_step, self.config.max_joint_step
        )
        state.rate_limited = not np.allclose(delta, limited_delta, atol=1e-12)
        candidate = state.kinematics.clamp_to_limits(
            state.q_target + limited_delta
        )
        if not state.kinematics.within_limits(candidate):
            self._hold(state, "joint_limit_violation", reset_clutch=False)
            return

        state.q_target = candidate
        state.tcp_pose = state.mount @ state.kinematics.fk(candidate)
        state.position_error = float(
            np.linalg.norm(target_world[:3, 3] - state.tcp_pose[:3, 3])
        )
        state.orientation_error = rotation_error_radians(state.tcp_pose, target_world)
        state.ik_successes += 1
        state.hold_reason = ""

    def _update_hand_visuals(self, frame: TeleopFrame) -> None:
        if self._hand_visuals is None:
            return
        raw_by_side = frame.extras.get("raw_openxr_hand_landmarks", {})
        for side, state in self.states.items():
            blocked = state.hold_reason in HAND_BLOCKED_REASONS
            hand = self._tracked_hand(frame, side)
            if hand is None or hand.wrist is None or not state.calibration.captured:
                if (
                    state.hold_reason == "tracking_dropout"
                    and self._hand_visuals.visible[side]
                ):
                    continue
                self._hand_visuals.hide(side)
                continue
            wrist = hand.wrist.matrix
            try:
                hand_target = state.calibration.target(wrist)
            except (RuntimeError, TypeError, ValueError, np.linalg.LinAlgError):
                if self._hand_visuals.visible[side]:
                    self._hand_visuals.set_style(side, "blocked")
                continue
            raw = raw_by_side.get(side) if hasattr(raw_by_side, "get") else None
            if raw is not None:
                points = np.asarray(raw, dtype=np.float64)
                if points.shape != (25, 3) or not np.isfinite(points).all():
                    continue
                local_points = (wrist[:3, :3].T @ (points - wrist[:3, 3]).T).T
            else:
                local_points = np.asarray(hand.landmarks, dtype=np.float64)
            mapped_points = (state.calibration.axis_rotation @ local_points.T).T
            self._hand_visuals.set(
                side,
                hand_target,
                mapped_points,
                blocked=blocked,
            )

    def _sync_render(self) -> None:
        if self.render_model is None or self.render_data is None:
            return
        import mujoco

        for side, state in self.states.items():
            self.render_data.qpos[self._qpos_addresses[side]] = state.q_target
            mocap_id = self._target_mocap_ids[side]
            target = (
                state.quest_target if state.quest_target is not None else state.tcp_pose
            )
            self.render_data.mocap_pos[mocap_id] = target[:3, 3]
            self.render_data.mocap_quat[mocap_id] = (
                YamSimArmModule._rotation_quaternion(target[:3, :3])
            )
            if self._sim_hands is not None:
                self.render_data.qpos[self._hand_qpos_addresses[side]] = (
                    self._sim_hands.model_qpos(side)
                )
                hand_mocap_id = self._hand_mount_mocap_ids[side]
                self.render_data.mocap_pos[hand_mocap_id] = state.tcp_pose[:3, 3]
                self.render_data.mocap_quat[hand_mocap_id] = (
                    YamSimArmModule._rotation_quaternion(state.tcp_pose[:3, :3])
                )
        mujoco.mj_forward(self.render_model, self.render_data)
        if self._viewer is not None and self._viewer.is_running():
            # Do not reset camera here: mouse-controlled view changes persist.
            self._viewer.sync()

    def _state_telemetry(self, state: _ArmState) -> dict[str, Any]:
        success_rate = (
            state.ik_successes / state.ik_attempts if state.ik_attempts else 0.0
        )
        return {
            "mode": "hold" if state.hold_reason else "tracking",
            "hold_reason": state.hold_reason,
            "clutch_captured": state.calibration.captured,
            "zero_capture_delay_s": self.config.zero_capture_delay,
            "zero_capture_remaining_s": state.zero_capture_remaining,
            "tracking_loss_grace_s": self.config.tracking_loss_grace,
            "tracking_loss_elapsed_s": state.tracking_loss_elapsed,
            "q_target": state.q_target.tolist(),
            "tcp_pose": state.tcp_pose.tolist(),
            "quest_target": (
                state.quest_target.tolist() if state.quest_target is not None else None
            ),
            "ik_attempts": state.ik_attempts,
            "ik_successes": state.ik_successes,
            "ik_success_rate": success_rate,
            "ik_detail": state.last_ik_detail,
            "position_error_m": state.position_error,
            "orientation_error_rad": state.orientation_error,
            "rate_limited": state.rate_limited,
            "joint_limits": state.kinematics.joint_limits.tolist(),
        }

    def status(self) -> ModuleStatus:
        arms = {
            side: self._state_telemetry(state) for side, state in self.states.items()
        }
        detail = ", ".join(
            f"{side}:{state.hold_reason}"
            for side, state in self.states.items()
            if state.hold_reason
        )
        return ModuleStatus(
            name=self.name,
            ready=self._started,
            detail=detail,
            telemetry={
                "sequence": self._last_sequence,
                "arms": arms,
                "hands_visualized": (
                    dict(self._hand_visuals.visible)
                    if self._hand_visuals is not None
                    else {"left": False, "right": False}
                ),
                "hand_visual_style": (
                    dict(self._hand_visuals.style)
                    if self._hand_visuals is not None
                    else {"left": "hidden", "right": "hidden"}
                ),
                "camera": "ego_free",
                "window_platform": self._window_platform,
                "control_execution": "parallel",
                "inspire_hands": (
                    self._sim_hands.telemetry()
                    if self._sim_hands is not None
                    else {"enabled": False}
                ),
                "table_calibration": (
                    self.table_calibration.telemetry()
                    if self.table_calibration is not None
                    else {"enabled": False, "calibrated": False}
                ),
            },
        )

    def close(self) -> None:
        if self._sim_hands is not None:
            self._sim_hands.close()
            self._sim_hands = None
        if self._control_executor is not None:
            self._control_executor.shutdown(wait=True, cancel_futures=True)
            self._control_executor = None
        for state in self.states.values():
            state.calibration.reset()
        if self._viewer is not None:
            self._viewer.close()
            self._viewer = None
        self._hand_visuals = None
        self.render_data = None
        self.render_model = None
        self.states.clear()
        self._qpos_addresses.clear()
        self._target_mocap_ids.clear()
        self._hand_qpos_addresses.clear()
        self._hand_mount_mocap_ids.clear()
        self._hand_geom_ids.clear()
        self._window_platform = "none"
        self._table_frame_applied = False
        self._started = False
