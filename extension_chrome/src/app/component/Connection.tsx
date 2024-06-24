import React, { useContext, useEffect, useState } from 'react';
import { AppContext } from '../context/AppContext';
import { AgentServerState } from '../../connector';
import { Button, FormControl, FormHelperText, FormLabel, Input } from '@chakra-ui/react';

const LABELS: { [state in AgentServerState]: string } = {
    [AgentServerState.CONNECTED]: 'Connected',
    [AgentServerState.DISCONNECTED]: 'Disconnected',
    [AgentServerState.CONNECTING]: 'Connecting...',
};

export default function Connection({ initialHost }: { initialHost: string }) {
    const { serverState, connector } = useContext(AppContext);
    const [host, setHost] = useState(initialHost);

    useEffect(() => {
        connector.connect(initialHost);
    }, [connector, initialHost]);

    return (
        <div className="connection">
            <div className="server">
                <FormControl>
                    <FormLabel htmlFor="host">Agent server host</FormLabel>
                    <Input type="text" value={host} onChange={(e) => setHost(e.target.value)} required />
                    <FormHelperText mt={1}>{LABELS[serverState]}</FormHelperText>
                </FormControl>
                {serverState === AgentServerState.CONNECTED ? (
                    <Button onClick={() => connector.disconnect()} mt={3}>
                        Disconnect
                    </Button>
                ) : (
                    <Button onClick={() => connector.connect(host)} mt={3}>
                        Connect
                    </Button>
                )}
            </div>
        </div>
    );
}
