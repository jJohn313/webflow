(function() {
    'use strict';

    if (window.__wf_hints_active) {
        if (typeof window.__wf_cleanup_hints === 'function') {
            window.__wf_cleanup_hints();
        }
        return;
    }

    const HINT_CHARS = 'abcdefghijklmnopqrstuvwxyz';
    let currentInput = '';
    const overlays = [];
    const container = document.createElement('div');
    container.id = '__wf_hints_container';
    container.style.position = 'fixed';
    container.style.top = '0';
    container.style.left = '0';
    container.style.width = '100vw';
    container.style.height = '100vh';
    container.style.zIndex = '2147483647';
    container.style.pointerEvents = 'none';
    container.style.margin = '0';
    container.style.padding = '0';

    function isVisible(el) {
        const style = window.getComputedStyle(el);
        if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') {
            return false;
        }
        const rect = el.getBoundingClientRect();
        if (rect.width <= 0 || rect.height <= 0) {
            return false;
        }
        return (
            rect.top < window.innerHeight &&
            rect.bottom > 0 &&
            rect.left < window.innerWidth &&
            rect.right > 0
        );
    }

    function getInteractiveElements() {
        const selector = [
            'a[href]',
            'button',
            'input:not([type="hidden"])',
            'select',
            'textarea',
            '[role="button"]',
            '[role="link"]',
            '[role="checkbox"]',
            '[role="menuitem"]',
            '[onclick]',
            '[tabindex]:not([tabindex="-1"])'
        ].join(',');

        const elements = Array.from(document.querySelectorAll(selector));
        return elements.filter(isVisible);
    }

    function generateHints(count) {
        const hints = [];
        const base = HINT_CHARS.length;
        for (let i = 0; i < count; i++) {
            const first = HINT_CHARS[Math.floor(i / base) % base];
            const second = HINT_CHARS[i % base];
            hints.push((first + second).toUpperCase());
        }
        return hints;
    }

    function notifyHost(action, payload = {}) {
        if (window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.webflow) {
            window.webkit.messageHandlers.webflow.postMessage(JSON.stringify({ action, ...payload }));
        }
    }

    const elements = getInteractiveElements();
    if (elements.length === 0) {
        notifyHost('hints_dismissed');
        return;
    }

    const hints = generateHints(elements.length);
    window.__wf_hints_active = true;

    elements.forEach((el, index) => {
        const rect = el.getBoundingClientRect();
        const hintText = hints[index];

        const badge = document.createElement('span');
        badge.className = '__wf_hint_badge';
        badge.textContent = hintText;
        badge.dataset.hint = hintText;
        badge.style.position = 'fixed';
        badge.style.top = `${Math.max(0, rect.top)}px`;
        badge.style.left = `${Math.max(0, rect.left)}px`;
        badge.style.background = '#ffd700';
        badge.style.color = '#000000';
        badge.style.fontFamily = 'monospace, monospace';
        badge.style.fontWeight = 'bold';
        badge.style.fontSize = '12px';
        badge.style.lineHeight = '14px';
        badge.style.padding = '1px 4px';
        badge.style.border = '1px solid #111111';
        badge.style.borderRadius = '3px';
        badge.style.boxShadow = '0 2px 4px rgba(0,0,0,0.4)';
        badge.style.zIndex = '2147483647';
        badge.style.pointerEvents = 'none';

        container.appendChild(badge);
        overlays.push({ badge, el, hint: hintText });
    });

    document.documentElement.appendChild(container);

    function cleanup() {
        if (container.parentNode) {
            container.parentNode.removeChild(container);
        }
        window.removeEventListener('keydown', onKeyDown, true);
        window.__wf_hints_active = false;
        notifyHost('hints_dismissed');
    }
    window.__wf_cleanup_hints = cleanup;

    function activateElement(el) {
        cleanup();
        const tagName = el.tagName.toLowerCase();
        const isEditable = el.isContentEditable ||
                           tagName === 'textarea' ||
                           (tagName === 'input' && !['checkbox', 'radio', 'button', 'submit', 'reset'].includes(el.type));

        if (isEditable) {
            el.focus();
            if (typeof el.select === 'function') {
                el.select();
            }
            notifyHost('set_mode', { mode: 'INSERT' });
        } else {
            el.focus();
            el.click();
        }
    }

    function onKeyDown(e) {
        if (e.key === 'Escape') {
            e.preventDefault();
            e.stopPropagation();
            cleanup();
            return;
        }

        if (e.key === 'Backspace') {
            e.preventDefault();
            e.stopPropagation();
            currentInput = currentInput.slice(0, -1);
            filterBadges();
            return;
        }

        const char = e.key.toUpperCase();
        if (HINT_CHARS.toUpperCase().includes(char)) {
            e.preventDefault();
            e.stopPropagation();
            currentInput += char;

            const exactMatch = overlays.find(o => o.hint === currentInput);
            if (exactMatch) {
                activateElement(exactMatch.el);
                return;
            }

            const prefixMatches = overlays.filter(o => o.hint.startsWith(currentInput));
            if (prefixMatches.length === 0) {
                cleanup();
            } else {
                filterBadges();
            }
        } else {
            // Unrelated key cancels hints
            cleanup();
        }
    }

    function filterBadges() {
        overlays.forEach(o => {
            if (o.hint.startsWith(currentInput)) {
                o.badge.style.display = 'inline-block';
                if (currentInput.length > 0) {
                    o.badge.style.background = '#ff9800';
                } else {
                    o.badge.style.background = '#ffd700';
                }
            } else {
                o.badge.style.display = 'none';
            }
        });
    }

    window.addEventListener('keydown', onKeyDown, true);
})();
