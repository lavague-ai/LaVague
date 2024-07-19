function getInteractions(e: any, xpath: string, eventDict: any) {
    if (e == null) {
        return [];
    }
    const tag = e.tagName.toLowerCase();
    if (!e.checkVisibility() || e.hasAttribute('disabled') || e.hasAttribute('readonly') || e.getAttribute('aria-hidden') === 'true'
      || e.getAttribute('aria-disabled') === 'true' || (tag === 'input' && e.getAttribute('type') === 'hidden')) {
        return [];
    }
    const style = getComputedStyle(e);
    if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') {
        return [];
    }
    const role = e.getAttribute('role');
    const clickableInputs = ['submit', 'checkbox', 'radio', 'color', 'file', 'image', 'reset'];
    function hasEvent(n: any) {
        let eventExistsInArray = eventDict.hasOwnProperty(xpath) && eventDict[xpath].includes(n);
        let elementHasAttribute = e.hasAttribute('on' + n);
        return eventExistsInArray || elementHasAttribute;
    }
    const evts = [];
    if (hasEvent('keydown') || hasEvent('keyup') || hasEvent('keypress') || hasEvent('keydown') || hasEvent('input') || e.isContentEditable
      || (
        (tag === 'input' || tag === 'textarea' || role === 'searchbox' || role === 'input')
        ) && !clickableInputs.includes(e.getAttribute('type')!)
      ) {
        evts.push('TYPE');
    }
    if (tag === 'a' || tag === 'button' || role === 'button' || role === 'checkbox' || hasEvent('click') || hasEvent('mousedown') || hasEvent('mouseup')
      || hasEvent('dblclick') || style.cursor === 'pointer' || (tag === 'input' && clickableInputs.includes(e.getAttribute('type')) )
      || e.hasAttribute('aria-haspopup') || tag === 'select' || role === 'select') {
        evts.push('CLICK');
    }
    return evts;
}

async function getEventListenersAll(xpath: string[]) {
    const res = await chrome.runtime.sendMessage({ action: "getEventListeners_all", xpath_list: xpath });
    return res.response
}

export async function traverse(node: any, xpath: string, results: any) {
    if (node.nodeType === Node.ELEMENT_NODE) {
        results.push(xpath); 
    }
    const countByTag: { [key: string]: number } = {};
    for (let child = node.firstChild; child; child = child.nextSibling) {
        const tag = child.nodeName.toLowerCase();
        countByTag[tag] = (countByTag[tag] || 0) + 1;
        let childXpath = xpath + '/' + tag;
        if (countByTag[tag] > 1) {
            childXpath += '[' + countByTag[tag] + ']';
        }
        if (tag === 'iframe') {
            try {
                await traverse(child.contentWindow!.document.body, childXpath + '/html/body', results);
            } catch (e) {
                console.error("iframe access blocked", child, e);
            }
        } else {
            await traverse(child, childXpath, results);
        } 
    }
    return results
}

function getElementByXpath(xpath: string) {
    return document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
  }

export async function get_possible_interactions() {
    let final_results: { [key: string]: string[] } = {};
    let xpath_list: string[] = [];
    xpath_list = await traverse(document.body, '/html/body', xpath_list);
    let results_events = await getEventListenersAll(xpath_list)
    for (const xpath of xpath_list) {
        const elem = getElementByXpath(xpath);
        const interactions = getInteractions(elem, xpath, results_events)
        if (interactions.length > 0) {
            final_results[xpath] = interactions;
        }
    }
    const ret_json = JSON.stringify(final_results); 
    return ret_json;
}