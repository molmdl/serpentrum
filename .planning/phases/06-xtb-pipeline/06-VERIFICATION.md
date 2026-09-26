---
phase: 06-xtb-pipeline
verified: 2026-09-26T17:14:07Z
status: passed
score: 5/5 success criteria verified
must_haves:
  truths:
    - "SC1: xtb --ohess starts on the final snake in a fresh per-run temp dir, asynchronously; dialog and viewer stay responsive"
    - "SC2: a running calculation can be cancelled and a new run can start after cancel or completion (no double-runs)"
    - "SC3: success declared only on the verified 3-leg contract (exit 0 + normal termination + expected files); corrupted input surfaces clear failure"
    - "SC4: before launch, hidden molecule/atom counts re-checked against the configured cap; exceeding shows a warning (warn-and-proceed)"
    - "SC5: ~100-atom snake completes --ohess headless with measured wall time; warning threshold and OMP environment calibrated from the measurement"
  artifacts:
    - path: serpentrum/budget_guard.py
    - path: serpentrum/xtb_run.py
    - path: serpentrum/xtb_runner.py
    - path: serpentrum/gui.py
    - path: serpentrum/gui_game.py
    - path: serpentrum/pymol_bridge.py
    - path: serpentrum/setup_logic.py
    - path: tools/check_purity.py
    - path: tests/run_gates.py
    - path: smoke/09_qprocess_smoke.py
    - path: smoke/10_chain_count_smoke.py
    - path: smoke/11_xtb_runner_smoke.py
    - path: .planning/phases/06-xtb-pipeline/06-CALIBRATION.md
    - path: tests/test_phase6_integration.py
    - path: tests/test_budget_guard.py
    - path: tests/test_xtb_run.py
    - path: tools/build_calibration_snake.py
    - path: tests/fixtures/calib_snake_104.xyz
  key_links:
    - from: serpentrum/gui.py _on_spectra_requested
      to: serpentrum/budget_guard.launch_budget_warnings
      via: head-inclusive counts from read_xyz_text(snake_xyz) vs chain_atom_counts; logged before launch
    - from: serpentrum/gui.py _launch_spectra_run
      to: anchor.spectra_runner (XtbRunController.start)
      via: tempfile.gettempdir() spray base + frozen last_run snake_id
    - from: serpentrum/xtb_runner.py _on_finished
      to: xtbenv.evaluate_run + xtb_run.resolve_status + anchor.spectra_run
      via: single terminal branch, copy-out to _stable_base(), spray-dir deletion
    - from: serpentrum/gui_game.py _present_completion
      to: xtb_run.build_run_input
      via: snake_xyz assembled at completion from engine/session atoms; explicit None branch
    - from: serpentrum/xtb_runner.py start()
      to: xtb_run.DEFAULT_THREAD_ARG
      via: extra_args default = (XTB_OHESS,) + ('-P', '4')
gaps: []
---

# Phase 6: xtb Pipeline — Verification Report

**Phase Goal:** The final snake can be handed to a real, cancellable, async `xtb --ohess` run with a verified success contract and a calibrated atom-budget guard — while the UI never blocks.
**Verified:** 2026-09-26T17:14:07Z
**Status:** passed
**Re-verification:** No — initial verification

## Method Note

All 12 SUMMARYs (06-01..06-12) were read; claims were verified against the actual codebase (file reads + grep structural checks), and all three gate legs were re-run by the verifier in this session. The owner checkpoint evidence in 06-12-SUMMARY (12-step verdict table, owner-staged artifact listing, commit 048d929) was cross-checked against git history and the live code.

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | SC1: `xtb --ohess` starts on the final snake in a fresh per-run temp dir, asynchronously — dialog/viewer responsive | ✓ VERIFIED | `xtb_runner.py:XtbRunController.start` writes snake.xyz into a fresh `xtbenv.new_run_dir(base_dir)` spray dir, cwd=that dir, bare-relative argv via `xtbenv.build_argv` (:160-193); signals-only (grep `waitForFinished\|subprocess` == 0, `.exec_(` == 0 in runner+gui). gui.py:246-248 launches with `tempfile.gettempdir()`. Live async proof: smoke 09 `PROBE RUN tick_at_ms: 298 tick_state: 2`, smoke 11 `PROBE TICK tick_at_ms: 306 status_at_tick: running`; owner checkpoint step 4 PASS ("xtb real-time log responsive yes") |
| 2 | SC2: cancel a running calculation; new run starts after cancel or completion (no double-runs) | ✓ VERIFIED | `xtb_runner.py:cancel` = proc.kill() (:201-208); `xtb_run.py:resolve_status` cancel-wins (:119-121); `xtb_run.py:can_start` + start() guard with 'already active' log line (:138-141). smoke 11: `PROBE CANCEL status: cancelled`, `PROBE AFTER_CANCEL started: True final: ok`, `PROBE RESTART started: True`, `PROBE GUARD first: True second: False`. Owner checkpoint steps 5/6/7 PASS |
| 3 | SC3: success only on verified contract (exit 0 + "normal termination" + expected files); corrupted input → clear failure, never fake success | ✓ VERIFIED | `xtb_runner.py:_on_finished` runs `xtbenv.evaluate_run(code, stderr, EXPECTED_FILES, present)` 3-leg verdict (:276-284); preflight failures route through `_fail_before_start` → frozen-record FAILED path (:352-367); killed run keeps snake.xyz+xtb.log only, contract paths None (smoke 11 cancel step). `tests/test_phase6_integration.py:168-180` pins both no-fake-success halves (`resolve_status(True,*)=='cancelled'` + `evaluate_run(62097,...)` not-ok with exactly exit-code + missing-files problems). Owner checkpoint steps 5/8/9 PASS incl. verbatim honest-cancel text |
| 4 | SC4: before launch, hidden molecule/atom counts re-checked against cap; exceeding shows a warning | ✓ VERIFIED | `gui.py:_on_spectra_requested` legs 3-4 (:189-209): `atoms_engine = len(xyzio.read_xyz_text(snake_xyz)[1])` (head-inclusive; never head-excluded `atoms_total`), viewer cross-check via `pymol_bridge.chain_atom_counts` (pymol_bridge.py:457), `budget_guard.launch_counts_line` + `launch_budget_warnings` logged BEFORE launch. `budget_guard.py` warns-and-proceeds, reuses `setup_logic.HESSIAN_WARNING` verbatim (:117-120), drift-pinned by `tests/test_budget_guard.py:51`. Owner checkpoint steps 3/10 PASS: HUD `atoms: 54` + benzene head 12 = 66 = counts line's "66 atoms (budget 100)" — head-inclusion arithmetic proven live |
| 5 | SC5: ~100-atom snake completes `--ohess` headless with measured wall time; warning threshold + OMP environment calibrated | ✓ VERIFIED | `06-CALIBRATION.md`: 16-run WSL sweep + 2 QProcess-timed runs; 104-atom wall 84.1/90.1 s uncapped, 99.9/100.8 s at -P 4, 268-281 s at -P 1; user-perceived 91.4 s uncapped / 107.6 s -P 4; VERIFIED-vs-ASSUMED split; OMP_STACKSIZE verdict NOT NEEDED; three decision inputs. Applied by 06-11: `setup_logic.py:132-135` HESSIAN_WARNING carries measured numbers (pin `tests/test_setup_logic.py:121`); `xtb_run.py:81` `DEFAULT_THREAD_ARG = ('-P', '4')` (pin `tests/test_xtb_run.py:131`) consumed in `xtb_runner.py:151-152`; `DEFAULT_RUN_KNOBS = {}` finalized (pin :120). Fixtures + builder committed (`tools/build_calibration_snake.py`, `tests/fixtures/calib_snake_104.xyz` = 104 atoms) |

**Score:** 5/5 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `serpentrum/budget_guard.py` | PURE SPECTRA-06 launch re-check | ✓ VERIFIED | 139 lines; `launch_budget_warnings` + `launch_counts_line`; never raises/blocks; imports setup_logic only; consumed by gui.py:203-207 |
| `serpentrum/xtb_run.py` | PURE runner decision half | ✓ VERIFIED | 196 lines; can_start/TERMINAL_STATES/resolve_status/build_env/build_run_input/SPECTRA_RUN_KEYS/new_spectra_run/DEFAULT_RUN_KNOBS/DEFAULT_THREAD_ARG; consumed by xtb_runner.py + gui_game.py |
| `serpentrum/xtb_runner.py` | XtbRunController Qt shell | ✓ VERIFIED | 367 lines; signals started/log_line/run_finished; single terminal branch `_on_finished` with copy-out → record → spray rmtree → reset → emit; `_stable_base()` SRP_SPECTRA_DIR resolver (048d929); pymol.Qt only |
| `serpentrum/gui.py` | Launch pipeline + placeholder affordances | ✓ VERIFIED | `_on_spectra_requested` (6 legs, :134-222), `_launch_spectra_run` (:224-255), `_build_spectra_placeholder` status/log/Cancel/Run-again (:257+), `_connect_runner` dialog-scoped once-guard (:320-334), `_log_spectra_line` two-channel with log_external mirror (:299-317) |
| `serpentrum/gui_game.py` | snake_xyz handoff + log_external | ✓ VERIFIED | `_present_completion` assembles snake_xyz via `xtb_run.build_run_input` with explicit None branch (:1413-1432); `GameTab.log_external` public wrapper (:1524-1535) |
| `serpentrum/pymol_bridge.py` | chain_atom_counts | ✓ VERIFIED | :457 after chain_object_names :443; get_model-based, missing object → 0 |
| `serpentrum/setup_logic.py` | HESSIAN_WARNING calibrated literal | ✓ VERIFIED | :132-135 carries "measured 84-101 s … up to ~5 min single-threaded" |
| `serpentrum/__init__.py` | anchor.spectra_run attribute | ✓ VERIFIED | `_SerpentrumState.spectra_run = None` with frozen-key docstring |
| `tools/check_purity.py` | GUI_MODULES xtb_runner entry | ✓ VERIFIED | :66-67 `'serpentrum/xtb_runner.py'` with 06-05/04-05 precedent comment; gate 2 PASS |
| `tests/run_gates.py` | REQUIRED_SMOKES incl. smoke 10 | ✓ VERIFIED | :55-63 includes `smoke/10_chain_count_smoke.py` with Phase-6 comment; gate 4 PASS |
| `smoke/09_qprocess_smoke.py` | QProcess mechanics smoke | ✓ VERIFIED | 360 lines; sentinel `SMOKE-OK QPROCESS`; informational PASS this session |
| `smoke/10_chain_count_smoke.py` | REQUIRED chain-count smoke | ✓ VERIFIED | 167 lines; sentinel `SMOKE-OK CHAIN-COUNT`; REQUIRED PASS this session |
| `smoke/11_xtb_runner_smoke.py` | Runner contract smoke | ✓ VERIFIED | 572 lines; sentinel `SMOKE-OK XTB-RUNNER`; sets `SRP_SPECTRA_DIR` (:111); informational PASS this session |
| `06-CALIBRATION.md` | Measured wall-time authority | ✓ VERIFIED | 71 lines; 8-row measured table + QProcess pair + verdicts + 3 decision inputs |
| `tests/test_budget_guard.py` | Guard behavior matrix + drift-pin | ✓ VERIFIED | 146 lines; `assertIn(setup_logic.HESSIAN_WARNING, lines[0])` :51 |
| `tests/test_xtb_run.py` | State machine + DEFAULT pins | ✓ VERIFIED | 204 lines; `DEFAULT_RUN_KNOBS == {}` :120, `DEFAULT_THREAD_ARG == ('-P','4')` :131 |
| `tests/test_phase6_integration.py` | End-to-end pure-chain pin | ✓ VERIFIED | 274 lines; 10 scenarios incl. killed-run no-fake-success (:168-180) |
| `tests/test_setup_logic.py` | Re-pinned HESSIAN_WARNING | ✓ VERIFIED | :121 pins the measured literal |
| `.gitignore` | srp_spectra/ entry | ✓ VERIFIED | line 29 `srp_spectra/` |
| Commit 048d929 | Owner SRP_SPECTRA_DIR directive | ✓ VERIFIED | git log confirms; `_stable_base()` in xtb_runner.py:48-60 + both use sites (:231, :287); smoke 11 env override :111 |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | --- | --- | ------ | ------- |
| gui.py `_on_spectra_requested` | budget_guard | counts from snake_xyz vs chain_atom_counts | ✓ WIRED | lines logged verbatim before any launch (gui.py:203-209) |
| gui.py `_launch_spectra_run` | XtbRunController.start | anchor.spectra_runner create-or-reuse | ✓ WIRED | gui.py:241-248; refused start re-enables Get Spectra (:249-255) |
| xtb_runner.start() | xtbenv.new_run_dir + build_argv | fresh spray dir, bare-relative argv | ✓ WIRED | xtb_runner.py:154-163 |
| xtb_runner `_on_finished` | xtbenv.evaluate_run → xtb_run.resolve_status → anchor.spectra_run | single terminal branch | ✓ WIRED | xtb_runner.py:276-328; cancel flag wins; record written on every branch |
| gui_game `_present_completion` | xtb_run.build_run_input | head atoms + engine segments | ✓ WIRED | gui_game.py:1416-1419; explicit None branch :1420 |
| gui_game log_external | gui.py `_log_spectra_line` mirror | two-channel logging | ✓ WIRED | gui.py:313-317 getattr-guarded |
| xtb_runner.start() extra_args default | xtb_run.DEFAULT_THREAD_ARG | '-P 4' calibration cap | ✓ WIRED | xtb_runner.py:151-152; caller overrides win |
| test_budget_guard | setup_logic.HESSIAN_WARNING | drift-pin | ✓ WIRED | assertIn on the literal — 06-11 amendment flows through (proven: suite green post-amendment) |
| smoke 10 | manifest.json atom_count | cross-pin | ✓ WIRED | CHAIN-COUNT smoke PASS (REQUIRED) |

### Requirements Coverage

| Requirement | Status | Blocking Issue |
| ----------- | ------ | -------------- |
| SPECTRA-02 (async cancellable --ohess, fresh temp dir, verified contract) | ✓ SATISFIED | None — SC1+SC2+SC3 all verified at code, test, smoke, and owner-checkpoint level |
| SPECTRA-06 (pre-launch hidden counts re-check with warning) | ✓ SATISFIED | None — SC4 verified; guard warn-and-proceed, head-inclusive arithmetic proven live (54+12=66) |

## Gate Results (re-run by verifier, 2026-09-26)

| Leg | Command | Result |
| --- | ------- | ------ |
| Default | `python3.6 tests/run_gates.py` | **GREEN** — 796 tests OK (2.7 s); gates 1-3 PASS; matches 06-12's recorded 796 exactly |
| Smokes | `python3.6 tests/run_gates.py --smoke` | **GREEN** — REQUIRED 8/8 PASS (01 SKELETON, 03 VIEWER-BRIDGE, 04 VIEWER-DEMO, 05 LOOP-CAMERA, 06 INPUT-WIZARD, 07 TRANSFORM, 08 EDGEON, **10 CHAIN-COUNT**); informational 09_qprocess **PASS**, 11_xtb_runner **PASS**; 02_dialog FAIL (pre-existing 01-05 offscreen dead end, non-blocking, unrelated to Phase 6); gate 4 PASS |
| xtb | `python3.6 tests/run_gates.py --xtb` | **GREEN** — `xtb version 6.7.1pre (5071a88)` rc=0 + `normal termination of xtb`; gate 5 PASS |

## Owner Checkpoint (06-12)

**APPROVED — 12/12 PASS** recorded in 06-12-SUMMARY.md with per-step owner evidence. Cross-checked here:

- Verdict table present with verbatim live-log lines (launch counts line, async-start line, honest-cancel contract text, "xtb real-time log responsive yes").
- Step-8 artifact evidence: owner-staged `tmp/srp_spectra/run_2/` listing with all five contract files (g98.out, snake.xyz, vibspectrum, xtb.log, xtbopt.xyz).
- Owner directive applied in commit **048d929** (verified in git log and in code: `_stable_base()` resolver, both use sites, .gitignore entry, smoke 11 env override) and re-verified green post-amendment (06-12 Task-3 legs + this session's green re-runs).
- EQ-smoke-1 disposition recorded: smokes 09/11 stay informational; owner instructed no promotion.
- EQ-checkpoint-1: Spectra PLOT/TABLE/LOG-PANEL verdicts explicitly deferred to Phase 7 (placeholder affordances only in Phase 6 scope — correct).

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| (none in Phase-6 files) | — | — | — | grep scan of budget_guard/xtb_run/xtb_runner/gui/gui_game/pymol_bridge: zero TODO/FIXME/placeholder-stub/empty-handler patterns; zero waitForFinished/subprocess; zero .exec_( |
| smoke/02_dialog_smoke.py | — | informational FAIL (non-blocking) | ℹ️ Info | Pre-existing 01-05 offscreen-dialog dead end; unrelated to Phase 6; gate green by design |

## Human Verification Required

None outstanding. The one blocking live human checkpoint for this phase (real Windows-PyMOL pipeline feel-check) was performed by the owner at 06-12 and **APPROVED 12/12** with recorded evidence. Residual live-GUI judgments (visual layout of the temporary placeholder, in-GUI responsiveness during a run) were covered by that checkpoint; Phase 7 owns the plot/table/log-panel UX verdicts by explicit deferral (EQ-checkpoint-1).

## Gaps Summary

No gaps. All 5 ROADMAP success criteria verified at four levels: (1) code exists and is substantive (all 20 artifacts checked), (2) wiring is live (every key link traced in source), (3) gates are green on the final tree (re-run this session: 796 tests, 8/8 required smokes, xtb probe), and (4) the live human checkpoint approved the real behavior 12/12 with an owner directive landed (048d929) and re-verified.

Two handoff observations (non-blocking, already recorded in 06-12): Phase-7 plan docs still cite the pre-amendment `%TEMP%/srp_spectra` default — Phase 7 must read artifact paths via the `spectra_run` record, not re-derive the location; and smoke 02's informational FAIL remains pre-existing/unrelated.

---

_Verified: 2026-09-26T17:14:07Z_
_Verifier: OpenCode (gsd-verifier)_
