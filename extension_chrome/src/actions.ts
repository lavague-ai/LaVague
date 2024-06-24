import { DomActions } from './domactions';
import { sleep } from './tools';
import { type ToolOperation } from './actionSchemas';

export async function clickWithXPath(domActions: DomActions, xpath: string): Promise<boolean> {
    console.log('clickWithXPath', xpath);
    return await domActions.clickwithXPath(xpath);
}

export async function setValueWithXPATH(domActions: DomActions, xpath: string, value: string): Promise<boolean> {
    console.log('setValueWithXPATH', xpath);
    return await domActions.setValueWithXPATH({
        xpath,
        value,
    });
}

export async function scroll(domActions: DomActions, value: string) {
    switch (value) {
        case 'up':
            await domActions.scrollUp();
            break;
        case 'down':
            await domActions.scrollDown();
            break;
        case 'top':
            await domActions.scrollToTop();
            break;
        case 'bottom':
            await domActions.scrollToBottom();
            break;
        default:
            console.error('Invalid scroll value', value);
    }
}

function createOperateTool(
    click: (domActions: DomActions, label: string) => Promise<boolean>,
    setValue: (domActions: DomActions, label: string, value: string) => Promise<boolean>
): (tabId: number, action: ToolOperation) => Promise<void> {
    return async (tabId: number, action: ToolOperation) => {
        const domActions = new DomActions(tabId);
        console.log('operateTool', action);
        switch (action.name) {
            case 'scroll':
                await scroll(domActions, action.args.value);
                break;
            case 'wait':
                console.log('Wait...');
                await sleep(action.args.value * 1000);
                console.log('Done waiting.');
                break;
            case 'fail':
                console.warn('Action failed.');
                break;
            case 'click': {
                const success = await click(domActions, action.args.xpath);
                if (!success) {
                    console.error('Unable to find element with label: ', action.args.xpath);
                }
                break;
            }
            case 'setValue': {
                const success = await setValue(domActions, action.args.xpath, action.args.value || '');
                if (!success) {
                    console.error('Unable to find element with xpath: ', action.args.xpath);
                }
                break;
            }
            case 'setValueAndEnter': {
                const success = await setValue(domActions, action.args.xpath, (action.args.value || '') + '\n');
                if (!success) {
                    console.error('Unable to find element with xpath: ', action.args.xpath);
                }
                break;
            }
            default:
                console.log('Unknown action name', action);
        }
    };
}

// DOM agent currently use this (using xpath instead of label)
export const operateToolWithXPATH = createOperateTool(clickWithXPath, setValueWithXPATH);
