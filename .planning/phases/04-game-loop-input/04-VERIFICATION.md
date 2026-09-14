---
phase: 04-game-loop-input
verified: 2026-09-14T19:52:33Z
status: passed
score: 40/40 must-haves verified (35/35 plan truths + 5/5 phase success criteria)
gaps: []
re_verification: null
---

# Phase 4: Game Loop & Input — Verification Report

**Phase Goal:** The snake moves under arrow-key control on a 2D locked-camera plane with countdown, HUD, pause and restart — the first playable (if not yet stackable) motion.
**Verified:** 2026-09-14T19:52:33Z
**Status:** PASSED
**Re-verification:** No — initial verification
**Verifier mode:** Goal-backward. SUMMARY claims were cross-checked against the actual codebase at three levels (exists / substantive / wired), gates were re-run by the verifier, and the recorded human verdicts (04-07 + 04-09) were treated as authoritative GUI/live evidence per the project's binding 01-05 decision (headless widget construction is a dead end — GUI behavior cannot be verified headlessly).

## Goal Achievement

### Verification performed by this run

1. **Gates re-executed by the verifier (not trusted from SUMMARYs):**
   - `python3.6 tests/run_gates.py` → gates 1–3 PASS: syntax + plugin-path safety, purity AST (zero violations, incl. `RealRepoCleanTest`), **451 unittest tests OK**, exit 0.
   - `python3.6 tests/run_gates.py --smoke` → gates 1–4 PASS, exit 0. All five REQUIRED smokes flushed their sentinels: `SMOKE-OK SKELETON`, `SMOKE-OK VIEWER-BRIDGE`, `SMOKE-OK VIEWER-DEMO`, `SMOKE-OK LOOP-CAMERA`, `SMOKE-OK INPUT-WIZARD`. `smoke/02` informational FAIL = the documented 01-5 offscreen-dialog dead end (non-blocking by design).
2. **All 9 plans' `must_haves` checked against actual code** (grep/read of `serpentrum/input.py`, `gui_game.py`, `gui.py`, `gui_setup.py`, `pymol_bridge.py`, `hud_logic.py`, `__init__.py`, `game_engine.py`, smokes 05/06, `tests/run_gates.py`, `tests/test_hud_logic.py`, `tests/test_purity_gates.py`, `tools/check_purity.py`).
3. **Human evidence treated as authoritative:** `04-09-SUMMARY.md` (12/12 live steps APPROVED in real Windows PyMOL 2.5.0, with SC1–SC5 mapping table + verbatim in-game log) and `04-07-SUMMARY.md` (keys checkpoint APPROVED — wizard route ships, fallback not needed).

### Observable Truths — Phase success criteria (ROADMAP SC1–SC5)

| # | Truth (success criterion) | Requirement | Status | Evidence |
|---|---------------------------|-------------|--------|----------|
| 1 | Click Start → dialog switches to Game tab → counts down 3-2-1 → head moves forward continuously without stopping | GAME-01 | ✓ VERIFIED | Wiring: `gui_setup.py:135,486-496` (Start button → `_on_start` = apply-then-emit `start_requested`), `gui.py:74,81-91` (signal → `setCurrentIndex(1)` + `begin_game`), `gui_game.py:157-185` (teardown-first → engine build → anchor → countdown), `:205-223` (epoch-guarded singleShot chain), `:230-250` (`_begin_play` arms lock+steering then starts timers). Human: 04-09 steps 1,2,3,9 PASS ("Game tab switched; 3-2-1-GO!", "No movement before GO!", constant crossing, crash end-of-run). Verbatim log: `Get ready... 3 2 1 GO! Move with the arrow keys. ... crashed into boundary / run over: crashed`. |
| 2 | Steer with all four arrow keys (up/down spike resolved with designed fallback if needed); movement never stops | GAME-03 | ✓ VERIFIED | Spike RESOLVED at the cheap checkpoint, wizard route (no fallback needed — `gui_input.py` correctly NOT built; only referenced as the documented one-line swap in comments): `input.py:87-90` mask 12, `:65,101-111` GLUT 100/101/102/103 → left/up/right/down → steer callback, always-grab. Machine proof: smoke/06 asserts mask==12, ordered dispatch, lifecycle round-trips, `key_mappings` untouched → `SMOKE-OK INPUT-WIZARD`. Live proof: 04-07 APPROVED (all four arrows dispatch through `do_special` in real PyMOL; left/right movie-step suppressed; teardown restores). 04-09 step 4 PASS mid-run. Never-stops: engine advances every tick (`game_engine.py:660-661`), pause only via explicit engine.pause. |
| 3 | 2D plane with locked camera; boundary box clearly visible throughout | GAME-02 | ✓ VERIFIED | `pymol_bridge.py:164-176` `move_head_delta` — `cmd.translate(..., camera=0)` model axes, dz=0.0 (2D contract; smoke/05 asserts exact 5×0.3→1.5 Å with y/z untouched). `:179-195` `lock_camera` — saves `{ortho, view}`, ortho on, `zoom(srp_box)` (whole box, never srp_*), all 16 button combos → 'none'. `:198-212` `unlock_camera` restores mouse/ortho/18-float view. Locked for the WHOLE run incl. pause (04-08 research D5 — no unlock in `_apply_pause_state`). Human: 04-09 step 5 PASS ("camera immovable, ortho, box visible"), step 10 (post-run restore clean). |
| 4 | Rolling info box, elapsed timer, molecules-remaining; pause/resume + restart work mid-run | GAME-07 | ✓ VERIFIED | HUD: `gui_game.py:107-148` (28-pt countdown label, read-only `info_box`, elapsed + remaining labels, pause/restart buttons), `:279-293` (`turn_refused`/`crashed`/`won` → info box), `:294-311` (elapsed = `time.time() - start_time - paused_accum`, clamped ≥0, via `hud_logic.format_elapsed` — wall-clock delta, never tick counts), `:313-320` (`hud_logic.remaining_text(engine.molecules_remaining)`). Pure math WSL-tested: `hud_logic.py:14-37` + `tests/test_hud_logic.py` (13 tests OK). Pause/resume: `:334-367` (same-timer stop/start, `paused_accum += now - pause_time` rebase, `set_active(False/True)`, camera stays locked); restart: `:389-403` (epoch-guarded re-run, head re-center via `object_exists`+`place_head`). Human: 04-09 steps 6,7,8 PASS (no elapsed jump; single countdown chain on restart-during-"3"). |
| 5 | Speed is constant regardless of snake length | GAME-08 | ✓ VERIFIED | `game_engine.py:55` `SPEED_A_PER_S = 3.0`; `:660-661` head += heading·SPEED·dt — length-independent; `gui_game.py:66-67` fixed `TICK_DT=0.1`/100 ms (deterministic engine, jitter eaten by QTimer). `test_engine_core.test_speed_constant_pinned` OK. Human: 04-09 step 3 PASS (constant pace, medium box crossed in ~6 s — the PLAN's "2 minutes" expectation text was miscalibrated, recorded as a plan note, not a defect; 3.0 Å/s is the locked GAME-08 speed). |

**Phase score:** 5/5 success criteria verified.

### Per-plan must-have verification (9 plans, 35 truths)

| Plan | Truths | Verdict | Key evidence |
|------|--------|---------|--------------|
| 04-01 purity pre-registration | 3/3 | ✓ VERIFIED | `tools/check_purity.py:62-63` GUI_MODULES contains `serpentrum/gui_game.py`; `:73` BRIDGE_MODULES contains `serpentrum/input.py`; `tests/test_purity_gates.py:335-432` fixture cases pin both classifications; `test_real_repo_clean` OK (re-run by verifier). |
| 04-02 HUD display helpers (TDD) | 3/3 | ✓ VERIFIED | `hud_logic.py:14-25` format_elapsed (floored, clamped), `:28-37` remaining_text None-safe; `game_engine.py:273` `molecules_remaining` property; `tests/test_hud_logic.py` 106 lines, 13 tests OK. Wired: `gui_game.py:311,320`. |
| 04-03 bridge movement + locked camera | 4/4 | ✓ VERIFIED | `pymol_bridge.py:164-222` all four functions; smoke/05 asserts zero-drift translate (dx==1.5, y/z equal), ortho off→on, 18-float view, unlock round-trip, `object_exists` true/false, cleanup_srp scope; `tests/run_gates.py:58` REQUIRED. Sentinel flushed this run. |
| 04-04 KeySteerWizard input route | 4/4 | ✓ VERIFIED | `input.py:65` code map, `:87-90` mask 12, `:101-111` do_special (unmapped no-op, always grab), `:116-158` install/set_active/teardown (idempotent, prior save/restore, `key_mappings` never touched); smoke/06 machine-proves all of it (sentinel flushed this run); `smoke/manual_wizard_keys_check.py:96` `srp_keys_off` harness staged. |
| 04-05 GameTab HUD + session | 5/5 | ✓ VERIFIED | `gui_game.py` 460 lines (≥200 required), `class GameTab`; begin_game teardown-first + engine seed (head (0,0), heading 'right', `pickups=None`, cap/atom_budget) + head re-center + anchor + countdown (`:157-185`); 100 ms tick → `engine.step` → `move_head_delta` (`:254-277`); wall-clock elapsed w/ paused_accum (`:294-311`); pause rebase + epoch-guarded restart (`:334-403`); session anchored on `_serpentrum.game_session` (`:180-181`; `__init__.py:26-31` field on `_SerpentrumState`, first-anchor-only creation); QTimers Qt-parent-owned (`:95-100`). |
| 04-06 Start → Game tab wiring | 3/3 | ✓ VERIFIED | `gui_setup.py:68` `start_requested = QtCore.Signal(object)`, `:135` Start button, `:407` `_on_apply` returns bool, `:486-496` apply-then-emit; `gui.py:60-63` GameTab registered as page 1 (Setup→Game→Spectra preserved), `:74` signal connect, `:81-91` `setCurrentIndex(1)` + `begin_game(setup)`; Spectra placeholder + reserved bottom row untouched (`gui.py:19-23,75-79`). |
| 04-07 keys human checkpoint | 4/4 | ✓ VERIFIED (human, binding) | 04-07-SUMMARY: checkpoint **APPROVED** (2026-09-13, real Windows PyMOL 2.5.0) — all four arrows dispatch through the wizard route (W7 live), left/right movie-step grabbed (W4), up/down history churn cosmetic (W8), focus click-viewer UX ACCEPTED (Q3), `srp_keys_off` teardown restores prior wizard (W5). Fallback route correctly NOT built. |
| 04-08 play lifecycle wiring | 4/4 | ✓ VERIFIED | `gui_game.py:230-250` `_begin_play` = lock_camera + `game_input.install(engine.request_direction)` BEFORE timers (same instant, GUI thread); `:421-449` ONE `_teardown_round` (idempotent: timers → epoch bump → input teardown → `unlock_camera(session.pop('saved_cam'))` → blockSignals button reset) called from EVERY end path (`begin_game:169`, `_on_restart:402`, `_end_run:414`, `shutdown:419`); pause gates steering via `set_active(False)`, camera stays LOCKED (`:354`, no unlock in `_apply_pause_state`); `gui.py:93-105` `focusInEvent` → `request_auto_pause` (guards `status=='playing'`), `:107-118` `closeEvent` → `shutdown()`. |
| 04-09 phase-closing gates + final human verify | 5/5 | ✓ VERIFIED | Gates re-run by THIS verifier: 451 tests OK + 5/5 REQUIRED sentinel flushes (gates 1–4 PASS). Human: 12/12 live steps APPROVED in real PyMOL 2.5.0 (04-09 verdict table), SC1–SC5 mapped 1:1, verbatim in-game log captured, all three leak checks clean (post-crash restore, dialog-close teardown, plugin-reload safety). `tests/run_gates.py:59` contains smoke/06. |

**Plan-truth score:** 35/35 verified.

### Required Artifacts

| Artifact | Expected | Exists | Substantive | Wired | Status |
|----------|----------|--------|-------------|-------|--------|
| `serpentrum/input.py` | KeySteerWizard + install/set_active/teardown (BRIDGE), ≥80 lines, `class KeySteerWizard` | ✓ | ✓ 158 lines, no stubs | ✓ imported as `game_input` by `gui_game.py:59`; install `:244`, set_active `:354,361`, teardown `:440` | ✓ VERIFIED |
| `serpentrum/gui_game.py` | GameTab: countdown, info box, HUD labels, pause/restart, 2 QTimers, epoch guard, `_teardown_round`; ≥200 lines | ✓ | ✓ 460 lines, no stubs | ✓ registered page 1 by `gui.py:60-61`; begin_game called `:91` | ✓ VERIFIED |
| `serpentrum/gui.py` | GameTab page-1 registration + Start transition + focusInEvent/closeEvent hooks | ✓ | ✓ 127 lines | ✓ `setCurrentIndex(1)`+`begin_game` `:90-91`; auto-pause `:105`; shutdown `:117` | ✓ VERIFIED |
| `serpentrum/gui_setup.py` | `start_requested` signal + temp Start button + apply-then-emit | ✓ | ✓ 502 lines | ✓ connected `gui.py:74`; emits `collect_state()` `:496` | ✓ VERIFIED |
| `serpentrum/pymol_bridge.py` | `move_head_delta` (camera=0), `lock_camera`/`unlock_camera`, `object_exists` | ✓ | ✓ 275 lines | ✓ called per-tick `gui_game.py:274`; lock `:243`, unlock `:444` | ✓ VERIFIED |
| `serpentrum/hud_logic.py` | PURE `format_elapsed` + `remaining_text`; ≥25 lines | ✓ | ✓ 37 lines | ✓ `gui_game.py:311,320` | ✓ VERIFIED |
| `serpentrum/__init__.py` | `game_session` field on `_SerpentrumState` | ✓ | ✓ `:26-31` documented field, first-anchor-only init | ✓ written by `gui_game.py:181` | ✓ VERIFIED |
| `serpentrum/game_engine.py` | `SPEED_A_PER_S`, `step`, `request_direction`, `pause`/`resume`, `molecules_remaining` | ✓ | ✓ 798 lines, 451-test suite green | ✓ engine methods called from `gui_game.py` tick/pause/restart paths | ✓ VERIFIED |
| `tools/check_purity.py` | BRIDGE gains input.py; GUI gains gui_game.py | ✓ | ✓ `:62-63,73` | ✓ enforced by gates 2 (PASS this run) | ✓ VERIFIED |
| `tests/test_purity_gates.py` | Fixture cases for both new classifications | ✓ | ✓ 448 lines; cases 25–27 pin input.py BRIDGE + gui_game.py GUI | ✓ gate 2 | ✓ VERIFIED |
| `tests/test_hud_logic.py` | Unit tests for elapsed/remaining/engine property; ≥40 lines | ✓ | ✓ 106 lines, 13 tests OK | ✓ gate 3 | ✓ VERIFIED |
| `tests/run_gates.py` | REQUIRED_SMOKES incl. smoke/05 + smoke/06 | ✓ | ✓ `:55-59` covers 01/03/04/05/06 | ✓ gate 4 re-run by verifier: all 5 flushed | ✓ VERIFIED |
| `smoke/05_loop_camera_smoke.py` | REQUIRED; zero-drift + lock/restore round-trip; `SMOKE-OK LOOP-CAMERA` | ✓ | ✓ 163 lines, assert-backed | ✓ gate 4: sentinel flushed this run | ✓ VERIFIED |
| `smoke/06_input_smoke.py` | REQUIRED; mask==12, dispatch, lifecycle, no key_mappings leak; `SMOKE-OK INPUT-WIZARD` | ✓ | ✓ 187 lines, assert-backed | ✓ gate 4: sentinel flushed this run | ✓ VERIFIED |
| `smoke/manual_wizard_keys_check.py` | Real-GUI harness, `srp_keys_off` teardown cmd, not NN_-prefixed | ✓ | ✓ 115 lines | ✓ used by the 04-07 APPROVED live checkpoint | ✓ VERIFIED |

### Key Link Verification

| From | To | Via | Status |
|------|----|----|--------|
| `gui_setup.py` (Start click) | `gui.py` | `start_requested(setup)` signal → `_on_start_requested` | ✓ WIRED |
| `gui.py` | `gui_game.py` | `setCurrentIndex(1)` + `begin_game(setup)` | ✓ WIRED |
| `gui_game.py` countdown | `_begin_play` | epoch-guarded singleShot chain (`scheduled != self._epoch` no-op) | ✓ WIRED |
| `_begin_play` | `pymol_bridge.lock_camera` | `session['saved_cam'] = lock_camera()` before timers | ✓ WIRED |
| `_begin_play` | `input.install` | `install(session['engine'].request_direction)` — steer callback IS the engine seam | ✓ WIRED |
| `_on_tick` | `game_engine.step` | `engine.step(TICK_DT)` per 100 ms; `('moved',)` → bridge | ✓ WIRED |
| `_on_tick` | `pymol_bridge.move_head_delta` | delta = engine's own increment, `camera=0`, dz=0.0 | ✓ WIRED |
| `_on_elapsed_tick` | `hud_logic.format_elapsed` | wall-clock delta − paused_accum, clamped | ✓ WIRED |
| `_update_remaining` | `hud_logic.remaining_text` ∘ `engine.molecules_remaining` | HUD reads the derived property, not raw arithmetic | ✓ WIRED |
| pause/resume | `input.set_active` | False/True around the paused_accum rebase; camera untouched | ✓ WIRED |
| every end path | `_teardown_round` | begin_game / _on_restart / _end_run / shutdown all funnel to ONE helper | ✓ WIRED |
| `_teardown_round` | `pymol_bridge.unlock_camera` | `unlock_camera(session.pop('saved_cam', None))` — double-unlock impossible by construction | ✓ WIRED |
| `gui.py focusInEvent` | `gui_game.request_auto_pause` | guards `status=='playing'`; blockSignals re-entry guard | ✓ WIRED |
| `gui.py closeEvent` | `gui_game.shutdown` | mid-game dialog close tears down timers+wizard+camera | ✓ WIRED |
| `GameTab` | `_serpentrum.game_session` | session dict anchored on the state object (`__init__.py:26-31`), never module globals | ✓ WIRED |
| real arrow keys | `input.do_special` | C `PyMOL_Special` → `WizardDoSpecial` → `do_special` → steer — human-APPROVED live (04-07) | ✓ WIRED (human evidence) |

### Requirements Coverage

| Requirement | Phase | Status | Blocking Issue |
|-------------|-------|--------|----------------|
| GAME-01 — Start → Game tab → 3-2-1 → movement starts | 4 | ✓ SATISFIED | none |
| GAME-02 — 2D plane, locked camera, boundary visible | 4 | ✓ SATISFIED | none |
| GAME-03 — continuous movement, 4-arrow steering (cannot stop) | 4 | ✓ SATISFIED | none (pickup-stick rendering is Phase-5 scope — the head-spheres half renders) |
| GAME-07 — info box, elapsed, molecules-remaining, pause/resume, restart | 4 | ✓ SATISFIED | none |
| GAME-08 — constant speed | 4 | ✓ SATISFIED | none |

Note: the REQUIREMENTS.md checkboxes still read "Pending" — updating ROADMAP/REQUIREMENTS status is the orchestrator's post-verification step, not a code gap.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `serpentrum/gui.py` | 9, 33 | "placeholder" — refers to the Spectra tab, Phase 7 scope | ℹ️ Info | By-design absent content, not a stub |
| `serpentrum/pymol_bridge.py` | 229 | "Phase-3 placeholder" — docstring note about 'random'→records[0] | ℹ️ Info | Documented decision, not stub code |
| `serpentrum/gui_game.py`, `input.py` | 56–58, 47–50 | `gui_input` fallback referenced in comments only | ℹ️ Info | Correct per 04-07 APPROVED verdict (fallback deliberately not built); one-line swap seam documented |

No TODO/FIXME/HACK markers, no empty handlers, no `console.log`-only paths, no `.exec_()` calls anywhere in the phase surface. **Zero blocker or warning anti-patterns.**

### Human Verification Required

**None outstanding.** GUI/live verdicts are already human-verified and recorded, per this project's binding 01-05 decision (headless widget construction is a dead end):

- **04-07 keys checkpoint — APPROVED (2026-09-13):** all four arrow keys dispatch through the wizard route in real Windows PyMOL 2.5.0; teardown restores the prior wizard; click-viewer focus UX accepted for v1.
- **04-09 phase-closing checkpoint — APPROVED 12/12 (2026-09-14):** full playable loop live in real PyMOL (Start → Game tab → 3-2-1-GO! → constant-speed movement → 4-key steering → locked ortho camera with box visible → HUD → pause/resume without elapsed jump → deterministic restart → crash verdict → leak-free teardown incl. plugin-reload safety), with a verbatim in-game info log as evidence.

Two human observations from the live run are recorded as **by-design, not defects** (04-09): (1) the plan's "roughly 2 minutes" wall-crossing estimate was miscalibrated — ~6 s at the locked 3.0 Å/s is correct (GAME-08 holds); (2) sub-second turn latency is the designed next-tick application of the buffered direction (potential future game-feel tuning knob, deliberately deferred).

### Absent-by-Design (NOT gaps)

- No pickups / stacking / win-handoff — Phase 5 scope (`pickups=None` seeded deliberately; 'won' unreachable and kept for Phase 5).
- Head shows the as-stored SDF orientation — edge-on presentation is the recorded Phase-5 decision (03-08 SUMMARY).
- Molecule never rotates during movement — Phase 4 is translation-only by contract (`move_head_delta`).

### Gaps Summary

**No gaps.** Every phase-level success criterion (5/5) and every per-plan must-have truth (35/35 across 9 plans) is verified against the actual codebase: all 15 required artifacts exist, are substantive, and are wired; all 16 key links are connected (verified by read, not by trusting summaries); both gate runs were re-executed by the verifier and are green (451 tests, 5/5 required smoke sentinels); and the GUI/live half of the goal is covered by the recorded, authoritative human APPROVED verdicts (04-07 + 04-09). The single open mechanism question of the phase (up/down arrow bindability) was resolved at the failure-cheap 04-07 checkpoint with the wizard route APPROVED — no fallback needed, and the route-agnostic seam remains as insurance.

---

_Verified: 2026-09-14T19:52:33Z_
_Verifier: OpenCode (gsd-verifier)_
