---
phase: 07-spectra-ui
plan: 03
subsystem: ui
tags: [pymol, cgo, spectra, mode-vectors, xtbopt, bridge, smoke]

# Dependency graph
requires:
  - phase: 06-xtb-pipeline
    provides: "frozen g98/vibspectrum/xtbopt artifact contract; REQUIRED-smoke protocol (10 already in tuple)"
  - phase: 02-spectra-parsing
    provides: "spectra.parse_g98 (26 atoms / 72 modes fixture) + FROZEN cgo_build.mode_arrows builder"
  - phase: 03-viewer-bridge
    provides: "pymol_bridge BRIDGE class: load_molecule/load_box/delete_object/object_exists/cleanup_srp patterns"
provides:
  - "pymol_bridge.load_mode_arrows(cgo, name='srp_mode_vec', zoom=0) — CGO arrow load channel (SPECTRA-05)"
  - "pymol_bridge.load_xtbopt(path, srp_name='srp_xtbopt', zoom=0) — optimized-frame molecule as sticks"
  - "pymol_bridge.zoom_mode_frame() — one-shot guarded framing of the spectra overlay"
  - "smoke/13_mode_arrows_smoke.py (REQUIRED) — pins CGO load + g98≡xtbopt overlay identity (<1e-3 Å) on every gate run"
affects: [07-09 (row-click wiring consumes these seams), 07-10 (human-verify checkpoint of the overlay)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "BRIDGE seams for spectra overlay are srp_-prefixed by constant (MODE_VEC_NAME/XTBOPT_NAME) — cleanup_srp + .pse-reload INFRA-04 contract"
    - "overlay-identity regression smoke: parse fixture g98, load fixture xtbopt, assert per-atom agreement <1e-3 Å on every gate run"

key-files:
  created:
    - smoke/13_mode_arrows_smoke.py
  modified:
    - serpentrum/pymol_bridge.py
    - tests/run_gates.py

key-decisions:
  - "Sticks rep for srp_xtbopt: view parity with pickups/snake (head stays spheres; optimized snake reads as a molecule)"
  - "zoom=0 on both loads; the ONE-shot zoom is zoom_mode_frame's job (pitfall 14 — never per click)"
  - "Identity tolerance 1e-3 Å (probe measured 0.0000 Å on fixture; smoke measured 1e-6 Å) — drift headroom, kills real desync"

patterns-established:
  - "Spectra overlay objects land ONLY under srp_mode_vec/srp_xtbopt; replace semantics = guarded delete + load (caller-owned)"

# Metrics
duration: 5min
completed: 2026-09-26
---

# Phase 7 Plan 03: Bridge mode-vector seams + overlay-identity smoke Summary

**SPECTRA-05 viewer half: three thin BRIDGE cmd seams (srp_mode_vec CGO arrows, srp_xtbopt sticks, one-shot guarded zoom) plus REQUIRED smoke 13 re-asserting the g98≡xtbopt overlay identity (<1e-3 Å, measured 1e-6 Å) on every gate run.**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-09-26T17:43:18Z
- **Completed:** 2026-09-26T17:48:39Z
- **Tasks:** 2
- **Files modified:** 3 (1 created, 2 modified)

## Accomplishments
- All viewer access for the spectra overlay flows through the BRIDGE with srp_-prefixed names (`MODE_VEC_NAME='srp_mode_vec'`, `XTBOPT_NAME='srp_xtbopt'` module constants) — GUI modules never need pymol.cmd; cleanup_srp / Setup-Apply / .pse-reload contracts (INFRA-04) hold.
- `zoom_mode_frame()` is one-shot and guarded: `cmd.zoom('srp_xtbopt or srp_mode_vec')` + refresh only when at least one overlay object exists; returns False (never a Selector error) otherwise.
- REQUIRED smoke 13 pins the mode-arrow CGO path and the OPTIMIZED-frame overlay assumption on every gate run — an xtb-version drift fails loudly, never a silent vectors-vs-molecule misalignment.
- cgo_build.mode_arrows byte-untouched (frozen Phase-2 contract confirmed by `git diff 33fe3ec..HEAD` — no changes).

## Task Commits

Each task was committed atomically:

1. **Task 1: bridge seams — load_mode_arrows, load_xtbopt, zoom_mode_frame** - `b368e6b` (feat)
2. **Task 2: REQUIRED smoke 13 — mode arrows + overlay assertion + tuple edit** - `c39afd6` (test)

## Files Created/Modified
- `serpentrum/pymol_bridge.py` — Phase-7 section: MODE_VEC_NAME/XTBOPT_NAME constants + load_mode_arrows (mirrors load_box, zoom=0), load_xtbopt (load + sticks, mirrors materialize_pickup minus transform), zoom_mode_frame (guarded one-shot)
- `smoke/13_mode_arrows_smoke.py` — headless REQUIRED smoke: STAGE1 parse fixture g98 (26 atoms/72 modes) → STAGE2 CGO arrows loaded as srp_mode_vec with finite non-degenerate extent → STAGE3 srp_xtbopt 26 atoms + per-atom |Δ| vs g98 atom block <1e-3 Å (measured 0.000001 Å) → STAGE4 zoom_mode_frame returns True → SMOKE-OK MODE-ARROWS
- `tests/run_gates.py` — REQUIRED_SMOKES += 'smoke/13_mode_arrows_smoke.py' with plan-07-03 comment

## Decisions Made
- PyMOL 2.5 chempy Atom exposes `.coord` ([x,y,z]), not `.x/.y/.z` — smoke stage 3 reads `atom.coord` (see Deviations).
- Kept REQUIRED_SMOKES edit minimal (append 13 only); smokes 09/11 remain informational on this base (see Issues).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Smoke read `atom.x/.y/.z`; PyMOL 2.5 Atom exposes `.coord`**
- **Found during:** Task 2 (first direct smoke run — stage3 AttributeError)
- **Issue:** Plan text says "compare cmd.get_model(...).atom[i].x/y/z"; PyMOL 2.5's chempy Atom has no per-axis attributes — coordinates live in `atom.coord`.
- **Fix:** Read `cx, cy, cz = atom.coord` in the per-atom comparison (comment notes the 2.5 API).
- **Files modified:** smoke/13_mode_arrows_smoke.py
- **Verification:** Re-ran direct smoke — STAGE3 XTBOPT-IDENTITY max_delta=0.000001 A, SMOKE-OK MODE-ARROWS; full --smoke leg green.
- **Committed in:** `c39afd6` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Plan-text API guess corrected against the live viewer; assertion semantics (per-atom <1e-3 Å) unchanged. No scope creep.

## Issues Encountered
- **Plan/orchestrator-stated gate state vs base 33fe3ec:** the prompt said REQUIRED_SMOKES "already lists 09/10/11"; on the base the tuple lists only 10 (09_qprocess and 11_xtb_runner exist on disk and run as informational smokes — both PASS). No action taken: the plan's own instruction was to append 13 only, which I did. The orchestrator may wish to promote 09/11 to REQUIRED in a later merge/plan if intended.
- Informational smoke 02_dialog_smoke FAILs (non-blocking) — pre-existing on this base, unrelated to this plan.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- 07-09 (or whichever plan wires the table row-click) can consume pb.load_mode_arrows / pb.load_xtbopt / pb.zoom_mode_frame with delete-then-load replace semantics; the smoke already exercises the exact call sequence.
- The overlay identity is now an always-on regression: any xtb fixture/binary drift trips gate 4 loudly.
- Merge note: this branch touches serpentrum/pymol_bridge.py, tests/run_gates.py (REQUIRED_SMOKES tuple) and smoke/13_mode_arrows_smoke.py — potential tuple conflicts with 07-05 (plot smoke takes number 12) are textual and adjacent; resolve by keeping both entries.

---
*Phase: 07-spectra-ui*
*Completed: 2026-09-26*
