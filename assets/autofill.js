(function() {
    'use strict';

    if (window.__wf_autofill_installed) return;
    window.__wf_autofill_installed = true;

    function isVisible(el) {
        if (!el) return false;
        const style = window.getComputedStyle(el);
        if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') {
            return false;
        }
        const rect = el.getBoundingClientRect();
        return rect.width > 0 && rect.height > 0;
    }

    function findPasswordField() {
        const pwInputs = Array.from(document.querySelectorAll('input[type="password"]')).filter(isVisible);
        return pwInputs.length > 0 ? pwInputs[0] : null;
    }

    function findUsernameField(pwInput) {
        // 1. Explicit autocomplete
        const explicitUser = document.querySelector('input[autocomplete="username" i], input[autocomplete="email" i]');
        if (explicitUser && isVisible(explicitUser)) return explicitUser;

        // 2. Scan within same form or document
        const scope = (pwInput && pwInput.closest('form')) || document;
        const candidates = Array.from(scope.querySelectorAll('input:not([type="hidden"]):not([type="password"]):not([type="submit"]):not([type="button"]):not([type="checkbox"]):not([type="radio"])')).filter(isVisible);

        for (const el of candidates) {
            const name = (el.getAttribute('name') || '').toLowerCase();
            const id = (el.getAttribute('id') || '').toLowerCase();
            const type = (el.getAttribute('type') || '').toLowerCase();
            if (type === 'email' || name.includes('user') || name.includes('login') || name.includes('email') ||
                id.includes('user') || id.includes('login') || id.includes('email')) {
                return el;
            }
        }

        // If a password input is present, the candidate text input directly before it is almost always the username/email
        if (pwInput && candidates.length > 0) {
            return candidates[candidates.length - 1];
        }

        return null;
    }

    function setInputValue(el, value) {
        if (!el || value === undefined || value === null) return;
        el.focus();
        try {
            const proto = Object.getPrototypeOf(el);
            const desc = Object.getOwnPropertyDescriptor(proto, 'value') || Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value');
            if (desc && desc.set) {
                desc.set.call(el, value);
            } else {
                el.value = value;
            }
        } catch (e) {
            el.value = value;
        }
        el.dispatchEvent(new Event('input', { bubbles: true, composed: true }));
        el.dispatchEvent(new Event('change', { bubbles: true, composed: true }));

        // Visual indicator of autofill
        const prevOutline = el.style.outline;
        el.style.outline = '2px solid #00ffc8';
        setTimeout(() => {
            el.style.outline = prevOutline;
        }, 1200);
    }

    window.__wf_autofill = function(username, password) {
        const pw = findPasswordField();
        const user = findUsernameField(pw);

        let filled = false;
        if (user && username) {
            setInputValue(user, username);
            filled = true;
        }
        if (pw && password) {
            setInputValue(pw, password);
            filled = true;
        }
        return filled;
    };

    window.__wf_capture_credentials = function() {
        const pw = findPasswordField();
        const user = findUsernameField(pw);
        const passVal = pw ? pw.value : '';
        const userVal = user ? user.value.trim() : '';
        if (passVal) {
            if (window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.webflow) {
                window.webkit.messageHandlers.webflow.postMessage(JSON.stringify({
                    action: 'credentials_detected',
                    domain: window.location.hostname,
                    username: userVal,
                    password: passVal
                }));
            }
            return true;
        }
        return false;
    };

    let hasRequestedAutofill = false;
    function checkAndRequestAutofill() {
        if (hasRequestedAutofill) return;
        const pw = findPasswordField();
        const user = findUsernameField(pw);
        if (pw || user) {
            hasRequestedAutofill = true;
            if (window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.webflow) {
                window.webkit.messageHandlers.webflow.postMessage(JSON.stringify({
                    action: 'request_autofill',
                    domain: window.location.hostname
                }));
            }
        }
    }

    // Attach listeners for login submission
    function attachLoginWatchers() {
        document.addEventListener('submit', function(e) {
            window.__wf_capture_credentials();
        }, true);

        document.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                const target = e.target;
                if (target && target.type === 'password') {
                    setTimeout(window.__wf_capture_credentials, 50);
                }
            }
        }, true);

        document.addEventListener('click', function(e) {
            const btn = e.target.closest('button, input[type="submit"]');
            if (btn) {
                const form = btn.closest('form');
                if (form && form.querySelector('input[type="password"]')) {
                    setTimeout(window.__wf_capture_credentials, 50);
                }
            }
        }, true);
    }

    if (document.readyState === 'complete' || document.readyState === 'interactive') {
        checkAndRequestAutofill();
        attachLoginWatchers();
    } else {
        document.addEventListener('DOMContentLoaded', () => {
            checkAndRequestAutofill();
            attachLoginWatchers();
        });
    }

    // SPA observer for delayed login forms
    let observerTimer = null;
    const observer = new MutationObserver(() => {
        if (!hasRequestedAutofill) {
            if (observerTimer) clearTimeout(observerTimer);
            observerTimer = setTimeout(checkAndRequestAutofill, 350);
        }
    });
    observer.observe(document.documentElement || document.body, { childList: true, subtree: true });
})();
