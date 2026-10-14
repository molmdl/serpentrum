---
phase: 09-random-line-wall-spawning
verified: 2026-10-14T00:00:00Z
status: passed
score: 36/36 must-haves verified
re_verification: none (initial verification)
gaps: []
---

# Phase 9: Random Line-Wall Spawning — Verification Report

**Phase Goal:** Picking up a molecule spawns the NEXT molecule and exactly ONE seeded-random pure-red line-wall inside the box together (same event, both respawn paths) — never overlapping the newly spawned mol (per-atom 3.0 Å clearance, live-auditable via SRP_DEBUG), fair (box-face inset, launch clearance, live-mol clearance), head contact crashes through the existing completion path ('crashed into wall', snake complete → Get Spectra); pickup spawning, the v1 release record, and GAME-07 replay determinism stay byte-identical.
**Verified:** 2026-10-14 (initial verification, no prior VERIFICATION.md)
**Status:** **PASSED**
**Re-verification:** No — initial

**Verifier methods:** all must-haves checked against actual code (existence → substance → wiring); full gate suite re-run live (`python3.6 tests/run_gates.py` → **1050 tests OK, all 3 gates green**); headless Windows PyMOL wall smoke re-run live (`smoke/15_line_wall_smoke.py` → **all 6 stage sentinels + `SMOKE-OK LINE-WALL` flushed**); requirements audit re-run live (**AUDIT-OK 46/46**); `git diff d02c030..HEAD -- serpentrum/spawn.py tests/test_spawn.py` → **EMPTY** (byte-identical).

> **Sanctioned retune (per verification mandate — NOT a gap):** `WALL_HEAD_CLEARANCE_A` 12.0 → **8.0** (commit `7042602`, wall.py:68) is the owner-APPROVED feel-check value under SC4's owner-retunable-constants contract. The ROADMAP's "12.0" is the DRAFT default. Verified: the single data-line edit landed in the wall.py constants table, the inline reaction-time comment was resynced, and tests derived from constants needed ZERO edits (gates green). Correctly executed retune.

---

## Goal Achievement — Plan-by-Plan Must-Have Verdicts

### 09-01 — serpentrum/wall.py: WallSpawner policy + tests/test_wall.py

| Must-have | Verdict | Evidence |
|---|---|---|
| `wall_seed_from_setup` derives distinct crc32 seed salted from pickup seed | ✓ VERIFIED | wall.py:77-87 — `zlib.crc32(('%d\|%s' % (pickup_seed, WALL_SALT)))`, `WALL_SALT = 'wall-v1'` (:74); TestStreamIsolation (test_wall.py:184) proves pickup-stream isolation |
| `next_wall` deterministic, 3 seeded draws in pinned order (x, y, theta∈[0,π)) | ✓ VERIFIED | wall.py:182 `random.Random(seed)`; :218 `next_wall`; TestDeterminism (:160) passes in 1050-suite |
| All FOUR clearance legs (box margin, per-atom mol, head, live mols) | ✓ VERIFIED | wall.py:64-73 constants table (margin 6.0, mol 3.0, head **8.0 sanctioned**, live 3.0); TestGeometry (:229) incl. straddle rejection — suite green |
| `WALL_MAX_DRAWS` exhaustion → None; degenerate box → None; draws consumed every attempt | ✓ VERIFIED | TestExhaustion (:326); RNG-state-level pin at :342-350 — degenerate (0,0)-(13,13) case proven via `_rng.getstate()` advance (the documented 09-01 deviation: proven at RNG-state level, no hardcoded position — sound) |
| spawn.py byte-identical; interleaved wall draws don't disturb pickup stream | ✓ VERIFIED | `git diff d02c030..HEAD -- serpentrum/spawn.py tests/test_spawn.py` = EMPTY; suite green |
| Artifact wall.py ≥160 lines, contains WALL_LENGTH_FRACTION | ✓ VERIFIED | 279 lines; constants at :64-74 |
| Artifact test_wall.py (est. 450), contains WallSpawner | ✓ VERIFIED (documented deviation) | 431 lines vs 450 estimate; **all 16 test methods in 7 classes present** (TestSeed/Determinism/StreamIsolation/Geometry/Exhaustion/CtorKwargs/MinAtomClearance) — estimate shortfall only, coverage complete |

### 09-02 — engine wall state + ('crashed','wall') referee leg

| Must-have | Verdict | Evidence |
|---|---|---|
| `wall` state (None / 2-endpoint tuple), set_wall/clear_wall, wall=None kwarg on __init__/reset | ✓ VERIFIED | game_engine.py:889 `set_wall`, :909 `clear_wall`; TestWallState (test_engine_wall.py:114) green |
| Head within WALL_COLLISION_RADIUS_A (2.0, STRICT <, squared) → ('crashed','wall'), finished=True, result='crashed', pending=[], snake complete | ✓ VERIFIED | game_engine.py:739-747 — exact end-state shape, strict `< WALL_COLLISION_RADIUS_A ** 2`; TestWallCrash (:179) |
| Referee order: moved → boundary → WALL → body → stacked; boundary-over-wall and wall-over-body precedence | ✓ VERIFIED (read in code) | step(): moved :709 → boundary :720-731 → **wall :732-747** → body :748-765 → stacked :766+; TestRefereeOrder (:267) |
| Head-only binding; sweeps never check; wall=None byte-identical streams | ✓ VERIFIED | wall leg sits after the sweep early-return (:690-703 returns before motion); TestHeadOnlyScope (:424) incl. wall=None parity |
| Artifact game_engine.py contains WALL_COLLISION_RADIUS_A | ✓ VERIFIED | :112 `WALL_COLLISION_RADIUS_A = 2.0` beside the body radius |
| Artifact test_engine_wall.py ≥320 lines, 6 named classes | ✓ VERIFIED | 602 lines; TestWallState/Crash/RefereeOrder/StrictEdge/HeadOnlyScope/LifecycleInvariants — all six present |

### 09-03 — cgo_build.wall_cgo 42-float LINES fence

| Must-have | Verdict | Evidence |
|---|---|---|
| 42-float vertical 4-edge fence from opposite 3D corners | ✓ VERIFIED | cgo_build.py:137 `def wall_cgo(p1, p2, color=(1.0, 0.4, 0.1), linewidth=2.0)`; 42-float + structure pins in TestWallCgo — green in 1050-suite |
| Parses under the existing mini-interpreter with ZERO harness changes | ✓ VERIFIED | tests/test_cgo_build.py:405 `class TestWallCgo`, streams via `wall_cgo(` at :420-506; `git diff d02c030..HEAD` harness untouched (suite green proves) |
| Color/linewidth into single header; defaults mirror box_cgo kwargs; all floats | ✓ VERIFIED | :137 kwargs defaults; TestWallCgo color/linewidth/all-floats tests green |
| Key link: local opcode constants, no pymol import | ✓ VERIFIED | wall_cgo lives beside box_cgo in the pure module (purity gate 2 green) |

### 09-04 — hud_logic.debug_wall_trace + help 'playing' clause

| Must-have | Verdict | Evidence |
|---|---|---|
| Exact SRP_DEBUG line `'DBG wall spawn <id> p1=(%.2f,%.2f) p2=(%.2f,%.2f) len=%.4f new_mol=<pid>@(%.2f,%.2f) gap=%.4f'` + conditional `' tick=%d'` | ✓ VERIFIED (read in code) | hud_logic.py:443-460 — exact %-format builder, `gap` field present, `if tick is not None: line += ' tick=%d'` |
| help 'playing' names red walls lethal, ASCII-pure, ValueError contract untouched | ✓ VERIFIED | help_text.py:169-171 exact literal `'Steer with the arrow keys. Red wall lines are obstacles - touching one ends the run. If keys seem dead, click the 3D viewer first.'`; test_help_text.py:151 re-pinned same-commit (019caef/843eee5) |
| check_docs/audit families untouched (docs stay hidden) | ✓ VERIFIED | audit re-run AUDIT-OK 46/46; no check_docs edits since d02c030 |
| NO wall_spawn_note builder; NO REFUSE_WALL taxonomy (absence pins) | ✓ VERIFIED | TestWallWiring `test_no_wall_kwarg_or_refuse_wall_literals` (test_hud_content.py:1033+ block, test at relative :100) green; grep confirms neither symbol exists in production modules |
| Artifacts: hud_logic (contains def debug_wall_trace), help_text (contains literal), TestWallDebugTrace ≥30 lines | ✓ VERIFIED | hud_logic.py:443; help_text.py:169; TestWallDebugTrace at test_hud_content.py:962 (71 lines to next class) |

### 09-05 — pymol_bridge wall channel

| Must-have | Verdict | Evidence |
|---|---|---|
| `load_line_wall(p1_xy, p2_xy, ...)` builds ONE wall CGO, z from BOX_DISPLAY_Z, returns name; replace semantics in caller | ✓ VERIFIED | pymol_bridge.py:527-543 — `cmd.load_cgo(cgo_build.wall_cgo((p1[0],p1[1],-BOX_DISPLAY_Z),(p2[0],p2[1],BOX_DISPLAY_Z),...))`; caller does delete-then-load (gui_game:1299-1300); live STAGE2 WALL-REPLACE extent-moved proof |
| `delete_walls()` removes every srp_wall* (pattern delete, idempotent, every end path) | ✓ VERIFIED | :546-555 `cmd.delete('srp_wall*')`; live STAGE5 WALL-DELETE `removed=2 sentinel+pickup survive`; STAGE6 SCENECLR-WALL `left=0` |
| DEFAULT_WALL_COLOR pure red (1.0,0.0,0.0); DEFAULT_WALL_LINEWIDTH 3.0 | ✓ VERIFIED | :522 `DEFAULT_WALL_COLOR = (1.0, 0.0, 0.0)`; :524 `DEFAULT_WALL_LINEWIDTH = 3.0` |
| ZERO new imports, ZERO purity edits, srp_ prefix reserved | ✓ VERIFIED | purity gate green; WALL_NAME='srp_wall' :521 — cleanup_srp pattern coverage (smoke STAGE6 fresh-process sweep) |
| Key links: `cgo_build.wall_cgo(` + `cmd.delete('srp_wall*')` | ✓ VERIFIED | :540 and :555 — both grep-confirmed |

### 09-06 — s10 integration scenario (test_phase5_integration.py)

| Must-have | Verdict | Evidence |
|---|---|---|
| s10 proves controller-mirroring seam order (note_resolution → next_after → seed append → next_wall → set_wall) at every capture | ✓ VERIFIED | test_phase5_integration.py:823 `test_s10_wall_spawn_pairing_and_crash`; :828 docstring pins the order; :954 `next_wall(`, :957 `set_wall` — scenario name 's10' :854 (NOT s9) |
| No-overlap invariant: translated atoms ≥ WALL_MOL_CLEARANCE_A - TOL from fresh wall at every capture | ✓ VERIFIED | s10 clearance assertions derived from constants — green in 1050-suite |
| Wall crash → ('crashed','wall'), result 'crashed', finished True, snake complete; begin-no-wall invariant | ✓ VERIFIED | :1023-1027 final event EXACTLY ('crashed','wall'); :1050 proof stream; begin-no-wall assertion green |
| GAME-07 end-to-end re-run byte-identical; s1-s9 untouched | ✓ VERIFIED | s10 replay block green; s1-s9 unmodified (whole 1050-suite green; test_phase5_integration diff is additive only per plan files_modified) |
| Key links: `next_wall(` + `'crashed', 'wall'` | ✓ VERIFIED | :954, :1027, :1050 |

### 09-07 — gui_game wall wiring (the seam)

| Must-have | Verdict | Evidence |
|---|---|---|
| WallSpawner at EXACTLY ONE site (_build_engine), seeded via wall_mod.wall_seed_from_setup, session 'wall_spawner' (None on no-records) | ✓ VERIFIED | gui_game.py:79 `from . import wall as wall_mod`; :541 `extras['wall_spawner'] = wall_mod.WallSpawner(` (sole site); :543 `wall_mod.wall_seed_from_setup(setup)` (sole site); :515 None default; TestWallWiring count==1 pins green |
| Seam INSIDE _respawn_pickup success-branch tail; finished guard → None-spawner → next_wall → None keeps old wall → set_wall + delete_walls + load_line_wall + debug-gated trace | ✓ VERIFIED (read in code) | gui_game.py:1277-1308: `if engine.finished: return` → `wall_spawner is None: return` → `next_wall(engine.head, seed['atoms'], other_live_atoms)` → None→return → `set_wall` :1298 → `delete_walls()` :1299 → `load_line_wall` :1300 → gap :1304 + `debug_wall_trace` :1305 computed UNCONDITIONALLY, only `self._log` gated by `session.get('debug')` :1307-1308 |
| _teardown_round delete_walls beside delete_pickups | ✓ VERIFIED | :1577 `pymol_bridge.delete_walls()   # Phase 9: walls die on every end path` inside `_teardown_round` (:1534); TestWallWiring body-slice pin green |
| TestWallWiring source-scan pins, all pre-existing count pins stay ==1 | ✓ VERIFIED | test_hud_content.py:1033+ — 9 test methods verified (single WallSpawner site, single seed wiring, single next_wall/load_line_wall/debug_wall_trace call, finished guard in body slice, teardown delete_walls, build_engine construction, absence literals) |
| Key links: next_wall→set_wall→load_line_wall seam order; debug_wall_trace consumed; delete_walls in teardown | ✓ VERIFIED | gui_game.py:1294/1298-1300, :1305, :1577 |

### 09-08 — smoke/15 + REQUIRED_SMOKES registration

| Must-have | Verdict | Evidence |
|---|---|---|
| 6 flushed-sentinel stages + final `SMOKE-OK LINE-WALL` | ✓ VERIFIED **LIVE** | Re-ran headless smoke: STAGE1 WALL-LOADED spans=30.000,25.000,10.000 / STAGE2 WALL-REPLACE extent moved / STAGE3 WALL-SPAWN ticks=4 pickup=pick_0001 clearance=93.1738 / STAGE4 WALL-CRASH reason=wall / STAGE5 WALL-DELETE removed=2 / STAGE6 SCENECLR-WALL left=0 → **SMOKE-OK LINE-WALL** |
| run_gates REQUIRED_SMOKES append-at-end hunk only | ✓ VERIFIED | tests/run_gates.py:78-80 — tuple entry + per-plan Phase 9 comment after smoke-14; SMOKE_TIMEOUT untouched |
| Full --smoke battery 12/12 | ✓ VERIFIED | Recorded battery (09-09-SUMMARY) + live wall-smoke re-run green today; 02 informational FAIL = known non-blocking |
| Tree rules: NO QApplication, no widgets, no __init__.py, _resolve_root | ✓ VERIFIED | grep: zero QApplication/exec_ matches in smoke/15; STAGE0 banner "no-Qt-App CGO-only"; gate 1 plugin-path safety green |
| Artifacts: smoke/15 ≥120 lines contains verdict; run_gates contains 15_line_wall_smoke | ✓ VERIFIED | 412 lines; verdict sentinel at :24 docstring + flushed live |

### 09-09 — phase close: battery + owner feel-check + amendment

| Must-have | Verdict | Evidence |
|---|---|---|
| Full battery green and recorded BEFORE checkpoint | ✓ VERIFIED | 09-09-SUMMARY.md battery tables (a1ff179) precede verdicts (130c957); re-run live today: gates 1050 OK, AUDIT-OK 46/46 |
| Live owner feel-check APPROVES (SRP_DEBUG=1) | ✓ VERIFIED (record) | 09-09-SUMMARY Task 2: two live games (medium/normal + small/expert), steps 1-6b PASS, verdicts verbatim |
| Shipped constants match owner verdicts; retune = single data-line edit + re-gates | ✓ VERIFIED | Exactly ONE retune: `WALL_HEAD_CLEARANCE_A` 12.0→8.0, wall.py:68, commit `7042602`, "zero test edits" (derivation discipline held — suite green) |
| REQUIREMENTS.md route-(b) dated amendment; coverage 46/46; audit tool+test ZERO edits | ✓ VERIFIED | REQUIREMENTS.md:31 italic Phase 9 wall clause on GAME-05; :191 dated footer 2026-10-13 "Coverage stays 46/46"; `git diff d02c030..HEAD -- tools/audit_requirements.py tests/test_audit_requirements.py` = EMPTY; commit `4c4e538`; live audit AUDIT-OK 46/46 |
| Artifacts: 09-09-SUMMARY contains feel-check; REQUIREMENTS contains Phase 9 | ✓ VERIFIED | Both grep-confirmed |
| Key link: single-retune path via wall.py constants table | ✓ VERIFIED | WALL_LENGTH_FRACTION et al. at wall.py:64-74; the 7042602 retune exercised the exact path |

---

## Observable Truths (phase-goal level)

| # | Truth (ROADMAP SC) | Status | Evidence |
|---|---|---|---|
| 1 | Exactly one red wall on the SAME event as next-mol spawn at BOTH respawn call sites; no spawn ⇒ no wall; never at run start; never on win tick | ✓ VERIFIED | Seam lives inside `_respawn_pickup` success tail (gui_game:1277+) so capture-tail AND cooldown-resume inherit it by construction; `engine.finished` win-tick guard :1284; s10 begin-no-wall invariant; TestWallWiring pins |
| 2 | Wall never overlaps new mol — per-atom ≥3.0 Å, SRP_DEBUG 'DBG wall spawn ... gap=' auditable | ✓ VERIFIED | WALL_MOL_CLEARANCE_A=3.0 leg in WallSpawner; debug_wall_trace exact format with gap field; gui_game:1304 unconditional gap via min_atom_clearance on raw sym-first atoms; smoke STAGE3 clearance=93.17 live |
| 3 | Head contact → ('crashed','wall') after boundary/before body; normal completion path; GUI 'crashed into wall' with ZERO new crash-handler code | ✓ VERIFIED | game_engine.py:732-747 leg placement; s10 crash assertions; gui_game diff shows no crash-handler edits (seam-only lines); TestRefereeOrder |
| 4 | Fairness constants owner-retunable in the single wall.py table (SC4 contract) | ✓ VERIFIED | wall.py:64-74 single table; margin 6.0 / head **8.0 (sanctioned owner retune)** / mol+live 3.0 / length 0.45 / max draws 32; retune 7042602 exercised the one-line path |
| 5 | GAME-07 both streams deterministic; spawn.py + test_spawn.py byte-identical | ✓ VERIFIED | `git diff d02c030..HEAD -- serpentrum/spawn.py tests/test_spawn.py` = EMPTY; separate crc32(pickup_seed\|'wall-v1') stream; s10 byte-identical re-run green |
| 6 | Wall hygiene: gone at completion (_teardown_round delete_walls), after Restart (cleanup_srp), swept in fresh .pse; help hint names red walls | ✓ VERIFIED | gui_game:1577; smoke STAGE5/6 live (`removed=2`, `left=0`); help_text.py:169 |
| 7 | Live owner feel-check APPROVES (the ONE blocking checkpoint) | ✓ VERIFIED (recorded) | 09-09-SUMMARY Task 2 verbatim record: APPROVED on two live games, exactly one retune requested and applied |

**Score:** 36/36 plan must-haves verified; 7/7 phase SC truths verified.

## Requirements Coverage

| Requirement | Status | Blocking Issue |
|---|---|---|
| GAME-05 (route-(b) amendment — wall as third lethal class) | ✓ SATISFIED | none — amendment landed (4c4e538), coverage 46/46, audit green live |
| GAME-07 (replay determinism — extended to wall stream) | ✓ SATISFIED | none — separate derived rng, byte-identical replay proofs |
| GAME-09 (viewer clears on completion — wall teardown) | ✓ SATISFIED | none — _teardown_round + cleanup_srp + smoke STAGE5/6 |
| DOCS-03 (help names red walls) | ✓ SATISFIED | none — exact clause shipped + re-pinned test |

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---|---|---|---|
| — | — | No blockers found | — | — |

No TODO/FIXME/placeholder/stub patterns in any Phase-9 artifact. All handlers real, all queries consumed, no console-log-only paths. The two documented deviations (test_wall.py 431 vs 450 estimate with all 16 tests present; 09-01 RNG-state-level degenerate pin; 09-06 test-side enrichments) are judged fair — estimate shortfalls, not coverage gaps.

## Human Verification Required

None outstanding. The phase's one blocking human checkpoint (SC7 owner feel-check) was executed and recorded verbatim in 09-09-SUMMARY.md (two live games, SRP_DEBUG=1, APPROVED, one retune applied and re-gated). Live-behavior proofs (smoke sentinels, spawn/crash/teardown channels) were re-verified headless today.

## Gaps Summary

No gaps. All 9 plans' must-haves verified against actual code at all three levels; all key links wired (gui_game seam → WallSpawner/set_wall/load_line_wall/debug_wall_trace/delete_walls; engine referee boundary→wall→body; pymol_bridge → cgo_build.wall_cgo; run_gates → smoke/15); suite proofs re-run live (1050 OK, AUDIT-OK 46/46, SMOKE-OK LINE-WALL, spawn.py byte-identical since d02c030). **Phase goal achieved.**

---

_Verified: 2026-10-14_
_Verifier: OpenCode (gsd-verifier)_
