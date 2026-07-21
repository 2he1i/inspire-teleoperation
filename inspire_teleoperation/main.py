#!/usr/bin/env python3
"""Quest hand tracking to six-DOF dexterous hands, without arm control.

This entry point owns only three data-path stages:
Quest hand landmarks -> dex-retargeting -> hand Modbus TCP commands.
It deliberately does not initialise cameras, robot motion, arm controllers,
or inverse kinematics, so it can later be embedded below a separate arm
teleoperation application.
"""

import argparse
import os
import sys
import time
from multiprocessing import Array, Lock, Value

import numpy as np
try:
    import logging_mp
except ModuleNotFoundError:
    # logging_mp is convenient in the full robot stack, but standard logging
    # is sufficient for this single-process entry point and for --help.
    import logging as logging_mp

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    logging_mp.basicConfig(level=logging_mp.INFO)
except RuntimeError:
    # logging_mp rejects reconfiguration when this module is imported by an
    # application that has already initialised Python logging.
    pass
logger_mp = logging_mp.getLogger(__name__)


class TeleopState:
    """Runtime state changed by validated web-console actions."""

    def __init__(self, start_immediately=False):
        self.running = True
        self.tracking_enabled = start_immediately

    def apply_action(self, action):
        if action == "run":
            self.tracking_enabled = True
            logger_mp.info("Hand tracking enabled.")
        elif action == "pause":
            self.tracking_enabled = False
            logger_mp.info("Hand tracking paused; retaining the last hand target.")
        elif action == "quit":
            self.tracking_enabled = False
            self.running = False
        else:
            raise ValueError(f"Unknown teleoperation action: {action!r}")


def _copy_landmarks(shared_array, landmarks, side):
    """Validate the 25x3 Quest landmark payload before sharing it with control."""
    data = np.asarray(landmarks, dtype=np.float64)
    if data.shape != (25, 3):
        raise ValueError(f"Quest {side} hand landmarks must have shape (25, 3), got {data.shape}.")
    if not np.isfinite(data).all():
        raise ValueError(f"Quest {side} hand landmarks contain NaN or infinity.")
    with shared_array.get_lock():
        shared_array[:] = data.ravel()


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Standalone Quest hand teleoperation for six-DOF dexterous hands."
    )
    parser.add_argument("--frequency", type=float, default=60.0, help="Quest landmark polling rate in Hz (default: 60).")
    parser.add_argument("--hand-frequency", type=float, default=100.0, help="hand command rate in Hz (default: 100).")
    parser.add_argument("--left-hand-host", help="Enable the left hand at this Modbus TCP address.")
    parser.add_argument(
        "--right-hand-host",
        default="192.168.11.210",
        help="Enable the right hand at this Modbus TCP address (default: 192.168.11.210).",
    )
    parser.add_argument("--modbus-port", type=int, default=6000, help="Modbus TCP port for both hands (default: 6000).")
    parser.add_argument("--left-device-id", type=int, default=1, help="Left-hand Modbus device ID (default: 1).")
    parser.add_argument("--right-device-id", type=int, default=1, help="Right-hand Modbus device ID (default: 1).")
    parser.add_argument("--modbus-timeout", type=float, default=3.0, help="Modbus request timeout in seconds (default: 3).")
    parser.add_argument("--target-speed", type=int, default=300, help="Joint speed used in fixed mode, 0-1000 (default: 300).")
    parser.add_argument(
        "--speed-mode",
        choices=["adaptive_v2", "adaptive_v1", "adaptive", "fixed"],
        default="adaptive_v2",
        help=(
            "Joint speed strategy; adaptive is an alias for adaptive_v2 "
            "(default: adaptive_v2)."
        ),
    )
    parser.add_argument("--display-mode", choices=["immersive", "ego", "pass-through"], default="pass-through",
                        help="Quest display mode. No image stream is opened by this module (default: pass-through).")
    parser.add_argument("--image-width", type=int, default=640, help="Placeholder XR image width required by televuer (default: 640).")
    parser.add_argument("--image-height", type=int, default=480, help="Placeholder XR image height required by televuer (default: 480).")
    parser.add_argument("--binocular", action="store_true", help="Configure the Quest viewer for binocular images if a display stream is added later.")
    parser.add_argument(
        "--hide-hand-markers",
        action="store_true",
        help="Hide Quest hand joint/skeleton markers (shown by default).",
    )
    parser.add_argument("--start", action="store_true", help="Enable tracking immediately after the web setup is confirmed.")
    parser.add_argument("--open-on-exit", action="store_true", help="Command all joints to 1000 (open) after a clean exit.")
    parser.add_argument("--web-host", default="127.0.0.1", help="Web console listen address (default: 127.0.0.1).")
    parser.add_argument("--web-port", type=int, default=8080, help="Web console port (default: 8080).")
    parser.add_argument(
        "--browser",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Open the web console in the default browser (default: enabled).",
    )
    parser.add_argument(
        "--language",
        choices=["auto", "zh", "en"],
        default="auto",
        help="Web console language: auto, zh, or en (default: auto).",
    )
    args = parser.parse_args(argv)
    if not args.left_hand_host and not args.right_hand_host:
        parser.error("At least one hand host must be configured.")
    if args.frequency <= 0 or args.hand_frequency <= 0:
        parser.error("--frequency and --hand-frequency must be positive.")
    if args.image_width <= 0 or args.image_height <= 0:
        parser.error("--image-width and --image-height must be positive.")
    if not 1 <= args.modbus_port <= 65535:
        parser.error("--modbus-port must be in the range 1-65535.")
    if not 1 <= args.left_device_id <= 254 or not 1 <= args.right_device_id <= 254:
        parser.error("--left-device-id and --right-device-id must be in the range 1-254.")
    if args.modbus_timeout <= 0:
        parser.error("--modbus-timeout must be positive.")
    if not 0 <= args.target_speed <= 1000:
        parser.error("--target-speed must be in the range 0-1000.")
    if not 1 <= args.web_port <= 65535:
        parser.error("--web-port must be in the range 1-65535.")
    return args


def _apply_web_config(args, config):
    """Apply the validated connection form to the command-line namespace."""

    args.left_hand_host = config["left_host"] if config["left_enabled"] else None
    args.right_hand_host = config["right_host"] if config["right_enabled"] else None
    for name in (
        "left_device_id", "right_device_id", "modbus_port", "modbus_timeout",
        "target_speed", "speed_mode", "frequency", "hand_frequency", "start",
        "open_on_exit", "hide_hand_markers",
    ):
        setattr(args, name, config[name])


def _read_shared(values):
    lock = getattr(values, "get_lock", lambda: None)()
    if lock is None:
        return tuple(values[:])
    with lock:
        return tuple(values[:])


def main():
    args = parse_args()
    from inspire_teleoperation.web_ui import HandTeleoperationWebUI, TeleopSnapshot

    state = TeleopState()
    tv_wrapper = None
    hand_controller = None
    web_ui = HandTeleoperationWebUI(args)
    session_started_at = 0.0
    loop_hz = 0.0
    loop_sample_started_at = 0.0
    loop_sample_count = 0
    xr_motion_data_ready = Value("b", False, lock=True)
    xr_motion_data_sequence = Value("L", 0, lock=True)

    # Each hand uses the Quest/OpenXR 25-landmark x 3-coordinate layout.
    left_hand_pos = Array("d", 75, lock=True)
    right_hand_pos = Array("d", 75, lock=True)
    dual_hand_data_lock = Lock()
    dual_hand_state = Array("d", 12, lock=False)
    dual_hand_action = Array("d", 12, lock=False)

    try:
        web_ui.start(open_browser=args.browser)
        logger_mp.info("Hand teleoperation web console: %s", web_ui.url)
        logger_mp.info("Waiting for connection settings and safety confirmation.")
        config = web_ui.wait_for_setup()
        if config is None:
            return
        _apply_web_config(args, config)
        state.tracking_enabled = args.start
        web_ui.set_phase("connecting")

        # Import hardware integrations only after the browser setup form is
        # confirmed, keeping --help and the setup page hardware-independent.
        from televuer import TeleVuerWrapper
        from inspire_teleoperation.hand_controller import HandController

        tv_wrapper = TeleVuerWrapper(
            use_hand_tracking=True,
            binocular=args.binocular,
            img_shape=(args.image_height, args.image_width, 3),
            display_mode=args.display_mode,
            zmq=False,
            webrtc=False,
            arm_reference_mode="head_yaw",
            show_hand_markers=not args.hide_hand_markers,
        )
        hand_controller = HandController(
            left_hand_pos,
            right_hand_pos,
            dual_hand_data_lock,
            dual_hand_state,
            dual_hand_action,
            left_host=args.left_hand_host,
            right_host=args.right_hand_host,
            port=args.modbus_port,
            left_device_id=args.left_device_id,
            right_device_id=args.right_device_id,
            timeout=args.modbus_timeout,
            target_speed=args.target_speed,
            speed_mode=args.speed_mode,
            fps=args.hand_frequency,
            xr_motion_data_ready_in=xr_motion_data_ready,
            xr_motion_data_sequence_in=xr_motion_data_sequence,
        )

        logger_mp.info("Hand teleoperation is ready.")
        logger_mp.info("Use the web console to run, pause, change speed mode, or quit.")
        enabled_sides = [
            side
            for side, host in (("left", args.left_hand_host), ("right", args.right_hand_host))
            if host
        ]
        logger_mp.info("Enabled hand(s): %s.", ", ".join(enabled_sides))
        logger_mp.info("Keep clear of enabled hands while commands are enabled.")
        web_ui.set_phase("live")

        session_started_at = time.monotonic()
        loop_sample_started_at = session_started_at

        while state.running:
            cycle_start = time.monotonic()
            action = web_ui.poll_action()
            if action == "run":
                state.apply_action("run")
            elif action == "pause":
                state.apply_action("pause")
            elif action == "quit":
                state.apply_action("quit")
                continue
            elif action == "speed_mode":
                mode = hand_controller.toggle_speed_mode()
                logger_mp.info("Switched to %s joint speed mode.", mode)
            hand_controller.raise_if_failed()
            tele_data = tv_wrapper.get_tele_data()
            motion_ready = bool(getattr(tele_data, "motion_data_ready", False))

            # Tell the controller not to consume the shared landmarks while a
            # complete left/right frame is being copied.
            with xr_motion_data_ready.get_lock():
                xr_motion_data_ready.value = False

            if state.tracking_enabled and motion_ready:
                try:
                    with dual_hand_data_lock:
                        if args.left_hand_host:
                            _copy_landmarks(left_hand_pos, tele_data.left_hand_pos, "left")
                        if args.right_hand_host:
                            _copy_landmarks(right_hand_pos, tele_data.right_hand_pos, "right")
                    with xr_motion_data_sequence.get_lock():
                        xr_motion_data_sequence.value += 1
                except (AttributeError, TypeError, ValueError) as error:
                    # A transient malformed XR frame must not become a hand
                    # command or kill the control session.
                    motion_ready = False
                    logger_mp.warning("Ignoring invalid Quest hand frame: %s", error)

            # The controller only retargets fresh data when this flag is true.
            # On pause, tracking loss, or invalid data it retains the last target.
            with xr_motion_data_ready.get_lock():
                xr_motion_data_ready.value = state.tracking_enabled and motion_ready

            loop_sample_count += 1
            sample_elapsed = time.monotonic() - loop_sample_started_at
            if sample_elapsed >= 0.5:
                loop_hz = loop_sample_count / sample_elapsed
                loop_sample_started_at = time.monotonic()
                loop_sample_count = 0

            action_values = _read_shared(dual_hand_action)
            web_ui.publish(
                TeleopSnapshot(
                    tracking_enabled=state.tracking_enabled,
                    motion_data_ready=motion_ready,
                    loop_hz=loop_hz,
                    elapsed_seconds=time.monotonic() - session_started_at,
                    left_enabled=bool(args.left_hand_host),
                    right_enabled=bool(args.right_hand_host),
                    left_state=_read_shared(hand_controller.left_hand_state_array),
                    right_state=_read_shared(hand_controller.right_hand_state_array),
                    left_target=action_values[:6],
                    right_target=action_values[6:],
                    speed_mode=hand_controller.speed_mode,
                    left_speed=_read_shared(hand_controller.left_hand_speed_array),
                    right_speed=_read_shared(hand_controller.right_hand_speed_array),
                )
            )

            sleep_time = (1.0 / args.frequency) - (time.monotonic() - cycle_start)
            if sleep_time > 0:
                time.sleep(sleep_time)
    except KeyboardInterrupt:
        logger_mp.info("Keyboard interrupt received; exiting hand teleoperation.")
    except Exception as error:
        web_ui.set_phase("error", str(error))
        logger_mp.exception("Hand teleoperation stopped due to an error.")
        raise
    finally:
        web_ui.set_phase("stopping")
        with xr_motion_data_ready.get_lock():
            xr_motion_data_ready.value = False
        try:
            if hand_controller is not None:
                hand_controller.stop(open_hand=args.open_on_exit)
            if tv_wrapper is not None:
                tv_wrapper.close()
        finally:
            web_ui.set_phase("stopped")
            web_ui.stop()


if __name__ == "__main__":
    main()
