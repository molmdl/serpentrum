---
phase: 09-random-line-wall-spawning
plan: 04
subsystem: ui
tags: [unittest, hud, help-text, dbg-trace, exact-string-pins, ascii, phase9, DOCS-03, D-WALL-HUD]

# Dependency graph
requires:
  - phase: 04-game-loop-input (04-02)
    provides: the hud_logic PURE module (stdlib-only display helpers,
      %-formatting) this builder joins
  - phase: 08-demo-data-docs-release-audit (08-06)
    provides: help_text._GAME_HINTS / game_hint(state) and its
      test_help_text.py pin home + TestAsciiSweep / TestDriftAlarms
      harness this edit must stay green under
  - phase: 05-stacking-game-rules (05-13, 33c13e7)
    provides: the pure DBG builder discipline (caller computes inputs
      unconditionally, gates only the log call) debug_wall_trace joins
provides:
  - hud_logic.debug_wall_trace(wall_id, p1, p2, new_mol_id, new_centroid,
    gap, tick=None) — the exact-format SRP_DEBUG wall-spawn line
    'DBG wall spawn <id> p1=(%.2f,%.2f) p2=(%.2f,%.2f) len=%.4f
    new_mol=<pid>@(%.2f,%.2f) gap=%.4f' (+ ' tick=%d' when tick given;
    len = segment length, gap = min per-atom clearance) — pure, NO
    gating inside
  - the '_playing' help clause: 'Steer with the arrow keys. Red wall
    lines are obstacles - touching one ends the run. If keys seem
    dead, click the 3D viewer first.' (D-WALL-HUD default SILENT holds:
    NO wall_spawn_note builder ships)
  - TestWallDebugTrace (4 exact/shape pins) + the re-pinned
    TestGameHint::test_playing
affects: [09-05 (the red srp_wall geometry the hint names), 09-07
  (the controller wall seam consumes debug_wall_trace + the call-site
  pins land there), 09-09 (the feel-check audits gap=%.4f live)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Exact-string %-format DBG pin family (debug_capture_trace /
      debug_event_trace / debug_spawn_cooldown precedent): the builder
      takes raw inputs, the test pins the byte-exact rendered line --
      builder purity asserted by NO session/debug/enable kwarg existing
      (TypeError on all three)"
    - "Coupled-pin discipline (913fbd5 quick-003 precedent): the shipped
      help string and its assertEqual pin move together, never drifting
      a user-visible literal from its tested wording"

key-files:
  created: []
  modified: [serpentrum/hud_logic.py, serpentrum/help_text.py,
             tests/test_hud_content.py, tests/test_help_text.py]

key-decisions:
  - "debug_wall_trace ships with ZERO gating inside (no session/debug
    flag in the signature): gating is the 09-07 caller's
    session.get('debug') concern, per the 33c13e7 unconditional-input
    discipline the plan locked"
  - "Feature B executed as the plan's named two-commit RED/GREEN pair
    (test re-pin 019caef, then feat string 843eee5), exactly as the
    <behavior>/<implementation> commit directives spell them; the
    plan's same-commit-discipline note blesses this route (the
    alternative single atomic commit was not needed -- the string and
    its pin are adjacent commits, never in different waves)"
  - "Purity asserted by calling with session=/debug=/enable= kwargs and
    expecting TypeError, instead of importing inspect: keeps the
    test_hud_content.py edit strictly append-only (the within-file
    additive discipline; the plan offers either arm)"

patterns-established:
  - "Wall-spawn DBG line carries the human audit fields: len (span
    sanity) + gap (min per-atom clearance, fed by
    wall.min_atom_clearance -- NEVER a viewer read, the 05-13
    zero-get_model discipline) so the owner's 'never overlap the new
    mol' mandate is auditable live at the 09-09 feel-check"
  - "One lethal rules get ONE help clause naming the visible cue (red =
    hazard) with the honest consequence ('ends the run'), DOCS-03
    clear-but-sufficient -- no rulebook paragraph in a state hint"

# Metrics
duration: 9min
completed: 2026-10-13
---

# Phase 9 Plan 04: Wall text surfaces (SRP_DEBUG wall trace + 'playing' help clause) Summary

**Two pure Phase-9 text surfaces TDD'd ahead of the wiring: the exact-format SRP_DEBUG wall-spawn trace builder (len + gap audit of the owner's no-overlap mandate, no gating inside) and the DOCS-03 'playing' help clause naming red wall lines as lethal obstacles — both exact-string/coupled-pinned, docs stay hidden, gates 1002 green**

## Performance

- **Duration:** ~9 min (wave-1 parallel worktree exec/09-04)
- **Started:** 2026-10-12T19:51:38Z
- **Completed:** 2026-10-12T20:00:19Z
- **Tasks:** 2/2 TDD features (2 RED/GREEN commit pairs, 4 atomic commits)
- **Files modified:** 4 (exactly the plan's files_modified; nothing else)

## Accomplishments

- `hud_logic.debug_wall_trace` — pure %-format DBG builder joining the
  33c13e7 family: renders
  `'DBG wall spawn <id> p1=(%.2f,%.2f) p2=(%.2f,%.2f) len=%.4f new_mol=<pid>@(%.2f,%.2f) gap=%.4f'`
  exactly (len = segment hypot, gap = the min per-atom clearance the
  09-07 caller feeds from wall.min_atom_clearance), optional
  `' tick=%d'` appended last; NO session/debug/enable parameter exists.
- `TestWallDebugTrace` (4 pins, test_hud_content.py +71 lines, strictly
  appended — pre-existing classes/count pins untouched) pins both tick
  variants byte-exactly, %s wall-id rendering for int + string ids, and
  the no-gating signature via TypeError on session=/debug=/enable=.
- `_GAME_HINTS['playing']` gains the DOCS-03 wall clause:
  `'Steer with the arrow keys. Red wall lines are obstacles - touching
  one ends the run. If keys seem dead, click the 3D viewer first.'` —
  ASCII-pure (TestAsciiSweep green), honest 'ends the run' wording,
  unknown-state ValueError contract untouched; its pin re-pinned in the
  coupled 019caef/843eee5 pair.
- Absence pins hold: ZERO `wall_spawn_note` in serpentrum/ (D-WALL-HUD
  default SILENT -- pickups are HUD-silent, the geometry IS the cue);
  no REFUSE_WALL-shaped placement taxonomy created (the active pin
  test_placement.py:234 hasattr(placement,'REFUSE_WALL') stays green);
  test_docs_audit.py 23 OK UNMODIFIED (check_docs does not audit
  help_text -- docs stay hidden).

## Task Commits

Each task was committed atomically (TDD RED -> GREEN per feature):

1. **Feature A RED: debug_wall_trace exact-string pins** — `dab63d4` (test)
   - new class errors (AttributeError) while all 79 pre-existing tests stay green
2. **Feature A GREEN: pure debug_wall_trace DBG builder** — `6178847` (feat)
   - scoped suite 83 OK (79 + 4 new)
3. **Feature B RED: re-pin playing hint with the wall-obstacle clause** — `019caef` (test)
   - only test_playing fails; TestAsciiSweep / TestDriftAlarms / unknown-state ValueError contracts stay green
4. **Feature B GREEN: playing-help clause names red walls as lethal obstacles (DOCS-03)** — `843eee5` (feat)

**Plan metadata:** see the docs(09-04) commit closing this plan (SUMMARY).

## Files Created/Modified

- `serpentrum/hud_logic.py` (+21) — `debug_wall_trace` beside
  `debug_spawn_cooldown`/`debug_spawn_cooldown_over` (the DBG family
  seam the 09-07 controller wall call will consume); `math` was already
  imported (no import change needed).
- `serpentrum/help_text.py` (+3/-2) — ONE-STRING edit to
  `_GAME_HINTS['playing']`; surrounding dict untouched, no new states.
- `tests/test_hud_content.py` (+71) — `TestWallDebugTrace` appended
  before `__main__`; TestGuiSpawnCallSites / TestDebugTailBinding /
  one-call-site count pins UNTOUCHED (no gui call sites added this
  plan; call-site pins belong to 09-07).
- `tests/test_help_text.py` (+5/-1) — `TestGameHint::test_playing`
  re-pinned to the new literal (the ONLY edit in the file).

## Verification (plan block, all run)

- `python3.6 -m unittest discover -s tests -p "test_hud_content.py" -v`
  -> 83 OK, all classes green
- `python3.6 -m unittest discover -s tests -p "test_help_text.py" -v`
  -> 22 OK (21 shapes + the re-pinned literal; TestAsciiSweep green)
- `python3.6 -m unittest discover -s tests -p "test_docs_audit.py" -v`
  -> 23 OK UNMODIFIED
- `python3.6 tests/run_gates.py` -> ALL GATES GREEN (syntax + plugin-path
  safety + AST purity + 1002 tests; hud_logic/help_text stay PURE,
  zero allowlist edits)
- `grep -rn "wall_spawn_note" serpentrum/` -> ZERO hits
- `grep -n "REFUSE_WALL" serpentrum/placement.py` -> only the pre-existing
  2026-09-20c retirement COMMENT (line 94); the ACTIVE absence pin
  (test_placement.py:234, `hasattr(placement, 'REFUSE_WALL') is False`)
  is green -- this plan created no REFUSE_WALL string anywhere
  (test_placement.py 37 OK)

Test-suite delta: 998 -> 1002 (net +4 = TestWallDebugTrace; measured at
the branch point d02c030 and at HEAD via full gates runs).

## Decisions Made

- **Feature B commit route:** executed as the plan's named two-commit
  RED/GREEN pair (RED test commit then feat string commit) exactly as
  the <behavior>/<implementation> directives spell them; the plan's
  same-commit-discipline note explicitly blesses this route (a single
  atomic commit could equivalently satisfy the 913fbd5 coupling rule).
  The shipped literal and its pin never live in different waves.
- **Purity-pin arm:** asserted no-gating via TypeError on
  session=/debug=/enable= calls instead of `import inspect` — keeps the
  test_hud_content.py change strictly append-only (the plan offers
  either arm; no new imports).
- **No refactor commit:** both implementations are the plan's verbatim
  code (the builder is the plan's exact function; the help edit is the
  ONE-STRING edit) — nothing to refactor, tests green after GREEN.

## Deviations from Plan

None - plan executed exactly as written (commits, literals, formats,
test names, and messages verbatim from the plan directives).

## Issues Encountered

- The plan's verification line `grep -n "REFUSE_WALL"
  serpentrum/placement.py -> ZERO hits` is imprecise about
  placement.py's historical retirement NOTE (comment lines 94-96, a
  pre-existing baseline record of the 2026-09-20c owner directive that
  the shipped pin deliberately tolerates). The actual absence pin
  (`test_refuse_wall_constant_is_retired`, test_placement.py:234,
  asserting the MODULE MEMBER does not exist) is green at baseline and
  at HEAD; this plan created none and touched no file outside its four
  files_modified. No action needed (and none allowed: removing the
  retirement comment is outside this plan's scope).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **09-05:** the red srp_wall geometry this help clause names becomes
  visible; the hint's 'red = hazard' wording and the DEFAULT-SILENT
  wall spawning (no wall_spawn_note) are already pinned here.
- **09-07:** the controller wall seam consumes `debug_wall_trace`
  exactly like the 33c13e7 family: compute p1/p2/the spawned record
  and the wall.min_atom_clearance gap UNCONDITIONALLY, gate only the
  log call on `session.get('debug')`; the gui call-site count pins
  (TestGuiSpawnCallSites pattern) land there, not here.
- **09-09:** the feel-check audits the owner's no-overlap mandate live
  by reading `gap=%.4f` off SRP_DEBUG=1 runs; D-WALL-HUD helper notes
  could be re-proposed there if the owner flips the silent default.
- Suite moved 998 -> 1002 with zero touched neighbors: the 09-07
  verifier can cite this plan for both text surfaces instead of
  re-deriving them.

---
*Phase: 09-random-line-wall-spawning*
*Completed: 2026-10-13*
