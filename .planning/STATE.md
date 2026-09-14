# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-09-06)

**Core value:** Playing snake by stacking real molecules with known stacking geometry, then seeing the IR spectrum of the molecule you assembled, computed end-to-end inside PyMOL via xtb.
**Current focus:** Phase 4 — Game Loop & Input (all 9 plans complete; 04-09 phase-closing verification APPROVED — pending phase goal verification, then Phase 5)

## Current Position

Phase: 4 of 8 (Game Loop & Input)
Plan: 9 of 9 complete (04-01..04-09; 04-09 phase-closing verification APPROVED — 12/12 live steps + all automated gates green, zero fixes)
Status: Phase 4 playable loop verified live in real Windows PyMOL 2.5.0 (countdown, constant-speed movement, 4-key steering, locked camera, HUD, pause/restart, crash, teardown leak checks); next is phase goal verification (gsd-verifier), then Phase 5
Last activity: 2026-09-13 — 04-09 phase-closing human-verify APPROVED (full playable loop live: countdown, constant-speed movement, 4-key steering, locked camera, HUD, pause/restart, crash, teardown leak checks; 451 tests + 5 REQUIRED smokes green, zero fixes)

Progress: [████████░░] ~84% (32 of ~38 estimated plans — Phases 1-4 firm at 6+14+8+9; Phases 5-8 TBD per roadmap estimates)

## Performance Metrics

**Velocity:**
- Total plans completed: 32
- Total execution time: ~640 executor min (Phase 1: 104; Phase 2: ~330; Phase 3: ~165 incl. smoke-04/fix/measure follow-up agents + verifier; Phase 4: ~41 incl. waves 1-2 + 04-06..04-09)

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1. Plugin Skeleton & Purity Harness | 6/6 | 104 min | 17 min |
| 2. Pure Core — Game & Chemistry Logic | 14/14 | ~330 min | ~24 min |
| 3. Molecules in the Viewer & Setup Tab | 8/8 | ~165 min | ~21 min |
| 4. Game Loop & Input | 9/9 | ~41 min (waves 1-2 merged by orchestrator; 04-06 = 7 min, 04-07 = ~5 min finalization, 04-08 = 6 min direct on main, 04-09 = ~15 min clean gate pass + checkpoint finalization) | ~4.6 min |

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
- 04-09 2026-09-13: Phase-4 closing APPROVED (12/12 live + gates green). Observations recorded: wall-crossing ~6 s on medium (plan estimate miscalibrated, speed correct); turn applies at the next 100 ms tick (designed; <1 s perceived latency — potential future game-feel tuning knob, NOT a defect; GAME-08 speed stays locked)
- 2026-09-11: Agent path discipline — ALL agent work uses /mnt/c/Users/nglok/Desktop/WORKDIR/molmdl/serpentrum (the /home/lwng/... symlink view triggered permission rejections twice); single-plan waves run directly on main (no worktree)

### Pending Todos

- **Phase 5 (stacking):** (a) ring-plane orientation — edge-on presentation per the 03-08 decision above; pick BOX_DISPLAY_Z 5.0 (fits, no margin) vs 6.0 (+2 Å margin) using the measured diameters in 03-08-SUMMARY.md; (b) manifest ring_atoms is the FULL 2-core — extract ONE planar 6-ring in ring order before calling stacking.ring_frame (biphenyl planarity trap).
- User remark (04-07, 2026-09-13): head currently displays the as-stored SDF orientation (ring flat on the xy board) — a pickup would contact via the hydrogen edge, not the ring face/centroid; edge-on orientation at materialization/placement must land BEFORE any stacking (already the recorded 03-08 carried-forward task).
- Phase 6 calibration pending: QProcess-in-conda smoke, ~100-atom `--ohess` wall time, OMP env (`[TRAIN]`) — Phase 6 can run parallel with Phases 4-5 (depends only on Phase 2).
- Demo-data FULL DATA_SOURCES.md checklist sign-off (all molecules + attribution) remains Phase 8-gated — Set A data placement is done (03-05), not the full DATA-02/04 approval.
- `tmp/upload_test/` holds the human-checkpoint upload test files (reject_4_rings.sdf tetracene C18H12, reject_no_h.sdf, accept_naphthalene.sdf, accept_benzene.mol2) — gitignored, disposable, regenerate per 03-08-SUMMARY if needed.

### Blockers/Concerns

- Phase 4 spike: up/down arrow-key mechanism question RESOLVED 2026-09-13 (04-07 keys checkpoint APPROVED — wizard do_special route dispatches all four arrows live; eventFilter fallback not needed).
- Offscreen route closed (01-05): headless dialog assertions impossible in PyMOL 2.5.0's Qt build — smoke 02 stays informational (non-blocking FAIL); GUI verdicts are human-verify only.
- Phase 5 consumes: setloader records (incl. demo ring_atoms), stacking placement math, GAME-10 sweep machinery; watch the two pending-todo items above.

## Session Continuity

Last session: 2026-09-13 (gsd-executor — Phase 4, plan 04-09 phase-closing verification finalization, single-plan direct on main)
Stopped at: Completed 04-09-PLAN.md (phase-closing human-verify APPROVED 12/12; 451 tests + 5 REQUIRED smokes green, zero fixes; SUMMARY + STATE + ROADMAP committed)
Resume file: None
Next action: phase goal verification (gsd-verifier, spawned from the execute-phase orchestrator), then ROADMAP/REQUIREMENTS status updates + Phase 5 (Stacking & Game Rules Complete)
