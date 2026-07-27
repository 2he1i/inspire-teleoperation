"""Six-axis YAM Pro forward and differential inverse kinematics."""

from __future__ import annotations

from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Any, Sequence

import numpy as np
from numpy.typing import NDArray


FloatArray = NDArray[np.float64]
YAM_JOINT_NAMES = tuple(f"joint{index}" for index in range(1, 7))
YAM_TCP_SITE = "inspire_tcp"


def default_yam_model_path() -> Path:
    """Return the packaged, hardware-free YAM Pro MuJoCo model."""

    return Path(str(files("inspire_teleoperation").joinpath(
        "assets", "yam_pro", "yam_pro_inspire.xml"
    )))


def rotation_error_radians(actual: Any, target: Any) -> float:
    relative = np.asarray(actual)[:3, :3].T @ np.asarray(target)[:3, :3]
    cosine = float(np.clip((np.trace(relative) - 1.0) * 0.5, -1.0, 1.0))
    return float(np.arccos(cosine))


@dataclass(frozen=True, slots=True)
class IKResult:
    success: bool
    q: FloatArray
    position_error: float
    orientation_error: float
    iterations: int
    detail: str = ""


class YamKinematics:
    """A small simulation-only adapter around MuJoCo and mink.

    The algorithm intentionally mirrors ``i2rt.robots.kinematics.Kinematics``
    while avoiding an import of i2rt's CAN/motor dependency tree.
    """

    joint_names = YAM_JOINT_NAMES
    site_name = YAM_TCP_SITE

    def __init__(
        self,
        xml_path: str | Path | None = None,
        *,
        solver: str = "quadprog",
    ) -> None:
        import mink
        import mujoco

        self.xml_path = Path(xml_path) if xml_path is not None else default_yam_model_path()
        if not self.xml_path.is_file():
            raise FileNotFoundError(f"YAM Pro model does not exist: {self.xml_path}")
        self.model = mujoco.MjModel.from_xml_path(str(self.xml_path))
        self._mink = mink
        self._mujoco = mujoco
        self.solver = solver
        self._validate_model()
        self.configuration = mink.Configuration(self.model)
        self._limits = [mink.ConfigurationLimit(self.model)]

        joint_ids = np.array(
            [mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, name)
             for name in self.joint_names],
            dtype=np.int32,
        )
        self._qpos_addresses = self.model.jnt_qposadr[joint_ids].copy()
        self.joint_limits = self.model.jnt_range[joint_ids].astype(np.float64).copy()
        self.neutral_q = np.mean(self.joint_limits, axis=1)
        self.configuration.update(self.neutral_q)

    def _validate_model(self) -> None:
        mujoco = self._mujoco
        if self.model.nq != 6 or self.model.nv != 6:
            raise ValueError(
                f"YAM simulation model must contain exactly six DoF, got "
                f"nq={self.model.nq}, nv={self.model.nv}"
            )
        actual = tuple(
            mujoco.mj_id2name(self.model, mujoco.mjtObj.mjOBJ_JOINT, index)
            for index in range(self.model.njnt)
        )
        if actual != self.joint_names:
            raise ValueError(
                f"YAM joint names must be {self.joint_names}, got {actual}"
            )
        site_id = mujoco.mj_name2id(
            self.model, mujoco.mjtObj.mjOBJ_SITE, self.site_name
        )
        if site_id < 0:
            raise ValueError(f"YAM model is missing TCP site {self.site_name!r}")

    @staticmethod
    def _q(value: Any, *, name: str) -> FloatArray:
        q = np.asarray(value, dtype=np.float64)
        if q.shape != (6,) or not np.isfinite(q).all():
            raise ValueError(f"{name} must contain six finite joint angles")
        return q.copy()

    @staticmethod
    def _pose(value: Any) -> FloatArray:
        pose = np.asarray(value, dtype=np.float64)
        if pose.shape != (4, 4) or not np.isfinite(pose).all():
            raise ValueError("target_pose must be a finite 4x4 transform")
        if not np.allclose(pose[3], (0.0, 0.0, 0.0, 1.0), atol=1e-6):
            raise ValueError("target_pose must be homogeneous")
        rotation = pose[:3, :3]
        if (
            not np.allclose(rotation.T @ rotation, np.eye(3), atol=1e-4)
            or not np.isclose(np.linalg.det(rotation), 1.0, atol=1e-4)
        ):
            raise ValueError("target_pose rotation must be orthonormal")
        return pose.copy()

    def within_limits(self, q: Any, *, tolerance: float = 1e-9) -> bool:
        joints = self._q(q, name="q")
        return bool(
            np.all(joints >= self.joint_limits[:, 0] - tolerance)
            and np.all(joints <= self.joint_limits[:, 1] + tolerance)
        )

    def clamp_to_limits(self, q: Any) -> FloatArray:
        joints = self._q(q, name="q")
        return np.clip(joints, self.joint_limits[:, 0], self.joint_limits[:, 1])

    def fk(self, q: Any) -> FloatArray:
        joints = self._q(q, name="q")
        self.configuration.update(joints)
        return self.configuration.get_transform_frame_to_world(
            self.site_name, "site"
        ).as_matrix().copy()

    def ik(
        self,
        target_pose: Any,
        *,
        init_q: Any | None = None,
        dt: float = 0.02,
        position_threshold: float = 1e-3,
        orientation_threshold: float = np.deg2rad(1.0),
        damping: float = 1e-4,
        max_iters: int = 35,
        position_cost: float = 1.0,
        orientation_cost: float = 0.35,
    ) -> IKResult:
        target = self._pose(target_pose)
        if max_iters <= 0:
            raise ValueError("max_iters must be positive")
        if dt <= 0.0:
            raise ValueError("dt must be positive")
        initial = self.neutral_q if init_q is None else self._q(init_q, name="init_q")
        if not self.within_limits(initial):
            return IKResult(
                False,
                initial,
                float("inf"),
                float("inf"),
                0,
                "initial joint position is outside model limits",
            )
        self.configuration.update(initial)
        task = self._mink.FrameTask(
            frame_name=self.site_name,
            frame_type="site",
            position_cost=position_cost,
            orientation_cost=orientation_cost,
            lm_damping=1.0,
        )
        task.set_target(self._mink.SE3.from_matrix(target))

        last_position_error = float("inf")
        last_orientation_error = float("inf")
        for iteration in range(1, max_iters + 1):
            try:
                velocity = self._mink.solve_ik(
                    self.configuration,
                    [task],
                    dt,
                    self.solver,
                    damping=damping,
                    limits=self._limits,
                )
            except Exception as error:
                return IKResult(
                    False,
                    initial.copy(),
                    last_position_error,
                    last_orientation_error,
                    iteration - 1,
                    f"IK solver error: {error}",
                )
            if not np.isfinite(velocity).all():
                return IKResult(
                    False,
                    initial.copy(),
                    last_position_error,
                    last_orientation_error,
                    iteration,
                    "IK solver produced a non-finite velocity",
                )
            self.configuration.integrate_inplace(velocity, dt)
            candidate = self.configuration.q.copy()
            actual = self.fk(candidate)
            last_position_error = float(
                np.linalg.norm(target[:3, 3] - actual[:3, 3])
            )
            last_orientation_error = rotation_error_radians(actual, target)
            if (
                last_position_error <= position_threshold
                and last_orientation_error <= orientation_threshold
                and self.within_limits(candidate, tolerance=1e-6)
            ):
                return IKResult(
                    True,
                    candidate,
                    last_position_error,
                    last_orientation_error,
                    iteration,
                )

        return IKResult(
            False,
            initial.copy(),
            last_position_error,
            last_orientation_error,
            max_iters,
            "IK did not converge within the online iteration budget",
        )

    def joint_index(self, name: str) -> int:
        try:
            return self.joint_names.index(name)
        except ValueError as error:
            raise KeyError(name) from error

    def validate_joint_names(self, names: Sequence[str]) -> None:
        if tuple(names) != self.joint_names:
            raise ValueError(f"expected joint order {self.joint_names}, got {tuple(names)}")
