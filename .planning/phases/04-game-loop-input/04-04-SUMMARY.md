---
phase: 04-game-loop-input
plan: 04
subsystem: input
tags: [pymol-wizard, do-special, arrow-keys, keyboard-steering, headless-smoke, bridge-purity]

# Dependency graph
requires:
  - phase: 04-game-loop-input (plan 04-01)
    provides: "serpentrum/input.py pre-registered in check_purity BRIDGE_MODULES"
  - phase: 04-game-loop-input (plan 04-03)
    provides: "pymol_bridge move_head_delta/lock_camera/object_exists + smoke-05 template"
provides:
  - "KeySteerWizard (serpentrum/input.py, BRIDGE) — arrow-key steering via do_special, the ONLY route receiving up/down"
  - "install/set_active/teardown lifecycle seam (opaque-handle teardown uniformity with the eventFilter fallback)"
  - "REQUIRED headless smoke 06 (SMOKE-OK INPUT-WIZARD) machine-proving mask 12, dispatch order, lifecycle round-trips, zero key_mappings leak"
  - "Real-GUI keys harness smoke/manual_wizard_keys_check.py staged for plan 04-07 human-verify"
affects: [04-05 GameTab, 04-07 keys human-verify, 04-08 play wiring, gui_input fallback gap-plan]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Wizard do_special steering route with MANDATORY event_mask override (key+special=12)"
    - "Stateless input layer: steer callback IS engine.request_direction; return value ignored (engine is sole authority)"
    - "Pause via set_active(False): wizard stays installed, grabs-but-no-ops — no frame-step leak, no key_mappings mutation"
    - "Opaque-handle teardown(handle=None) uniformity so a route swap (wizard <-> eventFilter) is a one-line import change"

key-files:
  created:
    - serpentrum/input.py
    - smoke/06_input_smoke.py
    - smoke/manual_wizard_keys_check.py
  modified:
    - tests/run_gates.py (REQUIRED_SMOKES += smoke/06_input_smoke.py)
    - AGENTS.md (steering convention bullet)

key-decisions:
  - "Wizard do_special route is PRIMARY (only route receiving up/down — set_key is C-blocked for up/down and leaks key_mappings); Qt eventFilter stays the designed FALLBACK, only built if plan 04-07 human-verify fails"
  - "do_special ALWAYS returns True (grab): suppresses the left/right movie-frame-step default; up/down grab is unconditional in C anyway"
  - "teardown(handle=None) accepts-and-ignores the handle so GameTab wiring (04-08) is route-agnostic across both input routes"

patterns-established:
  - "Steering convention (AGENTS.md): KeySteerWizard save/restore via cmd.set_wizard(prior); NEVER cmd.set_key for arrows"
  - "manual_* harness naming in smoke/ for real-GUI probes (non-NN_ name keeps run_gates from auto-running headless)"

# Metrics
duration: 13 min
completed: 2026-09-13
---

# Phase 4 Plan 04: Wizard Steering Input Route Summary

**KeySteerWizard arrow-key steering layer (event_mask 12, do_special dispatch to engine.request_direction) with leak-free install/set_active/teardown lifecycle — machine-proven headless by REQUIRED smoke 06 and staged for the plan 04-07 real-GUI keys human-verify.**

## Performance

- **Duration:** 13 min
- **Started:** 2026-09-13T18:03:49Z
- **Completed:** 2026-09-13T18:16:58Z
- **Tasks:** 3
- **Files modified:** 5 (3 created, 2 modified)

## Accomplishments

- **Primary input route landed (GAME-03 hinge):** `serpentrum/input.py` (BRIDGE) implements `KeySteerWizard(Wizard)` exactly per the research sketch — `get_event_mask()` returns `event_mask_key + event_mask_special` (= 12, MANDATORY: the base returns pick+select and `do_special` never fires without `event_mask_special`), `do_special` maps GLUT codes 100/101/102/103 to `left`/`up`/`right`/`down` and forwards to the injected steer callback, always returning True (grab). Zero `.set_key(` call sites anywhere in `serpentrum/`; `cmd.key_mappings` is never mutated.
- **Mechanism machine-proven headless:** `smoke/06_input_smoke.py` (registered REQUIRED in `tests/run_gates.py`) proves all 8 researched claims — mask==12, ordered dispatch left/up/right/down, unmapped-code grab-but-no-op (F1=1), idempotent install, pause gate (grabs-but-no-ops then steers again), idempotent teardown with opaque-handle acceptance, prior-wizard save/restore round-trip (foreign base Wizard restored), and zero key_mappings leak (up/down stay None). Full `--smoke` gate now echoes all five sentinels: SKELETON, VIEWER-BRIDGE, VIEWER-DEMO, LOOP-CAMERA, INPUT-WIZARD.
- **Live verify staged:** `smoke/manual_wizard_keys_check.py` (non-NN_ name — never auto-run headless) is the real-GUI harness for the plan 04-07 W7 checkpoint: materialized demo scene, wizard installed with a print + 0.3 A nudge steer seam (visible without a tick loop), `srp_keys_off` teardown command. AGENTS.md documents the steering convention.

## Task Commits

Each task was committed atomically on `exec/04-04` (iso-worktree, parallel wave):

1. **Task 1: serpentrum/input.py — KeySteerWizard + lifecycle (BRIDGE)** - `be8f5ec` (feat)
2. **Task 2: Headless smoke 06 (input mechanism) + REQUIRED registration** - `596e76d` (test)
3. **Task 3: Real-GUI keys harness + AGENTS.md convention** - `8f580a4` (docs)

**Plan metadata:** _see final commit_ (docs: complete plan)

## Files Created/Modified

- `serpentrum/input.py` — KeySteerWizard + install/set_active/teardown (BRIDGE purity; pymol.wizard + pymol.cmd at module level, no Qt/numpy, no .exec_())
- `smoke/06_input_smoke.py` — REQUIRED headless smoke, sentinel `SMOKE-OK INPUT-WIZARD` (8 steps)
- `smoke/manual_wizard_keys_check.py` — real-GUI keys harness (human runs it from PyMOL's command line; `srp_keys_off` restores)
- `tests/run_gates.py` — REQUIRED_SMOKES += `smoke/06_input_smoke.py` (now 01/03/04/05/06)
- `AGENTS.md` — single convention bullet under plugin gates & conventions

## Decisions Made

- Followed the research bottom line verbatim: wizard `do_special` PRIMARY, eventFilter FALLBACK (not built here — only if plan 04-07 human-verify fails), set_key NEVER.
- `teardown(handle=None)`: restores by reading `_saved_wizard` off the live wizard (never the caller's handle), keeping repeated teardown safe and route-swaps one-line.

## Deviations from Plan

None - plan executed exactly as written. (One trivial polish inside tasked scope: the harness prints the prompt from the installed wizard via `cmd.get_wizard().get_prompt()` instead of constructing a throwaway wizard — same output, no second object.)

## Issues Encountered

None. Smoke 06 passed on its first run; both gate legs green on first verification.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **Plan 04-07 (keys human-verify):** ready — run `run smoke\manual_wizard_keys_check.py` from the PyMOL command line in the real Windows GUI; the checklist lives in 04-RESEARCH-input.md (W7 live dispatch is the gate; focus stealing Q3 + W8 cosmetic churn expected).
- **Plan 04-08 (play wiring):** the seam is fixed — `GameTab._begin_play/_teardown_round` call `input.install(engine.request_direction)` / `input.set_active(bool)` / `input.teardown(prior)` route-agnostically.
- **Blockers/carried concern:** W7 (live C dispatch on a real keypress) remains `[ASSUMPTION-needs-human-verify]` by design — headless cannot generate key events; that verdict is plan 04-07's job, failure-cheap per the roadmap.

---
*Phase: 04-game-loop-input*
*Completed: 2026-09-13*
