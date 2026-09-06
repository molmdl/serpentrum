# Stack Research

**Domain:** PyMOL plugin — educational snake game (molecule stacking) + xtb IR spectra
**Researched:** 2026-09-06
**Confidence:** HIGH overall (every core claim verified against `pymol-src`, `tmp/bioCHEMeleon`, `Pymol-script-repo`, or live `xtb.exe` output; two items flagged LOW/MEDIUM requiring a phase spike)

**Method note:** This is a constrained-greenfield stack: the dependency set is fixed by repo AGENTS.md (only what `pymol-open-source` 2.5.0 ships — PyQt5 via `pymol.Qt`, numpy). Research therefore focused on (a) verifying exactly what PyMOL 2.5.0 ships, (b) verifying the runtime mechanisms (game loop, arrow keys, CGO rendering, Qt plotting), and (c) auditing the assumed xtb pipeline — which **failed** its audit and needs a corrected invocation. Zero third-party additions are required, which is the cleanest possible dependency posture.

---

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended | Verified |
|------------|---------|---------|-----------------|----------|
| PyMOL open-source (runtime) | 2.5.0 (ChangeLog 2021-05-10, `pymol-src/ChangeLog:4-6`) | Host app, molecular engine, OpenGL viewer | The only runtime; plugin API (`pymol.cmd`, `pymol.wizard`) is complete for all game needs | `pymol-src` tree = installed version |
| Python (runtime, in conda env) | Unknown exact (conda `pymol-open-source` 2.5.0 env) | Plugin language | Fixed by host; **author plugin code to Python 3.6 syntax** so the WSL `python3.6.9` dev gate and the Windows runtime both work (bioCHEMeleon proved this discipline) | LOW (exact runtime ver unverified) — dev gate = `python3.6 -m py_compile` (bioCHEMeleon AGENTS.md) |
| PyQt5 (via `pymol.Qt`) | bundled, auto-selected | GUI: tabs, dialogs, QTimer, QProcess, QPainter | `pymol/Qt/__init__.py:26-30` tries PyQt5 first, falls back PySide2 → **always import via `from pymol.Qt import ...`, never `from PyQt5 import`** | `pymol-src/modules/pymol/Qt/__init__.py:26-40` |
| numpy | bundled (PyMOL build dep, `setup.py:459-461`) | Broadening math (Gaussian sums), geometry, hessian/eigenvector math | Already a hard PyMOL dependency; imported at runtime by `chempy/brick.py` | `pymol-src/setup.py:459`; `pymol-src/modules/chempy/brick.py` |
| xtb (external exe, not a Python dep) | 6.7.1pre (5071a88, built 2024-07-23) | Opt + numerical Hessian → frequencies + IR intensities | Proven installed at `C:\xtb-6.7.1` and runnable from WSL; invoked as a subprocess (no Python binding involved) | `tmp/xtb_test/phenol_hess.log:10`; `test_wsl_winxtb.sh` |

**Headline: no additional Python libraries.** No matplotlib, no scipy, no vendoring into `3rd_party_lib/` — see "What NOT to Use" for why each candidate was rejected.

### Component Stack (mechanism choices — the load-bearing decisions)

#### 1. GUI shell — Qt plugin dialog, 3 tabs (verified pattern)

- Entry point `__init_plugin__(app=None)` + `from pymol.plugins import addmenuitemqt` — verified in-tree plugin convention (`Pymol-script-repo/plugins/dynoplot.py:446`) and proven in bioCHEMeleon (`tmp/bioCHEMeleon/biochemeleon/__init__.py:113+`).
- Main dialog **modeless**: `dialog.show()`, never `.exec_()` — required so the OpenGL viewer stays interactive during play (bioCHEMeleon AGENTS.md gate, enforced by grep). Module-level `dialog = None` singleton prevents GC (borrowed from `outline.py:46`, per bioCHEMeleon `__init__.py:6-8`).
- Tab structure (Setup / Gameplay / Spectra) mirrors bioCHEMeleon's `QTabWidget` shell; `QFileDialog` for molecule upload & setup JSON; `QMessageBox` only on child dialogs (modal OK for those; **forbidden during gameplay** — verified: modal dialogs block the Qt event loop and freeze the viewer, `gui_game.py:289-304` docstring + Bug A/B/C fixes).
- Dialogs that must appear above the OpenGL window: parent = `self.window()` + `WindowStaysOnTopHint` (verified `gui_game.py:337-344`).

#### 2. Game loop — `QtCore.QTimer` on the Qt main thread (verified)

- **`QtCore.QTimer` is the loop.** Verified in-tree usage: bioCHEMeleon `gui_game.py:109-111` (1 Hz status timer), `gui_game.py:261` (`QTimer.singleShot` countdown chain). For the snake: tick interval ≈ 100–150 ms (6–10 fps logic ticks; PyMOL scene redraw is cheap for CGO-only objects).
- Tick handler does: read pending direction → advance snake state (pure module) → push to viewer (CGO rebuild, see §3) → collision check (pure) → callbacks to UI (log/timer/counts).
- Pause = `self._timer.stop()`; resume = `.start(interval)`. Countdown 3-2-1-GO = `singleShot` chain (verified `gui_game.py:258-264`).
- Redraw sync: `cmd.refresh()` then `QTimer.singleShot(100, …)` before any modal/transition (verified pattern `gui_game.py:302-304`).
- **Threading rule (hard):** never `threading.Thread`/`QThread` calling `cmd.*` — verified pitfall (bioCHEMeleon PITFALLS Pitfall 6). Everything game-related runs on the Qt main thread; the *only* async work is the xtb subprocess (§5), which uses signals, not threads.

#### 3. Rendering — dedicated CGO objects per game entity (verified APIs)

All rendering via PyMOL objects the game owns; never mutate user molecules mid-game.

| Entity | Mechanism | Verified basis |
|--------|-----------|----------------|
| Boundary box | CGO object `serp_boundary`: `BEGIN LINES` + `LINEWIDTH` + `COLOR` segments from box corners | `cmd.load_cgo` verified `importing.py:300`; CGO constants `pymol/cgo.py:34-65` (`LINEWIDTH=10.0`, `COLOR=6.0`, `BEGIN=2.0`) |
| Snake | CGO object `serp_snake`: `SPHERE` per segment centroid + `CYLINDER` between consecutive segments; **rebuilt each tick** via `cmd.load_cgo` after `cmd.delete` (or first tick create) | `SPHERE=7.0`, `CYLINDER=9.0` verified `cgo.py:39,41`. Rebuild cost trivial: snake ≤ ~100 atoms → few hundred floats |
| Pickups (small molecules) | One PyMOL object per pickup loaded from bundled `.mol`/`.sdf`, shown as sticks; positioned by `cmd.translate([dx,dy,dz], 'objname')` | Native load formats "pdb, mol, mol2, sdf" verified `importing.py:683`; `cmd.translate` verified `editing.py:1610` (+ `_cmd.translate_object_ttt` `editing.py:1696`) |
| Snake head | Same `serp_snake` CGO, or a distinct colored sphere overlay | CGO COLOR verified |
| Vibrational vectors | CGO object `serp_vectors`: `LINE`/`CONE` arrows from atom positions along mode eigenvectors, scaled | `CONE=27.0` verified `cgo.py:65` |
| Stacking highlight (optional) | `cmd.color` / `cmd.spectrum` on pickup atoms | `cmd.spectrum` verified `viewing.py:2019` |

Rebuild-CGO-per-tick beats `cmd.alter_state` coordinate surgery: no atom bookkeeping, no index/id pitfalls (bioCHEMeleon's id-vs-index pitfalls all stemmed from mutating a loaded protein object — the snake avoids that class entirely by owning synthetic CGO objects).

#### 4. Input — `Wizard` subclass with `do_special`/`do_key` (verified end-to-end in C layer)

This is the highest-risk integration and it is **fully verified**:

1. Qt main window forwards keys: `pymol_qt_gui.py:50-54` `keyPressEvent` → `keymapping.keyPressEventToPyMOLButtonArgs` (`keymapping.py:61-97`). Arrow keys map via `specialMap` (`keymapping.py:19-23`): **Left=100, Up=101, Right=102, Down=103**, routed as "special" (state=-2 → C `PyMOL_Special`). Regular keys (letters) route via `PyMOL_Key`.
2. C layer dispatch: `layer5/PyMOL.cpp:2301-2307` — `PyMOL_Special` calls `WizardDoSpecial` **first**; `layer1/Wizard.cpp:465-476` calls Python `do_special(k,x,y,mod)`; a truthy return *grabs* the key.
3. **Required override:** the C wizard gates dispatch on an event mask read from Python — `Wizard.cpp:221-228` stores `get_event_mask()`; default is pick+select only (`wizard/__init__.py:55-56`). A keyboard wizard MUST return `Wizard.event_mask_key + Wizard.event_mask_special` (= 4+8; constants at `wizard/__init__.py:8-9`). Miss this and `do_special` never fires.
4. **Known side effect (documented, cosmetic):** in `PyMOL_Special`, UP/DOWN *always* also reach `OrthoSpecial` (`PyMOL.cpp:2310-2314` → `layer1/Ortho.cpp:314-393`), which scrolls the command-line history buffer. The wizard still receives the key first — gameplay is unaffected; the command line text just churns. LEFT/RIGHT only leak to `OrthoSpecial` when the command line holds unsubmitted text (`OrthoArrowsGrabbed`, `Ortho.cpp:398-402`) — clean during play. Mitigation: note in Help; optionally `cmd.deselect()`-style hygiene is irrelevant here.
5. `do_key` (ASCII k, verified example `wizard/command.py:166-180`: 8/127=delete, 13=enter, 27=esc, 31<k<127 printable) → use for **P** (pause), **R** (restart), **Esc** (quit) as keyboard shortcuts alongside buttons.
6. Wizard lifecycle: `cmd.set_wizard(self)` / restore prior wizard on deactivate — verified working pattern `bioCHEMeleon/wizard.py:86-92`; in-viewer prompt/panel via `get_prompt()`/`get_panel()` (`wizard/__init__.py:49-53`) gives space for in-game instructions ("arrow keys steer; P pauses").
7. **Focus caveat:** keys reach the viewer only when the PyMOL main window (not the command-line edit box, not another app) has focus (`pymol_qt_gui.py:50`; the only special-cased key is Tab, `pymol_qt_gui.py:437-451`). UX must handle "keys don't respond → click the 3D viewer" (Help text + wizard prompt).

#### 5. xtb pipeline — QProcess, per-run temp dir, **`--ohess` not `-o --hess`** (corrected!)

**Audit finding (HIGH confidence, empirical):** the assumed invocation `xtb.exe mol.xyz -o --hess` does **not** produce spectra. `tmp/xtb_test/phenol_hess.log` (640 lines, full run captured) contains optimization + final single point **and no vibrational frequency section**; the output dir has no `hessian`, `vibspectrum`, or `g98.out`. The "Using Lindh-Hessian" line (log:258) is the ANC *optimizer's model Hessian*, not a frequency job. AGENTS.md's "proven working" claim holds only for optimization.

**Verified correction** — from the actual `xtb.exe --help` output (captured to `tmp/xtb_test/xtb_help.txt`):
- `-o, --opt [LEVEL]` — optimization only (help:148-150)
- `--hess` — "numerical hessian calculation **on input geometry**" (help:152-153)
- `--ohess [LEVEL]` — "numerical hessian calculation on an **ancopt(3) optimized geometry**" (help:155-156) ← **the one-shot command serpentrum needs**

Two equally valid invocation shapes (pick in phase design; A is simpler to debug/parse):
- **A (two-stage):** `xtb snake.xyz -o` → parse/keep `xtbopt.xyz`; then `xtb xtbopt.xyz --hess` in a second run. Matches documented semantics exactly.
- **B (one-shot):** `xtb snake.xyz --ohess`.

Invocation mechanics (all verified or derived from verified facts):
- The plugin runs **inside Windows PyMOL**, so xtb is a plain local Windows exe: `subprocess`/`QProcess` with **`cwd` = a fresh per-run temp dir** (`tempfile.mkdtemp()`) and **bare relative filenames** as args (`snake.xyz`) → zero WSL↔Windows path translation at runtime. The WSL→Windows path guards remain a *dev-workflow* concern only (headless smokes).
- **Binary detection** (AGENTS.md requirement): probe configured path, then `shutil.which("xtb")` / `shutil.which("xtb.exe")` (Windows conda env has `.exe`; a Linux PyMOL install would have `xtb`). Pure-layer function → unit-testable.
- **Async model:** `QtCore.QProcess` (exported via `pymol.Qt` QtCore — verified export list `Qt/__init__.py:28`): `start()`, `finished(int, QProcess::ExitStatus)` signal lands on the Qt main thread → slot may safely call `cmd.*` (same-thread rule). Progress: readyReadStandardOutput → append to Spectra log. This keeps the viewer alive during the seconds-to-minutes hessian (phenol opt alone = 0.063 s wall, log:629; hessian ≈ 3N+1 SCF+gradient passes, cost grows ~N³ per PROJECT.md) and satisfies the no-threads-with-cmd rule. Fallback if QProcess proves awkward on the conda build: blocking `subprocess.run` + `processEvents` pump — accepted for v1 only with a "calculating…" note (freezes viewer; documented).
- Useful flags (verified help text): `--namespace serp` (namespaced output files, help:187-189), `-P N` threads (help:197-198), `--json` (xtbout.json, help:203-204 — verify whether it carries frequencies; do not rely until verified), `--gfn 2` (default GFN2-xTB, confirmed in log:413).
- A timeout kill + friendly error path is required (bad geometries → xtb non-zero exit).

#### 6. Hessian parsing + spectrum — pure module + QPainter widget (one LOW-confidence gate)

- **Parsing lives in a pure data module** (stdlib + numpy only) so it is fully unit-testable in WSL against the *real* captured xtb outputs as fixtures (the `phenol_hess.log` fixture practice is already established in `tmp/xtb_test/`).
- ⚠ **LOW/MEDIUM confidence gate (phase-1 spike required):** a completed `--ohess`/`--hess` run was **not yet captured in-repo** (the audit run never reached the hessian stage; a verification run was deferred by the user during research). Expectation from xtb's documented conventions: `hessian` (cartesian Hessian), `vibspectrum` (frequencies), `g98.out` (Gaussian-style file with frequencies **and IR intensities** and normal-mode vectors) — **these file names/contents must be verified by an actual run before the parser is written.** Budget a first task in the spectra phase: run `xtb.exe phenol.xyz --ohess`, commit outputs as fixtures, write parser to match reality.
- **Broadening:** numpy-only Gaussian (or Lorentzian/Gaussian mix) sum over (frequency, intensity) pairs — σ/FWHM as a Setup constant (~10–20 cm⁻¹ typical for educational display; exact value = user-tunable, no literature claim needed). No scipy.
- **Plot = custom `QWidget` with `paintEvent` + `QPainter`** — two verified in-ecosystem precedents prove this works inside PyMOL plugins with zero extra deps:
  - `pymol-src/modules/pmg_qt/volume.py:252-276` — PyMOL's own volume editor widget: grid, axes, histogram, antialiasing, interactive text boxes.
  - `Pymol-script-repo/plugins/dynoplot.py:68-133` — a *plugin* that draws an interactive plot (axes, ticks, curves, click hit-testing) with `pymol.Qt` only.
  - Widget features: frequency axis + broadened curve + stick spectrum; click → nearest mode (store mode→x map; hit-test like dynoplot); minimal adjustables (axis labels, size); **save plot** via `widget.grab().save(path)` (QPixmap — no extra deps).
- **Frequency table:** `QTableWidget` (mode #, cm⁻¹, intensity); row-click → emit mode index → viewer shows `serp_vectors` CGO (§3). Vibrational **animation** explicitly out of scope v1 (PROJECT.md).
- **Mode vectors source:** prefer the hessian-run's eigen output (g98.out if verified to contain displacement vectors); fallback = parse `hessian` + numpy `eigh` with mass-weighting and translation/rotation projection (more code — avoid unless g98.out lacks vectors). Decision gated on the phase spike.

#### 7. Game logic / geometry — pure modules (verified layering pattern)

- Strict dependency direction, proven in bioCHEMeleon and directly reusable: **pure data/logic (stdlib+numpy only; no pymol, no Qt; unit-testable on python3.6) ← cmd bridge ← Qt GUI ← composition root** (bioCHEMeleon AGENTS.md "Architecture — module dependency direction is strict"; `tests/test_setup_state.py` stubs `pymol`/`pymol.Qt` via `sys.modules` MagicMock).
- Pure modules: grid/box model, snake state machine (tick/direction/collision/self-hit), stacking placement math (known stacking mode + distance → next-segment transform), xtb path detection, hessian parser, broadening math, win-cap/atom-budget guard.
- Setup persistence: JSON (stdlib `json` + `QFileDialog`) — verified pattern (`bioCHEMeleon/persistence.py:22+`).

#### 8. Molecule library

- Bundled demo sets as `.mol`/`.sdf` files in a plugin `data/` dir + `DATA_SOURCES.md` attribution (all sources human-approved before inclusion — hard repo rule). Load via `cmd.load(path, 'stick-rep object')` (format support verified `importing.py:683`).
- Stacking metadata (mode + distance per molecule pair/set) as pure-Python/JSON tables **with verified citations** — no fabricated chemistry (hard repo rule).

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| WSL `python3.6 -m py_compile` | Syntax gate on every module | Verified bioCHEMeleon command; keep as a repo grep-gate habit |
| WSL `python3.6 -m unittest` | Pure-layer unit tests (logic, parser, geometry, path detection) | Stub `pymol`/`pymol.Qt` in `sys.modules` (verified pattern `tests/test_setup_state.py`) |
| `cmd.exe /c C:\src\run-conda-pymol.bat -cq <script>` | Headless cmd-only smoke tests from WSL | Verified workflow (bioCHEMeleon AGENTS.md, Phase 3 discovery); **cannot** exercise Qt/keyboard/GUI |
| Stage-then-run: copy package to a Windows-readable path | Headless runs | `/mnt/c/...`-path discipline; Windows PyMOL can't resolve WSL paths (repo AGENTS.md) |
| Human-in-loop UAT | Qt UI, arrow-key feel, game balance, plot interactions | Standard for this environment (bioCHEMeleon precedent) |
| `rg`-free grep gates | Dependency hygiene (`from PyQt5 import`, `.exec_()`, `import matplotlib` etc.) | bioCHEMeleon gate commands (AGENTS.md); add matplotlib/import-gate for serpentrum |

---

## Installation

No pip. No conda. Nothing to install — that is the point of this stack.

```bash
# Dev-side (WSL): syntax + unit tests only, using stock python3.6
python3.6 -m py_compile serp/*.py
python3.6 -m unittest discover -s tests -v

# Runtime-side (Windows): plugin install via PyMOL Plugin Manager,
# or for dev/testing add the repo path to PyMOL's plugin path
# (spec.md requirement 0: "install by adding to plugin path").
```

Plugin install convention: package dir containing `__init__.py` with `__init_plugin__(app=None)` + `addmenuitemqt` (verified convention §1). External runtime dependency: xtb at a user-configured or auto-detected path (Setup tab field, spec.md requirement 2).

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| `QtCore.QTimer` game loop | PyMOL movie/frames (`cmd.mset` + `cmd.frame`) | Never for interactive games — frame system is for molecular animation playback, no input-driven pacing. (Design-level rejection; no verified in-ecosystem game uses it.) |
| `QtCore.QTimer` game loop | C-level idle hook / `PyMOL_Idle` piggybacking | Never — private API, fragile across builds; QTimer is the proven plugin-level loop. |
| CGO-object rebuild per tick | `cmd.alter_state`/pseudoatom coordinate surgery on a real molecule object | Only if per-atom PyMOL-native rendering (e.g. real molecule reps on snake atoms) becomes a v2 requirement — then inherit bioCHEMeleon's sentinel/backup machinery too. |
| CGO objects for snake | Qt OpenGL overlay widget (`QtOpenGL` on top of viewer) | Never — fights PyMOL's own GL context/window for events; `QtOpenGL` is importable (`Qt/__init__.py:28`) but unused by any plugin precedent we verified. |
| Wizard `do_special` for arrows | Qt-side `keyPressEvent` on our own dialog | Only for UI-widget-level keys (table navigation). Gameplay arrows MUST go through the Wizard: the Qt path maps arrows to C `PyMOL_Special` regardless (`keymapping.py:19-23`), so a wizard is the only way to intercept them before Ortho/history handling. |
| `QProcess` for xtb | Blocking `subprocess.run` + `processEvents` | v1 fallback if QProcess misbehaves in the conda env; acceptable only with explicit "calculating…" UX (viewer freezes). |
| QPainter spectrum widget | Vendored matplotlib in `3rd_party_lib/` | Only if v2 demands publication-quality figures/interactivity that QPainter can't reach — requires written approval + license note + git-ignored vendoring (repo rule), and matplotlib's Qt backend inside PyMOL's Qt loop is unverified. Two verified QPainter precedents make this unnecessary for v1. |
| numpy `eigh` on parsed hessian | Eigen data from hessian-run text output (g98.out-style) | Prefer text output if the phase spike verifies it carries vectors; numpy diagonalization is the fallback (mass-weighting + projection = ~50 extra lines). |
| Two-stage `--opt` then `--hess` | One-shot `--ohess` | One-shot is fine once verified; two-stage gives a clean checkpoint (optimized xyz) between stages and keeps each log single-purpose — easier parsing/debugging. |
| 2D plane gameplay (locked view) | Full 3D movement (6-direction steering) | 3D only if user explicitly wants it — doubles steering ambiguity (arrow keys are 4), complicates collision + stacking placement, and camera-vs-plane confusion. **This is a pending Key Decision in PROJECT.md — recommend 2D for v1, needs user approval.** |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `from PyQt5 import ...` | Breaks under PySide2 fallback; violates verified hygiene gate (bioCHEMeleon grep gate) | `from pymol.Qt import QtWidgets, QtCore, QtGui` (`Qt/__init__.py:26-40`) |
| matplotlib (any form) | **Not bundled** — zero references in `pymol-src` modules + `setup.py` (verified). Vendoring = heavyweight approval + unverified Qt-backend-inside-PyMOL risk | QPainter custom widget (two verified precedents: `pmg_qt/volume.py`, `dynoplot.py`) |
| scipy | Not bundled; broadening/eigendecomposition are trivial in numpy | numpy |
| `threading.Thread`/`QThread` calling `cmd.*` | Verified pitfall (bioCHEMeleon PITFALLS 6): PyMOL cmd is not thread-safe from Python side-threads | Qt main thread + QProcess signals |
| Modal dialogs during gameplay (`QMessageBox.exec_`, main dialog `.exec_()`) | Verified: blocks Qt event loop → viewer freezes mid-tick (bioCHEMeleon Bug A/B/C) | Modeless main dialog; non-modal status messages; modals only on completion, after `cmd.refresh()` + 100 ms `singleShot` |
| Pmw / Tkinter (`pmg_tk` stack) | Legacy Tk GUI generation; bioCHEMeleon gate proves the codebase stays Tk-free | pymol.Qt |
| `-o --hess` xtb invocation | **Verified broken for spectra**: `phenol_hess.log` has no frequency section, no hessian/vibspectrum files written | `--ohess` (verified help:155-156) or two-stage `--opt` → `--hess` |
| Parsing `phenol_hess.log`-style logs for frequencies | The `-o` log contains no frequency block (verified) — parser would match nothing | Parse the hessian-run output files (names to be fixed by phase spike) |
| WSL paths (`/mnt/c/...`) in runtime code | Runtime is Windows PyMOL; `/mnt/c` unresolvable there (repo AGENTS.md) | `cwd`-relative args + temp dir; path conversion only in dev/headless helpers |
| Atom-`index`-keyed game state | Verified pitfall: index shifts on insert/delete (bioCHEMeleon AGENTS.md, `querying.py:1313+`) | Not applicable if snake is CGO-owned; if any atom tracking is added, key on atom `id` |
| 3rd-party game/physics engines | Overkill (grid arithmetic), dependency-approval cost, py3.6 compat risk | Pure-module grid logic |

## Stack Patterns by Variant

**If gameplay is 2D-plane (recommended v1):**
- Fixed camera: play field in the xy-plane; lock/ignore view rotation during play (document it; optionally restore view each game start with a saved `cmd.get_view()` matrix).
- Snake advance = grid steps in xy; stacking transform = planar (mode + distance in-plane); boundary CGO = rectangle (+ shallow depth for perception).
- All four arrow keys map 1:1 to directions — cleanest input mapping given the verified Left=100/Up=101/Right=102/Down=103 codes.

**If gameplay is 3D (only with user approval):**
- Keep grid (6 directions via arrows + PageUp/PageDown or modifier combos; `specialMap` also carries PgUp=104/PgDn=105 codes — verified `keymapping.py:24-25`).
- Stacking transforms become full 3D (known stacking modes still constrain them); boundary = box; camera orbit must remain enabled → input mapping must be camera-relative or world-fixed (decide in phase design).

**If a Linux PyMOL runtime is ever targeted:**
- Binary detection (`xtb` vs `xtb.exe`) already covers it (AGENTS.md requirement); `QProcess` and all `pymol.Qt` usage are platform-neutral; the only Windows-specific piece is the conda-env dev loop, which is dev-side, not plugin code.

## Version Compatibility

| Component | Compatible With | Notes |
|-----------|-----------------|-------|
| Plugin code (py3.6-compatible syntax) | PyMOL 2.5.0 conda env (Windows) + WSL python3.6.9 tests | Verified discipline from bioCHEMeleon; avoid dataclasses (3.7+), walrus (3.8+), f-string `=` (3.8+). f-strings themselves are 3.6-OK but repo precedent uses %-formatting — follow it |
| `pymol.Qt` API | PyQt5 **or** PySide2 (auto-selected) | Verified `Qt/__init__.py:26-40` + Signal/Slot normalization (:84-94). Avoid PyQt5-only APIs (e.g. `pyqtSignal` — use `QtCore.Signal`) |
| xtb 6.7.1pre Windows | `--ohess`, `--hess`, `--opt`, `--namespace`, `-P`, `--json` | Verified via captured `--help` (tmp/xtb_test/xtb_help.txt). Note: 6.7.1pre, built 2024-07-23 (log:10); a release 6.7.1 may differ slightly — pin to the installed binary |
| QProcess | QtCore (any Qt 5.x in the conda env) | Standard QtCore class; exact Qt version unverified — verify `QtCore.QProcess` import at phase start (one-line smoke) |
| CGO constants | PyMOL 2.5.0 | Verified `pymol/cgo.py:34-65` (values stable across PyMOL 2.x, but cite this file) |

## Open Verification Items (carry into phase research)

1. **xtb hessian output formats (gate for the spectra phase):** run `xtb.exe phenol.xyz --ohess` once, capture all output files as fixtures, then finalize the parser spec (which file carries frequencies; which carries IR intensities; whether normal-mode vectors are included or must be derived from the `hessian` file). *During research a verification run was deferred by the user; the `-o --hess` audit proves the current fixture set is insufficient for parser development.*
2. **Runtime Python + Qt versions in the Windows conda env** (one-line headless print: `sys.version`, `QtCore.QT_VERSION_STR`) — LOW confidence item affecting only niceties (no API at risk given py3.6-compatible source).
3. **`xtbout.json` contents for `--ohess`** — if it carries frequencies/intensities, it's a more robust parse target than text scraping (help:203-204 confirms existence, not content).
4. **QProcess availability/behavior in the conda PyMOL Qt loop** (smoke: start `xtb.exe --version`, catch `finished`).

## Sources

All verified against in-repo artifacts (HIGH confidence unless noted):

- `pymol-src/modules/pymol/Qt/__init__.py:26-40, 84-94` — PyQt5-first binding selection, exported modules
- `pymol-src/modules/pmg_qt/keymapping.py:19-41, 61-97` — Qt key → PyMOL key/special code mapping (Left=100, Up=101, Right=102, Down=103, PgUp=104, PgDn=105)
- `pymol-src/modules/pmg_qt/pymol_qt_gui.py:50-54, 437-451` — key event forwarding; Tab eventFilter; focus behavior
- `pymol-src/layer5/PyMOL.cpp:2301-2322` — `PyMOL_Special`/`PyMOL_Key` → wizard-first dispatch; UP/DOWN always hit Ortho; LEFT/RIGHT gated by `OrthoArrowsGrabbed`
- `pymol-src/layer1/Wizard.cpp:221-228, 327-340, 465-476` — event-mask gating; `do_key`/`do_special` invocation
- `pymol-src/layer1/Ortho.cpp:314-402` — what UP/DOWN/LEFT/RIGHT do to the command line (history scroll / cursor)
- `pymol-src/modules/pymol/wizard/__init__.py:5-16, 49-56, 82-86` — Wizard base, event mask constants, `do_key`/`do_special` defaults
- `pymol-src/modules/pymol/wizard/command.py:166-180` — verified `do_key` implementation example
- `pymol-src/modules/pymol/importing.py:300 (load_cgo), 683 (load formats pdb/mol/mol2/sdf)`
- `pymol-src/modules/pymol/cgo.py:34-65` — SPHERE/CYLINDER/LINEWIDTH/COLOR/ALPHA/CONE constants
- `pymol-src/modules/pymol/editing.py:1610, 1696, 2169` — translate / translate_object_ttt / translate_atom
- `pymol-src/modules/pymol/creating.py:1082` (pseudoatom); `viewing.py:2019` (spectrum)
- `pymol-src/modules/pmg_qt/volume.py:240-300` — in-tree QPainter custom-widget precedent (paintEvent, axes, grid, hit-testing)
- `Pymol-script-repo/plugins/dynoplot.py:18-21, 68-133, 446` — plugin QPainter plot precedent + `addmenuitemqt` convention
- `pymol-src/setup.py:459-461` — numpy build dependency; matplotlib absent from entire tree (grep-verified)
- `tmp/bioCHEMeleon/biochemeleon/gui_game.py:109-111, 258-264, 289-345` — QTimer loop, singleShot countdown, modal-freeze pitfalls, stay-on-top dialogs
- `tmp/bioCHEMeleon/biochemeleon/wizard.py` — verified Wizard lifecycle (set_wizard/activate/deactivate/get_panel)
- `tmp/bioCHEMeleon/biochemeleon/persistence.py:22+` — JSON+QFileDialog persistence pattern
- `tmp/bioCHEMeleon/AGENTS.md` — verified pitfalls (no undo → backup; no threads with cmd; pseudoatom returns None; ID uppercase; index fragility; headless cmd.exe workflow; py3.6 gates)
- `test_wsl_winxtb.sh` + `tmp/xtb_test/phenol_hess.log` — xtb invocation audit: `-o --hess` produced opt only, **no frequencies**; version 6.7.1pre (log:10); GFN2 default (log:413); wall-time 0.063 s (log:629)
- `tmp/xtb_test/xtb_help.txt` (captured live from the installed xtb.exe during this research) — `--opt`/`--hess`/`--ohess` semantics, `--namespace`, `-P`, `--json`
- `.planning/PROJECT.md` — requirements, key decisions pending research (2D/3D, movement model, speed)

---
*Stack research for: serpentrum — PyMOL plugin educational snake game with xtb spectra*
*Researched: 2026-09-06*
