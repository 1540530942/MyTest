import './styles.css';

const endpointInput = document.querySelector('#endpointInput');
const deviceIdInput = document.querySelector('#deviceIdInput');
const pinInput = document.querySelector('#pinInput');
const saveSettingsButton = document.querySelector('#saveSettingsButton');
const clearLogButton = document.querySelector('#clearLogButton');
const connectionState = document.querySelector('#connectionState');
const statusLight = document.querySelector('#statusLight');
const payloadPreview = document.querySelector('#payloadPreview');
const statePreview = document.querySelector('#statePreview');
const eventLog = document.querySelector('#eventLog');
const refreshStateButton = document.querySelector('#refreshStateButton');
const commandButtons = document.querySelectorAll('[data-command]');

const storageKey = 'iot-control-settings';

function defaultEndpoint() {
  const localHosts = new Set(['127.0.0.1', 'localhost']);
  if (window.location.pathname === '/remote' || window.location.pathname.startsWith('/remote/')) {
    return `${window.location.origin}/remote/devices/command`;
  }
  if (localHosts.has(window.location.hostname)) {
    return `${window.location.protocol}//${window.location.hostname}:8000/devices/command`;
  }
  return `${window.location.origin}/devices/command`;
}

function createRequestId() {
  return `req-${new Date().toISOString().replace(/[-:.TZ]/g, '').slice(0, 14)}-${crypto.randomUUID().slice(0, 8)}`;
}

function logEvent(message, type = 'info') {
  const item = document.createElement('li');
  item.className = `log-item ${type}`;
  item.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
  eventLog.prepend(item);
}

function setConnectionState(state, online) {
  connectionState.textContent = state;
  statusLight.classList.toggle('online', online);
  statusLight.classList.toggle('offline', !online);
}

function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function getSettings() {
  return {
    endpoint: endpointInput.value.trim(),
    deviceId: deviceIdInput.value.trim() || 'desk-led',
    pin: Number.parseInt(pinInput.value, 10) || 13
  };
}

function stateEndpoint(settings) {
  const endpoint = new URL(settings.endpoint);
  const apiPrefix = endpoint.pathname.startsWith('/remote/') ? '/remote' : '';
  endpoint.pathname = `${apiPrefix}/devices/${encodeURIComponent(settings.deviceId)}/state`;
  endpoint.search = '';
  endpoint.hash = '';
  return endpoint.toString();
}

function renderDeviceState(snapshot) {
  statePreview.textContent = JSON.stringify(snapshot, null, 2);

  const state = snapshot.state?.state;
  const pinState = state?.pin13;
  const response = snapshot.state?.serial_response;
  if (pinState) {
    setConnectionState(`Pin 13 ${pinState.toUpperCase()}`, true);
    logEvent(response ? `Device state: pin13 ${pinState} (${response})` : `Device state: pin13 ${pinState}`, 'success');
  }
}

async function refreshDeviceState(options = {}) {
  const settings = getSettings();
  if (!settings.endpoint) {
    return null;
  }

  const retries = options.retries ?? 0;
  const delayMs = options.delayMs ?? 500;
  for (let attempt = 0; attempt <= retries; attempt += 1) {
    if (attempt > 0) {
      await wait(delayMs);
    }

    try {
      const response = await fetch(stateEndpoint(settings));
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const snapshot = await response.json();
      renderDeviceState(snapshot);
      return snapshot;
    } catch (error) {
      if (attempt === retries) {
        statePreview.textContent = `No device state yet: ${error.message}`;
        logEvent(`State refresh failed: ${error.message}`, 'warn');
      }
    }
  }

  return null;
}

function saveSettings() {
  localStorage.setItem(storageKey, JSON.stringify(getSettings()));
  logEvent('Settings saved.', 'success');
  refreshDeviceState();
}

function loadSettings() {
  const saved = JSON.parse(localStorage.getItem(storageKey) || '{}');
  endpointInput.value = saved.endpoint || defaultEndpoint();
  deviceIdInput.value = saved.deviceId || 'desk-led';
  pinInput.value = saved.pin || 13;
}

function buildCommandPayload(command, value) {
  const settings = getSettings();

  return {
    request_id: createRequestId(),
    cmd: command,
    device_id: settings.deviceId,
    pin: settings.pin,
    value: value || undefined,
    source: 'web',
    mqtt_topic: `devices/${settings.deviceId}/cmd`,
    created_at: new Date().toISOString()
  };
}

async function sendCommand(command, value) {
  const settings = getSettings();
  const payload = buildCommandPayload(command, value);
  payloadPreview.textContent = JSON.stringify(payload, null, 2);

  if (!settings.endpoint) {
    logEvent('Set an API endpoint before sending commands.', 'warn');
    setConnectionState('Missing API', false);
    return;
  }

  setConnectionState('Sending', true);
  logEvent(`Sending ${payload.cmd} to ${payload.mqtt_topic}`);

  try {
    const response = await fetch(settings.endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(errorText ? `HTTP ${response.status}: ${errorText}` : `HTTP ${response.status}`);
    }

    const text = await response.text();
    setConnectionState('Online', true);
    logEvent(text ? `API response: ${text}` : 'Command accepted by API.', 'success');
    await refreshDeviceState({ retries: 5, delayMs: 450 });
  } catch (error) {
    setConnectionState('Failed', false);
    logEvent(`Send failed: ${error.message}`, 'error');
  }
}

function init() {
  loadSettings();
  setConnectionState(endpointInput.value ? 'Ready' : 'Offline', false);
  payloadPreview.textContent = JSON.stringify(buildCommandPayload('led_set', 'on'), null, 2);
  statePreview.textContent = 'No device state loaded yet.';
  logEvent('Dashboard ready.');

  saveSettingsButton.addEventListener('click', saveSettings);
  refreshStateButton.addEventListener('click', () => refreshDeviceState({ retries: 1 }));

  clearLogButton.addEventListener('click', () => {
    eventLog.replaceChildren();
    logEvent('Log cleared.');
  });

  commandButtons.forEach((button) => {
    button.addEventListener('click', () => sendCommand(button.dataset.command, button.dataset.value));
  });

  refreshDeviceState();
}

init();
