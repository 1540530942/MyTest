import './styles.css';

const endpointInput = document.querySelector('#endpointInput');
const deviceIdInput = document.querySelector('#deviceIdInput');
const pinInput = document.querySelector('#pinInput');
const saveSettingsButton = document.querySelector('#saveSettingsButton');
const clearLogButton = document.querySelector('#clearLogButton');
const connectionState = document.querySelector('#connectionState');
const statusLight = document.querySelector('#statusLight');
const payloadPreview = document.querySelector('#payloadPreview');
const eventLog = document.querySelector('#eventLog');
const commandButtons = document.querySelectorAll('[data-command]');

const storageKey = 'iot-control-settings';

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

function getSettings() {
  return {
    endpoint: endpointInput.value.trim(),
    deviceId: deviceIdInput.value.trim() || 'desk-led',
    pin: Number.parseInt(pinInput.value, 10) || 13
  };
}

function saveSettings() {
  localStorage.setItem(storageKey, JSON.stringify(getSettings()));
  logEvent('Settings saved.', 'success');
}

function loadSettings() {
  const saved = JSON.parse(localStorage.getItem(storageKey) || '{}');
  endpointInput.value = saved.endpoint || '';
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
      throw new Error(`HTTP ${response.status}`);
    }

    const text = await response.text();
    setConnectionState('Online', true);
    logEvent(text ? `API response: ${text}` : 'Command accepted by API.', 'success');
  } catch (error) {
    setConnectionState('Failed', false);
    logEvent(`Send failed: ${error.message}`, 'error');
  }
}

function init() {
  loadSettings();
  setConnectionState(endpointInput.value ? 'Ready' : 'Offline', false);
  payloadPreview.textContent = JSON.stringify(buildCommandPayload('led_set', 'on'), null, 2);
  logEvent('Dashboard ready.');

  saveSettingsButton.addEventListener('click', saveSettings);

  clearLogButton.addEventListener('click', () => {
    eventLog.replaceChildren();
    logEvent('Log cleared.');
  });

  commandButtons.forEach((button) => {
    button.addEventListener('click', () => sendCommand(button.dataset.command, button.dataset.value));
  });
}

init();
