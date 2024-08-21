ATTACH_MOVE_LISTENER = """
if (!window._lavague_move_listener) {
    window._lavague_move_listener = function() {
        const bbs = document.querySelectorAll('.lavague-highlight');
        bbs.forEach(bb => {
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
arguments[0].filter(a => a).forEach(a => a.style.cssText = a.dataset.originalStyle || '');
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
        label.style.padding = '0 4px';
        label.style.top = '-12px';
        label.style.left = '-12px';
        label.style['font-size'] = '13px';
        label.style['border-bottom-right-radius'] = '13px';
        label.textContent = i;
        bb.appendChild(label);
        """
    return set_style
