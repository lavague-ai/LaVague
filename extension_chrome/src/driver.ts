import { operateToolWithXPATH } from './actions';
import { DomActions } from './domactions';
import { parseResponse } from './parseactions';

export interface DriverCommandHandler {
    (message: any): Promise<any>;
}

export class ChromeExtensionDriver {
    private currentTabId: number | null = null;
    private readonly handlers: { [command: string]: DriverCommandHandler } = {
        get_url: () => this.sendTabURL(),
        get_html: () => this.sendHTML(),
        get: (msg) => this.get(msg.args),
        back: () => this.back(),
        get_screenshot: () => this.takeScreenshot(),
        execute_script: (msg) => this.executeScript(msg.args),
        exec_code: (msg) => this.executeCode(msg.args),
        is_visible: (msg) => this.isVisible(msg.args),
    };
    onTabDebugged?: (tabId: number) => void;
    onCommand?: (command: string) => void;

    tabActivatedListener = async (activeInfo: chrome.tabs.TabActiveInfo) => {
        chrome.tabs.query({ active: true, lastFocusedWindow: true }, (tabs) => {
            if (tabs[0].url != undefined && !tabs[0].url.startsWith('chrome://')) {
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
        if (tab.active && changeInfo.status === 'complete' && !tab.url!.startsWith('chrome://')) {
            if (this.currentTabId && this.currentTabId !== tabId) {
                this.detachDebuggerFromTab(this.currentTabId);
            }
            this.currentTabId = tabId;
            this.attachDebuggerToTab(tabId);
        }
    };

    attachDebuggerToTab(tabId: number | null) {
        return new Promise<void>((resolve, reject) => {
            if (tabId == null) {
                resolve();
            } else {
                chrome.debugger.attach({ tabId }, '1.3', () => {
                    if (chrome.runtime.lastError) {
                        reject(chrome.runtime.lastError.message);
                    } else {
                        resolve();
                        this.onTabDebugged?.(tabId);
                    }
                });
            }
        });
    }

    detachDebuggerFromTab(tabId: number | null) {
        return new Promise<void>((resolve, reject) => {
            if (tabId == null) {
                resolve();
            } else {
                chrome.debugger.detach({ tabId }, () => {
                    if (this.currentTabId === tabId) {
                        this.currentTabId = null;
                    }
                    if (chrome.runtime.lastError) {
                        reject(chrome.runtime.lastError.message);
                    } else {
                        resolve();
                    }
                });
            }
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
        return (
            this.currentTabId ??
            new Promise<number | null>((resolve, reject) => {
                chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
                    const currentTab = tabs[0];
                    if (currentTab.url!.startsWith('chrome://')) {
                        resolve(null);
                    }
                    const currentTabId = currentTab.id;
                    if (currentTabId) {
                        resolve(currentTabId);
                    } else {
                        reject('No active tab found');
                    }
                });
            })
        );
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
        return new Promise<string>((resolve) => {
            chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
                resolve(tabs[0].url!);
            });
        });
    }

    sendHTML() {
        return new Promise<string>((resolve, reject) => {
            this.getTabId()
                .then((tabId) => {
                    if (tabId == null) {
                        reject('No tab available');
                    } else {
                        chrome.scripting
                            .executeScript({
                                target: { tabId },
                                func: () => document.documentElement.outerHTML,
                            })
                            .then(([result]) => {
                                resolve(result.result);
                            })
                            .catch(reject);
                    }
                })
                .catch(reject);
        });
    }

    async get(url: string) {
        const tabId = await this.getTabId();
        if (tabId == null) {
            throw new Error('No tab available');
        }
        const res = await chrome.tabs.update(tabId, { url: url });
        const initialTabId = tabId;

        await new Promise<void>((resolve) => {
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
        const tabId = await this.getTabId();
        if (tabId == null) {
            return false;
        }
        await chrome.tabs.goBack(tabId);
        return true;
    }

    async takeScreenshot() {
        return chrome.tabs.captureVisibleTab({ format: 'png' });
    }

    async executeScript(code: string) {
        const tabId = await this.getTabId();
        if (tabId == null) {
            return false;
        }
        const dom = new DomActions(tabId);
        const code_ex = `(function() { ${code} })()`;
        const res = await dom.execCode(code_ex);
        return res.result == undefined ? true : res.result;
    }

    async executeCode(text: string) {
        const tabId = await this.getTabId();
        if (tabId == null) {
            return false;
        }
        const ret = parseResponse(text);
        for (let i = 0; i < ret.length; i++) {
            await operateToolWithXPATH(tabId, ret[i].operation);
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
        const tabId = await this.getTabId();
        if (tabId == null) {
            return false;
        }
        const dom = new DomActions(tabId);
        const res = await dom.execCode(combinedExpression);
        const isVisible = res.result.value;
        return isVisible;
    }
}
