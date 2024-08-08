import React, { useCallback, useContext, useEffect, useRef, useState } from 'react';
import { AppContext } from '../context/AppContext';
import { Badge, Stack, Text } from '@chakra-ui/react';
import { RunningAgentState } from '../../connector';
import { extractNextEngine, extractWorldModelInstruction } from '../../tools';

export type LogType = 'network' | 'cmd' | 'userprompt' | 'agent_log';

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
    get_possible_interactions: 'Get possible interactions',
};

export default function Logs({ logTypes }: { logTypes: LogType[] }) {
    const { connector, setRunningAgentState, runningAgentState } = useContext(AppContext);
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
                    if (log.type == 'agent_log') {
                        const index = logs.findIndex(log => log.type === 'agent_log' && log.log === "");
                        const foundLog = index !== -1 ? logs[index] : undefined;
                        if (foundLog === undefined) {
                            setLogs([...logs, { ...log, count: 1 }]);
                            setTimeout(() => bottomElementRef.current?.scrollIntoView({ behavior: 'smooth' }), 500);
                        } 
                        else {
                            const newLogs = [...logs];
                            newLogs[index].log = log.log;
                            setLogs(newLogs);
                        } 
                    }
                    else {
                        setLogs([...logs, { ...log, count: 1 }]);
                        setTimeout(() => bottomElementRef.current?.scrollIntoView({ behavior: 'smooth' }), 500);
                    } 
                }
            }
        },
        [logs, setLogs, bottomElementRef, logTypes]
    );

    useEffect(() => {
        let check_last_entry = false
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
                } else if (message.type === 'agent_log' && message.agent_log.world_model_output) {
                    const log_tmp = message.agent_log.world_model_output;
                    const engine = extractNextEngine(log_tmp);
                    if (engine === 'COMPLETE') {
                        const instruction = extractWorldModelInstruction(log_tmp);
                        log = instruction.indexOf('[NONE]') != -1 ? 'Objective reached' : 'Output:' + '\n' + instruction;
                    } else {
                        log = extractWorldModelInstruction(log_tmp);
                    }
                    type = 'agent_log';
                } else if (message.type === 'agent_log' && message.agent_log.current_state) {
                    log = ""
                    type = 'agent_log';
                    check_last_entry = true
                }
                else if (message.type === 'start') {
                    setRunningAgentState(RunningAgentState.RUNNING);
                } else if (message.type === 'stop') {
                    setRunningAgentState(RunningAgentState.IDLE);
                    for (let i = logs.length - 1; i >= 0; i--) {
                        if (logs[i].log === "") {
                            logs.splice(i, 1);
                        }
                    }
                    if (message.args == true) {
                        addLog({ log: 'The agent was interrupted.', type: 'agent_log' });
                    }
                }
                if (log) {
                    addLog({ log, type });
                }
                else if (check_last_entry) {
                    const curr_logs = [...logs]
                    if (curr_logs.length == 0 || curr_logs[curr_logs.length - 1].log != "")  {
                        const lo: string = log!
                        addLog({ log: lo, type });
                    }
                    check_last_entry = false                
                }
            }),
            connector.onOutputMessage((message) => addLog({ log: message.args, type: 'userprompt' })),
            connector.onSystemMessage((message) => {
                addLog({ log: message.args, type: 'agent_log' });
            }),
            connector.onDisconnect(() => {
                for (let i = logs.length - 1; i >= 0; i--) {
                    if (logs[i].log === "") {
                        logs.splice(i, 1);
                    }
                }
            }),
        ];
        return () => destructors.forEach((d) => d());
    }, [connector, addLog, setLogs, setRunningAgentState]);

    return (
        <div className="logs">
            {logs.map((log, index) => (
                <Stack key={index} className={'log ' + log.type} direction="row">
                    <Text>{log.log.length == 0 && log.type == "agent_log" ? " Thinking of next steps..." : log.log}</Text>
                    {log.count > 1 && <Badge>{log.count}</Badge>}
                </Stack>
            ))}
            <div ref={bottomElementRef}></div>
        </div>
    );
}
