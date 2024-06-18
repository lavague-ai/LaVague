import { DomActions } from "./domactions";
import { parseResponse } from "./parseactions";
import { operateToolWithXPATH } from "./actions";
import { sleep } from "./tools";

const TEN_SECONDS_MS = 10 * 1000;
let webSocket: any = null;
let currentTabId: number | undefined = undefined

// Toggle WebSocket connection on action button click
// Send a message every 10 seconds, the ServiceWorker will
// be kept alive as long as messages are being sent.
chrome.action.onClicked.addListener(async () => {
  if (webSocket) {
    disconnect();
  } else {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      currentTabId = tabs[0].id
    });
    connect();
    keepAlive();
  }
});

function connect() {
  webSocket = new WebSocket('ws://127.0.0.1:8000');

  webSocket.onopen = () => {
    chrome.action.setIcon({ path: 'icons/socket-active.png' });
  };

  webSocket.onmessage = async (event: { data: string; }) => {
    try {
      const msg = JSON.parse(event.data);
      if (msg.command == "get_url") {
        sendTabURL(msg.id);
      }
      else if (msg.command == "get_html") {
        await sendHTML(msg.id);
      }
      else if (msg.command == "get") {
        var dom = new DomActions(currentTabId!)
        await get(msg.args, msg.id);
        await sleep(2500)
        await dom.clickAtPosition(4, 4);
      }
      else if (msg.command == "back") {
        await back(msg.id);
      }
      else if (msg.command == "get_screenshot") {
        await get_screenshot(msg.id);
      }
      else if (msg.command == "execute_script") {
        var dom = new DomActions(currentTabId!)
        var code_ex = `(function() {
        ${msg.args}
        })()`;
        const res = await dom.execCode(code_ex)
        const jso_obj = {
          "method": "exec_script",
          "ret": res.result == undefined ? true : res.result,
          "id": msg.id,
        };
        const jso = JSON.stringify(jso_obj)
        if (webSocket) {
          webSocket.send(jso)
        }
      }
      else if (msg.command == "exec_code") {
        var ret = parseResponse(msg.args)
        console.log(ret)
        for (var i = 0; i < ret.length; i++ ) {
          await operateToolWithXPATH(currentTabId!, ret[i].operation)
        }
        const jso_obj = {
          "method": "exec_code",
          "ret": true,
          "id": msg.id,
        };
        const jso = JSON.stringify(jso_obj)
        if (webSocket) {
          webSocket.send(jso)
        }
      }
    } catch (error) {
        console.error('Error parsing JSON:', error);
    }
  };

  webSocket.onclose = () => {
    chrome.action.setIcon({ path: 'icons/socket-inactive.png' });
    console.log('websocket connection closed');
    webSocket = null;
  };
}

function disconnect() {
  if (webSocket) {
    webSocket.close();
  }
}


function keepAlive() {
  const keepAliveIntervalId = setInterval(
    () => {
      if (webSocket) {
        webSocket.send("PING");
      } else {
        clearInterval(keepAliveIntervalId);
      }
    },
    // It's important to pick an interval that's shorter than 30s, to
    // avoid that the service worker becomes inactive.
    TEN_SECONDS_MS
  );
}


function sendTabURL(id: string) {
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    console.log(tabs)
    const jso_obj = {
      "method": "sendTabURL",
      "ret": tabs[0].url,
      "id": id,
    };
    const jso = JSON.stringify(jso_obj)
    webSocket.send(jso)
  });
}

async function get(url: string, id: string) {
  const res = await chrome.tabs.update(currentTabId!, {url: url});
  const tabid = currentTabId

   await new Promise<void>(resolve => {
     chrome.tabs.onUpdated.addListener(function onUpdated(tabId, info) {
       if (tabId === tabid && info.status === 'complete') {
         chrome.tabs.onUpdated.removeListener(onUpdated);
         resolve();
       }
     });
   });

  if (res && webSocket) {
    const jso_obj = {
      "method": "get",
      "ret": true,
      "id": id,
    };
    const jso = JSON.stringify(jso_obj)
    webSocket.send(jso)
  }
}

async function sendHTML(id: string) {
      const [result] = await chrome.scripting.executeScript({
        target: { tabId: currentTabId! },
        func: () => document.documentElement.outerHTML
      });

        if (webSocket) {
          const jso_obj = {
            "method": "sendTabURL",
            "ret": result.result,
            "id": id,
          };
          const jso = JSON.stringify(jso_obj)
          webSocket.send(jso)
      }
}

// Listen for tab changes and attach debugger
chrome.tabs.onActivated.addListener(async (activeInfo) => {
  chrome.tabs.query({ active: true, lastFocusedWindow: true }, tabs => {
    if (tabs[0].url != undefined && !tabs[0].url.startsWith("chrome://")) {
      console.log(tabs[0].url)
      const newTabId = activeInfo.tabId;
      if (currentTabId && currentTabId !== newTabId) {
        detachDebuggerFromTab(currentTabId);
      }
      currentTabId = newTabId;
      attachDebuggerToTab(currentTabId);
    }
  });
});

chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
  if (tab.active && changeInfo.status === 'complete') {
    if (!tab.url!.startsWith("chrome://")) {
      if (currentTabId && currentTabId !== tabId) {
        detachDebuggerFromTab(currentTabId);
      }
      currentTabId = tabId;
      attachDebuggerToTab(tabId);    
    }
  }
});

function attachDebuggerToTab(tabId: number) {
  const debuggee = { tabId: tabId };

  chrome.debugger.attach(debuggee, '1.3', () => {
    if (chrome.runtime.lastError) {
      console.error(chrome.runtime.lastError.message);
      return;
    }
    console.log('Debugger attached to tab:', tabId);
  });
}

function detachDebuggerFromTab(tabId: number) {
  const debuggee = { tabId: tabId };

  chrome.debugger.detach(debuggee, () => {
    if (chrome.runtime.lastError) {
      console.error(chrome.runtime.lastError.message);
    } else {
      console.log('Debugger detached from tab:', tabId);
    }
  });
}

// TypeScript function
function scrollIntoViewFunction(this: any) {
  this.scrollIntoView({
    block: "center",
    inline: "center",
  });
}

export const scrollScriptString = scrollIntoViewFunction.toString();

export async function sendCommand(currentTabId: any, code: string, params: Object | undefined) {
  return chrome.debugger.sendCommand({ tabId: currentTabId }, code, params);
}

async function get_screenshot(id: string) {
    try {
      const scr = await chrome.tabs.captureVisibleTab({format: "png"});
      const jso_obj = {
        "method": "get_screenshot",
        "ret": scr,
        "id": id,
      };
      const jso = JSON.stringify(jso_obj)
      if (webSocket) {
        webSocket.send(jso)
      }
    }
    catch (e) {
      console.log(e)
    }
}
async function back(id: any) {
  await chrome.tabs.goBack(currentTabId!);
  const jso_obj = {
    "method": "back",
    "ret": true,
    "id": id,
  };
  const jso = JSON.stringify(jso_obj)
  if (webSocket) {
    webSocket.send(jso)
  }
}

