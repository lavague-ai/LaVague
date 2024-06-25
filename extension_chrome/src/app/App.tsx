import React from 'react';
import { createRoot } from 'react-dom/client';
import { AppProvider } from './context/AppContext';
import MainLayout from './component/MainLayout';
import { ChakraProvider } from '@chakra-ui/react';
import theme from './util/theme';

export default function App({ port }: { port: chrome.runtime.Port }) {
    return (
        <AppProvider port={port}>
            <ChakraProvider theme={theme}>
                <img src="images/lavague.png" className="logo" />
                <MainLayout />
            </ChakraProvider>
        </AppProvider>
    );
}

export function render(port: chrome.runtime.Port) {
    const root = createRoot(document.getElementById('app')!);
    root.render(<App port={port} />);
}
