# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-09-06)

**Core value:** Playing snake by stacking real molecules with known stacking geometry, then seeing the IR spectrum of the molecule you assembled, computed end-to-end inside PyMOL via xtb.
**Current focus:** Phase 5 COMPLETE (verified 2026-09-20) — next: Phase 5.2 Generic Upload Stacking Consent (STACK-06 promoted v2->v1, owner chose plan-first), then Phase 5.1 (GAME-11 speed tiers); execute 5.2 -> 5.1 sequentially (shared gui_setup/hud_logic files)

## Current Position

Phase: 5 of 8 (Stacking & Game Rules Complete) — COMPLETE + VERIFIED
Plan: 16 of 16 complete (05-01..05-16); 05-VERIFICATION.md: **passed** (48/48 plan must-have truths, 3 verified-as-owner-amended; 5/5 success criteria; 9/9 requirements; 7-round human checkpoint 2026-09-18..20)
Status: Phase 5 shipped contract = owner-amended (180-only turn veto, REFUSE_WALL removed, train-follow tail @3.60 A immutable, cooldown spawn, restart hygiene, upload skip parity + demo-mode note, recap taxonomy); gates at wrap: 640 unittests, 7/7 required smokes; REQUIREMENTS GAME-04/05/06/09/10 + STACK-01/03/04/05 -> Complete
Last activity: 2026-09-20 — 05-16 checkpoint approved by evidence (2 final-pass tests) -> SUMMARY b0ed958 -> gsd-verifier passed -> wrap-up commit (Phase 5 complete)

Progress: [█████████░] ~85% (53 plans executed — Phases 1-5 COMPLETE at 6+14+8+9+16; Phase 5.1 inserted (TBD ~2-3); Phases 6-8 TBD ~8-11; possible Phase 5.2 pending owner decision on generic upload stacking)

## Performance Metrics

**Velocity:**
- Total plans completed: 53
- Total execution time: ~640 executor min (Phase 1: 104; Phase 2: ~330; Phase 3: ~165 incl. smoke-04/fix/measure follow-up agents + verifier; Phase 4: ~41 incl. waves 1-2 + 04-06..04-09)

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1. Plugin Skeleton & Purity Harness | 6/6 | 104 min | 17 min |
| 2. Pure Core — Game & Chemistry Logic | 14/14 | ~330 min | ~24 min |
| 3. Molecules in the Viewer & Setup Tab | 8/8 | ~165 min | ~21 min |
| 4. Game Loop & Input | 9/9 | ~41 min (waves 1-2 merged by orchestrator; 04-06 = 7 min, 04-07 = ~5 min finalization, 04-08 = 6 min direct on main, 04-09 = ~15 min clean gate pass + checkpoint finalization) | ~4.6 min |
| 5. Stacking & Game Rules Complete | 16/16 | waves 1-6 via worktree protocol (batch-capped at 4 parallel) + wave 7 checkpoint still open; live-checkpoint fixes 2026-09-18/19 (perpendicular, tracer, ghost-point, owner overrides) | — not yet aggregated — |

**Recent Trend:**
- Phase 3: 03-01 (7 min), 03-02 (22), 03-03 (~15 incl. respawn after /home-symlink permission rejection), 03-04 (10), 03-05 (~8, single-plan direct on main), 03-06 (~25, Windows smokes), 03-07 (20), 03-08 (35 + 3 follow-up agents ~25)
- Phase 4: 04-06 (7), 04-07 (~5 finalization), 04-08 (6), 04-09 (~15 clean gate pass + human-verify 12/12 APPROVED, zero fixes)
- Trend: single-plan waves ran directly on main (no worktree) per protocol; the /mnt/c path guard (never /home/lwng symlink) eliminated the permission-rejection failure class

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Locked 2026-09-06: 2D plane + locked camera; constant speed; rigid chain pivot turns (GAME-10 — sweep refused on collision, no 180°)
- Locked 2026-09-06: Demo Set A only (π-stack); distances pinned at data-prep + human approval; refuse-and-skip fallback (STACK-03)
- Locked 2026-09-06: `xtb --ohess` (never `-o --hess`); broadened IR; static mode vectors; 6 buttons; crash still completes → spectra
- Roadmap 2026-09-06: Phase 6 (xtb pipeline) depends only on Phase 2 — run parallel with Phases 3–5; worktree protocol for concurrent plans
- 01-01 2026-09-06: Anchor live state on `pmg_tk.startup._serpentrum` — survives Plugin-Manager reload + double import (Pitfall 7); never module globals
- 01-03 2026-09-06: Purity gate is AST-based; GUI allowlist accepts only `pymol.Qt`/`pymol.Qt.*`; extend classes deliberately, everything else defaults PURE
- 01-05 2026-09-06: Offscreen Qt route is a DEAD END (dialog construction kills the process silently) — do NOT retry; dialog verdicts stay human-verify
- 01-06 2026-09-06: Reload phrasing: "restart PyMOL OR re-add the plugin directory in Plugin Manager"
- Phase 2 2026-09-10: π-stack APPROVED (DATA-02, human option-a): 3.60 Å centroid-centroid @ 20° off-normal, encoded distance_a 3.383 / lateral_offset_a 1.231; dataset file is the shipping contract; DATA_SOURCES.md stays DRAFT-headed (full sign-off Phase 8)
- Phase 2 2026-09-10: Engine referee event order moved→boundary→body→stacked→won; body = head-centroid vs polyline edges (skip newest 2), strict < 2.0 Å; GAME-10 sweeps 90°/6 ticks, newest-wins, pickup leg 2.5 Å
- Phase 2 2026-09-10: Worktree protocol proven at scale; executors skip STATE.md during parallel waves (orchestrator-owned)
- 03-01 2026-09-11: BRIDGE purity class live — `serpentrum/pymol_bridge.py` may import pymol/pmg_tk at ANY level; PyQt5/numpy banned there at any level; .exec_() banned (bridge builds no dialogs); `serpentrum/gui_setup.py` added to GUI_MODULES
- 03-02 2026-09-11: molfile — ring count = cyclomatic mu = E−V+C (stdlib BFS); SDF M CHG formal charges summed; mol2 = partial charges only → charge 0 + warning; gate order rings→explicit-H→inorganic-advisory, charge never rejects; write_sdf_text round-trip enables the upload split; MolFileError mirrors xyzio line+snippet contract
- 03-03 2026-09-11: `setup_logic._xtb_path_problems` delegates to `xtbenv.validate_binary_path` — single source of the rules; messages byte-identical (existing matrix green unmodified)
- 03-04 2026-09-11: `'__upload__'` sentinel is the skip-policy keying (uploaded molecules NEVER inherit set_a's stacking entry); demo load cross-verifies manifest atom_count/charge/ring_count against parsed reality (mismatch → exclude + error); multi-record uploads split via write_sdf_text into `srp_upload_*` tempdirs
- 03-05 2026-09-11: Demo Set A shipped — human-placed PubChem 3D SDFs (CIDs 241/931/8418/995/7095), manifest built by tools/build_demo_manifest.py from parsed reality (abort on mismatch); ring_atoms = full 2-core via find_ring_atoms — **Phase 5 must extract ONE planar 6-ring in ring order before stacking.ring_frame (biphenyl's twisted 2-core would fail the 0.15 Å planarity check)**
- 03-06 2026-09-12: `cmd.get_names('public_objects')` is the proven 2.5.0 type ('all_objects' raises); `cmd.get_extent` returns `[[minx,miny,minz],[maxx,maxy,maxz]]` (nested lists); materialize ALWAYS cleanup_srp() first → unknown head id = box-only scene (srp_head absent, not stale); BOX_DISPLAY_Z 5.0; camera = one-shot cmd.zoom('srp_*') only, NEVER ortho/set_view (Phase 4 owns GAME-02)
- 03-07 2026-09-12: setup dict's demo_set holds only KNOWN_SETS values ('__upload__' is UI-routing truth only — collect_state maps it to the last real set); hessian warning = inline QLabel shown on cap > 10 (valueChanged + apply_state); xtb detect is advisory in Phase 3; setup dict anchored on `_serpentrum.setup` (initialized on FIRST anchor creation only — reload must not reset it)
- 03-08 2026-09-12: xtb detect result surfaces IMMEDIATELY on auto-detect toggle (root cause of "status shows ready": toggle path had no detect surfacing, not a signal storm — head-combo already blockSignals'd); box linewidth 3.0; **human-verify APPROVED (10/10 steps, real Windows PyMOL, two rounds)** [SETUP-02..06, DATA-03, INFRA-04 delivered]
- 03-08 2026-09-12: **Stack presentation for Phase 5 (human-confirmed): molecule ring planes EDGE-ON (perpendicular to screen/xy) so the π-stack normal lies IN the movement plane — stacks grow along x/y, every layer visible to the locked camera.** Measured from shipped SDFs: max diameter = anthracene 9.526 Å (phenanthrene 9.296, biphenyl 9.198, naphthalene 7.187, benzene 4.962); 2·BOX_DISPLAY_Z = 10.0 Å ≥ 9.526 fits worst-case with 0.474 Å slack (no margin); Option B (BOX_DISPLAY_Z 6.0 = +2 Å margin) recorded in 03-08-SUMMARY.md — decide at Phase 5 planning
- 04-07 2026-09-13: Keys checkpoint APPROVED — KeySteerWizard do_special route is the shipping input route (no gui_input.py fallback); click-viewer-to-steer UX accepted for v1 (auto-pause = 04-08 safety net); harness False-flood explained (no-tick buffer-full refusals are correct engine authority)
- 04-08 2026-09-13: Play lifecycle wiring locked — camera lock + wizard install arm BEFORE timers at GO! (gameloop Q6); _teardown_round is THE single teardown on every end path (Pitfall 9.2, idempotent, saved_cam popped); pause keeps wizard installed (set_active grab-and-no-op) AND camera locked (D5); request_auto_pause guards status=='playing' (focusInEvent fires on Start click too); Phase 5 adds pickup teardown INTO _teardown_round, never a second helper
- 04-06 2026-09-13: Start flow = HUD research Q1 model A — SetupTab emits `start_requested(setup)`, PluginDialog owns `setCurrentIndex(1)` (self.tabs lives there; GameTab never reaches up to its parent QTabWidget); Start applies FIRST (`_on_apply` bool contract — False on all three modal paths suppresses the emit) so GAME-01 always plays on a materialized scene; temp Start lives in the Setup-tab btn_row (Phase-3 precedent), Phase-8 bottom row byte-identical
- 04-09 2026-09-14: Phase-4 closing APPROVED (12/12 live + gates green). Observations recorded: wall-crossing ~6 s on medium (plan estimate miscalibrated, speed correct); turn applies at the next 100 ms tick (designed; <1 s perceived latency — potential future game-feel tuning knob, NOT a defect; GAME-08 speed stays locked)
- 2026-09-11: Agent path discipline — ALL agent work uses /mnt/c/Users/nglok/Desktop/WORKDIR/molmdl/serpentrum (the /home/lwng/... symlink view triggered permission rejections twice); single-plan waves run directly on main (no worktree)
- **2026-09-19 (owner directives, override part of locked 2026-09-06 GAME-10 line during 05-16 live checkpoint):** (a) TRAIN-FOLLOW TAIL — engine.segments were stationary-per-tick by design (the tail stayed glued at capture points, gap grew 0.3 Å/tick; measured head↔newest 13.001 Å after capture 2 verbatim-matching the user report); now the chain translates rigidly with the head every 'moved' tick via _translate_chain + bridge move_chain_delta (srp_head or srp_seg_*, camera=0); the approved 3.60 Å spacing is unchanged — head↔Nth eaten = 3.6×N Å forever; straight-motion body-collision pins rewritten (train-follow makes head-approach-chain unreachable; crash now = already-overlapping pose tick-1 + sweep-time veto). (b) HEAD-ONLY WALL VETO — boundary leg removed from _sweep_check_safe; the CHAIN may visually swing past the box during a turn (accepted); body + pickup legs still refuse; 180° remains impossible; head-wall crash still ends the run (GAME-05 intact); refusal text updated; yesterday's ghost test rewritten so the same user state now ALLOWS the turn. (c) BOX PRESETS — small ±20 (was ±12), medium ±30 (was ±18, still default), large ±45 (was ±25); BOX_DISPLAY_Z=5.0 unchanged; straight-fit: medium now fits ~16 straight segments (cap-10 comfortable — was only 9)
- **2026-09-19b (owner directives, 05-16 re-test round 2 — completes the override of the locked 2026-09-06 GAME-10 line):** (a) TURN VETO = 180° ONLY — the perpendicular body/pickup sweep pre-check (`_sweep_check_safe`) is deleted entirely (`SWEEP_PICKUP_CLEARANCE_A` retired); every non-backward arrow always turns; the chain may visually swing through body/pickups/walls during a sweep (owner: a silly outcome is recoverable, a frozen snake is not); straight-motion GAME-05 crash rules untouched. (b) REFUSED PICKUPS DESPAWN on rejection + spawn DEMOTE-after-refuse (round-robin to back; never permanent exclusion — pool 5 vs cap 10 needs repeats; consecutive refuses ≥ pool size latches pool_exhausted for the run, DBG-only) + HUD ReasonCoalescer `(xN)` anti-spam (fixes the 18× biphenyl REFUSE_WALL cascade + refusal storms). (c) RESTART HYGIENE — gui_game.rebuild_scene runs cleanup_srp (ALL srp_*) BEFORE materializing the new run (old-run srp_seg_* rode move_chain_delta's `srp_head or srp_seg_*` wildcard); completion-view persistence stays completion→Get-Spectra-only. (d) BOX PRESETS for cap-10: small ±35 (18 straight segments), medium ±55 (30 segs, 3× comfortable, default), large ±85 (46 segs); BOX_DISPLAY_Z 5.0 unchanged (biphenyl REFUSE_WALL stays the designed demonstrator). Gameplay overrides are the REPLACEMENT GAME-10 contract for phase wrap-up; REQUIREMENTS note due at phase completion.
- **2026-09-19c (game-3 deadlock fix, 05-16 re-test round 3):** pool_exhausted permanent latch (from f211d97) REPLACED with a resumable cooldown — REFUSE_WALL storms near small-box walls are position-dependent (drive away and placements succeed); streak==pool size now PAUSES spawning for EXHAUST_COOLDOWN_TICKS=100 ticks (~10 s, tunable via constructor kwarg), streak resets on the resume edge and on any successful placement; DBG lines only (`spawn pool cooldown ... paused` / `cooldown over ... resumed`); pause freezes during wall-clock game pause. REFUSE_WALL/REFUSE_ATOM gate tolerances unchanged. (ee2a1d8/6b3017a/415cf50; games 1-2 of round-3 APPROVED: cap-10 win on medium smooth, small-box deliberate crash + clean restart)
- **2026-09-20 (final-pass results + insertions):** (a) Owner Q&A logged: biphenyl `skipped ... placement clashes (1.87 A)` is REFUSE_ATOM = the designed STACK-05 demonstrator (orthogonal rings always clash) — NOT the removed wall gate; accepted, never "fix". (b) Upload-ONLY run gap: set with zero stackable species = endless run (no win condition); logged to .planning/debug/05-upload-only-endless-run.md with candidates C1 begin_game explanation / C2 setup-side guard / C3 mixed-set doc note / C4 skip-vs-refuse recap wording; generic upload stacking stays OUT (v2 STACK-06; no invented chemistry). (c) PHASE 5.1 INSERTED (owner playtesting feedback "current speed is easy, kinda slow"): GAME-11 Setup-selectable speed/difficulty tiers, constant per run (GAME-08 intact), persisted w/ schema backcompat, default = baseline 3.0 A/s; draft tiers 2.0/3.0/4.5/6.0 A/s finalized at feel-check; plan ONLY after Phase 5 wrap; coverage 44 -> 45. (d) Handoff written: .planning/HANDOFF-2026-09-20-phase5-resume.md is the resume file.
- **2026-09-19d (owner directive + upload-path fixes, 05-16 re-test round 4):** (a) REFUSE_WALL placement gate REMOVED entirely — stacked chain may extend past the box on any axis; only the HEAD is box-bound (GAME-05 crash intact); REFUSE_ATOM clash gate untouched and remains the STACK-05 demonstrator (biphenyl 1.87 A); cooldown now fires only on genuine clash streaks (near-wall deadlock class structurally gone). (b) Upload path fixed: skip taxonomy pre-resolved BEFORE any geometry (uploads never inherit dataset entries per 03-04 -> clean `skipped <name>: no verified stacking entry` + (xN) coalescing; the `NoneType has no len()` placement crash is structurally impossible now; skips never feed the exhaust streak) + upload molecules WITH a canonical planar 6-ring render EDGE-ON like the demo set (incl. upload head); ring-less/non-planar uploads fall back to as-stored. Round-4 human verdicts so far: Get Spectra PASS (win ending; crash ending approved round 3). (d33f74c/93f4b2b/22b7245/3f89779; 630 tests)
- **2026-09-18 (checkpoint fixes within 05-16):** perpendicular-stack root cause = _reset_head_viewer double-applied edge_on_m16 (displayed head ring normal 90.00° off placed slabs while looking edge-on) → pymol_bridge.reload_head (fresh load + edge-on once); SPANOFFS/PLANEPAR smoke steps pin viewer spawn-offset algebra + plane parallelism (old checks were distance-only — why the bug was invisible; tracer added: SRP_DEBUG=1 capture lines `dot=1.000000 d=3.6000` + per-event steering lines; ghost-point cascade explained = same-dir + 180° silently dropped by design + one real chain-vs-wall veto (now overridden per (b) above); gates at the time: 575 → 593 → 603 unittests

### Roadmap Evolution

- 2026-09-20: **Phase 5.1 (Game Speed / Difficulty, GAME-11) inserted after Phase 5** (URGENT — owner playtesting feedback "current speed is easy, kinda slow even with small box"); directory .planning/phases/5.1-game-speed-difficulty/; coverage 44 -> 45; draft tiers relaxed ~2.0 / normal 3.0 (default) / fast ~4.5 / expert ~6.0 A/s — owner feel-check finalizes. Distinct from v2 GAME-10-v2 (speed-vs-length, still deferred).
- 2026-09-20: **Phase 5.2 (Generic Upload Stacking Consent, STACK-06 promoted v2->v1) inserted after 5.1** (owner request 2026-09-20, planning choice = plan-first before 5.1); directory .planning/phases/5.2-generic-upload-stacking-consent/; coverage 45 -> 46; consent via inline Setup control (modal popup purity-banned — .exec_() gate), OFF default, persisted; generic entry = already-approved idealized 3.60 A @ 20 geometry for canonical-planar-6-ring uploads, labeled "generic (illustrative — user-approved)" everywhere; ring-less uploads still skip; absorbs debug C2 seam; execute 5.2 -> 5.1 sequentially (shared gui_setup/hud_logic files).

### Pending Todos

- ~~Phase 5 leftover (05-16 checkpoint)~~ DONE 2026-09-20 — Phase 5 COMPLETE + VERIFIED (wrap-up commit; upload-endless debug resolved; all close-out steps executed).
- ~~Owner decision pending: generic upload stacking~~ DECIDED 2026-09-20c — Phase 5.2 INSERTED (STACK-06 promoted v2->v1; design per Roadmap Evolution entry); plan it FIRST, then Phase 5.1.
- ~~C2 soft Apply-time stacking warning~~ ABSORBED into Phase 5.2 scope (consent/label surface lives in the same Setup area; seam in .planning/debug/resolved/05-upload-only-endless-run.md).
- ~~Adjacent observation (old srp_seg_* decay on Restart)~~ RESOLVED 2026-09-20 in 56dd68b (begin_game hard-cleans all srp_* before materializing).
- ~~Phase 5 design note (biphenyl WALL refuse at display_z 5.0)~~ SUPERSEDED 2026-09-20 by d33f74c: REFUSE_WALL placement gate removed entirely; biphenyl's refuse path is now REFUSE_ATOM clash (1.87 Å — the STACK-05 demonstrator); placed z-extent is no longer gated.
- Phase 6 calibration pending: QProcess-in-conda smoke, ~100-atom `--ohess` wall time, OMP env (`[TRAIN]`) — Phase 6 can run parallel with Phases 4-5 (depends only on Phase 2).
- Demo-data FULL DATA_SOURCES.md checklist sign-off (all molecules + attribution) remains Phase 8-gated — Set A data placement is done (03-05), not the full DATA-02/04 approval.
- `tmp/upload_test/` holds the human-checkpoint upload test files (reject_4_rings.sdf tetracene C18H12, reject_no_h.sdf, accept_naphthalene.sdf, accept_benzene.mol2) — gitignored, disposable, regenerate per 03-08-SUMMARY if needed.

### Blockers/Concerns

- Phase 4 spike: up/down arrow-key mechanism question RESOLVED 2026-09-13 (04-07 keys checkpoint APPROVED — wizard do_special route dispatches all four arrows live; eventFilter fallback not needed).
- Offscreen route closed (01-05): headless dialog assertions impossible in PyMOL 2.5.0's Qt build — smoke 02 stays informational (non-blocking FAIL); GUI verdicts are human-verify only.
- RESOLVED 2026-09-19: ghost-point turn-lock (key silence was same-dir/180° design + real chain-vs-wall veto; veto then owner-overridden to head-only — cd04525) and lagging tail (stationary-per-tick chain → rigid train-follow — 76d74b3). Distance question settled: 3.60 Å @ 20° is DATA-02-approved and stays; benzene-crystal-specific distance would need verified source + human re-approval (repo rule).
- Old concern superseded: "Phase 5 consumes setloader ring_atoms / placement math / GAME-10 sweep" — landed (05-01 ring_cycle shim, 05-02/05-10 edge-on, 05-13/05-14 seams); only the 2026-09-19 owner directives in Decisions remain live for Phase 5 behavior.

## Session Continuity

Last session: 2026-09-20 (execute-phase orchestrator — 05-16 checkpoint APPROVED BY EVIDENCE (final-pass test 1: small-box cap-10 win with correct refused-clash recap; test 2: upload demo-mode note + skipped-Nx recap); 05-16-SUMMARY b0ed958; gsd-verifier FINAL 05-VERIFICATION passed (48/48 truths, 3 owner-amended; 5/5 criteria; 9/9 reqs); Phase 5 wrap-up committed)
Stopped at: Phase 5 COMPLETE + VERIFIED (1a251b6); Phase 5.2 INSERTED per owner choice (plan-first); Phase 5.1 queued after.
Resume file: None needed (Phase 5 closed); HANDOFF-2026-09-20-phase5-resume.md is historical (all steps complete)
Next action: (1) /gsd-plan-phase 5.2 (+ optionally /gsd-discuss-phase 5.2 first to settle consent-control wording); (2) execute 5.2 fully, then /gsd-plan-phase 5.1 + execute (sequential — shared gui_setup/hud_logic files); (3) then Phase 6 (xtb Pipeline — QProcess smoke gates it) or Phase 7
Date convention: planning-doc dates are UTC (git commit dates authoritative) — the dev shell is HKT (UTC+8); never stamp from the local date.
