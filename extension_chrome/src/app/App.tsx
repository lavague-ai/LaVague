import React, { useContext } from 'react';
import { createRoot } from 'react-dom/client';
import { AppContext, AppProvider } from './context/AppContext';
import MainLayout from './component/MainLayout';
import { ChakraProvider, Spinner, Box, Text } from '@chakra-ui/react';
import theme from './util/theme';
import { RunningAgentState } from '../connector';

export default function App({ port }: { port: chrome.runtime.Port }) {
    return (
        <AppProvider port={port}>
            <ChakraProvider theme={theme}>
                <MainContent />
            </ChakraProvider>
        </AppProvider>
    );
}

function MainContent() {
    return (
        <>
            {<img src="images/lavague.png" className="logo" />}
            <MainLayout />
        </>
    );
}

export function render(port: chrome.runtime.Port) {
    const root = createRoot(document.getElementById('app')!);
    root.render(<App port={port} />);
}
