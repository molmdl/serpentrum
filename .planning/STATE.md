# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-09-06)

**Core value:** Playing snake by stacking real molecules with known stacking geometry, then seeing the IR spectrum of the molecule you assembled, computed end-to-end inside PyMOL via xtb.
**Current focus:** Phase 1 — Plugin Skeleton & Purity Harness

## Current Position

Phase: 1 of 8 (Plugin Skeleton & Purity Harness)
Plan: 6 of 6 in current phase (01-01..01-06 complete)
Status: Phase complete — verified (5/5 must-haves, 01-VERIFICATION.md)
Last activity: 2026-09-06 — Phase 1 verified: gates green end-to-end + human-verify approved (install/single-instance/modeless)

Progress: [██░░░░░░░░] ~21% (6 of ~28 estimated plans — Phase 1 firm at 6; Phases 2–8 TBD)

## Performance Metrics

**Velocity:**
- Total plans completed: 6
- Average duration: 17 min
- Total execution time: 104 min

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1. Plugin Skeleton & Purity Harness | 6/6 | 104 min | 17 min |

**Recent Trend:**
- Last 5 plans: 01-06 (4 min auto + human checkpoint), 01-05 (6 min), 01-04 (79 min), 01-03 (7 min), 01-02 (5 min)
- Trend: 01-04 included two Windows PyMOL probe round-trips (root-cause debugging); 01-06's human checkpoint waited on user GUI verification (3 PyMOL launches)

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

### Pending Todos

None yet.

### Blockers/Concerns

- Demo-data approval track (human-gated) starts at Phase 2 and gates Phase 8 (DATA-02) — longest external lead time; must not slip.
- Phase 4 spike: up/down arrow-key binding is the one open mechanism question (Qt event-filter fallback already designed).
- Phase 6 calibration pending: QProcess-in-conda smoke, ~100-atom `--ohess` wall time, OMP env (`[TRAIN]`).
- ~~01-02 must define `PluginDialog.find_existing()` in `serpentrum/gui.py`~~ — resolved by 01-02 (find_existing landed in gui.py; run_plugin_gui call site wired)
- ~~01-04 smokes must key assertions on `pmg_tk.startup.serpentrum`~~ — resolved by 01-04 (skeleton smoke keys on the loader name; passed end-to-end)
- Offscreen route closed (01-05): headless dialog assertions are impossible in PyMOL 2.5.0's Qt build even with `QT_QPA_PLATFORM=offscreen` + QApplication-first — do NOT spend time on Qt-offscreen spikes again; smoke 02 remains informational (abort → no sentinel → non-blocking FAIL note)

## Session Continuity

Last session: 2026-09-06T14:30Z (01-06 continuation executor)
Stopped at: 01-06 complete (checkpoint approved); Phase 1 executed, awaiting /gsd-execute-phase verification step
Resume file: None
Next action: Orchestrator phase-verification of Phase 1 (all 6 plans complete), then /gsd-plan-phase 2 (Pure Core — Game & Chemistry Logic; starts demo-data approval track)
