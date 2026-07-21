const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

const copy = {
  zh: { setupEyebrow: "安全连接向导", setupTitle: "连接你的灵巧手", setupLead: "确认设备地址与控制参数。只有完成安全确认后，系统才会建立 Modbus 连接。", stepConfigure: "配置", stepConnect: "连接", stepControl: "控制", devices: "设备", devicesHelp: "启用需要控制的手并检查网络地址", leftHand: "左手", rightHand: "右手", host: "主机地址", deviceId: "设备 ID", controlParams: "控制参数", controlHelp: "建议先使用保守速度完成空载验证", port: "Modbus 端口", timeout: "请求超时（秒）", speedMode: "速度模式", adaptive: "自适应 2.0", adaptive_v2: "自适应 2.0", adaptive_v1: "自适应 1.0", fixed: "固定", fixedSpeed: "固定速度", questRate: "Quest 采样率", handRate: "手部指令率", startNow: "连接后立即跟踪", startNowHelp: "仅在工作区完全清空时启用", hideMarkers: "隐藏 Quest 手部标记", hideMarkersHelp: "不影响关节数据采集", openExit: "退出时张手", openExitHelp: "安装工具时请保持关闭", safetyConfirm: "我已确认双手工作区内没有人员、工具或易损物体", safetyDetail: "连接后，任何已启用的手都可能立即保持或执行目标位置。", connect: "确认并连接", liveEyebrow: "实时遥操作", dashboard: "控制台", session: "会话", teleopStatus: "遥操作状态", questData: "Quest 数据", loopRate: "主循环频率", liveRefresh: "实时刷新", clickSwitch: "可在下方切换", safetyTitle: "安全状态", safetyPause: "进入工作区前请先暂停遥操作", pause: "暂停", run: "开始跟踪", switchSpeed: "切换速度", shutdown: "安全退出", joint: "关节", position: "实际 / 目标", speed: "速度", systemLog: "系统日志", clear: "清空显示", cancel: "取消", confirm: "确认", waitingSetup: "等待配置", connecting: "正在连接", live: "已连接", stopping: "正在停止", stopped: "已停止", error: "连接错误", paused: "已暂停", running: "正在跟踪", waitingData: "等待手部数据", ready: "数据就绪", unavailable: "无数据", connected: "已连接", disabled: "未启用", setupFailed: "无法提交配置", actionFailed: "操作失败", runTitle: "启用手部跟踪？", runCopy: "请再次确认双手工作区已经清空。启用后，Quest 手势将实时驱动灵巧手。", quitTitle: "安全退出会话？", quitCopy: "系统将暂停跟踪并关闭 Modbus 连接。只有启用了“退出时张手”选项，关节才会在退出时移动。", jointNames: ["小指", "无名指", "中指", "食指", "拇指", "旋转"] },
  en: { setupEyebrow: "Safe connection", setupTitle: "Connect your dexterous hands", setupLead: "Review device addresses and control parameters. Modbus connections start only after safety confirmation.", stepConfigure: "Configure", stepConnect: "Connect", stepControl: "Control", devices: "Devices", devicesHelp: "Enable each hand and verify its network address", leftHand: "Left hand", rightHand: "Right hand", host: "Host address", deviceId: "Device ID", controlParams: "Control parameters", controlHelp: "Start conservatively and validate without a payload", port: "Modbus port", timeout: "Request timeout (s)", speedMode: "Speed mode", adaptive: "Adaptive 2.0", adaptive_v2: "Adaptive 2.0", adaptive_v1: "Adaptive 1.0", fixed: "Fixed", fixedSpeed: "Fixed speed", questRate: "Quest polling", handRate: "Hand command rate", startNow: "Track immediately after connection", startNowHelp: "Use only when the workspace is completely clear", hideMarkers: "Hide Quest hand markers", hideMarkersHelp: "Landmark capture is unaffected", openExit: "Open hands on exit", openExitHelp: "Keep off when a tool is attached", safetyConfirm: "I confirm both hand workspaces are clear of people, tools, and fragile objects", safetyDetail: "After connection, any enabled hand may immediately hold or execute a target position.", connect: "Confirm and connect", liveEyebrow: "Live teleoperation", dashboard: "Control center", session: "Session", teleopStatus: "Teleop status", questData: "Quest data", loopRate: "Main loop rate", liveRefresh: "Live refresh", clickSwitch: "Switch below", safetyTitle: "Safety status", safetyPause: "Pause teleoperation before entering the workspace", pause: "Pause", run: "Start tracking", switchSpeed: "Switch speed", shutdown: "Safe shutdown", joint: "Joint", position: "Actual / target", speed: "Speed", systemLog: "System log", clear: "Clear view", cancel: "Cancel", confirm: "Confirm", waitingSetup: "Awaiting setup", connecting: "Connecting", live: "Connected", stopping: "Stopping", stopped: "Stopped", error: "Connection error", paused: "Paused", running: "Tracking", waitingData: "Waiting for hand data", ready: "Data ready", unavailable: "Unavailable", connected: "Connected", disabled: "Disabled", setupFailed: "Could not submit configuration", actionFailed: "Action failed", runTitle: "Enable hand tracking?", runCopy: "Confirm the hand workspaces are clear. Quest gestures will drive the dexterous hands in real time.", quitTitle: "Safely end this session?", quitCopy: "Tracking will pause and Modbus connections will close. Joints move on exit only if “open hands on exit” was enabled.", jointNames: ["Little", "Ring", "Middle", "Index", "Thumb", "Rotate"] }
};

let language = "zh";
let configured = false;
let lastPhase = "setup";
let hiddenLogCount = 0;
let logFingerprint = "";

function t(key) { return copy[language][key] ?? key; }
function applyLanguage() {
  document.documentElement.lang = language === "zh" ? "zh-CN" : "en";
  $$('[data-i18n]').forEach(el => { el.textContent = t(el.dataset.i18n); });
  $('#language-button').textContent = language === "zh" ? "EN" : "中";
}

function setForm(config) {
  Object.entries(config).forEach(([name, value]) => {
    const field = $(`[name="${name}"]`);
    if (!field) return;
    if (field.type === "checkbox") field.checked = value;
    else field.value = value;
  });
  updateHandFields();
}

function updateHandFields() {
  ["left", "right"].forEach(side => {
    const enabled = $(`[name="${side}_enabled"]`).checked;
    const box = $(`#${side}-config`);
    box.classList.toggle("disabled", !enabled);
    $$(`input:not([name="${side}_enabled"])`, box).forEach(input => { input.disabled = !enabled; });
  });
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

async function post(path, payload) {
  const response = await fetch(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
  const body = await response.json();
  if (!response.ok) throw new Error(body.error || `HTTP ${response.status}`);
  return body;
}

function phaseLabel(phase) { return t({ setup: "waitingSetup", connecting: "connecting", live: "live", stopping: "stopping", stopped: "stopped", error: "error" }[phase] || phase); }
function renderPhase(state) {
  lastPhase = state.phase;
  $('#connection-label').textContent = phaseLabel(state.phase);
  $('#connection-dot').className = `status-dot ${state.phase === "live" ? "live" : state.phase === "error" ? "error" : ""}`;
  const showDashboard = state.phase !== "setup";
  $('#setup-view').hidden = showDashboard;
  $('#dashboard-view').hidden = !showDashboard;
  if (state.phase === "error" && state.detail) addLocalLog("error", state.detail);
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
    const a = Math.max(0, Math.min(1, Number(actual[index] || 0)));
    const d = Math.max(0, Math.min(1, Number(target[index] || 0)));
    return `<div class="joint-row"><span class="joint-name">${name}</span><div><div class="joint-values"><span>${a.toFixed(2)}</span><b>${d.toFixed(2)}</b></div><div class="joint-track"><span class="joint-actual" style="width:${a * 100}%"></span><i class="joint-target" style="left:${d * 100}%"></i></div></div><span class="joint-speed">${String(Math.round(speeds[index] || 0)).padStart(4, "0")}</span></div>`;
  }).join("");
}

function renderSnapshot(snapshot) {
  if (!snapshot) return;
  $('#session-time').textContent = formatDuration(snapshot.elapsed_seconds);
  $('#loop-rate').textContent = Number(snapshot.loop_hz).toFixed(1);
  $('#speed-mode-label').textContent = t(snapshot.speed_mode);
  const running = snapshot.tracking_enabled && snapshot.motion_data_ready;
  $('#tracking-indicator').classList.toggle("running", running);
  $('#tracking-label').textContent = running ? t("running") : snapshot.tracking_enabled ? t("waitingData") : t("paused");
  $('#tracking-detail').textContent = snapshot.tracking_enabled ? (snapshot.motion_data_ready ? t("ready") : t("waitingData")) : t("paused");
  $('#quest-label').textContent = snapshot.motion_data_ready ? t("ready") : t("unavailable");
  renderHand("left", snapshot.left_enabled, snapshot.left_state, snapshot.left_target, snapshot.left_speed);
  renderHand("right", snapshot.right_enabled, snapshot.right_state, snapshot.right_target, snapshot.right_speed);
}

function renderLogs(messages) {
  const visible = messages.slice(hiddenLogCount);
  const fingerprint = visible.map(item => `${item.level}:${item.message}`).join("\n");
  if (fingerprint === logFingerprint) return;
  logFingerprint = fingerprint;
  const list = $('#log-list');
  list.innerHTML = visible.map(item => `<div class="log-entry ${item.level}">${escapeHtml(item.message)}</div>`).join("");
  list.scrollTop = list.scrollHeight;
}
function escapeHtml(value) { const node = document.createElement("span"); node.textContent = value; return node.innerHTML; }
function addLocalLog(level, message) { const list = $('#log-list'); list.insertAdjacentHTML("beforeend", `<div class="log-entry ${level}">${escapeHtml(message)}</div>`); }

async function refresh() {
  try {
    const response = await fetch("/api/state", { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const state = await response.json();
    if (!configured) { language = state.language === "en" ? "en" : state.language === "zh" ? "zh" : navigator.language.toLowerCase().startsWith("zh") ? "zh" : "en"; applyLanguage(); setForm(state.config); configured = true; }
    renderPhase(state); renderSnapshot(state.snapshot); renderLogs(state.messages);
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
  $('#dialog-title').textContent = t(kind === "run" ? "runTitle" : "quitTitle");
  $('#dialog-copy').textContent = t(kind === "run" ? "runCopy" : "quitCopy");
  $('.dialog-icon', dialog).classList.toggle("danger", kind === "quit");
  $('#dialog-confirm').className = kind === "quit" ? "danger-button" : "run-button";
  dialog.showModal();
  dialog.addEventListener("close", () => { if (dialog.returnValue === "confirm") sendAction(kind); }, { once: true });
}

$('#setup-form').addEventListener("submit", async event => {
  event.preventDefault();
  const button = $('.primary-button', event.currentTarget);
  const error = $('#setup-error');
  error.textContent = ""; button.disabled = true;
  try { await post("/api/setup", formPayload()); }
  catch (reason) { error.textContent = `${t("setupFailed")}: ${reason.message}`; button.disabled = false; }
});
$$('[name="left_enabled"], [name="right_enabled"]').forEach(input => input.addEventListener("change", updateHandFields));
$('#language-button').addEventListener("click", () => { language = language === "zh" ? "en" : "zh"; applyLanguage(); if (lastPhase !== "setup") refresh(); });
$('#run-button').addEventListener("click", () => confirmAction("run"));
$('#pause-button').addEventListener("click", () => sendAction("pause"));
$('#speed-button').addEventListener("click", () => sendAction("speed_mode"));
$('#quit-button').addEventListener("click", () => confirmAction("quit"));
$('#clear-log').addEventListener("click", () => { hiddenLogCount += $$('.log-entry', $('#log-list')).length; logFingerprint = ""; $('#log-list').innerHTML = ""; });

applyLanguage(); refresh(); setInterval(refresh, 250);
