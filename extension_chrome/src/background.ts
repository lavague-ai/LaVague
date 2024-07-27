import { DomActions } from './domactions';

chrome.runtime.onInstalled.addListener(() => {
    const sidePanel = (chrome as any).sidePanel;
    sidePanel.setPanelBehavior({ openPanelOnActionClick: true });
});

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
                    let eventsXpath: { [key: string]: string[] } = {};
                    await domAction.sendCommand('DOM.getDocument', { depth: -1 });
                    const object_id = await domAction.getObjectID('/html/body');
                    let result_list: any = await domAction.sendCommand('DOMDebugger.getEventListeners', { objectId: object_id, depth: -1 });
                    let result: any[] = result_list.listeners;
                    for (const xpath of xpath_list) {
                        try {
                            const object_id = await domAction.getObjectID(xpath);
                            const nodeId_OBJ = await domAction.sendCommand('DOM.requestNode', {
                                objectId: object_id,
                            });
                            const describedNode = await domAction.sendCommand('DOM.describeNode', {
                                nodeId: nodeId_OBJ.nodeId,
                            });
                            for (var listener_obj of result) {
                                if (listener_obj.backendNodeId == describedNode.node.backendNodeId)
                                    if (xpath in eventsXpath) {
                                        if (!eventsXpath[xpath].includes(listener_obj.type)) eventsXpath[xpath].push(listener_obj.type);
                                    } else {
                                        eventsXpath[xpath] = [listener_obj.type];
                                    }
                            }
                        } catch (error) {
                            console.error(error);
                        }
                    }
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
