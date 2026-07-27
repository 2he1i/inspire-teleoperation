# Inspire Teleoperation

Modular Quest teleoperation for a six-DOF Inspire dexterous hand and a
hardware-free dual YAM Pro + dual Inspire-hand simulation. The real YAM
hardware path is not part of this implementation.

Data flow:

```text
QuestSource -> TeleopFrame -> TeleopRuntime -> HandTeleopModule
                                       `----> DualYamSimArmModule
                                               |-> parallel YAM IK
                                               `-> production hand retargeting
                                                          `-> MuJoCo
```

`TeleopFrame` carries immutable left/right hand landmarks plus optional wrist
and head transforms. Each output module owns its controller, update rate,
connection lifecycle, and telemetry. Pausing still distributes frames with
`enabled=False`, allowing every module to implement its own safe hold behavior.

## Layout

- `inspire_teleoperation/api.py`: stable frame, source, module, and status contracts
- `inspire_teleoperation/runtime.py`: source/module lifecycle and frame fan-out
- `inspire_teleoperation/quest_source.py`: TeleVuer input adapter
- `inspire_teleoperation/hand_module.py`: dexterous-hand output adapter
- `inspire_teleoperation/main.py`: CLI and Web application composition
- `inspire_teleoperation/web_ui.py` and `web/`: local Web console
- `inspire_teleoperation/hand_controller.py`: retargeting and command loop
- `inspire_teleoperation/hand_retargeting.py`: local retargeting setup
- `inspire_teleoperation/inspire_hand_sim.py`: no-hardware adapter for the same retargeting output
- `inspire_teleoperation/dexhand.py`: copied low-level Modbus client
- `inspire_teleoperation/yam_calibration.py`: Quest relative-pose clutch and axis mapping
- `inspire_teleoperation/yam_kinematics.py`: six-axis YAM Pro MuJoCo/mink FK and IK
- `inspire_teleoperation/yam_sim_arm.py`: workspace/limit/filter guarded simulation module
- `inspire_teleoperation/yam_dual_sim.py`: independent left/right YAM simulation
- `inspire_teleoperation/yam_sim_main.py`: hardware-free Quest or synthetic simulation CLI
- `inspire_teleoperation/assets/hand_model/`: retargeting model and meshes
- `inspire_teleoperation/assets/yam_pro/`: packaged YAM Pro model, TCP and defaults
- `tests/`: hardware-independent unit tests

The runtime uses `televuer` and `dex-retargeting` as libraries. The Modbus
client is included directly, so no sibling DexterousHand checkout is needed.

From the repository root:

```bash
uv run python -m inspire_teleoperation --help
uv run python -m unittest discover -s tests
uv run python -m inspire_teleoperation
```

The final command can connect hardware. Confirm each host, port, device ID,
the clear workspace, and a conservative speed in the Web console first.

The top-level **Simulation** menu is a self-contained simulation workspace. It
is available before device setup and can create a Quest session with both
Modbus hands disabled, so simulation-only use does not pass through the
device-access form. Connecting Quest does not create MuJoCo: use the separate
**Start simulation** button after the Quest session is ready. GPU/viewer
selection, tracking, MuJoCo start/close, table-calibration selection/restart,
wrist-zero delay and left, right or dual wrist recapture all live in this menu.
The regular live-control page contains only real dexterous-hand controls and
joint state.

When table calibration is skipped, the simulation uses its default Quest
coordinate mapping and proceeds directly to wrist-zero capture. The simulation
remains a separate output module, so closing MuJoCo does not end the Quest
session.

To start the Web service with simulation auto-start disabled:

```bash
uv run python -m inspire_teleoperation --no-simulation
```

To auto-start the simulation but skip three-point table calibration:

```bash
uv run python -m inspire_teleoperation --no-simulation-table-calibration
```

## Stage-two YAM + Inspire-hand simulation

Run a synthetic wrist trajectory without Quest or robot hardware:

```bash
uv run inspire-yam-sim --demo
```

For a headless smoke test:

```bash
uv run inspire-yam-sim --demo --no-viewer --duration 10
```

Run with Quest tracking:

```bash
uv run inspire-yam-sim
```

Quest 模式默认先执行一次三点桌面标定。两台机械臂在标定期间保持折叠，
灵巧手模型仍用于确认追踪是否正常。使用右手食指依次指向：

1. 桌面坐标原点；
2. 从原点向桌面前方至少 8 cm 的一点；
3. 从原点向桌面左方至少 8 cm 的一点。

每一点都保持食指不动，捏合至少 0.25 秒，再松开确认。控制台会显示当前
`table=0/3` 至 `table=3/3` 的进度；移动超过约 12 mm、捏合过短、两条轴近似
共线或追踪丢失时，本次点位不会生效，并会显示重试原因。三点标定建立：
桌面前方为 YAM 基座 `+X`，桌面左方为 `+Y`，桌面法向向上为 `+Z`。Quest
OpenXR 的 `+Y` 重力反方向用于校验桌面接近水平，并消除法向的正负歧义。

第三点确认后，才开始左右手腕原有的三秒零位倒计时；保持双手在期望的同步
零位，倒计时结束后再移动。仅在调试旧坐标映射或无法使用 Quest pinch 数据时，
可以显式跳过桌面标定：

```bash
uv run inspire-yam-sim --no-table-calibration
```

`inspire-yam-sim` defaults to NVIDIA PRIME render offload, so the MuJoCo
viewer uses the discrete NVIDIA GPU on a working hybrid-graphics setup. To
leave GPU selection to the desktop session instead:

```bash
uv run inspire-yam-sim --gpu system
```

After table calibration and each hand is first detected, its arm stays folded
while a three-second countdown runs. The wrist pose at the end of that countdown
becomes the relative-motion zero, and synchronization starts on the following
frame. A
brief tracking dropout keeps the last safe arm target and hand visual; a
continuous loss longer than the configured grace period resets only that
side's countdown. The Quest left hand controls the left YAM and the Quest
right hand controls the right YAM. As in the real dual-dexterous-hand control
path, persistent left/right workers compute both arm updates concurrently from
the same Quest frame; MuJoCo receives both results together for one render
update. Workspace rejection, joint-limit rejection, and IK failure hold the
affected arm without discarding its captured zero, so moving the hand back
into a valid region resumes immediately. The other arm continues tracking.

Both opaque Inspire-hand models are attached to the achieved left/right YAM
TCPs. Their finger commands are produced by the exact `HandRetargeting` path
used by the real Modbus controller, including the same hardware order
`[pinky, ring, middle, index, thumb_bend, thumb_rotation]`, joint limits and
`0=closed / 1=open` convention. Only the final executor is replaced: normalized
commands are expanded into the URDF mimic joints and written to MuJoCo instead
of opening Modbus sockets. Left/right hand retargeting uses independent workers
and overlaps the two arm IK workers. Tracking loss or invalid retargeting holds
the last safe finger command. Use `--no-simulate-hands` only for arm-only
diagnostics.

The two YAM bases are fixed along the near edge of a white table. The viewer
starts with both arms in a compact folded pose that keeps joints 2 and 3 clear
of their lower limits, at an Ego viewpoint centered between the two bases and
facing the workspace. This is an initial free-camera pose rather than a
per-frame camera lock, so MuJoCo mouse drag rotates the view and the selected
view persists. The translucent blue left hand and orange right hand are Quest
targets, while the opaque hands attached to the wrists are achieved simulated
Inspire poses. An unreachable/invalid arm target turns red until IK can resume;
each arm's green TCP marker remains the achieved pose.
Axis mapping, translation scale, temporary TCP extrinsic, workspace and motion
limits live in
`inspire_teleoperation/assets/yam_pro/default_sim.yml`.

完整的中文接口、生命周期、Web API、Modbus API 和机械臂接入说明见
[API 文档](docs/API.zh-CN.md)。

## Adding an arm module

Implement the small `TeleopModule` contract and register it beside the hand
module. The arm receives the same timestamped frame and can use wrist/head poses
without depending on Modbus or hand retargeting internals:

```python
from inspire_teleoperation import ModuleStatus, TeleopFrame

class ArmTeleopModule:
    name = "arms"

    def start(self):
        self.controller.connect()

    def update(self, frame: TeleopFrame, *, enabled: bool):
        if not enabled or not frame.motion_data_ready:
            self.controller.hold()
            return
        if frame.right_hand and frame.right_hand.wrist:
            self.controller.command_wrist(frame.right_hand.wrist.matrix)

    def status(self):
        return ModuleStatus(self.name, ready=self.controller.is_connected)

    def close(self):
        self.controller.close()
```

Compose it with `TeleopRuntime(source, [hand_module, arm_module])`. For a real
arm integration, add workspace limits, velocity/acceleration limiting, frame
calibration, watchdog timeout, and an explicit emergency-stop path inside the
arm module rather than in the shared runtime.
