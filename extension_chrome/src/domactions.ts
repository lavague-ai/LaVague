import { sleep, waitTillStable } from './tools';

const DEFAULT_INTERVAL = 500;
const DEFAULT_TIMEOUT = 10000; // 10 seconds

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

    public async execCode(code: string) {
        return await this.sendCommand('Runtime.evaluate', {
            expression: code,
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

    private async typeText(text: string, shiftEnter = false): Promise<void> {
        const enterModifier = shiftEnter ? 8 : 0;
        for (const char of text) {
            // handle enter
            if (char === '\n') {
                await this.sendCommand('Input.dispatchKeyEvent', {
                    type: 'rawKeyDown',
                    key: 'Enter',
                });
                await sleep(DomActions.delayBetweenKeystrokes / 2);
                await this.sendCommand('Input.dispatchKeyEvent', {
                    type: 'keyUp',
                    key: 'Enter',
                });
                continue;
            }
            await this.sendCommand('Input.dispatchKeyEvent', {
                type: 'keyDown',
                text: char,
            });
            await sleep(DomActions.delayBetweenKeystrokes / 2);
            await this.sendCommand('Input.dispatchKeyEvent', {
                type: 'keyUp',
                text: char,
            });
            await sleep(DomActions.delayBetweenKeystrokes / 2);
        }
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

    public async setValueWithXPATH(payload: { xpath: string; value: string; shiftEnter?: boolean }): Promise<boolean> {
        const code = `
      (function(xpath) {
        function getNodeFromXPATH(xpath) {
          var result = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
          return result.singleNodeValue;
        }
    
        function SetFocusOnTextBoxXPath(xpath: string): boolean {
          var textbox = getNodeFromXPATH(xpath)
          var success = true;
        
          if (textbox) {
            if (textbox instanceof HTMLInputElement) {
                textbox.focus();
            }
            // Check if textbox is a textarea element
            else if (textbox instanceof HTMLTextAreaElement) {
                textbox.focus();
            }
            else {
              console.log("failed to focus the textbox")
              success = false;
          }
          } else {
              console.log("failed to focus the textbox")
              success = false;
          }
          return success
        }
        
        SetFocusOnTextBoxXPath(xpath);
      })(${JSON.stringify(payload.xpath)});`;
        await this.selectAllText();
        await this.typeText(payload.value, payload.shiftEnter ?? false);
        return true;
    }

    public async clickwithXPath(xpath: string) {
        const code = `
      (function(xpath) {
        function getNodeFromXPATH(xpath) {
          var result = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
          return result.singleNodeValue;
        }
    
        function clickElementByXPath(xpath) {
          var element = getNodeFromXPATH(xpath);
          if (element && element instanceof HTMLElement) {
            if (element.tagName.toLowerCase() === 'a' && element.href) {
              // Navigate to the href URL to ensure history update
              console.log("Navigating to:", element.href);
              window.location.href = element.href;
            } else {
              // Simulate a user-initiated click
              var event = new MouseEvent('click', {
                view: window,
                bubbles: true,
                cancelable: true,
                buttons: 1
              });
              element.dispatchEvent(event);
              if (element.tagName.toLowerCase() === 'button' || element.tagName.toLowerCase() === 'input' && element.type === 'submit') {
                // Special handling for button and submit inputs to ensure form submission
                element.form.submit();
              }
            }
            console.log(element.textContent);
            console.log("clicked!");
            return true;
          } else {
            console.log("failed to click!");
            return false;
          }
        }
    
        clickElementByXPath(xpath);
      })(${JSON.stringify(xpath)});`;
        const ret = this.execCode(code);
        console.log(ret);
        return true;
    }
}
