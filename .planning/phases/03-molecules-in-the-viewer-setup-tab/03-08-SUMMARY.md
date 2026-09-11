---
phase: 03-molecules-in-the-viewer-setup-tab
plan: 08
subsystem: testing
tags: [pymol, gates, human-verify, smoke, xtb, setup-tab, viewer-bridge, infra-04, session-survival]

# Dependency graph
requires:
  - phase: 03-03
    provides: "xtbenv.validate_binary_path — unified xtb path validation (auto + manual)"
  - phase: 03-05
    provides: "Demo Set A shipped PubChem SDFs + manifest.json (SC1 demo-leg enabler, human-gated)"
  - phase: 03-06
    provides: "pymol_bridge materialize/cleanup_srp cmd-seam + headless viewer smoke (.pse survival, wildcard cleanup)"
  - phase: 03-07
    provides: "SetupTab form (5 grouped sections) + gui.py page-0 registration + anchored setup dict"
provides:
  - "Phase 3 closed: all automated gates green + human-verify APPROVED in real Windows PyMOL 2.5.0"
  - "smoke/04_demo_e2e_smoke.py — real-demo-data end-to-end smoke (SMOKE-OK VIEWER-DEMO sentinel)"
  - "xtb detect-on-toggle fix (auto-detect surfaces resolved path immediately, not only post-Apply)"
  - "Boundary box linewidth default 2.0 -> 3.0 (clearly visible on dark background)"
  - "Deferred Phase-5 design decision recorded: edge-on ring orientation (stacks along x/y, BOX_DISPLAY_Z=5.0 confirmed correct)"
affects: [Phase 4, Phase 5, Phase 8]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Real-data e2e smoke: manifest -> setloader.load_demo_set -> pymol_bridge.materialize -> head-switch -> cleanup on REAL shipped PubChem bytes (not fixtures)"
    - "Detect-on-toggle: xtb auto-detect checkbox surfaces _refresh_status_with_xtb() immediately on state change, not deferred to Apply"
    - "_loading guard as defense-in-depth around _populate_head_combo (alongside blockSignals) to prevent Apply-time signal storms"

key-files:
  created:
    - smoke/04_demo_e2e_smoke.py
  modified:
    - tests/run_gates.py
    - serpentrum/gui_setup.py
    - serpentrum/pymol_bridge.py

key-decisions:
  - "materialize's documented cleanup-first contract verified: an unknown head id leaves srp_head correctly ABSENT (box-only scene), not the previous molecule — smoke asserts this contract, not a 'head still present' assumption"
  - "xtb detect result is advisory in Phase 3 (status label); the toggle must surface it immediately so the user sees auto-detect worked without pressing Apply"
  - "Boundary box default linewidth 3.0 (was 2.0) — human-verified clearly visible; cgo_build's 2.0 default is a separate concern not touched here"
  - "Dialog head-dropdown keeps listing loaded records after Cleanup — by design (records persist for re-Apply); documented to the user, not a defect"
  - "DEFERRED TO PHASE 5 (user-confirmed): molecule ring planes must be PERPENDICULAR to the screen (edge-on, coin-on-edge) at placement; pi-stack normal lies IN the xy-plane and stacks grow along x/y — every layer visible to the locked 2D camera. Rejected alternative: rings parallel to screen / stacks along z (viewer sees only the top molecule)"

patterns-established:
  - "Real-shipped-data e2e smoke: prove the full manifest->materialize->cleanup chain on REAL data bytes, not synthetic fixtures, as a REQUIRED smoke before phase close"
  - "Detect-on-toggle UX: auto-detect checkboxes must surface their probe result on toggle, not defer to the next Apply"

# Metrics
duration: 35min
completed: 2026-09-12
---

# Phase 3 Plan 08: Phase-Closing Gate Pass + Human-Verify Summary

**All automated gates green (433 tests, 3 smokes, xtb probe) + 10/10 human-verify steps APPROVED in real Windows PyMOL 2.5.0, with three verification-strengthening/UX fixes made en route and a Phase-5 edge-on-ring design decision recorded**

## Performance

- **Duration:** ~35 min executor time (plus human-verify checkpoint pause)
- **Started:** 2026-09-12 (Task 1 gate pass)
- **Completed:** 2026-09-12 (checkpoint APPROVED + SUMMARY)
- **Tasks:** 2 (1 auto gate pass + 1 checkpoint:human-verify)
- **Files modified:** 4 (1 created, 3 modified)

## Accomplishments
- Every automated gate green before the human touched anything: default gates (syntax + plugin-path safety + purity AST + 433 unittest tests), all REQUIRED smokes (SMOKE-OK SKELETON + SMOKE-OK VIEWER-BRIDGE + SMOKE-OK VIEWER-DEMO), and the xtb probe (version + normal termination)
- Human-verify checkpoint APPROVED in real Windows PyMOL 2.5.0: all 10 verify steps PASS, covering SC1-SC5 end-to-end (form renders, demo leg, head pick, upload reject+accept, cleanup-with-own-object, .pse fresh-process session survival, xtb auto+manual, win-cap hessian warning, modeless sanity)
- INFRA-04 fresh-process contract PROVEN: .pse save -> full PyMOL restart -> session reload (srp objects reappear, no plugin state) -> Cleanup removes exactly srp_* again, user object survives
- Three fixes made under this plan (all re-verified green): real-demo-data e2e smoke added; xtb detect-on-toggle bug fixed; boundary box linewidth thickened
- Phase-5 design decision captured: edge-on ring orientation (stacks along x/y) — BOX_DISPLAY_Z=5.0 confirmed correct as-is

## Task Commits

Each task/fix was committed atomically:

1. **Task 1: full automated gate pass (fix anything red)** — gates green, no fixes needed at gate time; the e2e smoke below was added as verification strengthening
2. **Real-demo-data e2e smoke** — `943aec7` (test)
3. **xtb detect-on-toggle + Apply-time signal storm guard** — `ae27ffe` (fix)
4. **Boundary box linewidth 2.0 -> 3.0** — `e8b3a9d` (fix)

**Plan metadata:** `docs(03-08): complete phase-closing gate + human-verify plan` (this commit)

## Automated Gate Output (Task 1)

All three gate runs from the repo root (WSL), exit 0:

| Gate | Command | Verdict |
|------|---------|---------|
| 1 — syntax + plugin-path safety | `python3.6 tests/run_gates.py` | exit 0 — no top-level `*.py`, no `__init__.py` in tests/smoke/tools |
| 2 — purity AST | `python3.6 tests/run_gates.py` | exit 0 — entry lazy, GUI allowlist (pymol.Qt only), all else pure |
| 3 — unittest suite | `python3.6 tests/run_gates.py` | exit 0 — **433 tests OK** |
| 4 — headless smokes | `python3.6 tests/run_gates.py --smoke` | SMOKE-OK SKELETON + SMOKE-OK VIEWER-BRIDGE + SMOKE-OK VIEWER-DEMO (sentinels; never exit codes through the .bat) |
| 5 — xtb probe | `python3.6 tests/run_gates.py --xtb` | `xtb version 6.7.1pre` + `normal termination` (Windows xtb invoked from WSL, direct exe exec, /mnt/c cwd) |

> Note: at Task 1 gate time all gates were green with no fixes. Commit `943aec7` subsequently added the SMOKE-OK VIEWER-DEMO sentinel (a new REQUIRED smoke); the --smoke gate was re-verified green with the third sentinel present. Fixes `ae27ffe` and `e8b3a9d` were made during/after the human-verify checkpoint and re-verified green across all three gate runs.

## Human-Verify Verdicts (Task 2 — real Windows PyMOL 2.5.0)

| # | Verify step | Verdict | Notes |
|---|-------------|---------|-------|
| 1 | Form renders (real form, not placeholder) | PASS | SETUP-02..06 present |
| 2 | Demo leg: box + head materialize, framed | PASS | Box z-depth presentation deferred to Phase 5 (design note, not a defect) |
| 3 | Head pick: Naphthalene replaces srp_head | PASS | SETUP-04 |
| 4 | Upload rejection: 4-ring + no-H files -> modal with reason; nothing loads | PASS | tetracene "has 4 rings (limit is 3)"; reject_no_h.sdf hydrogen reason |
| 5 | Upload acceptance: valid SDF+mol2 -> materialize + head dropdown repopulates | PASS | accept_naphthalene.sdf + accept_benzene.mol2 |
| 6 | Cleanup with own object: 'ATP' loaded via File->Open; srp_* removed, ATP survives | PASS | `cmd.get_names('public_objects')` -> ['ATP'], zero srp_* |
| 7 | Session survival: .pse save -> restart -> reload -> Cleanup works again | PASS | INFRA-04 fresh-process contract proven |
| 8 | xtb: auto-detect surfaces resolved path immediately; manual path accepted | PASS | Fixed in ae27ffe (was post-Apply only) |
| 9 | Win cap 15 -> inline hessian warning; 10 -> hides | PASS | SC4 |
| 10 | Modeless sanity: viewer + command line responsive with dialog open | PASS | INFRA-05 held |

**Checkpoint resume-signal: APPROVED** (human verdicts on real Windows PyMOL 2.5.0)

> Design note (NOT a defect): the dialog head-dropdown keeps listing loaded records after Cleanup — by design, records persist for re-Apply. Documented to the user.

## Fixes Made Under This Plan

### 1. Real-demo-data end-to-end smoke — `943aec7` (test)

- **Found during:** Task 1 (verification strengthening)
- **Issue:** No smoke proved the REAL shipped Demo Set A data (PubChem SDFs + manifest) flows end-to-end through the loader/bridge; only fixture-based smokes existed
- **Fix:** `smoke/04_demo_e2e_smoke.py` — manifest -> `setloader.load_demo_set` -> `pymol_bridge.materialize` -> head-switch -> unknown-id fallback -> cleanup, on REAL shipped bytes; asserts `count_atoms` 12/18; registered in `tests/run_gates.py` REQUIRED_SMOKES (gate 4); sentinel SMOKE-OK VIEWER-DEMO
- **Finding:** materialize's documented cleanup-first contract means an unknown head id leaves `srp_head` correctly ABSENT (box-only scene), not "still the previous molecule" — the smoke asserts the verified contract
- **Files modified:** smoke/04_demo_e2e_smoke.py (created), tests/run_gates.py
- **Verification:** --smoke gate green with third sentinel

### 2. xtb detect-on-toggle + Apply-time signal storm guard — `ae27ffe` (fix)

- **Found during:** Task 2 human-verify (step 8)
- **Issue:** xtb detect result only surfaced post-Apply, never on toggle — the auto-detect checkbox gave no immediate feedback; also, `_populate_head_combo` could leak a signal storm during Apply
- **Fix:** `_on_xtb_auto_changed` now calls `_refresh_status_with_xtb()` so the resolved xtb path (or not-found advisory) appears immediately on toggle; `_populate_head_combo` wrapped in `_loading` guard (defense-in-depth alongside blockSignals); validate() messages untouched
- **Files modified:** serpentrum/gui_setup.py
- **Verification:** step 8 PASS — toggle immediately surfaces "xtb: <resolved path>" or the not-found advisory; manual path accepted

### 3. Boundary box default linewidth 2.0 -> 3.0 — `e8b3a9d` (fix)

- **Found during:** Task 2 human-verify (step 2, human feedback "box too thin")
- **Issue:** DEFAULT_BOX_LINEWIDTH 2.0 was too thin to read clearly on a dark background; first reading was linewidth, not a structural issue
- **Fix:** DEFAULT_BOX_LINEWIDTH 2.0 -> 3.0 in `pymol_bridge.load_box`; updated comment (no longer claims to match cgo_build's 2.0 default)
- **Files modified:** serpentrum/pymol_bridge.py
- **Verification:** no smoke/test asserts linewidth style (verified by grep); step 2 PASS — box clearly visible

## Deferred Design Decision (recorded for Phase 5 planning — user-confirmed)

**Stack presentation: edge-on ring orientation.** Molecule ring planes must be PERPENDICULAR to the screen/xy-plane (edge-on, coin-on-edge) at placement, so the pi-stack normal lies IN the xy-plane and stacks grow along x/y — every stack layer visible to the locked 2D camera.

Consequences:
- (a) Box z-extent only ever holds ONE molecule's edge-on width (~5 A) -> `BOX_DISPLAY_Z = 5.0` is correct as-is, no depth change
- (b) The 2D gameplay boundary/body rules naturally bound the visible stack
- (c) Phase 5 must orient head/pickup ring frames edge-on at materialization/placement (ring frame normal in-plane)
- (d) Verify per-molecule edge-on z-width fits 10 A at <=3-ring scope (anthracene/phenanthrene orientation detail)

**Rejected alternative** (by the user): rings parallel to screen, stacks along z — the viewer would see only the top molecule.

## Success Criteria Mapping (SC1-SC5)

| SC | Roadmap text | Verify steps | Verdict |
|----|--------------|--------------|---------|
| SC1 | Demo Set A loads / uploads <=3 rings rejected with clear reason | 2, 4, 5 | PASS |
| SC2 | Preset box visible + head molecule (default Random) appears | 2 | PASS |
| SC3 | xtb auto-detect (xtb + xtb.exe) or manual override | 8 | PASS |
| SC4 | Win cap defaults to safe budget + hessian (~N^3) warning when raised | 9 | PASS |
| SC5 | Cleanup removes only srp_* (user untouched) + fresh-process after .pse reload | 6, 7 | PASS |

## Requirements Delivered

| Requirement | Phase | Status after 03-08 |
|-------------|-------|--------------------|
| SETUP-02 | 3 | Complete (demo dropdown + upload) |
| SETUP-03 | 3 | Complete (box preset dropdown) |
| SETUP-04 | 3 | Complete (head dropdown, Random default) |
| SETUP-05 | 3 | Complete (xtb auto-detect + manual path) |
| SETUP-06 | 3 | Complete (win cap + hessian warning) |
| DATA-03 | 3 | Complete (<=3-ring upload gate, clear reasons) |
| INFRA-04 | 3 | Complete (srp_*-only cleanup, fresh-process proven) |

## Decisions Made
- materialize cleanup-first contract is the verified truth: unknown head id -> srp_head ABSENT (box-only), not "previous molecule"; smoke asserts it
- xtb detect result surfaces on toggle (not only Apply) — UX requirement for auto-detect feedback
- Box linewidth 3.0 default (human-verified visible); cgo_build's 2.0 default is a separate, untouched concern
- Head-dropdown persists records after Cleanup by design (re-Apply support)
- Edge-on ring orientation locked for Phase 5 (stacks along x/y, BOX_DISPLAY_Z=5.0 correct as-is); parallel-to-screen rejected

## Deviations from Plan

None — plan executed exactly as written. The plan explicitly anticipated gate fixes ("If ANY gate fails: diagnose, fix...") and human-reported fixes ("Anything the human reports broken comes back as concrete fix work INSIDE this plan"). The three commits are that authorized fix work, all re-verified green. No gate was weakened, no contract violated (purity classes, no `.exec_()`, srp_* naming, no user-molecule mutation all held).

## Issues Encountered
- xtb detect-on-toggle: auto-detect gave no immediate feedback (result only post-Apply) — fixed in `ae27ffe` by calling `_refresh_status_with_xtb()` on toggle
- Apply-time signal storm risk in `_populate_head_combo` — guarded with `_loading` flag in `ae27ffe` (defense-in-depth)
- Box too thin on dark background (human feedback) — `e8b3a9d` raised default linewidth to 3.0
- No real-data e2e smoke existed — `943aec7` added smoke/04 proving the full chain on REAL shipped PubChem bytes

## User Setup Required

None — no external service configuration required. Demo Set A SDFs already shipped via 03-05's human gate; xtb auto-detect handles path resolution (manual override available).

## Next Phase Readiness
- Phase 3 CLOSED: SC1-SC5 each human-confirmed, SETUP-02..06 + DATA-03 + INFRA-04 delivered
- The roadmap's human-verify note discharged: uploaded set loads; box renders; cleanup-after-.pse-reload proven in a fresh process
- Phase 4 (Game Loop & Input) can proceed: Setup tab form, viewer bridge, anchored setup state, srp_* cleanup all verified live
- Phase 5 must implement edge-on ring orientation at placement (recorded decision above); BOX_DISPLAY_Z=5.0 confirmed correct — no depth change needed
- Phase 8 will replace the temporary Apply/Cleanup buttons with the canonical 6-button row (SETUP-07/08)

---
*Phase: 03-molecules-in-the-viewer-setup-tab*
*Completed: 2026-09-12*
