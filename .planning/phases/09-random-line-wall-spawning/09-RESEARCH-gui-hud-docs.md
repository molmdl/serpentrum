# Phase 9: Random Line-Wall Spawning — Research: GUI Wiring / HUD / Help Text / Docs-Audit / Requirement Mapping

**Researched:** 2026-10-12 (UTC)
**Focus:** the GUI+HUD+help+docs half of Phase 9 — wiring points in `gui_game.py`, HUD wording families, help-text placement, doc-audit impact, requirement-mapping mechanics, Setup-knob verdict, feel-check design, GUI-side pitfalls
**Companion researchers:** `09-RESEARCH-engine-policy.md` (engine/spawn policy), `09-RESEARCH-viewer-bridge.md` (CGO/bridge/smoke) — both read in full; clashes verified against my files and surfaced inline
**Confidence:** HIGH (every claim verified against live source with file:line; scoped WSL python3.6 unittest probes re-run green 2026-10-12)

**Owner request (verbatim, 2026-10-11):** "improve gameplay experience by random spawn line as wall-within-box after picking up a mol, at the same time as the spawn of the next mol. the line-wall should not overlap with the newly spawn mol."
**Session directives (owner):** fine-grained focused plans (20–100+ accepted); doc-update plans ONLY if docs are actually affected — otherwise keep the change "hidden".

---

## 1. Context recap

- v1 milestone COMPLETE + GATE V owner "approved" 2026-10-10; **46/46 v1 requirements Complete**; post-release quick tasks 001–003 landed; baseline battery at HEAD: **995 unittests + 11/11 required smokes green** (STATE.md:13-15, 2026-10-11 quick-003).
- Phase 9 is the **first integer phase appended post-release** (ROADMAP.md:30, :323-335) — added 2026-10-11, UNPLANNED; ROADMAP leaves requirement mapping to planning: "refine an existing GAME rule vs. mint a new GAME-12" (STATE.md:108).
- No CONTEXT.md exists in this phase dir (the only inputs are the owner verbatim request + the two sibling research docs).
- Engine sibling research decided (§2 there): wall = `('crashed', 'wall')` riding the existing crash payload; wall hook in `_respawn_pickup`'s success branch guarded by `not engine.finished`; ONE live wall `(srp_wall)` replaced per spawn; separate seeded RNG stream; HUD spawn decision default SILENT.

**Baseline probes re-run 2026-10-12 (WSL python3.6.9, all green, zero files modified):**
`test_hud_content.py` 79 OK · `test_hud_logic.py` 13 OK · `test_help_text.py` 22 OK · `test_gui_pins.py` 19 OK · `test_docs_audit.py` 23 OK · `test_audit_requirements.py` 16 OK.

---

## 2. Verified findings (Q1–Q8, file:line evidence)

### 2.1 Q1 — Wiring map in `gui_game.py`

**The pickup spawn chain today (all line numbers at HEAD 2026-10-12):**

| Site | Location | What happens |
|---|---|---|
| Construction | `_build_engine` gui_game.py:520-522 | `spawn_mod.PickupSpawner(records, (x0,y0), (x1,y1), spawn_mod.seed_from_setup(setup), atoms_by_id)` — the ONLY construction site |
| First spawn | `_build_engine` :526-531 | `spawner.first((0.0, 0.0), 'right')` → `build_pickup_seed` → `GameEngine(pickups=[seed])` :532-538 |
| Session anchor | `begin_game` :405-430 | session dict keys incl. `'spawner': extras['spawner']` :415; anchored on `_serpentrum.game_session` :431-432 |
| Respawn (capture tail) | `_handle_stack_event` :1155-1160 | `spawner.note_resolution(...)` then **`self._respawn_pickup(session, engine)` — call site 1** |
| Respawn (cooldown resume) | `_on_tick` :727-732 | `spawner.tick()` resume edge → **`self._respawn_pickup(session, engine)` — call site 2** |
| The spawn gate itself | `_respawn_pickup` :1205-1257 | `can_spawn` gate :1222 → `next_after(engine.head, _heading_name(engine.heading), chain_atoms, live_centroids)` :1229-1231 → None path :1232-1243 (cooldown DBG note; **NO state advance**) → success: `build_pickup_seed` :1244-1246 → engine state append :1251-1253 → `pymol_bridge.materialize_pickup` :1254-1257 |

**THE wall hook attaches at the TAIL of `_respawn_pickup`'s success branch — after :1257** (`session['live_pickup_names'].append(name)`), as a single new guarded block:

1. `if engine.finished: return` — the win-tick guard (probe-verified by the engine research §5: `finished=True/result='won'` are ALREADY set while `'stacked'` dispatches; today `_respawn_pickup` does NOT guard this and materializes a doomed pickup on the win tick — harmless because teardown pattern-deletes `srp_pickup_*`, but a wall would NOT be swept there, :1524).
2. Read the wall spawner off the session (`session.get('wall_spawner')`); None (no-records runs, :511-512 parity) ⇒ return.
3. Draw the wall over data ALREADY assembled in this scope: `chain_atoms` (:1224-1226), `live_centroids` (:1227-1228) plus the fresh `seed`'s translated atoms (engine research C6).
4. On `None` → keep the previous wall (benign; engine research C3/L-exhaustion).
5. On a wall → `engine.set_wall(wall)` + bridge delete-then-load (`pymol_bridge.delete_walls()` guarded + `load_line_wall(...)`, bridge research §2.4) + optional SRP_DEBUG-gated trace line (§2.2 below).

**Why this placement is correct (and the alternatives are not):**
- **Owner pairing**: "at the same time as the spawn of the next mol" holds at BOTH call sites by construction — the capture tail (:1160) AND the exhaust-cooldown resume edge (:727-732) both route through `_respawn_pickup`. No mol spawn (MAX_LIVE gate :1222, cooldown None path :1243) ⇒ no wall swap.
- **Same-tick double-invocation is impossible**: on a tick where the resume edge fires after a capture, `_respawn_pickup` may run twice — the second run exits at the `can_spawn` gate (:1222, live count just grew) BEFORE the wall seam (success branch only) — a wall hook placed at the CALL SITES instead of inside `_respawn_pickup` could double-fire. Hook INSIDE the gate+success branch is correct by construction.
- **Crash-tick suppression**: the engine returns the crash event and stops processing (engine research §1.1/C2), so `_handle_stack_event` never runs on a wall/boundary/body crash tick — no wall can materialize between "crashed" dispatch and `_end_run`.

**`_build_engine` + `begin_game` additions (the construction half):**
- `from . import wall as wall_mod` (mirrors `from . import spawn as spawn_mod`, gui_game.py:75).
- In `_build_engine`, beside :520-522: `wall_mod.WallSpawner(...)` seeded via **`wall_mod.wall_seed_from_setup(setup)`** — a DIFFERENT call-string from `spawn_mod.seed_from_setup(` so the existing one-count source pin survives (test_hud_content.py:872-878).
- `extras['wall_spawner']` → session key `'wall_spawner'` in the :405-430 dict (session-dict additions are additive; the engine research C6 confirms no-records runs degrade to None).

**Epoch / pause considerations (Q1 tail):**
- The wall seam runs **synchronously inside the epoch-guarded tick** (`_on_tick` returns immediately on `session['epoch'] != self._epoch`, :687-689). NO singleShot may ever carry wall work — singleShot chains need epoch closures (Pitfall 9.1; `_run_countdown`/`_countdown_step` :625-648 is the pattern the wall must NOT join). Staying synchronous ⇒ **zero new epoch surface**.
- **Pause**: the seam only fires under `'stacked'` dispatch or the cooldown-resume edge, both inside `_on_tick`, which early-returns while `engine.paused or engine.finished` (:691-692). Timers stop on pause (:1313-1316) ⇒ the exhaust-cooldown clock freezes during pause (:721-726 comment) ⇒ wall swaps freeze with it. Auto-pause (dialog focus, :1339-1357) routes through the same `_apply_pause_state` — same freeze. **Nothing to design.**
- **Countdown**: tick timer starts at `_begin_play` (:674) — no wall can spawn during the countdown (status 'countdown', no ticks), and begin_game never spawns a wall (first wall = capture 1 ⇒ mol-2 spawn). Consequence invariant: **no `srp_wall` object exists at `frame_scene()` time** (:443, one-shot `cmd.zoom('srp_*')`) — framing geometry is unaffected.

**Source-scan pins (what test_gui_pins.py / test_hud_content.py expect):**
- `test_gui_pins.py` itself: its gui_game pins are PRESENCE-type only (`spawn_mod.effective_head_id` inside the `_build_head_state` body slice, :205-208) — **additive wall lines are safe**. Two repo-wide scans automatically sweep any new code: the blocking-modal token ban (`ex`+`ec_`, :116-124) and the move/resize-handler ban (:476-492) — both trivially green for wall wiring. test_gui_pins.py currently pins NOTHING about spawns.
- The **5.3-04 house pattern** puts gui_game call-site pins in `test_hud_content.py` (`TestGuiSpawnCallSites` :828-892) — that is where Phase-9 wall pins belong, as a NEW additive class (e.g. `TestWallWiring`), mirroring: exactly ONE `wall_mod.WallSpawner(` construction, ONE `wall_mod.wall_seed_from_setup(` wiring, ONE `next_wall(` call, the `engine.finished` win-tick guard inside the `_respawn_pickup` body slice, and the teardown call inside the `_teardown_round` body slice (bridge research §3.2; `_method_body` helper pattern, test_gui_pins.py:190-197/229-236). The blanket `assertNotIn('min_head_dist_a', source)` (:880-885) already covers wall kwargs too.
- `TestDebugTailBinding` (:895-959) slices `def _handle_stack_event` → `def _dbg_capture_line` (:922-924) and counts `debug_tail = None` == 2 and `if debug_tail is not None:` == 2. **Precision note:** `_respawn_pickup` (:1205) is defined AFTER `_dbg_capture_line` (:1169), so it lies OUTSIDE the counted slice — the wall seam lines never touch that test at all. (The engine research §2.6 called this "shares the slice region"; in fact `_respawn_pickup` is entirely outside the slice — safe either way, but the accurate statement is: the wall seam is slice-invisible.)

### 2.2 Q2 — HUD: crash wording family, recap, wall wording, builders

**Current crash-reason wording family (verbatim):**
- Engine reasons: `('crashed', 'boundary')` (game_engine.py:680) and `('crashed', 'body')` (game_engine.py:698); `result` is the unstructured `'crashed'`/`'won'` (:235-236).
- GUI handler (payload-generic): gui_game.py:770-772:
  ```python
  elif kind == 'crashed':
      self._log('crashed into %s' % ev[1])
      self._dbg_event(engine, 'crashed', result=ev[1])
  ```
  → 'crashed into boundary' / 'crashed into body'; SRP_DEBUG adds `debug_event_trace` output `'DBG event crashed tick=... heading=... head=(...) result=boundary'` (hud_logic.py:443-470; exact pin test_hud_content.py:446-452).
- End-of-run verdict line: `'run over: %s' % (engine.result or 'over')` (gui_game.py:1396) → 'run over: crashed'.
- End-of-run recap (hud_logic.py:247-261 `completion_lines`, called gui_game.py:1444-1446):
  ```
  result: %s                     <- engine.result only ('crashed'/'won'); the crash REASON never reaches the recap
  score: %d molecule(s) stacked
  snake: %d molecules (incl. head)
  atoms: %d (stacked molecules, head excluded)
  ```
  followed by `breakdown_lines(session['stacked_history'])` (:1448-1449) — stacked grouped by name with distance + citation; `SKIP_*` outcomes count 'skipped Nx', `REFUSE_*` count 'refused Nx' (hud_logic.py:264-299).
- Related defensive family (nearby literal): `turn_refuse_text` → 'turn refused: %s (%s)' with `_TURN_REFUSE_WHY = {'boundary': 'walls only stop the head (the chain may swing past the box during a turn)', ...}` (hud_logic.py:497-521) — **DEFENSIVE-ONLY** (the engine emits no 'turn_refused' events; gui_game.py:756-763, hud_logic.py:514-517). Note this family uses "walls" to mean the BOX faces — see Pitfall 9 (vocabulary).

**Wall crash wording — ZERO new HUD code for the crash path:** with `('crashed', 'wall')` (engine research C2) the GUI prints **'crashed into wall'** through the untouched generic handler, plus the free `'DBG event crashed ... result=wall'` trace. Recap stays 'result: crashed'. `'crashed into wall'` is unambiguous against 'crashed into boundary' (the GUI has never printed "wall" for the box — verified: the only "wall" strings in hud_logic.py:4-5 are "wall clock" doc-text, :479-498 the defensive turn comments). No completion-path edit: `_end_run` → `_teardown_round` → `_present_completion` all key on `engine.result` (:1382-1475).

**Optional wall-spawn note (D-WALL-HUD, default SILENT — endorse):** pickup spawns are HUD-silent today (no info-box line at spawn; only SRP_DEBUG cooldown lines, :1232-1242), so SILENT is the established chattiness policy — "the visible geometry IS the cue" (engine research §2.6 D-WALL-HUD). If the owner flips it at the feel-check, ship a **pure `hud_logic.wall_spawn_note()`** builder on the **5.1-03 speed_note TDD pattern** (5.1-03-SUMMARY: pure %-format builder + `TestWallSpawnNote` class in test_hud_content.py + a NEW one-call-site pin `source.count('wall_spawn_note(') == 1` mirroring :798-810; RED→GREEN commits). Proposed literal (owner-blessable, ASCII, one line, digit-free so GAME-04 hidden-counts stays trivially intact): **`'a red wall line spawned - it blocks part of the box'`**. Route through `_log` (NOT `_log_reason`): it is not a placement-outcome code, so **ReasonCoalescer never applies by design**; be aware `_log` breaks an in-flight coalesced refuse run (:1541-1544) and wall swaps land exactly during refuse cascades (capture resolution) — one more argument for the silent default.

**DBG wall trace (SRP_DEBUG=1 only) — name and format already proposed by the bridge half; endorsed:** `hud_logic.debug_wall_trace(...)` output `'DBG wall spawn <id> p1=(%.2f,%.2f) p2=(%.2f,%.2f) len=%.4f new_mol=<pid>@(%.2f,%.2f) gap=%.4f'` (bridge research §5.2), joining the pure DBG builder family (`debug_spawn_cooldown`/`_over`, hud_logic.py:423-440, exact-string pin pattern test_hud_content.py:813-825). The `gap=%.4f` field is the live human-audit of the owner's "should not overlap the newly spawn mol" invariant. **33c13e7 discipline applies**: any debug-locals in the wall seam must be bound UNCONDITIONALLY if consumed unconditionally (the TestDebugTailBinding backstory: debug-gated bindings broke non-debug spawning for weeks); simplest compliant shape = compute the trace inputs unconditionally, gate only the `self._log` call — and avoid ever writing the literal `debug_tail` in new code.

**Nearby literals pinned today (the pin blast radius for any wall HUD wording):**
- test_hud_content.py: `completion_lines` 4 exact lines (:180-197 — note the test feeds `result='crashed (boundary)'` to prove payload passthrough; the real runtime value from the caller is plain `'crashed'`); `REFUSE_WALL` absent from `placement.__dict__` + 'leave the play box' absent from `_REASON_TEXT` values (:351-357 — wall work must NOT add any `REFUSE_WALL`-shaped placement code); one-call-site pins `stack_mode_note(`==1 (:597), `generic_consent_note(`==1 (:736), `speed_note(`==1 (:808); TestGuiSpawnCallSites (:849-892); TestDebugTailBinding (:926-959); exact DBG event strings (:446-472); ReasonCoalescer behavior (:486-519).
- test_hud_logic.py: pins ONLY format_elapsed/remaining_text/molecules_remaining (:36-102) — **no crash/wall surface at all**; wall HUD builders belong in test_hud_content.py, not here.

### 2.3 Q3 — help_text.py: current Game hints + where a wall mention belongs

**Current Game-screen strings (verbatim, help_text.py):**
- `GAME_FOCUS_HINT = 'Click Start on the Setup tab. Steer with arrow keys; click the 3D viewer first if keys seem dead.'` (:61-62)
- `CONTROLS_RECAP = 'Arrow keys steer (no 180-degree turns - rigid chain pivot); Pause/Resume, Restart and Get Spectra are buttons.'` (:64-66)
- `_GAME_HINTS` (:165-174): `'idle'` = FOCUS + RECAP; `'countdown'` = 'Get ready - steer with the arrow keys once GO! appears.'; **`'playing'` = 'Steer with the arrow keys. If keys seem dead, click the 3D viewer first.'**; `'paused'` = 'Paused - press Resume to continue.'; `'over'` = 'Run over - press Get Spectra to compute the IR spectrum of your snake.'
- The Game tab renders `game_hint(state)` at every status flip (gui_game.py:327, :474, :681, :1323, :1337, :1475).

**Placement verdict:** a wall mention belongs in **`_GAME_HINTS['playing']`** only — the one state where walls exist and where an undiscoverable lethal rule needs one clause. DOCS-03 verbatim: "In-game help covers controls, a 'click the 3D viewer' focus hint, what negative frequencies mean, and a next-action hint on every screen — **clear but sufficient, no walls of text**" (REQUIREMENTS.md:77); AGENTS.md:17: "UI must be simple and user-friendly, with clear but sufficient in-game explanation." A crash-on-contact rule that a first-time player cannot know is the classic "clear but sufficient" gap; one short clause closes it without approaching a wall of text.

**Proposed exact wording (owner-blessable at the feel-check; honest — a wall crash ENDS the run but the snake still completes → spectra):**
> `'Steer with the arrow keys. Red wall lines are obstacles - touching one ends the run. If keys seem dead, click the 3D viewer first.'`
(Red = the bridge half's recommended color (1.0, 0.0, 0.0), bridge research §2.2 — the hint names the visible cue; keep the sentence honest: it says "ends the run", not "destroys the snake".)

**Which pins a help-text touch carries:**
- `tests/test_help_text.py::TestGameHint::test_playing` pins the CURRENT literal with `assertEqual` (:145-149) — **the test must be edited in the SAME commit as the string** (coupled-pin discipline; quick-003 precedent: coupled pins synced "in one atomic commit 913fbd5", STATE.md:101).
- `TestAsciiSweep` (:202-217) sweeps all public strings — a wall clause must stay pure ASCII (house convention, help_text.py:51-53).
- `game_hint`'s unknown-state ValueError contract (:161-165, :192-205) is untouched — no new states.
- `TestDriftAlarms` (:247-319) pins references in OTHER files (GAME_FOCUS_HINT / SETUP_TOOLTIPS / BUTTON_TOOLTIPS) — no help_text-internal pin touches `_GAME_HINTS['playing']` beyond test_playing.
- `tools/check_docs.py` does **NOT** audit help_text.py at all: its `CONTROLS` table (:102-124) pins literal control names in gui.py/gui_setup.py/gui_game.py/gui_spectra.py/gui_plot.py/input.py only. → **A help-text wall clause needs zero check_docs edits.**

### 2.4 Q4 — Docs-impact verdict (authoritative)

**check_docs.py check families (all 7, tools/check_docs.py:14-48 + `run_all` :365-389):**

| # | Family | What it proves | Wall impact |
|---|---|---|---|
| 1 | vibe-block | README lines 1-4 == `VIBE_LINES` byte-exact (:81-86, :152-159) | None |
| 2 | placeholders | zero 'TBD' in README; zero 'sECDpent' in README+spec (:162-172) | None |
| 3 | control-literals | 20 pinned control literals exist in named code files (:102-124, :175-190) | None (additive wall code removes nothing) |
| 4 | numeric-claims | README numeric tokens COMPOSED from setup_logic constants + dataset + manifest (:193-301); banned `'30-90 s'` absent | None (token list is fixed in `expected_numeric_tokens` :244-273 — **not auto-extending**; no wall constant is README-cited) |
| 5 | install-recipe | 'Add plugin directory' + 'restart PyMOL' present; 'Install New Plugin' banned (:304-315) | None |
| 6 | path-refs | every back-ticked README path exists on disk (:318-333) | None (no wall path needs documenting) |
| 7 | claim-bans | banned claims ('P = pause', 'Apply / Show in Viewer', 'xtb4stda', 'std2', 'Generate and export') + affirmative-'animation' window (:135-147, :348-356) | None |

**README gameplay claims (quoted, README.md):** line 8 "Classical snake game in (bio-) molecular viewer stacking molecules, as an analogue of 'self-assembly and spectra calculation'."; § Usage :36-45 (Setup canonical values line :39: "speed tiers 6.0 / 9.0 (default) / 11.0 / 13.0 A/s; box presets 35 / 55 / 85 A half-widths (medium default) ..." etc.; Start/countdown :40; steering :41 "Steer with the 4 arrow keys. If the keys seem dead, click the 3D viewer first; when the dialog takes focus the game auto-pauses."; completion :42; Get Spectra :43; srp_* cleanup :45). **There is NO mention of walls, obstacles, crash rules, or boundary/body collision anywhere in the README** (verified by full read + grep). Adding in-box walls makes no README claim false; "Classical snake game" (which across the genre conventionally includes wall/obstacle hazards) becomes, if anything, more accurate.

**VERDICT — docs stay "hidden" (no doc-update plan):**
- `tools/check_docs.py` + `tests/test_docs_audit.py` stay green with ZERO edits (baseline re-verified: 23 tests OK).
- README: NOT touched by Phase 9 — the doc-vs-code audit is one-directional for our change (existing claims remain true; nothing forces new claims).
- help_text.py IS a code module with its own TDD (not a "docs plan"): the ONE playing-hint clause of §2.3 rides the gui-wiring plan with its coupled test edit.
- DATA_SOURCES.md: **NOT relevant** (it is the demo-data source/attribution ledger for molecule geometry + stacking citations — a line-wall contributes no external data, no distances, no chemistry; the no-fabrication rule is not implicated; header scope: serpentrum/data/DATA_SOURCES.md:1-4 "All external data sources for the serpentrum Demo Set A").
- The only mandatory planning-doc edits are the NORMAL phase-close bookkeeping (§3 requirement mapping + ROADMAP Phase 9 stub fill + STATE wrap) — that is GSD bookkeeping built into the closing plan, not a doc-update plan.
- Re-evaluation trigger: if the owner later adds a Setup knob (§2.6) or flips D-WALL-HUD to a default-play line, revisit (a knob means a tooltip + `SETUP_TOOLTIP_KEYS` pin + possibly a README canonical-values token; a HUD line means one-call-site pins — all still plan-internal).

### 2.5 Q5 — Requirement-mapping dossier (both routes + recommendation)

**How `audit_requirements.py --release` treats the ledger (parse vs hardcoded):** the tool **PARSES** `.planning/REQUIREMENTS.md` (traceability table rows with ID-first cells, audit_requirements.py:70-85; checkbox lines `- [x] **ID**:` :88-93) and validates the parse against a **HARDCODED canonical ID list + count** (`CANONICAL_IDS` :47-54, `REQUIRED_COUNT = 46` :55) — the anti-drift design is deliberate: "the canonical 46 are hardcoded so count drift — the stale '44' class — fails loudly, Pitfall 8" (:5-7). `--release` adds the zero-Pending check (:187-193). An independent SECOND hardcoded list lives in tests/test_audit_requirements.py:29-37 and `TestCanonicalList` asserts the two lists are identical (:106-112). Evidence paths cited in rows must exist on disk (:150-161).

#### Route (a) — mint GAME-12: exact edit list

1. **tools/audit_requirements.py** (MANDATORY, same commit as the ledger flip):
   - `CANONICAL_IDS`: `'GAME-%02d' % i for i in range(1, 12)` → `range(1, 13)` (:47-54).
   - `REQUIRED_COUNT = 46` → `47` (:55).
   - comment :46 `# 8 + 11 + 6 + 6 + 4 + 6 + 5 = 46.` → 12-game/47.
   - docstring :5 "the canonical 46 are hardcoded" → 47.
2. **tests/test_audit_requirements.py** (independent list, same commit):
   - `IDS` GAME range edit (:31) + `assert len(IDS) == 46` → 47 (:37) + comment :28.
   - `TestCanonicalList.test_canonical_list_matches_fixture`: `self.assertEqual(46, len(ar.CANONICAL_IDS))` → 47 (:112).
   - `TestFixtureA.test_row_count_ok`: `self.assertIn('46', msg)` (:129) → '47' (or derive) — fixtures themselves auto-adapt (built by iterating `IDS`, `_build` :51-70).
3. **.planning/REQUIREMENTS.md**:
   - Gameplay checkbox: new `- [x] **GAME-12**: <text>` after GAME-11 (checkbox grammar pinned by `_CHECKBOX_RE`).
   - Traceability row: `| GAME-12 | Phase 9 | Complete | mech: tests/test_wall.py + tests/test_engine_wall.py + tests/test_phase5_integration.py (s10); code: serpentrum/wall.py + game_engine.py wall state/collision + gui_game.py wall seam; human: 09-XX feel-check APPROVED <date> |` — **every cited path must exist on disk when this lands** (check 3; flip AFTER code+tests, the 3fd30cf coupled-flip precedent).
   - Coverage block (":177-182"): "v1 requirements: 46 total" → "47 total", "(44 original + GAME-11 ... + STACK-06 ...)" gains "+ GAME-12 with Phase 9, 2026-10-XX"; Unmapped stays 0; count-note footnote updated.
   - Dated footer note (GAME-11 precedent wording, :187): "*2026-10-XX — GAME-12 added (Phase 9 appended): random line-wall ... Coverage 46 → 47.*"
   - Filing problem: the section header says "## v1 Requirements ... Requirements for initial release." (:6-8) — GAME-12 would be a **post-release feature filed as an initial-release requirement**; needs either a "v1.x" annotation inside the line or a new section (parser-agnostic: rows/checkboxes parse anywhere; only first-cell ID + count matter).
4. **.planning/ROADMAP.md**: header Coverage line :5 ("46/46 ... " → "47/47 ... + GAME-12 with Phase 9"); Phase 9 section :323-335 (Goal/Requirements `GAME-12`/Notes/Plans filled — TODO items "[To be planned]"); Coverage table Gameplay row :360 "GAME-01..11 | 4, 5, 5.1" → "GAME-01..12 | 4, 5, 5.1, 9"; Total line :367; count-note :369; Progress table :390.
- **Precedents (how GAME-11 + STACK-06 were recorded):** GAME-11 = new bullet :37 with "(inserted 2026-09-20 with Phase 5.1 — owner playtesting feedback)" + traceability row :145 + footer note :187 "Coverage 44 → 45" + ROADMAP Evolution (STATE.md:105). STACK-06 = v2 line struck through as "**PROMOTED to v1 2026-09-20** (Phase 5.2 — generic π-stack ...; see v1 STACK-06)" (:98) + v1 line :46 "(promoted from v2 with Phase 5.2, 2026-09-20 — owner request)" + footer :189 "Coverage 45 → 46". Both were **pre-release** mints; the audit tool + its test did not exist yet (built 08-10/T, post-5.x) — so GAME-12 is the FIRST mint that also forces the §1/§2 tool+test edits above.
- Cost: 4 non-planning files edited in lockstep + 6+ ROADMAP sites; risk = forgetting one hardcoded count (the tool fails loudly per design).

#### Route (b) — 5.3 precedent: dated amendment, coverage stays 46/46

1. **.planning/REQUIREMENTS.md** (host line amendment + footer note — the quick-003 pattern, STATE.md:101 "REQUIREMENTS GAME-11 dated amendment"):
   - GAME-05 line (:31) gains an italic amendment: *— **Phase 9 (2026-10-XX)**: the box may also hold ONE random line-wall (replaced at each next-mol spawn, never overlapping the newly spawned mol); head contact with it ends the run as the same crash class (snake still completes → spectra)*. GAME-05 is the natural host for the crash half ("Hitting the boundary or the snake's own body ... ends the run, but the snake is still 'complete'"); the spawn-pairing half has NO requirement host — exactly like 5.3's spawn policy (which minted no ID, ROADMAP.md:237 "no new requirement ID").
   - Dated footer note: "*2026-10-XX — Phase 9 (Random Line-Wall Spawning) COMPLETE: GAME-05 amended (third lethal-collision class: the random line-wall); spawn-pairing policy refined on the 5.3 model. Coverage stays 46/46.*"
2. **.planning/ROADMAP.md**: Phase 9 section filled; Requirements field mirrors 5.3's exact pattern — ROADMAP.md:221 "**Requirements**: (none new — refines the Phase 5 pickup spawn policy; coverage stays 46/46)" → "**Requirements**: (none new — refines the GAME-05 crash class + the spawn-cadence policy; coverage stays 46/46)". Coverage header/table/total lines UNTOUCHED (5.3's insertion touched none of them — verified: no 5.3 row exists in the Coverage table).
3. **tools/audit_requirements.py + tests/test_audit_requirements.py: ZERO edits** (46/46 unchanged; the audit's `--release` remains green).
4. STATE.md Roadmap Evolution entry mirrors the 5.3 line (STATE.md:107).

**How audit `--release` treats each route:** (b) — parser still finds 46 rows/checkboxes matching the hardcoded 46; green. (a) — green ONLY after both hardcoded lists go to 47 in the same commit as the ledger; missing tool edit ⇒ guaranteed FAIL (`ids-unique`: "unknown ID GAME-12 in traceability table" (audit_requirements.py:133-135); `row-count`: "traceability table has 47 ID rows, expected 46" (:141-147)).

**Recommendation: ROUTE (b).** Rationale:
1. **The v1 ledger is a CLOSED RELEASE RECORD**: GATE V signed 46/46 with human-certified evidence (REQUIREMENTS.md:175, "Flipped 2026-10-10 ... 46/46 v1 requirements Complete"); 08-VERIFICATION passed 162/162 against exactly that scope; STATE.md:108 explicitly holds the "v1 release record ... unaffected; milestone audit/archive deferred until Phase 9 lands". Minting retroactively into "Requirements for initial release" (:6-8) mislabels a post-release feature; route (b) keeps "46/46" meaning "the contract the owner signed".
2. **Direct precedent class**: Phase 9 is a post-release gameplay-refinement exactly like quick-003 (a shipped-mechanics change recorded as a dated amendment, coverage untouched) and structurally like 5.3 (a gameplay-policy change with no new ID).
3. **Feature-character honesty either way**: the crash half extends GAME-05's enumerated crash class (amendment keeps that text truthful — without it, GAME-05's line UNDER-describes the shipped surface, the strongest single argument that (b) must at least add the amendment note); the spawn-pairing half refines the same spawn cadence 5.3 refined.
4. **Churn minimization** per the owner's fine-grained-plans directive: (b) touches 2 planning docs; (a) touches 4 code/test/tool files + 6 ROADMAP sites in one lockstep commit.
Present both to the owner at plan time; if the owner prefers a visible new ID (scope-visibility argument), route (a)'s edit list above is complete and mechanical.

### 2.6 Q6 — Setup toggle: NO knob. Recommend ship-always-on

Evidence-based verdict:
- **5.3 precedent (the direct one):** 5.3 changed core gameplay policy (spawn positions) with NO Setup surface — just owner-retunable constants (`MIN_HEAD_DIST_FACTOR` via a ctor kwarg, ROADMAP.md:224, :237). Phase 9's wall is the same class: a core-rules improvement requested verbatim and unconditionally by the owner, not a user preference.
- **Knobs exist for choice/integrity dimensions only:** speed tier (GAME-11 — a feel preference), generic-stack consent (STACK-06 — educational-integrity consent, OFF default). Walls have no consent dimension and no obvious preference axis; an off/density knob is speculative scope the owner never asked for.
- **Cost of a knob today (what it would drag in):** a `DEFAULTS` key + `merge_defaults` absent-key backcompat (setup_logic.py:49-77, :183-197) + validate rule (:343-346 pattern) + randomize decision (randomize_setup must declare walls untouchable, as it does for consent, help_text.py:146-149) + a gui_setup row inside the **fixed-size two-column grid** (round-5 constraints, test_gui_pins.py:265-340) + `SETUP_TOOLTIPS` 13-key set pin edit (test_help_text.py:228-234 — a 14th key breaks the exact-set assertion unless coupled same-commit) + `collect_state` wiring pins (test_gui_pins.py:243-247) + persistence tests. One plan's worth of surface for a speculative need.
- **If the owner ever wants it:** additive follow-up is cheap by design — the `xtb_threads` comment shows the house pattern: "absent key = 4 via merge_defaults (additive key, no schema bump)" (setup_logic.py:58-61); 'speed' and 'generic_stack_consent' are the proven precedents. Wall constants remain owner-retunable data lines (wall.py constants/ctor kwargs — `WALL_LENGTH_FRACTION` etc., the `SPEED_TIERS`/`MIN_HEAD_DIST_FACTOR` quick-retune procedure).

### 2.7 Q7 — Feel-check design: the ONE consolidated owner closing checkpoint

**Convention check first:** every integer/urgent phase closes with EXACTLY ONE blocking human-verify checkpoint (Phase 8 is the owner-consolidated two-gate exception, ROADMAP.md:304): 04-09 "Phase-closing gate pass ... + final human-verify of the full playable loop" (:134); 05-16 "consolidated human-verify checkpoint" (:167); 5.1-06 "(Wave 3, blocking)" (:189); 5.2-09 "(Wave 5, blocking)" (:213); 5.3-05 "(Wave 3, blocking)" (:235); 06-12 "(Wave 4, blocking)" (:264); 07-10 "(Wave 6, blocking)" (:289). GUI verdicts are human-verify-only (offscreen route dead, STATE.md:130). **The pattern fits Phase 9 unchanged.**

**The closing plan (3 tasks, the 5.1-06/5.2-09/5.3-05 structures):**

- **Task 1 (executor, automatic) — gates + smokes recorded BEFORE the checkpoint** (5.3-05 "Wrap-plan verdict recording: gates + smokes run and recorded BEFORE the blocking human feel-check", patterns-established): `python3.6 tests/run_gates.py` (995 + net-new wall tests green) + `--smoke` battery — with the bridge half's smoke 15 registered, REQUIRED_SMOKES appends to 12/12 (run_gates.py:55-76; append-at-end + per-plan comment hunk, bridge research §3.3). Record verdict tables in the plan SUMMARY.
- **Task 2 (BLOCKING `checkpoint:human-verify`) — owner live feel-check in real Windows PyMOL, SRP_DEBUG=1.** Numbered live steps (all five mandated checks + the feel numbers):
  1. Launch the dev plugin (setenv.bat / dev install); Setup defaults (medium ±55, normal 9.0 A/s); Start.
  2. Pick up the first mol → the NEXT mol and the red wall line appear TOGETHER (same event); the wall is inside the box, both ends visibly roundable.
  3. **Not overlapping the new mol**: the live info box shows the `DBG wall spawn ... new_mol=... gap=...` line with gap above the clearance floor — the human-auditable form of the owner's no-overlap mandate (bridge research §5.2).
  4. The wall is AVOIDABLE: steer around it; it persists (environment) until the next pickup swaps it.
  5. Deliberately steer the head into the wall → **'crashed into wall'** info line (`'crashed into %s'` seam, gui_game.py:770-772) → **normal completion path**: snake complete, length/score/atoms recap + Get Spectra enabled (`_present_completion`, :1444-1475).
  6. Restart from the completion board → walls GONE (rebuild_scene `cleanup_srp` sweep, :194; fresh run shows NO wall until the first capture).
  7. Feel-number verdicts from the engine decision table (engine research §3): wall length (0.45×minor-span), orientation (arbitrary angle), clearances (12.0 head / 3.0 mol), box margin (6.0), collision radius (2.0) — "say the word" to retune (each is a single data-line edit).
  8. Owner decisions recorded: D-WALL decision-table verdicts + help-clause wording (§2.3) + (if D-WALL-HUD flipped) the spawn-note literal (§2.2).
- **Task 3 (conditional post-checkpoint)** — apply any feel retunes as data-only single-constant edits (5.1-06 Task 3 / quick-003 procedure: one commit, coupled pins re-synced, gates re-run; 5.3-05 shows the no-op recording when nothing retunes), then the wrap one-liner + STATE/ROADMAP consumption.

### 2.8 Q8 — Pitfalls (numbered, GUI-side) — see §4 "Pitfalls" below

---

## 3. Design contracts (wiring points, builders, literals, pin lists)

**D1. Wiring (gui_game.py only — 3 surfaces):**
- `_build_engine`: construct `wall_mod.WallSpawner(...)` beside :520-522, seed `wall_mod.wall_seed_from_setup(setup)` (distinct call-string), stow `extras['wall_spawner']`.
- `begin_game` session dict (:405-430): + `'wall_spawner'` key (session-anchored, NEVER module-global / widget state — Pitfall 7/8; anchored copy at :431-432).
- `_respawn_pickup`: wall block appended at the tail (after :1257), single definition: `if engine.finished: return` → spawner None check → `next_wall(...)` → None ⇒ keep-old; wall ⇒ `engine.set_wall` + `pymol_bridge.delete_walls()` + `load_line_wall(...)` + gated DBG trace. NO hook lines at :1160 / :727-732 call sites (both inherit it).
- `_teardown_round` (IF D-WALL-TEARDOWN (b) — my recommendation, see Pitfall 3): one line `pymol_bridge.delete_walls()` beside :1524 (`delete_pickups()`), pattern-delete ⇒ idempotent.

**D2. HUD builders (hud_logic.py, PURE — house TDD):**
- Crash path: ZERO builders (generic `'crashed into %s'` + `debug_event_trace(result=%s)` already cover it).
- `debug_wall_trace(wall_id, p1, p2, new_mol_id, new_centroid, gap, tick=None)` (SRP_DEBUG-only family; exact-string pins in test_hud_content.py; compute inputs unconditionally, gate the log).
- IF D-WALL-HUD flips: `wall_spawn_note()` returning **`'a red wall line spawned - it blocks part of the box'`** — via `_log`, with a new `source.count('wall_spawn_note(') == 1` pin. Default: do not ship.
- FORBIDDEN: any `REFUSE_WALL`-shaped placement taxonomy (two active absence-pins, test_hud_content.py:355 + test_placement.py:234 — walls are NOT placement concerns).

**D3. Help text (help_text.py, PURE + coupled test):**
- `_GAME_HINTS['playing']` → `'Steer with the arrow keys. Red wall lines are obstacles - touching one ends the run. If keys seem dead, click the 3D viewer first.'` (+ same-commit `test_playing` edit). Default recommendation: ship it (one clause); the alternative (no help change) is the fallback if the owner wants the feature fully "hidden".

**D4. New source-scan pins (test_hud_content.py, additive class `TestWallWiring`, 5.3-04 pattern):**
1. `source.count('wall_mod.WallSpawner(') == 1`
2. `source.count('wall_mod.wall_seed_from_setup(') == 1`
3. `source.count('next_wall(') == 1`
4. `engine.finished` guard present inside the `_respawn_pickup` `_method_body` slice
5. teardown line present inside the `_teardown_round` body slice (if (b) teardown)
6. `assertNotIn('min_head_dist_a', source)` already exists blanket (:880-885) — wall kwargs inherit it for free
7. debug-binding discipline pin modeled on TestDebugTailBinding IF any wall debug locals are gated (preferred: none needed)

**D5. Requirement mapping:** route (b) dated amendment on GAME-05 (§2.5), coverage stays 46/46 — owner may override to (a); both edit lists in §2.5 are complete.

**D6. Setup schema:** NO new keys. No merge_defaults / validate / tooltip / collect_state / persistence changes.

---

## 4. Pitfalls (numbered, GUI-side)

1. **Same-tick ordering — wall vs pickup spawn.** The wall swap must be INSIDE `_respawn_pickup`'s success branch (after materialize :1257), never at the call sites. Reason 1: pairing — both `_handle_stack_event`'s tail (:1160) and the cooldown-resume edge (:731-732) route through it; a wall at only one site breaks the owner's "at the same time" mandate on the other. Reason 2: `_respawn_pickup` can fire twice in one tick (capture + resume edge); the `can_spawn` gate (:1222) exits the second run BEFORE the wall seam only if the seam is inside the success branch — a call-site-level wall hook could double-swap.
2. **Pause/auto-pause interplay.** Nothing to build — but do not "fix" the freeze: wall swaps naturally quiesce while paused (timers stopped :1313-1316; `_on_tick` early-returns :691-692), matching the exhaust-cooldown freeze semantics (:721-726). Any wall-clock-timered wall cadence (e.g. "swap every N seconds") would VIOLATE pause-freeze and adds a singleShot/epoch surface — rejected.
3. **Teardown idempotency with a wall alive at run end — a REAL sibling-research CONFLICT, surface at planning.** Engine research D-WALL-TEARDOWN default (a): wall STAYS at completion as scenery (srp_box precedent; purged at next begin_game), so the crash cause stays visible on the final board — zero teardown code. Bridge research (§1.6) recommends (b): walls die in `_teardown_round` beside :1524 (`delete_walls()` — mirrors `delete_pickups()` :409-416 "idempotent. Used by teardown AND by the completion flow"), arguing GAME-09's "the viewer clears" and the locked "live pickups die, chain survives" contract. **My (GUI-side) recommendation: (b) delete at teardown** — (i) completion zooms `zoom_chain('srp_head or srp_seg_*')` (pymol_bridge.py:348) and a red fence crossing the framed payoff scene is visual noise on the screen the owner stares longest at; (ii) GAME-09 criterion text says "the viewer clears"; (iii) one idempotent line, zero maintenance; (iv) the crash evidence (info-box 'crashed into wall' + run-over line) persists in the log, so the crash cause stays auditable without the geometry. The choice is an owner-decision-table item either way — put it on the Task-2 checkpoint sheet.
4. **Reload/double-wiring (Pitfall 7/8 class).** WallSpawner state must live ONLY on the session dict (anchored `_serpentrum.game_session`, :405-432); constructing it in `_build_engine` makes it fresh per run and coincidentally dead on reload. A pre-reload orphan `srp_wall` viewer object survives until the next Start (INFRA-04's cleanup_srp + `.pse` fresh-process recovery cover every `srp_*` — the wall MUST be srp_-prefixed or it escapes cleanup, bridge research §1.4).
5. **DBG binding discipline (33c13e7 regression class).** Debug-gated locals consumed unconditionally once broke non-debug spawning for weeks; pins exist (TestDebugTailBinding). The wall seam must either consume nothing debug-gated or bind unconditionally; never write new `debug_tail`-named locals; `_respawn_pickup` lies outside that test's counted slice (:922-924 spans `_handle_stack_event`→`_dbg_capture_line`; `_respawn_pickup` is at :1205) — keep wall lines there anyway (correct location for other reasons, Pitfall 1).
6. **Epoch guards.** The wall seam is synchronous inside `_on_tick`'s guarded tick (:687-689) — zero new epoch surface as long as NO singleShot/timer ever carries wall work (singleShot chains need `scheduled`-epoch closures, :625-648). A `Restart` during the countdown bumps the epoch and kills stale chains (:1514); the wall inherits the existing session rebuild — no part of Phase 9 may add a second epoch authority.
7. **Win-tick flash.** Without the `if engine.finished: return` guard, a wall materializes on the completion board during the winning capture's `'stacked'` dispatch (probe-verified ordering, engine research §5) and survives (teardown deletes `srp_pickup_*` only). The guard is cheap and pinned (D4-4).
8. **Chattiness-policy + coalescer interplay.** Default play must gain ZERO new info-box lines from walls (byte-identical OFF behavior is the 5.2 OFF-pin sweep discipline); if a wall note IS added via `_log`, each line breaks any in-flight coalesced refuse run (:1541-1544) and wall swaps land exactly during capture resolutions — expect '(xN)' runs to fragment; SILENT default avoids the class entirely.
9. **Vocabulary collision (informational).** hud_logic's defensive `_TURN_REFUSE_WHY['boundary']` uses "walls" for the BOX faces ("walls only stop the head ...", :497-502) — with `srp_wall` in the game the word now has two referents in dead code. Recommended: leave untouched (defensive-only, unreachable, hud_logic.py:514-517) — but if the owner asks for cleanup, update the clause in the SAME commit as a test edit if ever pinned; NOT worth feel-check attention by default.
10. **Naming/selection safety (inherit, don't re-solve).** `srp_wall` is outside every chain wildcard (`'srp_head or srp_seg_*'`, move_chain_delta/sweep_chain/zoom_chain) and CGOs are transform-inert (bridge research §2.5); frame_scene zooms `'srp_*'` but no wall exists at begin_game (first wall = first capture). Pin the begin_game-no-wall invariant implicitly via the s10 integration scenario (first wall appears with mol 2, not at run start).

---

## 5. Docs-impact verdict (one line)

**Authoritative:** README + check_docs.py + test_docs_audit.py + DATA_SOURCES.md stay GREEN and UNTOUCHED (no pinned claim covers walls; no joiner files affected); no doc-update plan is required under the owner's "only if docs are actually affected" directive; the only user-visible text change (if any) is the help_text `playing`-hint clause, which ships inside the gui-wiring plan with its coupled `test_help_text.py::test_playing` edit — planning-ledger/ROADMAP/STATE updates are ordinary phase-close bookkeeping (route (a)/(b) per §2.5).

---

## 6. Open owner decisions (to put in front of the owner — planning/checkpoint sheet)

1. **D-MAP** — requirement mapping: dated GAME-05 amendment (recommended, coverage 46/46) vs mint GAME-12 (47/47; 4-file lockstep edit list provided). ROADMAP explicitly defers this to planning.
2. **D-WALL-TEARDOWN** — wall at completion: delete in `_teardown_round` (my + bridge recommendation) vs keep as scenery (engine research default). Pitfall 3.
3. **D-WALL-HUD** — info-box line on wall spawn: SILENT (recommended default) vs one `wall_spawn_note()` line (literal proposed in §2.2).
4. **D-WALL-HELP** — the `playing`-hint clause: ship the proposed one-clause wording (recommended, DOCS-03 "clear but sufficient") vs keep help text untouched (fully "hidden").
5. **D-WALL-SETUP** — Setup knob: none (recommended, §2.6) vs off/density toggle (additive follow-up possible later).
6. The engine research's own decision table (D-WALL-SCOPE … D-WALL-RADIUS, its §3) — feel numbers to bless/retune at the closing checkpoint (§2.7 Task 2 step 7).

---

## 7. What plans must NOT break (suites that must stay green UNMODIFIED)

**Zero-edit constraint (any Phase-9 plan):**

| Suite / file | Why it must stay green unmodified |
|---|---|
| `tests/test_spawn.py` (41) | `spawn.py` is byte-identical under the separate wall RNG stream (engine research C5/C7); zero wall surface |
| `tests/test_engine_core.py` (17), `test_engine_rules.py` (28), `test_engine_turns.py`, `test_engine_turn_veto_ghost.py`, `test_engine_tail_follow.py`, `test_engine_speed.py`, `test_engine_win_desync.py` | `wall=None` default ⇒ pre-Phase-9 behavior byte-identical; engine wall tests go in the NEW `test_engine_wall.py` (house style) |
| `tests/test_hud_logic.py` (13) | hud_logic's wall additions (DBG builder) are additive constants/classes; existing pins untouched |
| `tests/test_gui_pins.py` (19) | presence-type + repo-wide ban scans only; additive lines safe |
| `tests/test_docs_audit.py` (23) | no README/check_docs edit in scope (§2.4) |
| `tests/test_audit_requirements.py` (16) | route (b) touches neither list; route (a) touches both lists SAME-COMMIT (lockstep) |
| `tests/test_phase5_integration.py` s1–s9 | additive s10 only (+ docstring scenario line) |
| `test_phase51_integration.py`, `test_phase52_integration.py` | derive from tables; zero wall surface |
| `smoke/01..14` + `tests/run_gates.py` registry except the one append hunk | smokes untouched; smoke 15 is an ADDITIVE registered smoke (bridge plan owns it) |

**Within-file additive disciplines (verified safe, do not violate):** test_hud_content.py existing classes untouched (new `TestWall*` classes appended); `TestDebugTailBinding` slice counts (2× `debug_tail = None`, 2× `if debug_tail is not None:`) unchanged; one-call-site counts for `stack_mode_note(`/`generic_consent_note(`/`speed_note(` stay at 1; `spawn_mod.PickupSpawner(`/`spawner.first(`/`spawner.next_after(`/`spawn_mod.seed_from_setup(` stay at 1 each; NO `min_head_dist_a` anywhere in gui_game.py; `_heading_name(engine.heading)` kept (:887-892); NO `REFUSE_WALL` in placement (`test_hud_content.py:355`, `test_placement.py:234`); help-text edits coupled same-commit; no `__init__.py` in tests/smoke/tools; no top-level root `*.py`; python3.6 %-formatting; `srp_` prefix on the wall object; no `.exec_()`.

---

## 8. Metadata

**Confidence breakdown:**
- GUI wiring map (Q1): HIGH — every call site + line number read from live source; both respawn call sites + guard semantics verified.
- HUD wording/pins (Q2): HIGH — all literals quoted verbatim; pin lines enumerated from the test files; baselines re-run green.
- Help text (Q3): HIGH — module + tests read fully; check_docs families enumerated from source.
- Docs verdict (Q4): HIGH — 7 families read; README fully read; zero wall interaction proven by enumeration.
- Requirement mapping (Q5): HIGH — tool + test read line-by-line; both precedents quoted; the only judgment call (route (a) vs (b)) is flagged as an owner decision with a recommendation.
- Setup toggle (Q6): HIGH on facts (5.3 precedent + schema mechanics); MEDIUM on the verdict itself (owner preference).
- Feel-check design (Q7): HIGH — three SUMMARY structures read; the one-blocking-checkpoint convention verified across 7 phase closes.
- Pitfalls (Q8): HIGH on mechanics; the teardown conflict is honestly a DISAGREEMENT between sibling researches — surfaced with a recommendation.

**Research date:** 2026-10-12
**Valid until:** stable repo state; re-verify line numbers only if gui_game.py/hud_logic.py/help_text.py move before planning lands.
