# Phase 1: Plugin Skeleton & Purity Harness — Skeleton Research

**Researched:** 2026-09-06
**Domain:** PyMOL 2.5.0 plugin-package skeleton — entry point, single-instance state anchoring, modeless 3-tab dialog shell, plugin install/verification flow
**Confidence:** HIGH (every load-bearing claim verified against `pymol-src/`, `tmp/bioCHEMeleon/`, or an executed headless probe `[RUN]`; one correction to prior research flagged below)

## ⚠ Correction to prior research: the real plugin module name

Prior research (`.planning/research/PITFALLS.md:172`, `:334`) states plugins load as `pymol.plugins.startup.<name>`. **The actual `sys.modules` key is `pmg_tk.startup.<name>`.** Verified chain:

- `pymol/plugins/__init__.py:14` does `from .legacysupport import *`; `legacysupport.py:17` does `from pmg_tk import startup`, exported via `__all__` (`legacysupport.py:19-24`). So the name `startup` inside `pymol.plugins` **is the `pmg_tk.startup` module object**.
- Loader: `mod_name = parent.__name__ + '.' + name` (`plugins/__init__.py:427`) → `pmg_tk.startup.<name>`. Install path uses the same prefix (`installation.py:339-340`).
- **Empirically confirmed** `[RUN: headless probe tmp/probe_skeleton.py via cmd.exe run-conda-pymol.bat -cq]`: `pymol.plugins.startup.__name__` → `pmg_tk.startup`; `startup.__path__` → `[C:\Users\nglok\.conda\envs\chemtools-win10\Lib\site-packages\pmg_tk\startup, ...site-packages\pymol\pymol_path\data/startup]`.
- `pymol.plugins.startup` remains a valid *attribute alias* to the same module object — but smoke assertions and `sys.modules` scans must key on **`pmg_tk.startup.serpentrum`**.

Impact: the anchor object, reload simulation, and adopt-defense all use `pmg_tk.startup` (details §2). Planning docs citing `pymol.plugins.startup.<name>` should be read as the alias.

---

## 1. bioCHEMeleon prior art (verified, borrowable)

### 1.1 Proven entry-point shape — `tmp/bioCHEMeleon/biochemeleon/__init__.py`

| Element | Code | Lines |
|---|---|---|
| Module-level singleton | `dialog = None` with GC-prevention comment ("MUST be module scope, not inside `__init_plugin__`, or the dialog flashes and vanishes") | `__init__.py:3-5` |
| Entry point | `def __init_plugin__(app=None):` → **local** `from pymol.plugins import addmenuitemqt` → `addmenuitemqt('bioCHEMeleon', run_plugin_gui)` | `__init__.py:129-138` |
| Open + raise | `global dialog`; `if dialog is None: dialog = PluginDialog()`; `dialog.show()` / `dialog.raise_()` / `dialog.activateWindow()` | `__init__.py:141-153` |
| Qt imports | **Module-level** `from pymol.Qt import QtCore, QtGui, QtWidgets` + `from pymol import cmd` | `__init__.py:156-157` |

**Deviation serpentrum should make:** bioCHEMeleon imports Qt at module level — this is exactly why its WSL tests need `MagicMock` stubs (`tmp/bioCHEMeleon/tests/test_setup_state.py:11-18`, documented in its `AGENTS.md:74`). Serpentrum's INFRA-02 requires zero stubs → `__init__.py` must import **nothing but stdlib at module level**; Qt imported lazily inside `run_plugin_gui` (sketch in §2.3). `[SRC: REQUIREMENTS.md:65]`

### 1.2 3-tab dialog shell — `PluginDialog(QtWidgets.QDialog)` (`__init__.py:160-240`)

- `super().__init__(parent)`; `setWindowTitle("bioCHEMeleon")`; `setMinimumWidth(420)` (`:167-170`).
- `self.tabs = QtWidgets.QTabWidget(self)` (`:173`); tab classes **lazily imported inside `__init__`** so a sibling-module bug can't break plugin load (`:175-181`); `self.tabs.addTab(tab, "label")` (`:183-184`).
- Layout: `QVBoxLayout(self)` → tabs → **bottom button row** `QHBoxLayout` with `addStretch(1)` then right-aligned buttons (`:222-240`). Borrowable pattern for the spec's bottom button row (`spec.md:21` — 7 buttons; Phase 1 renders placeholders only; exact set lands Phase 8 per `ROADMAP.md:139`).

### 1.3 Tab switching, modality, stay-on-top

- Switch: `self.tabs.setCurrentWidget(self.game_tab)` (`__init__.py:260`; also `:641`, `:866`). `setCurrentIndex(int)` is the sibling API.
- Main dialog **modeless forever**: `.show()`, NEVER `.exec_()`; grep-enforced (`AGENTS.md:69,43`).
- **Modal children are allowed**: Help dialog `QDialog(self)` + `exec_()` (`__init__.py:961-972`); win dialog `QMessageBox(self.window())` + `setWindowFlags(msg.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)` + `exec_()` — exact stay-on-top code at `gui_game.py:337-345` (Pitfall 5/B reference).

### 1.4 Gate rules to mirror (bioCHEMeleon `AGENTS.md`)

| Rule | Reference |
|---|---|
| Grep gate — ZERO matches for `import Tkinter\|import tkinter\|from tkinter\|import Pmw\|from Pmw\|app\.root\|grab_set\|mainloop\|Toplevel\|menuBar\.addmenuitem\|from PyQt5 import\|import PyQt5` across package; docstring literals can false-positive | `AGENTS.md:36-39` |
| exec_ gate — `\.exec_\(\)` hits only on child dialogs (QFileDialog/QMessageBox/QInputDialog), never the main dialog | `AGENTS.md:41-43` |
| Entry rules: `__init_plugin__(app=None)` (not legacy `__init__`); local `addmenuitemqt` import; `dialog = None` module scope; modeless `.show()`; Qt only via `from pymol.Qt import ...` | `AGENTS.md:66-70` |
| Strict dependency direction (pure ← bridge ← gui); `GAME_REPS`-style constants live in the pure layer | `AGENTS.md:48-64` |
| Test stub pattern (`sys.modules['pymol'] = MagicMock()`) — exists ONLY because of module-level Qt import; serpentrum avoids it by design | `AGENTS.md:72-75`, `tests/test_setup_state.py:11-18` |

Note: bioCHEMeleon's AGENTS.md does **not** document module-identity/anchoring — it relied on the module-global singleton alone. The anchoring design (§2) is serpentrum's addition per Pitfall 7.

---

## 2. State anchoring (Pitfall 7 / INFRA-03) — concrete mechanism

### 2.1 Verified loader/reload mechanics

| Fact | Source |
|---|---|
| Plugins discovered in `startup.__path__`: top-level `*.py` files and dirs with `__init__.py`; names starting with `.` or `_` skipped; duplicate names warn | `plugins/__init__.py:365-405` (`:383-385` skip rule) |
| Load: `__import__(self.mod_name, level=0)`; **force → `reload(self.module)`** | `plugins/__init__.py:273-277` |
| After import, `legacyinit` calls `mod.__init_plugin__(pmgapp)` | `plugins/__init__.py:302-324` |
| **The real "Plugin Manager reload"** = reinstall via local file → `info.load(force=1)` → `reload(self.module)` re-executes module code: module globals reset (`dialog = None`), old dialog orphaned on screen, `__init_plugin__` re-runs (second menu item) | `installation.py:342` → `plugins/__init__.py:273-275` |
| Plugin Manager's "Reload" button only rebuilds the list UI (`reload_plugins`); per-plugin "Load" button calls `info.load()` (force=0 → cached `__import__` + `__init_plugin__` re-run; button disabled when already loaded) | `managergui_qt.py:219, 235, 239-240` |
| `HAVE_QT` defaults False; set True ONLY by the Qt GUI before `initialize(app)` | `plugins/__init__.py:29`; `pmg_qt/pymol_qt_gui.py:972-973` |
| `addmenuitemqt` raises `QtNotAvailableError` when `HAVE_QT` is False; loader catches it gracefully | `plugins/__init__.py:100-108, 287-288` |

### 2.2 Why an attribute anchor on `pmg_tk.startup` works

`importlib.reload` re-executes **only the child module**; the parent package object `pmg_tk.startup` (a real package: `pymol-src/modules/pmg_tk/startup/__init__.py`, present even headless `[RUN]`) is untouched and permanently resident in `sys.modules`. An attribute set on it survives `reload(pmg_tk.startup.serpentrum)` AND is shared by any duplicate import of the package under a second name (bare `serpentrum`, staged copies) — defeating both halves of Pitfall 7 by construction. It also subsumes bioCHEMeleon's module-global GC trick (the anchor holds the only needed reference). `[SRC: Python importlib semantics; structure verified via sources above]`

### 2.3 Recommended code (py3.6 syntax — compile-verified `[RUN: python3.6 -m py_compile /tmp/opencode/anchor_sketch.py → OK]`)

```python
# serpentrum/__init__.py  (module level: NO pymol/Qt imports — INFRA-02)
def _anchor():
    """Return the stable single-instance state object.

    The plugin loads as 'pmg_tk.startup.serpentrum'; Plugin-Manager
    reinstall re-executes THIS module (reload), and a stray direct import
    may load it under a second name. Attributes on the 'pmg_tk.startup'
    package object survive both, so live state can never duplicate."""
    import pmg_tk.startup
    if not hasattr(pmg_tk.startup, '_serpentrum'):
        class _SerpentrumState(object):
            dialog = None       # the single PluginDialog instance
            controller = None   # the single live game controller (later phases)
        pmg_tk.startup._serpentrum = _SerpentrumState()
    return pmg_tk.startup._serpentrum

def __init_plugin__(app=None):
    from pymol.plugins import addmenuitemqt          # local import (F3)
    addmenuitemqt('serpentrum', run_plugin_gui)

def run_plugin_gui():
    state = _anchor()
    if state.dialog is None:
        from .gui import PluginDialog                # lazy: Qt loads on first open
        state.dialog = PluginDialog()
    state.dialog.show()                              # MODELESS — never .exec_()
    state.dialog.raise_()
    state.dialog.activateWindow()
```

**Belt-and-braces adopt-defense** (optional, in `gui.py`): before constructing, scan for an orphaned instance:

```python
@classmethod
def find_existing(cls):
    from pymol.Qt import QtWidgets
    for w in QtWidgets.QApplication.topLevelWidgets():
        if isinstance(w, cls):
            return w
    return None
```

`QApplication.topLevelWidgets()` **verified available and callable without an app instance** in the runtime env (`[RUN: probe → TOPLEVELWIDGETS_ATTR: True; call OK, empty list]`, PyQt5 5.12.9). `sys.modules` scanning (second import name) is NOT needed — the shared anchor already covers it; document the dev-rule instead (never rely on bare `import serpentrum` at runtime).

**Rejected alternative:** anchoring on the `pymol` package or `cmd._pymol.session` (Pitfalls.md:181) — works, but `pmg_tk.startup` is the loader's own plugin namespace, guaranteed present before any plugin runs `[RUN]`, and keeps serpentrum state discoverable via `dir(pmg_tk.startup)`.

---

## 3. Plugin install flow (SETUP-01)

### 3.1 Directories and persistence

- Default user plugin dir: **Windows `%APPDATA%\pymol\startup`**, Linux `~/.pymol/startup` — `[SRC: installation.py:22-29]`. It is NOT on the path by default; it gets added when an install lands there (`installation.py:210-229`).
- Path at runtime `[RUN]`: `pmg_tk.startup.__path__` = site-packages `pmg_tk/startup` + `$PYMOL_DATA/startup`; user paths = everything before the last 2 entries (`plugins/__init__.py:38-39, 49-53`).
- User path edits persist to `~/.pymolpluginsrc.py` (`plugins/__init__.py:18, 70-92`; executed at every GUI `initialize()`, `:415-420`).

### 3.2 What "Install from local file" accepts

`.py` files, `.zip`, `.tar.gz` (`installation.py:13-14, 282-315`). A **package directory** installs by pointing the file dialog at the package's `__init__.py` (`legacysupport.py:60` comment; `installation.py:299-308` `name == '__init__'` → `copytree` of the parent dir). Zip layout must be `zip/<name>/__init__.py` (case 1, `installation.py:118-136`). After install: `info.load(force=1)` → the module-reload path (§2.1).

### 3.3 Dev install — "add repo path to plugin path" (concrete steps, Windows PyMOL 2.5.0)

The Plugin Manager (Qt) has a path editor: "Add plugin directory" (defaults to the user plugin path), up/down/remove buttons; every edit calls `set_startup_path` and persists (`managergui_qt.py:384-390, 392-415, 83-88`).

1. Ensure repo layout is plugin-path-safe (see §6): `serpentrum/` package present; **no `__init__.py` in `tests/` or `smoke/`**; no stray top-level `.py` at repo root (findPlugins would register them as plugins and import them at GUI startup).
2. PyMOL → **Plugin → Plugin Manager** → **Add plugin directory** → select `C:\Users\nglok\Desktop\WORKDIR\molmdl\serpentrum` (WSL `/mnt/c/...` maps to `C:\...`).
3. Restart PyMOL. Autoload scans the path, finds `serpentrum/`, imports it as `pmg_tk.startup.serpentrum`, calls `__init_plugin__` → single **"serpentrum"** item under the **Plugin** menu (`pymol_qt_gui.py:960-973` clears + rebuilds the Plugin menu, sets `PluginQt` = Plugin, legacy items go under "Legacy Plugins").
4. Zero-copy iteration: edit code → restart PyMOL → changes visible (no staging copy needed, unlike bioCHEMeleon's `wsl2win_cp.sh` flow, which existed for its own staging discipline — `bioCHEMeleon/AGENTS.md:16,24`).
5. Release alternative: `zip -r serpentrum.zip serpentrum/` → Plugin Manager → Install from local file.

---

## 4. Dialog shell specifics (Phase-1 scope)

- **Shell:** `PluginDialog(QtWidgets.QDialog)`; title `serpentrum`; `setMinimumWidth(...)` (bioCHEMeleon 420, optimize 450 — `optimize.py:58-74`); `QVBoxLayout(self)` containing `QTabWidget` + bottom `QHBoxLayout` button row (`addStretch(1)` + right-aligned buttons) — `bioCHEMeleon/__init__.py:167-240`.
- **Tabs:** Setup / Game / Spectra via `addTab(QWidget, label)`; Phase 1 = placeholder `QWidget` + label per tab (real content: Phases 3/4/7 per ROADMAP).
- **Switching:** `tabs.setCurrentWidget(w)` / `setCurrentIndex(i)` (§1.3).
- **Modeless:** `.show()`; INFRA-05 gate = zero `.exec_()` in Phase 1 (no child dialogs exist yet).
- **Stay-on-top** (for later child modals; exact verified code): `w.setWindowFlags(w.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)` with parent `self.window()` — `gui_game.py:337-344`.

---

## 5. Headless smoke capabilities & limits (INFRA-01)

**Environment facts `[RUN: probe + bat read]`:** `run-conda-pymol.bat` activates env `chemtools-win10` (`%USERPROFILE%\.conda\envs`) and runs `python <env>\Lib\site-packages\pymol\__init__.py %*` — args pass through; `-cq` = command-line quiet mode. Runtime Python **3.9.13** (WSL 3.6 gate remains the stricter authoring subset — py3.6-compatible source runs on 3.9). **Qt 5.12.9 (PyQt5) imports headless**; `HAVE_QT` is False headless; `get_pmgapp()` returns a no-op `Scratch_Storage` fake (`pymol/gui.py:20-26`; `legacysupport.py:113-127`).

| Skeleton fact | Headless-verifiable? | How |
|---|---|---|
| Loader namespace `pmg_tk.startup` | ✅ `[RUN]` | `import pymol.plugins; plugins.startup.__name__` |
| Plugin imports under real loader name | ✅ | Append repo root to `pmg_tk.startup.__path__` → `__import__('pmg_tk.startup.serpentrum')`; assert `sys.modules` key |
| `__init_plugin__` callable without exception | ✅ (with flag) | Set `pymol.plugins.HAVE_QT = True` first (exactly what the real GUI does, `pymol_qt_gui.py:972`); `addmenuitemqt` → `addmenuitem` → fake menuBar no-op `[RUN: FAKE_PMGAPP Scratch_Storage]` |
| Lazy-import purity (no Qt at import time) | ✅ | After import, assert `'PyQt5.QtWidgets' not in sys.modules` (headless PyMOL doesn't preload Qt) — runtime proof of the module-level-import ban |
| Anchor survives reload | ✅ | `_anchor() is _anchor()`; `importlib.reload(mod)` → anchor object unchanged |
| Double-import defense | ✅ | Bare `import serpentrum` (staged dir on sys.path) → `serpentrum._anchor() is pmg_tk.startup._serpentrum` |
| Dialog construction + 3 tabs headless | ⚠ likely | Qt imports fine and a desktop session exists; `QApplication([])` + `PluginDialog()` + `tabs.count()==3` **unverified** → smoke should attempt in try/except and degrade to "skipped" |
| Menu item visible in Plugin menu | ❌ human | Fake menuBar swallows registrations headless |
| Dialog visible, modeless (viewer responsive), tab labels, raise_/activateWindow, stay-on-top visuals | ❌ human | Requires real GUI session |

Smoke conventions (borrowed, proven): stage under `/mnt/c`-mapped path, `cd` there, `timeout 90 cmd.exe /c "C:\\src\\run-conda-pymol.bat -cq <script>"`, exit 0 = clean (`bioCHEMeleon/AGENTS.md:13-22`). Probe executed today exactly this way `[RUN]`.

---

## 6. Repo layout confirmation (RQ6)

Repo root today (`ls`): `AGENTS.md LICENSE README.md spec.md opencode.json test_wsl_winxtb.sh .gitignore .planning/ tmp/` + symlinks `pymol-src → ../bioCHEMeleon/tmp/pymol-src`, `Pymol-script-repo → ...`, `xtb-6.7.1 → /mnt/c/xtb-6.7.1`. **`serpentrum/` does not exist — greenfield.** ARCHITECTURE.md's layout (`:113-141`) stands, with these Phase-1 adjustments:

- **`tests/` and `smoke/` must NOT contain `__init__.py`** and repo root must stay free of top-level `.py` files. Reason: the dev plugin path IS the repo root (§3.3), and `findPlugins` registers any dir-with-`__init__.py` or `*.py` at top level as a plugin, importing it at GUI startup (`plugins/__init__.py:383-401`). bioCHEMeleon's `tests/` HAS an `__init__.py` (`tmp/bioCHEMeleon/tests/`) — safe there only because its repo root was never a startup path. Run WSL tests via `python3.6 -m unittest discover -s tests -t .`; test files self-insert the repo root on `sys.path` (pattern: `test_setup_state.py:18`).
- `tmp/` is git-ignored (`.gitignore:22`) → probe scripts, staging copies, xtb runs live there; never commit.
- Harness files: `tests/test_purity_gates.py` (stdlib-only `re` walk of `serpentrum/*.py` enforcing the §1.4 greps + py3.6-compilability of every module — no grep binary dependency, zero stubs, extends per-phase to new pure modules) and `smoke/01_skeleton_smoke.py` (§5 assertions).
- Constraints honored: `opencode.json` denies `rm *` / `rg *`; `git *` allowed; spec.md hard rules (no fabricated citations; only pymol-open-source deps).

---

## Planning Implications

- **Task order:** (1) package scaffold + anchor-based entry (`serpentrum/__init__.py` per §2.3, empty `gui.py` 3-tab shell) → (2) purity gates + WSL test scaffold (`tests/test_purity_gates.py`, py3.6 gate green) → (3) headless smoke `smoke/01_skeleton_smoke.py` (namespace/import/`__init_plugin__`/reload/double-import assertions) → (4) human-verify checkpoint (plugin-path install + single dialog + modelessness). Tasks 2–3 parallelizable after 1.
- **Write the module name correctly everywhere:** `pmg_tk.startup.serpentrum` (alias `pymol.plugins.startup` exists but is not the sys.modules key). Correct PITFALLS.md's wording in passing if convenient.
- **Anchor from commit one:** `_anchor()` on `pmg_tk.startup` + lazy Qt import in `run_plugin_gui`; adopt-defense scan optional but cheap. INFRA-03's reload/double-import halves are provable headlessly — put both assertions in the smoke.
- **Plugin-path safety conventions in AGENTS/plan:** no `__init__.py` in `tests/`/`smoke/`, no top-level `.py` at repo root.
- **Verified vs human-verify:** headless = namespace, import, entry call, purity, reload, double-import; human = install via Plugin Manager path editor, single visible menu item, dialog appears modeless, viewer stays interactive, double-click/reinstall yields one dialog.
- **Button set note:** spec.md:21 lists 7 bottom buttons; Phase 1 renders placeholder tab widgets and (optionally) a disabled placeholder button row — the real 6+button set is Phase 8 scope (`ROADMAP.md:139`).
- **Runtime is Python 3.9.13** — author py3.6-compatible anyway (WSL gate is stricter; bioCHEMeleon discipline, %-formatting preferred).

## Confidence Assessment

| Area | Level | Basis |
|---|---|---|
| Entry-point pattern | HIGH | bioCHEMeleon `__init__.py:129-153` + `optimize.py:29-44` read; loader source verified |
| Module name / reload mechanics | HIGH | Source chain (legacysupport:17 → plugins:427) + `[RUN]` probe |
| Anchor design | HIGH (mechanics) / MEDIUM (runtime behavior) | py3.6 compile `[RUN]`; reload semantics from source; runtime dialog-adopt behavior is human-verify |
| Install flow / Plugin Manager steps | HIGH | `installation.py` + `managergui_qt.py` read; `[RUN]` startup path contents. (Whether `~/.pymolpluginsrc.py` already exists on this machine not checked — irrelevant to steps.) |
| Headless smoke scope | HIGH for listed ✅ | Probe executed today in the real env |
| Dialog construction headless | MEDIUM-LOW | Qt imports `[RUN]`; QApplication+widget construction untested — smoke must degrade gracefully |
| Purity-gate mechanics | HIGH | bioCHEMeleon gate commands proven (`AGENTS.md:36-43`); re-implementation as stdlib-`re` unittest is straightforward |
