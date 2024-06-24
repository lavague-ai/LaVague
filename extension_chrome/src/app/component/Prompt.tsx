import React, { useContext, useState } from 'react';
import { AppContext } from '../context/AppContext';
import { AgentServerState } from '../../connector';
import { IconButton, Textarea } from '@chakra-ui/react';
import { ChatIcon } from '@chakra-ui/icons';

export default function Prompt({ requestConnection }: { requestConnection: () => void }) {
    const { connector, serverState } = useContext(AppContext);
    const [prompt, setPrompt] = useState('');

    const handleStart = () => {
        if (!prompt) {
            return false;
        }
        if (serverState === AgentServerState.CONNECTED) {
            connector.sendPrompt('run', prompt);
            setPrompt('');
        } else {
            requestConnection();
        }
    };

    return (
        <div className="prompt">
            <Textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Can I do something for you?"
                resize={'none'}
                required
            ></Textarea>
            <IconButton
                className="button"
                aria-label="Submit"
                icon={<ChatIcon />}
                onClick={handleStart}
                zIndex={10}
                isActive={!!prompt && serverState !== AgentServerState.CONNECTED}
            ></IconButton>
        </div>
    );
}
