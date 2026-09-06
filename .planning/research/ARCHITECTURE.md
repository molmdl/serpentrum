# Architecture Research

**Domain:** PyMOL plugin — educational snake game (molecule stacking + xtb IR spectra)
**Researched:** 2026-09-06
**Confidence:** HIGH for startup/Qt/timer/subprocess (verified against `pymol-src`, `Pymol-script-repo`, and `tmp/bioCHEMeleon` prior art); MEDIUM-LOW for a small number of flagged items (listed in Open Questions).

All file:line citations below were read and verified today. Empirical xtb claims were verified by actually running the Windows `xtb.exe` from WSL (see §xtb Pipeline).

---

## 1. Verified Platform Facts (foundation for every component)

These are the load-bearing facts. Everything in the architecture builds on them.

| # | Fact | Source (verified) |
|---|------|-------------------|
| F1 | Plugin discovery accepts **packages** (directories with `__init__.py`), not just single files | `pymol-src/modules/pymol/plugins/__init__.py:365-367` ("Find all python modules (extension .py and directories with `__init__.py`)") |
| F2 | Loader does `__import__(mod_name)` then `legacyinit(pmgapp)` which calls **`__init_plugin__(pmgapp)`** (falls back to a legacy module-level `__init__` *function*) | `pymol-src/modules/pymol/plugins/__init__.py:248-281, 302-324` |
| F3 | **`pmg_qt` is the modern path**: `addmenuitemqt(label, command)` registers the Plugins-menu item; raises `QtNotAvailableError` if Qt is missing, which the loader catches gracefully ("Plugin only available with PyQt GUI") | `plugins/__init__.py:100-108, 287-288` |
| F4 | `pmg_tk` survives only as **legacy support**: `legacysupport.py` imports `from pmg_tk import startup` (line 17) and `legacyinit`'s `__init__` fallback exists for old plugins. `pmg_tk/startup/` is the legacy drop dir. **Do NOT build on pmg_tk.** | `pymol-src/modules/pymol/plugins/legacysupport.py:17`; `modules/pmg_tk/` (legacy Tcl/Tk GUI) |
| F5 | User plugin dir: `~/.pymol/startup` (Linux) / `%APPDATA%\pymol\startup` (Windows); `$PYMOL_DATA/startup` also on path. Dev install = add package dir to plugin path (Plugin Manager "startup paths") | `pymol-src/modules/pymol/plugins/installation.py:24-29`; `plugins/__init__.py:38` |
| F6 | Canonical entry pattern (identical in both reference corpora): `def __init_plugin__(app=None):` → **local** import of `addmenuitemqt` → register callback; module-level `dialog = None` singleton; `dialog.show()` (**modeless, NEVER `.exec_()`**) | `Pymol-script-repo/plugins/optimize.py:29-44`; `tmp/bioCHEMeleon/biochemeleon/__init__.py:129-153` |
| F7 | Qt imports via `from pymol.Qt import QtCore, QtGui, QtWidgets` (auto-selects PyQt5/PySide2) — NEVER `from PyQt5 import` | bioCHEMeleon `AGENTS.md` domain rules; `optimize.py:25` |
| F8 | Tabbed dialog = `QTabWidget` + `addTab(QWidget, label)` | `optimize.py:72-79`; bioCHEMeleon `__init__.py:172-184` |
| F9 | Timers: `QtCore.QTimer` (interval) for the clock; recursive `QTimer.singleShot(ms, fn)` for countdown/async drains; `cmd.refresh()` before delayed UI so a redraw lands first | bioCHEMeleon `gui_game.py:108-111` (1 Hz clock), `:258-264` (3-2-1 countdown), `:289-304` (refresh + 100 ms delay) |
| F10 | Threading rule: worker threads are **stdlib-only and make NO `cmd.*` calls**; results flow through a `queue.Queue`, drained on the main thread by recursive `QTimer.singleShot`; all `cmd.*` happens in the drain | bioCHEMeleon `__init__.py:545-677` (worker + queue + modeless QProgressDialog + drain) |
| F11 | Key binding API: `cmd.set_key(key, fn)` → `key_mappings` → `_invoke_key`; special key names `'left'`(100), `'up'`(101), `'right'`(102), `'down'`(103) | `controlling.py:719-768`; `internal.py:398-423, 427-443` |
| F12 | Qt key path (external GUI): `keyPressEvent` → `keymapping.keyPressEventToPyMOLButtonArgs` maps `Qt.Key_Left/Up/Right/Down → 100/101/102/103` (state=-2, special) → `pymolwidget.pymol.button(*args)` | `pmg_qt/pymol_qt_gui.py:50-54`; `pmg_qt/keymapping.py:19-28` |
| F13 | ⚠️ **ARROW-KEY RISK**: `set_key` docstring "KEYS WHICH CAN BE REDEFINED: F1 to F12, left, right, pgup, pgdn, home, insert, CTRL-A..Z, ALT-0..9/A..Z" — **`up`/`down` are NOT listed**, and `shortcut_manager.py` reserves `'up','down'` (CLI history). In-tree precedents bind `'left'/'right'` (filter.py:101-105) and `'pgup'/'pgdn'` (density.py:68-69); **no in-tree code binds `'up'`/`'down'`** | `controlling.py:755-760`; `pymol/shortcut_manager.py:21`; `pymol/wizard/filter.py:101-105`; `pymol/wizard/density.py:68-69` |
| F14 | Movement/geometry APIs exist in 2.5.0: `alter_state` (editing.py:1535), `translate` (editing.py:1610), `transform_selection` (editing.py:1946), `translate_atom` (editing.py:2169), `get_coordset` (querying.py:914), `get_model` (querying.py:1053), `get_extent` (used by bioCHEMeleon `__init__.py:387`) | `pymol-src/modules/pymol/editing.py`, `querying.py` |
| F15 | CGO constants + `cmd.load_cgo(obj, name)`: `LINES/TRIANGLE_STRIP/VERTEX/COLOR/CYLINDER/CONE/SPHERE/LINEWIDTH` in `pymol/cgo.py:22-65`; box drawing via `TRIANGLE_STRIP` faces is in-tree prior art (`pymol/wizard/box.py:261-311`), loaded via `cmd.load_cgo(obj, name, zoom=0)` (box.py:380) | `pymol/cgo.py`; `pymol/wizard/box.py` |
| F16 | Camera helpers: `cmd.zoom(selection, buffer, ...)` (viewing.py:65), `cmd.origin` (viewing.py:227) | `pymol-src/modules/pymol/viewing.py` |
| F17 | PyMOL open source has **NO undo** — every destructive op needs snapshot/restore (bioCHEMeleon `backup.py` pattern). serpentrum avoids most of this by never mutating user objects (see A1 below) | bioCHEMeleon `AGENTS.md` phase-3 rules; `biochemeleon/backup.py` |
| F18 | Native molecule formats: `chempy/mol2.py` **and** `chempy/sdf.py` both ship in 2.5.0 → `.mol2`/`.sdf` demo files load natively via `cmd.load` | `pymol-src/modules/chempy/mol2.py`, `chempy/sdf.py` |
| F19 | **xtb flags (EMPIRICAL, run today):** `xtb.exe mol.xyz -o --hess` does **NOT** produce any vibrational output — log ends at the optimization summary, no `vibspectrum`/`g98.out`/`hessian` files (the `--hess` Hessian is consumed internally by the ANC optimizer). `xtb.exe mol.xyz --ohess` (optimize + Hessian) **produces** `hessian`, `vibspectrum`, `g98.out`, `xtbopt.xyz` | `tmp/xtb_test/` (old run — no freq files) vs `tmp/xtb_ohess_test/` (new run today — all three files present); `test_wsl_winxtb.sh` pattern proven for WSL→Windows invocation |
| F20 | `vibspectrum` format (Turbomole): `$vibrational spectrum` header, 2 `#` comment lines, rows = `mode  symmetry  wavenumber(cm⁻¹)  IR-intensity(km·mol⁻¹)  selection-rules`, terminated by `$end`. First 5-6 rows are near-zero translations/rotations (3N-6 real modes after) | `tmp/xtb_ohess_test/vibspectrum` (phenol: modes 1-6 ≈ 0, 7-39 real) |
| F21 | `g98.out` (Gaussian format) contains **everything needed in one file**: `Frequencies --` / `IR Inten    --` blocks (3 modes per block) **plus per-atom `X Y Z` normal-coordinate displacement vectors** under each block — no Hessian eigendecomposition or mass bookkeeping needed | `tmp/xtb_ohess_test/g98.out:33-53` (freq/inten header rows + `Atom AN X Y Z` vector rows) |
| F22 | WSL `python3.6` (3.6.9) has **NO numpy** (verified: `ModuleNotFoundError: No module named 'numpy'`); stdlib (json/math/struct/subprocess/threading/queue/tempfile) all available. → **Pure modules must be stdlib-only at module level** or WSL unit tests cannot import them. This is exactly why the AA-match-style gate forbids pymol/Qt/numpy at module level | Verified today in dev shell |
| F23 | Pure-layer testing precedent: WSL `python3.6 -m unittest` for pure modules; `MagicMock` stubbing of `pymol`/`pymol.Qt` in `sys.modules` only needed because bioCHEMeleon's `__init__.py` imports Qt at **module level** — the AA-match pattern (lazy imports, no module-level pymol/Qt/numpy) removes the need for stubs entirely. Headless cmd-only verification via `cmd.exe /c C:\src\run-conda-pymol.bat -cq <script>` from WSL | bioCHEMeleon `tests/test_setup_state.py:13-17`, `AGENTS.md` (Commands + Environment sections) |
| F24 | QPainter plot widget precedent (no matplotlib): `paintEvent` + `paintAxes`/`paintColorDots` with `drawLine/drawText/drawEllipse`, repaint via `self.update()` | `Pymol-script-repo/plugins/dynoplot.py:68-185, 320` |
| F25 | matplotlib exists in other plugins only as a **user-installed extra** (vina.py tells users to install it) — outside serpentrum's "only what pymol-open-source ships" constraint. Whether the local conda env happens to have matplotlib is unverified — and must not matter | `Pymol-script-repo/plugins/vina.py:108-112` |

---

## 2. Standard Architecture

### System Overview

```
┌────────────────────────────────────────────────────────────────────────────┐
│  PLUGIN ENTRY (thin)                                                       │
│  serpentrum/__init__.py — __init_plugin__ → addmenuitemqt → singleton      │
│  dialog (module-level ref, modeless .show())  [F2,F3,F6,F8]                │
└──────────────┬─────────────────────────────────────────────────────────────┘
               │ creates/owns
┌──────────────▼─────────────────────────────────────────────────────────────┐
│  Qt UI LAYER (pymol.Qt only; no cmd.* except via controller)               │
│  ┌────────────┐  ┌────────────┐  ┌──────────────────┐  ┌───────────────┐   │
│  │ gui_setup  │  │ gui_game   │  │ gui_spectra      │  │ plot_widget   │   │
│  │ (Setup tab)│  │ (Game tab) │  │ (Spectra tab)    │  │ (QPainter,    │   │
│  │            │  │ log/timer/ │  │ xtb cfg+log+     │  │  embeddable   │   │
│  │            │  │ pause/restart│ │ plot+freq table  │  │  in Spectra)  │   │
│  └─────┬──────┘  └─────┬──────┘  └────────┬─────────┘  └───────┬───────┘   │
│        └───────────────┴──── signals/slots ▼                    │           │
│  controller.py — composition root (wires Qt ↔ engine ↔ bridge ↔ runner)    │
└──────┬───────────────┬────────────────────┬───────────────────┬───────────┘
       │               │                    │                   │
┌──────▼───────┐ ┌─────▼────────┐ ┌─────────▼──────────┐ ┌──────▼──────────┐
│ PURE CORE    │ │ PYMOL BRIDGE │ │ XTB RUNNER         │ │ INPUT           │
│ (stdlib only)│ │ pymol_bridge │ │ (thread+queue+     │ │ input.py:       │
│ game_engine  │ │ .py (cmd.*)  │ │  subprocess)       │ │ cmd.set_key +   │
│ stacking     │ │ loads/copies │ │ xtb_runner.py      │ │ Qt eventFilter  │
│ cgo_build    │ │ translate/   │ │ + xtbenv.py (PURE: │ │ fallback [F13]  │
│ spectra_parse│ │ transform/   │ │  detect+path conv.)│ │                 │
│ xyzio        │ │ load_cgo/    │ └─────────┬──────────┘ │                 │
│ molecule_data│ │ zoom/origin  │           │ spawns     │                 │
│ setup logic  │ │ [F14-F18]    │           ▼            │                 │
│ [F22]        │ └──────────────┘ │  Windows xtb.exe       │                 │
└──────────────┘                  │  --ohess (from WSL)    │                 │
      ▲                           │  [F19,F10]             │                 │
      │ unit-tested in WSL        └────────────────────────┘                 │
      │ python3.6 unittest (no numpy!)                                       │
┌─────┴──────────────────────────────────────────────────────────────────────┐
│  TESTS: tests/ (WSL python3.6, pure modules) · smoke/ (headless Windows    │
│  PyMOL via cmd.exe /c run-conda-pymol.bat -cq) · human-verify (Qt/keys)    │
└────────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Talks to | Kind |
|-----------|----------------|----------|------|
| `serpentrum/__init__.py` | `__init_plugin__` (local `addmenuitemqt` import), module-level `dialog=None` singleton, `run_plugin_gui()` → `.show()` + `raise_()` + `activateWindow()` | imports `gui` lazily | entry (Qt) |
| `gui.py` (`PluginDialog`) | 3-tab QTabWidget + bottom button row (Reset, Randomize, Save Setup, Load Setup, Cleanup, Start); routes Start → Game tab + countdown; owns controller | gui_setup/gui_game/gui_spectra, controller | Qt |
| `gui_setup.py` | Setup tab widgets (demo-set dropdown / file upload, box preset, head choice, xtb path, win cap), `collect_state()` → dict | setup logic (pure) | Qt |
| `gui_game.py` | Info log, elapsed clock (QTimer), remaining/score labels, pause/resume toggle, restart | controller callbacks | Qt |
| `gui_spectra.py` | xtb options, Start-calculation button, progress log, embedded `SpectrumPlotWidget`, plot-adjust controls, Save-plot, frequency QTableWidget | controller, xtb_runner events | Qt |
| `plot_widget.py` | QPainter spectrum canvas (axes, Gaussian curve, labels); `set_data(freqs, intensities, curve)`; `update()` repaint | gui_spectra | Qt (no cmd) |
| `controller.py` | Composition root: owns engine/renderer/runner/input; all `cmd.*` calls orchestrated here; Qt callbacks in, engine events out | everything | cmd + Qt |
| `game_engine.py` | **PURE** grid + snake state: positions, direction queue, step(), pickup detection, boundary/self collision, score, win cap, atom budget | stacking, molecule_data | pure |
| `stacking.py` | **PURE** rigid-body placement: given pickup molecule geometry + known stacking mode + distance + tail anchor → transform (rotation+translation) and stacked coords | game_engine | pure |
| `cgo_build.py` | **PURE** CGO float-list builders: box edges/faces from extents, vibrational-mode arrows from (atom, vec) pairs | renderer applies via bridge | pure |
| `spectra.py` | **PURE** parse `g98.out` (freq/inten/vectors; `vibspectrum` fallback) + Gaussian broadening → (grid_x, grid_y) | gui_spectra via controller | pure |
| `xyzio.py` | **PURE** write final snake as `.xyz` for xtb; read/validate demo manifests | controller, molecule_data | pure |
| `xtbenv.py` | **PURE** xtb discovery: `xtb` vs `xtb.exe` by OS, path validation, WSL→Windows conversion (`/mnt/c/...` → `C:/...`), cwd choice | xtb_runner | pure |
| `xtb_runner.py` | Worker thread (stdlib-only: `subprocess.run` on `xtb --ohess`, streaming log lines into `queue.Queue`) + cancellation `Event`; main thread drains via QTimer (controller owns drain) | xtbenv, controller | subprocess/threading |
| `pymol_bridge.py` | The ONLY module (besides controller/input) importing `pymol.cmd`: load demo/user molecules, `cmd.create` game copies into `srp_*` namespace, `translate`/`transform_selection` movement, `load_cgo` box/arrow objects, `zoom/origin` focus, `get_model/get_coordset` extraction, cleanup-by-prefix `delete` | controller | cmd |
| `input.py` | Bind arrows via `cmd.set_key` during play (save prior bindings; restore on stop); **fallback**: Qt application-level event filter capturing arrows if `up`/`down` prove unbindable (F13) | cmd + QtCore | cmd + Qt |
| `data/demos/` + `SOURCES.md` | Pre-downloaded demo molecule files (mol2/sdf) + verified stacking/distance data + citations | molecule_data (pure manifest) | data |

### Recommended Project Structure

```
serpentrum/
├── serpentrum/              # the installable plugin package (added to plugin path)
│   ├── __init__.py          # entry: __init_plugin__ + dialog singleton (THIN — no logic)
│   ├── gui.py               # PluginDialog shell: tabs + button row + tab switching
│   ├── gui_setup.py         # Setup tab
│   ├── gui_game.py          # Game tab
│   ├── gui_spectra.py       # Spectra tab
│   ├── plot_widget.py       # QPainter spectrum canvas (Qt-only)
│   ├── controller.py        # composition root (cmd + Qt orchestration)
│   ├── input.py             # key bindings + event-filter fallback
│   ├── pymol_bridge.py      # ALL cmd.* side effects (object lifecycle, motion, cgo)
│   ├── xtb_runner.py        # subprocess worker + queue (threading, NO cmd)
│   ├── game_engine.py       # PURE
│   ├── stacking.py          # PURE
│   ├── cgo_build.py         # PURE
│   ├── spectra.py           # PURE (g98/vibspectrum parse + broadening)
│   ├── xyzio.py             # PURE (.xyz writer)
│   ├── xtbenv.py            # PURE (xtb detect / path conversion)
│   ├── setup_logic.py       # PURE (defaults, validation, save/load setup dicts, randomize)
│   ├── molecule_data.py     # PURE (demo manifest: stacking modes, distances, atom counts)
│   └── data/
│       └── demos/           # mol2/sdf files + SOURCES.md (verified citations)
├── tests/                   # WSL python3.6 unittest — pure modules ONLY
├── smoke/                   # headless Windows PyMOL scripts (cmd-only; staged + run via cmd.exe)
├── tmp/                     # git-ignored: xtb runs, staging copies (wsl2win_cp pattern)
├── .planning/
└── spec.md / AGENTS.md / README.md
```

**Structure rationale:**
- **Package (not single file)** — officially supported by the loader (F1), matches bioCHEMeleon precedent, and the purity gate needs the file split.
- **`pymol_bridge.py` as the single cmd seam** — strict dependency direction like bioCHEMeleon (`pure ← bridge ← gui/controller`); makes the "no pymol at module level in pure modules" grep gate trivially enforceable.
- **`xtb_runner.py` thread is stdlib-only** — mirrors the verified bioCHEMeleon download-worker pattern (F10) and is WSL-testable with a stub executable.
- **`smoke/` mirrors `tests/`** — every cmd-coupled behavior gets a headless script (F23 pattern); Qt visuals stay human-verify checkpoints.

---

## 3. Architectural Patterns

### Pattern 1: Thin entry + lazy imports (plugin-loading safety)

**What:** `__init__.py` contains only the entry function, the dialog singleton, and a lazy `PluginDialog` import. No heavy imports at module level; Qt imported inside functions/`__init__`.
**When:** Always — the loader imports every plugin at PyMOL startup (F2); an exception at import time = "Unable to initialize plugin" warning for the user (caught at `plugins/__init__.py:287-297`).
**Trade-offs:** Slightly more indirection; in exchange, a bug in a sibling module can't break plugin load, and pure modules import cleanly under WSL python3.6 with no stubs (F22-F23).

```python
# serpentrum/__init__.py (verified pattern: optimize.py:29-44 + bioCHEMeleon __init__.py:129-153)
dialog = None  # module scope: GC prevention — a dialog held only in a local
               # variable flashes and vanishes (bioCHEMeleon AGENTS rule)

def __init_plugin__(app=None):
    from pymol.plugins import addmenuitemqt   # local import: Qt-missing stays graceful [F3]
    addmenuitemqt('serpentrum', run_plugin_gui)

def run_plugin_gui():
    global dialog
    if dialog is None:
        from . import gui                     # lazy: heavy imports on first open only
        dialog = gui.PluginDialog()
    dialog.show()          # MODELESS — viewer stays interactive; NEVER .exec_() [F6]
    dialog.raise_()
    dialog.activateWindow()
```

### Pattern 2: Main-thread-only cmd with worker→queue→QTimer-drain (async everything)

**What:** Any slow operation (xtb subprocess; later, anything >100 ms) runs in a daemon `threading.Thread` that touches **only stdlib** and pushes events into a `queue.Queue`. The main thread drains the queue with recursive `QTimer.singleShot(100, drain)` and performs all `cmd.*`/UI updates there. Cancellation via `threading.Event`.
**When:** xtb runs (seconds → minutes for large snakes); any future long op.
**Trade-offs:** More moving parts than a blocking call, but a blocking call freezes the whole PyMOL Qt event loop (UI + viewer). This exact pattern is proven in-repo (bioCHEMeleon large-demo fetch, F10).

```python
# worker (NO cmd.*, NO Qt):                       # drain on main thread (controller):
def worker(cwd, argv, q, cancel):                 def drain():
    proc = subprocess.Popen(argv, cwd=cwd,            while True:
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,   try: ev = q.get_nowait()
        text=True)                                        except queue.Empty: break
    for line in proc.stdout:                          if ev[0] == 'log':   log_panel.append(ev[1])
        if cancel.is_set():                           elif ev[0] == 'done': parse_and_plot(ev[1])
            proc.kill()                               elif ev[0] == 'error': show_error(ev[1])
        q.put(('log', line.rstrip()))                 if finished(q, cancel, proc): return
    q.put(('done', returncode))                       QTimer.singleShot(100, drain)
```

### Pattern 3: Engine-owns-truth, renderer-applies (authoritative pure state)

**What:** `game_engine.py` holds the authoritative grid positions in plain Python data (cell coords, direction queue, snake chain as list of molecule ids). Each tick: `engine.step()` → event list (`moved`, `ate`, `crashed`, `won`) → `pymol_bridge` translates object(s) by the exact grid delta; UI labels update from engine counters. PyMOL object coordinates are a **projection** of engine state, never the source of truth.
**When:** The whole game loop.
**Trade-offs:** Tiny float drift if using incremental `cmd.translate` is cured by re-syncing coordinates from engine truth (`alter_state`/`transform_selection`) on stack events; cheap at ≤ a few hundred atoms.

```python
# tick (QTimer at game-speed interval, e.g. 250 ms — countdown/1 Hz clock verified F9):
events = engine.step(pending_direction)          # PURE
for ev in events:
    if ev.kind == 'move':
        bridge.translate_object(ev.obj, ev.delta)     # cmd.translate [F14]
    elif ev.kind == 'stack':
        bridge.apply_transform(ev.obj, ev.matrix)     # cmd.transform_selection [F14]
        bridge.resync_coords(engine_snake)            # optional truth re-sync
bridge.refresh_box_if_needed(); update_labels(engine.score, engine.remaining)
```

### Pattern 4: Game-created-object namespace (cleanup without undo)

**What:** serpentrum never mutates user molecules. All game artifacts are *copies* created via `cmd.create` into a `srp_`-prefixed namespace (`srp_head`, `srp_pickup_03`, `srp_box_cgo`, ...). Cleanup = `cmd.delete` everything matching the prefix. Originals stay pristine, so PyMOL's missing undo (F17) is a non-issue for v1 — the bioCHEMeleon backup/restore machinery is *not needed* at first.
**When:** Setup→Start→gameplay→Spectra lifecycle; "Cleanup model" button.
**Trade-offs:** Slightly more objects in the session; vastly simpler and safer lifecycle. If a later feature must mutate user objects (e.g., merging the snake into the user's object), adopt the bioCHEMeleon snapshot/restore pattern then.

### Pattern 5: Key bindings with save/restore + fallback path

**What:** During play, `input.py` binds `'left'/'right'` (and `'up'/'down'` behind a spike — F13) via `cmd.set_key`, saving any prior bindings first (the in-tree precedent saves/restores: `filter.py:101-105` binds, `:398-402` restores). On pause/stop, restore. If `up`/`down` set_key binding fails human verification, fall back to a Qt application-level event filter (`QApplication.instance().installEventFilter`) that captures arrow KeyPress events during play — standard Qt, and PyMOL itself uses `eventFilter` internally (`pymol_qt_gui.py:438-453`).
**When:** Countdown end → `_begin_play`; stop on game over/pause (pausing may keep bindings but queue them).
**Trade-offs:** set_key path is idiomatic PyMOL and survives viewer focus; the event-filter path is Qt-side and also works when the plugin dialog has focus — the two are complementary, not exclusive.

---

## 4. Data Flow

### Main lifecycle flow

```
Setup tab (gui_setup)
  → collect_state() → validated setup dict (setup_logic PURE: defaults/validate/randomize)
  → controller.start_game():
      1. resolve demo/upload molecules  → cmd.load (mol2/sdf native, F18)
      2. cmd.create copies into srp_* objects (Pattern 4); get_model/get_extent →
         per-molecule geometry (atoms, anchor atoms) fed to engine + molecule_data
      3. compute box extent (preset size) → cgo_build.box_cgo() → cmd.load_cgo [F15]
      4. place head (center) + N pickups (engine-placed grid cells)
      5. switch to Game tab → countdown (QTimer.singleShot chain, F9)
      6. bind keys (input.py) + start tick QTimer
        ↓
Game loop (each tick, main thread):
  key events → direction queue (engine)
  engine.step() [PURE] → events: move / stack / crash / win
  pymol_bridge: cmd.translate(head) per tick; on 'stack':
      stacking.transform(pickup_geom, mode, distance, tail_anchor) [PURE]
      → cmd.transform_selection(pickup_obj, matrix) [F14] → snake chain append
  labels: elapsed (QTimer clock), molecules-remaining, hidden atom-count budget
  crash/win → stop tick timer, unbind keys → clear pickups (delete srp_pickup_*),
      zoom/origin on snake (F16) → show length + score → enable "Get Spectra"
        ↓
Spectra flow:
  controller.get_spectra():
  1. extract final snake coords (cmd.get_coordset / get_model) [F14]
  2. xyzio.write_xyz(elements, coords, path) [PURE]  → tmp/xtb_runs/<id>/snake.xyz
     (dir on /mnt/c so Windows exe sees it — test_wsl_winxtb.sh pattern)
  3. xtbenv.detect() [PURE]: OS → 'xtb' | 'xtb.exe'; path convert /mnt/c/... → C:/...
  4. atom-budget guard (engine counters + molecule_data) → warn if > cap [N³ hessian]
  5. xtb_runner: worker thread runs `xtb(.exe) snake.xyz --ohess` [F19]
     → ('log', line) events → drain → Spectra log panel
     → ('done', rc) → parse on main thread
  6. spectra.parse_g98(path) [PURE] → modes: [(freq cm⁻¹, IR inten, [vec per atom])]
     (F20/F21; vibspectrum fallback for freq/inten only)
  7. spectra.broaden(modes, x_grid, fwhm) [PURE] → (x, y) curve
  8. plot_widget.set_data(...); frequency QTableWidget ← modes
        ↓
Vector display (no animation in v1):
  table row click → mode vector list → cgo_build.mode_arrows(atoms, vecs, scale) [PURE]
  → cmd.load_cgo('srp_modes_cgo') [F15] (delete+reload per selection)
        ↓
Save plot: plot_widget grab → PNG via Qt (human-verify; see Open Questions)
```

### State ownership map (single source of truth per datum)

| Datum | Owner | Projections |
|-------|-------|-------------|
| Grid positions, direction, snake chain, score, cap, atom budget | `game_engine` | labels, bridge calls |
| Stacking geometry transforms | `stacking` (pure fn) | bridge apply |
| xtb availability, resolved exe path, cwd | `xtbenv` (pure fn, cached by controller) | runner, Setup tab |
| Modes (freq/inten/vectors), broadened curve | `spectra` output (held by controller) | plot widget, table, CGO arrows |
| Elapsed time | GUI (start timestamp + QTimer), mirroring bioCHEMeleon's rebase-on-dialog trick | timer label |
| PyMOL object coords/representations | PyMOL session | (never read back as truth; `get_coordset` only at spectra handoff) |

---

## 5. Suggested Build Order (dependency-driven)

Ordered so that every phase's deliverable is testable with the tools available at that point (WSL tests → headless smokes → human verify).

```
Phase A: Skeleton + entry + purity harness
  __init__.py entry, gui.py empty 3-tab modeless dialog, repo layout,
  tests/ scaffold + purity grep gates (F22/F23, adapted AA-match pattern)
  └─ no dependencies; immediately installable via plugin path (F5) → human-verify #1

Phase B: Pure core (no PyMOL needed)
  setup_logic, game_engine, stacking, cgo_build, molecule_data (manifest schema),
  xyzio, spectra (parser+broadening), xtbenv — ALL with WSL python3.6 unittests
  └─ depends on: nothing (stdlib only). spectra parser can be written against the
     REAL g98.out/vibspectrum captured in tmp/xtb_ohess_test (F20/F21)
  └─ NOTE: demo-set *data acquisition + user approval of sources* should start here
     in parallel (external dependency, lead time)

Phase C: Molecules in the viewer
  pymol_bridge subset: load mol2/sdf, srp_* copies, box CGO, camera
  + smoke/*.py headless runs (F23 pattern)
  └─ depends on: A (package), B (engine types, cgo_build)

Phase D: Game loop + input
  input.py (set_key left/right; UP/DOWN SPIKE + event-filter fallback — F13),
  tick QTimer in controller, translate movement, countdown, pause/restart
  └─ depends on: B, C. First human-verify of keys is HERE (fail early)

Phase E: Stacking + game rules complete
  stacking transforms applied via transform_selection, pickup/collision/score/cap,
  win+crash completion flow, cleanup-by-prefix
  └─ depends on: D. This is the playable v1 core

Phase F: xtb pipeline
  xtb_runner (worker/queue/drain), atom-budget guard, end-to-end headless run:
  snake.xyz → real xtb.exe --ohess → files (tmp/xtb_runs/, git-ignored)
  └─ depends on: B (xyzio/xtbenv/spectra parser) — can be built in PARALLEL with D/E
     since only the final-snake handoff touches gameplay

Phase G: Spectra UI
  gui_spectra wiring, plot_widget, frequency table + mode-arrow CGO display, save plot
  └─ depends on: E (final snake), F (runner). Pure parts already tested in B.

Phase H: Demo sets + polish
  data/demos + SOURCES.md (approved citations), Save/Load Setup persistence,
  Randomize, help text, README
  └─ depends on: B (manifest schema), user-approved sources from Phase B track
```

**Critical-path insight:** Phases B and F are PyMOL-free and can proceed (and be fully tested) before any GUI work lands; the xtb-flag discovery (F19: `--ohess`, not `-o --hess`) means the F pipeline is de-risked *now*.

---

## 6. Testability Split

| Layer | Modules | How tested | Runs where |
|-------|---------|------------|------------|
| Pure logic | `game_engine, stacking, cgo_build, spectra, xyzio, xtbenv, setup_logic, molecule_data` | `python3.6 -m unittest tests.test_*` — stdlib-only imports, no stubs needed (if the AA-match lazy-import discipline is kept; bioCHEMeleon needed MagicMock stubs only because it imports Qt at module level, F23) | WSL |
| Subprocess logic | `xtb_runner` (worker/queue/timeout/cancel) | unittest with a **stub executable** (e.g., a tiny python script posing as xtb emitting fake log lines) | WSL |
| cmd side effects | `pymol_bridge`, `input.py` set_key half, controller cmd paths | headless smokes: stage package + script to a Windows-visible path, `timeout 90 cmd.exe /c "C:\src\run-conda-pymol.bat -cq smoke\NN_smoke.py"` (bioCHEMeleon pattern, F23) | Windows headless via WSL |
| Full spectra chain | bridge → xyz → real `xtb.exe --ohess` → parser | headless smoke on a small molecule set (proven today on phenol: seconds, not minutes) | Windows xtb from WSL |
| Qt visuals | `gui*.py`, `plot_widget.py`, dialog behavior, tab switching, plot save | human-verify checkpoints (cannot run Qt headlessly — established in bioCHEMeleon) | human in Windows PyMOL |
| Key bindings | `input.py` | headless: binding/unbinding/restore logic; human-verify: actual arrow behavior + focus (F13 risk) | both |

**Purity gate (adaptation of the AA-match pattern, as documented in serpentrum's PROJECT/AGENTS context):**
- Pure modules: stdlib-only **at module level** — no `pymol`, no Qt, no numpy (F22 makes the numpy ban non-negotiable for WSL testability). Where numpy would be habitual (broadening, small vector ops), use `math`; at serpentrum scale (≤ ~600 modes × ~1-2k grid points, ≤ ~200 atoms) stdlib performance is ample. numpy remains available on the Windows side if ever genuinely needed (lazy import inside a function).
- Enforced by CI-style grep gates in tests (bioCHEMeleon precedent): `grep -rnE "from pymol|import pymol|from PyQt5|import numpy" serpentrum/{pure modules}` must return zero; plus a gate that `__init__.py` imports only stdlib at module level.
- Dependency direction (`pure ← bridge ← gui/controller`) enforced by the same greps, mirroring bioCHEMeleon's architecture rule.

---

## 7. Anti-Patterns (domain-specific)

### Anti-Pattern 1: Mutating user molecules in place (bioCHEMeleon's game model)
**What people do:** Insert/modify atoms inside the user's loaded object (bioCHEMeleon hides hiders inside the target object).
**Why it's wrong here:** PyMOL has no undo (F17); serpentrum's lifecycle (game → spectra on the assembled snake) needs clean provenance and cheap cleanup.
**Do this instead:** Pattern 4 — `cmd.create` copies into a `srp_*` namespace; user objects never touched; cleanup = delete by prefix.

### Anti-Pattern 2: Blocking the Qt event loop
**What people do:** `subprocess.run(xtb...)` or `QDialog.exec_()` on the main plugin dialog during a long calculation.
**Why it's wrong:** Freezes the dialog AND PyMOL's viewer (one shared event loop); modal dialogs stop the 3D interaction loop that the game depends on.
**Do this instead:** Modeless dialog (`.show()`, F6) + Pattern 2 worker/drain. Only *child* dialogs (file pickers, confirms) may be modal — bioCHEMeleon's documented exception.

### Anti-Pattern 3: `cmd.*` calls from worker threads
**What people do:** Run xtb in a thread and call `cmd.load` on the result from that thread.
**Why it's wrong:** The Python cmd API is not thread-safe against the C layer; bioCHEMeleon's verified pattern explicitly forbids it (F10).
**Do this instead:** Worker pushes events to a queue; drain on main thread does all cmd work.

### Anti-Pattern 4: Treating PyMOL object coordinates as game truth
**What people do:** Read back atom coordinates each tick to decide collisions.
**Why it's wrong:** Round-trips through the C layer, float drift, representation-state coupling; untestable off-PyMOL.
**Do this instead:** Pattern 3 — engine owns grid truth; bridge writes coords; `get_coordset` read-back only once at the spectra handoff.

### Anti-Pattern 5: Parsing the `hessian` file / implementing eigendecomposition
**What people do:** Parse the Turbomole Hessian, mass-weight, diagonalize to get modes.
**Why it's wrong:** Massive unnecessary complexity + needs numpy/eigensolver; xtb already emits normal coordinates in `g98.out` (F21).
**Do this instead:** Parse `g98.out` (freq + inten + per-atom XYZ vectors in one file); keep `vibspectrum` as a freq/inten fallback.

### Anti-Pattern 6: `import matplotlib` for the spectrum plot
**What people do:** Reach for matplotlib like vina.py does.
**Why it's wrong:** Outside the "only what pymol-open-source ships" dependency constraint unless user-approved + vendored (vina.py makes users install it, F25).
**Do this instead:** QPainter widget (dynoplot.py precedent, F24) — broadened IR is just a filled polyline + axes + labels.

### Anti-Pattern 7: Assuming `-o --hess` gives frequencies
**What people do:** Copy the proven-looking `test_wsl_winxtb.sh` invocation.
**Why it's wrong:** Empirically verified today: that flag pair runs the optimizer (its ANC Hessian is internal) and writes NO vibrational files (F19).
**Do this instead:** `--ohess` for optimize+Hessian; assert the presence of `g98.out`/`vibspectrum` after the run; fail loudly with the log tail if absent.

---

## 8. Integration Points

### xtb (external binary)

| Aspect | Decision | Basis |
|--------|----------|-------|
| Invocation | `xtb.exe snake.xyz --ohess` (Windows) / `xtb snake.xyz --ohess` (Linux) — detection by `sys.platform` | F19 + PROJECT.md requirement |
| cwd | A fresh run dir under git-ignored `tmp/xtb_runs/<id>/`, on `/mnt/c` so the Windows exe + cmd.exe path mapping work (proven by `test_wsl_winxtb.sh`) | F19, spec |
| Path conversion | `/mnt/c/...` → `C:/...` for any absolute path handed to the exe or used in argv (bioCHEMeleon `to_windows_path` precedent); relative paths + correct cwd avoid most of it | bioCHEMeleon AGENTS |
| Env | Honor user-configured xtb path + optional env setup from Setup tab; default auto-detect (`xtbenv` pure logic, WSL-testable) | PROJECT.md |
| Version | 6.7.1pre Windows build is the local proven one (6.7.0 Windows build broken per PROJECT context) — log the version banner line for traceability | xtb log header, verified |
| Timeout + cancel | Worker tracks process handle; cancel event → `proc.kill()`; drain reports 'canceled' | Pattern 2 |
| Cost guard | Hessian ≈ N³ — atom budget check (user cap ~10 molecules/~100 atoms default) blocks or warns before spawn | PROJECT.md decision |

### Qt ↔ PyMOL boundary

| Boundary | Communication | Notes |
|----------|---------------|-------|
| Dialog ↔ viewer interactivity | modeless dialog only | F6; modal only for child confirms/pickers |
| Keys | `cmd.set_key` (viewer focus) with Qt event-filter fallback | F11-F13 |
| Progress | queue → QTimer drain → log panel | F10 |
| Scene objects | `cmd.load_cgo`, `cmd.create`, `cmd.translate`, `cmd.transform_selection`, `cmd.zoom/origin` | F14-F16 |

---

## 9. Open Questions / Flagged Items (carry into roadmap)

| Item | Confidence | Needed action |
|------|------------|---------------|
| `cmd.set_key('up'/'down', ...)` redefinability — docstring omits them, shortcut manager reserves them (F13) | LOW | **Phase D spike + human verify**; fallback = Qt app-level event filter (also fixes dialog-focus case) |
| Do arrow keys reach PyMOL when the plugin dialog (not viewer) has focus? | LOW | Human verify in Phase D; event-filter fallback likely solves it; consider documenting "click the viewer to steer" |
| `transform_selection` matrix argument convention (row/col-major, 4x4 layout) — existence verified (F14), argument layout not read in detail | LOW | Read `editing.py:1946` docstring during Phase E implementation; alternatively decompose into `cmd.rotate`+`cmd.translate` (both verified concepts) |
| Plot-to-PNG save (`QWidget.grab()` → `QPixmap.save`) — standard Qt but unverified inside PyMOL's Qt build | MEDIUM | Human verify in Phase G; fallback `cmd.png` is irrelevant (it photographs the viewer) — worst case render widget via QPainter into QImage |
| Whether matplotlib happens to exist in the local conda env | LOW (and deliberately irrelevant) | QPainter chosen so the answer doesn't matter; if user later approves matplotlib, plot_widget can be swapped behind its interface |
| Long-snake xtb runtime (Hessian ~N³) — behavior beyond phenol-scale unverified | MEDIUM | Phase F smoke with the default-cap snake (~100 atoms) to calibrate the timeout + budget warnings |
| AA-match purity-gate details (user deferred direct inspection: "no need for aa-match") | MEDIUM | Gate adapted from the documented description (stdlib-only pure modules, lazy imports, grep enforcement) + bioCHEMeleon's proven test patterns; **reminder logged for user: revisit AGENTS.md/spec.md AA-match references later** |

---

## Sources

- **PyMOL 2.5.0 source (verified today, file:line):** `pymol-src/modules/pymol/plugins/__init__.py` (entry/load/menu), `installation.py` (startup dirs), `legacysupport.py` (pmg_tk legacy), `controlling.py` (set_key + redefinable keys), `internal.py` (special key codes), `editing.py` / `querying.py` / `viewing.py` (movement + camera APIs), `pymol/cgo.py` (CGO constants), `pymol/wizard/box.py` (box CGO prior art), `pymol/wizard/filter.py` + `density.py` (key binding precedents), `pmg_qt/pymol_qt_gui.py` + `pmg_qt/keymapping.py` (Qt key path), `chempy/mol2.py` + `chempy/sdf.py` (formats)
- **Plugin corpora:** `Pymol-script-repo/plugins/optimize.py`, `outline.py`, `vina.py`, `dynoplot.py`; `tmp/bioCHEMeleon/biochemeleon/__init__.py`, `gui_game.py`, `wizard.py`, `AGENTS.md`, `tests/test_setup_state.py`
- **Empirical xtb runs (today, 2026-09-06):** `tmp/xtb_test/` (`-o --hess` → no vibrational output) vs `tmp/xtb_ohess_test/` (`--ohess` → `hessian`, `vibspectrum`, `g98.out`); `test_wsl_winxtb.sh` (WSL→Windows invocation pattern)
- **Environment (verified today):** WSL python3.6.9 present, **numpy absent**, stdlib OK
- **AA-match pattern:** adapted from its description in serpentrum `.planning/PROJECT.md` + root `AGENTS.md` (repo not read directly, per user instruction)

---
*Architecture research for: serpentrum — PyMOL-plugin educational snake game with xtb IR spectra*
*Researched: 2026-09-06*
