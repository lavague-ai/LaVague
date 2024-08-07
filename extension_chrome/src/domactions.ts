import { sleep, waitTillStable } from './tools';

const DEFAULT_INTERVAL = 500;
const DEFAULT_TIMEOUT = 10000; // 10 seconds

export function getNodeFromXPATH(xpath: string): Node | null {
    const result = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
    const res2 = result.singleNodeValue;
    return res2;
}

export function clickElementByXPath(xpath: string): boolean {
    const element = getNodeFromXPATH(xpath);
    if (element && element instanceof HTMLElement) {
        element.click();
        console.log('click', element.textContent);
        return true;
    } else {
        console.log('failed to click!');
        return false;
    }
}

export class DomActions {
    static delayBetweenClicks = 500;
    static delayBetweenKeystrokes = 10;

    tabId: number;

    constructor(tabId: number) {
        this.tabId = tabId;
    }

    public async sendCommand(method: string, params?: any): Promise<any> {
        return chrome.debugger.sendCommand({ tabId: this.tabId }, method, params);
    }

    public async execCode(code: string, returnByValue = false) {
        return await this.sendCommand('Runtime.evaluate', {
            expression: code,
            returnByValue: returnByValue,
        });
    }

    public async clickAtPosition(x: number, y: number, clickCount = 1): Promise<void> {
        await this.sendCommand('Input.dispatchMouseEvent', {
            type: 'mousePressed',
            x,
            y,
            button: 'left',
            clickCount,
        });
        await sleep(20);
        await this.sendCommand('Input.dispatchMouseEvent', {
            type: 'mouseReleased',
            x,
            y,
            button: 'left',
            clickCount,
        });
        await sleep(DomActions.delayBetweenClicks);
    }

    private async selectAllText() {
        await this.sendCommand('Input.dispatchKeyEvent', {
            type: 'keyDown',
            commands: ['selectAll'],
        });
        await sleep(200);
    }

    public async getCoordinatesFromXPATH(xpath: string) {
        const objectId = this.getObjectID(xpath);
        const { model } = await this.sendCommand('DOM.getBoxModel', {
            objectId,
        });
        const [x1, y1, _x2, _y2, x3, y3] = model.border;
        const centerX = (x1 + x3) / 2;
        const centerY = (y1 + y3) / 2;
        return { x: centerX, y: centerY };
    }

    private async typeText(text: string): Promise<void> {
        for (const char of text) {
            if (char === '\n') {
                this.enterButton();
                continue;
            }
            await this.sendCommand('Input.dispatchKeyEvent', {
                type: 'keyDown',
                text: char,
            });
            await sleep(DomActions.delayBetweenKeystrokes);
            await this.sendCommand('Input.dispatchKeyEvent', {
                type: 'keyUp',
                text: char,
            });
            await sleep(DomActions.delayBetweenKeystrokes);
        }
    }
    private async enterButton(): Promise<void> {
        await this.sendCommand('Input.dispatchKeyEvent', {
            type: 'keyDown',
            windowsVirtualKeyCode: 13,
            key: 'Enter',
            code: 'Enter',
            text: '\r',
        });
        await this.sendCommand('Input.dispatchKeyEvent', {
            type: 'keyUp',
            windowsVirtualKeyCode: 13,
            key: 'Enter',
            code: 'Enter',
            text: '\r',
        });
    }

    public async waitTillHTMLRendered(interval = DEFAULT_INTERVAL, timeout = DEFAULT_TIMEOUT): Promise<void> {
        return waitTillStable(
            async () => {
                const { result } = await this.sendCommand('Runtime.evaluate', {
                    expression: 'document.documentElement.innerHTML.length',
                });
                return result.value;
            },
            interval,
            timeout
        );
    }

    public async scrollUp() {
        await this.sendCommand('Runtime.evaluate', {
            expression: 'window.scrollBy(0, -window.innerHeight);',
        });
        await sleep(300);
    }

    public async scrollDown() {
        await this.sendCommand('Runtime.evaluate', {
            expression: 'window.scrollBy(0, window.innerHeight)',
        });
        await sleep(300);
    }

    public async scrollToTop() {
        await this.sendCommand('Runtime.evaluate', {
            expression: 'window.scroll({left: 0, top: 0})',
        });
        await sleep(300);
    }

    public async scrollToBottom() {
        await this.sendCommand('Runtime.evaluate', {
            expression: 'window.scroll({left: 0, top: document.body.offsetHeight})',
        });
        await sleep(300);
    }

    public async getObjectID(xpath: string) {
        const code = `
        (function(xpath) {
          ${getNodeFromXPATH.toString()}
          res = getNodeFromXPATH(xpath);
          return res
        })(${JSON.stringify(xpath)});`;
        const ret = await this.execCode(code);
        return ret.result.objectId;
    }

    public async remove_highlight(xpath: string) {
        const code = `
        (function() {
            const element = document.evaluate("${xpath}", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
            if (element) {
                element.style.removeProperty('outline');
            }
        })();`;
        return this.execCode(code, true);
    }

    public async highlight_elem(xpath: string) {
        const code = `
        (function() {
            const element = document.evaluate("${xpath}", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
            if (element) {
                element.style.outline = '2px solid red';
                element.style['outline-offset'] = '-1px';
                const rect = element.getBoundingClientRect();
                return {
                    x: rect.x,
                    y: rect.y,
                    x2: rect.left + rect.width,
                    y2: rect.top + rect.height,
                };
            } else {
                return {
                    x: 0,
                    y: 0,
                    x2: 0,
                    y2: 0,
                };
            }
        })();`;
        const ret = await this.execCode(code, true);
        return ret;
    }

    public async switchToTab(tabId: number) {
        await chrome.tabs.update(tabId, { active: true });
        chrome.tabs.highlight({ tabs: tabId }, function () {});
    }

    public async getOpenTabs(): Promise<string[]> {
        const queryTabs = (queryInfo: chrome.tabs.QueryInfo): Promise<chrome.tabs.Tab[]> => {
            return new Promise((resolve, reject) => {
                chrome.tabs.query(queryInfo, (result) => {
                    if (chrome.runtime.lastError) {
                        return reject(chrome.runtime.lastError);
                    }
                    resolve(result);
                });
            });
        };

        try {
            // Query all tabs once
            const tabs = await queryTabs({});

            // Map the tab titles, marking the active tab
            const tabTitles = tabs.map((t) => (t.id === this.tabId ? `${t.id} - [CURRENT] ${t.title}` : `${t.id} - ${t.title}`));
            console.log(tabTitles);

            return tabTitles;
        } catch (error) {
            console.error('Failed to get tabs:', error);
            return [];
        }
    }

    public async setFocus(xpath: string) {
        const code = `
        (function(xpath) {
          ${getNodeFromXPATH.toString()}
          res = getNodeFromXPATH(xpath);
          return res
        })(${JSON.stringify(xpath)});`;
        const ret = await this.execCode(code);
        console.log(ret);

        //Workaround so the nodeId can be retrieved. Might need some optimizations.
        await this.sendCommand('DOM.getDocument', { depth: -1 });
        const nodeId = await this.sendCommand('DOM.requestNode', {
            objectId: ret.result.objectId,
        });
        console.log(nodeId);
        await this.sendCommand('DOM.focus', { nodeId: nodeId.nodeId });
    }

    public async pressEnter(payload: { xpath: string }): Promise<boolean> {
        await this.setFocus(payload.xpath);
        await sleep(300);
        await this.enterButton();
        return true;
    }

    public async setValueWithXPATH(payload: { xpath: string; value: string }): Promise<boolean> {
        await this.setFocus(payload.xpath);
        await this.selectAllText();
        await this.typeText(payload.value);
        return true;
    }

    private async get_possible_interactions_dispatch(args: string) {
        return new Promise((resolve, reject) => {
            chrome.tabs.sendMessage(this.tabId, { method: 'get_possible_interactions', message: args }, (res) => {
                const error = chrome.runtime.lastError?.message || res.error;
                if (chrome.runtime.lastError || res.error) {
                    console.error('Error: ' + error);
                    reject(error);
                } else {
                    resolve(res);
                }
            });
        });
    }

    public async get_possible_interactions(args: string) {
        const res: any = await this.get_possible_interactions_dispatch(args);
        return res.response;
    }

    public async clickwithXPath(xpath: string) {
        const code = `
          (function(xpath) {
            ${getNodeFromXPATH.toString()}
            ${clickElementByXPath.toString()}
            res = getNodeFromXPATH(xpath);
            clickElementByXPath(xpath);
          })(${JSON.stringify(xpath)});`;
        await this.execCode(code);
        return true;
    }
}
