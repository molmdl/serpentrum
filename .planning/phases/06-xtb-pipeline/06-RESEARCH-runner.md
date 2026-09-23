# Phase 6 (runner half): Async cancellable QProcess xtb runner — Research

**Researched:** 2026-09-24
**Domain:** Qt QProcess subprocess orchestration inside Windows conda PyMOL 2.5.0; xtb 6.7.1pre `--ohess` run lifecycle
**Scope:** research questions Q1–Q8 (runner half only: QProcess smoke → runner shell). The atom-budget guard and the ~100-atom calibration run as parallel plans (ROADMAP line 226); their seams are noted but not designed here.

## summary_up_front

**Confidence: HIGH overall.** The two load-bearing unknowns this phase was gated on — "does QProcess exist and work in the Windows conda PyMOL build?" and "can a headless `-cq` process drive it through an event loop?" — are both **answered empirically today by live probes against the real environment**, not by training data. The roadmap's gate ("QProcess-in-conda smoke gates the runner plan") can be discharged by a smoke whose every mechanism is already proven in `tmp/spike_probe/qprocess_probe.py` (git-ignored, evidence values inline below).

**Key findings:**

1. **QProcess works in the conda build — fully probed today.** `pymol.Qt` → PyQt5 Qt **5.12.9** in the Windows conda runtime (`C:\Users\nglok\.conda\envs\chemtools-win10`), runtime Python **3.9.13** (author plugin code to 3.6 syntax anyway — the WSL `python3.6` gate is the binding constraint). `QProcess`, `QEventLoop`, `QTimer`, `QElapsedTimer`, `QProcessEnvironment` all present; a real `xtb.exe` run completed through QProcess signals headless. Probe evidence: `PROBE A_FINISHED: (0, 0)`, stderr head `b'normal termination of xtb\r\n'` (the contract literal goes to **stderr**, matching `xtbenv.STDERR_SUCCESS`).
2. **Cancel via `kill()` verified on the real binary:** kill at 309 ms into a dimer `--ohess` → `finished(exitcode=62097, exitstatus=1)` where 1 = `QProcess.CrashExit`, and the run dir retains only optimizer-stage files (`.xtboptok`, `snake.xyz`, `xtbopt.log`) — i.e. **a killed run automatically fails the 3-leg contract** (exit≠0, files missing) via the existing `xtbenv.evaluate_run` with zero extra code.
3. **Cancel-safe file quarantine is free:** partial kill output cannot masquerade as success — `g98.out`/`vibspectrum` are written only near the end; the files leg plus the exit leg both fire on kill.
4. **QProcessEnvironment env injection verified running:** `setProcessEnvironment` with `OMP_NUM_THREADS=2` produced a complete successful run (2848 ms, dimer 26 atoms). And the **argv-level `-P N` knob is verified from WSL** — the log echoes `omp threads : N` at line 106 — so thread calibration does NOT depend on env propagation through the WSL↔Windows boundary.
5. **`xtb.exe` is NOT on the Windows PATH** (`cmd.exe /c where xtb.exe` → not found) and the repo-root `xtb-6.7.1` is a **WSL symlink to `/mnt/c/xtb-6.7.1` that Windows cannot traverse** (`OSError(22, 'The file cannot be accessed by the system')` from the conda Python). `xtbenv.detect_binary()` auto-detect will therefore return None inside Windows PyMOL on this machine; the working binary is `C:\xtb-6.7.1\bin\xtb.exe` (verified). The Setup-tab configured path (SETUP-05) is the primary seam; smokes must probe fallbacks explicitly.
6. **The completion handoff does not yet carry atom coordinates.** `anchor.last_run` (built in `gui_game._present_completion`, `serpentrum/gui_game.py:1319-1333`) stores `result`, counts, `chain_objects` (PyMOL names), `snake_id` — but **no xyz text**. The engine atoms exist at exactly that code point (`engine` is the argument; 05-RESEARCH-core-integration line 151: "final snake xyz = head_atoms(translated) + Σ seg['atoms'] — do not re-read PyMOL"). One seam task in the runner plan must assemble `xyzio.write_xyz` text there and stash it on the record.
7. **Runtime needs zero WSL↔Windows path translation** (STACK.md:83): Windows PyMOL + Windows exe + per-run temp dir + bare `snake.xyz` argv. Verified by fixtures: `ohess.log:105` echo `program call : xtb.exe phenol.xyz --ohess`.
8. **Purity placement is settled by existing precedent:** the QProcess shell is a new **GUI** module added deliberately to `GUI_MODULES` in `tools/check_purity.py:57-63` (same edit shape as `gui_game.py` in 04-05); all decision logic stays PURE via existing `xtbenv` fns plus (optionally) one small new PURE module for state-machine/env logic that python3.6 can unit-test.

**Verified today (live probes), not assumed:** QProcess availability/signals/env/kill/exitstatus (probe A, B, C); `-P N` argv knob + log echo (WSL runs in `/tmp/opencode/xtbcal/run_P{1,4}.log`); repo tmp/ writable from Windows (`WRITE-OK` echo probe); `xtb.exe` absent from Windows PATH; repo xtb symlink Windows-inaccessible.
**Still assumed (LOW):** whether `~100-atom` snake `--ohess` stays in tens-of-seconds (extrapolation only — calibration plan discharges this); `OMP_STACKSIZE` necessity (`[TRAIN]` LOW per PITFALLS:431).

**Primary recommendation:** one GUI module `serpentrum/xtb_runner.py` (new-style `.connect()` signals, single run owner anchored on `pmg_tk.startup._serpentrum`, `kill()` for cancel, no polling) consuming `xtbenv` verbatim; gate it with smoke `09_xtb_runner_smoke.py` built directly on today's probe mechanics.

---

## Q1 — QProcess in PyMOL 2.5.0: availability, signals, connect style

**Answer: QProcess is available and functional; use new-style `.connect()` (house precedent), not old-style `SIGNAL()` strings.**

Evidence (live probe, `tmp/spike_probe/qprocess_probe.py`, run via `timeout 180 cmd.exe /c "C:\src\run-conda-pymol.bat -cq tmp\spike_probe\qprocess_probe.py"`):

| Fact | Value (probe output) |
|---|---|
| Runtime Python | 3.9.13 (conda-forge, `chemtools-win10` env) — `PROBE PYVER` |
| Binding via `pymol.Qt` | PyQt5 — `PROBE QT_BINDING` |
| Qt version | 5.12.9 (`QT_VERSION_STR`; `QT_VERSION`=0x50c09) |
| `QtCore.QProcess` | present — `PROBE HAS_QPROCESS: True` |
| `QtCore.QEventLoop` | present — `PROBE HAS_QEVENTLOOP: True` |
| `-cq` headless has NO Q(Core)Application | `PROBE COREAPP_BEFORE: None` → smoke/runner must create one if absent |
| Real `xtb.exe --version` via `proc.start(exe, [arg])` | `started` fired, `finished` delivered `(0, 0)` = (exitCode=0, exitStatus=NormalExit) |
| stderr channel | `readAllStandardError()` captured `b'normal termination of xtb\r\n'` — the contract literal is an **stderr** stream event, streamable incrementally |

Signal inventory (connected successfully in the probe): `started`, `finished(int, int)` (PyQt5 exposes `finished(int, QProcess.ExitStatus)`; the slot receives two ints), `error(int)` (connected without exception under 5.12.9; Qt 5.6+ also offers `errorOccurred` — prefer `getattr(proc, 'errorOccurred', proc.error)` defensively), `readyReadStandardOutput`, `readyReadStandardError`.

The source-tree wrapper `pymol-src/modules/pymol/Qt/__init__.py:28-40` (STACK.md:19 cites it) exports `QtCore` wholesale, so `QProcess` comes along with the module — no special-casing needed. The in-repo source tree predates/differs from the installed conda build version-wise, which is exactly why the live probe matters: STACK.md:193's "verify `QtCore.QProcess` import at phase start" is now **discharged**.

**Connect style:** every existing plugin module uses new-style `.connect()` on pyqtSignals (`gui_setup.py:222-235`, `gui_game.py:284-349`); `pymol.Qt/__init__.py:84-87` aliases `QtCore.Signal = pyqtSignal`, so declaring runner signals with `QtCore.Signal(...)` works too. **Do NOT use old-style `SIGNAL()` string connects** — there is no repo precedent for them and PyQt5 makes them unnecessary. The research brief's "old-style is safest" hypothesis is contradicted by in-repo evidence.

Confidence: HIGH (live probe + source).

## Q2 — Purity placement

**Answer: the QProcess runner is GUI class. Add `serpentrum/xtb_runner.py` to `GUI_MODULES` in `tools/check_purity.py` (deliberate allowlist edit is the established pattern). Keep every decision rule PURE.**

- `tools/check_purity.py:57-63`: `GUI_modules` = explicit allowlist, currently `{'serpentrum/gui.py', 'serpentrum/gui_setup.py', 'serpentrum/gui_game.py'}`; comment says "extend consciously in later phases: a new GUI module must be added here deliberately." The 04-05 edit for `gui_game.py` is the exact precedent (comment cites `04-RESEARCH-hud.md Q5`).
- GUI rules: only `pymol.Qt` / `pymol.Qt.*` imports, any level; **no other pymol*/pmg_tk**, no PyQt5/numpy, no `.exec_()` (anywhere, all classes). So `xtb_runner.py` must NOT import `pymol.cmd` — it must not touch the viewer at all (the runner half has no viewer work; the Spectra-tab presentation is Phase 7). If any `cmd.*` handoff is ever needed it must go through `pymol_bridge` or a signal the dialog handles.
- BRIDGE is the wrong class: `BRIDGE_MODULES` (`tools/check_purity.py:70-73`) **bans PyQt5/numpy and `.exec_()`** and Qt has no allowance there ("Qt stays in GUI modules").
- PURE needs no allowlist edit: "PURE is the default-strict class: a future pure module is automatically covered" (`check_purity.py:37-38`). Any new pure logic (state machine, env-dict builder, verdict mapping) can live in a new PURE module, WSL-`python3.6`-testable with unittest + DI seams (the `xtbenv.detect_binary(which_fn=...)` DI pattern from 02-02 is the model).

**Proposed layering (evidence-based):**

| Module | Class | Contents | Tested by |
|---|---|---|---|
| `serpentrum/xtb_runner.py` (NEW) | GUI (add to allowlist) | `XtbRunController` QtCore.QObject: owns one `QProcess`, signals `started/finished/failed/cancelled/log_line`, methods `start(xyz_text, exe_path, base_dir)`, `cancel()`; calls PURE fns for argv/env/verdict | headless smoke only (no WSL import) |
| `serpentrum/xtb_run.py` (NEW, optional) | PURE (auto-covered) | run-state machine (idle→running→done/failed/cancelled transitions; no-double-run guard logic), `build_env(base_env, knobs)` dict merge, kill→verdict mapping (CrashExit → 'run cancelled') | WSL python3.6 unittest, DI seams |
| `serpentrum/xtbenv.py` (EXISTS) | PURE | unchanged contract surface: `detect_binary`, `build_argv`, `new_run_dir`, `evaluate_run`, constants | existing `tests/test_xtbenv.py` (23 tests) |

Keep the GUI shell *thin*: it must not re-implement any rule already in `xtbenv` (see dont_hand_roll). Note the architecture map (`ARCHITECTURE.md:105-106`) still describes `xtb_runner.py` as a **stdlib worker+queue** module — that text predates the QProcess correction (STACK.md:85, SUMMARY:21); the planner should treat QProcess-first as locked, worker+queue as fallback.

Confidence: HIGH (checker source + 04-05 precedent).

## Q3 — Async drain pattern

**Answer: pure signal-driven QProcess, no polling. `started`/`finished`/`readyReadStandard{Output,Error}` all land on the Qt main thread; slots there may legally call `cmd.*` (same-thread rule) — STACK.md:85, PITFALLS.md:64.**

- Verified in the probe: during a live run, `QTimer.singleShot(300, do_kill)` fired (cancel signal), and incremental stderr bytes arrived through `readyReadStandardError`. The Qt event loop stays fully responsive — the Phase-4 game `QTimer` ticks (`gui_game.py:284`) keep running during a spectra run.
- No `waitForFinished()` anywhere, ever (PITFALLS.md:64 – "Never `waitForFinished()`", "exits codes through the .bat are ALWAYS 0" isn't relevant here but blocking is).
- Fallback if QProcess had misbehaved (it didn't): stdlib worker + `queue.Queue` + recursive `QTimer.singleShot(100, drain)` on the main thread — the **bioCHEMeleon-verified** pattern, `_resolve_large_demo`, `tmp/bioCHEMeleon/biochemeleon/__init__.py:545-677` (worker is stdlib-only, `cmd.*` only on the drain's done-branch, cancel via `threading.Event`, pending-flags cleared on every terminal branch). PITFALLS.md:150-157 nails the threading hazard (cmd single-lock, `pymol/locking.py:26-40,80`). Keep this fallback documented; do not build it.
- Log streaming: `readyReadStandardOutput/Error` → append decoded chunks to the Spectra log widget (Phase 7 owns the widget; Phase 6 runner emits `QtCore.Signal(str)` log lines and the caller connects). Incremental reads matter: PITFALLS.md:368 ("No feedback during minutes-long hessian — users think it hung").

Confidence: HIGH (probe + verified precedent).

## Q4 — Cancel + no-double-runs

**Cancel: verified `proc.kill()`.** Probe B: kill 309 ms into a real dimer `--ohess` → `finished(exitcode=62097, exitstatus=1)`; `QProcess.CrashExit == 1` (`B_EXITSTATUS_ENUM: (0, 1)`), process state returned to `NotRunning` (0). Total elapsed 320 ms — kill is immediate. Do not bother with `terminate()` (console-attached exes like xtb.exe get no WM_CLOSE graceful path on Windows; it is unverified here and `kill()` is already proven). The runner's cancel path = `kill()` → in the `finished` slot, detect the cancelled state (runner-tracked flag, since 62097≠0 already fails the exit leg) and report "cancelled", not "failed".

**Partial files after kill (probe B dir listing):** `.xtboptok, snake.xyz, xtbopt.log` only — `g98.out`/`vibspectrum` never written → `evaluate_run` files leg fails → no fake success, ever. Cleanup: delete the run dir in the terminal branch (success after extracting outputs / failure / cancel alike); xtb sprays 10–12 files (probe C listing: `.xtboptok, charges, g98.out, hessian, snake.xyz, vibspectrum, wbo, xtbhess.xyz, xtbopt.log, xtbopt.xyz, xtbrestart, xtbtopo.mol`), so quarantining partial dirs indefinitely litters temp. `new_run_dir`'s docstring (xtbenv.py:200-206) assigns dir lifecycle ownership to the runner.

**No-double-runs / state owner:** single run owner object lives on the live-state anchor — `pmg_tk.startup._serpentrum` (`serpentrum/__init__.py:10-48`, identity guaranteed by `s_anchor_identity`/`s_reload_survival`/`s_double_import_adoption` in `smoke/01_skeleton_smoke.py:91-109`; house rule: never module globals). The controller guards with a pure state machine: `start()` is a no-op-with-message (or disables the launch button — PITFALLS.md:66 "disable the Get-Spectra button while a run is in flight") unless state is idle/done/failed/cancelled. After cancel or completion the guard releases → new run allowed (success criterion 2). bioCHEMeleon's `_pending_*` flags cleared on EVERY terminal branch (`__init__.py:616-668`) is the discipline to copy: the terminal branch set is done / failed / cancelled / error-fired.

Confidence: HIGH (probe B) for cancel mechanics; HIGH (repo assets) for guard placement.

## Q5 — Per-run temp dir lifecycle, argv, files

**`new_run_dir(base_dir)` = `tempfile.mkdtemp(prefix='srp_', dir=base_dir)`** (`xtbenv.py:194-207`): collision-free (mkdtemp guarantees), zero cleanup semantics — caller owns deletion. Contract: input written INTO it, `cwd=`it, bare relative `snake.xyz` in argv.

**base_dir choice:** candidates:
1. **Windows per-user temp** (`tempfile.gettempdir()` → `%TEMP%`) — **verified today**: probes A/B/C ran full xtb cycles in `srp_probe_*` dirs under %TEMP% from the conda Python. Recommended default.
2. Repo `tmp/xtb_runs/` (SUMMARY:109 "end-to-end headless run … files in git-ignored `tmp/xtb_runs/`") — writable from Windows (echo-WRITE-OK probe verified), visible for dev debugging, git-ignored (`.gitignore` line: `tmp`). Good for the **smoke/calibration track** so artifacts can be inspected; fine as a dev override, not required at runtime.
3. Never the PyMOL session dir (PITFALLS Pitfall 3.1 / lines 82-92: cwd pollution, stale-`vibspectrum` masquerade, "mystery `.xtboptok` files next to the user's `.pse`"). xtbenv docstring repeats this (`xtbenv.py:204-206`).

Note: `.pse` desync (Pitfall 8.3) does not affect run dirs (filesystem, not viewer objects), but the `srp_` dir-name prefix is the same token as the PyMOL-object prefix reservation — harmless (different namespaces), just don't confuse cleanup paths (`pymol_bridge.cleanup_srp` deletes objects by name, never dirs).

**argv beyond `build_argv`:** none required. Fixtures' recorded command lines are exactly `[exe, input, --ohess]` (`ohess.log:105` `program call : xtb.exe phenol.xyz --ohess`; `co2.log:104`, `dimer2.log:105` same shape) — matching `build_argv(exe, 'snake.xyz')` defaults. The full output set (probe C) is produced with zero extra flags and no `--restart` pre-scan. Optional extras the planner MAY wire through `extra_args`: `-P N` threads (verified today — log line 106 echoes `omp threads : N` at both -P 1 and -P 4) for the calibration track; `--namespace serp` (help-verified per STACK.md:86; optional disambiguation — NOT needed since the dir itself is the namespace).

Datetime caveat: the probe found `xtbhess.xyz` in the dimer run but not in an earlier phenol run at %TEMP% — i.e. some outputs are system-dependent; the contract must stay pinned to `EXPECTED_FILES=('g98.out','vibspectrum')` exactly as fixtures pin.

Confidence: HIGH.

## Q6 — The ~100-atom calibration experiment

**Measurement method (PyMOL-free, already proven today twice):**
- From WSL, direct exec of the Windows exe (gate-5 pattern, `tests/run_gates.py:190+`, `test_wsl_winxtb.sh`): `/mnt/c`-backed cwd, bare relative args, parse `* wall-time:` lines from the log (each stage emits one; the LAST `* wall-time` block in the log also gives `total:`). Today: `co2.xyz --ohess -P 1` total ≈ 0.24 s; header echoes `omp threads : 1` (line 106).
- From headless PyMOL, QProcess + `QElapsedTimer` (probe pattern): startup overhead included (true user-perceived wall). Today: dimer2 (26 atoms) = **2848 ms** with `OMP_NUM_THREADS=2`; phenol finished in <500 ms at default threads.
- Prior measured points (SUMMARY:67, `[RUN]`-tagged): phenol 0.67 s, 26-atom dimer 1.75 s (default threads; probe B/C consistent).

**Thread knobs (all verified, none invented):**
- `xtb --help` (captured `tmp/xtb_test/xtb_help.txt`): `-P, --parallel INT number of parallel processes` (lines 197-198); env guidance lines 229-231: `MKL_NUM_THREADS=<NCORE>`, `OMP_NUM_THREADS=<NCORE>,1`, `OMP_STACKSIZE=4G`.
- `-P N` verified functional today via WSL exec (log `omp threads : N`). This is the cleanest knob for the runner because it is argv-level and `build_argv`-compatible (`extra_args=(XTB_OHESS, '-P', '2')` — quotes-free, injection-safe).
- `OMP_NUM_THREADS` via `QProcess.setProcessEnvironment(QProcessEnvironment)` verified functional today inside the conda PyMOL (probe C). Note: WSL-set env vars do NOT reliably cross the WSL→Windows interop boundary (WSLENV-gated) — for WSL-side calibration use `-P`; for the in-plugin run the QProcess env is verified.

**Proposed calibration experiment (executor-run, parallel plan):**
1. Build capped-snake xyz fixtures programmatically from committed molecules: e.g. phenol segments ×8 ≈ 104 atoms (or the dimer motif ×4 ≈ 104 atoms stacked at 3.4 Å like `dimer2.xyz`) using `xyzio`/`stacking` pure fns — never hand-edited. Commit the fixture.
2. Sweep `-P {1, 2, 4, all}` headless (QProcess probe pattern and/or WSL exec), record log `* wall-time` lines + header `omp threads` echo; 2 repeats each.
3. Commit artifacts: fixture xyz + a `06-CALIBRATION.md` table (size × threads × wall) + per-run logs (git-ignored `tmp/xtb_runs/` or commit small logs under fixtures).
4. Outcome feeds: `atom_budget` default (currently 100, `setup_logic.py:55-56`), `HESSIAN_WARNING` threshold copy (`setup_logic.py:270-279`), and whether a default `-P` cap ships with the runner (PITFALLS.md:333,348 — xtb grabs all cores by default, causing UI jank; capping keeps rendering smooth). `OMP_STACKSIZE` necessity for ~100-atom hessian remains `[TRAIN]` LOW (PITFALLS.md:431) — only adopt it if the uncapped run crashes.

Confidence: MEDIUM-HIGH (method fully verified; absolute ~100-atom wall time still an extrapolation — that is precisely what the experiment measures).

## Q7 — Smoke gating design

**Feasibility: fully verified by today's probe.** Every mechanism is proven: headless `-cq` + `QCoreApplication` (created since `C:\src\run-conda-pymol.bat -cq` starts with no app — `COREAPP_BEFORE: None`) + `QEventLoop.exec_()` inside the smoke script (legal — the `.exec_()` purity ban applies only to `serpentrum/`, smoke scripts are dev-side; `check_purity.py:52`) + real xtb.exe + safety-timeout `singleShot`.

**Proposed `smoke/09_xtb_runner_smoke.py`** (numbering continues 01–08; `tests/run_gates.py:55-61` lists required smokes — add as **informational first**, promote to required only after it proves stable across machines; gate code at `run_gates.py:150-188` runs informational smokes without failing):

Template obligations (copied from `smoke/01_skeleton_smoke.py:1-21` + `smoke/03_viewer_bridge_smoke.py:13-29`): named step functions + `check()` runner, `flush=True` on EVERY print, `_resolve_root()` candidate-validation (never trust `__file__`), NO widget construction (headless C-abort uncatchable), no `smoke/__init__.py`, verdict = flushed `SMOKE-OK XTB-RUNNER` sentinel only (rc through the .bat is always 0).

Steps (each maps to a success criterion):
1. `qprocess_available` — `pymol.Qt.QtCore.QProcess` import + app instance ensure.
2. `runner_constructs` — build the `XtbRunController` on the anchor (module load `pmg_tk.startup.serpentrum`).
3. `resolve_xtb` — `xtbenv.detect_binary(configured)` probing: configured path → `shutil.which` → **fallback list including `C:\xtb-6.7.1\bin\xtb.exe`** (verified working today; `where xtb.exe` on Windows PATH finds nothing, and the repo `xtb-6.7.1` symlink is Windows-inaccessible — Q1/Q5 evidence). Smoke FAILS with a clear message when no binary resolves.
4. `arun_success_contract` — launch a TINY REAL job (`co2.xyz`, 3 atoms, quarter-second today; real exe only — no fabricated stub per the no-fabrication rule) from snake xyz text; assert `started` fired, at least one `readyRead` chunk seen, `finished==(0,0)`, and `xtbenv.evaluate_run(0, stderr, EXPECTED_FILES, listdir) .ok is True`.
5. `responsiveness_tick` — a `QTimer` fires at N ms DURING the run (prove async-ness headlessly; probe's kill-timer-during-run already demonstrated this; in-GUI responsiveness is UAT/human-verify per the 01-05 dead end — no offscreen dialog tricks).
6. `cancel_path` — launch a longer job (dimer2 ≈ 2.8 s), `kill()` at ~300 ms, assert `finished` with `exitStatus==CrashExit`, runner state = cancelled, and `evaluate_run(...)` is NOT ok (files leg fails). Assert a second run can start after cancel (no-double-runs guard releases).
7. `no_double_run_guard` — second `start()` while running is rejected/defused.

Event-loop waiting pattern for the smoke: `QEventLoop` + `finished`/`error` → `loop.quit()` + `QTimer.singleShot(120000, loop.quit)` safety timeout (exactly the probe mechanism). Per-step elapsed via `QElapsedTimer`.

Confidence: HIGH — no mechanism in this smoke is unproven today.

## Q8 — python3.6 compatibility constraints

- Syntax: unchanged house rules (STACK.md:190): %-formatting house style (f-strings are 3.6-legal but repo precedent is `%`), no dataclasses/walrus/f-string`=`. WSL gate `python3.6 -m py_compile` is binding even though the runtime is 3.9.13.
- Signals: new-style `.connect()` is PyQt5-native and py3.6-fine (all existing GUI modules do it; probe did it under 3.9 — semantics identical). For `finished(int, ExitStatus)`, connect a slot taking `(code, status)`.
- QByteArray → text: `bytes(proc.readAllStandardOutput()).decode('utf-8', 'replace')` — verified pattern from the probe (raw `QByteArray` is not `str`-compatible for the `%`/join work the log parser will do). stderr arrives CRLF (`\r\n` in `B_STDERR_HEAD`) — `evaluate_run` is already CRLF-tolerant (substring check, `xtbenv.py:91-102`).
- Exit-status enum: compare against `QtCore.QProcess.CrashExit`/`NormalExit` (ints 1/0, probe-verified), not magic numbers.

Confidence: HIGH.

---

## open_questions_for_planner

1. **Handoff seam shape:** add `snake_xyz` (text) to `anchor.last_run` inside `_present_completion` (`gui_game.py:1289-1333`, engine still alive there) — or have the runner pull atoms from the session? Recommendation: extend `last_run` at completion time (single write, reload-safe, no PyMOL re-read; 05-RESEARCH line 151 forbids re-reading PyMOL for atoms). The runner plan must own this small `gui_game` edit (shared-file risk if Phase 7 touches the same method — sequence it).
2. **Smoke binary fallback list:** hard-coding `C:\xtb-6.7.1\bin\xtb.exe` in the smoke is machine-specific. Better: smoke reads an env var / probes a small candidate list [(setup-configured), which, C:\xtb-6.7.1, /mnt/c via %TEMP%-relative?]. Open for the planner to pick a clean probe list; MUST NOT rely on `shutil.which` alone (verified empty PATH today).
3. **Where launch-time atom-budget re-check lives** (SPECTRA-06 criterion 4): belongs to the parallel guard plan, but the runner's `start()` receives `atoms_total` from `last_run` — coordinate the seam so the guard prohibits/warns BEFORE `start()`. `HESSIAN_WARNING` copy and caps are in `setup_logic.py:55-56,270-279`; completion exposes `atoms_total` (gui_game.py:1326-1332).
4. **Default thread cap for the shipped runner:** none yet — calibration experiment (Q6) decides whether the runner adds `-P N` by default. Until then run uncapped but document the UI-jank risk (PITFALLS.md:333).
5. **`errorOccurred` vs `error` on the exact runtime (5.12.9):** probe verified `error` connects; `errorOccurred` availability not yet asserted — one-line check in the smoke (`getattr(proc, 'errorOccurred', proc.error)`) settles it defensively.
6. **QCoreApplication lifetime in real GUI runs:** headless needs creating one (verified); in the real PyMOL GUI a `QApplication` already exists — runner must use `QtCore.QCoreApplication.instance()` and never create a second app.

## dont_hand_roll (existing code the plan MUST reuse)

| Don't build | Use instead | Where |
|---|---|---|
| Custom success/failure logic, fake-exit-code checks | `xtbenv.evaluate_run(exit, stderr_text, EXPECTED_FILES, listdir)` — 3-leg contract, failure-before-success substring ordering, one problem string per failed leg | `serpentrum/xtbenv.py:51-110`; 23 pinned tests `tests/test_xtbenv.py` |
| Shell-string commands, `shell=True`, manual quoting | `xtbenv.build_argv` — list argv, quote rejection ValueError | `xtbenv.py:170-191`; PITFALLS.md:355 |
| `glob`/PATH probing logic, `.exe` handling | `xtbenv.detect_binary(configured_path)` — probe order configured → xtb.exe → xtb, DI seam | `xtbenv.py:141-167` |
| Path validation rules for user-x tb path | `xtbenv.validate_binary_path` (NOTE: `setup_logic._xtb_path_problems` is a parallel-plan mirror marked "unify later" — 02-07-SUMMARY; do NOT add a third copy) | `xtbenv.py:113-138` |
| `tempfile` naming, run-dir convention | `xtbenv.new_run_dir(base_dir)` — `srp_`-prefixed mkdtemp | `xtbenv.py:194-207` |
| XYZ serialization of the snake | `xyzio.write_xyz` / `write_xyz_file` (round-trip pinned Phase 2) | `serpentrum/xyzio.py`; 05-RESEARCH line 217 |
| State ownership location | anchor `pmg_tk.startup._serpentrum` via `_anchor()` — never module globals | `serpentrum/__init__.py:10-48`; smoke 01 identity tests |
| Polling/event-pump loops for the subprocess | QProcess signals (probe-verified); fallback documented but unbuilt: bioCHEMeleon `_resolve_large_demo` drain | `tmp/bioCHEMeleon/biochemeleon/__init__.py:545-677` |
| Thread-cap invention | `-P N` (help:197-198, log-echo verified) or QProcessEnvironment OMP knobs (help:229-231, probe-verified) | `tmp/xtb_test/xtb_help.txt` |
| Old-style `SIGNAL()` connects | new-style `.connect()` house style | `gui_setup.py:222-235` etc. |

## common_pitfalls (runner half)

1. **Fake success from stderr alone** — "normal termination" is a substring of "**ab**normal termination"; `evaluate_run` already orders failure-first (xtbenv.py:91-97, `bad.err` fixture). Runner must feed stderr text verbatim, never pre-filtered.
2. **stale-file masquerade** — running in a reused dir lets an old `vibspectrum` satisfy the files leg. Fresh `new_run_dir` every run; verify files via `os.listdir(run_dir)`, not existence anywhere else (PITFALLS Pitfall 3.1).
3. **`-o --hess` regression** — locked constant `XTB_OHESS = '--ohess'`; the repro_oh fixture proves `-o --hess` exits 0 with zero spectra files (PITFALLS Pitfall 1). Never pass flags as separate `-o`,`--hess` through `extra_args`.
4. **Blocking waits** — `waitForFinished`, `subprocess.run`, or `processEvents` pumping on the main thread freezes viewer + game timers (PITFALLS Pitfall 2; SUMMARY:67). Signals only.
5. **Worker threads touching cmd.*** — fallback-only pattern; worker must be stdlib-only, `cmd.*` only on main-thread drain (PITFALLS Pitfall 6; pymol single lock `pymol/locking.py:26-40,80`).
6. **Module-globals for run state** — reload/double-import duplicates them; anchor on `_serpentrum` (PITFALLS Pitfall 7; smoke 01 tests).
7. **Trusting exit codes through the .bat / trusting rc for smoke verdicts** — sentinel-based verdicts only (smoke template; run_gates.py:134-188).
8. **Offscreen-dialog testing** — 01-05 dead end; the smoke asserts mechanics (signals, contract, guard) headlessly; UI responsiveness is human-UAT (01-06-SUMMARY:114).
9. **Windows-inaccessible xtb paths** — repo `xtb-6.7.1` is a WSL symlink Windows cannot traverse (OSError 22, probed); auto-detect returns None on this machine; the smoke/runner must surface "xtb not found" instead of dying in `QProcess` with an opaque `FailedToStart` (probe the error path in the smoke).
10. **Dirty-dir deletion races** — deleting the run dir before `finished` fires (or while xtb still holds files open on cancel) → WinError 32; delete only in the terminal branch after `finished` (probe B: state `NotRunning` immediately at finished).
11. **Handoff re-reading PyMOL** — chain atoms authored by the engine; PyMOL objects are visual truth only. Assemble xyz from `engine` atoms at completion (05-RESEARCH:151), never `cmd.get_coords`.
12. **Env-knob overclaim** — only `-P`(help:197) and the three help-listed env vars (help:229-231) are verified to exist; `OMP_STACKSIZE` necessity is `[TRAIN]` LOW (PITFALLS.md:431). No invented knobs.

## Sources

### Primary (HIGH — live probes run today, 2026-09-24, this repo)
- `tmp/spike_probe/qprocess_probe.py` + its output — QProcess availability, signals, env injection, kill/CrashExit, wall-timing, CWD/PATH facts (git-ignored; values quoted inline above).
- `/tmp/opencode/xtbcal/run_P1.log`, `run_P4.log` — `-P N` argv knob + `omp threads : N` echo + wall-time lines.
- Echo WRITE-OK probe — repo `tmp/` writable from Windows.
- `cmd.exe /c where xtb.exe` → not found — PATH negative.
- `stat xtb-6.7.1` → `symbolic link -> /mnt/c/xtb-6.7.1`; Windows-side `OSError(22)` on traversal.

### Primary (HIGH — committed repo sources)
- `serpentrum/xtbenv.py` (207 lines, full read) — the contract surface the runner obeys.
- `tools/check_purity.py:52-63,70-73` — GUI/BRIDGE allowlist mechanics.
- `.planning/research/xtb-spike-fixtures/` — `ohess.log:105` (program call), `ohess.err`/`bad.err` (stderr contract), full file set.
- `tmp/xtb_test/xtb_help.txt:197-198,229-231` — `-P` + OMP env knobs (verbatim help capture).
- `tests/run_gates.py:55-61,134-188,190+` — smoke harness + gate-5 xtb pattern.
- `smoke/01_skeleton_smoke.py`, `smoke/03_viewer_bridge_smoke.py` — smoke template obligations.
- `.planning/research/STACK.md:19,83-87,150,190,193,201`; PITFALLS.md:51-66,82-92,150-157,196-203,320,333,348,355,368,425-446; SUMMARY.md:10,21,67,109; ARCHITECTURE.md:105-106.
- `tmp/bioCHEMeleon/biochemeleon/__init__.py:545-677` — verified worker+queue+drain fallback.
- `serpentrum/gui_game.py:1289-1333`, `serpentrum/gui.py:96-106`, `serpentrum/gui_setup.py:240-275`, `serpentrum/setup_logic.py:55-56,270-279` — handoff/setup seams.
- `pymol-src/modules/pymol/Qt/__init__.py:26-40,84-87` — Qt wrapper exports.
- `.planning/phases/02-pure-core-game-chemistry-logic/02-02-SUMMARY.md:49,108-110`; 02-07-SUMMARY.md:83 (path-rules mirror).

### Secondary/Tertiary: none required — no webfetch/Context7 claims used; all Qt-version-critical claims live-probed.

## Metadata

**Confidence breakdown:**
- QProcess availability/signals/cancel/env (Q1,Q3,Q4,Q7): HIGH — live probe in the exact runtime.
- Purity placement (Q2): HIGH — checker source + allowlist precedent.
- Run-dir/argv/files (Q5): HIGH — fixtures + probe.
- Calibration method (Q6): MEDIUM-HIGH — method verified; ~100-atom wall time unmeasured (the experiment).
- py3.6 constraints (Q8): HIGH — repo gates + probe.

**Research date:** 2026-09-24
**Valid until:** stable (Qt 5.12.9 runtime pinned by conda env); re-verify if the conda env or xtb version changes.
