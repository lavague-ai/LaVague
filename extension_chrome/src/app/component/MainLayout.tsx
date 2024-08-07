import React, { useCallback, useContext, useEffect, useState } from 'react';
import { List, ListItem, Stack, Tab, TabList, TabPanel, TabPanels, Tabs, Text } from '@chakra-ui/react';
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
    }, [serverState, setTabIndex, setFirstConnection, setRunningAgentState, firstConnection, connector, requestConnection]);

    tabs.push({
        header: <>Agent</>,
        content: (
            <div className="chatbox">
                <div className="wmlogs">
                    <div className="logs">
                        <Stack className={'log agent_log'} direction="column">
                            <Text>Welcome to the Lavague Chrome Extension!</Text>
                            <Text mt={3}>To get started:</Text>
                            <List mt={1}>
                                <ListItem>
                                    - Open your terminal and type <code>lavague-serve</code> to run the command ;
                                </ListItem>
                                <ListItem mt={1}>
                                    - Go to the{' '}
                                    <span style={{ cursor: 'pointer' }} onClick={() => requestConnection()}>
                                        &quot;Connection&quot;
                                    </span>{' '}
                                    tab and enter the host you want to reach (e.g., 127.0.0.1:8000).
                                </ListItem>
                            </List>
                            <Text mt={3}>
                                For more information and details, visit{' '}
                                <a href="https://docs.lavague.ai" target="_blank" rel="noreferrer">
                                    https://docs.lavague.ai
                                </a>
                            </Text>
                        </Stack>
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
