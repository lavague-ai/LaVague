// The content script runs inside each page this extension is enabled on
// Do NOT import from here from outside of content script (other than types).
import { get_possible_interactions } from './pages';

export const initializeRPC = () => {
    chrome.runtime.onMessage.addListener(function (request, sender, sendResponse) {
        if (request.method == 'get_possible_interactions') {
            try {
                (async () => {
                    const res = await get_possible_interactions(request.message);
                    sendResponse({ response: res });
                })();
            } catch (error) {
                console.error('Error getting possible interactions:', error);
                sendResponse({ error: 'Failed to get interactions' });
            }
        }
        return true;
    });
};
