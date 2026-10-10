---
phase: quick-003
plan: 003
type: execute
wave: 1
depends_on: []
files_modified:
  - serpentrum/setup_logic.py
  - serpentrum/help_text.py
  - serpentrum/game_engine.py
  - serpentrum/gui_game.py
  - README.md
  - tests/test_setup_logic.py
  - tests/test_hud_content.py
  - tests/test_engine_speed.py
  - tests/test_docs_audit.py
  - .planning/REQUIREMENTS.md
autonomous: true

must_haves:
  truths:
    - "The Setup-tab speed combo lists exactly four tiers in owner-approved order - relaxed (6.0) / normal (9.0) / fast (11.0) / expert (13.0) - each labeled '<name> (<x.x> A/s)'"
    - "A fresh setup resolves to 'normal' at 9.0 A/s: DEFAULTS['speed'] == 9.0 and speed_tier_for(9.0) == 'normal'; begin_game logs 'speed: normal (9.0 A/s) - steering cadence and turn time are unchanged' once per run"
    - "Old setup files load unchanged at any positive speed (accept-as-is, zero migration, no schema bump): a saved speed 6.0 resolves to tier 'relaxed'; saved 3.0/7.5 resolve to 'custom'"
    - "User-facing numbers agree with the code table everywhere: the in-plugin speed tooltip, the README canonical-values line, and the HUD note all carry 6.0/9.0/11.0/13.0 (docs-audit numeric gate green)"
    - "Nothing else moves: turn cadence (6-tick sweeps), box presets, spawn policy, engine SPEED_A_PER_S = 3.0 fallback, and all GUI/runtime code are byte-untouched (comments and data literals only)"
  artifacts:
    - path: "serpentrum/setup_logic.py"
      provides: "SPEED_TIERS retuned + DEFAULTS['speed'] = the new 'normal' 9.0 + history comments (5.1-06 record kept, quick-003 supersession noted)"
      contains: "('expert', 13.0)"
    - path: "serpentrum/help_text.py"
      provides: "speed_combo tooltip listing the new tier values"
      contains: "expert 13.0"
    - path: "README.md"
      provides: "canonical-values line synced to the new tiers (docs-audit token contract: four '%.1f' tier tokens + '<default> (default)' token)"
      contains: "speed tiers 6.0 / 9.0 (default) / 11.0 / 13.0 A/s"
    - path: "tests/test_setup_logic.py"
      provides: "updated EXPECTED_DEFAULTS pin + exact SPEED_TIERS tuple pin + tier-resolution pins (incl. old 5.1-06 values as 'custom') + merge-backcompat pin"
      contains: "('relaxed', 6.0), ('normal', 9.0), ('fast', 11.0)"
    - path: "tests/test_hud_content.py"
      provides: "TestSpeedNote exact pins at the new values"
      contains: "speed: normal (9.0 A/s)"
    - path: "tests/test_engine_speed.py"
      provides: "tier-exemplar test re-framed to the new shipped 'normal' 9.0 (0.9 A/tick); docstrings updated; arbitrary-value exemplars untouched"
      contains: "speed_a_per_s=9.0"
    - path: "tests/test_docs_audit.py"
      provides: "README tamper test re-anchored to the new default token"
      contains: "'9.0 (default)'"
    - path: ".planning/REQUIREMENTS.md"
      provides: "dated quick-003 amendment appended to GAME-11's bullet and traceability row (values superseded; mechanism unchanged)"
      contains: "quick-003"
  key_links:
    - from: "serpentrum/setup_logic.py DEFAULTS['speed']"
      to: "serpentrum/setup_logic.py SPEED_TIERS 'normal' entry"
      via: "default always lands on a named tier - equality pinned by test_default_speed_is_a_tier_value + test_absent_speed_merges_to_default_and_validates_clean"
      pattern: "self\\.assertIn\\(DEFAULTS\\['speed'\\], tier_values\\)"
    - from: "README.md canonical-values line"
      to: "serpentrum/setup_logic.py SPEED_TIERS + DEFAULTS"
      via: "tools/check_docs.expected_numeric_context imports the table as num-truth; missing token fails the default gate"
      pattern: "speed tiers 6\\.0 / 9\\.0 \\(default\\) / 11\\.0 / 13\\.0 A/s"
    - from: "serpentrum/help_text.py SETUP_TOOLTIPS['speed_combo']"
      to: "serpentrum/setup_logic.py SPEED_TIERS"
      via: "hand-synced literal (no framework) - MUST change in the SAME commit as the table"
      pattern: "relaxed 6\\.0, normal 9\\.0 \\(default\\), fast 11\\.0, expert 13\\.0"
    - from: "gui combo / HUD speed note / Randomize tier pick"
      to: "serpentrum/setup_logic.py SPEED_TIERS"
      via: "runtime derivation (addItem loop, speed_tier_for, rng.choice over tier values) - ZERO code edits by design (5.1-02 architecture); test_phase51_integration.py derives expectations and needs ZERO edits"
      pattern: "for name, aps in setup_logic\\.SPEED_TIERS"
---

<objective>
Retune the game's difficulty ladder up: the owner's 2026-10-11 directive "increase the speed of difficulty tiers. current expert should be normal", owner-approved at planning time as **Option C**:

  relaxed 6.0 / normal 9.0 (DEFAULT) / fast 11.0 / expert 13.0 A/s

superseding the 2026-09-25 (5.1-06) values relaxed 3.0 / normal 6.0 / fast 7.5 / expert 9.0.

Purpose: the second owner-directed speed correction (the 2026-09-25 feel-check already rejected all slower drafts as "only expert feel like playing"); at the new ladder the old expert 9.0 becomes the default 'normal' tier. The exact precedent is the 5.1-06 retune commit 4502143: value tweaks are data-only edits to the ONE table (`setup_logic.SPEED_TIERS`) plus its pin surface; tier count, names, order, and the whole mechanism are unchanged; `game_engine.SPEED_A_PER_S` stays 3.0 as the v1 baseline + kwarg fallback only.

Output: one atomic retune commit touching the table, the fresh-setup default, the user-facing numbers (tooltip + README), the comment blocks that pin the default tier, the coupled test pins, and the GAME-11 ledger amendment - with the full default gate + required-smoke battery green.
</objective>

<execution_context>
@~/.config/opencode/get-shit-done/workflows/execute-plan.md
@~/.config/opencode/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@serpentrum/setup_logic.py
@serpentrum/help_text.py
@README.md
@tests/test_setup_logic.py
@tests/test_hud_content.py
@tests/test_engine_speed.py
@tests/test_docs_audit.py

Owner approval (planning time, 2026-10-11, recorded verbatim): question "Approve the new speed tiers (current expert 9.0 becomes 'normal' in every option)" -> answer **"Option C"**. Proposal lineage: option A was the exact repeat of the 2026-09-25 shift pattern (6.0/9.0/10.5/12.0); option C (CHOSEN) keeps the 6.0 floor but scales the old top-gap ratios (x1.25, x1.2) to the new normal for a bigger jump between fast and expert.

Anchor facts (probed by the planner 2026-10-11; line numbers approximate - always find by the quoted text):
- ONE data table: `serpentrum/setup_logic.py` `SPEED_TIERS = (('relaxed', 3.0), ('normal', 6.0), ('fast', 7.5), ('expert', 9.0))` (lines ~136-141); `DEFAULTS['speed'] = 6.0` (line ~68). Runtime consumers ALL derive: gui_setup combo (`addItem('%s (%.1f A/s)' ...)`), `speed_tier_for`, `hud_logic.speed_note`, `randomize_setup` (`rng.choice` over tier values). ZERO code edits anywhere - values only.
- Docs-truth gate: `tools/check_docs.py` imports SPEED_TIERS + DEFAULTS and builds expected README tokens: `'%.1f' % value` for each tier + `'%.1f (default)' % DEFAULTS['speed']`. README.md line ~39 currently reads "speed tiers 3.0 / 6.0 (default) / 7.5 / 9.0 A/s". `tests/test_docs_audit.py::TestNumericClaims` - live README must PASS and `test_tampered_speed_tier_fails` tampers `'6.0 (default)'` -> `'5.0 (default)'` and asserts the tampered README FAILS.
- Hardcoded-value pins (must move with the table, SAME commit): `tests/test_setup_logic.py` (EXPECTED_DEFAULTS `'speed': 6.0` line ~59; exact tuple pin ~374-378; `merged['speed'] == 6.0` ~409; tier-resolution pins ~434-437), `tests/test_hud_content.py` (TestSpeedNote exact pins ~757-795 incl. the per-tier GAME-04 loop), `tests/test_engine_speed.py` (module docstring case 2 ~11-14, class docstring ~88-91, `test_normal_tier_60` ~101-106 framed "6.0 is the shipped 'normal' tier (5.1-06 retune)"), `serpentrum/help_text.py` (`speed_combo` tooltip ~117-118) and `README.md`.
- Comment blocks that pin the default tier (5.1-06 fixed these in the same commit as the retune - same discipline): `serpentrum/game_engine.py` ~74-79 ("the setup-side default tier is 'normal' = 6.0 A/s in setup_logic.SPEED_TIERS since the 5.1-06 owner retune") and `serpentrum/gui_game.py` ~93-99 ("at the default 'normal' tier (6.0 A/s after the 5.1-06 owner retune) that is 0.6 A/tick, while the engine's kwarg fallback (SPEED_A_PER_S = 3.0) would give 0.3").
- ZERO-edit surfaces (verification by NOT touching - a failure in any of these means an assumption is wrong: STOP and investigate, never band-aid): `tests/test_phase51_integration.py` (all expectations DERIVED from SPEED_TIERS/DEFAULTS - 5.1-06 proved zero edits on retune), `tools/check_docs.py`, `serpentrum/gui_setup.py`, `serpentrum/hud_logic.py`, `serpentrum/game_engine.py` code (comment only), all smoke files (smoke 14 consumes `setup['speed']` dynamically; its scripted win is speed-agnostic by construction: pickups sit ON the head path, tick cap 1000), `tests/test_engine_core.py` / `test_engine_rules.py` / `test_engine_win_desync.py` (they pin `SPEED_A_PER_S = 3.0`, which STAYS 3.0), `tests/test_spawn.py` (seed tests are value-agnostic), `tests/test_help_text.py` (pins the SETUP_TOOLTIPS KEY-SET + ASCII, not the value sentence).
- game_engine.SPEED_A_PER_S STAYS 3.0 - the 5.1-06 decision: "stays 3.0 as kwarg fallback + test pin (production always injects setup['speed'])".
- Expected default gate size: ~995 tests (quick-002 battery: 995 unittests + 11/11 required smokes; this retune updates pins only, net-new = 0). The gate prints the exact count - report it.
- Backcompat (accept-as-is rule, unchanged): `validate()` accepts any number > 0; the tier combo is the UI constraint, not the schema. Old saved files: 6.0 -> 'relaxed', 3.0/7.5 -> 'custom', 9.0 -> 'normal' via `speed_tier_for` exact match.
- Ledger precedent: GAME-11's bullet + traceability row in `.planning/REQUIREMENTS.md` already record the 5.1-06 owner amendment in-line; APPEND the quick-003 amendment the same way (dated, do not rewrite the 5.1-06 record).

HARD CONSTRAINTS (violating any fails the task):
- Start from a clean tree (`git status`). Work from the repo root in WSL. Single-plan wave: commit directly on main (NO worktree).
- python3.6 syntax, %-formatting ONLY (no f-strings), ASCII 'A/s' house style in every user-visible string. help_text stays ASCII-clean.
- Tier count/names/order UNCHANGED: exactly ('relaxed', 'normal', 'fast', 'expert') in that order. Values only: 6.0 / 9.0 / 11.0 / 13.0.
- Gates before the code commit, from the repo root: `python3.6 tests/run_gates.py` fully green AND `python3.6 tests/run_gates.py --smoke` all required smokes flush their SMOKE-OK sentinels (verdict = flushed sentinels, NEVER exit codes).
- Do NOT modify ANY file outside files_modified. In particular: ROADMAP.md, STATE.md (orchestrator-owned), smoke/*, tools/check_docs.py, tests/test_phase51_integration.py, serpentrum/gui_setup.py, serpentrum/hud_logic.py. Nothing named srp_*, no viewer work, no GUI behavior change (labels derive at runtime).
- Comments: APPEND the quick-003 record to the 5.1-06 history; never erase the 2026-09-25 provenance (values superseded, mechanism contract unchanged).
- Commit style: Conventional Commits, scope quick-003. One atomic feat commit for the retune; then the summary as its own docs commit.
</context>

<tasks>

<task type="auto">
  <name>Task 1: Retune SPEED_TIERS to 6.0/9.0/11.0/13.0 (Option C) - table, default, user-facing numbers, comment blocks, coupled pins, GAME-11 ledger</name>
  <files>serpentrum/setup_logic.py, serpentrum/help_text.py, serpentrum/game_engine.py, serpentrum/gui_game.py, README.md, tests/test_setup_logic.py, tests/test_hud_content.py, tests/test_engine_speed.py, tests/test_docs_audit.py, .planning/REQUIREMENTS.md</files>
  <action>
All edits are value literals, comments, or pin updates - zero logic changes. Find each site by the quoted text (line numbers approximate).

1. serpentrum/setup_logic.py (the ONE data table + the default):
   a. DEFAULTS entry (~line 68) becomes:

      'speed': 9.0,                  # A/s = the 'normal' tier (quick-003
                                     # owner retune 2026-10-11, option C:
                                     # 'increase the speed of difficulty
                                     # tiers - current expert should be
                                     # normal'; supersedes the 5.1-06
                                     # value 6.0; game_engine's
                                     # SPEED_A_PER_S stays 3.0 as the v1
                                     # baseline + kwarg fallback only)

   b. The tier-history comment block (~lines 121-135): KEEP the 5.1-06 history sentences, then reframe. The operative lines become (keep the existing history, adjust the framing):

      - "OWNER-FINALIZED at the 5.1-06 feel-check (2026-09-25): the drafts (2.0/3.0/4.5/6.0) all played too slow ... so the scale shifted up" -> keep as history, but the sentence "relaxed 3.0 ... and normal 6.0 ... are FINAL; fast 7.5 / expert 9.0 are the owner's 'try' values" becomes past-tense history (no longer FINAL).
      - ADD: "quick-003 (2026-10-11, owner-approved option C): the ladder shifted up once more per the owner directive - relaxed 6.0 (= the old 'normal') / normal 9.0 (= the old 'expert'; DEFAULTS['speed'] follows) / fast 11.0 / expert 13.0 (the old top-gap ratios x1.25/x1.2 scaled to the new normal, rounded to whole A/s). Tier count, names, and order unchanged."
      - Keep the tuple-ordering + SINGLE-source sentences verbatim, and update the schema sentence: "The schema key 'speed' STAYS numeric (DEFAULTS['speed'] = 9.0 = 'normal'): backcompat is free (every setup file ever written already carries it; pre-retune values load as-is - 6.0 resolves to 'relaxed', 3.0/7.5 to 'custom') and no SCHEMA_VERSION bump is needed."

   c. SPEED_TIERS itself:

      SPEED_TIERS = (
          ('relaxed', 6.0),
          ('normal', 9.0),
          ('fast', 11.0),
          ('expert', 13.0),
      )

   d. Leave `speed_tier_for` docstring as-is (its "hand-tuned 3.1 is honestly 'custom'" example is value-agnostic).

2. serpentrum/help_text.py (~lines 117-118), SETUP_TOOLTIPS['speed_combo'] becomes:

       'Head speed in A/s: relaxed 6.0, normal 9.0 (default), fast '
       '11.0, expert 13.0. The speed stays constant within a run.'),

3. README.md canonical-values sentence (line ~39): replace "speed tiers 3.0 / 6.0 (default) / 7.5 / 9.0 A/s" with "speed tiers 6.0 / 9.0 (default) / 11.0 / 13.0 A/s" - keep everything else on that line byte-identical (box presets 35 / 55 / 85, win cap, atom budget, broadening 8.0 cm-1, xtb threads, the hessian sentence).

4. serpentrum/game_engine.py comment block (~lines 74-79): the sentence "the setup-side default tier is 'normal' = 6.0 A/s in setup_logic.SPEED_TIERS since the 5.1-06 owner retune; production always injects it via the kwarg" becomes "the setup-side default tier is 'normal' = 9.0 A/s in setup_logic.SPEED_TIERS since the quick-003 owner retune (2026-10-11); production always injects it via the kwarg". SPEED_A_PER_S = 3.0 STAYS.

5. serpentrum/gui_game.py comment block (~lines 93-99): "at the default 'normal' tier (6.0 A/s after the 5.1-06 owner retune) that is 0.6 A/tick" becomes "at the default 'normal' tier (9.0 A/s after the quick-003 owner retune, 2026-10-11) that is 0.9 A/tick" - keep the cadence-vs-distance framing and the "SPEED_TIERS in setup_logic (data-only edits)" pointer verbatim.

6. tests/test_setup_logic.py (coupled pins - update values + provenance comments):
   a. Module docstring (~line 15): reframe "owner-finalized default (5.1-06 feel-check 2026-09-25: speed 6.0 = the ... 'normal' tier ...)" to the quick-003 record: owner-approved 2026-10-11, speed 9.0 = the 'normal' tier (5.1-06's 6.0 superseded).
   b. EXPECTED_DEFAULTS (~line 59): `'speed': 6.0,` -> `'speed': 9.0,` with a short comment: "# Owner-approved quick-003 retune (2026-10-11): 'normal' tier; was 6.0."
   c. TestSpeedTierTable docstring + exact pin (~lines 367-378): docstring records the option-C ladder (6.0/9.0/11.0/13.0, owner-approved quick-003 2026-10-11; supersedes 5.1-06's 3.0/6.0/7.5/9.0); pin becomes:

          self.assertEqual(
              SPEED_TIERS,
              (('relaxed', 6.0), ('normal', 9.0), ('fast', 11.0),
               ('expert', 13.0)))

   d. test_default_speed_is_a_tier_value comment (~381-382): "The numeric default (9.0) IS one of the tier values ... ('normal')" - comment updated to the quick-003 default.
   e. test_absent_speed_merges_to_default_and_validates_clean (~404-410): `self.assertEqual(merged['speed'], 6.0)` -> `9.0`; comment "(9.0 = 'normal' since the quick-003 retune)".
   f. TestSpeedTierFor.test_exact_tier_values_resolve_to_names (~432-437): becomes 6.0->'relaxed', 9.0->'normal', 11.0->'fast', 13.0->'expert' (update the table-provenance comment).
   g. test_off_tier_speed_is_custom (~439-445): keep `speed_tier_for(3.1), 'custom'` (comment becomes "3.1 sits between relaxed (6.0) and normal (9.0) - off-tier"); keep the 2.0/4.5 asserts with their comment ("the pre-5.1 draft values are now off-tier too" - still true); ADD two asserts documenting the relabel backcompat honestly:

          # quick-003: the 5.1-06 final values are off-tier after the
          # retune - an old saved file at these speeds shows 'custom'
          # (accept-as-is; the numeric value still loads and runs).
          self.assertEqual(speed_tier_for(3.0), 'custom')
          self.assertEqual(speed_tier_for(7.5), 'custom')

7. tests/test_hud_content.py TestSpeedNote (~lines 757-795):
   a. test_normal_tier_exact: comment "Owner-approved values (quick-003, 2026-10-11): normal = 9.0."; pin:
      `hud_logic.speed_note('normal', 9.0)` == `'speed: normal (9.0 A/s)' + self.SUFFIX`
   b. test_fast_and_expert_tiers_exact: pins become fast 11.0 -> 'speed: fast (11.0 A/s)' and expert 13.0 -> 'speed: expert (13.0 A/s)' (keep the one-decimal comment).
   c. test_custom_speed_surfaces_honestly (3.2): UNCHANGED.
   d. test_trailing_decimal_always_rendered: use `hud_logic.speed_note('relaxed', 6.0)` asserting `'(6.0 A/s)'` in line and `'(6 A/s)'` not in line (comment: the relaxed tier's round value is 6.0 post quick-003).
   e. test_count_free_game_04_guard loop list: [('relaxed', 6.0), ('normal', 9.0), ('fast', 11.0), ('expert', 13.0), ('custom', 3.2)].
   f. Do NOT touch speed_note's one-call-site pin or any other class.

8. tests/test_engine_speed.py (comments + the one tier-named exemplar; arbitrary exemplars stay):
   a. Module docstring case 2 (~lines 11-14): "speed 2.0 -> 0.2 A/tick, 9.0 -> 0.9 A/tick ... (heading 'up' with 6.0 -> (0.0, 0.6), never hardcoded +x). 9.0 is also the shipped 'normal' tier after the quick-003 owner retune (2026-10-11)."
   b. TestPerTierDisplacement class docstring (~88-91): "(owner-approved quick-003: 6.0/9.0/11.0/13.0) and the engine never reads it."
   c. test_arbitrary_slow_speed_20 comment (~94): "2.0 A/s: below every shipped tier after the quick-003 retune - still a legal kwarg value".
   d. test_normal_tier_60 -> rename test_normal_tier_90; body: `GameEngine(speed_a_per_s=9.0, **ENGINE_ARGS)`; expect `events[0][1][0] == 0.9` (delta 1e-9), y 0.0; comment "# 9.0 A/s is the shipped 'normal' tier (quick-003 retune)."
   e. test_movement_follows_heading_not_hardcoded_x (uses 6.0 arbitrary) + TestTrainFollowParity (6.0 -> 0.6) + the reset/attribute-echo tests (4.5, 6.0) + the seed-coupling tests (2.0/4.5) + case-1/7 module pins (SPEED_A_PER_S = 3.0): ALL UNCHANGED - their values are arbitrary legal speeds, not tier claims.

9. tests/test_docs_audit.py test_tampered_speed_tier_fails (~lines 127-131):

       fixture = self.readme.replace('9.0 (default)', '5.0 (default)')

   (the tamper must make the fixture differ AND make check_numeric fail - with the new README the token '9.0 (default)' goes missing and the tampered tier '5.0' is no tier value).

10. .planning/REQUIREMENTS.md - APPEND the quick-003 amendment (do not rewrite the existing 5.1-06 text; this file is a running ledger - amend in place with dated additions like the 5.1-06 amendment itself did):
    a. GAME-11 bullet (line ~37): append at the end of the bullet:

       " - **quick-003 retune (owner-approved 2026-10-11)**: directive 'increase the speed of difficulty tiers; current expert should be normal' (Option C): relaxed 6.0 / normal 9.0 (default) / fast 11.0 / expert 13.0 A/s; DEFAULTS['speed'] 9.0; 6.0 survives as 'relaxed'; the engine kwarg fallback stays 3.0; old saved files load as-is (accept-as-is tier relabeling); mechanism + 4-tier structure unchanged"

    b. GAME-11 traceability row (line ~145): append inside the Evidence cell: "; quick-003 2026-10-11: owner-approved option C VALUES 6.0/9.0 (default)/11.0/13.0 A/s"

11. Run the gates from the repo root: `python3.6 tests/run_gates.py` (expect ~995 tests green, exact count printed by the gate) and `python3.6 tests/run_gates.py --smoke` (all required smokes flush SMOKE-OK; smoke 14 RELEASE-E2E runs its scripted win at the new default speed and must pass UNCHANGED - never edit smokes for values).

12. ONE atomic commit with everything above:

       feat(quick-003): shift speed tiers to 6/9/11/13 A/s (option C owner-approved)

13. Then create the summary at .planning/quick/003-increase-the-speed-of-difficulty-tiers-c/003-SUMMARY.md (house template) and commit it as:

       docs(quick-003): record speed-tier retune summary

    The summary MUST record: the owner directive verbatim, the approval verbatim ("Option C" on the proposed ladder question), the final table 6.0/9.0/11.0/13.0, the relabeling backcompat (6.0->'relaxed', 3.0/7.5->'custom'), the gate + smoke counts/verdicts, and that the owner may feel-check live whenever they like (future tweaks = this exact single-table procedure).
  </action>
  <verify>
1. `python3.6 tests/run_gates.py` from repo root - fully green (expect ~995; report the gate's printed count).
2. `python3.6 tests/run_gates.py --smoke` - all required smokes flush SMOKE-OK sentinels (verdict = flushed sentinels, NEVER exit codes).
3. Headless spot-proof (pure, repo root, python3.6 - no Qt):

   python3.6 -c "
   import sys; sys.path.insert(0, '.')
   from serpentrum import setup_logic as sl, help_text, hud_logic
   assert sl.SPEED_TIERS == (('relaxed', 6.0), ('normal', 9.0),
                             ('fast', 11.0), ('expert', 13.0))
   assert sl.DEFAULTS['speed'] == 9.0
   assert sl.speed_tier_for(9.0) == 'normal'
   assert sl.speed_tier_for(6.0) == 'relaxed'
   assert sl.speed_tier_for(11.0) == 'fast'
   assert sl.speed_tier_for(13.0) == 'expert'
   assert sl.speed_tier_for(3.0) == 'custom'
   assert sl.speed_tier_for(7.5) == 'custom'
   assert sl.merge_defaults({'schema_version': 1})['speed'] == 9.0
   assert hud_logic.speed_note('normal', 9.0) == (
       'speed: normal (9.0 A/s) - steering cadence'
       ' and turn time are unchanged')
   tip = help_text.SETUP_TOOLTIPS['speed_combo']
   for tok in ('relaxed 6.0', 'normal 9.0 (default)', 'fast 11.0',
               'expert 13.0'):
       assert tok in tip, tok
   readme = open('README.md').read()
   assert 'speed tiers 6.0 / 9.0 (default) / 11.0 / 13.0 A/s' in readme
   print('QUICK003-SPOT-OK')
   "

   (expected final line: QUICK003-SPOT-OK)
4. `git status` clean-scoped: only this plan's files_modified were touched. `git log --oneline -3` shows the feat(quick-003) retune commit + the docs(quick-003) summary commit.
5. Backcompat spot: run the existing battery leg proving a hand-tuned speed still merges/validates (test_phase51_integration.py custom-speed case + test_setup_logic off-tier cases are in the default gate) - ZERO edits to those files.
  </verify>
  <done>The four shipped tiers read relaxed 6.0 / normal 9.0 (fresh-setup default; HUD logs 'speed: normal (9.0 A/s) - steering cadence and turn time are unchanged' once per run) / fast 11.0 / expert 13.0; tooltip + README carry the same numbers (docs-audit gate green); old saved setups load as-is with honest tier relabeling; SPEED_A_PER_S stays 3.0; tier count/names/order and every mechanism byte-unchanged; default gate + full smoke battery green; one atomic feat(quick-003) commit + the summary commit landed.</done>
  Commit: `feat(quick-003): shift speed tiers to 6/9/11/13 A/s (option C owner-approved)`
</task>

</tasks>

<verification>
1. Default gate green (python3.6 tests/run_gates.py, ~995 tests) + required-smoke battery green (python3.6 tests/run_gates.py --smoke, all SMOKE-OK sentinels) - both from the repo root, before the feat commit.
2. QUICK003-SPOT-OK spot-proof passes (table + default + tier resolution + relabeling backcompat + HUD note + tooltip + README in one pure run).
3. git diff confirmation: NO file outside files_modified was touched; tests/test_phase51_integration.py, tools/check_docs.py, smoke/*, serpentrum/gui_setup.py, serpentrum/hud_logic.py byte-identical; game_engine.py/gui_game.py comment-only (SPEED_A_PER_S = 3.0 intact).
4. Owner-visible behavior (for the owner's optional live sanity pass, NOT a plan gate): Setup tab -> Speed combo shows the four new A/s labels with 'normal (9.0 A/s)' selected on a fresh setup; Start -> HUD logs the new speed line once; steering cadence/turn time unchanged.
</verification>

<success_criteria>
- Owner-approved Option C ladder shipped: relaxed 6.0 / normal 9.0 (DEFAULT) / fast 11.0 / expert 13.0 A/s - single-table edit + coupled pins, in ONE atomic feat(quick-003) commit preceded by green default gate, with the smoke battery green before summary finalization.
- DEFAULTS['speed'] = 9.0 (fresh setups + merge_defaults backcompat land on 'normal'); old files load unchanged (6.0->'relaxed', 3.0/7.5->'custom' - accept-as-is).
- All user-facing surfaces agree: Setup combo labels (derived), HUD note (derived), in-plugin tooltip (literal), README canonical line (docs-audit token contract).
- Mechanism byte-untouched: 4 tiers, same names/order; engine fallback 3.0; turn cadence; box presets; spawn policy; zero logic edits anywhere.
- GAME-11 ledger amended (dated append, 5.1-06 history preserved); summary records the owner directive + approval verbatim.
</success_criteria>

<output>
After completion, create `.planning/quick/003-increase-the-speed-of-difficulty-tiers-c/003-SUMMARY.md` (owner directive + "Option C" approval verbatim; final ladder; relabeling backcompat; gate/smoke counts; the single-table future-tweak procedure pointer).
</output>
