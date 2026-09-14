---
phase: 04-game-loop-input
plan: 09
subsystem: testing
tags: [pymol, gates, human-verify, smoke, game-loop, steering, hud, locked-camera, teardown, leak-check]

# Dependency graph
requires:
  - phase: 04-06
    provides: "Start flow dialog wiring (SetupTab start_requested -> Game tab -> begin_game)"
  - phase: 04-07
    provides: "Keys checkpoint APPROVED — KeySteerWizard do_special is the shipping input route"
  - phase: 04-08
    provides: "Play lifecycle wiring — camera lock + steering arm at GO!, ONE _teardown_round on every end path, pause steering-gated, focus auto-pause + dialog-close teardown"
provides:
  - "Phase 4 closed: all automated gates green (451 tests, 5 REQUIRED smokes) + human-verify APPROVED 12/12 in real Windows PyMOL 2.5.0"
  - "Full playable loop verified live: Start -> Game tab -> 3-2-1-GO! -> constant-speed movement -> 4-key steering -> locked 2D camera -> HUD -> pause/resume -> deterministic restart -> crash verdict + run-over -> leak-free teardown (crash / dialog-close / plugin-reload)"
  - "Phase 4 success criteria SC1-SC5 (GAME-01/02/03/07/08) each human-confirmed live"
affects: [Phase 5, Phase 8]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Phase-closing verification ritual: full gate pass (fix anything red first) -> consolidated human-verify checklist mapped 1:1 onto phase success criteria -> recorded per-step verdict table"
    - "By-design observations recorded as plan-miscalibration / designed-latency notes, NOT defects — speed locked at 3.0 A/s (GAME-08); turn application at next 100 ms tick boundary recorded as a potential future game-feel tuning knob"

key-files:
  created: []
  modified: []   # zero code changes under this plan — clean gate pass, zero fixes needed

key-decisions:
  - "Step-3 wall-crossing ~6 s on medium is CORRECT game behavior (3.0 A/s locked, GAME-08); the PLAN's 'roughly 2 minutes' expectation text was miscalibrated — recorded as a plan note, not a game defect"
  - "Step-4 '<1 s pause before direction change' is the DESIGNED next-tick turn application (engine buffers max-1 direction request, applied at the next 100 ms tick); potential future game-feel tuning knob (tick cadence), NOT changed now — GAME-08 locks speed and cadence changes belong to a deliberate later decision"

patterns-established:
  - "Clean-pass phase closing: when gates are green with zero fixes, no code commits are made ('a clean pass needs no commit') and the SUMMARY records the evidence table instead"

# Metrics
duration: ~15min (+ human-verify checkpoint)
completed: 2026-09-13
---

# Phase 4 Plan 09: Phase-Closing Gate Pass + Human-Verify Summary

**PHASE-CLOSING VERIFICATION APPROVED — all automated gates green (451 tests, 5 REQUIRED smokes) with ZERO fixes required, and 12/12 live human-verify steps PASS in real Windows PyMOL 2.5.0: the full playable snake loop (countdown, constant-speed movement, four-key steering, locked camera, HUD, pause/restart, crash, leak-free teardown) is confirmed working end-to-end**

## Meta

- **Plan:** 04-09 (phase 04-game-loop-input)
- **Completed:** 2026-09-13
- **Status:** PHASE-CLOSING VERIFICATION APPROVED (12/12 live steps + all automated gates green)

## Performance

- **Duration:** ~15 min executor time total (Task 1 clean gate pass by the earlier executor + this finalization), plus the human-verify checkpoint
- **Started:** 2026-09-13 (Task 1 gate pass)
- **Completed:** 2026-09-13 (checkpoint APPROVED + SUMMARY)
- **Tasks:** 2 (1 auto gate pass + 1 checkpoint:human-verify)
- **Files modified:** 0 code files (planning artifacts only)

## Accomplishments
- Every automated gate green on the completed Phase-4 surface with **zero fixes required**: default gates (syntax + plugin-path safety + purity AST + 451 unittest tests) and all five REQUIRED headless smokes
- Human-verify checkpoint APPROVED in real Windows PyMOL 2.5.0: **all 12 steps PASS**, covering GAME-01 (Start, countdown, continuous movement, crash end-of-run), GAME-02 (locked ortho 2D camera, box visible), GAME-03 (four-key steering mid-run), GAME-07 (HUD, pause/resume, deterministic restart), GAME-08 (constant speed), plus all three leak checks (post-crash restore, dialog-close teardown, plugin-reload safety)
- Two human observations recorded as by-design (not defects): plan step-3 timing estimate miscalibrated (~6 s wall crossing is correct at the locked 3.0 A/s); step-4 sub-second turn latency is the designed next-tick application
- Phase 4 success criteria (ROADMAP SC1-SC5 -> GAME-01/02/03/07/08) each confirmed live — Phase 4 is verifiably complete pending phase goal verification

## Task Commits

1. **Task 1: Full automated gate pass** — ALL GATES GREEN, zero fixes needed; **no commits made** (plan contract: "a clean pass needs no commit")
2. **Task 2: checkpoint:human-verify** — APPROVED 12/12 (checkpoint task; no code commit)

**Plan metadata:** `docs(04-09): phase-closing verification approved — full playable loop live` (this commit)

## Automated Gate Output (Task 1 — earlier executor run, verbatim)

All gate runs from the repo root (WSL), exit 0:

| Gate | Command | Verdict |
|------|---------|---------|
| 1 — syntax + plugin-path safety | `python3.6 tests/run_gates.py` | PASS — no top-level `*.py`, no `__init__.py` in tests/smoke/tools |
| 2 — purity AST | `python3.6 tests/run_gates.py` | PASS — **zero violations** (entry lazy, GUI allowlist pymol.Qt only, all else pure) |
| 3 — unittest suite | `python3.6 tests/run_gates.py` | PASS — **451 tests OK** |
| 4 — headless smokes | `python3.6 tests/run_gates.py --smoke` | PASS — all five sentinels flushed: **SMOKE-OK SKELETON, SMOKE-OK VIEWER-BRIDGE, SMOKE-OK VIEWER-DEMO, SMOKE-OK LOOP-CAMERA, SMOKE-OK INPUT-WIZARD** (verdict = flushed sentinels, NEVER exit codes through the .bat) |

- REQUIRED_SMOKES verified = **smoke/01, 03, 04, 05, 06** (`tests/run_gates.py:55-59`); the 04-06 INPUT-WIZARD smoke is present (frontmatter `contains:` satisfied).
- smoke/02 remains an informational FAIL = the documented 01-05 offscreen-dialog dead end — non-blocking by design.
- **Zero fixes required; zero commits made for Task 1** (plan: "a clean pass needs no commit").

## Human-Verify Verdicts (Task 2 — real Windows PyMOL 2.5.0, 12-step consolidated checklist)

| # | Expected | Actual | Verdict | Requirement mapping |
|---|----------|--------|---------|---------------------|
| 1 | Start -> Game tab switch; "3" "2" "1" "GO!" at ~1 s in the big label AND info box | Game tab switched; 3-2-1-GO! countdown in label + info box | PASS | GAME-01 |
| 2 | Head does NOT move until GO! | No movement before GO! | PASS | GAME-01 |
| 3 | Continuous forward movement at CONSTANT pace; never stops (~0.3 A/tick) | Head crossed the medium box to a wall in ~6 s at constant pace (see Observation 1 — plan estimate miscalibrated, speed correct) | PASS | GAME-01, GAME-08 |
| 4 | All four arrows steer mid-run; turn at next tick; 180-reversals refused | All four arrows steer; <1 s pause before direction change = designed next-tick application (see Observation 2) | PASS | GAME-03 |
| 5 | Camera immovable to all drags/wheel; ortho view; box fully visible throughout | "yes locked" — camera immovable, ortho, box visible | PASS | GAME-02 |
| 6 | HUD: elapsed from 0:00 matches wall clock; Remaining shown; info box logs countdown + steer hint + refusals | Elapsed/remaining/info box all correct | PASS | GAME-07 |
| 7 | Pause freezes instantly, flips label, freezes elapsed; Resume resumes with NO elapsed jump | Pause/resume works; no elapsed jump | PASS | GAME-07 |
| 8 | Restart re-runs countdown, recenters head, resets elapsed; exactly ONE countdown chain (Restart during "3" — no double timers) | Deterministic restart; single countdown chain | PASS | GAME-07 (epoch guard) |
| 9 | Wall hit: "crashed into boundary" logged; motion stops; run over (pause disabled) | Crash verdict logged; run over | PASS | GAME-01 (end-of-run) |
| 10 | Post-crash leak check: mouse rotates/zooms again; arrows don't steer; ortho restored | Everything behaves as before the game — leaks NONE | PASS | Teardown — Pitfall 9 |
| 11 | Close dialog mid-run: no further movement; mouse/keys normal; plugin reopens | Dialog-close teardown clean | PASS | Close-path teardown (Pitfall 9/7) |
| 12 | Plugin reload mid-game (re-add directory): exactly ONE dialog + ONE moving snake; OLD session's lock/wizard gone | Plugin-reload safety confirmed — no ghosts | PASS | Reload safety (INFRA-03, Pitfall 7/A) |

**Checkpoint resume-signal: APPROVED (ALL 12 STEPS PASS)** — human verdicts on real Windows PyMOL 2.5.0.

### Human-captured in-game info log (verbatim — evidence of the full loop; clears every restart)

```
Get ready...
3
2
1
GO!
Move with the arrow keys.
paused
resumed
crashed into boundary
run over: crashed
```

Countdown -> steer hint -> pause/resume -> crash verdict: the complete loop lifecycle in one log.

## Human Observations (by-design — recorded verbatim, NOT defects)

1. **Step 3 — wall-crossing time:** *"its 6s but reasonable, a box this small if 30s its too slow"*. The head reached a medium-box wall in ~6 s. The PLAN's step-3 expectation text ("reaches a box wall on the medium preset in roughly 2 minutes") was **miscalibrated** — not a game defect. Constant pace confirmed (GAME-08 holds); ~6 s crossing is the correct result for a small box at the locked 3.0 A/s. **No change made.**
2. **Step 4 — sub-second turn latency:** *"all work, but after clicking arrow once theres a <1s pause before it change direction"*. All four arrows steer mid-run; the <1 s latency is the **DESIGNED next-tick turn application** — direction requests buffer max-1 in the engine and the newest applies at the next 100 ms tick boundary (step 4's own EXPECT says "turn happens at the next tick"). **No change made.** Recorded as a **potential future game-feel tuning knob** (tick cadence) — GAME-08's speed stays locked at 3.0 A/s and cadence changes belong to a deliberate later decision, not a defect fix.

## Fixes Made Under This Plan

**NONE.** Gates were green with zero fixes (Task 1 clean pass, no commits), and the human-verify surfaced no defects — only the two by-design observations above.

## Phase 4 Success Criteria Mapping (ROADMAP SC1-SC5)

| SC | Roadmap text | Verify steps | Verdict |
|----|--------------|--------------|---------|
| SC1 | Start -> Game tab -> 3-2-1 countdown -> continuous movement without stopping [GAME-01] | 1, 2, 3, 9 | PASS |
| SC2 | Steer with all four arrow keys; movement never stops [GAME-03] | 4 | PASS |
| SC3 | 2D plane with locked camera; boundary box clearly visible throughout [GAME-02] | 5 | PASS |
| SC4 | Rolling info box, elapsed timer, molecules-remaining; pause/resume + restart mid-run [GAME-07] | 6, 7, 8 | PASS |
| SC5 | Speed is constant regardless of snake length [GAME-08] | 3 | PASS |

## Requirements Delivered (phase sign-off pending goal verification)

| Requirement | Phase | Status after 04-09 |
|-------------|-------|--------------------|
| GAME-01 (game loop: start/countdown/continuous movement) | 4 | Human-verify PASS (steps 1, 2, 3, 9) |
| GAME-02 (2D plane + locked camera) | 4 | Human-verify PASS (step 5) |
| GAME-03 (four-key steering) | 4 | Human-verify PASS (step 4) |
| GAME-07 (HUD, pause/resume, restart) | 4 | Human-verify PASS (steps 6, 7, 8) |
| GAME-08 (constant speed) | 4 | Human-verify PASS (step 3) |

## Absent-by-Design Reminders (for the phase verifier — NOT defects)

- **Head shows the as-stored SDF orientation** (ring flat on the xy board) — edge-on presentation is the Phase-5 recorded decision (03-08 SUMMARY; the user's 04-07 remark is recorded in STATE.md Pending Todos). No stacking exists yet, so orientation is cosmetic in Phase 4.
- **No pickups / stacking / win handoff** — Phase 5 scope; absence here is by design.
- **The molecule never rotates during movement** — translation only is the Phase 4 contract (bridge move_head_delta).

## Decisions Made

- Recorded: step-3 plan timing estimate was miscalibrated (~6 s wall crossing is correct at the locked 3.0 A/s; GAME-08 holds) — a plan note, not a defect.
- Recorded: turn application at the next 100 ms tick boundary (engine buffers max-1, newest-in-buffer wins) is the designed behavior; sub-second perceived latency is a potential future game-feel tuning knob — deferred deliberately; GAME-08 speed stays locked.
- Both observations carry no code changes; they inform future tuning decisions only.

## Deviations from Plan

None — plan executed exactly as written. Task 1 was a clean gate pass (zero fixes, zero commits, as the plan's contract provides); Task 2's checkpoint returned APPROVED with two by-design observations that required no in-plan fix work. No gate weakened, no purity class violated, no Phase-5 scope creep.

## Issues Encountered

None. (The two human observations are recorded in the by-design section above.)

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Phase 4 (plans 04-01..04-09) is COMPLETE: all automated gates green (451 tests, 5 REQUIRED smokes), 12/12 live steps PASS in real Windows PyMOL 2.5.0, teardown/leak/reload checks all clean.
- **Next:** phase goal verification (gsd-verifier, spawned from the execute-phase orchestrator) -> ROADMAP/REQUIREMENTS status updates -> **Phase 5: Stacking & Game Rules Complete**.
- Phase 5 consumes: setloader records (incl. demo ring_atoms — extract ONE planar 6-ring, biphenyl trap), edge-on ring orientation at materialization/placement (03-08 recorded decision + 04-07 user remark), BOX_DISPLAY_Z 5.0 vs 6.0 decision, stacking placement math + clash gate, GAME-10 sweep machinery (engine referee already sweeps/refuses), pickup teardown folded INTO `_teardown_round` (never a second helper, 04-08).
- Optional future tuning knob recorded: tick cadence (game feel) — speed stays locked at 3.0 A/s (GAME-08).

---
*Phase: 04-game-loop-input*
*Completed: 2026-09-13*
