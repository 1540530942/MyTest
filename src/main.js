import './styles.css';

const endpointInput = document.querySelector('#endpointInput');
const saveEndpointButton = document.querySelector('#saveEndpointButton');
const clearLogButton = document.querySelector('#clearLogButton');
const connectionState = document.querySelector('#connectionState');
const statusLight = document.querySelector('#statusLight');
const eventLog = document.querySelector('#eventLog');
const commandButtons = document.querySelectorAll('[data-command]');

const storageKey = 'remote-control-endpoint';

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

function getEndpoint() {
  return endpointInput.value.trim();
}

async function sendCommand(command) {
  const endpoint = getEndpoint();

  if (!endpoint) {
    logEvent('请先填写并保存远端服务地址。', 'warn');
    setConnectionState('缺少服务地址', false);
    return;
  }

  setConnectionState('发送中', true);
  logEvent(`发送指令：${command}`);

  try {
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        command,
        source: 'personal-domain-dashboard',
        timestamp: new Date().toISOString()
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const text = await response.text();
    setConnectionState('在线', true);
    logEvent(text ? `远端响应：${text}` : '远端已确认指令。', 'success');
  } catch (error) {
    setConnectionState('连接失败', false);
    logEvent(`发送失败：${error.message}`, 'error');
  }
}

function init() {
  endpointInput.value = localStorage.getItem(storageKey) ?? '';
  setConnectionState(endpointInput.value ? '待发送' : '未连接', false);
  logEvent('控制台已就绪。');

  saveEndpointButton.addEventListener('click', () => {
    localStorage.setItem(storageKey, getEndpoint());
    logEvent('远端服务地址已保存。', 'success');
    setConnectionState('待发送', false);
  });

  clearLogButton.addEventListener('click', () => {
    eventLog.replaceChildren();
    logEvent('日志已清空。');
  });

  commandButtons.forEach((button) => {
    button.addEventListener('click', () => sendCommand(button.dataset.command));
  });
}

init();
