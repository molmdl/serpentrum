---
phase: 05-stacking-game-rules
plan: 16
subsystem: testing
tags: [pymol-plugin, phase-gate, human-verify, checkpoint, smoke-tests, live-gameplay, stacking-game, phase-closing]

# Dependency graph
requires:
  - phase: 05-stacking-game-rules
    provides: 05-01..05-15 (full stacking game: dataset geometry, engine, placement, sweeps, capture seam, HUD info blocks, spawn/win, completion presenter + Get Spectra)
  - phase: 04-game-loop-input
    provides: game loop, input wizard, viewer bridge that the 8-step live checklist exercises
provides:
  - Phase 5 phase-closing gate evidence: 640 unittests green, 7/7 required smokes green (flushed SMOKE-OK sentinels)
  - 8-step consolidated human-verify checkpoint APPROVED across 7 live rounds (2026-09-18..20)
  - smoke/08_stack_place_smoke.py 8-sentinel contract (EDGEON, PLACE360, PLANEPAR, SPAWNOFFS, HEADRESET, PICKUPS, SCENECLR, UPLEDGEON)
  - SRP_DEBUG=1 tracer contract (capture lines dot/d + per-event steering lines)
  - Final owner-directive behavior contract replacing the plan's stale must_haves (train-follow, 180-only veto, no wall placement gate, cooldown spawn, upload skip parity)
affects: [05.1-speed-tiers (GAME-11 builds on the approved v1 base), 06-xtb-pipeline (consumes the verified complete snake), 07-spectra-ui (Get Spectra handoff proven live, win AND crash)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "verdict = flushed SMOKE-OK sentinels, never exit codes (PyMOL swallows rc)"
    - "SRP_DEBUG=1 live tracer: capture lines print dot/d per stack; per-event steering lines for turn-request/refuse/skip triage"
    - "owner-directive override contract: mid-checkpoint behavior changes carry a recorded directive lineage in STATE.md Decisions and BECOME the replacement must_haves for final verification"
    - "phase-closing checkpoint spans multiple live rounds; partial per-item approvals accumulate in STATE.md until final pass"

key-files:
  created: []
  modified:
    - smoke/08_stack_place_smoke.py
    - .planning/debug/resolved/05-ghost-point-turn-lock.md
    - .planning/debug/resolved/05-lagging-tail-wall-box.md
    - .planning/debug/resolved/05-16-retest-fixes.md
    - .planning/debug/resolved/05-upload-only-endless-run.md

key-decisions:
  - "Train-follow tail: the chain translates rigidly with the head on every 'moved' tick (replaces stationary-tail model) — owner directive 2026-09-18"
  - "Turn veto refuses ONLY 180-degree reversal; the sweep pre-check for body/pickup/boundary legs was deleted entirely (silent pass) — owner directive 2026-09-18/19"
  - "Only the head is box-bound; REFUSE_WALL placement gate removed entirely (near-wall stack placements allowed); REFUSE_ATOM clash kept as the STACK-05 demonstrator — owner directive 2026-09-19"
  - "Box presets bumped twice for cap-10 winnability: small ±35 / medium ±55 / large ±85 — owner directive 2026-09-18/19"
  - "Pool exhaustion is a 100-tick resumable cooldown, not permadeath; spawn demotion after refuse + refused-pickup despawn + ReasonCoalescer — owner directive 2026-09-19"
  - "Upload captures route to the clean-skip path pre-geometry (no placement crash) with edge-on render parity and upload head parity — owner directive 2026-09-19"
  - "Recap taxonomy: SKIP_* -> 'skipped Nx', REFUSE_* -> 'refused Nx'; begin_game demo-mode note for zero-stackable sets via hud_logic.stack_mode_note — owner directive 2026-09-20"

patterns-established:
  - "Phase-closing plan = gates (auto) + ONE consolidated human-verify (blocking); diagnosis flows fix(05) -> re-gate -> re-checkpoint"
  - "Live-round checkpointing: each round's DBG/evidence narrows open items; APPROVED verdicts are per-checklist-item, not per-session"

# Metrics
duration: ~3 days wall-clock across 7 live rounds (2026-09-18..20); executor + live-session time not aggregated
completed: 2026-09-20
---

# Phase 5 Plan 16: Phase-Closing Gates + Human Checkpoint Summary

**Phase 5 closed green: 640 unittests + 7/7 required smokes, and the 8-step live-PyMOL human-verify APPROVED BY EVIDENCE across 7 rounds (2026-09-18..20) — the complete v1 stacking game (train-follow snake, 180-only veto, near-wall stacking, upload skip parity, cap-10 win, completion + Get Spectra) hands a verified snake to Phases 5.1/6/7.**

## Performance

- **Duration:** checkpoint window 2026-09-18 → 2026-09-20 (7 live rounds; Task 1 gates green earlier, held green throughout via re-gates after each fix batch)
- **Completed:** 2026-09-20
- **Tasks:** 2 (Task 1 auto gate pass; Task 2 blocking checkpoint:human-verify)
- **Files modified:** code + smokes + tracer + 4 resolved debug archives (no code changes in this finalization — documentation only)

## Accomplishments

- Task 1 gate pass green and held green: `python3.6 tests/run_gates.py` (640 unittests) + `python3.6 run_gates.py --smoke` (7/7 required smokes via flushed SMOKE-OK sentinels; smoke 08 STACK-PLACE = 8/8 steps incl. UPLEDGEON + SCENECLR; smoke 02 informational FAIL remains the known 01-05 offscreen dead end, non-blocking).
- Task 2 consolidated human-verify — the phase's single blocking human gate — APPROVED across 7 live rounds in real Windows PyMOL: every checklist item in the plan's 8-step how-to-verify passed, including the final-pass upload-only demo-mode test.
- The checkpoint window absorbed 7 owner-directive behavior overrides (see Deviations): each was diagnosed live, fixed, unit/smoke-re-gated, and re-verified; the directives ARE the replacement must_haves the final verdict was rendered against, with lineage recorded in STATE.md Decisions 2026-09-19/20.
- Debug instrumentation landed and was archived: SRP_DEBUG=1 tracer contract, plus four resolved debug sessions under `.planning/debug/resolved/`.

## Task Commits

Task 1 was a diagnosis-only gate pass (plan-locked: `tests/run_gates.py` itself never modified; zero patch-escape-hatch edits needed at gate time). Task 2 was a blocking human checkpoint spanning 7 live rounds — the checkpoint-window commits below are its driving/repair history, ordered as they landed:

1. `b4b5b34` (test) — parallelism regression test: ring-plane parallelism pinned for all four headings
2. `47eaba2` (fix) — perpendicular-stack fix: root cause was `_reset_head_viewer` double-applying `edge_on_m16`; fixed via `pymol_bridge.reload_head`
3. `d11295b` (feat) — SRP_DEBUG live tracer (05-16 retest instrument)
4. `0af3cde` (fix) — ghost-point turn feedback: refusal WHY lines explain + SRP_DEBUG turn-request tracer
5. `cb02333` (test) — ghost-point turn-veto regression + HUD turn-feedback pins
6. `8a17a74` (docs) — debug archive: 05-ghost-point-turn-lock
7. `af33de9` (docs) — debug archive: 05-lagging-tail-wall-box (train-follow / head-only-walls / bigger-boxes)
8. `76d74b3` (fix) — train-follow tail: chain translates rigidly with the head on every 'moved' tick (owner directive)
9. `cd04525` (fix) — head-only wall veto in turn sweeps (owner directive)
10. `69b8fb0` (feat) — box presets v1 bump (owner directive)
11. `7659555` (fix) — turn veto refuses ONLY 180-degree reversal; body/pickup sweep pre-check deleted (owner directive)
12. `f211d97` (fix) — refused pickups despawn + spawn demote-after-refuse stops the refuse cascade + ReasonCoalescer
13. `56dd68b` (fix) — begin_game hard-cleans every `srp_*` before materializing (restart leftovers rode the wildcard)
14. `98bf9f2` (fix) — box presets re-scaled to small ±35 / medium ±55 / large ±85 for cap-10 winnability (owner directive)
15. `ee2a1d8` (fix) — pool-exhaustion permadeath replaced by 100-tick resumable cooldown (deadlocked runs near walls)
16. `6b3017a` (test) — pin cooldown semantics
17. `415cf50` (docs) — game-3 deadlock note: pool_exhausted latch is now a cooldown
18. `d33f74c` (fix) — REFUSE_WALL placement gate removed; only the head is box-bound; REFUSE_ATOM clash kept as the STACK-05 demonstrator (owner directive)
19. `93f4b2b` (fix) — upload captures skip cleanly (clean skip routing pre-geometry, no placement crash) + upload molecules render edge-on
20. `22b7245` (test) — pin upload skip routing + edge-on/upload head parity
21. `3f89779` (docs) — re-test-fixes archive (wall-gate removal + upload path fixes)
22. `e0b2814` (fix) — recap taxonomy: SKIP_* -> "skipped Nx", REFUSE_* -> "refused Nx" (C4)
23. `64882c3` (fix) — begin_game demo-mode note for zero-stackable sets via `hud_logic.stack_mode_note` (C1)
24. `2bff573` (docs) — resolve upload-only endless-run debug session (C1+C4; C2 soft Start-warning evaluated, left as owner opt-in)

**Plan metadata:** this commit (docs: complete phase-closing gates + human checkpoint plan)

## Checkpoint Verdicts (Task 2 — per checklist step)

All steps PASS. Round numbers refer to the 7 live rounds 2026-09-18..20; final verdict APPROVED BY EVIDENCE from the user's final-pass logs.

| # | Checklist item | Verdict | Round(s) & evidence |
|---|----------------|---------|---------------------|
| 1a | STACK + GEOMETRY: tail-follow train; rigid sweep; spacing pinned 3.60 Å | APPROVED | rounds 2-3 — dot=1.000000 d=3.6000 on every capture line in the DBG logs |
| 1b | RIGID TURN — wall-refusals gone: a turn toward the wall executes (head-only veto) | APPROVED | round 3 |
| 1c | Near-wall stacking works after REFUSE_WALL removal | APPROVED | round 6 — small-box win with wall-adjacent placements |
| 2 | Turn veto = 180-degree only; body/pickup silent-pass everywhere | APPROVED | rounds 3-4 — zero wrong refusals in 1000+ ticks of DBG logs |
| 3 | CRASH: head-wall crash ends run; snake stays complete; completion + Get Spectra activates | APPROVED | round 2 (crash); completion parity re-confirmed round 4 |
| 4 | SKIP: upload (no dataset entry) captured -> clean skip, run continues | APPROVED | round 4 (clean skip + edge-on rings); rounds 6/7 (demo-mode note + (xN) coalescing + skipped-Nx recap) |
| 5 | REFUSE demonstrator: biphenyl REFUSE_ATOM clash (1.87 Å) | APPROVED | rounds 3-7 — appears by design every window; pickup despawns/chain continues |
| 6 | WIN + COMPLETION: cap-10 on medium, smooth gameplay | APPROVED | round 3 (medium); rounds 6 + 7 on small — spectator-confirmed Spectra-tab switch on Get Spectra (round 4) |
| 7 | CRASH COMPLETION: same presentation, Get Spectra activates | APPROVED | round 2 crash run — identical completion path as win (locked decision 8, 05-15) |
| 8 | HYGIENE: no leftovers, no wildcard-riding, deterministic restart | APPROVED | rounds 3-4 — "new game after win is ok"; begin_game hard-clean (56dd68b) held |
| + | Upload-only demo mode (final-pass test 2) | APPROVED | round 7 — begin_game note displayed for zero-stackable set; recap reads "skipped 5x 931:" |

**Final build state at approval:** 640 unittests green; 7/7 required smokes green — smoke 08 STACK-PLACE flushes all 8 sentinels (EDGEON, PLACE360, PLANEPAR, SPAWNOFFS, HEADRESET, PICKUPS, SCENECLR, UPLEDGEON); smoke 02 informational FAIL is the known 01-05 offscreen dead end (non-blocking).

## Files Created/Modified

- `smoke/08_stack_place_smoke.py` — grew from 3 to 8 flushed sentinels across the window (added PLANEPAR, SPAWNOFFS, HEADRESET, PICKUPS, SCENECLR, UPLEDGEON for the parallel-plane pin, spawn offset, head reset, pickup lifecycle, scene cleanup, and upload-edge-on checks)
- `serpentrum/` engine/gui/bridge modules — checkpoint fixes enumerated above (train-follow, 180-only veto, wall-gate removal, cooldown spawn, upload skip parity, recap taxonomy, demo-mode note)
- `.planning/debug/resolved/05-ghost-point-turn-lock.md` — archived turn-lock debug session (8a17a74)
- `.planning/debug/resolved/05-lagging-tail-wall-box.md` — archived train-follow/head-only-walls/bigger-boxes session (af33de9)
- `.planning/debug/resolved/05-16-retest-fixes.md` — archived wall-gate removal + upload-path fixes session (3f89779)
- `.planning/debug/resolved/05-upload-only-endless-run.md` — archived upload-only endless-run session; resolution C1 (demo-mode note) + C4 (recap taxonomy) landed, C2 soft Start-warning left owner opt-in with seam documented (2bff573)

## Decisions Made

All seven behavior-shaping decisions were owner directives rendered live during the checkpoint (round dates 2026-09-18/19/20), then recorded in STATE.md Decisions and pinned by unit tests + smokes before the next round:

1. Train-follow tail replaces the stationary-tail model (chain translates rigidly each 'moved' tick).
2. Turn veto refuses ONLY 180-degree reversal; the planned sweep pre-check for body/pickup/boundary legs was deleted — non-reversal turns always execute (silent pass).
3. REFUSE_WALL placement gate removed; only the head is box-bound; REFUSE_ATOM clash remains the STACK-05 demonstrator (biphenyl 1.87 Å).
4. Box presets bumped twice, landing at small ±35 / medium ±55 / large ±85 (cap-10 winnability).
5. Pool exhaustion = 100-tick resumable cooldown (not permadeath); spawn demotion after refuse + refused-pickup despawn + ReasonCoalescer stop refuse cascades.
6. Upload data path: clean skip routing pre-geometry (no placement crash) + edge-on render parity + upload head parity.
7. Recap taxonomy (SKIP_* -> "skipped Nx" / REFUSE_* -> "refused Nx") and begin_game demo-mode note for zero-stackable sets (`hud_logic.stack_mode_note`).

## Deviations from Plan

This plan was a checkpoint plan, and the live checkpoint drove seven owner-directive behavior changes against which the final APPROVED verdict was rendered. The plan's must_haves therefore describe PRE-checkpoint behavior in seven places; the directives supersede them (lineage: STATE.md Decisions 2026-09-19/20):

1. **Sweep pre-check refusals (body/pickup/boundary legs)** — plan step 2 expected `turn refused: boundary` (or body/pickup) messages. Fully removed by owner directive (7659555): the turn veto refuses ONLY 180-degree reversal; everything else executes silently. The plan text is stale on this point.
2. **REFUSE_WALL placement gate** — plan step 3 implied boundary-leg refusals; placement had an additional wall gate. Removed by owner directive (d33f74c): only the head is box-bound; near-wall placements stack normally. REFUSE_ATOM clash kept as the STACK-05 demonstrator.
3. **Box preset values** — plan's "default medium box" assumed the original sizes. Bumped twice by owner directive (69b8fb0 → 98bf9f2) to small ±35 / medium ±55 / large ±85.
4. **Stationary tail model** — plan implied the head moves through a stationary chain. Replaced by train-follow rigid translation per 'moved' tick (76d74b3).
5. **Spawn policy** — plan assumed "the pickup stays visible and the run continues" on refuse. Changed by owner directive (f211d97, ee2a1d8): refused pickups despawn, spawns demote after refuse, and pool exhaustion is a 100-tick resumable cooldown (ReasonCoalescer dedupes HUD spam).
6. **Upload data path** — plan step 4's skip was the only upload handling. Extended by owner directive (93f4b2b/22b7245): clean skip routing pre-geometry (no placement crash) plus edge-on render parity and upload head parity.
7. **Recap taxonomy + demo-mode note** — not in the plan: SKIP_* recaps as "skipped Nx", REFUSE_* as "refused Nx" (e0b2814), and begin_game shows a demo-mode note for zero-stackable sets (64882c3).

Each deviation was diagnosed in a live round, fixed, pinned by unit tests and/or smoke sentinels, re-gated, and re-verified in a later round — the overrides ARE the replacement contract for the final verification.

## Issues Encountered

All resolved in-window (full narratives in the four `.planning/debug/resolved/` archives):

- Perpendicular-stack geometry bug (47eaba2): head ring not edge-on at game start — root cause `_reset_head_viewer` double-applied `edge_on_m16`; fixed via `pymol_bridge.reload_head`; pinned by the parallelism regression test b4b5b34 and smoke 08 PLANEPAR.
- Ghost-point turn-lock: unexplained turn refusals; instrumented with SRP_DEBUG and refusal WHY lines (0af3cde/cb02333), later mooted by the 180-only veto.
- Lagging tail + wall gates boxing the plane (round 2-3): tail dragged non-rigidly and sweep/boundary refusals deadlocked runs; superseded by train-follow + 180-only veto + wall-gate removal.
- Restart leftovers rode the `srp_*` wildcard (56dd68b): begin_game now hard-cleans all `srp_*` before materializing; pinned by smoke 08 SCENECLR.
- Pool-exhaustion permadeath deadlocked game 3 (ee2a1d8/6b3017a/415cf50): replaced with the 100-tick resumable cooldown.
- Upload captures crashed pre-skip and rendered flat (93f4b2b/22b7245): skip routing moved pre-geometry; uploads render edge-on with head parity; pinned by smoke 08 UPLEDGEON.
- Upload-only endless run (final open item): no-feedback loop for zero-stackable sets — resolved round 7 via demo-mode note (64882c3) + recap taxonomy (e0b2814); archive 2bff573.

## User Setup Required

None - no external service configuration required.

## Gate Results (final state at approval)

- `python3.6 tests/run_gates.py` — green; 640 unittests
- `python3.6 tests/run_gates.py --smoke` — 7/7 required smokes green via flushed SMOKE-OK sentinels (01 SKELETON, 03 VIEWER-BRIDGE, 04 DEMO-E2E, 05 LOOP-CAMERA, 06 INPUT-WIZARD, 07 TRANSFORM/SWEEP/COMPLETION, 08 STACK-PLACE); smoke 08 = 8/8 steps incl. UPLEDGEON and SCENECLR; smoke 02 informational non-blocking FAIL (known 01-05 dead end, never retries per plan lock)

## Next Phase Readiness

- **Phase 5 closes.** The complete v1 game is verified end-to-end (machine + human halves) and hands a complete snake forward: `last_run` anchor (counts, chain_objects, snake_id) for 06-xtb-pipeline; proven Get Spectra tab switch for 07-spectra-ui.
- **Phase 5.1 (GAME-11 speed tiers)** was inserted by the owner during the checkpoint (ef913f2) and is next; the approved train-follow/spacing/veto contract is its stable base.
- No open Phase-5 blockers. Known non-blocking item: smoke 02 informational FAIL (01-05 offscreen dead end — plan-locked, never retried). Owner opt-in seam left open: soft Start-warning for zero-stackable sets (C2, documented in `.planning/debug/resolved/05-upload-only-endless-run.md`).

---
*Phase: 05-stacking-game-rules*
*Completed: 2026-09-20*
