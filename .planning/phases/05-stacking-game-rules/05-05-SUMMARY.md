---
phase: 05-stacking-game-rules
plan: 05
subsystem: pure-core
tags: [stacking, pi-stack, placement, clash-gate, skip-policy, pure-module, tdd]

# Dependency graph
requires:
  - phase: 02-pure-core
    provides: stacking.ring_frame/place_pickup/check_clash, molecule_data loaders + approval gate
  - phase: 03-molecules-setup
    provides: setloader records, __upload__ skip keying, demo Set A SDFs
provides:
  - serpentrum/placement.py resolve() — the pure controller the GUI 'stacked' branch calls
  - Pinned skip taxonomy (NO_ENTRY/NOT_APPROVED/MODE/NO_RING/NONPLANAR, ordered)
  - Pinned tail/growth policy (head + -heading first capture; newest-segment staircase)
  - Pinned 3D clash-gate assembly (head + segments + other live pickups, z = ±display_z)
  - Outcome-code constants consumed by hud_logic (plan 05-09)
affects: [05-08 setloader stack_ring carry, 05-09 hud_logic STACK-04 text, 05-10 materialization, 05-12 integration chain, 05-13 GameTab stacked seam]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Pure controller-seam module: GUI's entire 'stacked' logic = one resolve() call + engine attach/reject"
    - "Approval-gated dataset lookup: interaction_for + shipped_interactions id-set membership, never interaction_for alone"

key-files:
  created:
    - serpentrum/placement.py
    - tests/test_placement.py
  modified: []

key-decisions:
  - "Skip taxonomy ordered first-match-wins: NO_ENTRY -> NOT_APPROVED -> MODE -> NO_RING -> NONPLANAR (pinned)"
  - "Growth normal: exactly -(heading) for the first capture; the newest segment's recomputed own normal thereafter (linear staircase)"
  - "Clash-gate existing set INCLUDES other live pickups' atoms (research open Q7 — decided yes)"
  - "Gate box is 3D: xy from preset, z = ±display_z passed as a parameter (bridge owns BOX_DISPLAY_Z)"
  - "resolve() is PURE and never touches engine state — GUI always calls engine.reject_pickup on skip/refuse"

patterns-established:
  - "Outcome contract: {'status': 'placed'|'skipped'|'refused', ...} with code constants imported by hud_logic"

# Metrics
duration: 45min
completed: 2026-09-15
---

# Phase 5 Plan 05: Placement Seam Summary

**Pure placement controller seam: ordered skip taxonomy + snake-canonical growth policy + dataset-exact placement (sqrt(3.383²+1.231²) to 1e-9) + 3D clash gate over head/chain/live pickups — 26 pinned tests, gates 477 green.**

## Performance

- **Duration:** ~45 min
- **Started:** 2026-09-15T19:20Z (approx)
- **Completed:** 2026-09-15T20:09Z
- **Tasks:** 3 (TDD: RED ×2, GREEN ×1)
- **Files modified:** 2 created (serpentrum/placement.py, tests/test_placement.py)

## Accomplishments

- `placement.resolve()` — the single pure function the GUI's 'stacked' branch will call: skip taxonomy → tail frame → `stacking.place_pickup` at dataset geometry → `stacking.check_clash` 3D gate → outcome dict (`placed`/`skipped`/`refused` + codes + '%.2f A' clash detail).
- Skip taxonomy pinned with ordering (upload hits SKIP_NO_ENTRY before SKIP_NO_RING; DRAFT dataset hits SKIP_NOT_APPROVED via `shipped_interactions`, never `interaction_for` alone).
- Tail/growth policy pinned: first capture grows exactly along −heading from the head's ring frame; subsequent captures recompute the newest segment's frame (recomputed normal = the growth normal used at placement, dot pinned > 0.99 → linear staircase, second-step clash-free).
- Exactness pinned against the APPROVED dataset formula: composed centroid step == sqrt(3.383²+1.231²) to 1e-9, components 3.383/1.231 to 1e-9, headline 3.6000 Å @ 20.0° via its rounding (tolerance inherited from test_stacking_dataset).
- Biphenyl refuse-path demonstrator pinned: `('refused', REFUSE_ATOM, '%.2f A')` with measured distance < 2.5 Å (90°-twist conformer; data observation, not fixed).

## Task Commits

Each task was committed atomically (TDD):

1. **Task 1 RED: skip-taxonomy tests** — `07c6a79` (test)
2. **Task 2 RED: tail-frame + exactness + clash + orchestrator tests** — `8d5bc2a` (test)
3. **Task 3 GREEN: serpentrum/placement.py implementation** — `009b9fa` (feat)

**Plan metadata:** (this summary's docs commit follows)

## Files Created/Modified

- `serpentrum/placement.py` — PURE controller seam: SKIP_*/REFUSE_* code constants, `resolve_skip`, `tail_frame`, `attempt_place`, `gate`, `resolve`; module docstring records the four pinned policies.
- `tests/test_placement.py` — 26 unittest pins over the shipped dataset + real setloader records (stack_ring patched in locally per wave-1 isolation), raw-SDF atoms, local rot-90°-about-y edge-on head fixture mirroring the 05-02/05-10 presentation contract.

## Decisions Made

- **Skip taxonomy order (pinned):** NO_ENTRY → NOT_APPROVED → MODE → NO_RING → NONPLANAR (last detected at placement time via ring_frame ValueError).
- **Clash-gate existing set (research open Q7 — decided):** head atoms + ALL segment atoms + other live pickups' atoms; blocks stacks that would land onto an unpicked pickup (consistent mid-chain behavior).
- **Gate box:** 3D, z = ±display_z passed as a parameter — placement.py stays PURE, the bridge owns BOX_DISPLAY_Z.
- **resolve() purity:** never mutates the engine; the GUI always calls `engine.reject_pickup` on skip/refuse (capture/rollback symmetry stays engine-owned; the win-desync fix is plan 05-04's).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Test calibration] "dot(normal, segment_centroid − head_centroid) > 0.99" is arithmetically impossible**
- **Found during:** Task 2 (tail-frame/clash tests)
- **Issue:** the dataset's pinned lateral offset makes the centroid step sit exactly cos(20°) = 3.383/3.6000069 = 0.9397 from the growth normal; a > 0.99 centroid dot can never hold (geometry probe-confirmed).
- **Fix:** pinned staircase continuity as (a) dot(recomputed tail normal, growth normal used at placement) > 0.99 — the meaningful continuity guarantee, and (b) a companion centroid-step cosine asserted against its exact geometric value (3.383/√(3.383²+1.231²)) to 1e-9.
- **Files modified:** tests/test_placement.py
- **Verification:** both assertions green; exact cos value documented in the test.
- **Committed in:** `8d5bc2a`

**2. [Rule 1 - Test calibration] "== 3.6000 within 1e-9" / "== 20.0 deg within 1e-6" exceed the dataset encoding's own precision**
- **Found during:** Task 2 (exactness tests)
- **Issue:** the APPROVED file stores 3.383/1.231, whose exact composition is 3.6000069 Å and 19.9953° (probe-confirmed; test_stacking_dataset pins 3.60 via round-to-headline and ±0.5° tolerance).
- **Fix:** exactness pinned at 1e-9 against the FORMULA (composed distance, per-component decomposition, atan2 angle reproduction), plus headline assertions at the encoding's own rounding (|dist−3.6| < 5e-4, angle within 0.5° of 20.0 — same tolerance as test_stacking_dataset, "reuse" per the plan).
- **Files modified:** tests/test_placement.py
- **Verification:** all exactness pins green; encoding tolerance documented in the test-class docstring.
- **Committed in:** `8d5bc2a`

**3. [Rule 3 - Blocking] Biphenyl REFUSE_ATOM pin needs display_z = 7.0 (at 5.0 the wall check fires first)**
- **Found during:** Task 2 (biphenyl refusal test)
- **Issue:** placed biphenyl extends to |z| = 6.914 Å (probe), so with the shipped BOX_DISPLAY_Z = 5.0 the wall leg of check_clash (which runs first) refuses it as REFUSE_WALL — a correct refusal, but not the plan-pinned REFUSE_ATOM.
- **Fix:** the biphenyl test passes display_z = 7.0 (gate parameter by design) so the ATOM check refuses; the refusal codes' wall routing stays separately pinned (wall-poke tests + REFUSE_WALL resolve test at display_z 5.0).
- **Files modified:** tests/test_placement.py
- **Verification:** refused outcome = REFUSE_ATOM with measured detail '2.14 A' < 2.5 Å; note for 05-16/05-10: in the real game (display_z 5.0) biphenyl may refuse as wall — still the designed refuse-path demonstrator, code may differ by geometry.
- **Committed in:** `8d5bc2a`

---

**Total deviations:** 3 auto-fixed (2 test-calibration corrections of plan pins that exceeded geometric/data precision, 1 gate-parameter selection)
**Impact on plan:** All pins hold at their achievable precision; no scope creep; implementation signature unchanged. The local rot-90°-about-y edge-on test fixture (reproducing the 03-08 presentation decision without sibling plan 05-02) is an implementation detail, documented in the test docstring — production edge-on rotation remains 05-02/05-10's job.

## Issues Encountered

- Raw shipped SDFs lie flat in xy while the growth normal = −heading is always in-plane; a raw (unrotated) head makes the first-capture placement clash with the head itself (1.86 Å). Resolved by rotating the head fixture 90° about y inside the test (proper rigid rotation — exactness unaffected), mirroring the edge-on materialization contract that production will apply. Wave-1 isolation confirmed: no sibling artifacts (molfile.ring_cycle, orientation.edge_on) imported anywhere.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- 05-08 can carry `stack_ring` onto setloader records; placement.py consumes exactly that key (fixture shape in test_placement.py is the contract).
- 05-09 (hud_logic) imports the SKIP_*/REFUSE_* constants and maps codes → info-box text.
- 05-13 (GameTab 'stacked' seam): gui reduces to `outcome = placement.resolve(...)`; on 'placed' → `engine.attach_segment` + bridge transform; else → `engine.reject_pickup`.
- Watch: biphenyl at the shipped display_z 5.0 refuses via REFUSE_WALL (wall leg first); REFUSE_ATOM shows once BOX_DISPLAY_Z Option B (6.0) lands or molecule geometry differs — both are the designed refuse path.

---
*Phase: 05-stacking-game-rules*
*Completed: 2026-09-15*
