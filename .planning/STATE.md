# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-09-06)

**Core value:** Playing snake by stacking real molecules with known stacking geometry, then seeing the IR spectrum of the molecule you assembled, computed end-to-end inside PyMOL via xtb.
**Current focus:** Phase 3 — Molecules in the Viewer & Setup Tab (complete, verified)

## Current Position

Phase: 3 of 8 (Molecules in the Viewer & Setup Tab)
Plan: 8 of 8 in current phase (03-01..03-08 complete)
Status: Phase complete — verified (5/5 success criteria, 32/32 plan must-haves, 03-VERIFICATION.md status: passed)
Last activity: 2026-09-12 — Phase 3 executed (5 waves; wave 1 = 3 worktree-parallel plans; human SDF gate + human-verify approved) + verified; 433 tests green, all 5 gates + 3 smokes green

Progress: [███████░░░] ~74% (28 of ~38 estimated plans — Phases 1-3 firm at 6+14+8; Phases 4-8 TBD per roadmap estimates)

## Performance Metrics

**Velocity:**
- Total plans completed: 28
- Total execution time: ~600 executor min (Phase 1: 104; Phase 2: ~330; Phase 3: ~165 incl. smoke-04/fix/measure follow-up agents + verifier)

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1. Plugin Skeleton & Purity Harness | 6/6 | 104 min | 17 min |
| 2. Pure Core — Game & Chemistry Logic | 14/14 | ~330 min | ~24 min |
| 3. Molecules in the Viewer & Setup Tab | 8/8 | ~165 min | ~21 min |

**Recent Trend:**
- Phase 3: 03-01 (7 min), 03-02 (22), 03-03 (~15 incl. respawn after /home-symlink permission rejection), 03-04 (10), 03-05 (~8, single-plan direct on main), 03-06 (~25, Windows smokes), 03-07 (20), 03-08 (35 + 3 follow-up agents ~25)
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
- 2026-09-11: Agent path discipline — ALL agent work uses /mnt/c/Users/nglok/Desktop/WORKDIR/molmdl/serpentrum (the /home/lwng/... symlink view triggered permission rejections twice); single-plan waves run directly on main (no worktree)

### Pending Todos

- **Phase 5 (stacking):** (a) ring-plane orientation — edge-on presentation per the 03-08 decision above; pick BOX_DISPLAY_Z 5.0 (fits, no margin) vs 6.0 (+2 Å margin) using the measured diameters in 03-08-SUMMARY.md; (b) manifest ring_atoms is the FULL 2-core — extract ONE planar 6-ring in ring order before calling stacking.ring_frame (biphenyl planarity trap).
- Phase 6 calibration pending: QProcess-in-conda smoke, ~100-atom `--ohess` wall time, OMP env (`[TRAIN]`) — Phase 6 can run parallel with Phases 4-5 (depends only on Phase 2).
- Demo-data FULL DATA_SOURCES.md checklist sign-off (all molecules + attribution) remains Phase 8-gated — Set A data placement is done (03-05), not the full DATA-02/04 approval.
- `tmp/upload_test/` holds the human-checkpoint upload test files (reject_4_rings.sdf tetracene C18H12, reject_no_h.sdf, accept_naphthalene.sdf, accept_benzene.mol2) — gitignored, disposable, regenerate per 03-08-SUMMARY if needed.

### Blockers/Concerns

- Phase 4 spike: up/down arrow-key binding is the one open mechanism question (Qt event-filter fallback already designed). First human-verify of keys lands in Phase 4 so failure is cheap.
- Offscreen route closed (01-05): headless dialog assertions impossible in PyMOL 2.5.0's Qt build — smoke 02 stays informational (non-blocking FAIL); GUI verdicts are human-verify only.
- Phase 5 consumes: setloader records (incl. demo ring_atoms), stacking placement math, GAME-10 sweep machinery; watch the two pending-todo items above.

## Session Continuity

Last session: 2026-09-12 (execute-phase orchestrator — Phase 3 full run)
Stopped at: Phase 3 complete + verified (8/8 plans, 03-VERIFICATION.md status: passed); ROADMAP/STATE/REQUIREMENTS updated
Resume file: None
Next action: /gsd-plan-phase 4 (Game Loop & Input — input spike first: up/down set_key bindability, Wizard event-mask, focus stealing; fallback = Qt application-level event filter). Alternative per roadmap F∥D/E parallelism: /gsd-plan-phase 6 (xtb pipeline) can run in parallel with Phases 4-5.
