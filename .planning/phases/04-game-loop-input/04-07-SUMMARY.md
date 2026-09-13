---
phase: 04-game-loop-input
plan: 07
subsystem: testing
tags: [pymol, human-verify, wizard, do_special, arrow-keys, input-route, checkpoint]

# Dependency graph
requires:
  - phase: 04-04
    provides: "serpentrum/input.py KeySteerWizard (do_special route, event mask 12) + smoke/manual_wizard_keys_check.py real-GUI harness"
provides:
  - "Human verdict APPROVED: the KeySteerWizard do_special route is the SHIPPING input route — plan 04-08 wires it; no eventFilter fallback needed (serpentrum/gui_input.py NOT built)"
  - "Live proof of W7: all four arrow keys (up/down included) reach do_special in real Windows PyMOL 2.5.0 — set_key could never do this"
  - "Live proof of W4 (no movie-frame stepping) + W5 teardown/prior-wizard restore (bioCHEMeleon save/restore pattern proven live) + W8 (up/down history churn cosmetic)"
  - "Focus UX verdict: click-viewer-to-steer ACCEPTED for v1; plan 04-08's auto-pause-on-focus is the safety net"
  - "User orientation remark recorded: head shows the as-stored SDF orientation (ring flat on the board); edge-on orientation (03-08 carried-forward Phase-5 task) must land BEFORE any stacking"
affects: [Phase 4 (04-08, 04-09), Phase 5]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Early human-verify of the one open mechanism question before dependent plans pile on (roadmap: 'first human-verify of keys happens here so failure is cheap') — APPROVED, fallback not needed"
    - "No-tick harness interpretation: request_direction=False flood after the first press is CORRECT engine authority (direction buffer max 1 never drains without the 100 ms tick), not a defect"

key-files:
  created: []
  modified: []

key-decisions:
  - "Keys checkpoint APPROVED (2026-09-13): KeySteerWizard do_special route ships; no gui_input.py eventFilter fallback built"
  - "Click-viewer-to-steer UX accepted for v1 (persistent wizard prompt line); auto-pause-on-focus in 04-08 is the safety net against stolen focus"
  - "Phase 4 is translation-only on z=0 (camera=0 model axes) by design; edge-on ring presentation is the recorded 03-08 decision deferred to Phase 5"

patterns-established:
  - "Per-step human-verify verdict table (Step/Expected/Actual/Verdict) with verbatim console evidence — the 03-08 checkpoint style applied to a single-task checkpoint plan"
  - "Cosmetic observations (wizard prompt in console + right-panel wizard buttons) recorded as standard wizard UI, not defects"

# Metrics
duration: ~5 min (finalization; the human checkpoint ran in real Windows PyMOL)
completed: 2026-09-13
---

# Phase 4 Plan 07: Early Keys Human-Verify Summary

**Keys checkpoint APPROVED in real Windows PyMOL 2.5.0: the KeySteerWizard do_special route is the shipping arrow-key input route (all four arrows dispatch live; teardown restores the prior wizard; focus UX accepted) — zero defects, zero code changes, no eventFilter fallback needed.**

## Performance

- **Duration:** ~5 min executor time (finalization only — the checkpoint itself was executed by the human in real Windows PyMOL)
- **Started:** 2026-09-13 (human checkpoint in real Windows PyMOL 2.5.0)
- **Completed:** 2026-09-13 (verdict APPROVED + SUMMARY)
- **Tasks:** 1 (checkpoint:human-verify)
- **Files modified:** 0 — the plan's `files_modified` artifacts (smoke/manual_wizard_keys_check.py, serpentrum/input.py) were built in plan 04-04; this checkpoint passed with ZERO defects, so nothing changed and the frontmatter artifacts list is empty by design

## Accomplishments

- **W7 core claim proven live:** all four arrow keys — up/down included — dispatched through the wizard route (C `PyMOL_Special` → `WizardDoSpecial` → `KeySteerWizard.do_special`) in real Windows PyMOL 2.5.0. This is the half of W7 headless tests can never reach; `set_key` could never do this (up/down never fire through it). The roadmap's "one open mechanism question" is RESOLVED.
- **W5 teardown contract proven live, including prior-wizard restoration:** `srp_keys_off` cleared the steering wizard (`wizard now: None`); with PyMOL's measurement wizard active beforehand, the harness saved it as prior and `srp_keys_off` restored it — the bioCHEMeleon save/restore pattern verified in the real GUI.
- **W4 + W8 confirmed:** left/right arrows steer only (no movie-frame stepping); up/down command-line history churn is cosmetic as designed.
- **Focus behavior mapped with an explicit UX verdict (Q3):** arrows do NOT steer while the plugin dialog or command line has focus (arrows navigate within the dialog itself); steering resumes on clicking the viewer. Verdict: ACCEPTED for v1 — the persistent wizard prompt line tells the player what to do, and plan 04-08's focus auto-pause is the safety net.
- **Route decision:** APPROVED — plan 04-08 wires `serpentrum/input.py` directly; the designed Qt app-level eventFilter fallback (04-RESEARCH-input.md Q4, serpentrum/gui_input.py) is NOT built.

## Task Commits

This plan held a single checkpoint task with no implementation work up front and no in-plan fixes (zero defects found — the 03-08 precedent for fixes-during-verification was not triggered). The only commit is the plan-finalization metadata commit:

**Plan metadata:** `docs(04-07): keys checkpoint approved — wizard route stands` (SUMMARY + STATE/ROADMAP updates)

## Human-Verify Verdicts (real Windows PyMOL 2.5.0)

| Step | Expected | Actual | Verdict |
|------|----------|--------|---------|
| 1 — Run harness from PyMOL command line | Box + benzene head materialize and frame; wizard prompt line appears; console prints HARNESS READY | `HARNESS scene: srp_box + srp_head materialized (medium box)`; `HARNESS prompt: serpentrum: click the 3D viewer, then steer with arrow keys`; `HARNESS prior wizard saved: None (restored by srp_keys_off)`; `HARNESS READY ...` | PASS |
| 2 — Click viewer, press all four arrows (W7 core claim) | Head nudges 0.3 Å per pressed direction; console prints `KEY <dir> -> request_direction=...` for every press; up/down reach do_special | Console shows `KEY up -> request_direction=True`, then `KEY up/right/down/left -> request_direction=False` for every press. ALL FOUR arrow keys reached do_special live (up/down included). The `False` flood after the first press is EXPECTED harness behavior: the harness has NO tick loop, so the engine's direction buffer (max 1) never drains — first turn accepted, subsequent presses refused as same-direction/buffer-full. The real game's 100 ms tick consumes the buffer (plan 04-05). | PASS |
| 3 — Watch console while pressing left/right (W4) | Steering only; NO movie-frame stepping | Confirmed working; no movie-frame stepping | PASS |
| 4 — Up/down + command-line history (W8) | Command line may scroll history (cosmetic); gameplay unaffected | History churn cosmetic; steering unaffected | PASS |
| 5 — Focus: arrows with dialog/command-line focus (Q3) | NO steering; UX judgment on click-viewer-to-steer | PASS — arrows in the plugin dialog navigate within the dialog itself, no steering. UX JUDGMENT: ACCEPTED (click-the-viewer-to-steer is fine for v1; auto-pause safety net lands in plan 04-08) | PASS |
| 6 — Click back to viewer, press arrows | Steering resumes immediately | Steering resumes after clicking back to the viewer | PASS |
| 7 — `srp_keys_off` teardown (W5) | `wizard now: None`; arrows no longer nudge; second call clean no-op | `srp_keys_off` → `keys OFF — wizard now: None`; steering gone | PASS |
| 8 — (Optional) prior-wizard preservation | Measurement wizard's panel reappears after `srp_keys_off` | With measurement wizard active, harness printed `HARNESS prior wizard saved: <pymol.wizard.measurement.Measurement object at 0x...>`; after `srp_keys_off`: `wizard now: <pymol.wizard.measurement.Measurement object at 0x...>` — prior wizard restored (the bioCHEMeleon save/restore pattern proven live) | PASS |

**Checkpoint resume-signal: APPROVED** (human verdict, real Windows PyMOL 2.5.0)

## Route Decision

**APPROVED — the wizard route stands.** `serpentrum/input.py` (KeySteerWizard, `cmd.set_wizard` + `do_special`, event mask 12) is the shipping input route; plan 04-08 wires it into play. The designed fallback (Qt application-level eventFilter, `serpentrum/gui_input.py` per 04-RESEARCH-input.md Q4) is **not needed and was not built**. The roadmap's failure-cheap strategy paid off exactly as designed: the spike resolved at the cheap checkpoint, before play wiring depended on it.

## Notes

### 1. The `request_direction=False` flood is correct engine authority, not a defect

The step-2 console shows the first press accepted (`True`) and subsequent presses refused (`False`). This is EXPECTED for this harness: it installs the steering wizard with a steer callback but runs NO game tick loop, so the engine's direction buffer (capacity 1) never drains — the first turn request is accepted and later presses are refused as same-direction/buffer-full. Engine authority working as specified; the real game's 100 ms tick (plan 04-05's GameTab timer) consumes the buffer every tick.

### 2. Cosmetic prompt-location observation (step 1)

The wizard prompt line appeared in the CONSOLE (the harness prints it) and the wizard PANEL (serpentrum title + 'Quit game' button) appeared in the right-hand OpenGL panel below the object list. This is PyMOL's standard wizard UI — recorded as an observation, not a defect.

### 3. Orientation clarification — user remark recorded (Phase-5 prerequisite reinforced)

The user observed during the checkpoint (verbatim):

> "from my test it looks like the ring laying on the board and move. assuming when it touches a new mol it touch via hydrogen not the ring center, just fyi"

Answer recorded: **Phase 4 is translation-only by design.** Movement is pure 2D translation on the z=0 plane (camera=0 model axes); molecule orientation never changes in Phase 4. The head currently displays the **as-stored PubChem SDF orientation** (ring flat on the xy board) — the bridge has no orientation code yet (grep-verified). The user correctly infers that a pickup in this orientation would contact via the **hydrogen edge, not the ring face/centroid** — which matches the recorded 03-08 human-confirmed decision (STATE.md decision line; 03-08-SUMMARY.md "Carried-forward Phase-5 task: orient head/pickup ring frames edge-on at materialization/placement (ring-frame normal in-plane)"). **The user's H-edge-contact inference is recorded as supporting evidence that edge-on orientation is a HARD Phase-5 prerequisite that must land BEFORE any stacking can be geometrically correct and camera-visible.**

## Decisions Made

- Keys checkpoint APPROVED — KeySteerWizard `do_special` route is the shipping input route; no `gui_input.py` eventFilter fallback built
- Click-viewer-to-steer UX accepted for v1 (persistent wizard prompt line); plan 04-08's auto-pause-on-focus is the safety net against stolen focus
- Harness False-flood explained (no-tick buffer-full refusals are correct engine authority, not a defect)
- Phase-4 translation-only design reaffirmed; the user's orientation remark logged against the 03-08 carried-forward Phase-5 edge-on task

## Deviations from Plan

None — the checkpoint passed with zero defects, so the plan's authorized in-plan fix path ("Fixes discovered DURING verification ... are made inside this plan and re-verified") was never triggered. No code files changed anywhere in the repo.

## Issues Encountered

None. All 8 steps passed on the first harness run.

## User Setup Required

None.

## Next Phase Readiness

- **The one open mechanism question (up/down arrow dispatch live) is RESOLVED** before plan 04-08 builds on it — the roadmap's "failure is cheap" checkpoint discharged.
- Teardown/no-leak contract confirmed live (arrows revert, prior wizard preserved) — the same save/restore discipline plan 04-08's single `_teardown_round` will rely on.
- Focus behavior mapped with an explicit UX verdict, so plan 04-08's auto-pause mitigation targets the real behavior (dialog/command-line focus steals keys).
- **What's next:** plan 04-08 (play wiring: camera lock + input install at GO!, single `_teardown_round`, pause input-gating, focus auto-pause), then plan 04-09 (full gate pass + final human-verify of the full playable loop).
- **Carried forward to Phase 5:** edge-on ring orientation at materialization/placement (03-08 decision, now reinforced by the user's 04-07 H-edge-contact inference) — must precede any stacking.

---
*Phase: 04-game-loop-input*
*Completed: 2026-09-13*
