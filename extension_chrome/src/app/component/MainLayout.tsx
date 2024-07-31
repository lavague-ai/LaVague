import React, { useContext, useEffect, useState } from 'react';
import { Box, Tab, TabList, TabPanel, TabPanels, Tabs } from '@chakra-ui/react';
import Prompt from './Prompt';
import Logs from './Logs';
import Connection from './Connection';
import { AppContext } from '../context/AppContext';
import { AgentServerState } from '../../connector';

export default function MainLayout() {
    const { serverState } = useContext(AppContext);
    const [tabIndex, setTabIndex] = useState(0);

    const requestConnection = () => setTabIndex(2);

    useEffect(() => {
        if (serverState === AgentServerState.CONNECTED) {
            setTabIndex(0);
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
                            <Logs logTypes={['userprompt', 'agent_log']} />
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
