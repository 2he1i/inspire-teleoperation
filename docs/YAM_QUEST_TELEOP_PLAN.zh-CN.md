# YAM Pro + Inspire 灵巧手 + Quest Teleoperation 三阶段实施方案

## 目的与边界

本方案的目标是在现有的 Quest → Inspire 灵巧手遥操作工程上，接入一台
**I2RT YAM Pro**，形成安全、可记录、可逐步验证的 Quest 遥操作系统。

目标链路：

```text
Quest
  ├─ 手腕 6D 位姿 ──> YamArmTeleopModule ──> IK ──> YAM Pro（6 轴）
  └─ 25 个手部关键点 ─> HandTeleopModule ───────> Inspire（6 轴）
```

YAM 机械臂和 Inspire 手是两个独立输出通道：**不得把 Inspire 当成 YAM
自带的第 7 个夹爪关节**。YAM 臂端 IK 始终只求六个关节；灵巧手沿用当前
Modbus 与手部重定向链路。

所有 Python 命令必须通过 `uv run` 或项目的 uv 环境执行。

## 已确认的资产与可复用代码

当前项目已有：

- `inspire_teleoperation/quest_source.py`：Quest/TeleVuer 输入，输出
  `TeleopFrame`。
- `inspire_teleoperation/runtime.py`：同一 Quest 帧分发给多个独立模块。
- `inspire_teleoperation/hand_module.py` 与 `hand_controller.py`：Inspire
  手的 Quest 关键点重定向、Modbus 控制、限速与状态管理。
- `YAM Pro URDF/yam_pro_urdf_with_linear_gripper.urdf`：YAM Pro URDF。
- `YAM Pro URDF/yam_pro_urdf_with_linear_gripper.xml`：MuJoCo XML，适合作为
  仿真/IK 的起点。

父目录 `../YAM` 是实验室正在使用的 YAM 主从遥操作栈，应作为 YAM 的事实
硬件参考；不要复制其 GELLO leader 逻辑到 Quest。优先复用或参考：

- `../YAM/i2rt/i2rt/robots/kinematics.py`：MuJoCo + `mink` 的 FK/微分 IK。
- `../YAM/i2rt/i2rt/robots/get_robot.py`：YAM Pro 建链、关节限位、末端质量
  与惯量、真实/仿真机器人创建。
- `../YAM/gello_software/gello/robots/yam.py`：YAM follower 的反馈、
  Safe Hold、线程健康检查模式。
- `../YAM/gello_software/gello/safety/`：独立安全状态机、heartbeat lease、
  SAFE_HOLD、连续限速故障、watchdog 校验。
- `../YAM/gello_software/gello/data_utils/`：原子 HDF5 写入、相机同步、
  success/fail/discard 和异步写盘背压处理。

不应直接复用的部分：

- GELLO 的 `GelloAgent`、Dynamixel leader 标定和主从关节映射：它们只服务于
  物理 leader arm，不适用于 Quest。
- `YAMRobot` 的默认 7 DoF（六轴 + I2RT 原生夹爪）数据模型：外接 Inspire
  后应改为纯六轴机械臂包装器。
- 实验室双臂代码中硬编码的 14 DoF、左右臂索引和三相机布局：可复用安全/
  采集思想，不能原样接到单臂。
- `xr_teleoperate` 中面向 Unitree 的腰部偏移、坐标轴变换和 DDS 机械臂驱动。
- OpenTeach 的 Unity APK、ZMQ 多进程和 ROS 控制器；只借鉴其相对位姿 clutch
  与采集设计。

## 统一架构与关键设计决策

完成后应保持以下边界：

```text
QuestSource
  │ TeleopFrame（时间戳、头部、左右手腕、左右手关键点）
  ▼
TeleopRuntime
  ├── HandTeleopModule ───────────────> Inspire Modbus
  ├── YamSimArmModule（阶段一/二） ───> MuJoCo / 可视化
  ├── YamArmTeleopModule（阶段三） ──> YAM 安全门控 ─> CAN
  └── RecorderModule（阶段二后） ────> HDF5
```

### 坐标、TCP 与 clutch

机械臂不接受 Quest 的绝对世界位姿。每次启用臂控制时，捕获：

- 当前 Quest 手腕位姿 `T_XR_wrist_0`；
- 当前 YAM TCP 位姿 `T_base_tcp_0`；
- 标定得到的 Quest 增量到 YAM base 的旋转/尺度映射 `C`。

随后以相对增量驱动：

```text
ΔT_XR = inverse(T_XR_wrist_0) × T_XR_wrist
T_base_tcp_target = T_base_tcp_0 × C(ΔT_XR)
```

`C` 必须显式处理轴方向、平移缩放和手腕到 Inspire TCP 的固定外参。暂停、
重新启用、追踪丢失恢复或 IK 失败恢复时都重新捕获起点，绝不追赶旧目标。

当前上游 TeleVuer 的某些版本会输出带 Unitree 坐标约定和腰部偏移的数据。为
YAM 增加臂控制前，必须让机械臂模块获得原始 OpenXR 手腕位姿，或创建一个明确
的 YAM 专用坐标适配器；不得复用 Unitree 的固定腰部偏移。

### YAM Pro 的 TCP 模型

现有 MuJoCo XML 带线性夹爪，有六个臂关节和两个夹爪滑动关节，且没有为本项目
定义的 TCP site。实施时必须：

1. 验证 XML 中所有 mesh 路径可以被 MuJoCo 加载；缺少 mesh 时先修复资源布局，
   不允许用加载失败的模型继续开发。
2. 在第六轴法兰之后加入固定转接板和 `inspire_tcp` site。
3. 第一阶段将线性夹爪关节固定或移除，IK 只使用 `joint1` 至 `joint6`。
4. 在安装尺寸、质量、质心和惯量明确后，以真实 Inspire 安装参数替换临时模型；
   同时在真实 YAM 初始化时设置末端负载补偿。

## 阶段一：纯仿真机械臂 Teleop

### 目标

不连接 CAN、不使能 YAM 电机、不连接 Inspire 硬件，完成 Quest 手腕到 YAM Pro
六轴末端的可视化闭环。该阶段只验证臂端链路。

### 实施项

1. **建立 YAM 仿真资产与依赖。**

   - 将 YAM Pro XML/URDF 作为项目资源或以稳定的相对路径引用，避免依赖个人
     工作目录。
   - 增加 MuJoCo、`mink` 和 YAM/i2rt 本地依赖的 uv 配置；使用
     `ArmType.YAM_PRO`，不使用默认标准 YAM。
   - 添加 `inspire_tcp` site，并提供加载/关节名/关节限位的自动测试。

2. **实现运动学与仿真控制接口。**

   建议新增：

   ```text
   inspire_teleoperation/yam_kinematics.py
   inspire_teleoperation/yam_sim_arm.py
   inspire_teleoperation/assets/yam_pro/
   tests/test_yam_kinematics.py
   tests/test_yam_sim_arm.py
   ```

   `YamKinematics` 应封装 i2rt `Kinematics` 的 FK/IK，而不是复制求解器；每帧
   以最新 `q` warm start。在线控制初始应使用较小迭代预算，求解失败应返回失败
   状态并保持上一安全关节目标，不允许阻塞 200 次迭代。

3. **实现 `YamSimArmModule`。**

   - 满足 `TeleopModule` 合约：`start/update/status/close`。
   - `enabled=False`、Quest 追踪不完整、输入 NaN、目标越界、IK 失败时均进入
     hold，不改变模拟关节目标。
   - 有独立的工作空间 AABB、关节限位、每帧角度增量和低通滤波。
   - 仅接受右手或可配置的操作手；另一只手仍可留给 Inspire。
   - 显示当前 TCP、Quest 目标、IK 成功率、位置/姿态误差与限速状态。

4. **处理 Quest 坐标。**

   实现可测试的 `QuestToYamCalibration`，使旋转、缩放、基准位姿和 TCP 固定
   外参全部来自配置，而不是散落的常量。先在可视化中校正，不进入硬件阶段。

### 阶段一验收标准

- 无 YAM/Inspire 硬件时可启动、停止和运行 10 分钟以上。
- 在 YAM 可达工作空间内，连续平移/转动 Quest 手腕时 TCP 平滑跟随；重启或
  clutch 后无跳变。
- 对不可达目标、NaN、丢失手部追踪、暂停/恢复均保持上一安全姿态。
- 所有命令关节角满足模型限位，单帧增量不超过配置上限。
- 自动测试至少覆盖：XML 加载、FK/IK 往返误差、限位、追踪丢失 hold、clutch
  重置。

## 阶段二：Quest 臂手联合仿真与数据链路

### 目标

在仿真中同时运行 YAM 六轴和现有 Inspire 手逻辑，验证真正的操作者体验、
启停状态、数据格式和视觉记录；仍不向真实 YAM 电机下发命令。

当前实现进度（2026-07-27）：已完成“臂手联合仿真”子项。双 Inspire URDF
实体手固定在两台 YAM 的实际 TCP 上，直接复用真机 `HandRetargeting` 的左右手
重定向、六关节硬件顺序、归一化和限位；仿真只替换最终 Modbus 执行器，不另写
手势到关节角算法。左右手重定向并行运行，并与左右臂 IK 重叠执行。Quest
半透明手继续显示目标，实体手显示实际仿真输出。该入口不会连接 Inspire
Modbus，也不会连接 YAM CAN。Quest 模式还加入三点桌面标定：右手食指通过稳定
捏合并松开依次确认原点、前方点和左方点，建立“前/左/上”到 YAM 基座
`+X/+Y/+Z` 的右手坐标系；标定期间双臂保持折叠，完成后才进入双腕三秒零位
捕获。阶段二的模式 UI 与 episode 记录器仍是后续子项。

### 实施项

1. **组合运行时。**

   ```python
   runtime = TeleopRuntime(
       source,
       [hand_module, yam_sim_arm_module, recorder_module],
   )
   ```

   机械臂与手必须各自有状态和健康信息。Web UI 至少要能显示：Quest 连接、手
   状态、臂状态、IK 状态、限速状态、当前模式和最后一次故障原因。

2. **明确模式与安全交互。**

   建议仅保留以下模式，且模式切换必须由明确 UI 操作或稳定手势触发：

   - `PAUSED`：臂 hold；手保持最后安全命令或按手模块策略保持。
   - `HAND_ONLY`：仅 Inspire 响应；YAM TCP hold。
   - `ARM_AND_HAND`：两者并行响应。
   - `CLUTCH`：重新捕获 Quest/YAM 起点，未完成前不动臂。

   不能把短暂 pinch 直接作为真实机械臂启用命令；真实硬件启用必须另有确认。

3. **实现记录器。**

   参考实验室 `EpisodeWriter` 的原子写入与异步背压模型，但不要沿用其 14 DoF
   双臂 schema。新 schema 至少记录：

   ```text
   timestamp
   observations/yam_qpos                 [T, 6]
   actions/yam_qpos                      [T, 6]  # 实际送入安全层后的目标
   observations/inspire_qpos             [T, 6]
   actions/inspire_qpos                  [T, 6]
   inputs/quest_wrist_pose               [T, 4, 4]
   inputs/quest_hand_landmarks           [T, 25, 3]
   metadata/calibration
   metadata/yam_model_and_tcp
   metadata/software_versions
   ```

   如启用 RealSense，再记录每个相机的 RGB/Depth、帧号、主机时间戳和跨相机
   skew。写入队列满、相机连续失步或写盘错误时，必须停止记录并使臂进入 hold；
   未完成 episode 不能标记为成功。

4. **验证操控质量。**

   对平移、姿态旋转、暂停/重启、不同缩放、手指捏取进行回放。记录并审查
   IK 失败率、目标夹断次数、控制循环频率和最大动作跳变。

### 阶段二验收标准

- 手模块与 YAM 仿真模块可同时运行，任一模块异常不会让另一模块输出失控命令。
- `PAUSED`、`HAND_ONLY`、`ARM_AND_HAND`、`CLUTCH` 转换均无 YAM 目标跳变。
- 可录制并原子保存 success/fail/discard episode；回放时数组形状、时间轴和
  关节限位全部一致。
- 连续 30 分钟仿真中无内存持续增长、写盘积压或未处理异常。
- 通过桌面抓取类任务的操控演练：目标可达、姿态映射正确、手腕和手指互不串扰。

## 阶段三：低速真实 YAM Pro 接入与逐步开放 Inspire

### 目标

在不改变 Quest 映射、IK 和记录 schema 的前提下，只将模拟执行器替换成实验室
已经验证的 YAM follower 与安全链。真实硬件默认从 `PAUSED`/`SAFE_HOLD` 开始。

### 实施项

1. **实现纯六轴 YAM 硬件包装器。**

   建议新增 `YamHardwareArmController`，使用实验室 i2rt，但显式配置：

   - `ArmType.YAM_PRO`；
   - 无 I2RT 原生夹爪（Inspire 独立控制）；
   - 正确的 CAN channel；
   - Inspire + 转接板的 `ee_mass` 与 `ee_inertia`；
   - 当前关节反馈、关节限位、CAN 控制线程与反馈时间戳健康状态。

   不要直接把现有 7 DoF `YAMRobot` 接进当前运行时。可以抽取它的
   `get_health_status()`、`enter_safe_hold()` 与并行准备 CAN 链路模式。

2. **接入或泛化实验室安全守护。**

   真实臂命令必须通过安全状态机；最低要求如下：

   - 启动时验证 CAN UP、1 Mbps、全部 YAM 电机 400 ms watchdog、反馈新鲜度和
     控制线程存活。
   - 默认 `SAFE_HOLD`，且只有显式确认后才可 `ACTIVE`。
   - 至少两个独立 heartbeat lease（例如运行时和 UI/采集器）；任一超时立即
     SAFE_HOLD。
   - 验证 NaN、关节限位；对每帧关节增量限幅；连续多帧限幅时锁存故障并 hold。
   - IK 失败、Quest 丢失、相机/写盘严重故障、进程退出、CAN 线程死亡均进入
     SAFE_HOLD。
   - 电机 disable 必须是 SAFE_HOLD 后的独立二次确认，不可作为普通退出动作。

3. **按风险逐级验证。**

   严格按顺序，不跳级：

   1. 断开 Inspire、限低速度，仅读取 YAM 状态和验证 Safe Hold。
   2. 不戴 Quest，用固定小幅关节命令检查方向、限位和 TCP FK。
   3. 戴 Quest 但 `PAUSED`，验证跟踪、坐标和 clutch，不移动机械臂。
   4. `ARM_AND_HAND` 下仅开放小工作盒、低平移缩放、低关节步长；现场须有第二位
      监护人员与可达急停。
   5. 确认臂端稳定后接入 Inspire；先手指空载、再接触软物、最后进行抓取任务。
   6. 最后才开启相机记录和长 episode。

4. **配置与审计。**

   所有 CAN 名称、TCP 外参、末端质量/惯量、缩放、限位、最大速度、模型版本和
   calibration ID 必须在版本化配置中保存，并写入每个 episode 的 metadata。
   设备序列号、机器私有路径、网络地址等机器敏感值应放在本地配置，不能写入 Git。

### 阶段三验收标准

- 任何进程中断、Quest 追踪丢失、IK 连续失败或 heartbeat 过期，都可在
  watchdog 超时前进入确认的 SAFE_HOLD。
- 启用、暂停、clutch 和退出全过程中，真实 TCP 没有不可解释的跳变。
- 低速工作盒内完成至少一个不接触和一个软物抓取任务；YAM/手关节、相机和
  Quest 数据可回放、时间同步可审计。
- 在受控条件下连续运行前，复核末端负载补偿、关节温度、CAN 健康与动作限幅日志。

## 下一轮 Codex 的推荐执行顺序

下一轮只执行**阶段一**，不要连接真实 YAM 或 Inspire 硬件。建议提示词：

> 阅读 `docs/YAM_QUEST_TELEOP_PLAN.zh-CN.md`。仅实现阶段一的 YAM Pro
> MuJoCo 模型预检、`inspire_tcp`、Quest 相对位姿 clutch、`YamKinematics`、
> `YamSimArmModule` 和无硬件测试。所有 Python 命令使用 uv。不得修改父目录
> YAM 工程，不得连接 CAN 或下发真实机械臂命令。

阶段一验收通过后，再单独授权实施阶段二；阶段三必须在真实硬件、急停和现场
监护条件都具备时才开始。
