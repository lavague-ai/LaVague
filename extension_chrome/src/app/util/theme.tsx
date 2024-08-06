import { theme as chakraTheme, extendBaseTheme } from '@chakra-ui/react';

const { Button, Input, Textarea, FormLabel, Tabs, Badge, List, Accordion, Checkbox, Select } = chakraTheme.components;

const theme = extendBaseTheme({
    components: {
        Button,
        Input,
        Textarea,
        FormLabel,
        Tabs,
        Badge,
        List,
        Accordion,
        Checkbox,
        Select,
    },
});

export default theme;
