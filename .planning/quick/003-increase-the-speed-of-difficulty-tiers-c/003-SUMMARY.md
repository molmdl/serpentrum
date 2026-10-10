---
phase: quick-003
plan: 003
subsystem: game-speed
tags: [speed-tiers, difficulty, game-11, option-c, single-table-retune]
requires: ["5.1-02 SPEED_TIERS single-table architecture", "5.1-06 retune commit 4502143 (the exact precedent)", "GAME-11 (Phase 5.1, owner feel-check backdrop)"]
provides:
  - "Retuned difficulty ladder relaxed 6.0 / normal 9.0 (fresh-setup DEFAULT) / fast 11.0 / expert 13.0 A/s"
  - "DEFAULTS['speed'] = 9.0 (old expert becomes the new 'normal'); DEFAULTS follows the table's 'normal' entry"
  - "Accept-as-is relabel backcompat: old saved files load unchanged (6.0 -> 'relaxed'; 3.0/7.5 -> 'custom'; 9.0 -> 'normal')"
  - "GAME-11 ledger amendment (REQUIREMENTS.md bullet + traceability rows) recording the quick-003 owner retune, 5.1-06 history preserved"
affects: []
tech-stack:
  added: []
  patterns:
    - "Single-table data-only retune (5.1-02 architecture): EVERY runtime consumer derives from setup_logic.SPEED_TIERS (gui combo addItem loop, speed_tier_for, hud_logic.speed_note, randomize rng.choice) — a value change is edits to the ONE table plus coupled pins only; test_phase51_integration.py + tools/check_docs.py need ZERO edits by construction"
key-files:
  created:
    - ".planning/quick/003-increase-the-speed-of-difficulty-tiers-c/003-SUMMARY.md"
  modified:
    - "serpentrum/setup_logic.py"
    - "serpentrum/help_text.py"
    - "serpentrum/game_engine.py"
    - "serpentrum/gui_game.py"
    - "README.md"
    - "tests/test_setup_logic.py"
    - "tests/test_hud_content.py"
    - "tests/test_engine_speed.py"
    - "tests/test_docs_audit.py"
    - ".planning/REQUIREMENTS.md"
decisions:
  - "Owner-approved Option C ladder shipped verbatim: 6.0/9.0/11.0/13.0 (proposal lineage: option A repeated the 2026-09-25 shift pattern 6/9/10.5/12; option C keeps the 6.0 floor but scales the old top-gap ratios x1.25/x1.2 to the new normal for a bigger fast->expert jump)"
  - "game_engine.SPEED_A_PER_S stays 3.0 (the 5.1-06 decision unchanged): v1 baseline + kwarg fallback only; production always injects setup['speed']"
  - "Accept-as-is relabeling, zero migration, no SCHEMA_VERSION bump: the 'speed' key stays numeric; old files load and run at their saved speed with an honest tier name ('custom' where off-table)"
  - "Tier count, names, and order unchanged — exactly ('relaxed','normal','fast','expert'); mechanism byte-untouched (turn cadence, box presets, spawn policy)"
metrics:
  duration: "~20 min (single-pass autonomous; owner approval already granted at planning time)"
  completed: "2026-10-11"
---

# Quick Task 003: Increase the speed of difficulty tiers (Option C) — Summary

**One-liner:** The difficulty ladder shifts up one notch per the owner's 2026-10-11 directive — current expert 9.0 becomes the fresh-setup default 'normal' — shipping the owner-approved **Option C** table `relaxed 6.0 / normal 9.0 (DEFAULT) / fast 11.0 / expert 13.0 A/s` as a pure data-only retune of the ONE `setup_logic.SPEED_TIERS` table plus its coupled pins (tooltip, README, comment blocks, test pins, GAME-11 ledger), with every runtime surface (combo labels, HUD note, spawn seeds) deriving for free and all gates green first try.

## Owner directive & approval (verbatim)

- **Directive (owner, 2026-10-11):** "increase the speed of difficulty tiers. current expert should be normal / seek my approval after u propose the new tiers"
- **Approval (owner, planning time 2026-10-11, on the proposed ladder question):** **"Option C"**
  (question was "Approve the new speed tiers (current expert 9.0 becomes 'normal' in every option)"; option C keeps the 6.0 floor and scales the old top-gap ratios x1.25/x1.2 to the new normal — a bigger jump between fast and expert than the option-A repeat of the 2026-09-25 shift pattern.)
- **Final ladder shipped:** relaxed 6.0 / normal 9.0 (default) / fast 11.0 / expert 13.0 A/s — supersedes the 5.1-06 values (relaxed 3.0 / normal 6.0 / fast 7.5 / expert 9.0).

## What was delivered (commit 913fbd5, one atomic feat)

1. **The ONE data table + default** (`serpentrum/setup_logic.py`): `SPEED_TIERS` -> `(('relaxed', 6.0), ('normal', 9.0), ('fast', 11.0), ('expert', 13.0))`; `DEFAULTS['speed'] = 9.0` (old expert = the new fresh-setup 'normal'). The tier-history comment keeps the full 5.1-06 record as past-tense history (provenance never erased) and appends the quick-003 record (owner directive, option C, supersession, backcompat sentence).
2. **User-facing literals** (hand-synced, same commit by contract): `serpentrum/help_text.py` `SETUP_TOOLTIPS['speed_combo']` now reads "relaxed 6.0, normal 9.0 (default), fast 11.0, expert 13.0"; README.md canonical-values line now reads "speed tiers 6.0 / 9.0 (default) / 11.0 / 13.0 A/s" (rest of the line byte-identical — docs-audit numeric gate derives its expected tokens from the imported table + DEFAULTS and stays green).
3. **Comment blocks pinning the default tier** (`serpentrum/game_engine.py`, `serpentrum/gui_game.py`): values updated only ('normal' = 9.0 A/s since the quick-003 retune; 0.9 A/tick at dt 0.1). `SPEED_A_PER_S = 3.0` byte-untouched; both diffs are comment-only.
4. **Coupled test pins** (updated in the same commit — the visible reviewable diff the table comment promises):
   - `tests/test_setup_logic.py`: EXPECTED_DEFAULTS `'speed': 9.0`, the exact SPEED_TIERS tuple pin, tier-resolution pins (6.0->'relaxed', 9.0->'normal', 11.0->'fast', 13.0->'expert'), absent-key merge pin -> 9.0.
   - `tests/test_hud_content.py` TestSpeedNote: exact 'normal (9.0 A/s)' / 'fast (11.0 A/s)' / 'expert (13.0 A/s)' pins, trailing-decimal pin on relaxed 6.0, GAME-04 count-free loop list at the new values.
   - `tests/test_engine_speed.py`: tier exemplar re-framed `test_normal_tier_60` -> `test_normal_tier_90` (9.0 A/s -> 0.9 A/tick); docstrings/comments updated; arbitrary-value exemplars untouched.
   - `tests/test_docs_audit.py`: tamper test re-anchored to the `'9.0 (default)'` README token (tampered '5.0' makes the fixture differ AND the check fail).
5. **GAME-11 ledger amendment** (`.planning/REQUIREMENTS.md`, dated append — 5.1-06 record preserved): the bullet gains the quick-003 retune entry (directive + Option C + values + backcompat + "mechanism + 4-tier structure unchanged"); the traceability Evidence cell appends "quick-003 2026-10-11: owner-approved option C VALUES 6.0/9.0 (default)/11.0/13.0 A/s".

## Backcompat (accept-as-is, re-proven)

Old saved setup files load unchanged — zero migration, no schema bump, numeric key:

| Old saved speed | Loads as | Tier shown |
| --------------- | -------- | ---------- |
| 6.0 (old 'normal') | 6.0 | 'relaxed' — the value that tier now means |
| 9.0 (old 'expert') | 9.0 | 'normal' — exact-match relabel |
| 3.0 (old 'relaxed') / 7.5 (old 'fast') | unchanged | 'custom' — honest off-tier name |
| any other positive number (e.g. hand-tuned 3.1) | unchanged | 'custom' (accept-as-is rule intact) |

The two 'custom' relabels are now pinned explicitly in `test_off_tier_speed_is_custom` alongside the pre-5.1 draft values (2.0/4.5); `validate()` still accepts any speed > 0 (custom-speed case in `test_phase51_integration.py` green with ZERO edits).

## Verification

- **Default gate** (`python3.6 tests/run_gates.py`, repo root, before the commit): fully green — **gate printed `Ran 995 tests ... OK`** (exactly the plan's expected ~995; net-new = 0, pins only), gates 1-3 PASS (syntax+plugin-path safety, AST purity, scoped unittest discovery).
- **Smoke battery** (`python3.6 tests/run_gates.py --smoke`, generous timeout, Windows PyMOL via cmd.exe): **11/11 required smokes flushed their SMOKE-OK sentinels** — 01 SKELETON, 03 VIEWER-BRIDGE, 04 VIEWER-DEMO, 05 LOOP-CAMERA, 06 INPUT-WIZARD, 07 TRANSFORM, 08 EDGEON, 10 CHAIN-COUNT, 12 PLOT-RENDER, 13 MODE-ARROWS, **14 RELEASE-E2E** (the scripted win ran at the new default 9.0 A/s UNCHANGED — smoke files are value-agnostic by design); informational 02 FAIL non-blocking (known 01-05 dead end), 09/11 PASS. Verdict by flushed sentinels, never exit codes.
- **Headless spot-proof** (plan `<verification>` 3, pure python3.6, no Qt): final line **`QUICK003-SPOT-OK`** — pins table (6.0/9.0/11.0/13.0), DEFAULTS 9.0, all four tier resolutions, the 3.0/7.5 'custom' relabels, absent-key merge -> 9.0, the exact HUD note, all four tooltip tokens, and the README line.
- **Scope guard**: `git status` shows exactly the plan's 10 `files_modified`; `serpentrum/game_engine.py` + `serpentrum/gui_game.py` diffs are comment-only; `tests/test_phase51_integration.py`, `tools/check_docs.py`, `serpentrum/gui_setup.py`, `serpentrum/hud_logic.py`, `smoke/*` byte-untouched; nothing named `srp_*`; working tree clean after the feat commit.

## Deviations from Plan

1. **[Rule 1 — stale factual comment] `serpentrum/help_text.py` line ~78-79 facts comment.** The plan's edit list named only the `speed_combo` tooltip, but the comment block ABOVE `SETUP_TOOLTIPS` (introducing the 08-13 owner-inserted hover help) lists the baked-in facts as "speed tiers 3.0/6.0/7.5/9.0" and claims they mirror the setup_logic constants — factually stale after the retune and inside a files_modified file. Updated to "6.0/9.0/11.0/13.0" (verified unpinned by any test). No behavior change.
2. **[Rule 1 — comment arithmetic slip] `tests/test_setup_logic.py` off-tier comment.** The plan proposed the 3.1 comment become "3.1 sits between relaxed (6.0) and normal (9.0)" — but 3.1 < 6.0 sits BELOW every shipped tier, not between two of them. Shipped the truthful "3.1 sits below relaxed (6.0) — off-tier." No assert changed; the plan's asserts are all as written.

No bugs, blockers, authentication gates, or architectural decisions; everything else executed plan-verbatim (including the exact table, default, literals, comment sentences, pin values, and both commit messages).

## Commits

| Task | Commit | Message |
| ---- | ------ | ------- |
| plan | 242b83a | docs(quick-003): plan speed-tier retune option C (expert becomes normal) |
| 1 (retune) | 913fbd5 | feat(quick-003): shift speed tiers to 6/9/11/13 A/s (option C owner-approved) |
| docs | (this commit) | docs(quick-003): record speed-tier retune summary |

## Owner feel-check & future tweaks

The owner may feel-check the new speeds live in real PyMOL whenever they like (NOT a plan gate): fresh setup -> Speed combo shows the four new labels with 'normal (9.0 A/s)' selected; Start -> HUD logs "speed: normal (9.0 A/s) - steering cadence and turn time are unchanged" once; steering cadence and turn time are unchanged at every tier. **Any future tweak is the exact single-table procedure this task just ran a second time:** change `SPEED_TIERS` values (+ `DEFAULTS['speed']` if the default tier moves) in `serpentrum/setup_logic.py`, sync the tooltip literal + README tier tokens in the SAME commit, update the coupled pins (exact table pin, tier-resolution, HUD note, docs-audit tamper token, engine-exemplar), append a dated ledger line to GAME-11 — everything else derives for free.
