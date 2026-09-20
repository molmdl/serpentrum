---
status: resolved
trigger: "upload: can play just no stacking at all (endless)"
created: 2026-09-20T16:08:00Z
updated: 2026-09-21T00:00:00Z
---

## Current Focus

RESOLVED 2026-09-21. C1 + C4 implemented, pinned, gates green (640 unittests; 7/7 required smoke sentinels; smoke 02 informational FAIL known/ok). C2 evaluated: soft warning proposable (seam documented below), hard block REJECTED. C5 cosmetic glue: no code bug (verified by construction).

## Symptoms

expected: an upload-only game is playable-or-blocked in a way that is understandable (user knows WHY nothing can stack and what the end condition is)
actual: upload-only run plays smoothly but can never win — every capture skips cleanly (`skipped 931: no verified stacking entry for this molecule (no invented chemistry) (x2)`), stacked stays 0 forever, run only ends when the user crashes on purpose; end recap prints `refused 7x 931: no verified stacking entry...`
errors: none (the fix in 93f4b2b/22b7245 works — clean skip, no exception, coalescer active, edge-on upload rendering landed)
reproduction: Setup -> upload a set of SDFs only (e.g. accept_naphthalene.sdf / CID 931) -> Start -> eat pickups; nothing ever stacks
started: 2026-09-20, final 05-16 checkpoint confirmation round (upload game test)

## Eliminated

- NOT A BUG — biphenyl refuse in demo games: `skipped Biphenyl: placement clashes (1.87 A)` is REFUSE_ATOM, the STACK-05 clash gate. Biphenyl's two rings are orthogonal, so its placed second ring always clashes with the previous slab. This is the designed chemistry demonstrator (a clashing append would make xtb infer covalent bonds). REFUSE_WALL was removed by owner directive (d33f74c); REFUSE_ATOM stays deliberately. Owner briefed 2026-09-20, accepted.
- NOT A BUG — edge-on upload rendering + clean skip: both landed and live-verified in this same test round (93f4b2b, 22b7245); skip lines appear with (xN) coalescing, zero `placement error` spam.

## Evidence

- timestamp: 2026-09-20
  checked: live upload-only game, full SRP_DEBUG log captured by user
  found: 7 captures of CID 931 (naphthalene upload), all `skipped ... no verified stacking entry ... (x2)`; run ended only by deliberate boundary crash at tick 252; recap: `score: 0`, `atoms: 0 (spectra input size)`, `refused 7x 931: ...`
  implication: skip path is fully functional live; the gap is DESIGN: a set with zero stackable species yields an endless run with no feedback about why winning is impossible.

- timestamp: 2026-09-20
  checked: taxonomy wording in end-of-run recap (hud_logic end-summary)
  found: skips surface under the label `refused 7x 931: no verified stacking entry` — SKIP_NO_ENTRY is not a placement refuse; wording blurs skip vs refuse taxonomy (cosmetic, but confusing after the ReasonCoalescer already says `skipped`).

- timestamp: 2026-09-20
  checked: console copy formatting
  found: coalesced `(x2)` rewrite glued to the preceding DBG line in the user's paste (`delta=+90.0000skipped 931: ...`) — likely ReasonCoalescer QTextCursor rewrite not emitting a leading newline in some paths; cosmetic; verify in HUD, not console.

- timestamp: 2026-09-21
  checked: gui_game.begin_game / _build_engine / the info-box log seams for the C1 candidate
  found: begin_game collects `records` from the anchor (same list feeding the spawner), builds the engine via _build_engine, then logs ONLY 'Get ready...' before the countdown. Zero-stackable is pure-decidable from those records (`has_stack_entry`, computed at load with the stacking dataset for BOTH demo and upload paths — gui_setup._on_apply routes both through setloader with stacking_path). No records at all already has its own line ('no records anchored - play without pickups') inside _build_engine.
  implication: C1 seam = one hud_logic pure builder `stack_mode_note(records) -> line|None` + one call in begin_game just before 'Get ready...' — inherently once per run (begin_game runs once per Start/Restart).

- timestamp: 2026-09-21
  checked: hud_logic.breakdown_lines (C4) + its existing pins in tests/test_hud_content.py
  found: every non-'stacked' history entry renders `refused %dx %s: %s` — SKIP_* outcomes (informational skip taxonomy) are mislabeled 'refused' in the end-of-run recap even though the in-play ReasonCoalescer line says 'skipped'. Existing pins (test_refusals_grouped_by_outcome_and_name, test_first_appearance_order, test_distinct_outcome_codes_group_separately) hard-code the mislabel — they pin the bug and must be UPDATED. History entries carry outcome = placement code; SKIP_*/REFUSE_* prefix IS the taxonomy key (placement.py: 'the names are the contract').
  implication: C4 = label by code prefix in breakdown_lines ('skipped' for SKIP_*, 'refused' for REFUSE_*); the in-play skip_text('skipped <name>: ...') wording is checkpoint-pinned live text and OUT of scope (documented, unchanged).

- timestamp: 2026-09-21
  checked: gui_setup._on_apply seams for the C2 (Start/Apply guard) candidate
  found: the Apply success path builds a status_label message `parts` list with established advisory clauses ('xtb not found - ...', 'warning: ...'); records with has_stack_entry are local there, so a soft inline warning is ~1 helper call + 1 append — NEARLY FREE and honest. A HARD block (suppressing start_requested.emit) would break the legitimate practice/steering use and conflicts with the C1-preserving design.
  implication: C2 verdict-in-progress: soft warning PROPOSABLE (would reuse the same hud_logic.stack_mode_note builder, no wording drift); hard block REJECTED. Documented for owner decision — C1 already covers the honesty requirement at the natural play surface.

- timestamp: 2026-09-21
  checked: ReasonCoalescer QTextCursor rewrite path (the 'glued (x2)' cosmetic)
  found: info lines live ONLY in the Game tab QTextEdit (no console echo anywhere — _log/_log_reason/_dbg_event all funnel to info_box.append). Qt append() on a non-empty doc = insertBlock + insertText (exactly one block per line; last block = last line). The rewrite path (movePosition(End) -> select(BlockUnderCursor) -> insertText) replaces the LAST BLOCK'S CONTENTS; BlockUnderCursor never selects the block separator, so no line can ever fuse with its neighbor. A coalesced repeat CANNOT target a neighboring block (any interleaved _log breaks the run first, so the repeat arrives only when the last block IS the prior skip line).
  implication: NO formatting bug exists in the HUD path; the 2026-09-20 'delta=+90.0000skipped 931' glue was a copy/paste artifact external to the info box. Verified by inspection; nothing to fix (coalescer untouched).

## Candidates (owner decision needed)

- C1 (explanation line): at begin_game, if the active set has ZERO stackable species, print one info-box line: "this set has no stacking entries — demonstration mode: practice steering; only a crash ends the run". Minimal, honest.
- C2 (setup-side guard)***: warn or block Start for upload-only sets with the same explanation (harder block vs soft warn — owner's call).
- C3 (mixed-set escape hatch, document only): mixed demo+upload games already stack via demo species; docs note that uploads ride along as visual pickups.
- C4 (taxonomy fix): recap wording `skipped Nx` vs `refused Nx` distinguished; likely bundles with any of the above.
- OUT OF SCOPE without a new dataset + explicit approval: giving uploads a generic stacking geometry (that is v2 STACK-06 territory — user-approved generic fallback list; repo rule: no invented chemistry).

## Resolution

root_cause: DESIGN GAP, not a code defect. By locked STACK-03/03-04 design, '__upload__' records never carry a dataset entry, so every upload capture resolves cleanly to SKIP_NO_ENTRY — the placement/skip machinery worked exactly as designed. The failure was a MISSING COMMUNICATION LAYER: (1) begin_game gave no indication that a set with zero stackable species has no reachable win condition, so the run was silently endless-with-silence; (2) the end-of-run recap aggregated ALL non-stacked outcomes under the label 'refused', so the honest skip path was mislabeled as refusals ('refused 7x 931: ...').

fix:
  C4 (recap taxonomy) — commit e0b2814 `fix(05): recap breakdown labels skips vs refuses by outcome taxonomy (C4)`
    - serpentrum/hud_logic.py: breakdown_lines labels by outcome-code prefix — SKIP_* -> 'skipped Nx', REFUSE_* -> 'refused Nx' ('the names are the contract', placement.py). Docstring updated.
    - tests/test_hud_content.py: 3 pins updated (they pinned the mislabel) + 2 new pins (REFUSE keeps 'refused'; every SKIP_* code renders 'skipped').
  C1 (begin_game explanation) — commit 64882c3 `fix(05): begin_game demo-mode note for zero-stackable sets (C1)`
    - serpentrum/hud_logic.py: new pure builder stack_mode_note(records) -> 'this set has no stacking entries - demonstration mode: practice steering; only a crash ends the run' when EVERY record has has_stack_entry False; None when >= 1 stackable record or records empty (the 'no records anchored' branch owns that state); missing key counts as not stackable.
    - serpentrum/gui_game.py: begin_game logs the note ONCE per run (Start or Restart) right before 'Get ready...'.
    - tests/test_hud_content.py: TestStackModeNote — 8 pins incl. full detection matrix, real-data pins (shipped set_a -> None; naphthalene-as-upload -> note), and a one-shot-ness source pin (exactly 1 call site in gui_game.py).
  C2 (setup-side guard) — EVALUATED, NOT IMPLEMENTED (owner decision point):
    - verdict: soft inline warning is PROPOSABLE and nearly free: gui_setup._on_apply's Apply-success `parts` list (status_label; same seam as 'xtb not found - ...') could append hud_logic.stack_mode_note(records) — records are local there with has_stack_entry computed via the stacking dataset, no wording drift (same builder). ~6 lines + a GUI human-verify.
    - NOT implemented in this session because C1 already satisfies the honesty requirement at the play surface, and a second identical surface at Apply time is a UI-duplication trade-off the owner should opt into.
    - HARD block (suppressing start_requested.emit) REJECTED: a zero-stackable run is a legitimate practice/steering use the C1 note now names explicitly; blocking Start would remove a working demo mode.
  C3 (mixed-set escape hatch) — docs note: mixed demo+upload sets already stack via the demo species (their has_stack_entry records); uploads ride along as visual pickups and skip honestly. stack_mode_note returns None for any set with >= 1 stackable record, so mixed sets get no demo-mode note (correct).
  C5 (coalescer '(x2)' glue) — NO BUG: verified by construction (see Evidence 2026-09-21 #4 — info lines live only in the info-box QTextEdit, append() is one block per line, BlockUnderCursor+insertText replaces block contents and never the block separator; an interleaved _log always breaks the coalescer run first, so a rewrite can only ever target the prior skip line itself). The 2026-09-20 glue was a copy/paste artifact external to the info box. Coalescer untouched.

verification:
  - `python3.6 tests/run_gates.py` green after each of the two fix commits (syntax + plugin-path safety PASS, purity AST PASS, scoped unittest PASS).
  - TDD: new/updated pins went RED first (5 failures + 7 AttributeErrors pre-implementation), then GREEN.
  - Final full run: 640 unittests OK; `tests/run_gates.py --smoke` — 7/7 required sentinels PASS (SKELETON, VIEWER-BRIDGE, VIEWER-DEMO, LOOP-CAMERA, INPUT-WIZARD, TRANSFORM, EDGEON incl. smoke 08's 8-step UPLEDGEON/SCENECLR sequence); informational smoke 02 FAIL (known, non-blocking).
  - Human-verify (owner, next upload-only game): the run opens with the demonstration-mode line above 'Get ready...'; the recap reads 'skipped Nx <name>: no verified stacking entry...' (never 'refused').

files_changed:
  - serpentrum/hud_logic.py (C1 + C4)
  - serpentrum/gui_game.py (C1 call site + begin_game docstring)
  - tests/test_hud_content.py (C1 + C4 pins)

## Links

- Skip routing + edge-on uploads: commits 93f4b2b, 22b7245 (05-16 round-4 fixes)
- Wall-gate removal (context for why skips are now the only non-placement outcomes besides clash): commit d33f74c
- '__upload__' never inherits stacking entry: 03-04 decision (STATE.md 2026-09-11)
- STACK-06 (v2 generic fallback): REQUIREMENTS.md v2 section
