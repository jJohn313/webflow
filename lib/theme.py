"""
lib/theme.py - Sovereign Theme Loader & Curses Palette Engine for Webflow
Supports user customization via ~/.config/webflow/theme.conf or config/theme.conf.
"""
import os
import curses
import configparser
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Curses Color Pair IDs
PAIR_HEADER = 1
PAIR_TIER1 = 2
PAIR_TIER2 = 3
PAIR_TIER3 = 4
PAIR_SELECTED = 5
PAIR_BORDER = 6
PAIR_BORDER_ACTIVE = 7
PAIR_TEXT = 8
PAIR_DIM = 9
PAIR_PILL_NORMAL = 10
PAIR_PILL_SEARCH = 11


DEFAULT_THEME = {
    "palette": {
        "bg": -1,
        "fg": 223,
        "border": 240,
        "border_active": 214,
        "header_fg": 214,
        "header_bg": 236,
        "selected_fg": 235,
        "selected_bg": 214,
        "pill_normal_fg": 235,
        "pill_normal_bg": 214,
        "pill_search_fg": 235,
        "pill_search_bg": 108,
        "tier1": 108,
        "tier2": 214,
        "tier3": 175,
        "dim": 244,
        "accent": 214,
    },
    "layout": {
        "ratio_nav": 0.20,
        "ratio_mid": 0.48,
        "ratio_preview": 0.32,
        "show_relative_numbers": True,
    }
}


def load_theme_config() -> dict:
    theme = {
        "palette": dict(DEFAULT_THEME["palette"]),
        "layout": dict(DEFAULT_THEME["layout"]),
    }

    user_cfg = Path.home() / ".config" / "webflow" / "theme.conf"
    repo_cfg = REPO_ROOT / "config" / "theme.conf"

    cfg_path = user_cfg if user_cfg.exists() else (repo_cfg if repo_cfg.exists() else None)
    if not cfg_path:
        return theme

    cp = configparser.ConfigParser()
    try:
        cp.read(cfg_path, encoding="utf-8")
        if cp.has_section("palette"):
            for k in cp.options("palette"):
                try:
                    theme["palette"][k] = int(cp.get("palette", k))
                except ValueError:
                    pass
        if cp.has_section("layout"):
            if cp.has_option("layout", "ratio_nav"):
                theme["layout"]["ratio_nav"] = float(cp.get("layout", "ratio_nav"))
            if cp.has_option("layout", "ratio_mid"):
                theme["layout"]["ratio_mid"] = float(cp.get("layout", "ratio_mid"))
            if cp.has_option("layout", "ratio_preview"):
                theme["layout"]["ratio_preview"] = float(cp.get("layout", "ratio_preview"))
            if cp.has_option("layout", "show_relative_numbers"):
                theme["layout"]["show_relative_numbers"] = cp.getboolean("layout", "show_relative_numbers")
    except Exception:
        pass

    return theme


def init_curses_theme(theme: dict) -> bool:
    """Initializes color pairs according to 256-color support with safe fallbacks."""
    if not curses.has_colors():
        return False

    try:
        curses.start_color()
        curses.use_default_colors()
    except Exception:
        return False

    pal = theme["palette"]
    has_256 = curses.COLORS >= 256

    try:
        if has_256:
            curses.init_pair(PAIR_HEADER, pal["header_fg"], pal["header_bg"])
            curses.init_pair(PAIR_TIER1, pal["tier1"], pal["bg"])
            curses.init_pair(PAIR_TIER2, pal["tier2"], pal["bg"])
            curses.init_pair(PAIR_TIER3, pal["tier3"], pal["bg"])
            curses.init_pair(PAIR_SELECTED, pal["selected_fg"], pal["selected_bg"])
            curses.init_pair(PAIR_BORDER, pal["border"], pal["bg"])
            curses.init_pair(PAIR_BORDER_ACTIVE, pal["border_active"], pal["bg"])
            curses.init_pair(PAIR_TEXT, pal["fg"], pal["bg"])
            curses.init_pair(PAIR_DIM, pal["dim"], pal["bg"])
            curses.init_pair(PAIR_PILL_NORMAL, pal["pill_normal_fg"], pal["pill_normal_bg"])
            curses.init_pair(PAIR_PILL_SEARCH, pal["pill_search_fg"], pal["pill_search_bg"])
        else:
            curses.init_pair(PAIR_HEADER, curses.COLOR_BLACK, curses.COLOR_CYAN)
            curses.init_pair(PAIR_TIER1, curses.COLOR_GREEN, -1)
            curses.init_pair(PAIR_TIER2, curses.COLOR_YELLOW, -1)
            curses.init_pair(PAIR_TIER3, curses.COLOR_MAGENTA, -1)
            curses.init_pair(PAIR_SELECTED, curses.COLOR_BLACK, curses.COLOR_YELLOW)
            curses.init_pair(PAIR_BORDER, curses.COLOR_WHITE, -1)
            curses.init_pair(PAIR_BORDER_ACTIVE, curses.COLOR_YELLOW, -1)
            curses.init_pair(PAIR_TEXT, curses.COLOR_WHITE, -1)
            curses.init_pair(PAIR_DIM, curses.COLOR_WHITE, -1)
            curses.init_pair(PAIR_PILL_NORMAL, curses.COLOR_BLACK, curses.COLOR_YELLOW)
            curses.init_pair(PAIR_PILL_SEARCH, curses.COLOR_BLACK, curses.COLOR_GREEN)
        return True
    except Exception:
        return False
