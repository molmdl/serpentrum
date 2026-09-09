# Phase 3 (Setup Tab UI half) — Research

**Researched:** 2026-09-10
**Domain:** PyQt5 (via `pymol.Qt`) dialog widgets + Qt↔PyMOL `cmd` boundary + purity-gate module decomposition
**Confidence:** HIGH for Qt/widget/file-dialog/thread-boundary claims (verified against `tmp/bioCHEMeleon` shipped v1 plugin + repo research docs with `[SRC]` pointers); MEDIUM for the purity-class extension recommendation (inference from the current checker + documented architecture — a deliberate human decision); LOW for the demo-set data availability (open question, human-gated).

This research covers the **Setup-tab UI half** of Phase 3 only. The **loader/bridge-behavior half** (manifest loading, ring-count gate mechanics, `cmd.load`/`cmd.load_cgo` smoke proofs) is a separate research track; this doc states the **handoff contract** the UI needs from it but does not specify the loader's internals.

---

## Summary

The Setup tab is a `QWidget` form (QComboBox/QSpinBox/QLineEdit/QCheckBox + a status QLabel + two temporary action buttons) that edits a live `setup_logic` setup dict and, on Apply, hands it to a **new `pymol_bridge.py` cmd-seam module** that calls `cmd.load`/`cmd.load_cgo`/`cmd.delete` directly on the Qt main thread. The single most important architectural finding is that **serpentrum's purity checker currently has NO class that permits `from pymol import cmd`**: `gui.py` (GUI class) allows only `pymol.Qt`; everything else defaults PURE (bans pymol anywhere). bioCHEMeleon's shipped plugin sidesteps this by importing `cmd` directly inside its GUI modules (`tmp/bioCHEMeleon/biochemeleon/gui_setup.py:18`), but serpentrum's stricter AST gate forbids that. Phase 3 therefore must **extend `tools/check_purity.py` with a new "BRIDGE" module class** (an allowlist parallel to `GUI_MODULES`) and create `serpentrum/pymol_bridge.py` — this is the first phase that touches `cmd.*`, and the documented architecture (`ARCHITECTURE.md` §2) already reserves `pymol_bridge.py` as "The ONLY module (besides controller/input) importing `pymol.cmd`".

The Qt↔PyMOL thread-boundary answer is settled and simple for Phase 3: **button-click handlers run on the Qt main thread, which IS the PyMOL gui thread, so `cmd.*` may be called directly from handlers** — this is the verified bioCHEMeleon pattern (`__init__.py:839` `cmd.load(pse_path, partial=1)` inside `_on_load`; `gui_setup.py:631` `cmd.count_atoms(obj)` inside `_randomize`). The worker/queue/`QTimer.singleShot` drain pattern (`ARCHITECTURE.md` Pattern 2; bioCHEMeleon `_resolve_large_demo` `__init__.py:545-677`) is reserved for **long** operations (Phase 6 xtb subprocess, network fetches); Phase 3's operations (load a few small SDFs, one box CGO, one head, delete `srp_*`) are sub-second and need no worker. The hard rule (Pitfall 6) — never call `cmd.*` from a `threading.Thread`/`QThread` — is respected trivially because Phase 3 spawns no threads.

**Primary recommendation:** Add `serpentrum/gui_setup.py` (a `SetupTab(QWidget)`) to `GUI_MODULES`, add a new `BRIDGE_MODULES = {'serpentrum/pymol_bridge.py'}` class to `check_purity.py` (allows `pymol`/`pmg_tk`, bans `PyQt5`/`numpy`), wire the Setup page in `gui.py` to host the `SetupTab`, surface errors via `QMessageBox.warning` (static, no `.exec_()` token) and the hessian warning via an inline `QLabel`, anchor the live setup dict on `pmg_tk.startup._serpentrum` for reload survival, and ship two **temporary** Setup-page buttons (Apply/Show-in-Viewer + Cleanup) — the canonical 6-button row (SETUP-07) and save/load (SETUP-08) stay in Phase 8.

---

## 1. Verified Qt / PyMOL Behaviors (each with source pointers)

### 1.1 Qt imports must go through `pymol.Qt`, never `PyQt5` (HARD RULE, HIGH confidence)

`pymol/Qt/__init__.py:26-40` tries PyQt5 first, falls back to PySide2 — so `from pymol.Qt import QtWidgets, QtCore, QtGui` is the only portable form `[SRC: STACK.md §Core table; ARCHITECTURE.md F7]`. `from PyQt5 import ...` is banned project-wide and is a purity-gate violation in every module class (`tools/check_purity.py:60` `BANNED_ROOTS = ('pymol','pmg_tk','PyQt5','numpy')`; the GUI allowance grants `pymol.Qt` only — `_is_qt_form` at `check_purity.py:81-90`).

### 1.2 The main dialog is modeless; child modals are allowed (HIGH confidence)

`PluginDialog` is shown via `.show()` only — `.exec_()` on the main dialog is a purity-gate violation in every class (`check_purity.py:162-169` flags any `ast.Call` whose `func.attr == 'exec_'`). **However**, `QMessageBox.warning(...)` and `QFileDialog.getOpenFileName(...)` / `getSaveFileName(...)` are **static convenience methods** that perform their own internal modal exec **without the user code containing an `.exec_()` token**. Verified in bioCHEMeleon (`__init__.py:694,758,804,839` and `gui_setup.py:362,456,484,646,665,674` all use the static forms; `grep -n "\.exec_(" gui_setup.py` shows **zero** matches in that file). `[SRC: tmp/bioCHEMeleon/biochemeleon/gui_setup.py, __init__.py]`.

**Consequence for Phase 3:** the Setup tab can use `QtWidgets.QMessageBox.warning(self, title, msg)` and `QtWidgets.QFileDialog.getOpenFileName(self, ...)` for error surfacing and file picking **without** needing the per-module `.exec_()` allowlist that the checker comment (`check_purity.py:33-34`) anticipates for "later phases." If Phase 3 ever constructs a *custom* child `QDialog` and calls `.exec_()` on it, THEN the allowlist must be added — but the static methods make that unnecessary for Setup. `[SRC: check_purity.py:162-169; PITFALLS.md Pitfall 5]`.

### 1.3 Modal errors are acceptable in the Setup tab (pre-game), forbidden during play (HIGH confidence)

`PITFALLS.md` Pitfall 5: "Child modals (QMessageBox/QFileDialog/QColorDialog on children) are allowed — but never during active gameplay without pause." `STACK.md` §1: "QMessageBox only on child dialogs (modal OK for those; **forbidden during gameplay** — verified: modal dialogs block the Qt event loop and freeze the viewer)." INFRA-05's "no modal dialogs during play" binds the **Game tab during active play** (a tick timer is running). The Setup tab has no running timer — a modal error box there does not freeze gameplay. `[SRC: PITFALLS.md Pitfall 5; STACK.md §1; REQUIREMENTS.md INFRA-05]`.

### 1.4 `cmd.*` may be called directly from Qt main-thread handlers (HIGH confidence — the thread-boundary answer)

bioCHEMeleon's shipped v1 calls `cmd.*` directly inside Qt button handlers that run on the main thread:
- `cmd.load(pse_path, partial=1)` inside `_on_load` (`__init__.py:839`)
- `cmd.count_atoms(obj)` inside `gui_setup.py:_randomize` (`gui_setup.py:631`)
- `cmd.save(pse_path, target_obj)` inside `_on_save` (`__init__.py:770`)

These handlers are invoked by Qt signal/slot dispatch on the **Qt main thread**, which is the **same thread PyMOL's `cmd` API is safe on** (`cmd.is_gui_thread()` returns True; `[SRC: pymol-src/modules/pymol/locking.py:26-88` per `PITFALLS.md` Pitfall 6`). bioCHEMeleon even does `from pymol import cmd` lazily inside `_on_save` (`__init__.py:751`) — a function-body import — for the same reason serpentrum's ENTRY module does.

**The worker/queue/`QTimer.singleShot(100, drain)` pattern is NOT needed for sub-second operations.** It exists exclusively for long work: bioCHEMeleon uses it ONLY for the large-demo network fetch (`_resolve_large_demo`, `__init__.py:545-677`: stdlib-only worker → `queue.Queue` → recursive `QTimer.singleShot(100, drain)` → `cmd.*` only in the drain branch). Phase 3's loads (a few small SDFs, one CGO box, one head sphere/molecule, `delete srp_*`) are all sub-second local operations — direct `cmd.*` in the handler is the verified norm. `[SRC: ARCHITECTURE.md Pattern 2 + F10; PITFALLS.md Pitfall 6; bioCHEMeleon __init__.py:545-677]`.

### 1.5 `QFileDialog` static methods return a `(path, filter)` tuple; native on Windows (HIGH confidence)

`QtWidgets.QFileDialog.getOpenFileName(self, caption, dir, filter)` returns `(path, selectedFilter)`; `getOpenFileName`/`getSaveFileName` use the native Windows dialog by default. Verified usage: `path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save ...", "", "Setup (*.json);;All Files (*)")` (`bioCHEMeleon/__init__.py:694,758`; `gui_setup.py:646,665`). The `self` parent keeps the dialog above the plugin window. Multi-select uses `getOpenFileNames` (returns list). `[SRC: bioCHEMeleon gui_setup.py:646,665; __init__.py:694,758,804]`.

### 1.6 Runtime paths are Windows paths — the plugin NEVER converts them (HIGH confidence)

The plugin runs inside Windows PyMOL; `QFileDialog` returns Windows paths (`C:\Users\...`). `cmd.load` understands them natively. The `tools/winpath.py` helper is **DEV-SIDE ONLY** (decision 01-05: strict `ValueError` on non-`/mnt` paths, never mangles; the plugin runtime never converts paths). So the upload path from `QFileDialog` flows **unchanged** to the loader/bridge. `[SRC: STATE.md decisions 01-05; STACK.md "What NOT to Use" WSL-paths row; AGENTS.md]`.

### 1.7 `collect_state()` / `apply_state()` round-trip is the established Setup-tab pattern (HIGH confidence)

bioCHEMeleon `gui_setup.py` `SetupTab` exposes `collect_state()` (`:539`) → JSON-serializable dict, and `apply_state(state)` (`:559`) → repopulates widgets. A `self._loading` flag (`:77`) guards `apply_state` against cascading widget-signal recompute. `__init__` calls `apply_state(DEFAULTS)` on construction (`:80`). serpentrum's `setup_logic.new_setup()` / `validate()` / `DEFAULTS` are the pure-layer analogues. `[SRC: bioCHEMeleon gui_setup.py:75-80,539-617; serpentrum/setup_logic.py:48-58,83-90]`.

### 1.8 The `self.tabs` handle + fixed page order + one `addTab` per page is the registration contract (HIGH confidence)

`gui.py:46-55` builds the 3 placeholder pages in a loop with one `self.tabs.addTab(page, label)` per `_TAB_DEFS` entry; `self.tabs` (QTabWidget) is the documented switching handle (`setCurrentWidget`/`setCurrentIndex`); page order is fixed Setup→Game→Spectra. bioCHEMeleon switches tabs via `self.tabs.setCurrentWidget(self.game_tab)` (`__init__.py:260`). Phase 3 must preserve: (a) `self.tabs` remains the handle, (b) Setup stays page 0, (c) exactly one `addTab` registers the Setup page. `[SRC: serpentrum/gui.py:42-60; 01-02-SUMMARY.md key-decisions; bioCHEMeleon __init__.py:260]`.

### 1.9 py3.6 syntax constraint + `QtCore.Signal` (not `pyqtSignal`) (HIGH confidence)

Runtime is Python 3.6 (PyMOL 2.5 conda); f-strings OK, but no 3.7+ syntax (no dataclasses, walrus, f-string `=`). Repo precedent uses %-formatting (`setup_logic.py`, `xtbenv.py` throughout) — follow it. `pymol.Qt` normalizes Signal/Slot (`pymol/Qt/__init__.py:84-94` per STACK.md): use `QtCore.Signal(...)` / `@QtCore.Slot()` (portable across PyQt5/PySide2), never `pyqtSignal`. **Phase 3 needs NO custom signals** — the Setup tab calls bridge functions directly on button click; cross-tab signals arrive with the Game tab (Phase 4+). `[SRC: STACK.md Version Compatibility table; setup_logic.py docstring "python3.6 syntax only"]`.

---

## 2. Widget Inventory + Layout Recommendation

All widgets live in `QtWidgets` (imported via `from pymol.Qt import QtWidgets`). Every control below is a standard PyQt5 widget verified in bioCHEMeleon's `gui_setup.py` (`QComboBox`, `QSpinBox`, `QLineEdit`, `QCheckBox`, `QLabel`, `QPushButton`, `QGroupBox`, `QFormLayout` are all used there).

### 2.1 Widget inventory (one row per Setup control)

| Control (SC) | Widget class | Idioms / py3.6 notes | Source precedent |
|---|---|---|---|
| Demo-set dropdown (SC1, SETUP-02) | `QComboBox` | `addItem(label, userData=setId)`; read `currentData()`. Populate from `setup_logic.KNOWN_SETS` (`('set_a',)`). Add an "Upload…" entry whose `currentData()` is e.g. `None`/`'__upload__'` to flip to the upload row. | `gui_setup.py:89-92` mode_combo pattern |
| Upload file picker (SC1, SETUP-02, DATA-03) | `QPushButton` ("Browse…") + `QLineEdit` (read-only path display), revealed when dropdown = Upload | `path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Choose molecule set", "", "Molecules (*.sdf *.mol2);;All Files (*)")`. **One multi-record SDF is the upload unit** (SDF carries multiple `$$$$`-delimited records); directory-upload is a Phase 8 enhancement. Path displayed unchanged (Windows path — see 1.6). | `gui_setup.py:665` getOpenFileName |
| Box-size dropdown (SC2, SETUP-03) | `QComboBox` | Populate from `setup_logic.BOX_PRESETS.keys()` (`small`/`medium`/`large`); default `medium` (`DEFAULTS['box_preset']`). | `gui_setup.py:89-92` |
| Head-molecule dropdown (SC2, SETUP-04) | `QComboBox` | Default entry "Random" (`userData='random'`, matching `DEFAULTS['head_molecule']`). Remaining entries = candidate molecule ids **handed up by the loader half** after a set is loaded (see §6 handoff). Re-populate on set change. | `gui_setup.py:89-92`; `setup_logic.py:50` |
| xtb path field + auto-detect checkbox (SC3, SETUP-05) | `QLineEdit` + `QCheckBox` ("auto-detect") + optional `QPushButton` ("Browse…") | When checkbox checked → field disabled, `setup['xtb_path']=None` (auto-detect via `xtbenv.detect_binary()`). When unchecked → field enabled; Browse opens `QFileDialog.getOpenFileName` for the exe. Manual path overrides detection (`xtbenv.detect_binary(configured_path=...)` validates first, falls through to auto on invalid — `xtbenv.py:141-167`). | `xtbenv.py:141-167`; `setup_logic.py:53,100-127` |
| Win-cap spinbox + warning label (SC4, SETUP-06) | `QSpinBox` (range 1..20 per `validate`) + `QLabel` (hidden by default) | `setRange(1, 20)`; default 10 (`DEFAULTS['win_cap_molecules']`). On `valueChanged`, if value > 10 → show `QLabel` with `setup_logic.HESSIAN_WARNING` text (`'hessian cost scales ~N^3; a ~100-atom snake may take 30-90 s'`); else hide. Inline advisory label, NOT a modal. | `setup_logic.py:54,73-74,200-204`; `PITFALLS.md` perf table |
| Status / error label (persistent) | `QLabel` (word-wrapped) at form bottom | Shows inline validation status from `setup_logic.validate(setup)` (errors joined; warnings = hessian line). Updated on Apply and on field change (debounced). Complements the one-shot modal `QMessageBox` for blocking errors. | `gui.py:50-51` QLabel pattern |
| Apply / Show-in-Viewer button (Phase 3 temporary) | `QPushButton` | Runs `validate()` → on errors, `QMessageBox.warning` + status label; on success, calls `pymol_bridge.materialize(setup)` (cleanup `srp_*` first, then load box + head). NOT one of the 6 Phase-8 buttons. | §5 control split |
| Cleanup button (Phase 3 temporary, SC5) | `QPushButton` | Calls `pymol_bridge.cleanup_srp()` → `cmd.delete('srp_*')`. Tests INFRA-04 semantics in Phase 3. Replaced by the canonical "Cleanup model" button in Phase 8. | §5 control split |

### 2.2 Layout recommendation

Mirror bioCHEMeleon's `SetupTab` structure (`gui_setup.py:83-88`): a top-level `QVBoxLayout(self)` holding a sequence of `QGroupBox` sections, each with a `QFormLayout`:

```
SetupTab(QWidget)
└── QVBoxLayout
    ├── QGroupBox "Molecule set"     (QFormLayout: demo-set combo; upload row [Browse + pathLineEdit])
    ├── QGroupBox "Box"              (QFormLayout: box-preset combo)
    ├── QGroupBox "Head molecule"    (QFormLayout: head combo, default Random)
    ├── QGroupBox "xtb"              (QFormLayout: auto-detect checkbox; path line-edit + Browse)
    ├── QGroupBox "Win cap"          (QFormLayout: spinbox; hessian warning QLabel below)
    ├── status QLabel (word-wrapped)   ← inline errors/warnings
    ├── stretch
    └── QHBoxLayout [Apply/Show] [Cleanup]   ← TEMPORARY Phase-3 buttons (NOT the reserved bottom row)
```

The reserved bottom `QHBoxLayout` in `gui.py:56-57` (Phase 8's 6 right-aligned buttons) is **untouched** by Phase 3 — the temporary buttons live inside the Setup page itself, above the reserved row.

---

## 3. The Qt↔PyMOL Thread Boundary Answer

**Question:** Can dialog handlers call `cmd.load`/`cmd.delete` directly, or must they marshal onto PyMOL's thread?

**Answer (HIGH confidence): call directly.** A Qt button-click handler is dispatched by the Qt event loop on the **Qt main thread**. In PyMOL's Qt build, the Qt main thread **is** the PyMOL gui thread (`cmd.is_gui_thread()` returns True on it; `[SRC: locking.py:80` per Pitfall 6). The `cmd` Python API is safe to call from the gui thread. This is the verified bioCHEMeleon pattern: handlers call `cmd.load`, `cmd.count_atoms`, `cmd.save` directly (`__init__.py:839,770`; `gui_setup.py:631`).

**Why no marshalling/queue is needed for Phase 3:** the worker→queue→`QTimer.singleShot(100, drain)` pattern (`ARCHITECTURE.md` Pattern 2; bioCHEMeleon `_resolve_large_demo` `__init__.py:545-677`) exists to keep the Qt event loop pumping during **multi-second** work (network fetch; Phase 6 xtb hessian = 30–90 s at 100 atoms per `PITFALLS.md` Pitfall 2). Phase 3's operations are sub-second local file/CGO loads — the brief handler-blocking is the same class bioCHEMeleon accepts for `cmd.fetch`/`cmd.load` in `_prepare_and_start` (`__init__.py:311,322`). The viewer redraws via `cmd.refresh()` after the loads (the verified pre-UI-refresh pattern, `STACK.md` F9 / bioCHEMeleon `gui_game.py:302-304`); call it once at the end of Apply so the box+head appear.

**The one hard rule (Pitfall 6, INFRA-05): never call `cmd.*` from a `threading.Thread`/`QThread`.** Phase 3 spawns **no threads**, so this is trivially satisfied. If a future Phase-3 need ever requires async work (e.g. parsing a huge upload — not in scope), the rule is: worker touches **only stdlib** (parse to pure data), pushes to a `queue.Queue`, and a recursive `QTimer.singleShot` drain on the main thread performs the `cmd.*` — never the reverse. `[SRC: PITFALLS.md Pitfalls 2, 6; ARCHITECTURE.md Pattern 2 + F10; bioCHEMeleon __init__.py:545-677]`.

**QProcess (Phase 6, NOT Phase 3):** the `QProcess.finished(int, ExitStatus)` signal also lands on the Qt main thread, so its slot may call `cmd.*` — but this is the xtb pipeline's concern, not Setup's. `[SRC: STACK.md §5; PITFALLS.md Pitfall 2]`.

---

## 4. Error / Warning Surfacing Design

Two distinct surfaces, matching the research:

### 4.1 Blocking errors → `QMessageBox.warning` (one-shot modal, pre-game OK)

Use for **one-shot rejection events** where the user must acknowledge before proceeding:
- **Upload rejected (SC1, DATA-03):** a molecule exceeds the ≤3-ring gate → `QtWidgets.QMessageBox.warning(self, "Upload rejected", "<molecule>: <reason>\n\nSets are limited to 3 rings.")`. The "clear reason" requirement (SC1) is satisfied by naming the offending molecule + the rule.
- **Invalid setup on Apply:** `setup_logic.validate(setup)` returns errors → `QMessageBox.warning(self, "Cannot apply", "\n".join(errors))`.
- **Load failure:** bridge `cmd.load` raises → `QMessageBox.warning(self, "Load failed", "<detail>")`.

`QMessageBox.warning` is a **static** method — no `.exec_()` token in source, so the AST purity gate (`check_purity.py:162-169`) does not fire (see §1.2). Parent on `self` (the SetupTab or dialog) so it stays above the plugin window. Pre-game modals are permitted (§1.3); only Game-tab-during-play modals are forbidden. `[SRC: bioCHEMeleon gui_setup.py:362,456,484,657,674; PITFALLS.md Pitfall 5; STACK.md §1]`.

### 4.2 Advisory warnings → inline `QLabel` (persistent, non-modal)

Use for **state-dependent persistent** advisories:
- **Hessian-cost warning (SC4, SETUP-06):** a `QLabel` (hidden by default) below the win-cap spinbox. On `spinbox.valueChanged` (and on `apply_state`): if `win_cap_molecules > 10` OR `atom_budget > 100` → show `setup_logic.HESSIAN_WARNING`; else hide. This mirrors `validate()`'s warning logic (`setup_logic.py:201-204`) exactly. Inline (not modal) because it is advisory — the user may legitimately raise the cap and proceed.
- **Live validation status:** a status `QLabel` at the form bottom showing the current `validate(setup)` verdict (errors + warnings joined), updated on field change (debounced) and on Apply. Gives continuous feedback without modal interruption.

`[SRC: setup_logic.py:73-74,130-206; PITFALLS.md perf table; bioCHEMeleon gui_setup.py:50-51 QLabel pattern]`.

### 4.3 What NOT to do

- Do **not** pop a `QMessageBox` for the hessian warning on every spinbox change — it is advisory and persistent; a modal on each keystroke violates the "no modal dialogs during play" spirit and is hostile UX.
- Do **not** rely solely on the inline label for hard upload rejection — SC1 demands a "clear reason" that the user acknowledges; a modal guarantees visibility.
- Do **not** write `dialog.exec_()` anywhere (main dialog stays modeless); use the static `QMessageBox`/`QFileDialog` forms so no `.exec_()` token enters source.

---

## 5. Module Decomposition — The Allowlist Decision (HUMAN DECISION)

### 5.1 The core finding: no current purity class permits `from pymol import cmd`

`tools/check_purity.py` defines three classes (`classify`, `:66-72`):
- **ENTRY** (`serpentrum/__init__.py`): allows `pymol`/`pmg_tk` **only lazily inside function bodies** (module-level pymol import = violation; `:113-119`).
- **GUI** (`GUI_MODULES = {'serpentrum/gui.py'}`, `:55`): allows **only `pymol.Qt`/`pymol.Qt.*`**; any other `pymol`/`pmg_tk` anywhere (module level OR bodies) is a violation (`:124-131`). So `from pymol import cmd` in a GUI module = violation.
- **PURE** (everything else under `serpentrum/`): bans `pymol`/`pmg_tk`/`PyQt5`/`numpy` **anywhere** (`:135-138`).

bioCHEMeleon sidesteps this by importing `cmd` directly in GUI modules (`gui_setup.py:18` module-level `from pymol import cmd`; `__init__.py:751` lazy). **serpentrum's stricter gate forbids both.** Phase 3 is the first phase that must call `cmd.*` (load molecules, load_cgo box, delete `srp_*`). There is currently nowhere legal to put those calls.

### 5.2 Recommendation (MEDIUM confidence — deliberate human decision): add a BRIDGE class + `pymol_bridge.py`

Extend `check_purity.py` with a third allowlist, parallel to `GUI_MODULES`:

```python
# Explicit cmd-bridge allowlist — the ONLY modules (besides ENTRY-lazy) that
# may import pymol.cmd. Allows pymol/pmg_tk at module level AND in bodies;
# bans PyQt5/numpy everywhere (Qt stays in GUI modules; numpy never needed
# in the bridge — pure modules do the math).
BRIDGE_MODULES = {'serpentrum/pymol_bridge.py'}
```

Classification rule addition: a path in `BRIDGE_MODULES` → class `BRIDGE` → allow `pymol`/`pmg_tk` roots (any level); ban `PyQt5`/`numpy` (any level). Then create `serpentrum/pymol_bridge.py` — the single cmd-seam module the documented architecture reserves (`ARCHITECTURE.md` §2: "pymol_bridge.py — The ONLY module (besides controller/input) importing pymol.cmd"). `[SRC: tools/check_purity.py:55,60,66-138; ARCHITECTURE.md §2 component table + structure rationale]`.

**Phase 3 bridge surface (minimal):** `load_demo_set(manifest_path)` / `load_upload(path)` → returns (loaded_names, errors); `load_box(preset)` → `cmd.load_cgo(cgo_build.box_cgo(...), 'srp_box', zoom=0)`; `place_head(molecule_id_or_random, candidates)` → loads/shows head; `cleanup_srp()` → `cmd.delete('srp_*')`; `refresh()` → `cmd.refresh()`. Pure builders (`cgo_build.box_cgo`, `spheres_cgo`) feed `cmd.load_cgo` — the bridge imports `pymol.cmd` + the pure `cgo_build`/`setup_logic`/`molecule_data` via relative imports (always exempt, `check_purity.py:75-78`).

### 5.3 The GUI-module decision: add `gui_setup.py` to `GUI_MODULES`

Split Setup widgets into a new `serpentrum/gui_setup.py` holding a `SetupTab(QtWidgets.QWidget)` class, and add it to `GUI_MODULES` (`GUI_MODULES = {'serpentrum/gui.py', 'serpentrum/gui_setup.py'}`). `gui.py` constructs the `SetupTab` and passes it as the Setup page to `self.tabs.addTab(setup_tab, 'Setup')` (replacing the placeholder `QWidget`). This:
- preserves the registration contract (`self.tabs` handle, page 0 = Setup, one `addTab` per page — §1.8);
- matches the documented architecture (`ARCHITECTURE.md` §2 lists `gui_setup.py`, `gui_game.py`, `gui_spectra.py` as separate GUI modules — `gui.py` would otherwise balloon to hold all three tabs);
- is the "extend `GUI_MODULES` deliberately" decision the 01-03 summary anticipates (`STATE.md`: "a new GUI module must be added to GUI_MODULES deliberately").

`gui_setup.py` imports `pymol.Qt` (allowed, GUI class) + pure modules (`setup_logic`, `molecule_data`) + `pymol_bridge` via relative imports (exempt). It calls `pymol_bridge.*` on Apply/Cleanup — **never `cmd.*` directly** (GUI class bans it). `[SRC: ARCHITECTURE.md §2 structure; STATE.md decision 01-03; check_purity.py:55,75-78]`.

### 5.4 Rejected alternatives

| Alternative | Why rejected |
|---|---|
| Put `cmd.*` calls in `gui_setup.py` via lazy `from pymol import cmd` inside methods | GUI class bans non-Qt pymol **anywhere** incl. bodies (`check_purity.py:124-131` + `ast.walk`). Would require relaxing the GUI rule — defeats the purity separation. |
| Put `cmd.*` calls in `__init__.py` (ENTRY allows lazy pymol in bodies) | Bloats the "thin entry" (`ARCHITECTURE.md`: `__init__.py` is "THIN — no logic"); conflates entry with bridge; the documented design wants a separate `pymol_bridge.py`. |
| Make `pymol_bridge.py` a GUI module (add to `GUI_MODULES`) | GUI class allows only `pymol.Qt`, not `pymol.cmd` — wrong allowance. Needs the distinct BRIDGE class. |
| Delay all `cmd.*` to a Phase-4 `controller.py` | Phase 3 SC1/SC2/SC5 require viewer materialization + cleanup NOW; controller (game-loop orchestration) is Phase 4+ per `ARCHITECTURE.md` build order. |

---

## 6. Wiring to Pure Logic — The Handoff Contract

### 6.1 The live setup dict

`setup_logic.new_setup()` returns a fresh copy of `DEFAULTS` (schema_version, demo_set, head_molecule, box_preset, xtb_path, win_cap_molecules, atom_budget, broadening_fwhm, speed — `setup_logic.py:48-58,83-90`). The Setup tab edits this dict; `validate(setup)` returns `(errors:[str], warnings:[str])` (`:130-206`).

**When validate runs:** (a) on **Apply** (full validation, blocking on errors); (b) **debounced on field change** to refresh the inline status label (advisory only — never blocks typing). The hessian warning label reuses `validate()`'s warning logic but is wired directly to the spinbox for immediacy.

### 6.2 Dropdown options derive from data

- **Demo-set dropdown** ← `setup_logic.KNOWN_SETS` (`('set_a',)`). v1 ships Set A only; an unknown id is a validation error (`setup_logic.py:43,161-164`).
- **Head-molecule dropdown** ← candidates **handed up by the loader half** after a set is loaded. Default "Random" (`userData='random'`). When the user picks Random, the eventual head selection uses `setup_logic.randomize_head(candidates, seed)` (`:253-265`) — but the **seed and the randomize call belong to game-start (Phase 4)**, not Phase 3 Setup. For Phase 3, "Random" just means "defer choice to game start"; the materialize step may show the first candidate as a placeholder head or none.

### 6.3 Handoff contract the UI needs from the loader half (NOT this research's scope, but stated for planning)

The Setup tab's Apply path needs the loader/bridge to provide:
1. **`load_demo_set(set_id) -> (candidate_ids:[str], errors:[str])`** — loads the shipped manifest + SDFs for a KNOWN_SET, returns the molecule ids usable as head-molecule dropdown candidates (and for Random). Ring-count gate (≤3, DATA-03) is enforced here.
2. **`load_upload(path) -> (candidate_ids:[str], errors:[str])`** — loads a user SDF/mol2 (possibly multi-record), enforces the ≤3-ring gate per molecule, returns candidates + per-molecule rejection reasons (for the "clear reason" modal).
3. **`materialize(setup, candidates) -> errors:[str]`** — cleanup `srp_*`, load box CGO (`cgo_build.box_cgo` from `BOX_PRESETS[setup['box_preset']]`), place/show head (or first candidate if Random-for-now). Returns load errors for the status label.
4. **`cleanup_srp() -> deleted_count:int`** — `cmd.delete('srp_*')`; must work in a fresh process after `.pse` reload (INFRA-04/SC5 — objects survive `.pse`, plugin state does not).

The UI calls these via `pymol_bridge` and displays results. The exact loader internals (manifest parse, ring detection, `cmd.load` smoke proofs) are the **other** Phase-3 research track.

---

## 7. Phase 3 vs Phase 8 Control Split (PROPOSAL — human confirm)

### 7.1 What Phase 3 MUST build (SC1–SC5)

- The **configuration form**: demo-set dropdown, upload picker, box-preset dropdown, head-molecule dropdown (Random default), xtb path+auto-detect, win-cap spinbox + hessian warning label, status label. (SC1–SC4)
- **Two temporary Setup-page buttons** (inside the Setup `QWidget`, NOT the reserved bottom row):
  - **Apply / Show in Viewer** — validates, then `pymol_bridge.materialize(setup)` (cleanup `srp_*` first → load box + head). Satisfies "see the box and chosen head molecule materialize" (SC1/SC2).
  - **Cleanup** — `pymol_bridge.cleanup_srp()`. Satisfies SC5 (Cleanup works, removes only `srp_*`, survives fresh process after `.pse` reload — INFRA-04).
- The **purity-checker BRIDGE class** + `pymol_bridge.py` + `gui_setup.py` in `GUI_MODULES` (§5).

### 7.2 What stays Phase 8 (SETUP-07 / SETUP-08)

- The **canonical 6-button bottom row** (Reset, Randomize, Save Setup, Load Setup, Cleanup model, Start) — `REQUIREMENTS.md` SETUP-07; `ROADMAP.md` Phase 8 SC2; `gui.py:56` comment "Phase 8: 6 right-aligned buttons." Phase 3's temporary buttons are **replaced** by this row in Phase 8.
- **Save/Load Setup** files (SETUP-08) — `QFileDialog` + `setup_logic.save_setup`/`load_setup` round-trip. (The pure `save_setup`/`load_setup` already exist in `setup_logic.py:209-250`; only the GUI wiring is Phase 8.)
- **Randomize** button (uses `setup_logic.randomize_head` / a future `randomize_setup`) — Phase 8.
- **Reset** button (restore `DEFAULTS`) — Phase 8 (though `apply_state(new_setup())` is trivial, the button itself is SETUP-07).
- **Start** button (begins the game → Phase 4 countdown) — not Phase 3; Phase 3 only materializes the configured scene, never starts play.

### 7.3 Why this split is safe

The roadmap note ("the real bottom button row lands in Phase 8") and `REQUIREMENTS.md` traceability (SETUP-07/08 → Phase 8) make the 6-button row explicitly Phase 8. Phase 3's SC5 ("Cleanup model removes only `srp_*`…") requires the cleanup **semantics** to work in Phase 3 — hence the temporary Cleanup button. The temporary Apply button is needed because none of the 6 Phase-8 buttons means "materialize the configured scene without starting a game" (Start starts play; the others reset/randomize/persist). The temporary buttons are clearly labeled as such and live in the Setup page, leaving the reserved bottom `QHBoxLayout` (`gui.py:56-57`) untouched for Phase 8.

**Human-decision item:** confirm that two temporary Setup-page buttons (Apply/Show + Cleanup) are acceptable for Phase 3, vs. an alternative (e.g. auto-materialize on field change with no Apply button; or reusing a subset of the Phase-8 button names early). See §9.

---

## 8. Persisting UI State Across Close/Reopen and Reload

### 8.1 The dialog singleton persists; the setup dict should anchor with it

The dialog is a singleton anchored on `pmg_tk.startup._serpentrum` (`__init__.py:10-26` `_anchor()` → `_SerpentrumState` with `dialog`/`controller` attrs). `run_plugin_gui` reuses `state.dialog` if non-None, else constructs+anchors (`__init__.py:37-45`). So **close/reopen** (re-show) preserves the dialog instance and its child `SetupTab` — a setup dict stored on the `SetupTab` survives close/reopen.

**Plugin-Manager reload** re-executes `__init__.py`; `_anchor()` reuses the existing `_SerpentrumState` (it checks `hasattr` first, `:21`). But `state.dialog` may point to an old dialog; `run_plugin_gui` adopts an orphan via `PluginDialog.find_existing()` (`gui.py:62-69`) or builds a new one if none alive. **If a new dialog is built, a setup dict stored only on the old `SetupTab` is LOST.** To survive reload, store the live setup dict on the **anchor** (`pmg_tk.startup._serpentrum`), which persists across reload.

### 8.2 Recommendation (HIGH confidence)

Add a `setup` field to `_SerpentrumState` (`__init__.py:22-25`), initialized to `setup_logic.new_setup()` on first anchor creation. The `SetupTab` reads/writes `state.setup` (accessed via the dialog/anchor, not module globals — Pitfall 7/8.1). On `SetupTab.__init__`, call `apply_state(state.setup)` to populate widgets; `collect_state()` writes back to `state.setup` on changes/Apply. This survives both close/reopen (singleton dialog) and reload (anchor persists). `[SRC: serpentrum/__init__.py:10-45; PITFALLS.md Pitfalls 7, 8; STATE.md decision 01-01]`.

**Pitfall 8.1 (GC):** never hold the dialog or setup dict in a local variable only — module-global singletons are also unsafe (Pitfall 7 double-import); the anchor is the documented safe location.

---

## 9. Open Questions Needing Human Decision

1. **Purity-checker BRIDGE class + `pymol_bridge.py`** (§5.2). **Recommendation: YES** — extend `check_purity.py` with `BRIDGE_MODULES = {'serpentrum/pymol_bridge.py'}` and create the bridge. This is the documented architecture and the only clean way to permit `cmd.*` under serpentrum's stricter gate. **Confidence: MEDIUM** (inference; the alternative of stuffing cmd calls into ENTRY-lazy works but violates "thin entry"). **Needs human approval** because it changes a gate tool.

2. **Demo Set A data availability for Phase 3** (§6.3, SC1). `serpentrum/data/` currently ships only `DATA_SOURCES.md` + `stacking_pi_stack.json` — **no `manifest.json`, no molecule SDFs** (DATA-01 ships in Phase 8; STATE.md: "do not treat Set A data as fully approved"). Phase 3 SC1 says "choose Demo Set A… and its molecules load." Options: (a) Phase 3 ships a **DRAFT** manifest + a few PubChem SDFs (benzene CID 241 verified available, `FEATURES.md`) sufficient to demo the load path, marked DRAFT; (b) Phase 3 stubs the demo-set load and exercises only the **upload** path; (c) defer demo-set load to Phase 8 and reduce Phase 3 SC1 to upload-only. **This is a scope/human decision** — it determines whether SC1's "Demo Set A" clause is achievable in Phase 3. **Confidence: LOW** (depends on data-approval timing).

3. **Temporary Phase-3 buttons** (§7). Confirm two temporary Setup-page buttons (Apply/Show-in-Viewer + Cleanup) vs. alternatives (auto-materialize on change; reuse Phase-8 button names early). **Recommendation: two temporary buttons**, clearly labeled, leaving the reserved bottom row for Phase 8. **Confidence: MEDIUM** (matches roadmap note; alternative phrasings possible).

4. **Upload unit: single multi-record SDF vs. directory** (§2.1). **Recommendation: single multi-record SDF** via `getOpenFileName` (filter `*.sdf *.mol2`) for Phase 3; directory-upload (`getExistingDirectory`) as a Phase 8 enhancement. The loader half must confirm it parses multi-record SDF. **Confidence: MEDIUM**.

5. **Head "Random" materialization in Phase 3** (§6.2). For Phase 3, "Random" cannot truly randomize (seed + `randomize_head` belong to game-start, Phase 4). Options: show the first candidate as a placeholder head; show no head until Start (Phase 4); show all candidates faintly. **Recommendation: show the first candidate as a placeholder** with a status note "head will be randomized at game start." **Confidence: LOW** (UX judgment; human-confirm).

---

## RESEARCH COMPLETE

**Phase:** 3 — Molecules in the Viewer & Setup Tab (Setup-tab UI half)
**Confidence:** HIGH (Qt/widgets/thread-boundary/error-surfacing verified against shipped bioCHEMeleon + repo research docs); MEDIUM (purity-class extension — deliberate human decision); LOW (demo-data availability — human-gated).

### Key Findings

- **Thread boundary (settled):** button-click handlers run on the Qt main thread = the PyMOL gui thread, so `cmd.*` may be called **directly** from handlers (verified bioCHEMeleon pattern). No worker/queue needed for Phase 3's sub-second loads; the queue/drain pattern is reserved for Phase 6 xtb. Pitfall 6 (no `cmd.*` from threads) is trivially satisfied — Phase 3 spawns no threads.
- **Allowlist/module recommendation:** add `serpentrum/gui_setup.py` (`SetupTab(QWidget)`) to `GUI_MODULES`; add a **new `BRIDGE_MODULES` class** to `check_purity.py` permitting `pymol import cmd` (banning PyQt5/numpy) and create `serpentrum/pymol_bridge.py` as the single cmd-seam. This is the first phase touching `cmd.*`, and the current purity checker has no class that allows it.
- **Error surfacing:** one-shot blocking errors (upload rejected, invalid setup) → `QMessageBox.warning` (static method, no `.exec_()` token, pre-game modals OK); advisory hessian warning → inline `QLabel` toggled by the spinbox.
- **Phase 3 vs Phase 8 split:** Phase 3 = the config form + two temporary buttons (Apply/Show + Cleanup); Phase 8 = the canonical 6-button row + save/load/randomize/reset/start. The reserved bottom `QHBoxLayout` stays untouched.
- **State persistence:** anchor the live setup dict on `pmg_tk.startup._serpentrum` (add a `setup` field to `_SerpentrumState`) so it survives close/reopen AND Plugin-Manager reload.

### Human-Decision Items

1. Approve the purity-checker BRIDGE class + `pymol_bridge.py` (§5.2, §9.1).
2. Decide Demo Set A data availability for Phase 3 (DRAFT manifest vs. upload-only vs. defer) (§9.2).
3. Confirm the two temporary Phase-3 buttons (§7, §9.3).
4. Confirm single-multi-record-SDF upload unit (§9.4).
5. Confirm "Random" head placeholder behavior in Phase 3 (§9.5).

### File Created

`.planning/phases/03-molecules-in-the-viewer-setup-tab/03-RESEARCH-setup-ui.md`

### Sources (verified)

- `serpentrum/gui.py`, `serpentrum/__init__.py`, `serpentrum/setup_logic.py`, `serpentrum/xtbenv.py`, `serpentrum/molecule_data.py`, `serpentrum/cgo_build.py`, `tools/check_purity.py` (read in full)
- `tmp/bioCHEMeleon/biochemeleon/gui_setup.py` (collect_state/apply_state `:539-617`; widget patterns `:67-120`; `QMessageBox`/`QFileDialog` static use `:362,456,484,646,665,674` — zero `.exec_()`), `__init__.py` (`_on_start`/`_prepare_and_start` `:242-346`; `cmd.load` direct in handler `:839`; `cmd.count_atoms` in `_randomize`; worker/queue/drain `_resolve_large_demo` `:545-677`), `persistence.py` (pure/Qt split)
- `.planning/research/STACK.md` (§1 GUI shell, §Core table pymol.Qt `:26-40`, F9 refresh, Pitfall-row thread rule), `PITFALLS.md` (Pitfalls 2, 5, 6, 7, 8), `ARCHITECTURE.md` (§2 component table + structure, Pattern 2 worker/drain, F7/F10), `FEATURES.md`, `REQUIREMENTS.md` (SETUP-02..08, DATA-03, INFRA-04/05), `ROADMAP.md` (Phase 3 SC1–SC5, Phase 8 SETUP-07/08), `STATE.md` (decisions 01-01..01-06, Phase-2 data approval)
- `.planning/phases/01-plugin-skeleton-purity-harness/01-02-SUMMARY.md` (registration contract), `01-06-SUMMARY.md` (gates + module identity)

### Confidence Assessment

| Area | Level | Reason |
|------|-------|--------|
| Qt widget inventory + layout | HIGH | All widgets verified in shipped bioCHEMeleon gui_setup.py; standard PyQt5 |
| Qt↔PyMOL thread boundary | HIGH | Direct-cmd pattern verified in bioCHEMeleon handlers + locking.py citation; Pitfalls 2/6 |
| Error/warning surfacing | HIGH | Static QMessageBox/QFileDialog verified no-.exec_(); Pitfall 5 modal rule |
| Module decomposition / allowlist | MEDIUM | Inference from current checker + documented architecture; deliberate human decision |
| Phase 3/8 control split | MEDIUM | Matches roadmap note; temporary-button phrasing is a judgment call |
| Demo-data availability | LOW | Data not shipped (Phase 8); human-gated scope decision |
| State persistence | HIGH | Anchor pattern verified in __init__.py + Pitfalls 7/8 |

**Valid until:** 2026-10-10 (stable domain; re-verify bioCHEMeleon patterns only if upstream plugin is updated).

---

*Setup-tab UI research for: serpentrum Phase 3 — Molecules in the Viewer & Setup Tab*
*Researched: 2026-09-10*
