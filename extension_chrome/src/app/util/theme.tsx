import { theme as chakraTheme, extendBaseTheme } from '@chakra-ui/react';

const { Button, Input, Textarea, FormLabel, Tabs, Badge } = chakraTheme.components;

const theme = extendBaseTheme({
    components: {
        Button,
        Input,
        Textarea,
        FormLabel,
        Tabs,
        Badge,
    },
});

export default theme;
