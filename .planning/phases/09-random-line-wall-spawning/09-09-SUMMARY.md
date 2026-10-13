---
phase: 09-random-line-wall-spawning
plan: 09
subsystem: testing
tags: [gates, smoke, xtb, audit, wall, phase-close, feel-check, phase-9, complete]

# Dependency graph
requires:
  - phase: 09-random-line-wall-spawning
    provides: "the fully merged wall feature: wall.WallSpawner (09-01); game_engine set_wall/clear_wall + ('crashed','wall') leg (09-02); pymol_bridge load_line_wall/delete_walls + red linewidth-3.0 look (09-05); REQUIRED smoke/15 LINE-WALL (09-08); gui_game respawn/session/teardown wiring (09-07)"
provides:
  - "phase-close battery record: default-gate unittest count, the 12/12 required-smoke sentinel list, the xtb normal-termination line, the audit 46/46 result"
  - "the owner feel-check verdict record (two live games): steps 1-6b PASS, the single feel retune (head launch clearance 12 -> 8 A), all remaining feel rows + decision rows confirmed as shipped"
  - "the retune record (commit 7042602: WALL_HEAD_CLEARANCE_A 8.0 + scoped-suite + gates green with zero test edits)"
  - "the REQUIREMENTS route-(b) amendment record (GAME-05 dated clause + footer; commit 4c4e538; audit tool + test byte-untouched, 46/46)"
  - "the phase-wrap one-liner for STATE/ROADMAP consumption"
affects: [phase-9 wrap into STATE/ROADMAP by the orchestrator; v1 milestone audit/archive (deferred until then)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Battery-before-checkpoint (the 5.3-05 pattern): all four record types run and recorded on the merged tree BEFORE the blocking human feel-check; retunes afterwards are single-data-line edits + green re-gates"
    - "Single-tunable-table retune (the 5.1 SPEED_TIERS / 5.3 MIN_HEAD_DIST_FACTOR procedure): owner says the word -> one data-line edit -> scoped suite + gates (derivation-mandated tests need zero edits)"
    - "Route-(b) dated REQUIREMENTS amendment (5.3 / quick-003 precedent): a post-release feature extends an existing requirement's text instead of minting an ID; the closed GATE V 46/46 ledger keeps its meaning; audit tool + test untouched"
    - "Sentinel-only smoke verdicts (AGENTS.md): SMOKE-OK flushed lines are the verdict, never PyMOL exit codes"

key-files:
  created:
    - .planning/phases/09-random-line-wall-spawning/09-09-SUMMARY.md
  modified:
    - serpentrum/wall.py           # WALL_HEAD_CLEARANCE_A 12.0 -> 8.0 (owner retune)
    - .planning/REQUIREMENTS.md    # GAME-05 dated route-(b) amendment + footer

key-decisions:
  - "Battery green on the first run of every leg; zero fix commits needed"
  - "Owner feel-check APPROVED on two live games (medium/normal + small/expert); exactly ONE feel retune requested: head launch clearance 12.0 -> 8.0 A"
  - "D-MAP route (b) CONFIRMED by the owner: dated GAME-05 amendment, coverage stays 46/46, audit tool + test byte-untouched"
  - "Owner's accumulate-walls idea DEFERRED as a new-plan candidate (design-contract change) — recorded, not applied (5.3 edge-bias precedent)"

# Metrics
duration: ~25min (Tasks 1-3)
completed: 2026-10-13
---

# Phase 9 Plan 09: phase-close battery + owner feel-check Summary

**Phase 9 wall feature shipped and owner-APPROVED: the random line-wall spawns with the next mol (no-overlap, avoidable, replaced per spawn), head contact ends the run through the normal completion path (snake still completes -> spectra), teardown/restart clean; the full battery ran green on the merged tree (default gates 1050 tests, 12/12 required smokes incl. `SMOKE-OK LINE-WALL`, Windows xtb `normal termination`, requirements audit 46/46); the owner feel-check requested exactly ONE retune (head launch clearance 12.0 -> 8.0 A), and the route-(b) dated GAME-05 amendment landed with the audit tool + test byte-untouched at 46/46.**

> **STATUS: COMPLETE.** Tasks 1-3 executed. The battery (Task 1) was recorded before the blocking feel-check; Task 2 (the owner live feel-check) is RESOLVED; Task 3 applied the single retune + the route-(b) REQUIREMENTS amendment + finalized this record.

## Performance

- **Duration:** ~25 min (Tasks 1-3)
- **Started:** 2026-10-13T18:47:40Z
- **Completed:** 2026-10-13
- **Tasks:** 3 of 3 executed
- **Files modified:** 3 (this SUMMARY; `serpentrum/wall.py` one data line; `.planning/REQUIREMENTS.md` two clauses)

## Task 1 — Battery verdict tables (recorded on the fully merged phase state)

All four legs ran from the repo root in WSL with `python3.6`, on `main` at `d2a66ce` (Merge `exec/09-08` into main; all of 09-01..09-08 merged). **Every leg was green on the first run — zero `fix(09-09)` commits were needed.**

### 1a. Default gates — `python3.6 tests/run_gates.py`

| Gate | Result |
|------|--------|
| gate 1: syntax + plugin-path safety | PASS |
| gate 2: purity (AST) | PASS |
| gate 3: unittest (scoped discover) | PASS |

**Final unittest count: 1050 tests, `OK`** (995 pre-Phase-9 baseline + net-new wall tests; matches the plan's "995 + net-new" expectation). `run_gates: all gates green`.

### 1b. Required smokes — `python3.6 tests/run_gates.py --smoke`

Verdict = flushed `SMOKE-OK` sentinels ONLY (never exit codes, per AGENTS.md). **12/12 required smokes PASS:**

| # | Smoke | Sentinel |
|---|-------|----------|
| 1 | smoke/01_skeleton_smoke.py | `SMOKE-OK SKELETON` |
| 2 | smoke/03_viewer_bridge_smoke.py | `SMOKE-OK VIEWER-BRIDGE` |
| 3 | smoke/04_demo_e2e_smoke.py | `SMOKE-OK VIEWER-DEMO` |
| 4 | smoke/05_loop_camera_smoke.py | `SMOKE-OK LOOP-CAMERA` |
| 5 | smoke/06_input_smoke.py | `SMOKE-OK INPUT-WIZARD` |
| 6 | smoke/07_transform_sweep_smoke.py | `SMOKE-OK TRANSFORM` |
| 7 | smoke/08_stack_place_smoke.py | `SMOKE-OK EDGEON` |
| 8 | smoke/10_chain_count_smoke.py | `SMOKE-OK CHAIN-COUNT` |
| 9 | smoke/12_plot_smoke.py | `SMOKE-OK PLOT-RENDER` |
| 10 | smoke/13_mode_arrows_smoke.py | `SMOKE-OK MODE-ARROWS` |
| 11 | smoke/14_release_e2e_smoke.py | `SMOKE-OK RELEASE-E2E` |
| 12 | **smoke/15_line_wall_smoke.py** | **`SMOKE-OK LINE-WALL`** |

Informational smokes (non-blocking): smoke/02_dialog FAIL (the known 01-05 offscreen dead end — expected, unrelated), smoke/09_qprocess PASS, smoke/11_xtb_runner PASS. `gate 4: headless smokes (required) PASS`.

### 1c. Windows xtb leg — `python3.6 tests/run_gates.py --xtb`

| Item | Value |
|------|-------|
| xtb version | `xtb version 6.7.1pre (5071a88) compiled by 'Marcel@Raven' on 2024-07-23` |
| Verdict line | **`normal termination of xtb`** |
| Gate | `gate 5: xtb probe (Windows from WSL) PASS` |

Walls touch no xtb surface; recorded for phase-close completeness. `run_gates: all gates green`.

### 1d. Requirements audit — `python3.6 tools/audit_requirements.py` + scoped unittest

| Check | Result |
|-------|--------|
| ids-unique | PASS — all 46 canonical IDs appear exactly once |
| row-count | PASS — traceability table has exactly 46 ID rows |
| evidence-paths | PASS — all 136 cited Evidence path(s) exist |
| checkbox-agreement | PASS — checkbox list and table statuses agree for all 46 IDs |
| Verdict | **`AUDIT-OK requirements-ledger`** (exit 0) |

Scoped unittest `discover -s tests -p "test_audit_requirements.py" -v`: **Ran 16 tests — OK**. Route-(b) prior state confirmed: `tools/audit_requirements.py` and `tests/test_audit_requirements.py` are **unmodified** and green at 46/46.

### 1e. Battery summary

| Leg | Verdict |
|-----|---------|
| default gates | GREEN — 1050 tests, gates 1-3 PASS |
| required smokes | GREEN — 12/12 SMOKE-OK incl. LINE-WALL |
| Windows xtb | GREEN — `normal termination of xtb` |
| requirements audit | GREEN — 46/46, `AUDIT-OK` (zero tool/test churn) |

**No deviations were required. No fix commits. Merged tree is green across all four record types.**

## Task 2 — Owner feel-check verdicts (the blocking checkpoint) — VERBATIM RECORD

The owner ran the live feel-check in real Windows PyMOL with `SRP_DEBUG=1`, playing **two games (medium box / normal 9.0 A/s and small box / expert 13.0 A/s)**.

### Owner verdict (verbatim)

> "tested 2 games, medium-normal and small-expert. 1-6 pass, 7 head clearance can use 8 rest ok. others looks ok if i get it right"

### Verdict sections (all eight, as clarified/resolved by the orchestrator)

**1. Steps 1-6b — PASS** on two live games (medium box/normal 9.0 A/s + small box/expert 13.0 A/s, `SRP_DEBUG=1`). Verbatim from the owner note: **"1-6 pass"**. This covers:
- step 1: no red wall inside the box BEFORE the first capture (no wall at run start) — PASS;
- step 2: after the first capture the next mol AND the red wall line appear TOGETHER, inside the box, floor-to-ceiling, ends leaving a visible roundable corridor — PASS;
- step 3: NO-OVERLAP AUDIT — the `DBG wall spawn ... new_mol=... gap=...` line shows gap ≥ 3.0, visible on the molecule too, across several captures — PASS;
- step 4: AVOIDABILITY — steer across/around the wall freely; it persists until the NEXT capture swaps it for a different random wall (exactly one live wall at a time), including through the refuse/cooldown flows — PASS;
- step 5: DELIBERATE CRASH — steering the head into the wall shows `crashed into wall`, the run ends via the NORMAL completion path (snake complete; length/score/atoms recap; Get Spectra enabled) and the wall is GONE from the completion board (D-WALL-TEARDOWN (b)) — PASS;
- step 6: restart from the completion board -> fresh run, no wall until the first capture — PASS;
- step 6b (optional SC6 spot-check, PSE-WALL stage): save session to .pse, reopen in a fresh viewer, `Cleanup model` sweeps `srp_wall*` with zero plugin state (INFRA-04 fresh-process cleanup contract) — PASS.

**2. Step 7 — FEEL-NUMBER ROWS (single-data-line retunes):** **exactly ONE retune requested** — owner verbatim: **"head clearance can use 8 rest ok"**.
- **RETUNE:** head launch clearance `WALL_HEAD_CLEARANCE_A` 12.0 -> **8.0** A (applied in Task 3, commit `7042602`);
- **approved as shipped:** wall length `WALL_LENGTH_FRACTION` 0.45 / arbitrary angle [0, pi) / new-mol clearance `WALL_MOL_CLEARANCE_A` 3.0 / live clearance `WALL_LIVE_CLEARANCE_A` 3.0 / box-face inset `WALL_BOX_MARGIN_A` 6.0 / collision radius `WALL_COLLISION_RADIUS_A` 2.0 (engine table) / red (1.0, 0.0, 0.0) + linewidth 3.0 (wall look).

**3. Step 8 — DECISION-CONFIRM:** all rows **confirmed as shipped** — teardown-on-completion `del` (D-WALL-TEARDOWN (b)), HUD silent (no spawn line), help-clause wording unchanged, and **requirement mapping route (b)** confirmed (dated GAME-05 amendment; coverage stays 46/46).

**4. Speed confirmation (owner's speed question):** CONFIRMED current — quick-003 tiers 6.0/9.0/11.0/13.0 A/s with `DEFAULTS['speed']` 9.0 ('normal'); verified live against the `SPEED_TIERS` table + commit `913fbd5` in history. The two games were played at 9.0 and 13.0 A/s.

**5. Accumulate-walls candidate idea (owner-floated) — DEFERRED, NOT applied.** The owner floated **ONE candidate idea**: walls that persist/accumulate (possibly shorter) instead of being replaced per spawn. Assessment: this is a **design-contract change**, i.e. **NEW-PLAN scope** — it alters the one-live-wall replacement contract that every Phase-9 layer (engine reset, bridge seat, teardown wiring, smoke STAGE5/6) was built and pinned against, so it requires its own TDD plan (new replacement/accumulation semantics + spread/cadence pins + re-proof). **DEFERRED as a future-insertion candidate** (the 5.3 edge-bias-spawn deferral precedent: record the sketch, needs its own plan if picked up). It is **NOT part of this amendment** and was **NOT applied** here.

## Task 3 — Retune + REQUIREMENTS route-(b) amendment

### 3a. Feel retune — `WALL_HEAD_CLEARANCE_A` 12.0 -> 8.0

- **Edit:** ONE data line in `serpentrum/wall.py`'s single tunable constants table — `WALL_HEAD_CLEARANCE_A = 12.0` -> `8.0`; the constant's inline comment reaction-time arithmetic was resynced to the new value in the same logical edit (`~0.89 s reaction at the 9.0 A/s default, ~0.62 s at expert 13.0`; was `~0.63 s` / `~0.22 s`).
- **Zero test edits:** the 09-01 derivation mandate holds — `tests/test_wall.py` references `wall.WALL_HEAD_CLEARANCE_A` symbolically (lines 276/290/368) and `tests/test_phase5_integration.py` imports the symbol; **no pin hardcoded 12.0**, so no coupled-pin resync was needed (the 913fbd5 discipline was available but not required).
- **Scoped suite:** `python3.6 -m unittest discover -s tests -p "test_wall.py" -v` -> **Ran 16 tests — OK**.
- **Gates:** `python3.6 tests/run_gates.py` -> **all gates green, 1050 tests OK** (gate 1 syntax + plugin-path PASS, gate 2 purity PASS, gate 3 unittest PASS).
- **Commit:** `7042602` — `fix(09-09): retune wall head launch clearance to 8 A per owner feel-check`.

### 3b. REQUIREMENTS.md route-(b) amendment

- **UTC date used:** **2026-10-13** (stamped via `date -u +%Y-%m-%d`, never the local HKT date).
- **GAME-05 bullet:** appended the italic clause — *— **Phase 9 (2026-10-13, planner verdict route (b))**: the box may also hold ONE random line-wall (replaced at each next-mol spawn, never overlapping the newly spawned mol); head contact with it ends the run as the same crash class (snake still completes -> spectra).*
- **Dated footer note** (below the 2026-10-10 block): *2026-10-13 — Phase 9 (Random Line-Wall Spawning) COMPLETE: GAME-05 amended (third lethal-collision class: the random line-wall); spawn-pairing policy refined on the 5.3 model. Coverage stays 46/46.*
- **Zero audit-tool churn:** `tools/audit_requirements.py` and `tests/test_audit_requirements.py` are **byte-untouched** (`git diff --stat` empty). Both verified green: scoped unittest **Ran 16 tests — OK**; tool **`AUDIT-OK requirements-ledger`** (ids-unique / row-count / evidence-paths / checkbox-agreement all PASS at 46/46).
- **Commit:** `4c4e538` — `docs(09): GAME-05 dated amendment — Phase 9 wall crash class (coverage stays 46/46)`.

## Task Commits

1. **Task 1: full battery recorded (gates + 12/12 smokes + xtb + audit)** — `a1ff179` (docs) — `docs(09-09): record phase-close battery verdicts (checkpoint pending)`
2. **Task 3a: head launch clearance retune** — `7042602` (fix) — `fix(09-09): retune wall head launch clearance to 8 A per owner feel-check`
3. **Task 3b: REQUIREMENTS route-(b) amendment** — `4c4e538` (docs) — `docs(09): GAME-05 dated amendment — Phase 9 wall crash class (coverage stays 46/46)`
4. **Task 3c: SUMMARY finalization** — `(this docs commit)` (docs) — `docs(09-09): finalize phase close — owner verdicts, retune + amendment records`

## Files Created/Modified

- `.planning/phases/09-random-line-wall-spawning/09-09-SUMMARY.md` - this phase-close record (battery tables + all eight owner verdicts + retune/amendment records + phase-wrap one-liner)
- `serpentrum/wall.py` - `WALL_HEAD_CLEARANCE_A` 12.0 -> 8.0 + comment arithmetic resync
- `.planning/REQUIREMENTS.md` - GAME-05 italic route-(b) clause + dated footer note

## Decisions Made

- **Battery-before-checkpoint honoured:** the full battery was recorded before the blocking feel-check, so the owner played on recorded-green state (the 5.3-05 pattern, locked in the plan).
- **One retune only:** head launch clearance 12.0 -> 8.0 A (owner verdict); every other feel row and all four decision rows (teardown/HUD/help/route-b) confirmed as shipped.
- **Route (b) landed:** the wall extends GAME-05's lethal-collision class via a dated amendment; coverage stays 46/46; the closed GATE V ledger keeps its meaning; audit tool + test untouched.
- **Accumulate-walls idea deferred:** a design-contract change is new-plan scope (5.3 edge-bias precedent); recorded as a future-insertion candidate, not applied.

## Deviations from Plan

None - Tasks 1-3 executed as written. The only conditional path the plan anticipated (a coupled-pin resync in `tests/test_wall.py`) did NOT fire — the derivation-mandated tests reference the constant symbolically, so the single data-line retune needed zero test edits.

## Issues Encountered

None. Informational smoke/02 remains a pre-existing non-blocking FAIL (01-05 offscreen dead end), unrelated to Phase 9.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **Phase 9 is COMPLETE:** battery green + recorded; owner feel-check APPROVED (two live games); shipped constants == approved constants (single retune applied); GAME-05 amendment landed via route (b) with the audit tool + test byte-identical at 46/46.
- **Phase-wrap one-liner (for STATE/ROADMAP consumption by the orchestrator):**
  > Phase 9 (Random Line-Wall Spawning) COMPLETE — 9/9 plans. The random line-wall spawns with the next mol (one live wall, replaced per spawn, never overlapping the newly spawned mol), is avoidable, and head contact ends the run as the same crash class (snake completes -> spectra); walls vanish from the completion board and after Restart. Owner feel-check APPROVED on two live games (medium/normal + small/expert); ONE retune applied (head launch clearance 12.0 -> 8.0 A, commit 7042602); all other feel rows + decision rows confirmed as shipped. REQUIREMENTS GAME-05 dated route-(b) amendment landed (commit 4c4e538, UTC 2026-10-13), coverage stays 46/46 with the audit tool + test byte-untouched. Battery: default gates 1050 tests OK, 12/12 required smokes SMOKE-OK incl. LINE-WALL, Windows xtb normal termination, audit 46/46. The accumulate-walls idea was DEFERRED as a new-plan candidate.
- **Orchestrator-owned next steps (off-limits to this executor):** update `.planning/STATE.md` position/progress and the `.planning/ROADMAP.md` Phase 9 row; milestone audit/archive (`/gsd-audit-milestone`, `/gsd-complete-milestone`) remains deferred until Phase 9's wrap lands.

---
*Phase: 09-random-line-wall-spawning*
*Completed: 2026-10-13*
