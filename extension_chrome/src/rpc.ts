// The content script runs inside each page this extension is enabled on
// Do NOT import from here from outside of content script (other than types).
import { getPossibleInteractions } from './pages';

export const initializeRPC = () => {
    chrome.runtime.onMessage.addListener(function (request, sender, sendResponse) {
        async function tryAndSend(fn: () => Promise<any>) {
            try {
                sendResponse({ response: await fn() });
            } catch (error: any) {
                console.error('Error:', error);
                sendResponse({ error: error.toString() });
            }
        }
        if (request.method == 'get_possible_interactions') {
            tryAndSend(() => getPossibleInteractions(request.message));
        }
        return true;
    });
};
