import React, { createContext, useEffect, useMemo, useState } from 'react';
import { AgentServerConnector, AgentServerState } from '../../connector';

export interface AppContextProps {
    connector: AgentServerConnector;
    serverState: AgentServerState;
}

export const AppContext = createContext<AppContextProps>({
    connector: new AgentServerConnector(),
    serverState: AgentServerState.DISCONNECTED,
});

export const AppProvider = ({ children, port }: { children: React.ReactNode; port: chrome.runtime.Port }) => {
    const [serverState, setServerState] = useState<AgentServerState>(AgentServerState.DISCONNECTED);
    const connector = useMemo(() => new AgentServerConnector(), []);

    useEffect(() => {
        connector.driver.onTabDebugged = (tabId) => port.postMessage({ type: 'tab_debug', tabId });
        return connector.onStateChange(setServerState);
    }, [connector, port]);

    return (
        <AppContext.Provider
            value={{
                connector,
                serverState,
            }}
        >
            {children}
        </AppContext.Provider>
    );
};
