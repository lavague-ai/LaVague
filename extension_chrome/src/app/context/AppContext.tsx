import React, { createContext, useEffect, useMemo, useState } from 'react';
import { AgentServerConnector, AgentServerState, RunningAgentState } from '../../connector';

export interface AppContextProps {
    connector: AgentServerConnector;
    serverState: AgentServerState;
    runningAgentState: RunningAgentState;
    setRunningAgentState: React.Dispatch<React.SetStateAction<RunningAgentState>>;
}

export const AppContext = createContext<AppContextProps>({
    connector: new AgentServerConnector(),
    serverState: AgentServerState.DISCONNECTED,
    runningAgentState: RunningAgentState.IDLE,
    setRunningAgentState: () => {},
});

export const AppProvider = ({ children, port }: { children: React.ReactNode; port: chrome.runtime.Port }) => {
    const [serverState, setServerState] = useState<AgentServerState>(AgentServerState.DISCONNECTED);
    const [runningAgentState, setRunningAgentState] = useState<RunningAgentState>(RunningAgentState.IDLE);
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
                runningAgentState,
                setRunningAgentState,
            }}
        >
            {children}
        </AppContext.Provider>
    );
};
