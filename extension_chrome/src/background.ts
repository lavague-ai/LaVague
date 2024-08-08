import { DomActions } from './domactions';

chrome.runtime.onInstalled.addListener(() => {
    const sidePanel = (chrome as any).sidePanel;
    sidePanel.setPanelBehavior({ openPanelOnActionClick: true });
    // Forcefully inject the RPC script on the open tabs, as chrome will usually only start to inject the code after the page is refreshed...
    initRPCScript();
});

function injectIntoTab(tab: any) {
    const manifest = chrome.runtime.getManifest();
    const scripts = manifest.content_scripts![0].js;
    const s = scripts!.length;
    for (let i = 0; i < s; i++) {
        chrome.scripting.executeScript({
            target: { tabId: tab.id },
            files: [scripts![i]],
        });
    }
}

function initRPCScript(): void {
    chrome.windows.getAll({ populate: true }, (windows: chrome.windows.Window[]) => {
        windows.forEach((currentWindow) => {
            currentWindow.tabs?.forEach((currentTab) => {
                if (currentTab.url && currentTab.url.match(/(file|http|https):\/\//gi)) {
                    injectIntoTab(currentTab);
                }
            });
        });
    });
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === 'getEventListeners_all') {
        const { xpath_list } = message;
        const tabId = sender.tab?.id;
        if (!tabId) {
            console.error('No tabId found in the sender');
            sendResponse({ response: {} });
        } else {
            const domAction = new DomActions(tabId!);
            (async () => {
                try {
                    const eventsXpath: { [key: string]: string[] } = {};
                    await domAction.sendCommand('DOM.getDocument', { depth: -1 });
                    const bodyId = await domAction.getObjectID('/html/body');
                    const result_list: any = await domAction.sendCommand('DOMDebugger.getEventListeners', { objectId: bodyId, depth: -1 });
                    const result: any[] = result_list.listeners;
                    await Promise.all(
                        xpath_list.map(async (xpath: string) => {
                            try {
                                const objectId = await domAction.getObjectID(xpath);
                                if (objectId != null) {
                                    const nodeId_OBJ = await domAction.sendCommand('DOM.requestNode', {
                                        objectId: objectId,
                                    });
                                    const describedNode = await domAction.sendCommand('DOM.describeNode', {
                                        nodeId: nodeId_OBJ.nodeId,
                                    });
                                    for (const listener_obj of result) {
                                        if (listener_obj.backendNodeId == describedNode.node.backendNodeId) {
                                            if (!(xpath in eventsXpath)) {
                                                eventsXpath[xpath] = [listener_obj.type];
                                            } else if (!eventsXpath[xpath].includes(listener_obj.type)) {
                                                eventsXpath[xpath].push(listener_obj.type);
                                            }
                                        }
                                    }
                                }
                            } catch (error) {
                                console.error(error);
                            }
                        })
                    );
                    sendResponse({ response: eventsXpath });
                } catch (error) {
                    console.error(error);
                    sendResponse({ response: {} });
                }
            })();
        }
    }
    return true;
});

chrome.runtime.onConnect.addListener(function (port) {
    if (port.name === 'content') {
        let tabId: number | null = null;
        port.onMessage.addListener((msg: any) => {
            if (msg.type === 'tab_debug') {
                tabId = msg.tabId;
            }
        });
        port.onDisconnect.addListener(() => {
            if (tabId != null) {
                chrome.debugger.detach({ tabId });
            }
        });
    }
});
