const DEFAULT_ENGINES: string[] = ['Navigation Controls', 'Python Engine', 'Navigation Engine', 'COMPLETE'];

export async function copyToClipboard(text: string) {
    await navigator.clipboard.writeText(text);
}

export async function sleep(ms: number) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

export function truthyFilter<T>(value: T | null | undefined): value is T {
    return Boolean(value);
}

export function extractNextEngine(text: string, nextEngines: string[] = DEFAULT_ENGINES): string {
    // Define the patterns to match "Next engine:"
    const nextEnginePatterns: RegExp[] = [/Next engine:\s*(.*)/, /### Next Engine:\s*(.*)/];

    for (const pattern of nextEnginePatterns) {
        try {
            const nextEngineMatch = text.match(pattern);
            if (nextEngineMatch) {
                const extractedText = nextEngineMatch[1].trim();
                // Check if the extracted text matches any of the provided engines
                for (const engine of nextEngines) {
                    if (extractedText.toLowerCase().includes(engine.toLowerCase())) {
                        return engine;
                    }
                }
            }
        } catch (e) {}
    }

    throw new Error(`No next engine found in the text: ${text}`);
}

export function extractWorldModelInstruction(text: string): string {
    // Define the instruction patterns as an array of regular expressions
    const instructionPatterns: RegExp[] = [
        /Instruction:\s*((?:- .*\n?)+)/, // For multi-line hyphenated instructions
        /### Instruction:\s*((?:- .*\n?)+)/, // For multi-line hyphenated instructions with ### prefix
        /Instruction:\s*((?:\d+\.\s.*\n?)+)/, // For multi-line numbered instructions
        /### Instruction:\s*((?:\d+\.\s.*\n?)+)/, // For multi-line numbered instructions with ### prefix
        /Instruction:\s*```([\s\S]*?)```/, // For block of text within triple backticks
        /### Instruction:\s*```([\s\S]*?)```/, // For block of text within triple backticks with ### prefix
        /Instruction:\s*(.*)/, // For single-line instructions
        /### Instruction:\s*(.*)/, // For single-line instructions with ### prefix
    ];

    let longestInstruction = '';

    for (const pattern of instructionPatterns) {
        const matches = text.match(pattern);
        if (matches && matches[1]) {
            let instructionText = matches[1];
            // Check if the instruction is multi-line or single-line
            if (instructionText.includes('\n')) {
                // Remove newlines and extra spaces for multi-line instructions
                instructionText = instructionText.split('\n').join(' ').trim();
            }
            // Update longestInstruction if the current one is longer
            if (instructionText.length > longestInstruction.length) {
                longestInstruction = instructionText;
            }
        }
    }

    if (longestInstruction) {
        return longestInstruction;
    }

    throw new Error('No instruction found in the text.');
}

export function ripple(x: number, y: number) {
    const rippleRadius = 30;
    const ripple = document.createElement('div');
    ripple.classList.add('web-agent-ripple');
    ripple.style.width = ripple.style.height = `${rippleRadius * 2}px`;
    // Take scroll position into account
    ripple.style.top = `${window.scrollY + y - rippleRadius}px`;
    ripple.style.left = `${x - rippleRadius}px`;

    document.body.appendChild(ripple);

    // remove after the animation to finish
    // but we don't need to `await` it
    sleep(800).then(() => {
        ripple.remove();
    });
}

export function xpathToCss(xpath: string) {
    // Replace double slashes with spaces
    const css = xpath
        .replace(/\/\//g, ' ')
        .replace(/\//g, ' > ')
        .replace(/\[(\d+)\]/g, (match, p1) => `:nth-of-type(${p1})`)
        .replace(/@/g, '')
        .replace(/\[contains\((.*?),\s*'(.*?)'\)\]/g, (match, p1, p2) => `[${p1}*='${p2}']`)
        .replace(/\[name\(\)='(.*?)'\]/g, '$1')
        .replace(/\[(.*?)\]/g, '[$1]');

    return css.trim();
}

export async function waitFor(predicate: () => Promise<boolean>, interval: number, _maxChecks: number, rejectOnTimeout = true): Promise<void> {
    // special case for 0 maxChecks (wait forever)
    const maxChecks = _maxChecks === 0 ? Infinity : _maxChecks;
    let checkCount = 0;
    return new Promise((resolve, reject) => {
        const intervalId = setInterval(async () => {
            if (await predicate()) {
                clearInterval(intervalId);
                resolve();
            } else {
                checkCount++;
                if (checkCount >= maxChecks) {
                    clearInterval(intervalId);
                    if (rejectOnTimeout) {
                        reject(new Error('Timed out waiting for condition'));
                    } else {
                        resolve();
                    }
                }
            }
        }, interval);
    });
}

export async function waitTillStable(
    getSize: () => Promise<number>,
    interval: number,
    timeout: number,
    rejectOnTimeout = false // default to assuming stable after timeout
): Promise<void> {
    let lastSize = 0;
    let countStableSizeIterations = 0;
    const minStableSizeIterations = 3;

    return waitFor(
        async () => {
            const currentSize = await getSize();

            console.log('last: ', lastSize, ' <> curr: ', currentSize);

            if (lastSize != 0 && currentSize === lastSize) {
                countStableSizeIterations++;
            } else {
                countStableSizeIterations = 0; //reset the counter
            }

            if (countStableSizeIterations >= minStableSizeIterations) {
                console.log('Size stable! Assume fully rendered..');
                return true;
            }

            lastSize = currentSize;
            return false;
        },
        interval,
        timeout / interval,
        rejectOnTimeout
    );
}

export function enumKeys<O extends object, K extends keyof O = keyof O>(obj: O): K[] {
    return Object.keys(obj) as K[];
}

export function enumValues<O extends object>(obj: O): O[keyof O][] {
    return enumKeys(obj).map((key) => obj[key]);
}

// TypeScript function
function scrollIntoViewFunction() {
    // @ts-expect-error this is run in the browser context
    this.scrollIntoView({
        block: 'center',
        inline: 'center',
    });
}
// Convert the TypeScript function to a string
export const scrollScriptString = scrollIntoViewFunction.toString();
