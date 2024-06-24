chrome.runtime.onInstalled.addListener(() => {
    const sidePanel = (chrome as any).sidePanel;
    sidePanel.setPanelBehavior({ openPanelOnActionClick: true });
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
