import '../scss/content.scss';
import { AgentServerConnector, AgentServerState } from './connector';

const port = chrome.runtime.connect({ name: 'content' });


const COMMAND_LABELS: {[key: string]: string} = {
  'get_url': 'Get URL',
  'get_html': 'Get HTML',
  'get': 'Navigate',
  'back': 'Go back',
  'get_screenshot': 'Take screenshot',
  'execute_script': 'Execute script',
  'exec_code': 'Execute code',
  'is_visible': 'Check visibility'
};

function main() {

  const server = new AgentServerConnector();

  const hostField = document.getElementById('host') as HTMLInputElement;
  const connectBtn = document.getElementById('connect') as HTMLButtonElement;
  const disconnectBtn = document.getElementById('disconnect') as HTMLButtonElement;
  const prompt = document.getElementById('prompt') as HTMLTextAreaElement;
  const startBtn = document.getElementById('start') as HTMLButtonElement;
  const statusText = document.getElementById('status') as HTMLElement;
  const logs = document.getElementById('logs') as HTMLElement;

  function setUIState(opts: {canConnect: boolean, canDisconnect: boolean, label: string}) {
    statusText.innerHTML = opts.label;
    if (opts.canConnect) {
      startBtn.disabled = true;
      connectBtn.classList.remove('hidden');
    } else {
      startBtn.disabled = false;
      connectBtn.classList.add('hidden');
    }
    if (opts.canDisconnect) {
      disconnectBtn.classList.remove('hidden');
    } else {
      disconnectBtn.classList.add('hidden');
    }
  }

  function addLog(text: string) {
    const log = document.createElement('div');
    log.appendChild(document.createTextNode(text));
    logs.appendChild(log);
    log.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }

  function clearLogs() {
    logs.innerHTML = '';
  }

  function setState(state: AgentServerState) {
    if (state === AgentServerState.CONNECTED) {
      setUIState({canConnect: false, canDisconnect: true, label: 'Connected'});
    } else if (state === AgentServerState.DISCONNECTED) {
      setUIState({canConnect: true, canDisconnect: false, label: 'Disconnected'});
    } else if (state === AgentServerState.CONNECTING) {
      setUIState({canConnect: false, canDisconnect: true, label: 'Connecting'});
    }
  }
  setState(AgentServerState.DISCONNECTED);
  
  server.onStateChange = setState;
  server.onError = err => {
    if (err instanceof Event && err.target instanceof WebSocket) {
      addLog('Network error');
    } else {
      addLog(err.message || (err + ''));
    }
  };

  server.driver.onTabDebugged = tabId => port.postMessage({ type: 'tab_debug', tabId });
  server.driver.onCommand = cmd => {
    const label = COMMAND_LABELS[cmd];
    if (label) {
      addLog(label);
    }
  };

  connectBtn.addEventListener('click', () => server.connect(hostField.value));
  disconnectBtn.addEventListener('click', () => server.disconnect());
  startBtn.addEventListener('click', () => {
    const { value } = prompt;
    if (value) {
      server.sendPrompt('run', value);
      prompt.value = '';
      clearLogs();
      addLog(value);
    }
  });

  if (hostField.value) {
    server.connect(hostField.value);
  }
}
main();
