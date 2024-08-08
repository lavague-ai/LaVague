import React, { useCallback, useContext, useEffect, useState } from 'react';
import { Stack, Tab, TabList, TabPanel, TabPanels, Tabs, Text } from '@chakra-ui/react';
import Prompt from './Prompt';
import Logs from './Logs';
import Debug from './Debug';
import Connection from './Connection';
import { AppContext } from '../context/AppContext';
import { AgentServerState, RunningAgentState } from '../../connector';

export default function MainLayout() {
    const { serverState, setRunningAgentState, connector } = useContext(AppContext);
    const [tabIndex, setTabIndex] = useState(0);
    const [firstConnection, setFirstConnection] = useState<boolean>(false);

    const tabs: { header: React.JSX.Element; content: React.JSX.Element }[] = [];

    const requestConnection = useCallback(() => setTabIndex(1), []);

    useEffect(() => {
        if (serverState === AgentServerState.CONNECTED) {
            setTabIndex(0);
            setFirstConnection(true);
        }
        if (serverState === AgentServerState.DISCONNECTED) {
            if (firstConnection && !connector.forced_disconnection) {
                requestConnection();
            }
            setRunningAgentState(RunningAgentState.IDLE);
        }
    }, [serverState ,setTabIndex, setFirstConnection, setRunningAgentState, firstConnection, connector, requestConnection]);

    tabs.push({
        header: <>Agent</>,
        content: (
            <div className="chatbox">
                <div className="wmlogs">
                    <div className="logs">
                        <Logs logTypes={['userprompt', 'agent_log']} />
                    </div>
                </div>
                <Prompt requestConnection={requestConnection} />
            </div>
        ),
    });

    tabs.push({
        header: <>Connection</>,
        content: <Connection initialHost="127.0.0.1:8000" />,
    });

    tabs.push({
        header: <>Dev tool</>,
        content: <Debug requestConnection={requestConnection} />,
    });

    return (
        <Tabs index={tabIndex} onChange={setTabIndex}>
            <TabList>
                {tabs.map((tab, index) => (
                    <Tab key={index}>{tab.header}</Tab>
                ))}
            </TabList>
            <TabPanels>
                {tabs.map((tab, index) => (
                    <TabPanel key={index}>{tab.content}</TabPanel>
                ))}
            </TabPanels>
        </Tabs>
    );
}
