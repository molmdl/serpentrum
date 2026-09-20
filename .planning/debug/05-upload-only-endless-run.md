---
status: open
trigger: "upload: can play just no stacking at all (endless)"
created: 2026-09-20T16:08:00Z
updated: 2026-09-20T16:08:00Z
---

## Current Focus

hypothesis: an upload-ONLY molecule set can never stack (STACK-03: '__upload__' records carry no dataset entry by design — 03-04 decision), so the run has no reachable win condition; the only terminal outcomes are deliberate crash or boredom
test: read begin_game/setloader composition flow; enumerate what a run with zero stackable species should DO (not whether it can)
expecting: an owner-picked UX resolution from the candidate list below
next_action: dedicated /gsd-debug session; owner decision required on the resolution (see Candidates)

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

## Candidates (owner decision needed)

- C1 (explanation line): at begin_game, if the active set has ZERO stackable species, print one info-box line: "this set has no stacking entries — demonstration mode: practice steering; only a crash ends the run". Minimal, honest.
- C2 (setup-side guard)***: warn or block Start for upload-only sets with the same explanation (harder block vs soft warn — owner's call).
- C3 (mixed-set escape hatch, document only): mixed demo+upload games already stack via demo species; docs note that uploads ride along as visual pickups.
- C4 (taxonomy fix): recap wording `skipped Nx` vs `refused Nx` distinguished; likely bundles with any of the above.
- OUT OF SCOPE without a new dataset + explicit approval: giving uploads a generic stacking geometry (that is v2 STACK-06 territory — user-approved generic fallback list; repo rule: no invented chemistry).

## Links

- Skip routing + edge-on uploads: commits 93f4b2b, 22b7245 (05-16 round-4 fixes)
- Wall-gate removal (context for why skips are now the only non-placement outcomes besides clash): commit d33f74c
- '__upload__' never inherits stacking entry: 03-04 decision (STATE.md 2026-09-11)
- STACK-06 (v2 generic fallback): REQUIREMENTS.md v2 section
