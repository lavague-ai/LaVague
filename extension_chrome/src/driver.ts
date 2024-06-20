import { operateToolWithXPATH } from "./actions";
import { DomActions } from "./domactions";
import { parseResponse } from "./parseactions";

export interface DriverCommandHandler {
  (message: any): Promise<any>;
}

export class ChromeExtensionDriver {
  private currentTabId: number | null = null;
  private readonly handlers: {[command: string]: DriverCommandHandler} = {
    'get_url': () => this.sendTabURL(),
    'get_html': () => this.sendHTML(),
    'get': msg => this.get(msg.args),
    'back': () => this.back(),
    'get_screenshot': () => this.takeScreenshot(),
    'execute_script': msg => this.executeScript(msg.args),
    'exec_code': msg => this.executeCode(msg.args),
    'is_visible': msg => this.isVisible(msg.args),
  };
  onTabDebugged?: (tabId: number) => void;
  onCommand?: (command: string) => void;

  constructor() {}

  tabActivatedListener = async (activeInfo: chrome.tabs.TabActiveInfo) => {
    chrome.tabs.query({ active: true, lastFocusedWindow: true }, tabs => {
      if (tabs[0].url != undefined && !tabs[0].url.startsWith("chrome://")) {
        const newTabId = activeInfo.tabId;
        if (this.currentTabId != null && this.currentTabId !== newTabId) {
          this.detachDebuggerFromTab(this.currentTabId);
        }
        this.currentTabId = newTabId;
        this.attachDebuggerToTab(this.currentTabId);
      }
    });
  };

  tabUpdatedListener = async (tabId: number, changeInfo: chrome.tabs.TabChangeInfo, tab: chrome.tabs.Tab) => {
    if (tab.active && changeInfo.status === 'complete' && !tab.url!.startsWith("chrome://")) {
      if (this.currentTabId && this.currentTabId !== tabId) {
        this.detachDebuggerFromTab(this.currentTabId);
      }
      this.currentTabId = tabId;
      this.attachDebuggerToTab(tabId);    
    }
  };

  attachDebuggerToTab(tabId: number) {
    return new Promise<number>((resolve, reject) => {
      chrome.debugger.attach({ tabId }, '1.3', () => {
        if (chrome.runtime.lastError) {
          reject(chrome.runtime.lastError.message);
        } else {
          resolve(tabId);
          this.onTabDebugged?.(tabId);
        }
      });
    });
  }
  
  detachDebuggerFromTab(tabId: number) {
    return new Promise<number>((resolve, reject) => {
      chrome.debugger.detach({ tabId }, () => {
        if (this.currentTabId === tabId) {
          this.currentTabId = null;
        }
        if (chrome.runtime.lastError) {
          reject(chrome.runtime.lastError.message);
        } else {
          resolve(tabId);
        }
      });
    });
  }

  async start() {
    chrome.tabs.onActivated.addListener(this.tabActivatedListener);
    chrome.tabs.onUpdated.addListener(this.tabUpdatedListener);
    await this.attachDebuggerToTab(await this.getTabId());
  }

  async stop() {
    chrome.tabs.onActivated.removeListener(this.tabActivatedListener);
    chrome.tabs.onUpdated.removeListener(this.tabUpdatedListener);
    await this.detachDebuggerFromTab(await this.getTabId());
  }

  async getTabId() {
    return this.currentTabId ?? new Promise<number>((resolve, reject) => {
      chrome.tabs.query({ active: true, currentWindow: true }, tabs => {
        const currentTabId = tabs[0].id;
        if (currentTabId) {
          resolve(currentTabId);
        } else {
          reject('No active tab found');
        }
      });
    });
  }

  handleMessage(message: any) {
    const handler = this.handlers[message.command];
    if (handler) {
      this.onCommand?.(message.command);
      return handler(message);
    }
    console.warn(`Unknown command ignored: ${message.command}`);
    return null;
  }

  sendTabURL() {
    return new Promise<string>(resolve => {
      chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        resolve(tabs[0].url!)
      });
    });
  }

  sendHTML() {
    return new Promise<string>(async (resolve, reject) => {
      try {
        const [result] = await chrome.scripting.executeScript({
          target: { tabId: await this.getTabId() },
          func: () => document.documentElement.outerHTML
        });
        resolve(result.result);
      } catch (e) {
        reject(e);
      }
    });
  }

  async get(url: string) {
    const tabId = await this.getTabId();
    const res = await chrome.tabs.update(tabId, {url: url});
    const initialTabId = tabId;
  
    await new Promise<void>(resolve => {
      chrome.tabs.onUpdated.addListener(function onUpdated(localTabId, info) {
        if (localTabId === initialTabId && info.status === 'complete') {
          chrome.tabs.onUpdated.removeListener(onUpdated);
          resolve();
        }
      });
    });
    return !!res;
  }

  async back() {
    await chrome.tabs.goBack(await this.getTabId());
    return true;
  }

  async takeScreenshot() {
    return chrome.tabs.captureVisibleTab({format: "png"});
  }

  async executeScript(code: string) {
    const tabId = await this.getTabId();
    const dom = new DomActions(tabId);
    const code_ex = `(function() { ${code} })()`;
    const res = await dom.execCode(code_ex)
    return res.result == undefined ? true : res.result;
  }

  async executeCode(text: string) {
    const tabId = await this.getTabId();
    const ret = parseResponse(text)
    for (var i = 0; i < ret.length; i++ ) {
      await operateToolWithXPATH(tabId, ret[i].operation)
    }
    return true;
  }

  async isVisible(xpath: string) {
    const combinedExpression = `
    (function() {
      const xpath = "${xpath}";
      const element = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
      if (!element) return false;
      const style = window.getComputedStyle(element);
      return style.opacity !== "" && style.display !== "none" && style.visibility !== "hidden" && style.opacity !== "0" && element.getAttribute("aria-hidden") !== "true";
    })();
  `;
    var dom = new DomActions(await this.getTabId());
    const res = await dom.execCode(combinedExpression);
    const isVisible = res.result.value;
    return isVisible;
  }

}