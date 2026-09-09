# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-09-06)

**Core value:** Playing snake by stacking real molecules with known stacking geometry, then seeing the IR spectrum of the molecule you assembled, computed end-to-end inside PyMOL via xtb.
**Current focus:** Phase 2 — Pure Core — Game & Chemistry Logic (complete, verified)

## Current Position

Phase: 2 of 8 (Pure Core — Game & Chemistry Logic)
Plan: 14 of 14 in current phase (02-01..02-14 complete)
Status: Phase complete — verified (4/4 success criteria, 02-VERIFICATION.md)
Last activity: 2026-09-10 — Phase 2 executed (4 waves, worktree-parallel) + verified; 383 tests green, zero stubs

Progress: [█████░░░░░] ~53% (20 of ~38 estimated plans — Phases 1-2 firm at 6+14; Phases 3-8 TBD per roadmap estimates)

## Performance Metrics

**Velocity:**
- Total plans completed: 20
- Average duration: ~21 min
- Total execution time: ~430 min (Phase 1: 104; Phase 2: ~330 executor min incl. 1 re-spawn + 1 session resume)

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1. Plugin Skeleton & Purity Harness | 6/6 | 104 min | 17 min |
| 2. Pure Core — Game & Chemistry Logic | 14/14 | ~330 min | ~24 min |

**Recent Trend:**
- Last 5 plans: 02-14 (5 min), 02-13 (22 min), 02-12 (8 min), 02-11 (checkpoint pause + ~20 min continuation), 02-10 (26 min)
- Trend: worktree-parallel waves held avg ~24 min/plan across 14 plans; the only slow plan was 02-04 (68 min — silent first attempt, re-spawned clean)

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Locked 2026-09-06: 2D plane + locked camera; constant speed; rigid chain pivot turns (GAME-10 — sweep refused on collision, no 180°)
- Locked 2026-09-06: Demo Set A only (π-stack); distances pinned at data-prep + human approval; refuse-and-skip fallback (STACK-03)
- Locked 2026-09-06: `xtb --ohess` (never `-o --hess`); broadened IR; static mode vectors; 6 buttons; crash still completes → spectra
- Roadmap 2026-09-06: Phase 6 (xtb pipeline) depends only on Phase 2 — run parallel with Phases 3–5; worktree protocol for concurrent plans
- Roadmap 2026-09-06: v1 requirement count corrected 41 → 44 (listed ID ranges sum to 44; all mapped exactly once)
- 01-01 2026-09-06: Anchor live state on `pmg_tk.startup._serpentrum` (loader's own plugin namespace) — survives Plugin-Manager reload + double import (Pitfall 7 / INFRA-03); never module globals
- 01-01 2026-09-06: Entry module is stdlib-only at module level; pymol imported inside `__init_plugin__`, Qt lazily inside `run_plugin_gui` (INFRA-02 — zero-stub py3.6 gate green from commit one)
- 01-01 2026-09-06: tests/ has NO `__init__.py`; discovery = `python3.6 -m unittest discover -s tests -p "test_*.py" -v` (never `-t .` — fails on py3.6 non-package start dir); every test file repeats the sys.path self-insert
- 01-02 2026-09-06: gui.py docstrings stay free of banned literals (exec_(, from PyQt5, import PyQt5) — plan verify + 01-03 AST checker grep the raw text and docstring literals false-positive (research §1.4); contracts are documented in checker-safe wording instead
- 01-03 2026-09-06: Purity gate is AST-based, not grep (docstring-proof; splits module-level vs lazy); "module level" = direct Module.body children only; GUI allowlist accepts only `pymol.Qt`/`pymol.Qt.*` import paths — extend GUI_MODULES deliberately, everything else defaults PURE
- 01-04 2026-09-06: Under `-cq`, `__file__` IS defined but is PyMOL's own launcher (`...\site-packages\pymol\__init__.py`), NOT the script — smokes resolve ROOT by validating candidates against `serpentrum/__init__.py`; never trust `__file__` (probe-verified; append to `pmg_tk.startup.__path__` itself is safe — regular package, plain list)
- 01-05 2026-09-06: Offscreen dialog mechanism is a DEAD END — `QApplication([])` constructs OK under `QT_QPA_PLATFORM=offscreen`, but `PluginDialog()` construction kills the process silently (no sentinel, rc 0 through the .bat); smoke 02 stays as the documented experiment, never promote to required; dialog verdicts stay with human-verify
- 01-05 2026-09-06: Windows-exe probe pattern: `subprocess.run([exe, ...], cwd=ROOT)` with WSL-style exe path + /mnt/c-backed cwd + bare relative args; verdict asserts output content ('xtb version' + 'normal termination') even though direct-exec rc is meaningful
- 01-05 2026-09-06: winpath is harness/dev-side ONLY (strict ValueError on non-`/mnt` paths, never mangles); the plugin runtime never converts paths (Windows PyMOL + Windows exe + relative names)
- 01-06 2026-09-06: Human-verify approved in real Windows PyMOL (3 launches): single menu item → 3-tab modeless dialog; single-instance + reload-via-restart hold [SETUP-01, INFRA-03, INFRA-05]
- 01-06 2026-09-06: Reload phrasing for future docs: "restart PyMOL OR re-add the plugin directory in Plugin Manager" (restart is the simpler, equally valid reload path — step-6 wording confused the user; no code impact)
- Phase 2 2026-09-10: **π-stack APPROVED (DATA-02, human decision option-a): 3.60 Å centroid-centroid @ 20° off-normal, encoded distance_a 3.383 / lateral_offset_a 1.231** — the dataset file (`serpentrum/data/stacking_pi_stack.json`) is the shipping contract; place_pickup composition: distance_a = perpendicular component, lateral_offset_a = in-plane; composed = sqrt(d²+l²), angle = atan2(l,d). 3.4 Å stays UNVERIFIED/do-not-ship; DATA_SOURCES.md stays DRAFT-headed (full DATA-02/04 checklist sign-off is Phase 8)
- Phase 2 2026-09-10: Trivial-mode filter is |freq| < threshold ONLY (never sign — dimer modes 7-9 are negative REAL modes; never selection column; never hardcoded 5/6 count — CO2 has 5, dimer has 6)
- Phase 2 2026-09-10: Spectra broaden(): grid [0, max(3600, max_freq+5σ)], σ = fwhm/2.35482 (runtime-computed in tests), empty modes → pinned zero curve; g98↔vibspectrum correspondence offset = 3N − n_g98_modes, tolerances 0.01 cm⁻¹ / 1e-4 intensity
- Phase 2 2026-09-10: Engine referee event order: moved → boundary crash → body crash → stacked (≤1 capture/tick) → won; reject_pickup returns canonical ('refused', pickup_id, reason); body model = head-centroid vs polyline edges from segment centroids (skip newest 2 edges), strict < 2.0 Å
- Phase 2 2026-09-10: GAME-10 sweeps: TURN_DEGREES 90 / TURN_TICKS 6 (15°/tick, 7-sample pre-check); pending applied exactly once at step start (refused requests consumed, fall through to forward motion); sweep-level 180° judged vs sweep target, newest-wins buffering in-sweep; pickup sweep leg is atom-level at 2.5 Å (SWEEP_PICKUP_CLEARANCE_A)
- Phase 2 2026-09-10: Worktree protocol proven at scale: 14 plans, 3+3+2+3+2+1 parallel spawns across 4 waves — zero shared-index races, zero merge conflicts (disjoint files_modified); executors skip STATE.md during parallel waves (orchestrator-owned)

### Pending Todos

None yet.

### Blockers/Concerns

- Demo-data: distance leg of DATA-02 is DONE (π-stack APPROVED 3.6 Å @ 20°); the FULL DATA_SOURCES.md checklist sign-off (all molecules + attribution) remains Phase 8-gated — do not treat Set A data as fully approved.
- Phase 4 spike: up/down arrow-key binding is the one open mechanism question (Qt event-filter fallback already designed).
- Phase 6 calibration pending: QProcess-in-conda smoke, ~100-atom `--ohess` wall time, OMP env (`[TRAIN]`).
- Phase 3 consumes Phase 2's pure halves: setup_logic (schema/defaults), molecule_data (loader), stacking (placement+clash), xyzio (loads), cgo_build (box+head rendering). The bridge wiring is Phase 3's job — nothing in serpentrum/ imports these modules yet (pure modules stay mutually decoupled by design).
- Offscreen route closed (01-05): headless dialog assertions are impossible in PyMOL 2.5.0's Qt build even with `QT_QPA_PLATFORM=offscreen` + QApplication-first — do NOT spend time on Qt-offscreen spikes again; smoke 02 remains informational (abort → no sentinel → non-blocking FAIL note)

## Session Continuity

Last session: 2026-09-10 (execute-phase orchestrator — Phase 2 full run)
Stopped at: Phase 2 complete + verified (14/14 plans, 02-VERIFICATION.md status: passed); ROADMAP/STATE/REQUIREMENTS updated
Resume file: None
Next action: /gsd-plan-phase 3 (Molecules in the Viewer & Setup Tab — bridge/loader + validation gate, box/camera/cleanup, setup-tab UI; consumes setup_logic + molecule_data + stacking + cgo_build)
