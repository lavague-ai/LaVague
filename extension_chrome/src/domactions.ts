import { sleep, waitTillStable } from './tools';

const DEFAULT_INTERVAL = 500;
const DEFAULT_TIMEOUT = 10000; // 10 seconds

function getNodeFromXPATH(xpath: string): Node | null {
    const result = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
    const res2 = result.singleNodeValue;
    return res2
}
  
function getCoordinatesFromXPATH(xpath: string): { x: number; y: number } | null {
    const element = getNodeFromXPATH(xpath);
    if (element && element instanceof HTMLElement) {
      const rect = element.getBoundingClientRect();
      return { x: rect.left + rect.width / 2, y: rect.top + 8};
    }
    return null;
}

const JS_GET_INTERACTIVES = `
(function() {
    function getInteractions(e) {
        const tag = e.tagName.toLowerCase();
        if (!e.checkVisibility() || e.hasAttribute('disabled') || e.hasAttribute('readonly') || e.getAttribute('aria-hidden') === 'true'
          || e.getAttribute('aria-disabled') === 'true' || (tag === 'input' && e.getAttribute('type') === 'hidden')) {
            return [];
        }
        const style = getComputedStyle(e);
        if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') {
            return [];
        }
        const events = getEventListeners(e);
        const role = e.getAttribute('role');
        const clickableInputs = ['submit', 'checkbox', 'radio', 'color', 'file', 'image', 'reset'];
        function hasEvent(n) {
            return events[n]?.length || e.hasAttribute('on' + n);
        }
        const evts = [];
        if (hasEvent('keydown') || hasEvent('keyup') || hasEvent('keypress') || hasEvent('keydown') || hasEvent('input') || e.isContentEditable
          || (
            (tag === 'input' || tag === 'textarea' || role === 'searchbox' || role === 'input')
            ) && !clickableInputs.includes(e.getAttribute('type'))
          ) {
            evts.push('TYPE');
        }
        if (tag === 'a' || tag === 'button' || role === 'button' || role === 'checkbox' || hasEvent('click') || hasEvent('mousedown') || hasEvent('mouseup')
          || hasEvent('dblclick') || style.cursor === 'pointer' || (tag === 'input' && clickableInputs.includes(e.getAttribute('type')) )
          || e.hasAttribute('aria-haspopup') || tag === 'select' || role === 'select') {
            evts.push('CLICK');
        }
        if (hasEvent('mouseover')) {
            evts.push('HOVER');
        }
        return evts;
    }

    const results = {};
    function traverse(node, xpath) {
        if (node.nodeType === Node.ELEMENT_NODE) {
            const interactions = getInteractions(node);
            if (interactions.length > 0) {
                results[xpath] = interactions;
            }
        }
        const countByTag = {};
        for (let child = node.firstChild; child; child = child.nextSibling) {
            const tag = child.nodeName.toLowerCase();
            countByTag[tag] = (countByTag[tag] || 0) + 1;
            let childXpath = xpath + '/' + tag;
            if (countByTag[tag] > 1) {
                childXpath += '[' + countByTag[tag] + ']';
            }
            if (tag === 'iframe') {
                try {
                    traverse(child.contentWindow.document.body, childXpath + '/html/body');
                } catch (e) {
                    console.error("iframe access blocked", child, e);
                }
            } else {
                traverse(child, childXpath);
            } 
        }
    }
    traverse(document.body, '/html/body');
    return results;
})();
`;

export class DomActions {
    static delayBetweenClicks = 500;
    static delayBetweenKeystrokes = 10;

    tabId: number;

    constructor(tabId: number) {
        this.tabId = tabId;
    }

    private async sendCommand(method: string, params?: any): Promise<any> {
        return chrome.debugger.sendCommand({ tabId: this.tabId }, method, params);
    }

    public async execCode(code: string, returnByValue: boolean = false) {
        return await this.sendCommand('Runtime.evaluate', {
            expression: code,
            returnByValue: returnByValue
        });
    }

    private async getObjectIdByXPath(xpath: string): Promise<string | undefined> {
        // Step 1: Perform XPath search
        const searchResults = await this.sendCommand('DOM.performSearch', {
            query: xpath,
            includeUserAgentShadowDOM: true,
        });

        // Step 2: Get search results
        const { nodeIds } = await this.sendCommand('DOM.getSearchResults', {
            searchId: searchResults.searchId,
            fromIndex: 0,
            toIndex: 1, // Adjust if expecting multiple results
        });

        if (nodeIds.length === 0) {
            console.log('Element not found for XPath: ' + xpath);
            return;
        }

        const elementNodeId = nodeIds[0];

        // Step 3: Resolve node to get objectId
        const result = await this.sendCommand('DOM.resolveNode', {
            nodeId: elementNodeId,
        });

        const objectId = result.object.objectId;
        return objectId;
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

    private async typeText(text: string): Promise<void> {
        for (const char of text) {
            if (char === '\n') {
                this.enterButton()
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
        await this.sendCommand("Input.dispatchKeyEvent", {
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
          })
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

    public async setFocus(xpath: string) {
        const code = `
        (function(xpath) {
          ${getNodeFromXPATH.toString()}
          ${getCoordinatesFromXPATH.toString()}
          res = getNodeFromXPATH(xpath);
          return res
        })(${JSON.stringify(xpath)});`;
        const ret = await this.execCode(code);
        console.log(ret)

        //Workaround so the nodeId can be retrieved. Might need some optimizations.
        await this.sendCommand('DOM.getDocument', {depth: -1});
        const nodeId = await this.sendCommand('DOM.requestNode', {
            objectId: ret.result.objectId,
        });
        console.log(nodeId)
        await this.sendCommand('DOM.focus', { nodeId: nodeId.nodeId })
    }

    public async pressEnter(payload: { xpath: string;}): Promise<boolean> {
        await this.setFocus(payload.xpath)
        await sleep(300)
        await this.enterButton()
        return true;
    }

    public async setValueWithXPATH(payload: { xpath: string; value: string }): Promise<boolean> {
        await this.setFocus(payload.xpath)
        await this.selectAllText();
        await this.typeText(payload.value);
        return true;
    }

    public async clickwithXPath(xpath: string) {
        // const ret_test = await this.execCode(JS_GET_INTERACTIVES, true);
        // console.log(ret_test)
        const code = `
          (function(xpath) {
            ${getNodeFromXPATH.toString()}
            res = getNodeFromXPATH(xpath);
            event = new MouseEvent('click', {
                'view': window,
                'bubbles': true,
                'cancelable': true,
                buttons: 1
            });
            res.dispatchEvent(event);
          })(${JSON.stringify(xpath)});`;
        const ret = await this.execCode(code);
        return true;
    }
}
