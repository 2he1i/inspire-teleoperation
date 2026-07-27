"""Web-controllable lifecycle wrapper for the dual YAM simulation."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable

from .api import ModuleStatus, TeleopFrame
from .table_calibration import ThreePointTableCalibration
from .yam_dual_sim import DualYamSimArmModule
from .yam_sim_arm import YamSimArmConfig


NVIDIA_OFFLOAD_ENV = {
    "__NV_PRIME_RENDER_OFFLOAD": "1",
    "__GLX_VENDOR_LIBRARY_NAME": "nvidia",
    "__VK_LAYER_NV_optimus": "NVIDIA_only",
}


class YamSimulationLifecycleModule:
    """Keep a dynamically started simulation inside a fixed TeleopRuntime."""

    name = "yam_simulation"

    def __init__(
        self,
        *,
        auto_start: bool = False,
        viewer: bool = True,
        gpu: str = "nvidia",
        zero_capture_delay: float = 3.0,
        table_calibration_enabled: bool = True,
        simulate_hands: bool = True,
        config_path: str | Path | None = None,
        model_path: str | Path | None = None,
        module_factory: Callable[..., DualYamSimArmModule] = DualYamSimArmModule,
    ) -> None:
        self.auto_start = bool(auto_start)
        self.viewer = bool(viewer)
        if gpu not in {"nvidia", "system"}:
            raise ValueError("simulation GPU must be 'nvidia' or 'system'")
        self.gpu = gpu
        self.zero_capture_delay = self._validate_delay(zero_capture_delay)
        self.table_calibration_enabled = bool(table_calibration_enabled)
        self.simulate_hands = bool(simulate_hands)
        self.config_path = config_path
        self.model_path = model_path
        self._module_factory = module_factory
        self._simulation: DualYamSimArmModule | None = None
        self._ready = False
        self._lifecycle = "not_started"
        self._last_error = ""

    @staticmethod
    def _validate_delay(value: Any) -> float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError("zero-pose capture delay must be a number")
        delay = float(value)
        if not 0.0 <= delay <= 30.0:
            raise ValueError("zero-pose capture delay must be in the range 0..30 seconds")
        return delay

    @property
    def active(self) -> bool:
        return self._simulation is not None

    @property
    def simulation(self) -> DualYamSimArmModule | None:
        return self._simulation

    def start(self) -> None:
        if self._ready:
            return
        self._ready = True
        self._lifecycle = "stopped"
        if self.auto_start:
            try:
                self.start_simulation()
            except Exception:
                # Keep the Quest/real-hand Web session usable when only the
                # optional MuJoCo viewer fails to start.
                return

    def _configure_gpu(self) -> None:
        if self.gpu == "nvidia":
            os.environ.update(NVIDIA_OFFLOAD_ENV)

    def start_simulation(self, *, zero_capture_delay: float | None = None) -> None:
        if not self._ready:
            raise RuntimeError("simulation lifecycle module has not been started")
        if zero_capture_delay is not None:
            self.zero_capture_delay = self._validate_delay(zero_capture_delay)
        if self._simulation is not None:
            return

        self._lifecycle = "starting"
        self._last_error = ""
        simulation: DualYamSimArmModule | None = None
        try:
            self._configure_gpu()
            config = YamSimArmConfig.from_yaml(self.config_path)
            config.zero_capture_delay = self.zero_capture_delay
            simulation = self._module_factory(
                config=config,
                model_path=self.model_path,
                viewer=self.viewer,
                simulate_hands=self.simulate_hands,
                table_calibration=(
                    ThreePointTableCalibration()
                    if self.table_calibration_enabled
                    else None
                ),
            )
            simulation.start()
        except Exception as error:
            if simulation is not None:
                try:
                    simulation.close()
                except Exception:
                    pass
            self._lifecycle = "error"
            self._last_error = str(error)
            raise
        self._simulation = simulation
        self._lifecycle = "running"

    def stop_simulation(self) -> None:
        simulation = self._simulation
        if simulation is None:
            if self._lifecycle != "error":
                self._lifecycle = "stopped"
            return
        self._lifecycle = "stopping"
        self._simulation = None
        try:
            simulation.close()
        except Exception as error:
            self._lifecycle = "error"
            self._last_error = str(error)
            raise
        self._lifecycle = "stopped"
        self._last_error = ""

    def request_table_calibration(self) -> None:
        simulation = self._require_simulation()
        self.table_calibration_enabled = True
        simulation.set_table_calibration_enabled(True)

    def set_table_calibration_enabled(self, enabled: bool) -> None:
        self.table_calibration_enabled = bool(enabled)
        simulation = self._simulation
        if simulation is not None:
            simulation.set_table_calibration_enabled(
                self.table_calibration_enabled
            )

    def request_zero_capture(
        self,
        *,
        side: str | None = None,
        delay_seconds: float | None = None,
    ) -> None:
        simulation = self._require_simulation()
        table = simulation.table_calibration
        if table is not None and not table.calibrated:
            raise RuntimeError("complete table calibration before capturing wrist zero poses")
        if side not in {None, "left", "right"}:
            raise ValueError("zero-pose capture side must be left, right, or both")
        if delay_seconds is not None:
            self.zero_capture_delay = self._validate_delay(delay_seconds)
            simulation.config.zero_capture_delay = self.zero_capture_delay
        simulation.request_clutch(side)

    def _require_simulation(self) -> DualYamSimArmModule:
        if self._simulation is None:
            raise RuntimeError("YAM simulation is not running")
        return self._simulation

    def update(self, frame: TeleopFrame, *, enabled: bool) -> None:
        simulation = self._simulation
        if simulation is None:
            return
        try:
            simulation.update(frame, enabled=enabled)
        except Exception as error:
            self._last_error = str(error)
            self._lifecycle = "error"
            try:
                simulation.close()
            except Exception:
                pass
            finally:
                self._simulation = None

    def status(self) -> ModuleStatus:
        simulation = self._simulation
        inner_telemetry: dict[str, Any] = {}
        inner_detail = ""
        if simulation is not None:
            inner = simulation.status()
            inner_telemetry = dict(inner.telemetry)
            inner_detail = inner.detail
        telemetry = {
            **inner_telemetry,
            "active": simulation is not None,
            "lifecycle": self._lifecycle,
            "last_error": self._last_error,
            "viewer_enabled": self.viewer,
            "gpu": self.gpu,
            "simulate_hands": self.simulate_hands,
            "zero_capture_delay_s": self.zero_capture_delay,
            "table_calibration_enabled": self.table_calibration_enabled,
        }
        detail = self._last_error or inner_detail or self._lifecycle
        return ModuleStatus(
            name=self.name,
            ready=self._ready,
            detail=detail,
            telemetry=telemetry,
        )

    def close(self) -> None:
        try:
            self.stop_simulation()
        finally:
            self._ready = False
            self._lifecycle = "closed"
