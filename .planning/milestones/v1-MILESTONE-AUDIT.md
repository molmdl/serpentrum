---
milestone: v1
audited: 2026-10-18 (UTC)
status: passed
scores:
  requirements: 46/46
  phases: 13/13
  integration: 8/8
  flows: 6/6
gaps:  # Critical blockers
  requirements: []
  integration: []
  flows: []
tech_debt:  # Non-critical, deferred — full detail in report §8
  - phase: 01-plugin-skeleton-purity-harness
    items:
      - "Accepted disposition: smoke/02_dialog_smoke.py stays an informational FAIL (the 01-05 offscreen-Qt dead end) — documented, never retried"
  - phase: 5.3-randomized-pickup-spawning
    items:
      - "Parked candidate (owner-deferred; sketch in 5.3-05-SUMMARY.md): edge-biased pickup spawn distribution near box walls"
  - phase: 07-spectra-ui
    items:
      - "Accepted limitation (owner-approved with visible): Selector-Error zoom noise when zoom_mode_frame fires before arrows exist; benign Qt DPI warning on first show"
      - "Accepted fixture limitations: no CO2 g98 fixture (linear g98 table/vector leg smoke-only behind real --xtb runs); zero-intensity display coverage unit-level; g98≡xtbopt overlay generality = one fixture + always-on smoke 13 assertion"
      - "Parked candidate (owner declined): optional guidance line for small (<20i) imaginary frequencies in the Spectra log"
      - "Owner flag 2026-10-10 (open, scope undefined until pickup): fix the IR intensity plot title later"
  - phase: 9.1-accumulating-line-walls
    items:
      - "Parked follow-up (owner-floated at 9.1-09, needs owner GO): raise the wall-count cap on bigger boxes (per-box-preset cap = new engine/spawner ctor scope)"
      - "Advisory note (owner played live and approved as shipped): 9.1-01 Monte-Carlo probe measured the draft constants RED on small ±35 late-game; the None-keeps-set single-wall degradation is designed benign behavior"
  - phase: milestone-docs (bookkeeping — not shipped code)
    items:
      - "ROADMAP.md plan-checkbox rows stale for Phases 5.2 / 6 / 8 (all three phases verified COMPLETE; plan rows unchecked)"
      - "STATE.md velocity line (114) vs Progress line (127 of 127) — Phase-8 plans not folded into the velocity count"
      - "Stale docstring serpentrum/pymol_bridge.py:244-246 claims 'true randomization is game-start, Phase 4' — contradicts the 08-09 honesty fix; cosmetic doc drift, zero wiring impact"
---

# v1 Milestone Audit — serpentrum

**Milestone:** v1 (the playable, spectra-complete, human-certified release + the two post-v1 gameplay refinements appended under the same milestone umbrella)
**Audited:** 2026-10-18 (UTC), repo HEAD 0ec1ea6, tree clean
**Status:** **passed** — all requirements met, all phases verified, cross-phase integration verified, E2E flows complete; remaining items are owner-accepted limitations, parked-by-design candidates awaiting owner GO, and docs-only bookkeeping (§8). No critical gaps, no blockers.

**Core value delivered:** Playing snake by stacking real molecules with known stacking geometry, then seeing the IR spectrum of the molecule you assembled, computed end-to-end inside PyMOL via xtb.

## 1. Milestone Scope

- **13 phase directories**, all plans closed: Phases 1–9 + inserted 5.1 / 5.2 / 5.3 / 9.1 = **127/127 plans complete**.
- **v1 release record:** GATE V (08-11) owner verdict "approved" 2026-10-10 (UTC) across Sections A (data sign-off) / B (6-button + educator round-trip) / C (release close incl. real xtb); 46/46 requirements flipped Complete; DATA_SOURCES.md APPROVED (3fd30cf).
- **Post-v1 gameplay refinements** inside this milestone audit: Phase 9 (Random Line-Wall Spawning, COMPLETE+VERIFIED 2026-10-13) and Phase 9.1 (Accumulating Line-Walls, COMPLETE+VERIFIED 2026-10-17) — both shipped as dated route-(b) GAME-05 amendments (4c4e538, then supersede 757e849); coverage stays 46/46 with the audit tooling byte-untouched.
- **Definition of done** (ROADMAP Phase 8 / DOCS-05): the full flow (setup → play → complete → xtb → IR plot → save) passes headless with human checkpoints, and all v1 requirements are checked off with complete traceability — **achieved and re-attested below**.

## 2. Method

1. Read all 13 `*-VERIFICATION.md` files; extracted status, scores, critical gaps, anti-patterns, and requirements coverage per phase (§4).
2. Aggregated tech debt and deferred items from VERIFICATIONs + STATE.md Pending Todos (§8). No phase is unverified (13/13 VERIFICATION.md present — no "unverified phase" blockers).
3. Spawned an independent **gsd-integration-checker** agent for cross-phase wiring + E2E flows (seams ≥2 phases apart, which per-phase verifications do not own) — verdict in §6.
4. Re-ran the fast WSL battery **twice, independently** (orchestrator + integration checker), both on current HEAD — §3.
5. Requirements coverage cross-checked against REQUIREMENTS.md's traceability table + the live `--release` audit (§5).

## 3. Live Evidence at Audit Time (re-run on current HEAD 0ec1ea6)

| Check | Run 1 (orchestrator) | Run 2 (integration checker) | Agreement |
|---|---|---|---|
| `python3.6 tests/run_gates.py` (gates 1-3) | **Ran 1084 tests … OK**; 3/3 gates PASS; "run_gates: all gates green" | **Ran 1084 tests (5.65s) OK**; 3/3 gates PASS | ✓ |
| `python3.6 tools/check_docs.py` | **7/7 checks PASS** (vibe-block, placeholders, 20 control literals, 26 numeric tokens, install-recipe, path-refs, claim-bans) | **7/7 checks PASS** | ✓ |
| `python3.6 tools/audit_requirements.py --release` | **AUDIT-OK** — 46 IDs unique, 46-row table, 136 evidence paths exist, checkbox↔table agree, zero Pending | **AUDIT-OK** | ✓ |
| Windows legs (`--smoke` 12/12 required smokes incl. `SMOKE-OK LINE-WALL` + RELEASE-E2E; `--xtb` `normal termination of xtb`) | cited evidence (9.1-VERIFICATION 2026-10-17, re-run live then) | cited evidence — verified the 3 commits after it are docs/chore-only (384e95e README+screenshots w/ doc gates re-verified green, fe82b24 STATE, 0ec1ea6 oc-stats) | ✓ |

Exec last changed at the 9.1 close; everything since HEAD→b959820..0ec1ea6 is docs/chore-only, so the 9.1-VERIFICATION live Windows battery remains valid for current HEAD.

## 4. Phase Verification Summary (13/13 passed — zero critical gaps in any phase)

| Phase (dir date = plan set) | Score | Gaps | Verified |
|---|---|---|---|
| 01 Plugin Skeleton & Purity Harness | 5/5 SC (+ plan truths) | none | 2026-09-06 |
| 02 Pure Core — Game & Chemistry Logic | 4/4 SC (383 tests) | none | 2026-09-10 |
| 03 Molecules in the Viewer & Setup Tab | 5/5 SC + 32/32 plan truths | none | 2026-09-12 |
| 04 Game Loop & Input | 40/40 (5/5 SC + 35/35) | none | 2026-09-14 |
| 05 Stacking & Game Rules Complete | 48/48 truths + 5/5 SC (3 owner-amended, verified as replacement contract) | none | 2026-09-20 (re-verified) |
| 5.1 Game Speed / Difficulty | 17/17 (3 value-only owner amendments; quick-003 retune landed 2026-10-11) | none | 2026-09-24/25 |
| 5.2 Generic Upload Stacking Consent | 5/5 SCs | none | 2026-09-26 |
| 5.3 Randomized Pickup Spawning | 5/5 | none | 2026-09-26 |
| 06 xtb Pipeline | 5/5 SCs | none | 2026-09-26 |
| 07 Spectra UI | 38/38 truths + 3/3 SCs | none | 2026-09-27 |
| 08 Demo Data, Docs & Release Audit | 162/162 must-haves + 5/5 SCs — GATE V v1 release sign-off | none | 2026-10-10 |
| 09 Random Line-Wall Spawning | 36/36 + 7/7 SCs (1 sanctioned retune 12→8 Å) | none | 2026-10-14 |
| 9.1 Accumulating Line-Walls | 78/78 + 8/8 SCs (constants approved as shipped 5/0.35/8.0) | none | 2026-10-17 |

Every phase closed all blocking human checkpoints with recorded owner verbatim verdicts (install, keys, feel-checks, GATE D, GATE V…). No outstanding human verification anywhere.

## 5. Requirements Coverage — 46/46

All 46 v1 requirements are **Complete**, mechanically attested at audit time (`--release` AUDIT-OK: ids-unique, 46-row table, **136 evidence paths exist**, checkbox↔table agreement, zero Pending) and human-certified at GATE V. Full per-ID evidence ledger: `REQUIREMENTS.md` traceability table (not duplicated here).

| Category | IDs | Owning phases | Status |
|---|---|---|---|
| Setup & Configuration | SETUP-01..08 (8) | 1, 3, 8 | 8/8 Complete |
| Gameplay | GAME-01..11 (11) | 4, 5, 5.1 (+9/9.1 amendments) | 11/11 Complete |
| Molecular Stacking | STACK-01..06 (6) | 2, 5, 5.2 | 6/6 Complete |
| Spectra | SPECTRA-01..06 (6) | 7, 6 | 6/6 Complete |
| Demo Data & Attribution | DATA-01..04 (4) | 8, 3 | 4/4 Complete |
| Infrastructure & Environment | INFRA-01..06 (6) | 1, 3 | 6/6 Complete |
| Documentation & Audit | DOCS-01..05 (5) | 8 | 5/5 Complete |

**Amendment lineage (fully documented, coverage unchanged):** GAME-10 shipped owner-amended (train-follow rigid sweep, 180°-only veto, 2026-09-20); GAME-11 values retuned twice by owner authority (5.1-06 → quick-003; final 6.0/9.0 default/11.0/13.0 A/s); GAME-05 carries two dated route-(b) amendments (Phase 9 wall class; Phase 9.1 supersede — accumulated walls under cap 5); STACK-06 promoted v2→v1 (5.2). No invented chemistry anywhere — every shipped distance is the human-approved 3.60 Å @ 20° Janiak/COD-pinned geometry; biphenyl remains the designed REFUSE_ATOM demonstrator.

## 6. Integration Check (gsd-integration-checker, 2026-10-18) — 8/8 seams WIRED, 0 gaps

| Seam | Verdict | Key evidence (file:line) |
|---|---|---|
| W1 Setup keys → downstream consumers (speed/cap/budget/threads/box/consent/fwhm) | WIRED | single injection gui_game.py:558; launch guard gui.py:433-439 → budget_guard.py:65-139; thread_arg gui.py:487-489 → xtb_run.py:84-97; consent overlay gui_setup.py:886-944 → restamp gui_game.py:1032-1033; fwhm live-read gui_spectra.py:352-356 |
| W2 Phase-8 button row ↔ earlier seams | WIRED | 6 buttons gui.py:175-200; Start = apply-first gui_setup.py:1047-1048 → the single setCurrentIndex(1); Load chain gui_setup.py:812-840; Cleanup = cleanup_srp only; Randomize preserves consent/budget/threads (setup_logic.py:457-466) |
| W3 Money chain 05→06→07 (completion→xyz→guard→xtb→record→plot→table→vectors→PNG) | WIRED | _present_completion gui_game.py:1530-1543; _on_spectra_requested gui.py:366-454 (head-inclusive counts); xtb_runner.py:284-341 single terminal branch; _refresh_from_record gui_spectra.py:282-362; row-click vectors :413-497 (snake_id latch, delete-then-load); Get Spectra re-arms on every terminal branch |
| W4 Walls (09/9.1) vs everything | WIRED | seam in _respawn_pickup success tail gui_game.py:1278-1328 (finished guard :1287; ordinal=len(walls)+1 :1307; viewer-write-before-commit :1313-1316); sole delete site _teardown_round :1596; cleanup_srp covers srp_wall_<n> fresh-process (INFRA-04; smoke/15 STAGE6) |
| W5 Single completion path (GAME-09) | WIRED | boundary/wall/body/won all funnel to the one `_end_run` (gui_game.py:755 sole call) → _teardown_round → _present_completion; bool bottom-row Start resets via begin_game teardown-first |
| W6 Module identity + purity | WIRED | 7 live fields on pmg_tk.startup._serpentrum (__init__.py:22-62); controllers on anchor, never module globals; zero `.exec_()` in serpentrum/; gate 2 PASS live |
| W7 Docs ↔ code | WIRED | SPEED_TIERS 6.0/9.0/11.0/13.0 == help_text.py:117-119; consent label == generic_stack.py:46; wall constants as shipped; README Start-only usage == the one Start route; check_docs 7/7 live |
| W8 Planning bookkeeping (ROADMAP checkboxes 5.2/6/8) | STALE — not a gap | phase headers [x] + VERIFICATIONs passed + all plan SUMMARYs exist; checkbox rows only — docs bookkeeping (§8) |

**Extra broken seams found: none.** Three benign observations (by-design or cosmetic): ① stale docstring pymol_bridge.py:244-246 (docs item, §8); ② plugin reload with a terminal record keeps Get Spectra disabled until the next completion — the presenter-only-enable contract, Run-again still re-enters the full pipeline; ③ a final pickup may materialize on the win tick before teardown — invisible, removed by delete_pickups :1595.

### E2E Flows — 6/6 COMPLETE

| Flow | Verdict |
|---|---|
| A — Money flow: install → Setup config → Start → countdown → play → capture/stack (3.60 Å DBG) → win at cap → Get Spectra → async xtb + live log → plot + table + row-click vectors → Save Plot PNG | **COMPLETE** (mechanical proof: smoke/14 RELEASE-E2E in REQUIRED_SMOKES) |
| B — Crash endings (boundary / body / accumulated wall): snake still complete → Get Spectra armed → spectra reachable identically | **COMPLETE** |
| C — SETUP-08 educator round-trip: Save → Load fresh session reproduces exact config; absent-key backcompat (pre-5.1/5.2 files → default tier / consent OFF) | **COMPLETE** (smoke/14 STAGE7) |
| D — Uploads: >3-ring rejected with reason; consent ON + planar 6-ring → labeled generic π-stack (upload-only winnable); ringless → specific skip; consent OFF → byte-identical legacy skip | **COMPLETE** |
| E — Hygiene: mid-run Restart; Cleanup model in-session + fresh .pse (incl. srp_wall_* indexed family); completion-view teardown | **COMPLETE** |
| F — Environment contract: gates green in WSL; smoke/14 + smoke/15 registered REQUIRED; --xtb gate asserts normal termination | **COMPLETE** |

## 7. Anti-Pattern Sweep

Clean. Zero live TODO/FIXME/XXX/HACK in `serpentrum/` production code; all "placeholder"/"stub" hits are historical docstrings or deliberate checker-fixture literals; zero `.exec_()` repo-wide in shipped plugin code; no empty handlers; smoke/02 informational FAIL is the documented dead-end exception. (Per anti-pattern line items in all 13 VERIFICATIONs + the integration checker's independent sweep.)

## 8. Tech Debt & Deferred Items (all non-blocking; each with recorded disposition)

| Item | Class | Owner disposition |
|---|---|---|
| smoke/02 informational FAIL (offscreen-Qt dead end) | accepted | documented 01-05; never retried |
| Selector-Error zoom noise + Qt DPI warning | deferred cosmetic | owner-approved with it visible (07-10) |
| No CO2 g98 fixture / unit-level zero-intensity / one-fixture g98≡xtbopt | accepted fixture limitation | 07-VERIFICATION Accepted Limitations |
| Small-imaginary (<20i) guidance line | parked candidate | owner declined at Phase 8 (GATE D two-tier wording shipped instead) |
| Edge-biased pickup spawn distribution | parked candidate | owner-deferred at 5.3-05 ("mark it and move on"); sketch on file |
| IR intensity plot title fix | open owner flag | "fix later" (2026-10-10); scope undefined until pickup |
| Bigger-box wall-count cap | open candidate (needs owner GO) | floated at 9.1-09; per-preset cap = new ctor scope; probe sizing on file |
| 9.1 probe RED-on-small verdict | advisory note | owner played live + approved as shipped; designed benign degradation |
| ROADMAP plan-checkbox staleness (5.2/6/8) + STATE velocity count (114 vs 127) | docs bookkeeping | fixable at milestone close; zero code impact |
| pymol_bridge.py:246 stale docstring | cosmetic doc drift | one-line fix; zero wiring impact |

**Nothing here blocks completion.** The code debt list is empty; every item above is either owner-accepted, parked pending an owner decision, or docs-only bookkeeping.

## 9. Milestone DoD Check

| # | Definition of done | Verdict |
|---|---|---|
| 1 | All 46 v1 requirements Complete with traceability | ✓ AUDIT-OK live at audit time; 136 evidence paths exist; human-certified GATE V |
| 2 | All phases verified, zero critical gaps | ✓ 13/13 VERIFICATION.md, status passed |
| 3 | E2E flow headless + human checkpoints (DOCS-05) | ✓ smoke/14 RELEASE-E2E required + GATE V Section C live incl. real xtb |
| 4 | Cross-phase integration sound | ✓ 8/8 seams WIRED (integration checker), 0 gaps |
| 5 | E2E user journeys complete | ✓ 6/6 flows COMPLETE |
| 6 | Release record intact through post-v1 phases | ✓ GATE V record closed; 9/9.1 shipped as dated GAME-05 amendments; coverage 46/46 unchanged; audit tooling byte-untouched |
| 7 | Gates green at audit time | ✓ 1084 tests + 3 gates + docs 7/7 + audit OK, re-run twice on HEAD |

## 10. Verdict

**PASS.** The v1 milestone — 13 phases, 127 plans, 46/46 requirements — is achieved, verified, integrated, and human-certified. Ready for archive/tag via `/gsd-complete-milestone v1`.

---
*Audit executed by the /gsd-audit-milestone orchestrator (OpenCode) with the gsd-integration-checker subagent, 2026-10-18 (UTC).*
*Evidence basis: 13 phase VERIFICATION.md files, REQUIREMENTS.md traceability ledger, live gate battery (×2), independent cross-phase audit with file:line citations.*
