# HANDOFF — Phase 5 checkpoint resume (2026-09-20)

**Read this file + `.planning/STATE.md` at session start, in any fresh context window, to continue.**

## Where things stand

Phase 5 (Stacking & Game Rules Complete): **16/16 plans executed** (05-01..05-16), machine verification green (`05-VERIFICATION.md`, 15/15 plans, zero gaps), and the 05-16 human checkpoint (Task 2) is in its **final pass** — one open design item remains, logged to a debug session.

### Checkpoint test history (all preserved in STATE.md Decisions)

| Round | Result |
|-------|--------|
| Rounds 1–2 (2026-09-19) | Steps 1–3 APPROVED (tail-follow, rigid turn, no wall refusals); then 4 gameplay fixes landed (turn veto = 180° only `7659555`, refuse despawn + spawn demotion `f211d97`, restart hygiene `56dd68b`, presets ±35/±55/±85 `98bf9f2`) |
| Round 3 (2026-09-19) | Cap-10 WIN on medium ✓ (smooth), small-box crash ✓, clean restart ✓; near-wall deadlock found → pool-exhaustion permadeath replaced with 100-tick cooldown (`ee2a1d8`) |
| Round 4 (2026-09-20) | Get Spectra ✓ PASS; owner directive: REFUSE_WALL placement gate REMOVED (`d33f74c` — chain may extend out of box, only head is box-bound, clash gate REFUSE_ATOM kept as STACK-05 demonstrator); upload path fixed: clean skip routing + edge-on uploads (`93f4b2b`, `22b7245`) |
| Final pass (2026-09-20) | Small-box WIN ✓ near-wall stacking works; upload run skips cleanly ✓; **open**: upload-ONLY runs are endless (no stacking possible → no win condition) → logged as `.planning/debug/05-upload-only-endless-run.md` |

**Biphenyl "refuse" is expected, forever:** REFUSE_ATOM clash (1.87 Å) — orthogonal rings always clash; designed STACK-05 chemistry demonstrator. Owner briefed and accepted 2026-09-20. Do not "fix" it.

### Build state

630 unittests green, 7/7 required smokes green (smoke 08: 8/8 steps incl. UPLEDGEON, SCENECLR), last commits `3f89779` (fix docs) + `25ee1e8` (state) + this session's docs commit. All behavior constraints and owner directives are in STATE.md Decisions (2026-09-19/20 entries).

## What's queued (recommended order)

1. **Dedicated debug session** — run `/gsd-debug` on `.planning/debug/05-upload-only-endless-run.md`. Contains candidates C1–C4; **owner decision required** (probably begin_game explanation line and/or setup-side guard; generic upload stacking is OUT — v2 STACK-06 territory, repo rule: no invented chemistry). Implement the resolution; gates + smokes.
2. **Plan + execute Phase 5.1 (INSERTED)** — Game Speed / Difficulty (GAME-11). ROADMAP entry + success criteria already written; draft tiers relaxed ≈ 2.0 / normal 3.0 (default) / fast ≈ 4.5 / expert ≈ 6.0 Å/s, owner approves final values at the feel-check checkpoint. Start with `/gsd-discuss-phase 5.1` or `/gsd-plan-phase 5.1`.
3. **Resume the 05-16 checkpoint** — fresh Windows PyMOL with `set SRP_DEBUG=1` in the shell first; confirm game(s) covering whatever changed in steps 1–2 (a win on any box + one glance at the upload behavior if the debug fix touched it).
4. **On "approved"** — spawn a continuation agent: write `05-16-SUMMARY.md` (per-step verdicts across all rounds), then gsd-verifier re-run (final 05-VERIFICATION), then phase wrap-up commit (`docs(05)`): ROADMAP Phase-5 row → Complete; REQUIREMENTS GAME-04/05/06/09/10 + STACK-01/03/04/05 → Complete (**note on GAME-10**: the 05-16 owner overrides are the replacement contract — 180°-only turn veto, REFUSE_WALL removed — REQUIREMENTS footer already carries the note).
5. **Then**: Phase 6 (xtb Pipeline — depends only on Phase 2, parallel-track candidate) or Phase 7.

## Standing rules (non-negotiable in any continuation)

- Repo root `/mnt/c/Users/nglok/Desktop/WORKDIR/molmdl/serpentrum` only; python3.6 (no f-strings); never pip/apt/conda.
- Gates per commit: `python3.6 tests/run_gates.py`; + `--smoke` when bridge/GUI/smoke touched (verdict = SMOKE-OK sentinels; smoke 02 informational FAIL known).
- Conventional commits scoped `(05)` / `(5.1)`; stage files individually; STATE.md/ROADMAP.md are orchestrator-owned (agents must not edit).
- Planning-doc dates UTC; SRP_DEBUG=1 set in the Windows shell BEFORE launching PyMOL.
- Dataset `serpentrum/data/stacking_pi_stack.json` (3.60 Å @ 20°) is human-approved and immutable.
