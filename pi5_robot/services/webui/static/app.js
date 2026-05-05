const $ = (selector) => document.querySelector(selector);
const API_PREFIX = (() => {
  const path = window.location.pathname;
  if (path === "/robot" || path.startsWith("/robot/")) {
    return "/robot";
  }
  return "";
})();

async function api(path, options = {}) {
  const response = await fetch(`${API_PREFIX}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || response.statusText);
  }
  return data;
}

function renderJson(node, data) {
  node.textContent = JSON.stringify(data, null, 2);
}

async function refreshState() {
  const state = await api("/api/robot/state");
  $("#battery").textContent = `${state.battery}%`;
  $("#front").textContent = `${state.obstacle.front_cm} cm`;
  $("#pose").textContent = `${state.pose.x.toFixed(2)}, ${state.pose.y.toFixed(2)}, ${state.pose.theta.toFixed(0)}°`;
  $("#servo").textContent = `${state.servo.pan_deg.toFixed(0)}°, ${state.servo.tilt_deg.toFixed(0)}°`;
  return state;
}

async function boot() {
  const health = await api("/api/health");
  $("#health").textContent = `${health.status} · ${health.mode}`;
  await refreshState();
}

document.querySelectorAll("[data-move]").forEach((button) => {
  button.addEventListener("click", async () => {
    try {
      await api("/api/robot/move", {
        method: "POST",
        body: JSON.stringify({ direction: button.dataset.move, distance_cm: 10 }),
      });
      await refreshState();
    } catch (error) {
      alert(error.message);
    }
  });
});

document.querySelectorAll("[data-rotate]").forEach((button) => {
  button.addEventListener("click", async () => {
    try {
      await api("/api/robot/rotate", {
        method: "POST",
        body: JSON.stringify({ angle_deg: Number(button.dataset.rotate) }),
      });
      await refreshState();
    } catch (error) {
      alert(error.message);
    }
  });
});

document.querySelectorAll("[data-servo-pan], [data-servo-tilt]").forEach((button) => {
  button.addEventListener("click", async () => {
    const state = await refreshState();
    const pan = state.servo.pan_deg + Number(button.dataset.servoPan || 0);
    const tilt = state.servo.tilt_deg + Number(button.dataset.servoTilt || 0);
    await api("/api/robot/servo/pan_tilt", {
      method: "POST",
      body: JSON.stringify({ pan_deg: pan, tilt_deg: tilt }),
    });
    await refreshState();
  });
});

async function stopRobot() {
  await api("/api/robot/stop", { method: "POST", body: "{}" });
  await refreshState();
}

$("#stopBtn").addEventListener("click", stopRobot);
$("#softStopBtn").addEventListener("click", stopRobot);

$("#captureBtn").addEventListener("click", async () => {
  const capture = await api("/api/camera/capture", { method: "POST", body: "{}" });
  const scene = await api("/api/vision/describe", { method: "POST", body: "{}" });
  renderJson($("#visionBox"), { capture, scene });
});

$("#runTaskBtn").addEventListener("click", async () => {
  try {
    const result = await api("/api/task", {
      method: "POST",
      body: JSON.stringify({ task: $("#taskText").value }),
    });
    renderJson($("#taskBox"), result);
    await refreshState();
  } catch (error) {
    $("#taskBox").textContent = error.message;
  }
});

boot().catch((error) => {
  $("#health").textContent = error.message;
});
