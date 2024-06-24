// The content script runs inside each page this extension is enabled on
// Do NOT import from here from outside of content script (other than types).

import getAnnotatedDOM, { clickElementByXPath, getNodeFromXPATH, getUniqueElementSelectorId, SetFocusOnTextBoxXPath } from './pages';
import { copyToClipboard } from './pages';
import attachFile from './pages';
import ripple from './pages';

export const rpcMethods = {
    getAnnotatedDOM,
    getUniqueElementSelectorId,
    ripple,
    copyToClipboard,
    attachFile,
    clickElementByXPath,
    getNodeFromXPATH,
    SetFocusOnTextBoxXPath,
} as const;

export type RPCMethods = typeof rpcMethods;
type MethodName = keyof RPCMethods;

export type RPCMessage = {
    [K in MethodName]: {
        method: K;
        payload: Parameters<RPCMethods[K]>;
    };
}[MethodName];

// This function should run in the content script
export const initializeRPC = () => {
    chrome.runtime.onMessage.addListener((message: RPCMessage, sender, sendResponse): true | undefined => {
        const { method, payload } = message;
        console.log('RPC listener', method);
        if (method in rpcMethods) {
            // @ts-expect-error - we know this is valid (see pageRPC)
            const resp = rpcMethods[method as keyof RPCMethods](...payload);
            if (resp instanceof Promise) {
                resp.then((resolvedResp) => {
                    sendResponse(resolvedResp);
                });
            } else {
                sendResponse(resp);
            }
            return true;
        }
    });
};
