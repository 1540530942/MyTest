const elements = {
  statusBadge: document.getElementById("statusBadge"),
  singleButton: document.getElementById("singleButton"),
  continuousButton: document.getElementById("continuousButton"),
  intervalSelect: document.getElementById("intervalSelect"),
  gpioSelect: document.getElementById("gpioSelect"),
  refreshButton: document.getElementById("refreshButton"),
  cameraImage: document.getElementById("cameraImage"),
  emptyState: document.getElementById("emptyState"),
  deviceId: document.getElementById("deviceId"),
  frameId: document.getElementById("frameId"),
  updatedAt: document.getElementById("updatedAt"),
  contentLength: document.getElementById("contentLength"),
  gpioState: document.getElementById("gpioState"),
  gpioSampledAt: document.getElementById("gpioSampledAt"),
  taskState: document.getElementById("taskState"),
};

let control = { task: null };
let lastUpdatedAt = 0;

function formatTime(seconds) {
  if (!seconds) return "-";
  return new Date(seconds * 1000).toLocaleString();
}

function setStatus(text, mode) {
  elements.statusBadge.textContent = text;
  elements.statusBadge.dataset.mode = mode;
}

async function getJson(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) {
    throw new Error(`${url} ${response.status}`);
  }
  return response.json();
}

function apiPath(path) {
  return `api/${path}`;
}

function selectedGpio() {
  return Number(elements.gpioSelect.value || 26);
}

function formatGpio(gpioMeta) {
  const fallbackGpio = selectedGpio();
  if (!gpioMeta) return `GPIO${fallbackGpio} 未采样`;
  const gpio = gpioMeta.gpio === 0 || gpioMeta.gpio ? `GPIO${gpioMeta.gpio}` : `GPIO${fallbackGpio}`;
  if (!gpioMeta.available) return `${gpio} 未采样`;
  const level = gpioMeta.level === "hi" ? "高电平" : gpioMeta.level === "lo" ? "低电平" : gpioMeta.level || "-";
  const value = gpioMeta.value === 0 || gpioMeta.value === 1 ? ` (${gpioMeta.value})` : "";
  return `${gpio} ${level}${value}`;
}

function applyGpioMeta(gpioMeta) {
  elements.gpioState.textContent = formatGpio(gpioMeta);
  elements.gpioSampledAt.textContent = gpioMeta && gpioMeta.sampled_at ? formatTime(gpioMeta.sampled_at) : "-";
}

async function loadControl() {
  control = await getJson(apiPath("control"));
  const task = control.task;
  if (task) {
    const total = task.max_frames ? task.max_frames : "∞";
    elements.taskState.textContent = `${task.mode} ${task.status} ${task.uploaded_frames}/${total}`;
    const activeContinuous = task.mode === "continuous" && !["complete", "expired", "stopped"].includes(task.status);
    elements.continuousButton.textContent = activeContinuous ? "停止持续发送" : "持续发送";
    elements.continuousButton.classList.toggle("danger", activeContinuous);
  } else {
    elements.taskState.textContent = "-";
    elements.continuousButton.textContent = "持续发送";
    elements.continuousButton.classList.remove("danger");
  }
}

async function createTask(mode, extra = {}) {
  applyGpioMeta({ gpio: selectedGpio(), available: false, sampled_at: 0 });
  const result = await getJson(apiPath("capture"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mode, query_gpio: selectedGpio(), ...extra }),
  });
  await loadControl();
  if (mode === "single" && result.task && result.task.id) {
    await waitForTaskFrame(result.task.id);
  } else {
    await refreshLatest(false);
  }
}

async function stopTask() {
  await getJson(apiPath("stop"), { method: "POST" });
  await loadControl();
}

async function refreshLatest(forceImage) {
  try {
    const [meta, gpioMeta] = await Promise.all([
      getJson(apiPath("latest")),
      getJson(apiPath("gpio")).catch(() => null),
    ]);
    if (!meta.has_image) {
      setStatus(control.task ? "等待上传" : "空闲", control.task ? "warn" : "idle");
      elements.emptyState.hidden = false;
      elements.cameraImage.hidden = true;
      applyGpioMeta(gpioMeta || meta.gpio || { gpio: selectedGpio(), available: false, sampled_at: 0 });
      return meta;
    }

    elements.deviceId.textContent = meta.device_id || "-";
    elements.frameId.textContent = meta.frame_id || "-";
    elements.updatedAt.textContent = formatTime(meta.updated_at);
    elements.contentLength.textContent = meta.content_length ? `${Math.round(meta.content_length / 1024)} KB` : "-";
    applyGpioMeta(gpioMeta || meta.gpio || meta.led1);
    elements.emptyState.hidden = true;
    elements.cameraImage.hidden = false;

    if (forceImage || meta.updated_at !== lastUpdatedAt) {
      lastUpdatedAt = meta.updated_at;
      elements.cameraImage.src = `${apiPath("latest.jpg")}?t=${Date.now()}`;
    }

    const ageSeconds = Date.now() / 1000 - Number(meta.updated_at || 0);
    setStatus(ageSeconds < 5 ? "实时" : `${Math.round(ageSeconds)} 秒前`, ageSeconds < 5 ? "ok" : "warn");
    return meta;
  } catch (error) {
    setStatus("连接失败", "bad");
    return null;
  }
}

async function waitForTaskFrame(taskId) {
  const deadline = Date.now() + 12000;
  while (Date.now() < deadline) {
    const meta = await refreshLatest(false);
    if (meta && meta.task_id === taskId) return;
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
}

elements.singleButton.addEventListener("click", () => createTask("single"));
elements.continuousButton.addEventListener("click", async () => {
  const task = control.task;
  const activeContinuous = task && task.mode === "continuous" && !["complete", "expired", "stopped"].includes(task.status);
  if (activeContinuous) {
    await stopTask();
    return;
  }
  await createTask("continuous", { interval_ms: Number(elements.intervalSelect.value) });
});
elements.refreshButton.addEventListener("click", () => refreshLatest(true));

async function tick() {
  try {
    await loadControl();
  } catch (error) {
    setStatus("控制失败", "bad");
  }
  await refreshLatest(false);
}

tick();
setInterval(tick, 1000);
