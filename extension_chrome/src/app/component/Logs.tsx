import React, { useCallback, useContext, useEffect, useRef, useState } from 'react';
import { AppContext } from '../context/AppContext';
import { Badge, Stack, Text } from '@chakra-ui/react';

type LogType = 'network' | 'cmd' | 'userprompt' | 'agent_log';

interface Log {
    type: LogType;
    log: string;
}

interface RepeatableLog extends Log {
    count: number;
}

const COMMAND_LABELS: { [key: string]: string } = {
    get_url: 'Get URL',
    get_html: 'Get HTML',
    get: 'Navigate',
    back: 'Go back',
    get_screenshot: 'Take screenshot',
    execute_script: 'Execute script',
    exec_code: 'Execute code',
    is_visible: 'Check visibility',
};

export default function Logs({ logTypes }: { logTypes: LogType[] }) {
    const { connector } = useContext(AppContext);
    const [logs, setLogs] = useState<RepeatableLog[]>([]);
    const bottomElementRef = useRef<HTMLDivElement | null>(null);

    const addLog = useCallback(
        (log: Log) => {
            if (logTypes.includes(log.type)) {
                if (logs.length > 0 && logs[logs.length - 1].log === log.log) {
                    const newLogs = [...logs];
                    newLogs[newLogs.length - 1].count++;
                    setLogs(newLogs);
                } else {
                    setLogs([...logs, { ...log, count: 1 }]);
                    setTimeout(() => bottomElementRef.current?.scrollIntoView({ behavior: 'smooth' }), 500);
                }
            }
        },
        [logs, setLogs, bottomElementRef, logTypes]
    );

    useEffect(() => {
        const destructors = [
            connector.onError((err: any) => {
                if (err instanceof Event && err.target instanceof WebSocket) {
                    addLog({ log: 'Unable to connect. Please ensure that the host is valid and points to an active driver server', type: 'network' });
                } else {
                    console.error(err);
                }
            }),
            connector.onInputMessage((message) => {
                let log: string | null = null;
                let type: LogType = 'cmd';
                if (message.command) {
                    log = COMMAND_LABELS[message.command];
                } else if (message.type === 'agent_log') {
                    log = message.agent_log.world_model_output;
                    type = 'agent_log';
                }
                if (log) {
                    addLog({ log, type });
                }
            }),
            connector.onOutputMessage((message) => addLog({ log: message.args, type: 'userprompt' })),
        ];
        return () => destructors.forEach((d) => d());
    }, [connector, addLog, setLogs]);

    return (
        <div className="logs">
            {logs.map((log, index) => (
                <Stack key={index} className={'log ' + log.type} direction="row">
                    <Text>{log.log}</Text>
                    {log.count > 1 && <Badge>{log.count}</Badge>}
                </Stack>
            ))}
            <div ref={bottomElementRef}></div>
        </div>
    );
}
