function getInteractions(e: any, xpath: string, eventDict: any) {
    if (e == null) {
        return [];
    }
    const tag = e.tagName.toLowerCase();
    if (
        !e.checkVisibility() ||
        e.hasAttribute('disabled') ||
        e.hasAttribute('readonly') ||
        e.getAttribute('aria-hidden') === 'true' ||
        e.getAttribute('aria-disabled') === 'true' ||
        (tag === 'input' && e.getAttribute('type') === 'hidden')
    ) {
        return [];
    }
    const rect = e.getBoundingClientRect();
    if (rect.width + rect.height < 5) {
        return [];
    }
    const style = getComputedStyle(e);
    if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') {
        return [];
    }
    const role = e.getAttribute('role');
    const clickableInputs = ['submit', 'checkbox', 'radio', 'color', 'file', 'image', 'reset'];
    function hasEvent(n: any) {
        const eventExistsInArray = xpath in eventDict && eventDict[xpath].includes(n);
        const elementHasAttribute = e.hasAttribute('on' + n);
        return eventExistsInArray || elementHasAttribute;
    }
    const evts = [];
    if (
        hasEvent('keydown') ||
        hasEvent('keyup') ||
        hasEvent('keypress') ||
        hasEvent('keydown') ||
        hasEvent('input') ||
        e.isContentEditable ||
        ((tag === 'input' || tag === 'textarea' || role === 'searchbox' || role === 'input') && !clickableInputs.includes(e.getAttribute('type')!))
    ) {
        evts.push('TYPE');
    }
    if (
        tag === 'a' ||
        tag === 'button' ||
        role === 'button' ||
        role === 'checkbox' ||
        hasEvent('click') ||
        hasEvent('mousedown') ||
        hasEvent('mouseup') ||
        hasEvent('dblclick') ||
        style.cursor === 'pointer' ||
        (tag === 'input' && clickableInputs.includes(e.getAttribute('type'))) ||
        e.hasAttribute('aria-haspopup') ||
        tag === 'select' ||
        role === 'select'
    ) {
        evts.push('CLICK');
    }
    return evts;
}

function getInteractives(elements: any, foreground_only = false): Record<string, any> {
    const windowHeight = window.innerHeight || document.documentElement.clientHeight;
    const windowWidth = window.innerWidth || document.documentElement.clientWidth;

    return Object.fromEntries(
        Object.entries(elements).filter(([xpath]) => {
            const element = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue as HTMLElement;
            if (!element) return false;

            const rect = element.getBoundingClientRect();

            const elemCenter = {
                x: rect.left + rect.width / 2,
                y: rect.top + rect.height / 2,
            };

            if (elemCenter.x < 0) return false;
            if (elemCenter.x > windowWidth) return false;
            if (elemCenter.y < 0) return false;
            if (elemCenter.y > windowHeight) return false;

            if (!foreground_only) {
                return true;
            }

            try {
                let pointContainer = document.elementFromPoint(elemCenter.x, elemCenter.y);
                while (pointContainer) {
                    if (pointContainer === element) return true;
                    if (pointContainer == null) return true;
                    pointContainer = pointContainer.parentNode as HTMLElement | null;
                }
            } catch (e) {
                console.error(e);
            }

            return false;
        })
    );
}

async function getEventListenersAll(xpath: string[]) {
    const res = await chrome.runtime.sendMessage({ action: 'getEventListeners_all', xpath_list: xpath });
    return res.response;
}

function traverse(node: any, xpath: string, results: any) {
    if (node.nodeType === Node.ELEMENT_NODE) {
        results.push(xpath);
    }
    const countByTag: { [key: string]: number } = {};
    for (let child = node.firstChild; child; child = child.nextSibling) {
        let tag = child.nodeName.toLowerCase();
        if (tag.includes(':')) continue; //namespace
        const isLocal = ['svg'].includes(tag);
        if (isLocal) {
            tag = `*[local-name() = '${tag}']`;
        }
        countByTag[tag] = (countByTag[tag] || 0) + 1;
        let childXpath = xpath + '/' + tag;
        if (countByTag[tag] > 1) {
            childXpath += '[' + countByTag[tag] + ']';
        }
        if (tag === 'iframe') {
            try {
                traverse(child.contentWindow!.document.body, childXpath + '/html/body', results);
            } catch (e) {
                // iframe access blocked
            }
        } else {
            traverse(child, childXpath, results);
        }
    }
    return results;
}

function getElementByXpath(xpath: string) {
    return document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
}

export async function getPossibleInteractions(args: string) {
    let final_results: { [key: string]: string[] } = {};
    let xpath_list: string[] = [];
    const args_parsed = JSON.parse(args);
    xpath_list = traverse(document.body, '/html/body', xpath_list);
    const results_events = await getEventListenersAll(xpath_list);
    for (const xpath of xpath_list) {
        const elem = getElementByXpath(xpath);
        const interactions = getInteractions(elem, xpath, results_events);
        if (interactions.length > 0) {
            final_results[xpath] = interactions;
        }
    }
    if (args_parsed['in_viewport'] == true) {
        final_results = getInteractives(final_results, args_parsed['foreground_only']);
    }
    return JSON.stringify(final_results);
}
