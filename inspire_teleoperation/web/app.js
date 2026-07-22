const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

const copy = {
  zh: {
    workspace: "工作区", connection: "设备接入", dashboard: "实时控制", systemLog: "系统日志", systemState: "系统状态", localConsole: "本地控制台", preferences: "界面设置", appearance: "外观",
    setupEyebrow: "设备接入", setupTitle: "建立遥操作连接", setupLead: "配置设备与控制策略，确认安全后启动会话。", stepConfigure: "配置", stepConnect: "连接", stepControl: "控制",
    devices: "设备", devicesHelp: "选择要控制的灵巧手并确认网络地址", oneRequired: "至少启用一台", leftHand: "左手", rightHand: "右手", host: "主机地址", deviceId: "设备 ID",
    controlParams: "控制策略", controlHelp: "设置通信频率与关节运动速度", port: "Modbus 端口", timeout: "请求超时", speedMode: "速度模式", adaptive: "自适应 2.0", adaptive_v2: "自适应 2.0", adaptive_v1: "自适应 1.0", fixed: "固定速度", fixedSpeed: "固定速度", fixedSpeedHint: "仅固定模式生效", questRate: "Quest 采样率", handRate: "手部指令率",
    advancedOptions: "会话选项", advancedHint: "跟踪启动、标记显示与断开行为", startNow: "连接后立即跟踪", startNowHelp: "工作区清空时使用", hideMarkers: "隐藏 Quest 标记", hideMarkersHelp: "不影响数据采集", openExit: "断开设备时张手", openExitHelp: "安装工具时保持关闭",
    safetyCheck: "连接前检查", safetyIntro: "设备可能在连接后立即运动", checkWorkspace: "设备固定与线缆状态已检查", checkNetwork: "设备地址与网络已确认", checkSpeed: "已选择合适的速度策略", safetyConfirm: "我确认工作区内没有人员、工具或易损物体", safetyDetail: "此确认是建立设备连接的必要条件。", connect: "连接设备", localOnly: "仅在本机建立连接",
    liveEyebrow: "实时遥操作", dashboardTitle: "运行控制台", dashboardLead: "监控连接、数据链路与关节状态。", session: "会话", teleopStatus: "遥操作状态", questData: "Quest 数据", loopRate: "主循环频率", safetyTitle: "进入工作区前", safetyPause: "请先停止跟踪", run: "开始跟踪", stopTracking: "停止跟踪", switchSpeed: "切换速度", disconnect: "断开设备",
    joint: "关节", position: "实际 / 目标", speed: "速度", sixJoints: "6 个关节", latestEvents: "最新运行事件", clear: "清空", level: "级别", event: "事件", noEvents: "暂无运行日志",
    cancel: "取消", confirm: "确认", waitingSetup: "等待配置", connecting: "正在连接", disconnecting: "正在断开", live: "已连接", stopping: "正在停止", stopped: "已停止", error: "连接错误", paused: "跟踪已停止", running: "正在跟踪", waitingData: "等待手部数据", ready: "数据就绪", unavailable: "无数据", connected: "已连接", enabled: "已启用", disabled: "未启用",
    fontSize: "界面字号", fontSizeHelp: "输入精确字号，整个控制台会按比例调整。", themeColor: "主题色", themeColorHelp: "选择预设颜色，或使用自定义颜色。", customColor: "自定义", resetAppearance: "恢复默认", shutdownService: "关闭控制服务",
    setupFailed: "无法提交配置", enableOneHandError: "请至少启用一只手。", safetyConfirmationError: "请勾选工作区安全确认。", invalidSettingsError: "请检查高亮的设备地址或控制参数。", actionFailed: "操作失败", runTitle: "开始手部跟踪？", runCopy: "确认双手工作区已经清空。开始后，Quest 手势将实时驱动灵巧手。", disconnectTitle: "断开当前设备？", disconnectCopy: "跟踪将停止，Modbus 与 Quest 会话将关闭。随后可以立即修改设备接入设置并重新连接。", quitTitle: "关闭控制服务？", quitCopy: "所有设备会断开，当前页面也将停止提供服务。下次使用需要重新启动程序。", jointNames: ["小指", "无名指", "中指", "食指", "拇指", "旋转"]
  },
  en: {
    workspace: "Workspace", connection: "Device setup", dashboard: "Live control", systemLog: "System log", systemState: "System state", localConsole: "Local console", preferences: "Interface settings", appearance: "Appearance",
    setupEyebrow: "Device setup", setupTitle: "Start a teleoperation session", setupLead: "Configure devices and control behavior, then complete the safety check.", stepConfigure: "Configure", stepConnect: "Connect", stepControl: "Control",
    devices: "Devices", devicesHelp: "Choose each dexterous hand and verify its network address", oneRequired: "One required", leftHand: "Left hand", rightHand: "Right hand", host: "Host address", deviceId: "Device ID",
    controlParams: "Control strategy", controlHelp: "Set communication rates and joint motion speed", port: "Modbus port", timeout: "Request timeout", speedMode: "Speed mode", adaptive: "Adaptive 2.0", adaptive_v2: "Adaptive 2.0", adaptive_v1: "Adaptive 1.0", fixed: "Fixed speed", fixedSpeed: "Fixed speed", fixedSpeedHint: "Used in fixed mode only", questRate: "Quest polling", handRate: "Hand command rate",
    advancedOptions: "Session options", advancedHint: "Tracking start, marker display, and disconnect behavior", startNow: "Track immediately", startNowHelp: "Use only in a clear workspace", hideMarkers: "Hide Quest markers", hideMarkersHelp: "Capture is unaffected", openExit: "Open hands on disconnect", openExitHelp: "Keep off when tools are attached",
    safetyCheck: "Preflight check", safetyIntro: "Devices may move immediately after connection", checkWorkspace: "Device mounting and cables checked", checkNetwork: "Device addresses and network verified", checkSpeed: "Appropriate speed strategy selected", safetyConfirm: "I confirm the workspaces are clear of people, tools, and fragile objects", safetyDetail: "This confirmation is required to establish a connection.", connect: "Connect devices", localOnly: "Connection stays on this machine",
    liveEyebrow: "Live teleoperation", dashboardTitle: "Operations console", dashboardLead: "Monitor connections, data flow, and joint state.", session: "Session", teleopStatus: "Teleop status", questData: "Quest data", loopRate: "Main loop rate", safetyTitle: "Before entering workspace", safetyPause: "Stop tracking first", run: "Start tracking", stopTracking: "Stop tracking", switchSpeed: "Switch speed", disconnect: "Disconnect devices",
    joint: "Joint", position: "Actual / target", speed: "Speed", sixJoints: "6 joints", latestEvents: "Latest runtime events", clear: "Clear", level: "Level", event: "Event", noEvents: "No runtime events",
    cancel: "Cancel", confirm: "Confirm", waitingSetup: "Awaiting setup", connecting: "Connecting", disconnecting: "Disconnecting", live: "Connected", stopping: "Stopping", stopped: "Stopped", error: "Connection error", paused: "Tracking stopped", running: "Tracking", waitingData: "Waiting for hand data", ready: "Data ready", unavailable: "Unavailable", connected: "Connected", enabled: "Enabled", disabled: "Disabled",
    fontSize: "Interface font size", fontSizeHelp: "Enter an exact size to scale console typography.", themeColor: "Theme color", themeColorHelp: "Choose a preset or use a custom color.", customColor: "Custom", resetAppearance: "Reset appearance", shutdownService: "Stop control service",
    setupFailed: "Could not submit configuration", enableOneHandError: "Enable at least one hand.", safetyConfirmationError: "Confirm that the hand workspace is clear.", invalidSettingsError: "Check the highlighted device addresses or control settings.", actionFailed: "Action failed", runTitle: "Start hand tracking?", runCopy: "Confirm both hand workspaces are clear. Quest gestures will drive the dexterous hands in real time.", disconnectTitle: "Disconnect current devices?", disconnectCopy: "Tracking, Modbus, and the Quest session will stop. You can then edit device settings and reconnect immediately.", quitTitle: "Stop the control service?", quitCopy: "All devices will disconnect and this page will stop responding. Restart the program to use it again.", jointNames: ["Little", "Ring", "Middle", "Index", "Thumb", "Rotate"]
  }
};

let language = "zh";
let configured = false;
let lastPhase = "setup";
let lastDetail = "";
let hiddenLogCount = 0;
let logFingerprint = "";
let latestSnapshot = null;
let activeNav = "setup";
let setupSubmitting = false;
let setupErrors = [];
const preferenceKey = "inspire-console-appearance-v1";
const defaultPreferences = { fontSize: 12, accent: "#a7f432" };
let preferences = { ...defaultPreferences };

function t(key) { return copy[language][key] ?? key; }

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

function applyLanguage() {
  document.documentElement.lang = language === "zh" ? "zh-CN" : "en";
  $$('[data-i18n]').forEach(element => { element.textContent = t(element.dataset.i18n); });
  $('#language-button').textContent = language === "zh" ? "EN" : "中";
  $('#page-name').textContent = lastPhase === "setup" ? t("connection") : t("dashboard");
  updateHandFields();
  if (latestSnapshot) renderSnapshot(latestSnapshot);
  if (setupErrors.length) renderSetupErrors(setupErrors);
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
    speed_mode: value("speed_mode"), frequency: Number(value("frequency")), hand_frequency: Number(value("hand_frequency")),
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
  const showDashboard = state.phase !== "setup";
  $('#setup-view').hidden = showDashboard;
  $('#dashboard-view').hidden = !showDashboard;
  $('#top-session').hidden = !showDashboard;
  $('#page-name').textContent = showDashboard ? t("dashboard") : t("connection");
  const setupNav = $('[data-nav="setup"]');
  const dashboardNav = $('[data-nav="dashboard"]');
  const logsNav = $('[data-nav="logs"]');
  setupNav.disabled = showDashboard;
  dashboardNav.disabled = !showDashboard;
  logsNav.disabled = !showDashboard;
  if (!showDashboard) activeNav = "setup";
  else if (phaseChanged || activeNav === "setup") activeNav = "dashboard";
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

function renderLogs(messages) {
  const visible = messages.slice(hiddenLogCount);
  const fingerprint = `${language}\n${visible.map(item => `${item.level}:${item.message}`).join("\n")}`;
  if (fingerprint === logFingerprint) return;
  logFingerprint = fingerprint;
  const list = $('#log-list');
  if (!visible.length) {
    list.innerHTML = `<div class="log-empty">${t("noEvents")}</div>`;
    return;
  }
  list.innerHTML = visible.map(item => `<div class="log-entry ${escapeHtml(item.level)}"><span class="log-level">${escapeHtml(item.level)}</span><span>${escapeHtml(item.message)}</span></div>`).join("");
  list.scrollTop = list.scrollHeight;
}

function escapeHtml(value) {
  const node = document.createElement("span");
  node.textContent = value;
  return node.innerHTML;
}

function addLocalLog(level, message) {
  const list = $('#log-list');
  if ($('.log-empty', list)) list.innerHTML = "";
  list.insertAdjacentHTML("beforeend", `<div class="log-entry ${escapeHtml(level)}"><span class="log-level">${escapeHtml(level)}</span><span>${escapeHtml(message)}</span></div>`);
}

async function refresh() {
  try {
    const response = await fetch("/api/state", { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const state = await response.json();
    if (!configured) {
      language = state.language === "en" ? "en" : state.language === "zh" ? "zh" : navigator.language.toLowerCase().startsWith("zh") ? "zh" : "en";
      setForm(state.config);
      configured = true;
      applyLanguage();
    }
    renderPhase(state);
    renderSnapshot(state.snapshot);
    renderLogs(state.messages);
  } catch (error) {
    $('#connection-label').textContent = t("error");
    $('#connection-dot').className = "status-dot error";
  }
}

async function sendAction(action) {
  try { await post("/api/action", { action }); }
  catch (error) { addLocalLog("error", `${t("actionFailed")}: ${error.message}`); }
}

function confirmAction(kind) {
  const dialog = $('#confirm-dialog');
  const titleKey = { run: "runTitle", disconnect: "disconnectTitle", quit: "quitTitle" }[kind];
  const copyKey = { run: "runCopy", disconnect: "disconnectCopy", quit: "quitCopy" }[kind];
  $('#dialog-title').textContent = t(titleKey);
  $('#dialog-copy').textContent = t(copyKey);
  $('.dialog-icon', dialog).classList.toggle("danger", kind !== "run");
  $('#dialog-confirm').className = kind === "run" ? "run-button" : "danger-button";
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
  if (setupErrors.length) clearSetupErrors();
});

$$('[name="left_enabled"], [name="right_enabled"]').forEach(input => input.addEventListener("change", updateHandFields));
$('[name="speed_mode"]').addEventListener("change", updateSpeedFields);
$('#language-button').addEventListener("click", () => { language = language === "zh" ? "en" : "zh"; applyLanguage(); logFingerprint = ""; closeSidebar(); });
$('#tracking-button').addEventListener("click", event => {
  const action = event.currentTarget.dataset.action || "run";
  if (action === "run") confirmAction("run");
  else sendAction("pause");
});
$('#speed-button').addEventListener("click", () => sendAction("speed_mode"));
$('#disconnect-button').addEventListener("click", () => confirmAction("disconnect"));
$('#clear-log').addEventListener("click", () => { hiddenLogCount += $$('.log-entry', $('#log-list')).length; logFingerprint = ""; $('#log-list').innerHTML = `<div class="log-empty">${t("noEvents")}</div>`; });
$('#menu-button').addEventListener("click", () => document.body.classList.toggle("sidebar-open"));
$('#sidebar-backdrop').addEventListener("click", closeSidebar);
$$('.nav-item').forEach(button => button.addEventListener("click", () => {
  if (button.dataset.nav === "preferences") {
    $('#preferences-dialog').showModal();
    closeSidebar();
    return;
  } else if (button.dataset.nav === "logs") {
    $('#log-panel').scrollIntoView({ behavior: "smooth", block: "start" });
  } else if (button.dataset.nav === "dashboard") {
    window.scrollTo({ top: 0, behavior: "smooth" });
  }
  activeNav = button.dataset.nav;
  $$('.nav-item').forEach(item => item.classList.toggle("active", item === button));
  closeSidebar();
}));
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
  $('#preferences-dialog').close();
  confirmAction("quit");
});

loadPreferences();
applyLanguage();
renderLogs([]);
refresh();
setInterval(refresh, 250);
