# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-09-06)

**Core value:** Playing snake by stacking real molecules with known stacking geometry, then seeing the IR spectrum of the molecule you assembled, computed end-to-end inside PyMOL via xtb.
**Current focus:** Phase 1 — Plugin Skeleton & Purity Harness

## Current Position

Phase: 1 of 8 (Plugin Skeleton & Purity Harness)
Plan: 3 of 6 in current phase (01-03 done; 01-02/01-04 in parallel worktrees)
Status: In progress
Last activity: 2026-09-06 — Completed 01-03-PLAN.md (AST purity checker + run_gates harness)

Progress: [██░░░░░░░░] ~7% (2 of ~28 estimated plans — Phase 1 firm at 6; Phases 2–8 TBD)

## Performance Metrics

**Velocity:**
- Total plans completed: 2
- Average duration: 5 min
- Total execution time: 10 min

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1. Plugin Skeleton & Purity Harness | 2/6 | 10 min | 5 min |

**Recent Trend:**
- Last 5 plans: 01-03 (7 min), 01-01 (3 min)
- Trend: — (early)

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
- 01-03 2026-09-06: Purity gate is AST-based, not grep (docstring-proof; splits module-level vs lazy); "module level" = direct Module.body children only; GUI allowlist accepts only `pymol.Qt`/`pymol.Qt.*` import paths — extend GUI_MODULES deliberately, everything else defaults PURE

### Pending Todos

None yet.

### Blockers/Concerns

- Demo-data approval track (human-gated) starts at Phase 2 and gates Phase 8 (DATA-02) — longest external lead time; must not slip.
- Phase 4 spike: up/down arrow-key binding is the one open mechanism question (Qt event-filter fallback already designed).
- Phase 6 calibration pending: QProcess-in-conda smoke, ~100-atom `--ohess` wall time, OMP env (`[TRAIN]`).
- 01-02 must define `PluginDialog.find_existing()` in `serpentrum/gui.py` (scan `QApplication.topLevelWidgets()` for an instance of the class) — `run_plugin_gui` already calls it; safe until then because the lazy import only executes at menu-click time (never headless).
- 01-04 smokes must key assertions on `pmg_tk.startup.serpentrum` — `pymol.plugins.startup` is only an attribute alias, not the sys.modules key.

## Session Continuity

Last session: 2026-09-06 19:25
Stopped at: Completed 01-03-PLAN.md (SUMMARY written; STATE updated)
Resume file: None
Next action: Merge Wave 2 branches (01-02 ∥ 01-03 ∥ 01-04) in dependency order; then 01-05 / 01-06. Note: `run_gates.py --smoke` fails until 01-04 lands smoke/01_skeleton_smoke.py
