import React, { useContext, useEffect, useState } from 'react';
import { Stack, Tab, TabList, TabPanel, TabPanels, Tabs, Text } from '@chakra-ui/react';
import { Link } from 'react-router-dom';
import Prompt from './Prompt';
import Logs from './Logs';
import Connection from './Connection';
import { AppContext } from '../context/AppContext';
import { AgentServerState, RunningAgentState } from '../../connector';

export default function MainLayout() {
    const { serverState, setRunningAgentState, connector } = useContext(AppContext);
    const [tabIndex, setTabIndex] = useState(0);
    const [firstConnection, setFirstConnection] = useState<boolean>(false);
    const requestConnection = () => setTabIndex(2);

    useEffect(() => {
        if (serverState === AgentServerState.CONNECTED) {
            setTabIndex(0);
            setFirstConnection(true);
        }
        if (serverState === AgentServerState.DISCONNECTED) {
            if (firstConnection && !connector.forced_disconnection) {
                setTabIndex(2);
            }
            setRunningAgentState(RunningAgentState.IDLE)
        }
    }, [serverState]);

    return (
        <Tabs index={tabIndex} onChange={setTabIndex}>
            <TabList>
                <Tab>Agent</Tab>
                <Tab>Logs</Tab>
                <Tab>Connection</Tab>
            </TabList>
            <TabPanels>
                <TabPanel>
                    <div className="chatbox">
                        <div className="wmlogs">
                            <div className="logs">
                            <Stack className={'log agent_log'} direction="row">
                            <Text>
                                    Welcome to Lavague Chrome Extension!
                                    <br />
                                    <br />
                                    In order to get started easily, please run the command "lavague-serve" on your terminal.
                                    <br />
                                    Then, please write in the connect tab the IP you would like to reach (for example, 127.0.0.1).
                                    <br />
                                    <br />
                                    You can find more details about the usage and the project:{' '}
                                    <a href="https://docs.lavague.ai" target="_blank">
                                        https://docs.lavague.ai
                                    </a>
                                </Text>
                            </Stack>
                            <Logs logTypes={['userprompt', 'agent_log']} />
                            </div>
                        </div>
                        <Prompt requestConnection={requestConnection} />
                    </div>
                </TabPanel>
                <TabPanel>
                    <Logs logTypes={['cmd']} />
                </TabPanel>
                <TabPanel>
                    <Connection initialHost="127.0.0.1:8000" />
                </TabPanel>
            </TabPanels>
        </Tabs>
    );
}
