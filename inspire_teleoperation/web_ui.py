"""Local web control surface for standalone hand teleoperation."""

from __future__ import annotations

import json
import logging
import threading
import webbrowser
from collections import deque
from dataclasses import asdict, dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class TeleopSnapshot:
    """Values published to the live web dashboard."""

    tracking_enabled: bool
    motion_data_ready: bool
    loop_hz: float
    elapsed_seconds: float
    left_enabled: bool
    right_enabled: bool
    left_state: tuple[float, ...]
    right_state: tuple[float, ...]
    left_target: tuple[float, ...]
    right_target: tuple[float, ...]
    speed_mode: str = "adaptive_v2"
    left_speed: tuple[float, ...] = ()
    right_speed: tuple[float, ...] = ()


class _WebLogHandler(logging.Handler):
    def __init__(self, web_ui: "HandTeleoperationWebUI") -> None:
        super().__init__()
        self._web_ui = web_ui

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self._web_ui.add_message(record.levelname, record.getMessage())
        except Exception:
            self.handleError(record)


class _WebServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, server_address, handler, web_ui: "HandTeleoperationWebUI") -> None:
        self.web_ui = web_ui
        super().__init__(server_address, handler)


class _RequestHandler(BaseHTTPRequestHandler):
    server: _WebServer

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        if self.path == "/api/state":
            self._json(HTTPStatus.OK, self.server.web_ui.state_payload())
            return
        asset = self.server.web_ui.asset(self.path)
        if asset is None:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        content, content_type = asset
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        try:
            payload = self._read_json()
            if self.path == "/api/setup":
                config = self.server.web_ui.submit_setup(payload)
                self._json(HTTPStatus.ACCEPTED, {"ok": True, "config": config})
            elif self.path == "/api/action":
                action = self.server.web_ui.submit_action(payload.get("action"))
                self._json(HTTPStatus.ACCEPTED, {"ok": True, "action": action})
            else:
                self.send_error(HTTPStatus.NOT_FOUND)
        except (TypeError, ValueError) as error:
            self._json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": str(error)})

    def _read_json(self) -> dict[str, Any]:
        content_type = self.headers.get_content_type()
        if content_type != "application/json":
            raise ValueError("Content-Type must be application/json")
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as error:
            raise ValueError("Invalid Content-Length") from error
        if length <= 0 or length > 32_768:
            raise ValueError("Request body must contain 1..32768 bytes")
        try:
            payload = json.loads(self.rfile.read(length))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError("Request body is not valid JSON") from error
        if not isinstance(payload, dict):
            raise TypeError("JSON body must be an object")
        return payload

    def _json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
        content = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, _format: str, *args: Any) -> None:
        """Keep high-frequency polling out of the application log."""


class HandTeleoperationWebUI:
    """Serve configuration, telemetry, and controls from a local web page."""

    _ASSETS = {
        "/": ("index.html", "text/html; charset=utf-8"),
        "/index.html": ("index.html", "text/html; charset=utf-8"),
        "/app.css": ("app.css", "text/css; charset=utf-8"),
        "/app.js": ("app.js", "text/javascript; charset=utf-8"),
    }
    _ACTIONS = {"run", "pause", "speed_mode", "quit"}

    def __init__(self, args) -> None:
        self.host = args.web_host
        self.port = args.web_port
        self.language = args.language
        self._assets_dir = Path(__file__).with_name("web")
        self._condition = threading.Condition()
        self._phase = "setup"
        self._detail = ""
        self._setup_config = self._config_from_args(args)
        self._pending_setup: dict[str, Any] | None = None
        self._actions: deque[str] = deque()
        self._messages: deque[dict[str, str]] = deque(maxlen=80)
        self._snapshot: TeleopSnapshot | None = None
        self._server: _WebServer | None = None
        self._thread: threading.Thread | None = None
        self._log_handler = _WebLogHandler(self)

    @staticmethod
    def _config_from_args(args) -> dict[str, Any]:
        speed_mode = "adaptive_v2" if args.speed_mode == "adaptive" else args.speed_mode
        return {
            "left_enabled": bool(args.left_hand_host),
            "left_host": args.left_hand_host or "192.168.11.211",
            "left_device_id": args.left_device_id,
            "right_enabled": bool(args.right_hand_host),
            "right_host": args.right_hand_host or "192.168.11.210",
            "right_device_id": args.right_device_id,
            "modbus_port": args.modbus_port,
            "modbus_timeout": args.modbus_timeout,
            "target_speed": args.target_speed,
            "speed_mode": speed_mode,
            "frequency": args.frequency,
            "hand_frequency": args.hand_frequency,
            "start": args.start,
            "open_on_exit": args.open_on_exit,
            "hide_hand_markers": args.hide_hand_markers,
        }

    @property
    def url(self) -> str:
        display_host = "127.0.0.1" if self.host in ("0.0.0.0", "::") else self.host
        return f"http://{display_host}:{self.port}"

    def start(self, open_browser: bool = True) -> None:
        self._server = _WebServer((self.host, self.port), _RequestHandler, self)
        self.port = self._server.server_port
        self._thread = threading.Thread(
            target=self._server.serve_forever,
            name="hand-teleoperation-web",
            daemon=True,
        )
        self._thread.start()
        logging.getLogger().addHandler(self._log_handler)
        if open_browser:
            threading.Thread(target=webbrowser.open, args=(self.url,), daemon=True).start()

    def stop(self) -> None:
        logging.getLogger().removeHandler(self._log_handler)
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
            self._server = None
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None

    def asset(self, path: str) -> tuple[bytes, str] | None:
        descriptor = self._ASSETS.get(path.split("?", 1)[0])
        if descriptor is None:
            return None
        filename, content_type = descriptor
        return (self._assets_dir.joinpath(filename).read_bytes(), content_type)

    @staticmethod
    def validate_setup(payload: dict[str, Any]) -> dict[str, Any]:
        required = {
            "left_enabled", "left_host", "left_device_id", "right_enabled",
            "right_host", "right_device_id", "modbus_port", "modbus_timeout",
            "target_speed", "speed_mode", "frequency", "hand_frequency",
            "start", "open_on_exit", "hide_hand_markers", "safety_confirmed",
        }
        missing = required.difference(payload)
        if missing:
            raise ValueError(f"Missing setup field: {sorted(missing)[0]}")

        def boolean(name: str) -> bool:
            value = payload[name]
            if not isinstance(value, bool):
                raise TypeError(f"{name} must be a boolean")
            return value

        def integer(name: str, minimum: int, maximum: int) -> int:
            value = payload[name]
            if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
                raise ValueError(f"{name} must be an integer in {minimum}..{maximum}")
            return value

        def number(name: str) -> float:
            value = payload[name]
            if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
                raise ValueError(f"{name} must be a positive number")
            return float(value)

        left_enabled = boolean("left_enabled")
        right_enabled = boolean("right_enabled")
        if not left_enabled and not right_enabled:
            raise ValueError("At least one hand must be enabled")
        if not boolean("safety_confirmed"):
            raise ValueError("Confirm that the hand workspace is clear before connecting")

        def host(name: str, enabled: bool) -> str:
            value = payload[name]
            if not isinstance(value, str):
                raise TypeError(f"{name} must be text")
            value = value.strip()
            if enabled and not value:
                raise ValueError(f"{name} cannot be empty when the hand is enabled")
            if len(value) > 253 or any(character.isspace() for character in value):
                raise ValueError(f"{name} is not a valid host name or address")
            return value

        speed_mode = payload["speed_mode"]
        if speed_mode == "adaptive":
            speed_mode = "adaptive_v2"
        if speed_mode not in ("adaptive_v2", "adaptive_v1", "fixed"):
            raise ValueError(
                "speed_mode must be adaptive_v2, adaptive_v1, adaptive, or fixed"
            )
        return {
            "left_enabled": left_enabled,
            "left_host": host("left_host", left_enabled),
            "left_device_id": integer("left_device_id", 1, 254),
            "right_enabled": right_enabled,
            "right_host": host("right_host", right_enabled),
            "right_device_id": integer("right_device_id", 1, 254),
            "modbus_port": integer("modbus_port", 1, 65535),
            "modbus_timeout": number("modbus_timeout"),
            "target_speed": integer("target_speed", 0, 1000),
            "speed_mode": speed_mode,
            "frequency": number("frequency"),
            "hand_frequency": number("hand_frequency"),
            "start": boolean("start"),
            "open_on_exit": boolean("open_on_exit"),
            "hide_hand_markers": boolean("hide_hand_markers"),
        }

    def submit_setup(self, payload: dict[str, Any]) -> dict[str, Any]:
        config = self.validate_setup(payload)
        with self._condition:
            if self._phase != "setup":
                raise ValueError("Setup has already been submitted")
            self._setup_config = config
            self._pending_setup = config
            self._phase = "connecting"
            self._condition.notify_all()
        return config

    def wait_for_setup(self) -> dict[str, Any] | None:
        with self._condition:
            while self._pending_setup is None and "quit" not in self._actions:
                self._condition.wait(timeout=0.5)
            if "quit" in self._actions:
                return None
            return dict(self._pending_setup or {})

    def submit_action(self, action: Any) -> str:
        if action not in self._ACTIONS:
            raise ValueError(f"Unknown action: {action!r}")
        with self._condition:
            if self._phase == "setup" and action != "quit":
                raise ValueError("Connect the hands before sending controls")
            self._actions.append(action)
            self._condition.notify_all()
        return action

    def poll_action(self) -> str | None:
        with self._condition:
            return self._actions.popleft() if self._actions else None

    def set_phase(self, phase: str, detail: str = "") -> None:
        with self._condition:
            self._phase = phase
            self._detail = detail

    def publish(self, snapshot: TeleopSnapshot) -> None:
        with self._condition:
            self._snapshot = snapshot

    def add_message(self, level: str, message: str) -> None:
        normalized = " ".join(str(message).split())
        if not normalized:
            return
        item = {"level": level.lower(), "message": normalized}
        with self._condition:
            if not self._messages or self._messages[-1] != item:
                self._messages.append(item)

    def state_payload(self) -> dict[str, Any]:
        with self._condition:
            return {
                "phase": self._phase,
                "detail": self._detail,
                "language": self.language,
                "config": dict(self._setup_config),
                "snapshot": asdict(self._snapshot) if self._snapshot is not None else None,
                "messages": list(self._messages),
            }
