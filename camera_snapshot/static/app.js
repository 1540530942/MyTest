const elements = {
  statusBadge: document.getElementById("statusBadge"),
  singleButton: document.getElementById("singleButton"),
  continuousButton: document.getElementById("continuousButton"),
  intervalSelect: document.getElementById("intervalSelect"),
  refreshButton: document.getElementById("refreshButton"),
  cameraImage: document.getElementById("cameraImage"),
  emptyState: document.getElementById("emptyState"),
  deviceId: document.getElementById("deviceId"),
  frameId: document.getElementById("frameId"),
  updatedAt: document.getElementById("updatedAt"),
  contentLength: document.getElementById("contentLength"),
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

async function loadControl() {
  control = await getJson("/api/control");
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
  await getJson("/api/capture", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mode, ...extra }),
  });
  await loadControl();
  await refreshLatest(false);
}

async function stopTask() {
  await getJson("/api/stop", { method: "POST" });
  await loadControl();
}

async function refreshLatest(forceImage) {
  try {
    const meta = await getJson("/api/latest");
    if (!meta.has_image) {
      setStatus(control.task ? "等待上传" : "空闲", control.task ? "warn" : "idle");
      elements.emptyState.hidden = false;
      elements.cameraImage.hidden = true;
      return;
    }

    elements.deviceId.textContent = meta.device_id || "-";
    elements.frameId.textContent = meta.frame_id || "-";
    elements.updatedAt.textContent = formatTime(meta.updated_at);
    elements.contentLength.textContent = meta.content_length ? `${Math.round(meta.content_length / 1024)} KB` : "-";
    elements.emptyState.hidden = true;
    elements.cameraImage.hidden = false;

    if (forceImage || meta.updated_at !== lastUpdatedAt) {
      lastUpdatedAt = meta.updated_at;
      elements.cameraImage.src = `/api/latest.jpg?t=${Date.now()}`;
    }

    const ageSeconds = Date.now() / 1000 - Number(meta.updated_at || 0);
    setStatus(ageSeconds < 5 ? "实时" : `${Math.round(ageSeconds)} 秒前`, ageSeconds < 5 ? "ok" : "warn");
  } catch (error) {
    setStatus("连接失败", "bad");
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
