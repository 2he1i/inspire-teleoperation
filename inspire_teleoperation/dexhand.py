"""六自由度灵巧手的 Modbus TCP 通信 API。

提供原始寄存器读写以及六自由度速度、位置、角度、力和状态寄存器的便捷接口；
不包含触觉、运动学、关节坐标或角度转换。
"""

from __future__ import annotations

from dataclasses import dataclass
import sys
from threading import RLock
import time
from types import TracebackType
from typing import Protocol, Sequence, TextIO

import numpy as np
from numpy.typing import NDArray
from pymodbus.client import ModbusTcpClient


DEFAULT_HOST = "192.168.11.210"
DEFAULT_PORT = 6000
DEFAULT_DEVICE_ID = 1
DEFAULT_TIMEOUT_SECONDS = 3.0
DOF_COUNT = 6
MAX_MODBUS_READ_REGISTERS = 125
MAX_MODBUS_WRITE_REGISTERS = 123

DOF_NAMES = (
    "finger4",
    "finger3",
    "finger2",
    "finger1",
    "finger0_bend",
    "finger0_rotate",
)

JointArray = NDArray[np.signedinteger | np.unsignedinteger]


class ModbusClient(Protocol):
    """本客户端所需的 PyModbus 客户端最小接口。"""

    connected: bool

    def connect(self) -> bool: ...

    def close(self) -> None: ...

    def read_holding_registers(
        self, address: int, *, count: int, device_id: int
    ) -> object: ...

    def write_registers(
        self, address: int, values: list[int], *, device_id: int
    ) -> object: ...


@dataclass(frozen=True, slots=True)
class RegisterSpec:
    """连续六自由度寄存器块的原始范围定义。"""

    address: int
    minimum: int
    maximum: int
    writable: bool = False
    signed: bool = False
    allow_no_change: bool = False


REGISTER_SPECS: dict[str, RegisterSpec] = {
    "default_speeds": RegisterSpec(1032, 0, 1000, writable=True),
    "default_force_limits": RegisterSpec(1044, 0, 3000, writable=True),
    "target_positions": RegisterSpec(
        1474, 0, 2000, writable=True, allow_no_change=True
    ),
    "target_angles": RegisterSpec(1486, 0, 1000, writable=True, allow_no_change=True),
    "target_force_limits": RegisterSpec(1498, 0, 3000, writable=True),
    "target_speeds": RegisterSpec(1522, 0, 1000, writable=True),
    "actual_positions": RegisterSpec(1534, 0, 2000),
    "actual_angles": RegisterSpec(1546, 0, 1000),
    "actual_forces": RegisterSpec(1582, -4000, 4000, signed=True),
    "currents": RegisterSpec(1594, 0, 2000),
}


class Dexhand:
    """灵巧手的 Modbus TCP 客户端。

    构造函数不会连接设备。除原始寄存器 API 外，六自由度便捷方法只做寄存器
    地址选择、范围校验与 16 位有符号值/``-1`` 保持不动标记的协议转换。
    """

    def __init__(
        self,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        device_id: int = DEFAULT_DEVICE_ID,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        *,
        client: ModbusClient | None = None,
    ) -> None:
        if not host:
            raise ValueError("host 不能为空")
        if not 1 <= port <= 65535:
            raise ValueError("port 必须在 1～65535 范围内")
        if not 1 <= device_id <= 254:
            raise ValueError("device_id 必须在 1～254 范围内")
        if timeout <= 0:
            raise ValueError("timeout 必须大于 0")

        self.host = host
        self.port = port
        self.device_id = device_id
        self.timeout = timeout
        self._client: ModbusClient = client or ModbusTcpClient(
            host=host, port=port, timeout=timeout
        )
        self._connected = client is not None
        self._lock = RLock()

    @property
    def is_connected(self) -> bool:
        """当前客户端是否可用于通信。"""

        client_connected = getattr(self._client, "connected", None)
        return self._connected if client_connected is None else self._connected and bool(
            client_connected
        )

    def connect(self) -> None:
        """建立到灵巧手的 Modbus TCP 连接。"""

        with self._lock:
            if self.is_connected:
                return
            if not self._client.connect():
                self._client.close()
                raise ConnectionError(
                    f"无法连接 Modbus TCP 设备：{self.host}:{self.port}"
                )
            self._connected = True

    def close(self) -> None:
        """关闭连接；重复调用安全。"""

        with self._lock:
            self._client.close()
            self._connected = False

    def __enter__(self) -> Dexhand:
        self.connect()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

    def read_registers(self, address: int, count: int) -> NDArray[np.uint16]:
        """读取 1～125 个连续保持寄存器，返回未解释的 ``uint16`` word。"""

        self._validate_address(address)
        if not 1 <= count <= MAX_MODBUS_READ_REGISTERS:
            raise ValueError("count 必须在 1～125 范围内")
        self._require_connected()

        with self._lock:
            response = self._client.read_holding_registers(
                address, count=count, device_id=self.device_id
            )
        self._ensure_success(response, f"读寄存器 {address}")
        registers = getattr(response, "registers", None)
        if not isinstance(registers, Sequence) or isinstance(registers, (str, bytes)):
            raise RuntimeError(f"读寄存器 {address}失败：响应中没有寄存器数据")
        if len(registers) != count:
            raise RuntimeError(
                f"读寄存器 {address}失败：期望 {count} 个寄存器，实际收到 {len(registers)} 个"
            )
        return self._as_word_array(registers, name="响应寄存器").astype(
            np.uint16, copy=False
        )

    def write_registers(self, address: int, values: Sequence[int]) -> None:
        """写入 1～123 个连续保持寄存器，不解释地址或数据含义。"""

        self._validate_address(address)
        if not 1 <= len(values) <= MAX_MODBUS_WRITE_REGISTERS:
            raise ValueError("values 长度必须在 1～123 范围内")
        words = self._as_word_array(values, name="values")
        self._require_connected()

        with self._lock:
            response = self._client.write_registers(
                address, [int(value) for value in words], device_id=self.device_id
            )
        self._ensure_success(response, f"写寄存器 {address}")

    def read_default_speeds(self) -> NDArray[np.uint16]:
        """读取六自由度上电默认速度（0～1000）。"""

        return self._read_joint_block("default_speeds")

    def write_default_speeds(self, values: Sequence[int]) -> None:
        """写入六自由度上电默认速度（每项 0～1000）。"""

        self._write_joint_block("default_speeds", values)

    def read_default_force_limits(self) -> NDArray[np.uint16]:
        """读取六自由度上电默认力阈值。"""

        return self._read_joint_block("default_force_limits")

    def write_default_force_limits(self, values: Sequence[int]) -> None:
        """写入六自由度上电默认力阈值（每项 0～3000）。"""

        self._write_joint_block("default_force_limits", values)

    def read_target_positions(self) -> NDArray[np.int16]:
        """读取六自由度目标位置。"""

        return self._read_joint_block("target_positions")

    def write_target_positions(self, values: Sequence[int]) -> None:
        """写入六自由度目标位置（0～2000；``-1`` 表示保持不动）。"""

        self._write_joint_block("target_positions", values)

    def read_target_angles(self) -> NDArray[np.int16]:
        """读取六自由度目标角度标度值。"""

        return self._read_joint_block("target_angles")

    def write_target_angles(self, values: Sequence[int]) -> None:
        """写入六自由度目标角度标度值（0～1000；``-1`` 表示保持不动）。"""

        self._write_joint_block("target_angles", values)

    def read_target_force_limits(self) -> NDArray[np.uint16]:
        """读取六自由度目标力阈值。"""

        return self._read_joint_block("target_force_limits")

    def write_target_force_limits(self, values: Sequence[int]) -> None:
        """写入六自由度目标力阈值（每项 0～3000）。"""

        self._write_joint_block("target_force_limits", values)

    def read_target_speeds(self) -> NDArray[np.uint16]:
        """读取六自由度目标速度。"""

        return self._read_joint_block("target_speeds")

    def write_target_speeds(self, values: Sequence[int]) -> None:
        """写入六自由度目标速度（每项 0～1000）。"""

        self._write_joint_block("target_speeds", values)

    def read_actual_positions(self) -> NDArray[np.uint16]:
        """读取六自由度实际位置。"""

        return self._read_joint_block("actual_positions")

    def read_actual_angles(self) -> NDArray[np.uint16]:
        """读取六自由度实际角度标度值。"""

        return self._read_joint_block("actual_angles")

    def wait_for_motion_complete(
        self,
        *,
        poll_interval: float = 0.02,
        stable_samples: int = 5,
        timeout: float | None = 30.0,
        output: TextIO | None = None,
    ) -> NDArray[np.uint16]:
        """等待实际角度连续稳定后返回最后一次六自由度读数。"""

        if poll_interval <= 0:
            raise ValueError("poll_interval 必须大于 0")
        if stable_samples < 2:
            raise ValueError("stable_samples 必须至少为 2")
        if timeout is not None and timeout <= 0:
            raise ValueError("timeout 必须大于 0 或为 None")

        stream = sys.stdout if output is None else output
        deadline = None if timeout is None else time.monotonic() + timeout
        previous: NDArray[np.uint16] | None = None
        stable_count = 0
        while True:
            angles = self.read_actual_angles()
            if previous is not None and np.array_equal(angles, previous):
                stable_count += 1
            else:
                stable_count = 1
            if stable_count >= stable_samples:
                return angles
            previous = angles
            if deadline is not None and time.monotonic() >= deadline:
                raise TimeoutError("等待动作完成超时，实际角度仍在变化")
            if output is not None:
                print("当前关节角度：" + " ".join(map(str, angles)), file=stream)
            time.sleep(poll_interval)

    def read_actual_forces(self) -> NDArray[np.int16]:
        """读取六自由度实际作用力（有符号 16 位值）。"""

        return self._read_joint_block("actual_forces")

    def read_currents(self) -> NDArray[np.uint16]:
        """读取六自由度电流。"""

        return self._read_joint_block("currents")

    def read_error_codes(self) -> NDArray[np.uint8]:
        """读取六自由度错误码。"""

        return self._read_byte_block(1606, DOF_COUNT)

    def read_status_codes(self) -> NDArray[np.uint8]:
        """读取六自由度状态码。"""

        return self._read_byte_block(1612, DOF_COUNT)

    def read_temperatures(self) -> NDArray[np.uint8]:
        """读取六自由度温度。"""

        return self._read_byte_block(1618, DOF_COUNT)

    def clear_errors(self) -> None:
        """清除设备允许清除的错误。"""

        self.write_registers(1004, [1])

    def save_parameters(self) -> None:
        """将可保存参数写入设备 Flash。"""

        self.write_registers(1005, [1])

    def restore_factory_defaults(self) -> None:
        """请求恢复设备出厂参数。"""

        self.write_registers(1006, [1])

    def calibrate_force_sensors(self) -> None:
        """启动六自由度力传感器校准。"""

        self.write_registers(1009, [1])

    def _read_joint_block(self, name: str) -> JointArray:
        spec = REGISTER_SPECS[name]
        raw = self.read_registers(spec.address, DOF_COUNT)
        if spec.signed:
            return raw.view(np.int16).copy()
        if spec.allow_no_change:
            decoded = raw.astype(np.int32)
            decoded[raw == 0xFFFF] = -1
            return decoded.astype(np.int16)
        return raw

    def _write_joint_block(self, name: str, values: Sequence[int]) -> None:
        spec = REGISTER_SPECS[name]
        if not spec.writable:
            raise ValueError(f"寄存器组 {name} 不可写")
        array = self._as_integer_array(values, name="values")
        if array.size != DOF_COUNT:
            raise ValueError(f"values 必须包含 {DOF_COUNT} 个元素，顺序为 {DOF_NAMES}")
        in_range = (array >= spec.minimum) & (array <= spec.maximum)
        if spec.allow_no_change:
            in_range |= array == -1
        if not np.all(in_range):
            allowed = f"{spec.minimum}～{spec.maximum}"
            if spec.allow_no_change:
                allowed += " 或 -1"
            raise ValueError(f"values 的每个元素必须为 {allowed}")
        self.write_registers(spec.address, [int(value) & 0xFFFF for value in array])

    def _read_byte_block(self, address: int, count: int) -> NDArray[np.uint8]:
        words = self.read_registers(address, (count + 1) // 2)
        result = np.empty(count, dtype=np.uint8)
        result[0::2] = words[: (count + 1) // 2] & 0xFF
        result[1::2] = (words[: count // 2] >> 8) & 0xFF
        return result

    def _require_connected(self) -> None:
        if not self.is_connected:
            raise ConnectionError("Modbus TCP 客户端尚未连接，请先调用 connect()")

    @staticmethod
    def _validate_address(address: int) -> None:
        if not isinstance(address, int) or isinstance(address, bool) or address < 0:
            raise ValueError("address 必须是非负整数")

    @staticmethod
    def _as_word_array(values: Sequence[int], *, name: str) -> NDArray[np.int64]:
        array = Dexhand._as_integer_array(values, name=name)
        if np.any((array < 0) | (array > 0xFFFF)):
            raise ValueError(f"{name} 的元素必须在 0～65535 范围内")
        return array

    @staticmethod
    def _as_integer_array(values: Sequence[int], *, name: str) -> NDArray[np.int64]:
        array = np.asarray(values)
        if array.ndim != 1:
            raise ValueError(f"{name} 必须是一维整数序列")
        if not np.issubdtype(array.dtype, np.integer):
            raise TypeError(f"{name} 的元素必须全部为整数")
        return array.astype(np.int64, copy=False)

    @staticmethod
    def _ensure_success(response: object, operation: str) -> None:
        is_error = getattr(response, "isError", None)
        if response is None or not callable(is_error) or is_error():
            raise RuntimeError(f"{operation}失败：{response}")


__all__ = [
    "DEFAULT_DEVICE_ID",
    "DEFAULT_HOST",
    "DEFAULT_PORT",
    "DEFAULT_TIMEOUT_SECONDS",
    "DOF_NAMES",
    "Dexhand",
    "MAX_MODBUS_READ_REGISTERS",
    "MAX_MODBUS_WRITE_REGISTERS",
    "REGISTER_SPECS",
]
