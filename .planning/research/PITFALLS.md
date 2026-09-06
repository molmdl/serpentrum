# Pitfalls Research

**Domain:** Educational snake game as a PyMOL 2.5.0 plugin (PyQt5) + Windows xtb 6.7.1 spectra pipeline, developed in WSL
**Researched:** 2026-09-06
**Confidence:** HIGH overall (core pitfalls empirically verified in this repo/environment); per-pitfall levels inline

## How to read this file

Each critical pitfall has:
- **What goes wrong** — the failure mode
- **Why it happens** — root cause, with runtime evidence where verified
- **How to avoid** — actionable prevention
- **Warning signs** — early detection
- **Confidence & evidence** — `[RUN]` = executed today by this researcher (scratch runs under `/tmp/opencode/xtb_spike/` using the repo's proven `xtb.exe` symlink and `tmp/xtb_test/phenol.xyz`); `[SRC: file:line]` = read directly in `pymol-src/`, `tmp/bioCHEMeleon/`, or `tmp/xtb_test/phenol_hess.log`; `[TRAIN]` = training-data knowledge, unverified here — treat as hypothesis
- **Phase to address** — phase letters follow `.planning/research/ARCHITECTURE.md` §5 build order (A skeleton, B pure core, C molecules in viewer, D game loop + input, E stacking + rules, F xtb pipeline, G spectra UI, H demo sets + polish). If roadmap renames phases, keep the relative order.

Sibling research files: STACK.md §4–6 already verified the wizard-key mechanism end-to-end and flagged the `--ohess` audit; **this file's `[RUN]` spikes close STACK.md's §6 "LOW-confidence gate"** — `vibspectrum`, `g98.out`, and `hessian` outputs are now captured and characterized (see Pitfalls 1 and 12), so the spectra-phase parser can be written against real fixtures from day one.

---

## Critical Pitfalls

### Pitfall 1: `-o --hess` silently skips the Hessian — exit 0, no error, no spectra

**What goes wrong:**
The AGENTS.md "proven pipeline" command (`xtb.exe mol.xyz -o --hess`) does NOT compute vibrational frequencies. It optimizes, exits 0, writes only optimization outputs — and the Spectra tab then has nothing to plot. There is no error message anywhere; the failure is completely silent.

**Why it happens:**
`-o/--opt` takes an optional LEVEL argument. With `-o --hess`, the parser consumes `--hess` as the opt level (falling back to "normal"), so the Hessian flag disappears. Empirically confirmed on the repo's exact binary:

- Reproduced today: `xtb.exe phenol.xyz -o --hess` → exit 0; log has NO "projected vibrational frequencies" section; output dir = only `charges, wbo, xtbopt.log, xtbopt.xyz, xtbrestart, xtbtopo.mol, .xtboptok` — identical to `tmp/xtb_test/` and `phenol_hess.log` (640 lines: the only "hessian" mentions at log:257-260, 346, 351 are the ANC *optimizer's* Lindh model Hessian, not a frequency job).
- Same input, `xtb.exe phenol.xyz --ohess` (one word) → exit 0; writes `hessian`, `vibspectrum`, `g98.out`; log prints "projected vibrational frequencies (cm⁻¹)" twice; timing block shows "analytical hessian". `[RUN]`

**How to avoid:**
- Hard rule in the xtb-bridge module: invoke `--ohess` (one-shot opt+hessian) or the two-stage `-o` then `--hess` on `xtbopt.xyz`. **Never** the two-flag spelling. Encode it as a single module-level constant so it can't drift.
- After every run, assert `vibspectrum` (and `g98.out` if mode vectors are needed) exist before declaring success; missing file → explicit user-facing error, not a crash later in the parser.
- Commit the `--ohess` outputs as parser fixtures (phenol is only ~0.7 s wall).

**Warning signs:**
A spectra run whose log lacks "projected vibrational frequencies"; a Spectra tab that opens an empty table; any run where the output dir lacks `vibspectrum`.

**Confidence & evidence:** HIGH — `[RUN]` reproduced + fixed today; `[SRC: tmp/xtb_test/phenol_hess.log:257-260,629-640]`; matches STACK.md §5 audit and xtb `--help` text (`--hess` = "on input geometry", `--ohess` = "on an ancopt(3) optimized geometry").

**Phase to address:** F (xtb pipeline) — but write the *fixtures* task first in F; the geometry/stacking phase (E) only needs `-o`.

---

### Pitfall 2: Long xtb runs on the Qt main thread freeze the whole viewer

**What goes wrong:**
The spectra calculation runs synchronously (blocking `subprocess.run` or an un-pumped QProcess wait) on the thread that runs the Qt event loop. PyMOL's entire UI — viewer redraw, dialogs, buttons — freezes for the duration. At snake sizes this is **minutes**, not milliseconds (measured scaling below).

**Why it happens:**
XTB Hessian cost grows superlinearly; measured on this machine `[RUN]`:

| Molecule | atoms | `--ohess` wall | Hessian portion |
|----------|-------|----------------|-----------------|
| phenol | 13 | 0.67 s | 0.28 s |
| π-stacked phenol dimer | 26 | 1.75 s | 1.03 s |

Hessian eigensolver ~N³ ⇒ a ~100-atom snake (PROJECT.md's safe cap) is plausibly **30–90 s of Hessian + optimization** on this box. Any block of the Qt loop during that window also coalesces/drops QTimer ticks (a stopped event loop does not deliver timer events), so the game clock and any pending UI work pile up.

**How to avoid:**
- Run xtb via `QtCore.QProcess` (STACK.md §5 choice): `start()` + `readyReadStandardOutput` → append to the progress log; `finished(int, QProcess::ExitStatus)` lands on the Qt main thread, where `cmd.*` is legal. Never `waitForFinished()`.
- Fallback (documented, v1-acceptable only with a "calculating… viewer paused" notice): blocking run + `QApplication.processEvents()` pump. Prefer QProcess; the fallback silently reintroduces Pitfall 2.
- Show a cancel button wired to `QProcess::kill()`; disable the Get-Spectra button while a run is in flight (re-entrancy guard).

**Warning signs:**
Viewer rotation stops responding during "Get Spectra"; the Spectra log updates in huge chunks instead of streaming; the elapsed timer jumps after the run.

**Confidence & evidence:** HIGH for the freeze mechanism (modal/synchronous work blocks the Qt loop — `[SRC: bioCHEMeleon/biochemeleon/gui_game.py:289-304]` Bug-A/B/C notes; v1 Pitfall 6 in bioCHEMeleon gui_game.py:6-7 "NEVER threading.Thread with cmd.*"); HIGH for the timing numbers (`[RUN]`); MEDIUM for exact 100-atom runtime (extrapolation).

**Phase to address:** F (pipeline), UX surface in G.

---

### Pitfall 3: xtb sprays ~10 files into its CWD and reports success/failure on **stderr**, not stdout

**What goes wrong:**
Three related mistakes when shelling out to xtb:

1. **CWD pollution / wrong-dir reads:** xtb writes its outputs into the *current working directory* — measured file set `[RUN]`: `xtbopt.xyz, xtbopt.log, xtbrestart, charges, wbo, xtbtopo.mol, .xtboptok` (+ `hessian, vibspectrum, g98.out` for `--ohess`, + `xtbout.json` with `--json`). If the plugin launches xtb with PyMOL's session dir as CWD, the user's folder gets littered and a *stale* `vibspectrum` from a previous run can be read as if it were this run's.
2. **Success/failure detection from stdout:** on success xtb prints `normal termination of xtb` **to stderr** (stdout does not carry it); on failure it prints `abnormal termination of xtb` to stderr with exit code **128** (observed for an unknown element; xtb uses several non-zero codes), while the pretty diagnostic (file:line, "unknown element") goes to **stdout**. A `stderr-empty-means-success` heuristic, or `returncode == 1` check, misclassifies both directions.
3. **Quoting/robustness:** invoking via a single shell string breaks on paths with spaces (`C:\Program Files\...`).

**How to avoid:**
- Always launch with `cwd=` a **fresh per-run temp dir** (`tempfile.mkdtemp()`, STACK.md §5) and bare relative filenames as arguments; write the snake `.xyz` there; parse outputs there; delete the dir after copying what you need. Optionally use xtb's `--namespace serp` (verified in help by STACK.md §5) to make outputs unambiguous.
- Success contract (encode in the bridge module): `exitcode == 0` **AND** stderr contains "normal termination" **AND** expected output files exist. Anything else → failure path with stdout tail shown to the user.
- `subprocess`/`QProcess` with **list arguments** (no shell); resolve the xtb binary path once (probe configured path → `shutil.which("xtb.exe")` → `shutil.which("xtb")` — the AGENTS.md xtb/xtb.exe detection rule) and reject paths containing quotes.

**Warning signs:**
Mystery `.xtboptok`/`charges` files appearing next to the user's `.pse`; a spectra run that "succeeds" but plots a previous molecule's spectrum; error dialogs that show nothing useful.

**Confidence & evidence:** HIGH — all three behaviors `[RUN]` today (including a deliberately corrupted input: exit 128, `abnormal termination of xtb` on stderr, miet-sim diagnostic on stdout).

**Phase to address:** F. Unit-test the success-contract function in the pure layer with captured fixtures.

---

### Pitfall 4: Arrow keys — frame-stepping conflict, focus capture, and leaked global rebinds

**What goes wrong:**
Three distinct arrow-key failure modes:

1. **Default conflict:** PyMOL's documented default for LEFT/RIGHT arrows is "go backward or forward one frame" (`[SRC: pymol-src/modules/pymol/helping.py:320-322]`). If the snake object (or the pickups) is ever multi-state, un-rebound arrows flip states mid-game instead of steering.
2. **Focus:** keys only reach the PyMOL key pipeline when the PyMOL main window (3D viewer) has focus. Clicking the plugin dialog (or its command-line edit box, where Up/Down are command history — `[SRC: pmg_qt/pymol_qt_gui.py:423]`) silently steals steering; the player experiences "the game is broken".
3. **Leaked rebinds:** whatever capture mechanism is used (Wizard `do_special` per STACK.md §4, or `cmd.set_key`), teardown paths (crash, mid-game plugin close, win-without-cleanup) can leave the game's key handling installed. `cmd.set_key` mutates the **global** `cmd.key_mappings` for the whole session — a leaked mapping permanently breaks the user's arrow keys even outside the game.

**How to avoid:**
- Prefer the verified Wizard mechanism (STACK.md §4: Qt forwards arrows as "special" keys, C layer calls `WizardDoSpecial` **first**, truthy return grabs the key). If `do_special` returns None for non-game keys, PyMOL defaults still work. **Mandatory:** override `get_event_mask()` to include `event_mask_key + event_mask_special` (4+8) — the base class returns pick+select only (`[SRC: pymol/wizard/__init__.py:8-9,55-56,82-86]`); miss this and `do_special` never fires.
- If `cmd.set_key('left'/'up'/'right'/'down', fn)` is used as fallback: valid keys are verified (`[SRC: pymol/internal.py:400-410]` `special_key_codes` includes 100:left, 101:up, 102:right, 103:down — note the `set_key` docstring at controlling.py:760-763 omits up/down, but the validation code accepts them). Save the previous mapping for each key at install time and restore it in **every** teardown path (win, lose, pause-to-setup, plugin reload, error abort).
- Known cosmetic side effect (accepted, document in Help): UP/DOWN always also reach the command-line history (`OrthoSpecial`) — the command line text churns but gameplay is unaffected (STACK.md §4.4).
- Instruct focus explicitly: wizard prompt/panel (`get_prompt()`/`get_panel()`, `[SRC: wizard/__init__.py:49-53]`) says "click the 3D viewer, then steer with arrow keys"; auto-pause when the plugin dialog gains focus (Qt focus event on the dialog → pause) so stolen focus can't kill the snake.

**Warning signs:**
Steering works only right after clicking the viewer; arrow keys step a state/frame counter in the PyMOL console after the game ends; two games in one session behave differently (first left rebinds, second doesn't — leak from run 1).

**Confidence & evidence:** HIGH for defaults, key codes, wizard hooks, and the event-mask requirement (`[SRC]` above; STACK.md §4 additionally verified the C-layer dispatch order). MEDIUM for the OrthoSpecial side effect (STACK.md-verified; C code not in this repo's pymol-src).

**Phase to address:** D (input), with teardown-restore enforced in E and the "Looks Done" checklist.

---

### Pitfall 5: Modal dialogs during play block the Qt event loop — frozen viewer, and a redraw you never see

**What goes wrong:**
`QMessageBox.exec_()` (or any modal) on the main dialog stops the Qt event loop: the 3D viewer stops redrawing, QTimer ticks stop (game clock and movement halt silently), and any `cmd.*` change issued just before the modal never becomes visible.

**Why it happens:**
bioCHEMeleon shipped exactly this bug class and fixed it in three places (`[SRC: bioCHEMeleon/gui_game.py:289-344]`, Bug A/B/C): (A) the last `cmd.color('green')` was invisible because the win modal blocked before the redraw landed — fix: `cmd.refresh()` + `QTimer.singleShot(100, …)` before the modal; (B) dialogs vanished *behind* the OpenGL window — fix: parent = `self.window()` + `WindowStaysOnTopHint`; (C) cleanup ordering around the modal. The main plugin dialog must stay **modeless** (`dialog.show()`, never `.exec_()`) for the viewer to stay interactive at all (`[SRC: bioCHEMeleon/__init__.py:141-153]`, grep-enforced gate).

**How to avoid:**
- Main dialog: modeless forever (keep bioCHEMeleon's grep gate as a repo check: `grep -rnE "\.exec_\(\)"` must only hit child dialogs).
- Child modals (QMessageBox/QFileDialog/QColorDialog on children) are allowed — but never during active gameplay without pause: entering any modal path from the game tab should pause the tick timer first, and rebase wall-clock timers afterwards (bioCHEMeleon's `_on_save` stop → `time.time() - elapsed` rebase → restart pattern, `[SRC: bioCHEMeleon/__init__.py:745-788]`).
- Before every modal that follows a `cmd.*` visual change: `cmd.refresh()` then 100 ms `singleShot` (verified pattern).
- Elapsed-time math must be delta-based (`time.time() - start_time`), never accumulated tick counts — tick coalescing during any block would otherwise undercount.

**Warning signs:**
Win/game-over dialogs appear before the final frame is visible; the timer "loses" seconds equal to dialog-open time; the viewer freezes when a confirmation pops up mid-run.

**Confidence & evidence:** HIGH — `[SRC]` verified fixes shipped in the prior game; same Qt model here.

**Phase to address:** A (dialog scaffolding + grep gate), D/E (pause semantics), G (pre-modal redraw before showing results).

---

### Pitfall 6: `cmd.*` from a worker thread — the hard threading rule

**What goes wrong:**
Calling any `cmd.*` API from a `threading.Thread` (or QThread) corrupts PyMOL state or deadlocks: the Python API is guarded by a single lock (`[SRC: pymol/locking.py:26-40,80]` `lock/lock_attempt/unlock/is_gui_thread`), and a worker holding it while the C render thread wants it (or vice versa) freezes the viewer. This is v1's documented "Pitfall 6: NEVER threading.Thread with cmd.*" (`[SRC: bioCHEMeleon/gui_game.py:6-7]`).

**Why it happens:**
It looks natural to "download/calculate in a background thread and update the molecule when done". Any `cmd` call inside that thread violates the single-threaded API contract.

**How to avoid:**
- The Qt main thread owns **all** `cmd.*` and all Qt widget mutation. Workers (download, xtb via QProcess — which needs no thread at all) exchange data only via `queue.Queue`, drained by a recursive `QTimer.singleShot` on the main thread — the verified pattern in bioCHEMeleon `_resolve_large_demo` (`[SRC: bioCHEMeleon/__init__.py:545-677]`: stdlib-only worker, modeless QProgressDialog, main-thread drain, `cmd.*` only in the 'done' branch).
- Prefer **QProcess signals over threads** for xtb (STACK.md §5): `finished` arrives on the main thread; no worker exists to misuse.
- Optional belt-and-braces: `assert cmd.is_gui_thread()` at the entry of cmd-touching slots (`[SRC: locking.py:80]`).

**Warning signs:**
Intermittent freezes during spectra; `CmdException`s about locks; errors that only appear under load.

**Confidence & evidence:** HIGH — verified pattern + source refs; the QProcess upgrade is STACK.md-verified (`pymol.Qt` exports QtCore, `[SRC: pymol/Qt/__init__.py:28]` per STACK.md).

**Phase to address:** F (pipeline), A (establish the drain pattern skeleton early).

---

### Pitfall 7: Plugin module identity — the double-singleton trap (two live copies of "the" singleton)

**What goes wrong:**
PyMOL imports plugins as **`pymol.plugins.startup.<name>`**, not as the bare package name (`[SRC: pymol/plugins/__init__.py:423-430]` `mod_name = parent.__name__ + '.' + name`; `installation.py:339` `prefix = startup.__name__`; load via `__import__(self.mod_name)`, `__init__.py:277`). If the same code becomes importable under a **second name** — bare `serpentrum` (sys.path leakage, dev `run`-script experiments, tests importing the package directly, the staged dev copy under `tmp/`) — Python creates a **second module object** with its own module-level globals. Consequences:

> CORRECTED 2026-09-06 (phase-1 research [RUN] probe): the actual sys.modules key is pmg_tk.startup.<name>; pymol.plugins.startup is an attribute alias to the same module object. See phases/01-plugin-skeleton-purity-harness/01-RESEARCH-skeleton.md § correction.

- The `dialog = None` module singleton (`[SRC: bioCHEMeleon/__init__.py:3-5]`) exists twice → two plugin windows can be opened; each has its **own** GameController; both drive the same viewer objects.
- Plugin Manager **reload** (`[SRC: pymol/plugins/__init__.py:274-275]` `reload(self.module)`) re-executes the module: fresh globals, `dialog = None` again, while the old dialog is still on screen → the next menu click opens a **second** dialog, and the orphaned one still holds a live controller/timer.

**Why it happens:**
Module-level singletons are keyed by module object identity, and PyMOL's plugin namespace guarantees the *first* identity is not the bare name.

**How to avoid:**
- Put the plugin menu entry + singleton in `__init__.py` exactly like bioCHEMeleon, but **anchor live state outside module globals**: attach the singletons to a stable object that survives re-import, e.g. `pymol` package or `cmd._pymol.session` (`getattr(pymol, '_serpentrum_state', None)` accessor used by every module). Then module reload / double import cannot duplicate the controller.
- Dev-rule: tests and smokes import the package under ONE canonical name only; never add the repo root to `sys.path` at runtime; never `import serpentrum` from inside the plugin.
- On `__init_plugin__`, defensively detect and adopt an existing instance: if `sys.modules` already holds the plugin under another name with a live `dialog`, reuse/re-export instead of constructing a second dialog.

**Warning signs:**
Two plugin windows after using the Plugin Manager; "game already started" errors with no visible game; timer ticks applied twice per second (two controllers driving one scene).

**Confidence & evidence:** HIGH for the import/reload mechanics (`[SRC]` above); MEDIUM-HIGH for the failure modes (direct inference from singleton pattern + module semantics; the class of bug was the reason AA-match documented module-identity rules).

**Phase to address:** A (skeleton) — must be built in from the first commit; retro-fitting state anchoring after GUI code exists is painful.

---

### Pitfall 8: Qt dialog lifetime vs PyMOL session — GC, reload orphans, and `.pse` desync

**What goes wrong:**
Three lifetime mistakes around the plugin dialog:

1. **GC flash:** storing the dialog in a local variable → it flashes and vanishes (garbage-collected). The singleton must live at module scope (`[SRC: bioCHEMeleon/__init__.py:3-5]` comment; mitigated further by Pitfall 7's state anchoring).
2. **Orphans after reload:** Plugin Manager reload (Pitfall 7) leaves a visible, orphaned dialog; new code constructs a second one. Also: any timer owned by an orphaned dialog keeps firing against stale state.
3. **`.pse` session desync:** saving a session keeps **all viewer objects** (the game's box CGO, snake, pickups, vector CGO) but **no plugin Python state** (v1-verified: ".pse doesn't save plugin Python state", bioCHEMeleon v1→VMD carry-over matrix row 6). After File→Open Session: game objects litter the scene, no controller exists to clean them, arrow rebinds are gone but the user expects a playable game.

**How to avoid:**
- Singleton + state anchoring (Pitfall 7); on new-dialog construction, scan `QApplication.topLevelWidgets()` for an existing instance of the class and re-show it instead of building a new one.
- Name every game-created object with one prefix (STACK.md Pattern 4 namespace, e.g. `serp_*`) and give the **Cleanup model** button the ability to delete `name serp_*` + restore user objects from the pre-game backup (v1 backup/restore pattern, `[SRC: bioCHEMeleon/backup.py]`). This makes post-session-reload scenes recoverable with one click — even in a fresh PyMOL process where the plugin state never existed.
- On completion (win/lose→spectra flow) delete or fold transient game objects promptly; never rely on "the user will clean up".
- Timers: stop in `closeEvent`/destructor of the dialog; a stopped UI must never leave a `singleShot` chain armed (see Pitfall 9's epoch guard).

**Warning signs:**
Empty-looking scene after opening a saved session with stray sticks/spheres; "Cleanup" does nothing because the controller is None; two dialogs after Plugin Manager reload.

**Confidence & evidence:** HIGH (1, 2 — verified mechanics); HIGH (3 — v1-verified experience; session-saves-CGO-objects is standard PyMOL behavior, MEDIUM).

**Phase to address:** A (singleton/anchor + naming convention), C/E (cleanup button semantics), H (polish pass).

---

### Pitfall 9: Game-state desync on pause / restart / cleanup — epoch guards and teardown ordering

**What goes wrong:**
The continuous snake loop adds state-machine hazards the click-to-find game never had:

1. **Countdown double-fire:** the 3-2-1 countdown is a `QTimer.singleShot` chain (`[SRC: bioCHEMeleon/gui_game.py:258-264]`). singleShot chains **cannot be cancelled** — pressing Restart (or Start twice) during the countdown leaves the old chain alive; it fires `_begin_play` a second time → two wizards / two timers / duplicated state.
2. **Teardown order:** bioCHEMeleon hit this exactly: starting a new round without deactivating the previous wizard corrupted `mouse_selection_mode` and orphaned the wizard (`[SRC: bioCHEMeleon/__init__.py:516-534]` fix comments). The snake equivalent: new round without stopping the old QTimer + deactivating the old wizard + deleting old CGO objects → moving snake plus phantom snake.
3. **Pause asymmetry:** pause stops the tick timer but the wall-clock elapsed timer (delta-based) keeps counting; resume without rebase inflates elapsed time. Conversely "pause" that only stops rendering but not the pure-engine tick leaves collisions accumulating.
4. **No undo:** PyMOL open-source has **no undo** (`[SRC: bioCHEMeleon/AGENTS.md:81]`, editor.py:25-36 stub) — any destructive restart/cleanup op needs the v1 snapshot/restore backup pattern, or (better for the snake) only delete game-owned `serp_*` objects and never touch user molecules.

**How to avoid:**
- **Epoch counter:** a monotonically increasing `self._epoch`; every `singleShot` callback closes over the epoch it was scheduled with and no-ops if `epoch != self._epoch`. Bump epoch on every start/restart/cleanup. This is the only reliable cancellation for singleShot chains.
- **One teardown helper** (`_teardown_round()`: stop tick timer → deactivate wizard → save/restore key mappings → delete `serp_*` objects → reset engine state) called by EVERY path (Restart, Start-mid-game, Cleanup, win, lose, error).bioCHEMeleon's final architecture does this in four separate places; centralize it from day one.
- Engine owns truth (STACK.md Pattern 3): pause = engine `paused` flag (tick becomes no-op) + timer stop; resume = rebase `start_time` then timer start.
- Never mutate user molecules mid-game (STACK.md §3: game owns synthetic objects) — this deletes the entire v1 id/index/sentinel bug class by construction.

**Warning signs:**
Two snakes moving after fast Start/Restart; countdown continuing after Cancel; elapsed timer exceeding played time; `mouse_selection_mode` still at game value after quitting.

**Confidence & evidence:** HIGH — (1) singleShot non-cancellability is standard Qt (MEDIUM-HIGH); (2), (4) `[SRC]` verified in bioCHEMeleon; (3) follows from the verified delta-timer pattern.

**Phase to address:** D (loop + lifecycle), E (restart/cleanup completion), A (epoch pattern in skeleton).

---

### Pitfall 10: Stacking geometry — clash-free appends are a **hard prerequisite for valid xtb input**, not just cosmetics

**What goes wrong:**
- **Spurious covalent bonds → garbage hessian.** xtb infers bonds from distances (rcov-based). If a chain-appended molecule lands too close to the previous segment (clash), xtb bridges them covalently and the "spectrum of your stacked snake" becomes the spectrum of a wrong covalent polymer. Verified safe margin `[RUN]`: a π-stacked phenol dimer at **3.4 Å** optimized cleanly (`normal termination`; bond list contains *only* intra-molecular bonds — no C···C bridge across the 3.4 Å gap; gap stayed 3.40→3.44 Å after optimization, i.e. GFN2 preserves the stack). At game-geometry distances this is safe; at clash distances it is silently catastrophic.
- **Boundary poke-through:** appending at a known stacking distance from a head near the box wall puts the new molecule partly outside the displayed box → collision with the boundary happens "after" the stack visually, and the final xtb input extends beyond the promised domain.
- **Opt drift:** `--ohess` optimizes *everything*, including inter-molecular degrees of freedom. Verified benign for π-stacking (above), but other stacking modes (H-bonded pairs, edge-to-face) may translate/rotate during opt, moving the snake away from what the player built. The spectra are of the **optimized** snake (xtbopt.xyz), which is scientifically correct but visually different from the played structure.

**How to avoid:**
- After each stack placement, run a pure-layer minimum-interatomic-distance check (new molecule vs. every existing segment AND vs. box walls) with a conservative threshold; on violation, reject the pickup placement direction (game-rule response: treat as obstacle / re-place), never silently accept a clashing append.
- Compute stacking transforms in the pure layer (numpy rigid-body: known mode + distance → rotation+translation), apply via `cmd.translate`/`cmd.rotate` per STACK.md §3; unit-test the math headlessly in WSL.
- Feed xtb the exact combined coordinates via a single `.xyz` the plugin writes (xyz = symbols+coords only; no bonds — let xtb infer, which is safe **only if** the clash gate passed).
- In the Spectra tab, show both geometries' availability honestly: plot/parse from the optimized output (xtbopt.xyz), and state "geometry optimized before spectra" in the log (educational framing, no silent substitution).

**Warning signs:**
xtb log's bond list crossing molecule boundaries (`O12-C14`-style links); spectra run "succeeds" but frequencies look like a covalent dimer; stacked molecule visibly halfway through the box wall.

**Confidence & evidence:** HIGH for the verified dimer behavior and bond-inference risk mechanism (`[RUN]`); MEDIUM for other stacking modes (only π-stack verified — PROJECT.md already gates non-π modes on research + user approval).

**Phase to address:** E (stacking + rules — clash gate is a game rule, not a spectra afterthought).

---

### Pitfall 11: Input molecule hygiene — missing hydrogens, wrong charges, and the silent wrong-electron-count failure

**What goes wrong:**
- **Missing H:** user-supplied SDF/mol2 files frequently lack explicit hydrogens. xtb runs anyway (no error) but computes the spectrum of the wrong electron count → garbage frequencies presented as real chemistry. The failure is silent.
- **Charges:** mol2 files carry **partial** charges only (`[SRC: chempy/mol2.py:74]`); formal charges survive only from SDF's `M  CHG` records (`[SRC: chempy/mol.py:74-81]`). xtb needs the **total** molecular charge (`--chrg`); default 0 is wrong for ionic groups (COO⁻, NH₃⁺). PyMOL's `cmd.h_add` (`[SRC: pymol/editing.py:1216]`) is geometric-rule-based and unreliable for arbitrary organics — auto-adding H can produce wrong structures that look fine.
- **Odd electrons:** a malformed input can yield an odd valence-electron count (open shell) — xtb will treat it as a radical; spectra differ silently.

**How to avoid:**
- **Validation gate in the pure layer at load time** (Setup tab): every demo/user molecule must (a) contain explicit H (reject or demand a pre-protonated file — do NOT auto-add), (b) carry a declared total charge (default 0; ionic demo entries declare theirs), (c) have ≤3 rings (PROJECT.md scope).
- **Post-hoc sanity check against xtb's own numbers:** the log prints the valence electron count (`[SRC: phenol_hess.log:470 area — "# electrons 36"`, = C 4×6 + H 1×6 + O 6 ✓) and `unpaired electrons 0`. Before plotting, assert even electrons (unless declared radical) and unpaired==0; mismatch → user-facing warning with the molecule name, not a silent plot.
- Compute snake total charge as the sum of loaded molecule charges; pass `--chrg <sum>` only when non-zero (avoid touching defaults for the common neutral case).
- Prefer SDF over mol2 for the demo library (formal-charge fidelity + simpler parsing); document the choice in DATA_SOURCES.md.

**Warning signs:**
xtb log electron count ≠ hand-computed valence count; "unpaired electrons: 2" in a closed-shell set; spectra of what is visually the same molecule differing between runs.

**Confidence & evidence:** HIGH for parsing behavior (`[SRC]`), HIGH for the electron-count check (`[SRC: phenol_hess.log]`); MEDIUM for `cmd.h_add` unreliability (community experience, `[TRAIN]`) — the recommendation stands regardless since we don't auto-add H.

**Phase to address:** C (load/validation), E (charge aggregation into the snake), F (electron-count assertion before plotting).

---

### Pitfall 12: Hessian/spectrum parsing edge cases — trivial-mode counts differ (6 vs 5), negatives are real, and g98.out is the mode-vector source

**What goes wrong:**
Parser assumptions that hold for phenol break elsewhere:

1. **Trivial (trans/rot) mode count is NOT constant.** `vibspectrum` lists all 3N modes. Nonlinear molecules: **6** near-zero rows first (verified phenol: modes 1–6 at ±0.00, empty symmetry, `-` selection rule). **Linear molecules: 5** (verified CO₂ `[RUN]`: log prints `linear (good luck) true`; vibspectrum has 5 zero rows, vibrations start at mode 6, doubly-degenerate bend at 600.18 twice). A parser hardcoding "skip 6" silently misassigns mode indices for linear molecules — and the frequency-table→vector mapping (clicked row ≠ shown vector) is the worst version of this bug because it's off-by-one *visually correct-ish*.
2. **Negative frequencies are normal, not errors.** Phenol's `--ohess` g98.out shows −31.92, −23.08, −18.11 cm⁻¹ (soft modes at a not-perfectly-converged minimum). Imaginary modes print as negative wavenumbers. Filtering them out entirely hides chemistry; plotting them naively at face value puts spikes at "negative cm⁻¹".
3. **Zero-intensity / inactive modes exist.** Verified CO₂ symmetric stretch: intensity 0.00000, selection rule "NO" — must appear in the frequency table but contributes nothing to the broadened IR curve.
4. **g98.out layout:** frequencies+intensities+vectors come in blocks of **3 columns** (`Frequencies --`, `IR Inten --`, then `Atom AN X Y Z …` triplets) — N mod 3 remainder blocks and more-atoms-than-columns layouts must be handled; `vibspectrum` does **not** contain displacement vectors, so the clicked-row→viewer-vector feature (PROJECT.md Spectra requirement) **must parse g98.out** (fallback: `hessian` file + numpy `eigh` with mass-weighting and trans/rot projection — much more code; avoid unless g98.out proves insufficient).
5. **Degenerate duplicates:** degenerate modes produce identical frequency rows (verified CO₂ 600.18 twice) — table display may want to group them; the plot simply sums them.

**How to avoid:**
- Pure-module parser (stdlib+numpy) unit-tested against **real captured fixtures** — commit today's `[RUN]` outputs (phenol + CO₂ `--ohess`: `vibspectrum`, `g98.out`, `hessian`) as test fixtures; write the parser to match reality, not documentation.
- Trivial-mode filter: drop rows with |freq| below a threshold (~10–20 cm⁻¹) **or** empty-symmetry+`-` selection rule; do NOT hardcode a count (6 vs 5).
- Negatives: keep in the table (display as e.g. "−31.9i" with an explanatory note — educational value); clamp/exclude from the broadened plot below the axis minimum.
- Intensity-0 modes: include in table, contribute 0 to the curve (trivially correct in a sum-over-Gaussians implementation).
- g98.out block parser: iterate in column-groups of 3; handle the remainder block; index modes identically to the table (mode numbers from `vibspectrum` are 1-based and consistent with g98.out ordering — verify the index correspondence in the fixture test, since Pitfall 12.1's off-by-one lives exactly there).

**Warning signs:**
Frequency table starting at a nonzero frequency for a linear molecule; clicked row highlights vectors for the wrong-looking motion; spectrum plot axis extending below 0; a molecule with 3N−5 table rows but 3N−6 expected.

**Confidence & evidence:** HIGH — every claim `[RUN]`-verified today against real xtb 6.7.1 output (phenol + CO₂); g98.out `Atom AN X Y Z` vector blocks verified present (`[RUN]`).

**Phase to address:** F (fixtures + parser), G (table/plot/vector rendering).

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Blocking `subprocess.run` for xtb instead of QProcess | 10 lines less code | Pitfall 2 freeze; rework of the whole Spectra flow later | Never for the real pipeline; OK for a phase-F spike behind a flag |
| Hardcoding "skip first 6 vibspectrum rows" | Parser done in 20 min | Linear molecules misindex modes (Pitfall 12.1) | Never |
| Module-global controller/dialog state without anchoring | Fast skeleton | Reload/double-import dup (Pitfall 7); painful retrofit | Never (anchor from day one — it's ~10 lines) |
| Separate teardown code per button | Quick to write each time | Desync bugs (Pitfall 9.2) multiply with every new path | Never — one `_teardown_round()` |
| `get_model()` per tick for collision checks | Easy code | O(N) Python-object copy every tick; GC churn at 6–10 fps | Only if N is tiny and measured cheap; prefer pure-engine state + `get_atom_coords` for one-off reads (`[SRC: querying.py:881]`) |
| Parsing stdout for xtb success | Feels natural | stderr/exit-code contract missed (Pitfall 3.2) | Never |
| Auto-adding H with `cmd.h_add` | Handles sloppy user files | Wrong structures, wrong spectra, misleading education (Pitfall 11) | Only behind an explicit, user-visible "protonated by rules — verify!" warning; default reject |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| xtb (Windows exe) | Two-flag `-o --hess`; running in session CWD; trusting stdout | `--ohess` (or two-stage); per-run temp dir CWD; exit-code + stderr + output-files contract (Pitfalls 1, 3) |
| xtb env | Ignoring OpenMP | xtb grabs all cores by default (measured cpu/wall ≈ 3.7–4.9 → ~4 threads `[RUN]`); consider `OMP_NUM_THREADS` capping so PyMOL rendering stays smooth during spectra (`[TRAIN]` MEDIUM); `OMP_STACKSIZE` for large-system eigensolver crashes is `[TRAIN]` LOW — verify in F with the real ~100-atom snake before relying on it |
| xtb binary detection | Assuming `xtb` name everywhere | Probe configured path → `which("xtb.exe")` → `which("xtb")` (AGENTS.md rule); note the repo uses the 6.7.1 **Windows pre-release** because 6.7.0's Windows build misses a DLL (PROJECT.md) — pin and log the detected version |
| WSL↔Windows (dev only) | Converting paths at plugin runtime | Runtime needs **no** conversion (Windows PyMOL + Windows exe, temp dir + relative names); conversion is only for dev-side headless smokes (`to_windows_path` pattern, `[SRC: bioCHEMeleon/demos.py:59-74]`) |
| PyMOL Plugin Manager | Assuming module name == package name | Loads as `pymol.plugins.startup.<name>`; supports package plugins (dir with `__init__.py`, `[SRC: pymol/plugins/__init__.py:365-390]`); reload re-executes module (Pitfall 7) |
| Qt inside PyMOL | `from PyQt5 import ...` | Always `from pymol.Qt import QtWidgets` (auto PyQt5/PySide2); repo grep gate (bioCHEMeleon AGENTS.md) |
| PyMOL sessions | Assuming plugin state survives `.pse` | Only viewer objects survive; Cleanup-by-name-prefix is the recovery path (Pitfall 8.3) |
| numpy for broadening | Importing scipy/matplotlib | numpy ships with PyMOL (constraint); matplotlib does NOT — plot via custom `QWidget.paintEvent`/`QPainter` (STACK.md §6 verified precedents) or seek user approval + vendoring |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Hessian cost ~N³ vs the win cap | Spectra runs take minutes; users raise the cap | Atom-budget guard before xtb (PROJECT.md cap ~100 atoms, warning when raised); show estimated scale in UI | Breaks in user-perceived time beyond ~150 atoms |
| CGO rebuild per tick of a growing snake | Late-game stutter | Rebuild is cheap (few hundred floats ≤100 segments); measure before optimizing; never rebuild *user* molecules | Only if per-tick cmd chatter grows with O(snake) cmd calls — batch into ONE `load_cgo` |
| Per-tick `cmd.get_model` | GC churn, rising tick latency | Pure engine state; `cmd.get_atom_coords`/`iterate_state` only for absolute positions (`[SRC: bioCHEMeleon/AGENTS.md:98]` — plain `iterate` has no x/y/z) | From day one at 6–10 fps |
| xtb default thread grab | UI jank during spectra | `OMP_NUM_THREADS` cap (Pitfall/gotcha above) | Multi-core machines, during G |
| Modal-heavy UX | Frozen-feeling app | Modeless main dialog + pause-before-modal discipline (Pitfall 5) | Everywhere, immediately |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Building the xtb command as a shell string with user-supplied path | Command injection / breakage on spaces & quotes | List-args subprocess/QProcess; validate the configured binary path (exists, is file, no quotes); never `shell=True` |
| Running xtb in a user-chosen directory | Overwrites user files (`xtbopt.xyz`, `charges` in CWD) | Per-run temp dir (Pitfall 3.1) |
| Loading arbitrary user SDF/mol2 without checks | Parser exceptions crash the dialog; malformed files → weird chemistry | Load in try/except with user-facing message; validate atom count/rings/H before accepting (Pitfall 11) |
| Vendoring third-party libs without license note | License violation (repo rule) | `3rd_party_lib/` + license file + user approval (PROJECT.md constraint) |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Keys "don't work" after clicking the plugin dialog | Game feels broken | Wizard prompt "click the 3D viewer"; auto-pause on dialog focus (Pitfall 4.2) |
| Spectra silently showing another molecule's spectrum (stale files, Pitfall 3) | Wrong chemistry taught | Per-run temp dir + file-exists assert + log the parsed filename & molecule atom count |
| Negative frequencies hidden or crashing the plot | Confusion / exception | Show "−31.9i" in table with a one-line explanation (educational moment, Pitfall 12.2) |
| Optimized snake differs from played snake without explanation | Distrust of the tool | Log line "geometry optimized (RMSD …) before spectra" (Pitfall 10) |
| No feedback during minutes-long hessian | Users think it hung | Streaming QProcess stdout → log widget; indeterminate progress + cancel (Pitfall 2) |

## "Looks Done But Isn't" Checklist

- [ ] **Spectra feature:** works with `--ohess` fixtures — verify a real `vibspectrum`/`g98.out` was parsed, not a stub (Pitfall 1)
- [ ] **Linear molecule support:** run the parser against a linear fixture (CO₂) — verify 5-trivial-mode handling and table→vector index match (Pitfall 12.1)
- [ ] **Arrow-key teardown:** after win/lose/quit/plugin-reload, LEFT/RIGHT restore prior behavior — verify by pressing arrows post-game and checking no frame-step hijack or leaked mapping (Pitfall 4.3)
- [ ] **Restart during countdown:** no double snake/wizard — verify epoch guard (Pitfall 9.1)
- [ ] **Cleanup after session save/reload:** stray `serp_*` objects removable in a fresh process — verify Cleanup works with `controller is None` (Pitfall 8.3)
- [ ] **Plugin Manager reload:** only one dialog, one controller — verify after reload (Pitfall 7)
- [ ] **Charged/odd-electron input:** validation gate fires — verify with a deliberately H-less and an ionic test file (Pitfall 11)
- [ ] **Cancel during hessian:** process killed, temp dir removed, UI re-enabled — verify (Pitfall 2/3)
- [ ] **Clash gate:** append onto a head near a wall/corner — verify rejection, not out-of-box stacking (Pitfall 10)
- [ ] **Modeless discipline:** grep gate `\.exec_\(\)` only on child dialogs (bioCHEMeleon AGENTS.md gate, carried into this repo)

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| 1 (`-o --hess`) | LOW | Switch constant to `--ohess`; re-run (seconds at fixture sizes) |
| 2 (freeze) | MEDIUM | Refactor to QProcess signals; keep progress log; re-test cancel path |
| 3 (cwd/stderr) | LOW | Bridge-module contract change; delete polluted files; re-run |
| 4 (leaked keys) | LOW–MEDIUM | Restore saved mappings; restart PyMOL clears global key state if needed |
| 5 (modal) | LOW | Insert refresh+100ms pattern; add pause-before-modal |
| 6 (thread cmd) | HIGH | Full rework of the offending path to queue+drain; prevention is cheap, recovery is not |
| 7 (double singleton) | MEDIUM | Anchor state on stable object; re-audit all module-global mutables |
| 8 (.pse desync) | LOW | Cleanup-by-prefix run manually; improve auto-cleanup timing |
| 9 (desync/epoch) | MEDIUM | Centralize teardown; add epoch; regression-test restart matrix |
| 10 (clash→bonded) | LOW | Re-run spectra after gate fix; geometry inputs were garbage, nothing persisted |
| 11 (wrong H/charge) | LOW | Fix input file/validation; re-run |
| 12 (parser) | MEDIUM | Fix parser against fixtures; re-verify table↔vector indexing |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| 1 `--ohess` | F (fixtures task first) | Fixture commit + parser test green |
| 2 UI freeze | F | Manual: rotate viewer during spectra; cancel works |
| 3 cwd/stderr contract | F | Pure-layer unit tests vs captured fixtures (success + exit-128 cases) |
| 4 arrow keys | D (capture), E (restore) | Post-game arrow check; Plugin-reload check |
| 5 modal discipline | A (gate), D/G | Grep gate + win-dialog visibility test |
| 6 thread rule | A (pattern), F | Code review gate; no `threading.Thread` touching cmd |
| 7 module identity | A | Reload + double-open test |
| 8 dialog/session lifetime | A, C, E | Session save/reload + Cleanup test |
| 9 state desync | A (epoch), D/E | Restart-during-countdown matrix |
| 10 stacking clash | E | Near-wall append rejection test; xtb bond list sanity on a 2-mer |
| 11 molecule hygiene | C (validate), F (electron assert) | H-less + ionic fixture rejections |
| 12 parser edge cases | F (fixtures/parser), G (UI) | CO₂ + phenol fixture tests; clicked-row vector match |

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| A skeleton | Pitfalls 7, 8, 5 | Anchor state; modeless gate; epoch pattern from commit one |
| C molecules | Pitfall 11 | Load-time validation gate (pure layer) |
| D game loop + input | Pitfalls 4, 9, 5 | Wizard mask override; epoch guard; pause-on-focus-loss |
| E stacking + rules | Pitfalls 10, 9, 4-restore | Clash gate; centralized teardown; key-mapping restore |
| F xtb pipeline | Pitfalls 1, 2, 3, 6, 11-assert, 12-fixtures | `--ohess` constant; QProcess; temp-dir contract; fixtures committed first |
| G spectra UI | Pitfalls 12, 2, 5 | Fixture-driven parser tests; streaming log; pre-modal redraw |
| H polish | Pitfalls 8, 4, UX table | Cleanup-by-prefix in fresh process; Help text for focus + negatives |

## Open Questions (need phase-specific / human verification)

- `OMP_STACKSIZE` necessity for ~100-atom hessian (crash risk in eigensolver) — `[TRAIN]` LOW; verify in F with a real capped-size snake.
- Exact 100-atom `--ohess` wall time on this machine (drives the atom-cap warning thresholds) — measure in F.
- g98.out mode ordering vs `vibspectrum` mode numbering for >3N columns layouts — confirm index correspondence in the fixture test (Pitfall 12.5).
- Non-π stacking modes (H-bond, edge-to-face): opt-stability unverified — only π-stack proven `[RUN]`; PROJECT.md already requires research + user approval per mode.
- QProcess availability/behavior in the Windows conda PyMOL build (STACK.md §5 fallback documented) — spike early in F.

## Sources

- `[RUN]` spikes executed 2026-09-06 in `/tmp/opencode/xtb_spike/` with the repo's `xtb-6.7.1/bin/xtb.exe` (via WSL interop, mirroring `test_wsl_winxtb.sh`): `-o --hess` repro (exit 0, no hessian files), `--ohess` (phenol + CO₂ + π-stacked phenol dimer; captured `vibspectrum`, `g98.out`, `hessian`, timings, bond lists), corrupted-input run (exit 128, stderr contract).
- `[SRC] tmp/xtb_test/phenol_hess.log` (640 lines): ANC model-Hessian lines 257-260/346/351; electron count; no frequency section; wall-time 0.063 s.
- `[SRC] pymol-src/modules/pymol/`: `internal.py:400-437` (special_key_codes incl. up/down; `_special` dispatch), `controlling.py:719-770` (`set_key` + key list), `helping.py:320-322` (LEFT/RIGHT = frame step), `wizard/__init__.py:6-16,49-56,82-86` (event masks, do_key/do_special), `locking.py:26-88` (lock/is_gui_thread), `querying.py:881` (get_atom_coords), `editing.py:1216` (h_add), `pymol/Qt/__init__.py` (QtCore export, per STACK.md).
- `[SRC] pymol-src/modules/pymol/plugins/`: `__init__.py:130-149,186-280,365-390,407-430` (PluginInfo.load, `pymol.plugins.startup.<name>` identity, reload, findPlugins incl. packages), `installation.py:186-345` (install flow, `prefix = startup.__name__`).
- `[SRC] tmp/bioCHEMeleon/`: `AGENTS.md` (domain rules, gates, module-identity context), `__init__.py:3-8,129-153` (singleton, modeless, reload context), `gui_game.py:6-7,109-111,228-264,289-344` (QTimer, countdown, Bug A/B/C), `__init__.py:516-534,745-788,870-913` (wizard teardown ordering, timer rebase, restart), `_resolve_large_demo` in `__init__.py:545-677` (worker+queue+drain), `wizard.py:86-92` (set_wizard save/restore), `demos.py:59-74` (WSL→Windows guard), sibling repo `.planning/research/PITFALLS.md` carry-over matrix (v1 ".pse doesn't save plugin state").
- `[SRC] chempy/mol.py:74-81` (M CHG formal charges), `chempy/mol2.py:74` (partial charges only).
- Sibling research: `.planning/research/STACK.md` §4–6 (wizard C-layer dispatch verification, QProcess choice, `--help`-verified flag semantics, QPainter precedents), `.planning/research/ARCHITECTURE.md` §3–5 (patterns, namespace, phase letters A–H).
- `[TRAIN]` items explicitly marked above (OMP_STACKSIZE, OMP_NUM_THREADS guidance, cmd.h_add unreliability) — unverified here; validate before relying.

---
*Pitfalls research for: serpentrum — PyMOL plugin snake game with xtb spectra*
*Researched: 2026-09-06*
