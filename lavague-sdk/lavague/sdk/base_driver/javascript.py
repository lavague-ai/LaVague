def js_wrap_function_call(fn: str):
    return "(function(){" + fn + "})()"


JS_SETUP_GET_EVENTS = """
(function() {
  if (window && !window.getEventListeners) {
    const targetProto = EventTarget.prototype;
    targetProto._addEventListener = Element.prototype.addEventListener;
    targetProto.addEventListener = function(a,b,c) {
        this._addEventListener(a,b,c);
        if(!this.eventListenerList) this.eventListenerList = {};
        if(!this.eventListenerList[a]) this.eventListenerList[a] = [];
        this.eventListenerList[a].push(b);
    };
    targetProto._removeEventListener = Element.prototype.removeEventListener;
    targetProto.removeEventListener = function(a, b, c) {
        this._removeEventListener(a, b, c);
        if(this.eventListenerList && this.eventListenerList[a]) {
            const index = this.eventListenerList[a].indexOf(b);
            if (index > -1) {
                this.eventListenerList[a].splice(index, 1);
                if (!this.eventListenerList[a].length) {
                    delete this.eventListenerList[a];
                }
            }
        }
    };
    window.getEventListeners = function(e) {
      return (e && e.eventListenerList) || [];
    }
  }
})();"""

JS_GET_INTERACTIVES = """
const windowHeight = (window.innerHeight || document.documentElement.clientHeight);
const windowWidth = (window.innerWidth || document.documentElement.clientWidth);

return (function(inViewport, foregroundOnly, nonInteractives, filterTypes) {
    function getInteractions(e) {
        const tag = e.tagName.toLowerCase();
        if (!e.checkVisibility() || (e.hasAttribute('disabled') && !nonInteractives) || e.hasAttribute('readonly')
          || (tag === 'input' && e.getAttribute('type') === 'hidden') || tag === 'body') {
            return [];
        }
        const rect = e.getBoundingClientRect();
        if (rect.width + rect.height < 5) {
            return [];
        }
        const style = getComputedStyle(e) || {};
        if (style.display === 'none' || style.visibility === 'hidden') {
            return [];
        }
        const events = window && typeof window.getEventListeners === 'function' ? window.getEventListeners(e) : [];
        const role = e.getAttribute('role');
        const clickableInputs = ['submit', 'checkbox', 'radio', 'color', 'file', 'image', 'reset'];
        function hasEvent(n) {
            return events[n]?.length || e.hasAttribute('on' + n);
        }
        let evts = [];
        if (hasEvent('keydown') || hasEvent('keyup') || hasEvent('keypress') || hasEvent('keydown') || hasEvent('input') || e.isContentEditable
          || (
            (tag === 'input' || tag === 'textarea' || role === 'searchbox' || role === 'input')
            ) && !clickableInputs.includes(e.getAttribute('type'))
          ) {
            evts.push('TYPE');
        }
        if (['a', 'button', 'select'].includes(tag) || ['button', 'checkbox', 'select'].includes(role)
            || hasEvent('click') || hasEvent('mousedown') || hasEvent('mouseup') || hasEvent('dblclick')
            || style.cursor === 'pointer'
            || e.hasAttribute('aria-haspopup')
            || (tag === 'input' && clickableInputs.includes(e.getAttribute('type')))
            || (tag === 'label' && document.getElementById(e.getAttribute('for')))
        ) {
            evts.push('CLICK');
        }
        if (
            (hasEvent('scroll') || hasEvent('wheel') || style.overflow === 'auto' || style.overflow === 'scroll' || style.overflowY === 'auto' || style.overflowY === 'scroll')
            && (e.scrollHeight > e.clientHeight || e.scrollWidth > e.clientWidth)) {
            evts.push('SCROLL');
        }
        if (filterTypes && filterTypes.length) {
            evts = evts.filter(t => filterTypes.includes(t));
        }
        if (nonInteractives && evts.length === 0) {
            evts.push('NONE');
        }

        if (inViewport) {
            let rect = e.getBoundingClientRect();
            let iframe = e.ownerDocument.defaultView.frameElement;
            while (iframe) {
                const iframeRect = iframe.getBoundingClientRect();
                rect = {
                    top: rect.top + iframeRect.top,
                    left: rect.left + iframeRect.left,
                    bottom: rect.bottom + iframeRect.bottom,
                    right: rect.right + iframeRect.right,
                    width: rect.width,
                    height: rect.height
                }
                iframe = iframe.ownerDocument.defaultView.frameElement;
            }
            const elemCenter = {
                x: Math.round(rect.left + rect.width / 2),
                y: Math.round(rect.top + rect.height / 2)
            };
            if (elemCenter.x < 0) return [];
            if (elemCenter.x > windowWidth) return [];
            if (elemCenter.y < 0) return [];
            if (elemCenter.y > windowHeight) return [];
            if (!foregroundOnly) return evts; // whenever to check for elements above
            let pointContainer = document.elementFromPoint(elemCenter.x, elemCenter.y);
            iframe = e.ownerDocument.defaultView.frameElement;
            while (iframe) {
                const iframeRect = iframe.getBoundingClientRect();
                pointContainer = iframe.contentDocument.elementFromPoint(
                    elemCenter.x - iframeRect.left,
                    elemCenter.y - iframeRect.top
                );
                iframe = iframe.ownerDocument.defaultView.frameElement;
            }
            do {
                if (pointContainer === e) return evts;
                if (pointContainer == null) return evts;
            } while (pointContainer = pointContainer.parentNode);
            return [];
        }
        return evts;
    }

    const results = {};
    function traverse(node, xpath) {
        if (node.nodeType === Node.ELEMENT_NODE) {
            const interactions = getInteractions(node);
            if (interactions.length > 0) {
                results[xpath] = interactions;
            }
        }
        const countByTag = {};
        for (let child = node.firstChild; child; child = child.nextSibling) {
            let tag = child.nodeName.toLowerCase();
            if (tag.includes(":")) continue; //namespace
            let isLocal = ['svg'].includes(tag);
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
                    traverse(child.contentWindow.document.body, childXpath + '/html/body');
                } catch (e) {
                    console.warn("iframe access blocked", child, e);
                }
            } else if (!isLocal) {
                traverse(child, childXpath);
                if (child.shadowRoot) {
                    traverse(child.shadowRoot, childXpath + '/');
                }
            } 
        }
    }
    traverse(document.body, '/html/body');
    return results;
})(arguments?.[0], arguments?.[1], arguments?.[2], arguments?.[3]);
"""

JS_WAIT_DOM_IDLE = """
return new Promise(resolve => {
    const timeout = arguments[0] || 10000;
    const stabilityThreshold = arguments[1] || 100;

    let mutationObserver;
    let timeoutId = null;

    const waitForIdle = () => {
        if (timeoutId) clearTimeout(timeoutId);
        timeoutId = setTimeout(() => resolve(true), stabilityThreshold);
    };
    mutationObserver = new MutationObserver(waitForIdle);
    mutationObserver.observe(document.body, {
        childList: true,
        attributes: true,
        subtree: true,
    });
    waitForIdle();

    setTimeout(() => {
        resolve(false);
        mutationObserver.disconnect();
        mutationObserver = null;
        if (timeoutId) {
            clearTimeout(timeoutId);
            timeoutId = null;
        }
    }, timeout);
});
"""

JS_GET_SCROLLABLE_PARENT = """
let element = arguments[0];
while (element) {
    const style = window.getComputedStyle(element);

    // Check if the element is scrollable
    if (style.overflow === 'auto' || style.overflow === 'scroll' || 
        style.overflowX === 'auto' || style.overflowX === 'scroll' || 
        style.overflowY === 'auto' || style.overflowY === 'scroll') {
        
        // Check if the element has a scrollable area
        if (element.scrollHeight > element.clientHeight || 
            element.scrollWidth > element.clientWidth) {
            return element;
        }
    }
    element = element.parentElement;
}
return null;
"""

JS_GET_SHADOW_ROOTS = """
const results = {};
function traverse(node, xpath) {
    if (node.shadowRoot) {
        results[xpath] = node.shadowRoot.innerHTML;
    }
    const countByTag = {};
    for (let child = node.firstChild; child; child = child.nextSibling) {
        let tag = child.nodeName.toLowerCase();
        countByTag[tag] = (countByTag[tag] || 0) + 1;
        let childXpath = xpath + '/' + tag;
        if (countByTag[tag] > 1) {
            childXpath += '[' + countByTag[tag] + ']';
        }
        if (child.shadowRoot) {
            traverse(child.shadowRoot, childXpath + '/');
        }
        if (tag === 'iframe') {
            try {
                traverse(child.contentWindow.document.body, childXpath + '/html/body');
            } catch (e) {
                console.warn("iframe access blocked", child, e);
            }
        } else {
            traverse(child, childXpath);
        }
    }
}
traverse(document.body, '/html/body');
return results;
"""

ATTACH_MOVE_LISTENER = """
if (!window._lavague_move_listener) {
    window._lavague_move_listener = function() {
        document.querySelectorAll('.lavague-highlight').forEach(bb => {
            const rect = bb._tracking.getBoundingClientRect();
            bb.style.top = rect.top + 'px';
            bb.style.left = rect.left + 'px';
            bb.style.width = rect.width + 'px';
            bb.style.height = rect.height + 'px';
        });
    };
    window.addEventListener('scroll', window._lavague_move_listener);
    window.addEventListener('resize', window._lavague_move_listener);
}
"""

REMOVE_HIGHLIGHT = """
if (window._lavague_move_listener) {
    window.removeEventListener('scroll', window._lavague_move_listener);
    window.removeEventListener('resize', window._lavague_move_listener);
    delete window._lavague_move_listener;
}
document.querySelectorAll('.lavague-highlight').forEach(a => a.remove());
"""


def get_highlighter_style(color: str = "red", label: bool = False):
    set_style = f"""
    const r = a.getBoundingClientRect();
    const bb = document.createElement('div');
    const s = window.getComputedStyle(a);
    bb.className = 'lavague-highlight';
    bb.style.position = 'fixed';
    bb.style.top = r.top + 'px';
    bb.style.left = r.left + 'px';
    bb.style.width = r.width + 'px';
    bb.style.height = r.height + 'px';
    bb.style.border = '3px solid {color}';
    bb.style.borderRadius = s.borderRadius;
    bb.style['z-index'] = '2147483647';
    bb.style['pointer-events'] = 'none';
    bb._tracking = a;
    document.body.appendChild(bb);
    """

    if label:
        set_style += """
        const label = document.createElement('div');
        label.style.position = 'absolute';
        label.style.backgroundColor = 'red';
        label.style.color = 'white';
        label.style.padding = '0px 6px 2px 4px';
        label.style.top = '-12px';
        label.style.left = '-12px';
        label.style['font-size'] = '13pt';
        label.style['font-weight'] = 'bold';
        label.style['border-bottom-right-radius'] = '13px';
        label.textContent = i + 1;
        bb.appendChild(label);
        """
    return set_style
