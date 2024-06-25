import React, { useContext, useEffect, useState } from 'react';
import { AppContext } from '../context/AppContext';
import { AgentServerState } from '../../connector';
import { Button, FormControl, FormHelperText, FormLabel, Input, Text } from '@chakra-ui/react';

const LABELS: { [state in AgentServerState]: string } = {
    [AgentServerState.CONNECTED]: 'Connected',
    [AgentServerState.DISCONNECTED]: 'Disconnected',
    [AgentServerState.CONNECTING]: 'Connecting...',
};

export default function Connection({ initialHost }: { initialHost: string }) {
    const { serverState, connector } = useContext(AppContext);
    const [host, setHost] = useState(initialHost);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        connector.connect(initialHost);
    }, [connector, initialHost]);

    const handleConnect = async () => {
        setError(null);
        try {
            await connector.connect(host);
        } catch (err: any) {
            if (err instanceof Event && err.target instanceof WebSocket) {
                setError('Unable to connect. Please ensure that the host is valid and points to an active driver server.');
            } else {
                setError((err.message ?? err) + '');
            }
        }
    };

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
                    <Button onClick={handleConnect} isDisabled={serverState === AgentServerState.CONNECTING} mt={3}>
                        Connect
                    </Button>
                )}
            </div>
            {error && (
                <Text color={'red'} mt={4}>
                    {error}
                </Text>
            )}
        </div>
    );
}
