import React, { useContext, useState } from 'react';
import { AppContext } from '../context/AppContext';
import {
    Accordion,
    AccordionButton,
    AccordionIcon,
    AccordionItem,
    AccordionPanel,
    Box,
    Button,
    Checkbox,
    FormLabel,
    HStack,
    IconButton,
    Input,
    Select,
    Text,
    Textarea,
    VStack,
} from '@chakra-ui/react';
import { AgentServerState, RunningAgentState } from '../../connector';
import { ChatIcon } from '@chakra-ui/icons';
import Logs from './Logs';
import * as yaml from 'js-yaml';

export default function Debug({ requestConnection }: { requestConnection: () => void }) {
    const { connector, runningAgentState, serverState } = useContext(AppContext);
    const [highlightedElements, setHighlightedElements] = React.useState<string[]>([]);
    const [inViewport, setInViewport] = useState<boolean>(true);
    const [foregroundOnly, setForegroundOnly] = useState<boolean>(true);
    const [loadHighlight, setLoadHighlight] = useState<boolean>(false);
    const [prompt, setPrompt] = useState('');
    const [action, setAction] = useState('click');
    const [element, setElement] = useState('');
    const [value, setValue] = useState('');

    const removeHighlight = () => {
        for (const xpath of highlightedElements) {
            connector.driver.remove_highlight(xpath);
        }
        setHighlightedElements([]);
    };

    const highlightElements = async () => {
        setLoadHighlight(true);
        try {
            removeHighlight();
            const res = await connector.driver.get_possible_interactions(`{"in_viewport": ${inViewport}, "foreground_only": ${foregroundOnly}}`);
            const interactions = JSON.parse(res);
            const xpaths = Object.keys(interactions);
            for (const xpath of xpaths) {
                connector.driver.highlight_elem(xpath);
            }
            setHighlightedElements(xpaths);
        } finally {
            setLoadHighlight(false);
        }
    };

    const selectInViewport = (e: React.ChangeEvent<HTMLInputElement>) => {
        setInViewport(e.target.checked);
        if (highlightElements.length) {
            highlightElements();
        }
    };

    const selectForegroundOnly = (e: React.ChangeEvent<HTMLInputElement>) => {
        setForegroundOnly(e.target.checked);
        if (highlightElements.length) {
            highlightElements();
        }
    };

    const handleStart = () => {
        if (!prompt && runningAgentState != RunningAgentState.RUNNING) {
            return false;
        }
        if (serverState === AgentServerState.CONNECTED) {
            if (runningAgentState === RunningAgentState.IDLE) {
                connector.sendPrompt('navigate', prompt);
            }
        } else {
            requestConnection();
        }
    };

    const handleKeyDownNav = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            handleStart();
        }
    };

    const executeCommand = async () => {
        try {
            await connector.driver.executeCode(
                yaml.dump([
                    {
                        actions: [
                            {
                                action: { name: action, args: { xpath: element, value } },
                            },
                        ],
                    },
                ])
            );
        } catch (e: any) {
            alert(e?.message ?? e + '');
            console.error(e);
        }
    };

    return (
        <Accordion allowMultiple={true} defaultIndex={0}>
            <AccordionItem>
                <h2>
                    <AccordionButton>
                        <Box as="span" flex="1" textAlign="left">
                            Interactive elements
                        </Box>
                        <AccordionIcon />
                    </AccordionButton>
                </h2>
                <AccordionPanel>
                    <VStack align={'start'}>
                        {highlightedElements.length && <Text>{highlightedElements.length} elements found</Text>}
                        <Checkbox isChecked={foregroundOnly} onChange={selectForegroundOnly}>
                            Foreground only
                        </Checkbox>
                        <Checkbox isChecked={inViewport} onChange={selectInViewport}>
                            In viewport only
                        </Checkbox>
                        <HStack>
                            <Button isDisabled={loadHighlight} onClick={highlightElements}>
                                Highlight
                            </Button>
                            <Button isDisabled={highlightedElements.length === 0} onClick={removeHighlight}>
                                Clear highlight
                            </Button>
                        </HStack>
                    </VStack>
                </AccordionPanel>
            </AccordionItem>
            <AccordionItem>
                <h2>
                    <AccordionButton>
                        <Box as="span" flex="1" textAlign="left">
                            Navigation engine prompt
                        </Box>
                        <AccordionIcon />
                    </AccordionButton>
                </h2>
                <AccordionPanel>
                    <div className="prompt">
                        <Textarea
                            value={prompt}
                            onChange={(e) => setPrompt(e.target.value)}
                            onKeyDown={handleKeyDownNav}
                            placeholder={'Type "LaVague.ai" in search bar and press Enter'}
                            resize={'none'}
                            isDisabled={runningAgentState == RunningAgentState.RUNNING}
                            required
                        ></Textarea>
                        <IconButton
                            className="button"
                            aria-label="Submit"
                            icon={<ChatIcon />}
                            onClick={handleStart}
                            zIndex={10}
                            isActive={!!prompt && serverState !== AgentServerState.CONNECTED && runningAgentState == RunningAgentState.IDLE}
                        ></IconButton>
                    </div>
                </AccordionPanel>
            </AccordionItem>
            <AccordionItem>
                <h2>
                    <AccordionButton>
                        <Box as="span" flex="1" textAlign="left">
                            Structured action
                        </Box>
                        <AccordionIcon />
                    </AccordionButton>
                </h2>
                <AccordionPanel>
                    <Select value={action} onChange={(e) => setAction(e.target.value)}>
                        <option value="click">Click</option>
                        <option value="setValue">Set value</option>
                        <option value="setValueAndEnter">Set value and enter</option>
                    </Select>
                    <Input mt={1} placeholder="Target xpath" value={element} onChange={(e) => setElement(e.target.value)} />
                    {action.startsWith('setValue') && <Input mt={1} placeholder="Value" value={value} onChange={(e) => setValue(e.target.value)} />}
                    <Button mt={1} onClick={executeCommand}>
                        Execute
                    </Button>
                </AccordionPanel>
            </AccordionItem>
            <AccordionItem>
                <h2>
                    <AccordionButton>
                        <Box as="span" flex="1" textAlign="left">
                            Command logs
                        </Box>
                        <AccordionIcon />
                    </AccordionButton>
                </h2>
                <AccordionPanel>
                    <Logs logTypes={['cmd']} />
                </AccordionPanel>
            </AccordionItem>
        </Accordion>
    );
}
