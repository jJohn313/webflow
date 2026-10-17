#!/usr/bin/env python3
"""
lib/shield.py - Native WebKitGTK Bytecode Content Blocker, Tracker Shield & RAM Optimizer
Compiles network block rules and cosmetic CSS rules directly into WebKit's C++ engine.
"""
import json
from pathlib import Path

import gi
gi.require_version("WebKit2", "4.1")
from gi.repository import GLib, WebKit2 as WebKit

# High-impact tracker, telemetry, and ad patterns compiled into WebKit C++ bytecode
WEBKIT_BLOCK_RULES = [
    {
        "trigger": {
            "url-filter": ".*",
            "if-domain": ["*youtube.com", "*googlevideo.com"],
            "url-filter-is-case-sensitive": False
        },
        "action": {"type": "ignore-previous-rules"}
    },
    {
        "trigger": {
            "url-filter": "(doubleclick\\.net|googlesyndication\\.com|google-analytics\\.com|googletagmanager\\.com|googletagservices\\.com|adservice\\.google\\.|pagead2\\.googlesyndication|adsystem\\.com|adnxs\\.com|rubiconproject\\.com|pubmatic\\.com|criteo\\.com|outbrain\\.com|taboola\\.com|scorecardresearch\\.com|quantserve\\.com|hotjar\\.com|mouseflow\\.com|fullstory\\.com|clarity\\.ms|mixpanel\\.com|segment\\.io|amplitude\\.com|sentry\\.io|bugsnag\\.com|newrelic\\.com|nr-data\\.net|connect\\.facebook\\.net|analytics\\.tiktok\\.com|ads-twitter\\.com)"
        },
        "action": {"type": "block"}
    },
    {
        "trigger": {
            "url-filter": "(/api/stats/ads|/api/stats/atr|/pagead/|/ptracking|/get_midroll_info|/collect\\?v=|/beacon/|/telemetry/|/pixel\\.|/analytics\\.js|/gtm\\.js|/fbevents\\.js)"
        },
        "action": {"type": "block"}
    },
    {
        "trigger": {
            "url-filter": ".*",
            "resource-type": ["popup"]
        },
        "action": {"type": "block"}
    }
]

# Cosmetic CSS to hide ad containers and intrusive cookie/consent banners before paint
COSMETIC_SHIELD_CSS = """
.ad-container, .adsbygoogle, [id^="google_ads_"], [class*="ad-slot"],
[class*="cookie-banner"], [id*="cookie-banner"], [class*="cookie-consent"],
[id*="onetrust-consent-sdk"], #onetrust-banner-sdk, .fc-consent-root,
ytd-ad-slot-renderer, ytd-in-feed-ad-layout-renderer, ytd-banner-promo-renderer,
.ytp-ad-overlay-container, .ytp-ad-message-container {
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
    pointer-events: none !important;
}
"""

# Pre-document JS to neuter beacon/ping trackers and set Do-Not-Track / GPC signals
PRIVACY_SHIELD_JS = """
(function() {
    'use strict';
    try {
        Object.defineProperty(navigator, 'globalPrivacyControl', { value: true, writable: false });
        Object.defineProperty(navigator, 'doNotTrack', { value: '1', writable: false });
        navigator.sendBeacon = function() { return true; };
        window.ga = function() {};
        window.gtag = function() {};
        window.fbq = function() {};
        window._gaq = [];
    } catch (e) {}
})();
"""


def apply_shield_and_ram_diet(web_context, data_manager, ucm, settings, base_share: Path):
    """
    Applies strict RAM limits, Intelligent Tracking Prevention (ITP),
    Cosmetic CSS/JS shields, and compiles WebKit bytecode network filters.
    """
    # 1. Process & Cache Diet (Reduces WebKitWebProcess RAM by ~35-50%)
    try:
        # DOCUMENT_VIEWER keeps 0 dead pages in memory cache
        web_context.set_cache_model(WebKit.CacheModel.DOCUMENT_VIEWER)
    except Exception:
        pass

    try:
        if hasattr(web_context, "set_process_swap_on_cross_site_navigation_enabled"):
            web_context.set_process_swap_on_cross_site_navigation_enabled(False)
    except Exception:
        pass

    # Enable Intelligent Tracking Prevention (ITP)
    try:
        if data_manager and hasattr(data_manager, "set_itp_enabled"):
            data_manager.set_itp_enabled(True)
    except Exception:
        pass

    # 2. Strip down WebKitSettings
    if hasattr(settings, "set_enable_page_cache"):
        settings.set_enable_page_cache(False)
    if hasattr(settings, "set_enable_offline_web_application_cache"):
        settings.set_enable_offline_web_application_cache(False)
    if hasattr(settings, "set_enable_hyperlink_auditing"):
        settings.set_enable_hyperlink_auditing(False)
    if hasattr(settings, "set_enable_media_stream"):
        settings.set_enable_media_stream(False)
    if hasattr(settings, "set_enable_mediasource"):
        settings.set_enable_mediasource(False)  # Prevents MSE YouTube crashes; video goes to mpv/youtube-tui
    if hasattr(settings, "set_enable_webgl"):
        settings.set_enable_webgl(False)        # Huge GPU/RAM savings; toggleable if needed
    if hasattr(settings, "set_enable_webaudio"):
        settings.set_enable_webaudio(False)
    if hasattr(settings, "set_enable_dns_prefetching"):
        settings.set_enable_dns_prefetching(False)
    if hasattr(settings, "set_enable_back_forward_navigation_gestures"):
        settings.set_enable_back_forward_navigation_gestures(False)

    # 3. Inject Cosmetic CSS & Pre-Load Privacy JS
    try:
        style_sheet = WebKit.UserStyleSheet.new(
            COSMETIC_SHIELD_CSS,
            WebKit.UserContentInjectedFrames.ALL_FRAMES,
            WebKit.UserStyleLevel.USER,
            None,
            None
        )
        ucm.add_style_sheet(style_sheet)
    except Exception:
        pass

    try:
        privacy_script = WebKit.UserScript.new(
            PRIVACY_SHIELD_JS,
            WebKit.UserContentInjectedFrames.ALL_FRAMES,
            WebKit.UserScriptInjectionTime.START,
            None,
            None
        )
        ucm.add_script(privacy_script)
    except Exception:
        pass

    # 4. Compile & Attach Native C++ Bytecode Network Blocker
    try:
        filter_dir = base_share / "filters"
        filter_dir.mkdir(parents=True, exist_ok=True)
        store = WebKit.UserContentFilterStore.new(str(filter_dir))
        rules_bytes = GLib.Bytes.new(json.dumps(WEBKIT_BLOCK_RULES).encode("utf-8"))

        def _on_filter_saved(store_obj, res, *user_data):
            try:
                uf = store_obj.save_finish(res)
                if uf:
                    ucm.add_filter(uf)
            except Exception:
                pass

        store.save("webflow-shield-v1", rules_bytes, None, _on_filter_saved)
    except Exception:
        pass
