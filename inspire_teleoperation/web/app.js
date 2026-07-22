const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

const copy = {
  zh: {
    workspace: "工作区", connection: "设备接入", dashboard: "实时控制", tactile: "触觉反馈", systemLog: "系统日志", systemState: "系统状态", localConsole: "本地控制台", preferences: "界面设置", appearance: "外观",
    setupEyebrow: "设备接入", setupTitle: "建立遥操作连接", setupLead: "配置设备与控制策略，确认安全后启动会话。", stepConfigure: "配置", stepConnect: "连接", stepControl: "控制",
    devices: "设备", devicesHelp: "选择要控制的灵巧手并确认网络地址", oneRequired: "至少启用一台", leftHand: "左手", rightHand: "右手", host: "主机地址", deviceId: "设备 ID",
    controlParams: "控制策略", controlHelp: "设置通信频率与关节运动速度", port: "Modbus 端口", timeout: "请求超时", speedMode: "速度模式", adaptive: "自适应 2.0", adaptive_v2: "自适应 2.0", adaptive_v1: "自适应 1.0", fixed: "固定速度", fixedSpeed: "固定速度", fixedSpeedHint: "仅固定模式生效", questRate: "Quest 采样率", handRate: "手部指令率", tactileRateSetting: "触觉轮询率", tactileRateHint: "范围 1–60 Hz，仅在触觉页采集",
    advancedOptions: "会话选项", advancedHint: "跟踪启动、标记显示与断开行为", startNow: "连接后立即跟踪", startNowHelp: "工作区清空时使用", hideMarkers: "隐藏 Quest 标记", hideMarkersHelp: "不影响数据采集", openExit: "断开设备时张手", openExitHelp: "安装工具时保持关闭",
    safetyCheck: "连接前检查", safetyIntro: "设备可能在连接后立即运动", checkWorkspace: "设备固定与线缆状态已检查", checkNetwork: "设备地址与网络已确认", checkSpeed: "已选择合适的速度策略", safetyConfirm: "我确认工作区内没有人员、工具或易损物体", safetyDetail: "此确认是建立设备连接的必要条件。", connect: "连接设备", localOnly: "仅在本机建立连接",
    liveEyebrow: "实时遥操作", dashboardTitle: "运行控制台", dashboardLead: "监控连接、数据链路与关节状态。", session: "会话", teleopStatus: "遥操作状态", questData: "Quest 数据", loopRate: "主循环频率", safetyTitle: "进入工作区前", safetyPause: "请先停止跟踪", run: "开始跟踪", stopTracking: "停止跟踪", switchSpeed: "切换速度", calibrateForce: "力传感器校准", disconnect: "断开设备",
    tactileEyebrow: "触觉反馈", tactileTitle: "触觉热力图", tactileLead: "查看每个触觉区域的压力分布，悬停方格可读取精确数值。", bothHands: "双手", tactileStatus: "数据状态", sampleRate: "采样频率", waitingTactile: "等待首帧", tactileReady: "数据已更新", tactileNoData: "正在读取触觉数据…", tactileError: "读取失败", row: "行", column: "列", sensorValue: "数值",
    captureTitle: "触觉信息采集", captureLead: "按指定频率将当前所选手部的触觉帧流式写入文件", captureFrequency: "采集频率", captureFrequencyHint: "不得高于当前触觉数据率", captureDuration: "采集时间", captureDurationHint: "最长 24 小时", captureOutput: "输出路径", captureOutputHint: "可填写目录或以 .jsonl 结尾的文件路径", captureFormat: "输出格式", captureFormatHint: "每行一帧，支持流式读取", captureStart: "开始采集", captureStop: "停止采集", captureIdle: "未开始", captureRecording: "采集中", captureStopping: "正在停止", captureCompleted: "采集完成", captureStopped: "已停止", captureFailed: "采集失败", captureWaiting: "等待开始采集", captureSamples: "帧", captureSavedTo: "输出文件", captureSelectHand: "请先选择要采集的手部。", captureProgress: "采集进度", captureDropped: "丢弃帧",
    joint: "关节", position: "实际 / 目标", speed: "速度", sixJoints: "6 个关节", latestEvents: "最近 4 条运行事件", viewAllLogs: "查看全部", logsEyebrow: "运行记录", logsLead: "查看当前控制会话的完整运行事件。", logEntries: "条记录", clearLogs: "清空日志", currentSession: "当前会话", realtimeUpdates: "日志实时更新", liveUpdate: "实时", time: "时间", clear: "清空", level: "级别", event: "事件", noEvents: "暂无运行日志",
    cancel: "取消", confirm: "确认", waitingSetup: "等待配置", connecting: "正在连接", disconnecting: "正在断开", live: "已连接", stopping: "正在停止", stopped: "已停止", error: "连接错误", paused: "跟踪已停止", running: "正在跟踪", waitingData: "等待手部数据", ready: "数据就绪", unavailable: "无数据", connected: "已连接", enabled: "已启用", disabled: "未启用",
    fontSize: "界面字号", fontSizeHelp: "输入精确字号，整个控制台会按比例调整。", themeColor: "主题色", themeColorHelp: "选择预设颜色，或使用自定义颜色。", customColor: "自定义", resetAppearance: "恢复默认", shutdownService: "关闭控制服务", disconnectBeforeShutdown: "请先断开设备，再关闭控制服务。",
    setupFailed: "无法提交配置", enableOneHandError: "请至少启用一只手。", duplicateHostError: "左右手不能使用相同的主机地址。", safetyConfirmationError: "请勾选工作区安全确认。", invalidSettingsError: "请检查高亮的设备地址或控制参数。", actionFailed: "操作失败", runTitle: "开始手部跟踪？", runCopy: "确认双手工作区已经清空。开始后，Quest 手势将实时驱动灵巧手。", calibrateForceTitle: "校准力传感器？", calibrateForceCopy: "移除灵巧手上的外力与接触物。确认后将停止跟踪，并校准所有已连接的手。", calibrationRequested: "正在校准力传感器，请保持灵巧手不受外力。", calibrationRunningTitle: "正在校准", calibrationRunningCopy: "正在等待最短校准时间并验证六路力值稳定，请勿接触灵巧手。", calibrationCompletedTitle: "校准完成", calibrationCompletedCopy: "所有已连接灵巧手的零点力值已经稳定。确认后关闭此窗口。", calibrationFailedTitle: "校准失败", calibrationFailedCopy: "力值未能稳定或设备通信失败。", acknowledge: "确定", disconnectTitle: "断开当前设备？", disconnectCopy: "跟踪将停止，Modbus 与 Quest 会话将关闭。随后可以立即修改设备接入设置并重新连接。", quitTitle: "关闭控制服务？", quitCopy: "所有设备会断开，当前页面也将停止提供服务。下次使用需要重新启动程序。", jointNames: ["小指", "无名指", "中指", "食指", "拇指", "旋转"], tactileRegions: { little_tip: "小指尖", little_nail: "小指背", little_pad: "小指腹", ring_tip: "无名指尖", ring_nail: "无名指背", ring_pad: "无名指腹", middle_tip: "中指尖", middle_nail: "中指背", middle_pad: "中指腹", index_tip: "食指尖", index_nail: "食指背", index_pad: "食指腹", thumb_tip: "拇指尖", thumb_nail: "拇指背", thumb_middle: "拇指中部", thumb_pad: "拇指腹", palm: "掌心" }, tactileGroups: { little: "小指", ring: "无名指", middle: "中指", index: "食指", thumb: "拇指", palm: "掌心" }
  },
  en: {
    workspace: "Workspace", connection: "Device setup", dashboard: "Live control", tactile: "Tactile feedback", systemLog: "System log", systemState: "System state", localConsole: "Local console", preferences: "Interface settings", appearance: "Appearance",
    setupEyebrow: "Device setup", setupTitle: "Start a teleoperation session", setupLead: "Configure devices and control behavior, then complete the safety check.", stepConfigure: "Configure", stepConnect: "Connect", stepControl: "Control",
    devices: "Devices", devicesHelp: "Choose each dexterous hand and verify its network address", oneRequired: "One required", leftHand: "Left hand", rightHand: "Right hand", host: "Host address", deviceId: "Device ID",
    controlParams: "Control strategy", controlHelp: "Set communication rates and joint motion speed", port: "Modbus port", timeout: "Request timeout", speedMode: "Speed mode", adaptive: "Adaptive 2.0", adaptive_v2: "Adaptive 2.0", adaptive_v1: "Adaptive 1.0", fixed: "Fixed speed", fixedSpeed: "Fixed speed", fixedSpeedHint: "Used in fixed mode only", questRate: "Quest polling", handRate: "Hand command rate", tactileRateSetting: "Tactile polling", tactileRateHint: "1–60 Hz; sampled only on the tactile page",
    advancedOptions: "Session options", advancedHint: "Tracking start, marker display, and disconnect behavior", startNow: "Track immediately", startNowHelp: "Use only in a clear workspace", hideMarkers: "Hide Quest markers", hideMarkersHelp: "Capture is unaffected", openExit: "Open hands on disconnect", openExitHelp: "Keep off when tools are attached",
    safetyCheck: "Preflight check", safetyIntro: "Devices may move immediately after connection", checkWorkspace: "Device mounting and cables checked", checkNetwork: "Device addresses and network verified", checkSpeed: "Appropriate speed strategy selected", safetyConfirm: "I confirm the workspaces are clear of people, tools, and fragile objects", safetyDetail: "This confirmation is required to establish a connection.", connect: "Connect devices", localOnly: "Connection stays on this machine",
    liveEyebrow: "Live teleoperation", dashboardTitle: "Operations console", dashboardLead: "Monitor connections, data flow, and joint state.", session: "Session", teleopStatus: "Teleop status", questData: "Quest data", loopRate: "Main loop rate", safetyTitle: "Before entering workspace", safetyPause: "Stop tracking first", run: "Start tracking", stopTracking: "Stop tracking", switchSpeed: "Switch speed", calibrateForce: "Calibrate force sensors", disconnect: "Disconnect devices",
    tactileEyebrow: "Tactile feedback", tactileTitle: "Tactile heatmap", tactileLead: "Inspect pressure across every tactile region; hover a cell for its exact value.", bothHands: "Both hands", tactileStatus: "Live data", sampleRate: "Sample rate", waitingTactile: "Waiting for first frame", tactileReady: "Data updated", tactileNoData: "Reading tactile data…", tactileError: "Read failed", row: "Row", column: "Column", sensorValue: "Value",
    captureTitle: "Tactile data capture", captureLead: "Stream tactile frames from the selected hands to a file at a defined rate", captureFrequency: "Capture rate", captureFrequencyHint: "Cannot exceed the available tactile data rate", captureDuration: "Duration", captureDurationHint: "Up to 24 hours", captureOutput: "Output path", captureOutputHint: "Enter a directory or a file ending in .jsonl", captureFormat: "Output format", captureFormatHint: "One frame per line for streaming reads", captureStart: "Start capture", captureStop: "Stop capture", captureIdle: "Not started", captureRecording: "Recording", captureStopping: "Stopping", captureCompleted: "Complete", captureStopped: "Stopped", captureFailed: "Capture failed", captureWaiting: "Waiting to start", captureSamples: "frames", captureSavedTo: "Output file", captureSelectHand: "Select at least one hand to capture.", captureProgress: "Capture progress", captureDropped: "Dropped frames",
    joint: "Joint", position: "Actual / target", speed: "Speed", sixJoints: "6 joints", latestEvents: "Latest 4 runtime events", viewAllLogs: "View all", logsEyebrow: "Runtime records", logsLead: "Review the complete event history for the current control session.", logEntries: "entries", clearLogs: "Clear logs", currentSession: "Current session", realtimeUpdates: "Logs update in real time", liveUpdate: "Live", time: "Time", clear: "Clear", level: "Level", event: "Event", noEvents: "No runtime events",
    cancel: "Cancel", confirm: "Confirm", waitingSetup: "Awaiting setup", connecting: "Connecting", disconnecting: "Disconnecting", live: "Connected", stopping: "Stopping", stopped: "Stopped", error: "Connection error", paused: "Tracking stopped", running: "Tracking", waitingData: "Waiting for hand data", ready: "Data ready", unavailable: "Unavailable", connected: "Connected", enabled: "Enabled", disabled: "Disabled",
    fontSize: "Interface font size", fontSizeHelp: "Enter an exact size to scale console typography.", themeColor: "Theme color", themeColorHelp: "Choose a preset or use a custom color.", customColor: "Custom", resetAppearance: "Reset appearance", shutdownService: "Stop control service", disconnectBeforeShutdown: "Disconnect the devices before stopping the control service.",
    setupFailed: "Could not submit configuration", enableOneHandError: "Enable at least one hand.", duplicateHostError: "Left and right hands cannot use the same host address.", safetyConfirmationError: "Confirm that the hand workspace is clear.", invalidSettingsError: "Check the highlighted device addresses or control settings.", actionFailed: "Action failed", runTitle: "Start hand tracking?", runCopy: "Confirm both hand workspaces are clear. Quest gestures will drive the dexterous hands in real time.", calibrateForceTitle: "Calibrate force sensors?", calibrateForceCopy: "Remove all loads and contact from the hands. Tracking will stop and every connected hand will be calibrated.", calibrationRequested: "Calibrating force sensors. Keep the hands unloaded.", calibrationRunningTitle: "Calibrating", calibrationRunningCopy: "Waiting for the minimum calibration time and stable readings from all six force channels. Do not touch the hands.", calibrationCompletedTitle: "Calibration complete", calibrationCompletedCopy: "Zero-force readings are stable on every connected hand. Confirm to close this window.", calibrationFailedTitle: "Calibration failed", calibrationFailedCopy: "Force readings did not stabilize or device communication failed.", acknowledge: "OK", disconnectTitle: "Disconnect current devices?", disconnectCopy: "Tracking, Modbus, and the Quest session will stop. You can then edit device settings and reconnect immediately.", quitTitle: "Stop the control service?", quitCopy: "All devices will disconnect and this page will stop responding. Restart the program to use it again.", jointNames: ["Little", "Ring", "Middle", "Index", "Thumb", "Rotate"], tactileRegions: { little_tip: "Little tip", little_nail: "Little nail", little_pad: "Little pad", ring_tip: "Ring tip", ring_nail: "Ring nail", ring_pad: "Ring pad", middle_tip: "Middle tip", middle_nail: "Middle nail", middle_pad: "Middle pad", index_tip: "Index tip", index_nail: "Index nail", index_pad: "Index pad", thumb_tip: "Thumb tip", thumb_nail: "Thumb nail", thumb_middle: "Thumb middle", thumb_pad: "Thumb pad", palm: "Palm" }, tactileGroups: { little: "Little", ring: "Ring", middle: "Middle", index: "Index", thumb: "Thumb", palm: "Palm" }
  }
};

let language = "zh";
let configured = false;
let lastPhase = "setup";
let lastDetail = "";
let hiddenLogCount = 0;
let logFingerprint = "";
let latestMessages = [];
let latestSnapshot = null;
let latestConfig = {};
let activeNav = "setup";
let setupSubmitting = false;
let setupErrors = [];
let tactileSelection = [];
let tactileFingerprint = "";
let activeTactileCell = null;
let latestCapture = { state: "idle" };
let captureRequestError = "";
let calibrationDialogStage = "idle";
let calibrationDialogDetail = "";
const preferenceKey = "inspire-console-appearance-v1";
const setupPreferenceKey = "inspire-console-setup-v1";
const capturePreferenceKey = "inspire-console-capture-v1";
const languagePreferenceKey = "inspire-console-language-v1";
const setupPreferenceFields = [
  "left_enabled", "left_host", "left_device_id",
  "right_enabled", "right_host", "right_device_id",
  "modbus_port", "modbus_timeout", "target_speed", "speed_mode",
  "frequency", "hand_frequency", "tactile_frequency",
  "start", "open_on_exit", "hide_hand_markers"
];
const defaultPreferences = { fontSize: 12, accent: "#a7f432" };
const defaultCapturePreferences = { frequency: 10, duration: 10, output: "tactile_captures" };
let preferences = { ...defaultPreferences };

const tactileGroupSpecs = [
  ["little", ["little_tip", "little_nail", "little_pad"]],
  ["ring", ["ring_tip", "ring_nail", "ring_pad"]],
  ["middle", ["middle_tip", "middle_nail", "middle_pad"]],
  ["index", ["index_tip", "index_nail", "index_pad"]],
  ["thumb", ["thumb_tip", "thumb_nail", "thumb_middle", "thumb_pad"]],
  ["palm", ["palm"]]
];

function t(key) { return copy[language][key] ?? key; }

function updateShutdownAvailability(hasSession = lastPhase !== "setup") {
  const button = $('#shutdown-button');
  button.setAttribute("aria-disabled", hasSession ? "true" : "false");
  button.dataset.blockedHint = t("disconnectBeforeShutdown");
  button.setAttribute("aria-label", hasSession
    ? `${t("shutdownService")}。${t("disconnectBeforeShutdown")}`
    : t("shutdownService"));
}

function normalizePreferences(value = {}) {
  const fontSize = Math.max(10, Math.min(18, Number(value.fontSize) || defaultPreferences.fontSize));
  const accent = /^#[0-9a-f]{6}$/i.test(value.accent || "") ? value.accent.toLowerCase() : defaultPreferences.accent;
  return { fontSize, accent };
}

function loadPreferences() {
  try { preferences = normalizePreferences(JSON.parse(localStorage.getItem(preferenceKey) || "{}")); }
  catch (_error) { preferences = { ...defaultPreferences }; }
  applyPreferences(false);
}

function applyPreferences(persist = true) {
  preferences = normalizePreferences(preferences);
  document.documentElement.style.setProperty("--ui-font-size", `${preferences.fontSize}px`);
  document.documentElement.style.setProperty("--accent", preferences.accent);
  $('#font-size-input').value = preferences.fontSize;
  $('#custom-color-input').value = preferences.accent;
  $$('.theme-swatch').forEach(button => button.classList.toggle("active", button.dataset.color.toLowerCase() === preferences.accent));
  if (persist) {
    try { localStorage.setItem(preferenceKey, JSON.stringify(preferences)); }
    catch (_error) { /* Appearance still applies when storage is unavailable. */ }
  }
}

function setFontSize(value) {
  if (!Number.isFinite(Number(value))) return;
  preferences.fontSize = Math.round(Number(value));
  applyPreferences();
}

function loadSetupPreferences() {
  try {
    const saved = JSON.parse(localStorage.getItem(setupPreferenceKey) || "{}");
    if (!saved || typeof saved !== "object" || Array.isArray(saved)) return {};
    return Object.fromEntries(setupPreferenceFields
      .filter(name => {
        if (!Object.hasOwn(saved, name)) return false;
        const field = $('#setup-form').elements[name];
        return field.type === "checkbox"
          ? typeof saved[name] === "boolean"
          : ["string", "number"].includes(typeof saved[name]);
      })
      .map(name => [name, saved[name]]));
  } catch (_error) {
    return {};
  }
}

function loadLanguagePreference() {
  try {
    const saved = localStorage.getItem(languagePreferenceKey);
    return saved === "zh" || saved === "en" ? saved : "";
  } catch (_error) {
    return "";
  }
}

function saveSetupPreferences() {
  const form = $('#setup-form');
  const saved = Object.fromEntries(setupPreferenceFields.map(name => {
    const field = form.elements[name];
    return [name, field.type === "checkbox" ? field.checked : field.value];
  }));
  try { localStorage.setItem(setupPreferenceKey, JSON.stringify(saved)); }
  catch (_error) { /* Form settings still work when storage is unavailable. */ }
}

function loadCapturePreferences() {
  let saved = {};
  try { saved = JSON.parse(localStorage.getItem(capturePreferenceKey) || "{}"); }
  catch (_error) { /* Fall back to capture defaults. */ }
  const form = $('#tactile-capture-form');
  form.elements.capture_frequency.value = Number(saved.frequency) > 0 ? saved.frequency : defaultCapturePreferences.frequency;
  form.elements.capture_duration.value = Number(saved.duration) > 0 ? saved.duration : defaultCapturePreferences.duration;
  form.elements.capture_output.value = typeof saved.output === "string" && saved.output.trim() ? saved.output : defaultCapturePreferences.output;
}

function saveCapturePreferences() {
  const form = $('#tactile-capture-form');
  const value = {
    frequency: Number(form.elements.capture_frequency.value),
    duration: Number(form.elements.capture_duration.value),
    output: form.elements.capture_output.value
  };
  try { localStorage.setItem(capturePreferenceKey, JSON.stringify(value)); }
  catch (_error) { /* Capture settings still apply when storage is unavailable. */ }
}

function applyLanguage() {
  document.documentElement.lang = language === "zh" ? "zh-CN" : "en";
  $$('[data-i18n]').forEach(element => { element.textContent = t(element.dataset.i18n); });
  $('#language-button').textContent = language === "zh" ? "EN" : "中";
  $('#page-name').textContent = lastPhase === "setup" ? t("connection") : t(activeNav === "tactile" ? "tactile" : activeNav === "logs" ? "systemLog" : "dashboard");
  updateShutdownAvailability();
  updateHandFields();
  if (latestSnapshot) {
    renderSnapshot(latestSnapshot);
    tactileFingerprint = "";
    activeTactileCell = null;
    $('#tactile-tooltip').hidden = true;
    $('#tactile-hands').innerHTML = "";
    renderTactile(latestSnapshot.tactile || {});
  }
  if (setupErrors.length) renderSetupErrors(setupErrors);
  renderTactileCapture(latestCapture);
  logFingerprint = "";
  renderLogs(latestMessages);
}

function setForm(config) {
  Object.entries(config).forEach(([name, value]) => {
    const field = $(`[name="${name}"]`);
    if (!field) return;
    if (field.type === "checkbox") field.checked = value;
    else field.value = value;
  });
  updateHandFields();
  updateSpeedFields();
}

function updateHandFields() {
  ["left", "right"].forEach(side => {
    const enabled = $(`[name="${side}_enabled"]`).checked;
    const box = $(`#${side}-config`);
    box.classList.toggle("disabled", !enabled);
    $$(`input:not([name="${side}_enabled"])`, box).forEach(input => { input.disabled = !enabled; });
    $(`[data-side-summary="${side}"]`).textContent = t(enabled ? "enabled" : "disabled");
  });
}

function updateSpeedFields() {
  const fixed = $('[name="speed_mode"]').value === "fixed";
  $('#fixed-speed-field').classList.toggle("inactive", !fixed);
}

function formPayload() {
  const form = $('#setup-form');
  const value = name => form.elements[name].value;
  const checked = name => form.elements[name].checked;
  return {
    left_enabled: checked("left_enabled"), left_host: value("left_host"), left_device_id: Number(value("left_device_id")),
    right_enabled: checked("right_enabled"), right_host: value("right_host"), right_device_id: Number(value("right_device_id")),
    modbus_port: Number(value("modbus_port")), modbus_timeout: Number(value("modbus_timeout")), target_speed: Number(value("target_speed")),
    speed_mode: value("speed_mode"), frequency: Number(value("frequency")), hand_frequency: Number(value("hand_frequency")), tactile_frequency: Number(value("tactile_frequency")),
    start: checked("start"), open_on_exit: checked("open_on_exit"), hide_hand_markers: checked("hide_hand_markers"), safety_confirmed: checked("safety_confirmed")
  };
}

function renderSetupErrors(errors) {
  setupErrors = [...new Set(errors.filter(Boolean))];
  const container = $('#setup-error');
  if (!setupErrors.length) {
    container.innerHTML = "";
    return;
  }
  container.innerHTML = `<strong>${escapeHtml(t("setupFailed"))}</strong><ul>${setupErrors.map(error => `<li>${escapeHtml(t(error))}</li>`).join("")}</ul>`;
}

function clearSetupErrors() {
  setupErrors = [];
  $('#setup-error').innerHTML = "";
  $$('.field-invalid', $('#setup-form')).forEach(element => element.classList.remove("field-invalid"));
  $$('[aria-invalid="true"]', $('#setup-form')).forEach(element => element.removeAttribute("aria-invalid"));
}

function validateSetupForm(form) {
  clearSetupErrors();
  const errors = [];
  const leftEnabled = form.elements.left_enabled.checked;
  const rightEnabled = form.elements.right_enabled.checked;
  if (!leftEnabled && !rightEnabled) {
    errors.push("enableOneHandError");
    $('#left-config').classList.add("field-invalid");
    $('#right-config').classList.add("field-invalid");
  }
  const leftHost = form.elements.left_host.value.trim().toLocaleLowerCase();
  const rightHost = form.elements.right_host.value.trim().toLocaleLowerCase();
  if (leftEnabled && rightEnabled && leftHost && leftHost === rightHost) {
    errors.push("duplicateHostError");
    [form.elements.left_host, form.elements.right_host].forEach(field => {
      field.classList.add("field-invalid");
      field.setAttribute("aria-invalid", "true");
    });
    $('#left-config').classList.add("field-invalid");
    $('#right-config').classList.add("field-invalid");
  }
  if (!form.elements.safety_confirmed.checked) {
    errors.push("safetyConfirmationError");
    $('.safety-check').classList.add("field-invalid");
    form.elements.safety_confirmed.setAttribute("aria-invalid", "true");
  }

  let invalidSettings = false;
  $$('input, select', form).forEach(field => {
    if (field.disabled || field.type === "checkbox" || field.type === "submit") return;
    const emptyHost = field.name.endsWith("_host") && !field.value.trim();
    if (!field.validity.valid || emptyHost) {
      invalidSettings = true;
      field.classList.add("field-invalid");
      field.setAttribute("aria-invalid", "true");
    }
  });
  if (invalidSettings) errors.push("invalidSettingsError");
  renderSetupErrors(errors);
  return errors.length === 0;
}

async function post(path, payload) {
  const response = await fetch(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
  const body = await response.json();
  if (!response.ok) throw new Error(body.error || `HTTP ${response.status}`);
  return body;
}

function phaseLabel(phase) {
  return t({ setup: "waitingSetup", connecting: "connecting", disconnecting: "disconnecting", live: "live", stopping: "stopping", stopped: "stopped", error: "error" }[phase] || phase);
}

function renderPhase(state) {
  const phaseChanged = lastPhase !== state.phase;
  lastPhase = state.phase;
  $('#connection-label').textContent = phaseLabel(state.phase);
  $('#connection-dot').className = `status-dot ${state.phase === "live" ? "live" : state.phase === "error" ? "error" : ""}`;
  const hasSession = state.phase !== "setup";
  updateShutdownAvailability(hasSession);
  if (!hasSession) activeNav = "setup";
  else if (phaseChanged || activeNav === "setup") activeNav = "dashboard";
  if (state.phase !== "live" && activeNav === "tactile") activeNav = "dashboard";
  const showTactile = state.phase === "live" && activeNav === "tactile";
  const showLogs = hasSession && activeNav === "logs";
  $('#setup-view').hidden = hasSession;
  $('#dashboard-view').hidden = !hasSession || showTactile || showLogs;
  $('#tactile-view').hidden = !showTactile;
  $('#logs-view').hidden = !showLogs;
  $('#top-session').hidden = !hasSession;
  $('#page-name').textContent = !hasSession ? t("connection") : t(showTactile ? "tactile" : showLogs ? "systemLog" : "dashboard");
  const setupNav = $('[data-nav="setup"]');
  const dashboardNav = $('[data-nav="dashboard"]');
  const tactileNav = $('[data-nav="tactile"]');
  const logsNav = $('[data-nav="logs"]');
  setupNav.disabled = hasSession;
  dashboardNav.disabled = !hasSession;
  tactileNav.disabled = state.phase !== "live";
  logsNav.disabled = !hasSession;
  $$('.nav-item').forEach(item => item.classList.toggle("active", item.dataset.nav === activeNav));
  if (state.phase === "error" && state.detail && (phaseChanged || state.detail !== lastDetail)) addLocalLog("error", state.detail);
  const connectButton = $('.primary-button', $('#setup-form'));
  if (state.phase === "setup" && !setupSubmitting && (
    phaseChanged || state.detail !== lastDetail || connectButton.disabled
  )) {
    setForm(state.config);
    $('[name="safety_confirmed"]').checked = false;
    connectButton.disabled = false;
    if (state.detail) renderSetupErrors([state.detail]);
    else clearSetupErrors();
  }
  lastDetail = state.detail || "";
  $$('.control-actions button').forEach(button => { button.disabled = state.phase !== "live"; });
}

function formatDuration(seconds = 0) {
  const total = Math.max(0, Math.floor(seconds));
  return [Math.floor(total / 3600), Math.floor(total % 3600 / 60), total % 60].map(value => String(value).padStart(2, "0")).join(":");
}

function renderHand(side, enabled, actual = [], target = [], speeds = []) {
  const panel = $(`#${side}-panel`);
  const state = $('.hand-state', panel);
  state.textContent = enabled ? t("connected") : t("disabled");
  state.classList.toggle("disabled", !enabled);
  const list = $('.joint-list', panel);
  list.innerHTML = copy[language].jointNames.map((name, index) => {
    const actualValue = Math.max(0, Math.min(1, Number(actual[index] || 0)));
    const targetValue = Math.max(0, Math.min(1, Number(target[index] || 0)));
    const speed = String(Math.round(speeds[index] || 0)).padStart(4, "0");
    return `<div class="joint-row"><span class="joint-name">${name}</span><div><div class="joint-values"><span>${actualValue.toFixed(2)}</span><b>${targetValue.toFixed(2)}</b></div><div class="joint-track"><span class="joint-actual" style="width:${actualValue * 100}%"></span><i class="joint-target" style="left:${targetValue * 100}%"></i></div></div><span class="joint-speed">${speed}</span></div>`;
  }).join("");
}

function renderSnapshot(snapshot) {
  if (!snapshot) return;
  latestSnapshot = snapshot;
  $('#session-time').textContent = formatDuration(snapshot.elapsed_seconds);
  $('#loop-rate').textContent = Number(snapshot.loop_hz || 0).toFixed(1);
  $('#speed-mode-label').textContent = t(snapshot.speed_mode);
  const running = snapshot.tracking_enabled && snapshot.motion_data_ready;
  const trackingEnabled = Boolean(snapshot.tracking_enabled);
  $('#tracking-indicator').classList.toggle("running", running);
  $('#tracking-label').textContent = running ? t("running") : trackingEnabled ? t("waitingData") : t("paused");
  $('#tracking-detail').textContent = trackingEnabled ? (snapshot.motion_data_ready ? t("ready") : t("waitingData")) : t("paused");
  $('#quest-label').textContent = snapshot.motion_data_ready ? t("ready") : t("unavailable");
  const trackingButton = $('#tracking-button');
  trackingButton.classList.toggle("stop-button", trackingEnabled);
  trackingButton.dataset.action = trackingEnabled ? "pause" : "run";
  $('span:last-child', trackingButton).textContent = t(trackingEnabled ? "stopTracking" : "run");
  $('span:first-child', trackingButton).className = trackingEnabled ? "stop-icon" : "play-icon";
  renderHand("left", snapshot.left_enabled, snapshot.left_state, snapshot.left_target, snapshot.left_speed);
  renderHand("right", snapshot.right_enabled, snapshot.right_state, snapshot.right_target, snapshot.right_speed);
}

function tactileHeatColor(value) {
  const ratio = Math.max(0, Math.min(1, Number(value || 0) / 4095));
  const stops = [
    [0, [20, 25, 33]],
    [0.2, [31, 80, 125]],
    [0.45, [27, 170, 145]],
    [0.7, [239, 193, 58]],
    [1, [240, 71, 69]]
  ];
  const upperIndex = Math.max(1, stops.findIndex(stop => ratio <= stop[0]));
  const lower = stops[upperIndex - 1];
  const upper = stops[upperIndex];
  const progress = (ratio - lower[0]) / (upper[0] - lower[0] || 1);
  const rgb = lower[1].map((channel, index) => Math.round(channel + (upper[1][index] - channel) * progress));
  return `rgb(${rgb.join(",")})`;
}

function tactilePointDescription(label, rowIndex, columnIndex, value) {
  return `${label} · ${t("row")} ${rowIndex + 1} · ${t("column")} ${columnIndex + 1} · ${t("sensorValue")} ${value}`;
}

function tactileRegionMarkup(name, values) {
  const rows = Array.isArray(values) ? values : [];
  const columns = rows.length && Array.isArray(rows[0]) ? rows[0].length : 0;
  if (!rows.length || !columns) return "";
  const label = copy[language].tactileRegions[name] || name;
  const displayRows = rows.map((row, rowIndex) => ({ row, rowIndex }));
  if (name === "palm") displayRows.reverse();
  const cells = displayRows.flatMap(({ row, rowIndex }) => row.map((rawValue, columnIndex) => {
    const value = Math.max(0, Math.min(4095, Number(rawValue) || 0));
    const description = tactilePointDescription(label, rowIndex, columnIndex, value);
    return `<span class="tactile-cell" style="--cell-color:${tactileHeatColor(value)}" data-row="${rowIndex}" data-column="${columnIndex}" data-tooltip="${escapeHtml(description)}"></span>`;
  })).join("");
  return `<section class="tactile-region" data-region="${name}"><header><strong>${escapeHtml(label)}</strong><span>${rows.length} × ${columns}</span></header><div class="tactile-matrix" style="--tactile-columns:${columns}">${cells}</div></section>`;
}

function tactileHandMarkup(side, hand) {
  const sideLabel = t(side === "left" ? "leftHand" : "rightHand");
  const regions = hand?.regions || {};
  if (hand?.error && !Object.keys(regions).length) {
    return `<article class="tactile-hand console-card" data-side="${side}"><div class="tactile-hand-heading"><span class="hand-avatar">${side === "left" ? "L" : "R"}</span><div><h2>${escapeHtml(sideLabel)}</h2><p class="tactile-error-text">${escapeHtml(hand.error)}</p></div></div><div class="tactile-empty error"><span>!</span><strong>${escapeHtml(t("tactileError"))}</strong></div></article>`;
  }
  if (!Object.keys(regions).length) {
    return `<article class="tactile-hand console-card" data-side="${side}"><div class="tactile-hand-heading"><span class="hand-avatar">${side === "left" ? "L" : "R"}</span><div><h2>${escapeHtml(sideLabel)}</h2><p>${escapeHtml(t("waitingTactile"))}</p></div></div><div class="tactile-empty"><span class="tactile-loader"></span><strong>${escapeHtml(t("tactileNoData"))}</strong></div></article>`;
  }
  const fingerGroups = tactileGroupSpecs.filter(([groupName]) => groupName !== "palm");
  const palmGroups = tactileGroupSpecs.filter(([groupName]) => groupName === "palm");
  const displayGroups = side === "left"
    ? [...fingerGroups].reverse().concat(palmGroups)
    : fingerGroups.concat(palmGroups);
  const groups = displayGroups.map(([groupName, regionNames]) => {
    const regionMarkup = regionNames.map(name => tactileRegionMarkup(name, regions[name])).filter(Boolean).join("");
    if (!regionMarkup) return "";
    return `<section class="tactile-digit ${groupName === "palm" ? "palm" : ""}"><h3>${escapeHtml(copy[language].tactileGroups[groupName])}</h3><div>${regionMarkup}</div></section>`;
  }).join("");
  return `<article class="tactile-hand console-card" data-side="${side}"><div class="tactile-hand-heading"><span class="hand-avatar">${side === "left" ? "L" : "R"}</span><div><h2>${escapeHtml(sideLabel)}</h2><p>${escapeHtml(t("tactileReady"))}</p></div><span class="hand-state">${escapeHtml(t("connected"))}</span></div><div class="tactile-regions">${groups}</div></article>`;
}

function updateTactileCells(selection, hands) {
  const renderedSides = $$('.tactile-hand', $('#tactile-hands')).map(element => element.dataset.side);
  if (renderedSides.join(",") !== selection.join(",")) return false;
  const updates = [];
  for (const side of selection) {
    const handElement = $(`.tactile-hand[data-side="${side}"]`, $('#tactile-hands'));
    const regions = hands[side]?.regions || {};
    if (!handElement || !Object.keys(regions).length) return false;
    for (const [name, rows] of Object.entries(regions)) {
      const regionElement = $(`.tactile-region[data-region="${name}"]`, handElement);
      const columns = Array.isArray(rows) && rows.length && Array.isArray(rows[0]) ? rows[0].length : 0;
      const cells = regionElement ? $$('.tactile-cell', regionElement) : [];
      const valueCount = Array.isArray(rows) ? rows.reduce((total, row) => total + (Array.isArray(row) ? row.length : 0), 0) : 0;
      if (!columns || cells.length !== valueCount) return false;
      const label = copy[language].tactileRegions[name] || name;
      cells.forEach(cell => {
        const rowIndex = Number(cell.dataset.row);
        const columnIndex = Number(cell.dataset.column);
        const value = Math.max(0, Math.min(4095, Number(rows[rowIndex]?.[columnIndex]) || 0));
        updates.push({ cell, color: tactileHeatColor(value), description: tactilePointDescription(label, rowIndex, columnIndex, value) });
      });
    }
  }
  updates.forEach(({ cell, color, description }) => {
    cell.style.setProperty("--cell-color", color);
    cell.dataset.tooltip = description;
  });
  if (activeTactileCell?.isConnected && !$('#tactile-tooltip').hidden) {
    $('#tactile-tooltip').textContent = activeTactileCell.dataset.tooltip;
  }
  return true;
}

function renderTactile(tactile = {}) {
  if (activeNav !== "tactile") return;
  const enabledSides = ["left", "right"].filter(side => latestSnapshot?.[`${side}_enabled`]);
  const selection = Array.isArray(tactile.selection) && tactile.selection.length ? tactile.selection : tactileSelection;
  tactileSelection = selection.filter(side => enabledSides.includes(side));
  if (!tactileSelection.length && enabledSides.length) {
    setTactileSelection(enabledSides);
    return;
  }
  const singleHand = enabledSides.length === 1;
  $$('#tactile-side-selector button').forEach(button => {
    const buttonSides = button.dataset.tactileSides.split(",");
    const available = buttonSides.every(side => enabledSides.includes(side)) && (!singleHand || buttonSides.length === 1);
    button.hidden = !available;
    button.classList.toggle("active", button.dataset.tactileSides === tactileSelection.join(","));
    button.setAttribute("aria-pressed", button.classList.contains("active") ? "true" : "false");
  });
  const sampleRate = Number(tactile.sample_hz || tactile.target_hz || 0);
  $('#tactile-rate').textContent = sampleRate > 0
    ? `${sampleRate.toFixed(sampleRate >= 10 ? 0 : 1)} Hz`
    : "--";

  const hands = tactile.hands || {};
  const hasError = tactileSelection.some(side => hands[side]?.error);
  const ready = tactileSelection.length > 0 && tactileSelection.every(side => Object.keys(hands[side]?.regions || {}).length > 0);
  const status = $('#tactile-status');
  status.textContent = t(hasError ? "tactileError" : ready ? "tactileReady" : "waitingTactile");
  $('.tactile-live-state .status-dot').className = `status-dot ${hasError ? "error" : ready ? "live" : ""}`;

  const fingerprint = `${language}|${tactileSelection.join(",")}|${tactileSelection.map(side => `${side}:${hands[side]?.revision || 0}:${hands[side]?.error || ""}`).join("|")}`;
  if (fingerprint === tactileFingerprint) return;
  tactileFingerprint = fingerprint;
  const container = $('#tactile-hands');
  container.classList.toggle("single", tactileSelection.length === 1);
  if (updateTactileCells(tactileSelection, hands)) return;
  activeTactileCell = null;
  $('#tactile-tooltip').hidden = true;
  container.innerHTML = tactileSelection.map(side => tactileHandMarkup(side, hands[side])).join("");
}

function captureStateLabel(state) {
  return t({
    idle: "captureIdle",
    recording: "captureRecording",
    stopping: "captureStopping",
    completed: "captureCompleted",
    stopped: "captureStopped",
    error: "captureFailed"
  }[state] || "captureIdle");
}

function renderTactileCapture(capture = { state: "idle" }) {
  const wasActive = ["recording", "stopping"].includes(latestCapture.state);
  latestCapture = capture || { state: "idle" };
  const state = latestCapture.state || "idle";
  const active = state === "recording" || state === "stopping";
  const stateElement = $('#capture-state');
  stateElement.dataset.state = state;
  $('span:last-child', stateElement).textContent = captureStateLabel(state);

  const form = $('#tactile-capture-form');
  $$('input', form).forEach(input => { input.disabled = active; });
  $('#capture-start').hidden = active;
  $('#capture-stop').hidden = !active;
  $('#capture-stop').disabled = state === "stopping";
  $$('#tactile-side-selector button').forEach(button => { button.disabled = active; });

  const tactileRate = Number(latestSnapshot?.tactile?.target_hz || latestConfig.tactile_frequency || 60);
  const mainRate = Number(latestConfig.frequency || 60);
  const maximumRate = Math.max(0.1, Math.min(60, tactileRate || 60, mainRate || 60));
  const frequencyInput = form.elements.capture_frequency;
  frequencyInput.max = String(Number(maximumRate.toFixed(1)));
  if (!active && Number(frequencyInput.value) > maximumRate) frequencyInput.value = maximumRate.toFixed(maximumRate >= 1 ? 1 : 2);
  $('#capture-frequency-hint').textContent = `${t("captureFrequencyHint")} · ≤ ${maximumRate.toFixed(maximumRate >= 10 ? 0 : 1)} Hz`;

  const elapsed = Number(latestCapture.elapsed_seconds || 0);
  const duration = Number(latestCapture.duration_seconds || form.elements.capture_duration.value || 0);
  const progress = duration > 0 ? Math.max(0, Math.min(100, elapsed / duration * 100)) : 0;
  $('#capture-progress-bar').style.width = `${state === "completed" ? 100 : progress}%`;
  $('#capture-sample-count').textContent = Number(latestCapture.sample_count || 0);
  $('#capture-progress-label').textContent = state === "idle"
    ? t("captureWaiting")
    : `${t("captureProgress")} · ${elapsed.toFixed(1)} / ${duration.toFixed(1)} s`;

  const details = [];
  if (latestCapture.path) details.push(`${t("captureSavedTo")}: ${latestCapture.path}`);
  if (Number(latestCapture.dropped_count || 0) > 0) details.push(`${t("captureDropped")}: ${latestCapture.dropped_count}`);
  $('#capture-result').textContent = details.join(" · ");
  $('#capture-result').title = latestCapture.path || "";
  $('#capture-error').textContent = latestCapture.error || captureRequestError;
  if (wasActive && !active && activeNav !== "tactile" && lastPhase === "live") stopTactileSampling();
}

async function setTactileSelection(requestedSides) {
  if (["recording", "stopping"].includes(latestCapture.state)) return;
  const enabledSides = ["left", "right"].filter(side => latestSnapshot?.[`${side}_enabled`]);
  if (!enabledSides.length) return;
  const nextSelection = enabledSides.length === 1
    ? enabledSides
    : ["left", "right"].filter(side => requestedSides.includes(side) && enabledSides.includes(side));
  tactileSelection = nextSelection;
  tactileFingerprint = "";
  const targetRate = Number(latestSnapshot?.tactile?.target_hz || 0);
  renderTactile({ sample_hz: targetRate, target_hz: targetRate, selection: nextSelection, hands: {} });
  try {
    const result = await post("/api/tactile", { sides: nextSelection });
    tactileSelection = result.sides || nextSelection;
  } catch (error) {
    addLocalLog("error", `${t("actionFailed")}: ${error.message}`);
  }
}

function stopTactileSampling() {
  if (["recording", "stopping"].includes(latestCapture.state)) return;
  if (!tactileSelection.length) return;
  tactileSelection = [];
  tactileFingerprint = "";
  post("/api/tactile", { sides: [] }).catch(error => addLocalLog("error", `${t("actionFailed")}: ${error.message}`));
}

function logEntryMarkup(item, detailed = false) {
  const level = escapeHtml(item.level || "info");
  const message = escapeHtml(item.message || "");
  const time = escapeHtml(item.time || "--:--:--");
  return detailed
    ? `<div class="log-entry detailed ${level}"><time>${time}</time><span class="log-level">${level}</span><span class="log-message">${message}</span></div>`
    : `<div class="log-entry ${level}"><span class="log-level">${level}</span><span class="log-message">${message}</span></div>`;
}

function renderLogs(messages = []) {
  latestMessages = messages;
  const visible = messages.slice(hiddenLogCount);
  const fingerprint = `${language}\n${visible.map(item => `${item.time || ""}:${item.level}:${item.message}`).join("\n")}`;
  if (fingerprint === logFingerprint) return;
  logFingerprint = fingerprint;
  const list = $('#log-list');
  const preview = $('#log-preview-list');
  $('#log-count').textContent = visible.length;
  if (!visible.length) {
    list.innerHTML = `<div class="log-empty">${t("noEvents")}</div>`;
    preview.innerHTML = `<div class="log-empty">${t("noEvents")}</div>`;
    return;
  }
  list.innerHTML = visible.map(item => logEntryMarkup(item, true)).join("");
  preview.innerHTML = visible.slice(-4).map(item => logEntryMarkup(item)).join("");
  list.scrollTop = list.scrollHeight;
}

function escapeHtml(value) {
  const node = document.createElement("span");
  node.textContent = value;
  return node.innerHTML;
}

function addLocalLog(level, message) {
  const time = new Intl.DateTimeFormat(language === "zh" ? "zh-CN" : "en-GB", {
    hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false
  }).format(new Date());
  logFingerprint = "";
  renderLogs([...latestMessages, { level, message, time }]);
}

function showCalibrationDialog(stage, detail = "") {
  const dialog = $('#confirm-dialog');
  const icon = $('.dialog-icon', dialog);
  const cancelButton = $('#dialog-cancel');
  const confirmButton = $('#dialog-confirm');
  const actions = $('#dialog-actions');
  const running = stage === "queued" || stage === "running";
  const terminal = stage === "completed" || stage === "failed";
  calibrationDialogStage = stage;
  calibrationDialogDetail = detail || "";
  dialog.dataset.flow = "calibration";
  icon.className = `dialog-icon${running ? " running" : stage === "completed" ? " success" : stage === "failed" ? " danger" : ""}`;
  icon.textContent = running ? "" : stage === "completed" ? "✓" : stage === "failed" ? "×" : "!";
  $('#dialog-title').textContent = t(
    running ? "calibrationRunningTitle" : stage === "completed" ? "calibrationCompletedTitle" : stage === "failed" ? "calibrationFailedTitle" : "calibrateForceTitle"
  );
  const copyKey = running ? "calibrationRunningCopy" : stage === "completed" ? "calibrationCompletedCopy" : stage === "failed" ? "calibrationFailedCopy" : "calibrateForceCopy";
  $('#dialog-copy').textContent = `${t(copyKey)}${stage === "failed" && detail ? ` ${detail}` : ""}`;
  cancelButton.hidden = stage !== "confirm";
  confirmButton.hidden = false;
  confirmButton.disabled = running;
  confirmButton.className = stage === "confirm" ? "secondary-button" : stage === "failed" ? "danger-button" : "run-button";
  confirmButton.textContent = terminal ? t("acknowledge") : running ? t("calibrationRunningTitle") : t("confirm");
  actions.classList.toggle("single-action", stage !== "confirm");
  if (!dialog.open) dialog.showModal();
}

function renderCalibration(calibration = { state: "idle", detail: "" }) {
  if (!["queued", "running", "completed", "failed"].includes(calibration.state)) return;
  showCalibrationDialog(calibration.state, calibration.detail || "");
}

async function beginCalibration() {
  showCalibrationDialog("running");
  addLocalLog("info", t("calibrationRequested"));
  try {
    await post("/api/action", { action: "calibrate_force" });
  } catch (error) {
    addLocalLog("error", `${t("actionFailed")}: ${error.message}`);
    showCalibrationDialog("failed", error.message);
  }
}

async function acknowledgeCalibration() {
  const button = $('#dialog-confirm');
  button.disabled = true;
  try {
    await post("/api/calibration/ack", {});
    calibrationDialogStage = "idle";
    calibrationDialogDetail = "";
    const dialog = $('#confirm-dialog');
    delete dialog.dataset.flow;
    dialog.close("confirm");
  } catch (error) {
    button.disabled = false;
    addLocalLog("error", `${t("actionFailed")}: ${error.message}`);
  }
}

async function refresh() {
  try {
    const response = await fetch("/api/state", { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const state = await response.json();
    latestConfig = state.config || latestConfig;
    if (!configured) {
      const savedLanguage = loadLanguagePreference();
      language = savedLanguage === "en" || savedLanguage === "zh"
        ? savedLanguage
        : state.language === "en" ? "en" : state.language === "zh" ? "zh" : navigator.language.toLowerCase().startsWith("zh") ? "zh" : "en";
      setForm({ ...state.config, ...loadSetupPreferences() });
      configured = true;
      applyLanguage();
    }
    renderPhase(state);
    tactileSelection = Array.isArray(state.tactile_selection) ? state.tactile_selection : tactileSelection;
    if (activeNav === "tactile" && state.snapshot) {
      latestSnapshot = state.snapshot;
      $('#session-time').textContent = formatDuration(state.snapshot.elapsed_seconds);
    } else {
      renderSnapshot(state.snapshot);
    }
    renderTactile(state.snapshot?.tactile || {});
    renderTactileCapture(state.tactile_capture || { state: "idle" });
    renderCalibration(state.calibration || { state: "idle", detail: "" });
    renderLogs(state.messages);
  } catch (error) {
    $('#connection-label').textContent = t("error");
    $('#connection-dot').className = "status-dot error";
  }
}

async function sendAction(action) {
  try {
    await post("/api/action", { action });
  }
  catch (error) { addLocalLog("error", `${t("actionFailed")}: ${error.message}`); }
}

function confirmAction(kind) {
  const dialog = $('#confirm-dialog');
  if (kind === "calibrate_force") {
    showCalibrationDialog("confirm");
    return;
  }
  delete dialog.dataset.flow;
  const titleKey = { run: "runTitle", disconnect: "disconnectTitle", quit: "quitTitle" }[kind];
  const copyKey = { run: "runCopy", disconnect: "disconnectCopy", quit: "quitCopy" }[kind];
  const dangerous = kind === "disconnect" || kind === "quit";
  const icon = $('.dialog-icon', dialog);
  icon.className = `dialog-icon${dangerous ? " danger" : ""}`;
  icon.textContent = "!";
  $('#dialog-title').textContent = t(titleKey);
  $('#dialog-copy').textContent = t(copyKey);
  $('#dialog-cancel').hidden = false;
  $('#dialog-confirm').hidden = false;
  $('#dialog-confirm').disabled = false;
  $('#dialog-confirm').textContent = t("confirm");
  $('#dialog-confirm').className = dangerous ? "danger-button" : kind === "run" ? "run-button" : "secondary-button";
  $('#dialog-actions').classList.remove("single-action");
  dialog.showModal();
  dialog.addEventListener("close", () => { if (dialog.returnValue === "confirm") sendAction(kind); }, { once: true });
}

function closeSidebar() { document.body.classList.remove("sidebar-open"); }

$('#setup-form').addEventListener("submit", async event => {
  event.preventDefault();
  const form = event.currentTarget;
  if (!validateSetupForm(form)) return;
  const button = $('.primary-button', form);
  button.disabled = true;
  setupSubmitting = true;
  try { await post("/api/setup", formPayload()); }
  catch (reason) { renderSetupErrors([reason.message]); button.disabled = false; }
  finally { setupSubmitting = false; }
});
$('#setup-form').addEventListener("input", () => {
  saveSetupPreferences();
  if (setupErrors.length) clearSetupErrors();
});

$$('[name="left_enabled"], [name="right_enabled"]').forEach(input => input.addEventListener("change", updateHandFields));
$('[name="speed_mode"]').addEventListener("change", updateSpeedFields);
$('#language-button').addEventListener("click", () => {
  language = language === "zh" ? "en" : "zh";
  try { localStorage.setItem(languagePreferenceKey, language); }
  catch (_error) { /* Language still applies when storage is unavailable. */ }
  applyLanguage();
  logFingerprint = "";
  closeSidebar();
});
$('#tracking-button').addEventListener("click", event => {
  const action = event.currentTarget.dataset.action || "run";
  if (action === "run") confirmAction("run");
  else sendAction("pause");
});
$('#speed-button').addEventListener("click", () => sendAction("speed_mode"));
$('#force-calibration-button').addEventListener("click", () => confirmAction("calibrate_force"));
$('#dialog-confirm').addEventListener("click", event => {
  if ($('#confirm-dialog').dataset.flow !== "calibration") return;
  event.preventDefault();
  if (calibrationDialogStage === "confirm") beginCalibration();
  else if (["completed", "failed"].includes(calibrationDialogStage)) acknowledgeCalibration();
});
$('#confirm-dialog').addEventListener("cancel", event => {
  if (
    event.currentTarget.dataset.flow === "calibration"
    && calibrationDialogStage !== "confirm"
  ) event.preventDefault();
});
$('#confirm-dialog').addEventListener("close", event => {
  if (
    event.currentTarget.dataset.flow === "calibration"
    && calibrationDialogStage === "confirm"
  ) {
    calibrationDialogStage = "idle";
    calibrationDialogDetail = "";
    delete event.currentTarget.dataset.flow;
  }
});
$('#disconnect-button').addEventListener("click", () => confirmAction("disconnect"));
$('#clear-log').addEventListener("click", () => {
  hiddenLogCount += latestMessages.slice(hiddenLogCount).length;
  logFingerprint = "";
  renderLogs(latestMessages);
});
$('#view-all-logs').addEventListener("click", () => $('[data-nav="logs"]').click());
$('#menu-button').addEventListener("click", () => document.body.classList.toggle("sidebar-open"));
$('#sidebar-backdrop').addEventListener("click", closeSidebar);
$$('.nav-item').forEach(button => button.addEventListener("click", () => {
  const previousNav = activeNav;
  if (button.dataset.nav === "preferences") {
    $('#preferences-dialog').showModal();
    closeSidebar();
    return;
  }
  activeNav = button.dataset.nav;
  if (activeNav === "tactile") {
    $('#dashboard-view').hidden = true;
    $('#logs-view').hidden = true;
    $('#tactile-view').hidden = false;
    $('#page-name').textContent = t("tactile");
    window.scrollTo({ top: 0, behavior: "smooth" });
    const enabledSides = ["left", "right"].filter(side => latestSnapshot?.[`${side}_enabled`]);
    const initialSelection = enabledSides.length === 1 ? enabledSides : (tactileSelection.length ? tactileSelection : enabledSides);
    setTactileSelection(initialSelection);
  } else {
    $('#tactile-view').hidden = true;
    $('#logs-view').hidden = activeNav !== "logs";
    $('#dashboard-view').hidden = lastPhase === "setup" || activeNav === "logs";
    $('#page-name').textContent = t(activeNav === "setup" ? "connection" : activeNav === "logs" ? "systemLog" : "dashboard");
    if (previousNav === "tactile") stopTactileSampling();
    if (activeNav === "logs") {
      window.scrollTo({ top: 0, behavior: "smooth" });
    } else if (activeNav === "dashboard") {
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  }
  $$('.nav-item').forEach(item => item.classList.toggle("active", item === button));
  closeSidebar();
}));
$$('#tactile-side-selector button').forEach(button => button.addEventListener("click", () => {
  setTactileSelection(button.dataset.tactileSides.split(","));
}));
$('#tactile-capture-form').addEventListener("input", () => {
  captureRequestError = "";
  $('#capture-error').textContent = "";
  saveCapturePreferences();
});
$('#tactile-capture-form').addEventListener("submit", async event => {
  event.preventDefault();
  const form = event.currentTarget;
  captureRequestError = "";
  $('#capture-error').textContent = "";
  if (!tactileSelection.length) {
    $('#capture-error').textContent = t("captureSelectHand");
    return;
  }
  if (!form.reportValidity()) return;
  saveCapturePreferences();
  $('#capture-start').disabled = true;
  try {
    const result = await post("/api/tactile/capture", {
      action: "start",
      sides: tactileSelection,
      frequency_hz: Number(form.elements.capture_frequency.value),
      duration_seconds: Number(form.elements.capture_duration.value),
      output_path: form.elements.capture_output.value.trim()
    });
    captureRequestError = "";
    renderTactileCapture(result.capture);
  } catch (error) {
    captureRequestError = error.message;
    $('#capture-error').textContent = captureRequestError;
  } finally {
    $('#capture-start').disabled = false;
  }
});
$('#capture-stop').addEventListener("click", async () => {
  captureRequestError = "";
  $('#capture-error').textContent = "";
  $('#capture-stop').disabled = true;
  try {
    const result = await post("/api/tactile/capture", { action: "stop" });
    captureRequestError = "";
    renderTactileCapture(result.capture);
  } catch (error) {
    captureRequestError = error.message;
    $('#capture-error').textContent = captureRequestError;
    $('#capture-stop').disabled = false;
  }
});
$('#tactile-hands').addEventListener("pointermove", event => {
  const cell = event.target.closest(".tactile-cell");
  const tooltip = $('#tactile-tooltip');
  if (!cell) {
    activeTactileCell = null;
    tooltip.hidden = true;
    return;
  }
  activeTactileCell = cell;
  tooltip.textContent = cell.dataset.tooltip;
  tooltip.hidden = false;
  const margin = 14;
  const width = tooltip.offsetWidth;
  const height = tooltip.offsetHeight;
  tooltip.style.left = `${Math.min(event.clientX + margin, window.innerWidth - width - 8)}px`;
  tooltip.style.top = `${Math.min(event.clientY + margin, window.innerHeight - height - 8)}px`;
});
$('#tactile-hands').addEventListener("pointerleave", () => {
  activeTactileCell = null;
  $('#tactile-tooltip').hidden = true;
});
$('#preferences-close').addEventListener("click", () => $('#preferences-dialog').close());
$('#font-size-input').addEventListener("change", event => setFontSize(event.currentTarget.value));
$('#font-decrease').addEventListener("click", () => setFontSize(preferences.fontSize - 1));
$('#font-increase').addEventListener("click", () => setFontSize(preferences.fontSize + 1));
$$('.theme-swatch').forEach(button => button.addEventListener("click", () => {
  preferences.accent = button.dataset.color;
  applyPreferences();
}));
$('#custom-color-input').addEventListener("input", event => {
  preferences.accent = event.currentTarget.value;
  applyPreferences();
});
$('#preferences-reset').addEventListener("click", () => {
  preferences = { ...defaultPreferences };
  applyPreferences();
});
$('#shutdown-button').addEventListener("click", () => {
  if (lastPhase !== "setup") return;
  closeSidebar();
  confirmAction("quit");
});

loadPreferences();
loadCapturePreferences();
applyLanguage();
renderLogs([]);
async function runRefreshLoop() {
  await refresh();
  const configuredTactileRate = Math.max(1, Math.min(60, Number(latestSnapshot?.tactile?.target_hz || 10)));
  window.setTimeout(runRefreshLoop, activeNav === "tactile" ? 1000 / configuredTactileRate : 250);
}
runRefreshLoop();
