import { theme as chakraTheme, extendBaseTheme } from '@chakra-ui/react';

const { Button, Input, Textarea, FormLabel, Tabs } = chakraTheme.components;

const theme = extendBaseTheme({
    components: {
        Button,
        Input,
        Textarea,
        FormLabel,
        Tabs,
    },
});

export default theme;
