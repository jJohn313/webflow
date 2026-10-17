# 🌐 Webflow (`webflow`)

> **A Non-Chromium, Modular, Terminal-First Web Architecture for Linux (Wayland / Kitty)**  
> *Under the umbrella of [Terminal Everything Linux (TEL)](https://github.com/jJohn313/terminal-everything-linux).*

[![Status: Early WIP](https://img.shields.io/badge/Status-Early%20WIP%20(Pre--Alpha)-orange.svg)]()
[![Platform: Linux / Wayland](https://img.shields.io/badge/Platform-Arch%20Linux%20%7C%20Wayland-blue.svg)]()
[![Engine: WebKitGTK](https://img.shields.io/badge/Engine-WebKitGTK%204.1%2F6.0-green.svg)]()

> [!WARNING]
> **Project Status: Early Work-in-Progress (Pre-Alpha)**  
> Webflow is currently an early architectural prototype. The foundation, single-process WebKitGTK Wayland canvas, modal event handler, DOM link hints, and terminal extractor are implemented as a working baseline, but active development, dogfooding, and refinement are ongoing.

---

## ⚡ Architecture Overview

Modern web browsers have devolved into multi-gigabyte monolithic operating systems bundled with telemetry, ad engines, and heavy Chromium/Blink runtimes.

**Webflow** completely eliminates Chromium, Blink, Electron, and QtWebEngine. It decouples **State** (bookmarks, history, credentials, session cookies) from **Rendering**:

1. **Tier 1 (Terminal Reader - `wf-reader`)**: Extracts raw semantic content into clean Markdown streams viewed directly in Kitty/Neovim or `glow`. Fast, zero-engine, zero-ad readability.
2. **Tier 3 (In-House WebKitGTK Viewer - `wf-view`)**: A chromeless, high-performance Wayland GUI browser written in Python using native system `WebKitGTK` and `GTK 3/4`. Features complete Vim-modal navigation (`NORMAL`, `INSERT`), strict per-domain session isolation, hard process lifecycle termination, and a custom JavaScript link-hinting engine (`f`).
3. **Dispatcher (`wf-open`)**: High-speed heuristic probe & rule router serving as the system's `xdg-open` handler.
4. **Decoupled State (`wf-bookmarks` & `wf-pass`)**: Externalized bookmarks/history fuzzy selector (`fzf`) and compositor-level credential synthesizer (`pass`/`rbw` + `wtype`).

```
                              [ Incoming URL ]
                                     │
                                     ▼
                              ┌─────────────┐
                              │   wf-open   │ (xdg-open dispatcher)
                              └──────┬──────┘
                                     │
                 ┌───────────────────┴───────────────────┐
                 ▼ (Semantic / Article)                  ▼ (App / SPA / Dynamic)
          ┌─────────────┐                         ┌─────────────┐
          │  wf-reader  │                         │   wf-view   │
          │ (Terminal)  │                         │ (WebKitGTK) │
          └──────┬──────┘                         └──────┬──────┘
                 │ [E] Escalate                          │
                 └───────────────────────────────────────┘
```

---

## 📁 Repository Structure

```text
webflow/
├── bin/
│   ├── wf-open          # Entry dispatcher & heuristic classifier (Python 3)
│   ├── wf-reader        # Tier 1: Terminal Markdown extractor & Kitty/glow runner
│   ├── wf-view          # Tier 3: Custom in-house WebKitGTK modal browser (PyGObject)
│   ├── wf-bookmarks     # Fast plaintext bookmark/history picker (fzf)
│   └── wf-pass          # Active-window credential injector (rbw/pass + wtype)
├── assets/
│   └── hints.js         # Injected JavaScript for zero-latency DOM link hinting
├── config/
│   └── rules.conf       # Domain routing overrides (TIER1_ONLY, TIER3_ONLY)
└── README.md
```

---

## ⌨️ `wf-view` Modal Keyboard Controller

`wf-view` operates as a true Vim-modal Wayland window without any URL bar, buttons, or decorative chrome:

### Normal Mode (Default)
| Key | Action |
| :--- | :--- |
| `j` / `k` | Smooth scroll down / up (100px) |
| `d` / `u` | Half-page scroll down / up |
| `gg` | Scroll to very top of page |
| `G` | Scroll to bottom of document |
| `H` | Navigate backward in history (`history.back()`) |
| `L` | Navigate forward in history (`history.forward()`) |
| `r` | Reload current page |
| `f` | Trigger DOM link hinting engine (`AA`, `AB`, ...) |
| `i` | Enter `INSERT` mode manually |
| `b` | Bookmark current URL and page title to `~/.local/share/webflow/bookmarks.txt` |
| `y` | Copy current URL to Wayland clipboard (`wl-copy`) |
| `q` | Immediately terminate process and release WebKit rendering threads |

### Insert Mode
- Triggered automatically when clicking or focusing an `<input>`, `<textarea>`, or content-editable container, or by typing `i`.
- All keystrokes pass directly to the web page.
- Press **`Escape`** to blur the active input, restore keyboard sovereignty, and return to **`NORMAL`** mode.

### Link Hinting Mode (`f`)
- Press `f` to overlay two-letter badges over all visible interactive elements (`<a>`, `<button>`, inputs).
- Type the 2-letter hint to automatically trigger the click or focus the field.
- Press `Escape` or `Backspace` to dismiss hints.

---

## 📖 `wf-reader` Keybindings

When reading articles in the terminal:
- **`E`**: Escalate immediately to the GUI viewer (`wf-view <URL>`).
- **`b`**: Bookmark page to `bookmarks.txt`.
- **`1..N`**: Jump directly to referenced hyperlink number via `wf-open`.
- **`q`**: Quit reader.

---

## 🔧 Compositor Integration (Hyprland Snippet)

Add the following keybindings to your `~/.config/hypr/hyprland.conf`:

```ini
# Webflow: Open bookmark & history picker
bind = $mainMod, B, exec, kitty --class clip-term -e wf-bookmarks

# Webflow: Inject credentials into active wf-view window
bind = $mainMod SHIFT, P, exec, wf-pass

# Window rule: Chromeless floating or tiled WebKitGTK windows
windowrulev2 = noblur, class:^(wf-view|python3)$
windowrulev2 = bordersize 2, class:^(wf-view|python3)$
```

---

## 🚀 Installation & Setup

### Dependencies (Arch Linux)
```bash
sudo pacman -S webkit2gtk-4.1 python-gobject glow fzf wtype wl-clipboard kitty
```

### Symlink Binaries
Symlink the tools into `~/.local/bin` (or use TEL's `install.sh`):
```bash
ln -sfn $(pwd)/bin/wf-open ~/.local/bin/wf-open
ln -sfn $(pwd)/bin/wf-view ~/.local/bin/wf-view
ln -sfn $(pwd)/bin/wf-reader ~/.local/bin/wf-reader
ln -sfn $(pwd)/bin/wf-bookmarks ~/.local/bin/wf-bookmarks
ln -sfn $(pwd)/bin/wf-pass ~/.local/bin/wf-pass
```

### Set as Default Browser
```bash
xdg-settings set default-web-browser wf-open.desktop
```

---

## 🛡️ License & Acknowledgments
Part of the **Terminal Everything Linux** initiative. MIT License.
