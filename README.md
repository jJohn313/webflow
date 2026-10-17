# 🌐 Webflow (`webflow`)

> **A Non-Chromium, Modular, Terminal-First Web Architecture for Linux (Wayland / Kitty)**  
> *Under the umbrella of [Terminal Everything Linux (TEL)](https://github.com/jJohn313/terminal-everything-linux).*

[![Status: Early Build](https://img.shields.io/badge/Status-Early%20Build%20(v0.3)-green.svg)]()
[![Platform: Linux / Wayland](https://img.shields.io/badge/Platform-Arch%20Linux%20%7C%20Wayland-blue.svg)]()
[![Engine: WebKitGTK / MPV](https://img.shields.io/badge/Engine-WebKitGTK%204.1%20%7C%20MPV-yellowgreen.svg)]()

> [!NOTE]
> **Project Status: Early Build (v0.3)**  
> Webflow is a functioning, daily-driver ready non-Chromium web architecture. It decouples state, credentials, and content extraction from heavy rendering engines. Everything runs smoothly across three dedicated tiers: a terminal Markdown reader, hardware-accelerated media streaming, and a modal WebKitGTK browser with sovereign credential autofill and native ad/tracker shielding.

---

## ⚡ Architecture Overview

Modern web browsers have devolved into multi-gigabyte monolithic operating systems bundled with telemetry, ad engines, and heavy Chromium/Blink runtimes.

**Webflow** completely eliminates Chromium, Blink, Electron, and QtWebEngine. It decouples **State** (bookmarks, history, credentials, session cookies) from **Rendering**:

```
                              [ Incoming URL ]
                                     │
                                     ▼
                              ┌─────────────┐
                              │   wf-open   │ (xdg-open dispatcher & tier classifier)
                              └──────┬──────┘
                                     │
         ┌───────────────────────────┼───────────────────────────┐
         ▼ (Articles / Docs)         ▼ (Video / Streams)         ▼ (SPAs / Auth / Dynamic)
  ┌─────────────┐             ┌─────────────┐             ┌─────────────┐
  │   Tier 1    │             │   Tier 2    │             │   Tier 3    │
  │  wf-reader  │             │  wf-media   │             │   wf-view   │
  │ (Terminal)  │             │    (MPV)    │             │ (WebKitGTK) │
  └──────┬──────┘             └─────────────┘             └──────┬──────┘
         │ [E] Escalate                                          │ [E] Return
         └───────────────────────────────────────────────────────┘
                        (Preserves Exact Scroll State)
```

1. **Tier 0: Sovereign Dispatcher & Probe (`wf-open`, `wf-tier`)**: High-speed heuristic probe & rule router serving as the system's `xdg-open` handler.
2. **Tier 1: Terminal Reader (`wf-reader`)**: Extracts clean semantic Markdown streams via `trafilatura` and renders directly in a responsive curses TUI. Features numeric link jumping (`1..N`), local saving (`s`), bookmarking (`b`), and bidirectional escalation (`e`/`E`) to GUI while preserving exact terminal scroll position.
3. **Tier 2: Sovereign Media Streamer (`wf-media`)**: Low-latency video playback for YouTube, Twitch, Vimeo, and Odysee. Strips tracking query parameters (`clean_video_url`), configures Wayland-native NVDEC/VA-API hardware acceleration, and buffers in <0.1s via `mpv` with zero browser RAM, or drops into `youtube-tui` / `ytfzf`.
4. **Tier 3: In-House WebKitGTK Viewer (`wf-view`)**: Chromeless, modal Wayland browser written in Python using system `WebKitGTK 4.1`. Features Vim navigation (`NORMAL`, `INSERT`, `SEARCH`, `HINTS`), native C++ ad/tracker shield (`lib/shield.py`), per-domain isolated session storage (`~/.local/share/webflow/sessions/<domain>`), reactive DOM link hints (`hints.js`), and sovereign credential autofill (`p`).
5. **Decoupled State & Memory**:
   - **Workbenches (`wf-workbench`)**: Persistent project tab groups (`~/.local/share/webflow/workbenches/<name>.json`) sharing domain cookies and auto-updating open tab URLs upon exit.
   - **Sovereign Vault (`wf-pass`, `lib/vault.py`)**: Local AES-GCM encrypted credential vault with DOM autofill and CLI management.
   - **Bookmarks & History (`wf-bookmarks`)**: Plaintext deliberate bookmark ledger and deduplicated chronological visit stream.

---

## 📁 Repository Structure

```text
webflow/
├── bin/
│   ├── webflow          # Flagship Yazi-style 3-pane TUI dashboard & ephemeral search
│   ├── wf-open          # Entry dispatcher & heuristic classifier (Python 3)
│   ├── wf-tier          # Fast routing predictor (prints TIER1, TIER2, or TIER3)
│   ├── wf-reader        # Tier 1: Terminal Markdown extractor & interactive curses reader
│   ├── wf-media         # Tier 2: Low-latency Wayland MPV streamer & YouTube interceptor
│   ├── wf-view          # Tier 3: In-house WebKitGTK modal browser with Vim bindings
│   ├── wf-workbench     # Persistent project workspace manager (JSON manifests)
│   ├── wf-pass          # Sovereign AES-GCM credential vault & auto-login injector
│   └── wf-bookmarks     # Fast plaintext bookmark/history picker (fzf)
├── lib/
│   ├── shield.py        # Native C++ WebKit content filter adblocker & RAM optimizer
│   ├── vault.py         # Sovereign encrypted credential store & domain matching
│   └── theme.py         # Theme loader & curses 256-color palette engine
├── assets/
│   ├── hints.js         # Injected JavaScript for zero-latency DOM link hinting
│   └── autofill.js      # Reactive DOM input handler for sovereign credential injection
├── config/
│   ├── rules.conf       # Domain routing overrides ([TIER1_ONLY], [TIER2_ONLY], [TIER3_ONLY])
│   └── theme.conf       # Yazi warm sand palette & 3-pane layout configuration
└── README.md
```

---

## 🖥️ The Yazi-Aesthetic Terminal Dashboard (`webflow`)

Launch the unified 3-column TUI directly in your terminal:
```bash
webflow
```

* **Unified 3-Pane Outer Grid**: Clean single-frame layout (`╭───┬───┬───╮` ... `╰───┴───┴───╯`) with embedded section headers and active column indicators.
* **Warm Sand / Gold Palette**: Styled with dark charcoal text on a warm gold highlight bar, matching the modern Yazi aesthetic. Fully customizable via `config/theme.conf` or `~/.config/webflow/theme.conf`.
* **Relative Line Numbers**: Displays relative distance numbers (`1`, `2`, `3`...) in the active middle list for instant Vim jumping (`5j`, `3k`).
* **Bottom Pill Statusline**: Real-time modal pills (`[ NORMAL ]` / `[ SEARCH ]`), active query status, and item counters (`[1/N] [LIST:SEARCH]`).

### Column Breakdown
* **Column 1 (Sections)**:
  * `⚡ Ephemeral Search`: Zero-engine live search (DuckDuckGo Lite / Wikipedia / Direct URL).
  * `🗂 Workbenches`: Saved project workspaces (`Research`, `Homelab`, `Documentation`).
  * `➕ New Workbench`: Initialize a dedicated project space.
  * `📅 History (Grouped)`: Deduplicated chronological stream with visit counters and tier badges.
  * `🔖 Bookmarks (Deliberate)`: Explicitly tagged collections with custom notes.
* **Column 2 (Active Items)**: Instant search query bar or filtered list with relative line distances.
* **Column 3 (Live Preview & Route)**: Target URL, predicted tier (`[T1]` Reader, `[T2]` Media, `[T3]` WebKit), snippet summary, persisted workbench tabs, and saved vault login status.

### TUI Keybindings
| Key | Action |
| :--- | :--- |
| `/` | Jump directly into Search prompt |
| `h` / `l` / `Tab` / `Shift-Tab` | Switch between columns (Sections, List, Live Preview) |
| `j` / `k` / `Down` / `Up` | Move row selection (with relative distance markers) |
| `Enter` | Auto-route and open selection |
| `v` / `V` | Force launch in **Tier 3** WebKitGTK GUI |
| `r` / `R` | Force launch in **Tier 1** Terminal Reader |
| `m` / `M` | Force launch in **Tier 2** Media Streamer (`mpv` / `youtube-tui`) |
| `w` / `W` | Interactive popup menu to assign URL to existing or new Workbench |
| `y` / `Y` | **Yank** URL directly to Wayland clipboard (`wl-copy` / `xclip`) |
| `b` / `B` | Save deliberate bookmark with custom tag and note |
| `x` | **Delete** selected item across History, Bookmarks, or Workbenches |
| `C` | Clear history stream |
| `P` / `p` | Inspect Sovereign Vault credentials for domain |
| `q` | Quit dashboard |

---

## ⌨️ `wf-view` Modal Keyboard Controller

`wf-view` operates as a true Vim-modal Wayland window without URL bars, buttons, or decorative chrome:

### Normal Mode (Default)
| Key | Action |
| :--- | :--- |
| `j` / `k` | Smooth scroll down / up (120px) |
| `d` / `u` | Half-page scroll down / up |
| `gg` | Scroll to top of page |
| `G` | Scroll to bottom of document |
| `H` | Navigate backward in history (`history.back()`) |
| `L` | Navigate forward in history (`history.forward()`) |
| `r` / `R` | Reload page / Reload bypassing cache |
| `/` | In-page text search mode (`n` next, `N` previous) |
| `+` / `-` / `0` | Zoom in / Zoom out / Reset zoom |
| `f` | Trigger DOM link hinting engine (`AA`, `AB`, ...) |
| `i` | Enter `INSERT` mode manually |
| `p` | **Autofill credentials** from Sovereign Vault for current domain |
| `b` | Bookmark current URL and page title |
| `y` | Copy current URL to Wayland clipboard (`wl-copy`) |
| `E` | De-escalate back to Terminal Reader (`wf-reader`) |
| `q` | Terminate process and release WebKit rendering threads |

### Insert Mode
- Triggered automatically when clicking or focusing an `<input>`, `<textarea>`, or content-editable container, or by typing `i`.
- All keystrokes pass directly to the web page.
- Press **`Escape`** to blur the active input, restore keyboard sovereignty, and return to **`NORMAL`** mode.

### Link Hinting Mode (`f`)
- Press `f` to overlay two-letter badges over all visible interactive elements (`<a>`, `<button>`, `<input>`).
- Type the 2-letter hint to automatically trigger the click or focus the field.
- Links with `target="_blank"` are automatically intercepted and routed smoothly within the engine.
- Press `Escape` or `Backspace` to dismiss hints.

---

## 📖 `wf-reader` Keybindings & Bidirectional Escalation

When reading articles in the terminal:
- **`e` / `E`**: **Bidirectional Escalation**: Suspends curses, launches `wf-view --from-reader <url>`, and upon closing the GUI (via `q` or `e`/`E`), automatically restores terminal curses mode at the **exact same scroll position** (`scroll_y`).
- **`j` / `k`** (or `Down` / `Up`): Scroll down / up line-by-line.
- **`d` / `u`**: Half-page scroll down / up.
- **`g` / `G`**: Jump to top / bottom of article.
- **`1..N`**: Jump directly to referenced hyperlink number via `wf-open`.
- **`s`**: Save rendered Markdown file to `~/Documents/Webflow/<title>.md`.
- **`b`**: Bookmark page to `bookmarks.txt`.
- **`q`**: Quit reader.

---

## 🔐 Sovereign Credential Vault (`wf-pass`)

Webflow includes a built-in, local AES-GCM encrypted password vault (`~/.local/share/webflow/vault.enc`), eliminating third-party browser extensions.

### CLI Usage
```bash
# Add or update credentials
wf-pass add accounts.google.com user@example.com

# Retrieve credentials
wf-pass get accounts.google.com

# List all saved domain accounts
wf-pass list

# Delete saved credentials
wf-pass delete accounts.google.com user@example.com
```

### In-Browser Autofill
When visiting any login page in `wf-view`:
1. Press `p` in **`NORMAL`** mode.
2. `wf-view` retrieves credentials for `@domain` from the Sovereign Vault and securely injects them into the DOM without clipboard exposure.

---

## 🛡️ Native Ad/Tracker Shield & RAM Optimization (`lib/shield.py`)

- **Native WebKit Content Filtering**: Compiles EasyList and EasyPrivacy rules into native byte-compiled JSON filter stores via `WebKit.UserContentFilterStore`. Ads, trackers, and analytics scripts are dropped at the C++ network layer before execution.
- **Strict RAM Diet**: Ephemeral memory caches, automatic discard of disk cache bloat, and disabled background MSE video decoders reduce WebKitGTK memory consumption to ~150–220 MB.

---

## ⚙️ Configuration Files

### 1. Domain Routing Rules (`config/rules.conf` or `~/.config/webflow/rules.conf`)
```ini
[TIER1_ONLY]
wikipedia.org
.*\.wikipedia\.org
archlinux.org
news\.ycombinator\.com
danluu\.com

[TIER2_ONLY]
youtube\.com/watch.*
youtube\.com/shorts.*
youtu\.be/.*
twitch\.tv/.*
vimeo\.com/.*

[TIER3_ONLY]
gemini\.google\.com
accounts\.google\.com
github\.com
reddit\.com
```

### 2. Yazi Theme Configuration (`config/theme.conf` or `~/.config/webflow/theme.conf`)
```ini
[palette]
bg = -1
fg = 223
border = 240
border_active = 214
header_fg = 214
header_bg = 236
selected_fg = 235
selected_bg = 214
pill_normal_fg = 235
pill_normal_bg = 214
pill_search_fg = 235
pill_search_bg = 108
tier1 = 108
tier2 = 214
tier3 = 175
dim = 244

[layout]
ratio_nav = 0.20
ratio_mid = 0.48
ratio_preview = 0.32
show_relative_numbers = true
```

---

## 🚀 Installation & Setup

### Dependencies (Arch Linux)
```bash
sudo pacman -S webkit2gtk-4.1 python-gobject mpv yt-dlp trafilatura glow fzf wtype wl-clipboard kitty python-cryptography
```

### Symlink Binaries
Symlink the tools into `~/.local/bin` (or use TEL's `install.sh`):
```bash
ln -sfn $(pwd)/bin/webflow ~/.local/bin/webflow
ln -sfn $(pwd)/bin/wf-open ~/.local/bin/wf-open
ln -sfn $(pwd)/bin/wf-tier ~/.local/bin/wf-tier
ln -sfn $(pwd)/bin/wf-reader ~/.local/bin/wf-reader
ln -sfn $(pwd)/bin/wf-media ~/.local/bin/wf-media
ln -sfn $(pwd)/bin/wf-view ~/.local/bin/wf-view
ln -sfn $(pwd)/bin/wf-workbench ~/.local/bin/wf-workbench
ln -sfn $(pwd)/bin/wf-pass ~/.local/bin/wf-pass
ln -sfn $(pwd)/bin/wf-bookmarks ~/.local/bin/wf-bookmarks
```

### Set as System Default Browser
```bash
xdg-settings set default-web-browser wf-open.desktop
```

### Hyprland Compositor Snippet (`~/.config/hypr/hyprland.conf`)
```ini
# Webflow: Open Yazi TUI Dashboard
bind = $mainMod, W, exec, kitty --class webflow -e webflow

# Webflow: Open bookmark & history picker
bind = $mainMod, B, exec, kitty --class clip-term -e wf-bookmarks

# Webflow: Inject credentials into active window
bind = $mainMod SHIFT, P, exec, wf-pass

# Window rules: Chromeless floating or tiled WebKitGTK windows
windowrulev2 = noblur, class:^(wf-view|python3)$
windowrulev2 = bordersize 2, class:^(wf-view|python3)$
```

---

## 🛡️ License & Acknowledgments
Part of the **Terminal Everything Linux** initiative. MIT License.
