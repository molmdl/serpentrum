---
phase: 01-plugin-skeleton-purity-harness
plan: 04
subsystem: infra
tags: [pymol, headless-smoke, pyqt5, importlib, plugin-loader, sentinels, windows, cmd-exe]

# Dependency graph
requires:
  - phase: 01-plugin-skeleton-purity-harness
    provides: "01-01 entry module — `_anchor()` on `pmg_tk.startup`, lazy Qt in `run_plugin_gui`, `__init_plugin__` menu registration"
provides:
  - "Permanent headless Windows PyMOL skeleton smoke (`smoke/01_skeleton_smoke.py`) — the required `--smoke` target for tests/run_gates.py (01-03 wires it)"
  - "Flushed-sentinel verdict protocol: `SMOKE-OK SKELETON` / `SMOKE-FAIL <step>` greppable from piped stdout"
  - "The reusable smoke template (step functions + check() runner + sentinel epilogue) for every later phase's smoke"
  - "Probe-verified `-cq` environment facts: `__file__` is PyMOL's launcher module, cwd inheritance through cmd.exe works, exit codes stay 0 even with failing steps"
affects: [01-03, 01-05, 01-06, "all later phases' smokes (02+)"]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Flushed-sentinel smoke protocol (exit codes through the .bat always lie → grep stdout)"
    - "Stepwise check() runner: named step functions, per-step SMOKE-STEP OK / SMOKE-FAIL lines"
    - "Defensive ROOT resolution — never trust `__file__` under -cq; validate candidates against serpentrum/__init__.py"
    - "HAVE_QT flag set before `__init_plugin__` (exactly what the real GUI does) — headless menu registration proof"

key-files:
  created:
    - smoke/01_skeleton_smoke.py
  modified: []

key-decisions:
  - "Under `-cq`, `__file__` IS defined but points at PyMOL's launcher (`...\\site-packages\\pymol\\__init__.py`), not the smoke script — ROOT is resolved by validating candidates for `serpentrum/__init__.py` (cwd fallback wins); probe-verified [RUN 2026-09-06]"
  - "Appending to `pmg_tk.startup.__path__` is safe (regular package, plain list — probe confirmed appends persist through failed imports); the loader-name import failure was purely the bad ROOT"
  - "Verdicts are flushed stdout sentinels, never exit codes: first failing round-trip still returned rc=0 through the .bat (empirically confirmed)"

patterns-established:
  - "Smoke template: docstring with canonical one-liner → _resolve_root() → FAILURES list → check(name, fn) → ordered step functions → sentinel epilogue"
  - "Every print carries flush=True (block-buffered when piped; lost on abort)"
  - "No widget construction in smokes (headless Qt C-abort is uncatchable); widget work belongs to 01-05 offscreen probe / 01-06 human-verify"

# Metrics
duration: 79min
completed: 2026-09-06
---

# Phase 1 Plan 4: Headless Skeleton Smoke Summary

**Headless Windows PyMOL smoke proving real-loader-name import (`pmg_tk.startup.serpentrum`), lazy-Qt purity at import time, `HAVE_QT=True` menu registration, and anchor stability across reload + double-import — all via flushed `SMOKE-OK SKELETON` sentinels (exit codes through the .bat always lie).**

## Performance

- **Duration:** 79 min (includes 2 Windows PyMOL probe round-trips for root-cause analysis)
- **Started:** 2026-09-06T11:18:45Z
- **Completed:** 2026-09-06T12:38:06Z
- **Tasks:** 2
- **Files modified:** 1 created

## Accomplishments
- 7 stepwise assertions all green under real headless Windows PyMOL 2.5.0 (Python 3.9.13): `loader_namespace`, `import_under_loader_name`, `no_qt_at_import`, `menu_registration`, `anchor_identity`, `reload_survival`, `double_import_adoption`
- Runtime proof of INFRA-02's lazy-import rule: after the plugin import, neither `PyQt5.QtWidgets` nor `pymol.Qt` is in `sys.modules` (headless PyMOL preloads no Qt, so any eager import would be visible)
- INFRA-03 proven headlessly: `mod._anchor() is mod._anchor()`; `importlib.reload(mod)` keeps `pmg_tk.startup._serpentrum` identical; a second import under the bare name `serpentrum` adopts the same anchor object
- Smoke is 3.6-parseable (`python3.6 -m py_compile` rc 0) so gate 1 can walk it; 130 lines; no `smoke/__init__.py` (findPlugins plugin-path safety)

## Task Commits

Each task was committed atomically:

1. **Task 1: smoke/01_skeleton_smoke.py — stepwise assertions with flushed sentinels** - `3031fa9` (feat)
2. **Task 2: Round-trip via cmd.exe and record the canonical one-liner** - no separate commit (verification-only task; the fix it mandated landed inside Task 1's commit after Task 1's round-trip verification exposed the ROOT bug; the canonical one-liner is recorded in the smoke's docstring for 01-06 to document in AGENTS.md)

**Plan metadata:** (docs commit follows this summary)

## Files Created/Modified
- `smoke/01_skeleton_smoke.py` — headless skeleton smoke: 7 steps + `check()` runner + flushed `SMOKE-OK SKELETON` / `SMOKE-FAIL <step>` sentinel epilogue; the template every later phase's smoke copies

## Verification (canonical invocation, recorded for run_gates --smoke)

From the repo root (cwd is /mnt/c-backed so cmd.exe inherits the C:\ cwd):

```
timeout 90 cmd.exe /c "C:\\src\\run-conda-pymol.bat -cq smoke\\01_skeleton_smoke.py"
```

Final green output:

```
SMOKE-STEP OK  loader_namespace
SMOKE-STEP OK  import_under_loader_name
SMOKE-STEP OK  no_qt_at_import
SMOKE-STEP OK  menu_registration
SMOKE-STEP OK  anchor_identity
SMOKE-STEP OK  reload_survival
SMOKE-STEP OK  double_import_adoption
SMOKE-OK SKELETON
```

- `grep -c "SMOKE-OK SKELETON"` → 1; `grep -c "SMOKE-FAIL"` → 0
- `python3.6 -m py_compile smoke/01_skeleton_smoke.py` → rc 0 (WSL 3.6 gate)
- `python3.6 -m unittest discover -s tests -p "test_*.py"` → OK (3 tests; no regression)
- `tests/run_gates.py` not present on this branch (01-03 runs in a parallel worktree) — per plan, the manual one-liner above is the proof; 01-03 wires this exact invocation as `--smoke`

## Decisions Made
- ROOT resolution validates candidates (`__file__`-derived dir, its parent, cwd) against the presence of `serpentrum/__init__.py` before trusting any of them — because `__file__` under `-cq` is PyMOL's launcher module, not the script (probe-verified; the plan's "fall back to cwd" guard never fired since `__file__` exists but is wrong)
- Kept the plan's plain `__path__.append(ROOT)` mechanism — probe confirmed `pmg_tk.startup` is a regular package with a plain-list `__path__` whose appends persist (no `_NamespacePath` hazard)
- Verdicts via flushed sentinels only; exit code recorded but always ignored (rc=0 observed even on a 4-failure run)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Plan template's ROOT resolution resolved to site-packages under -cq**
- **Found during:** Task 1 verification round-trip (first run: 4 of 7 steps failed with `ModuleNotFoundError("No module named 'pmg_tk.startup.serpentrum'")`)
- **Issue:** The plan assumed `__file__` is either the smoke script or absent under `-cq` script exec. Probe [RUN: `tmp/probe_01_04.py` via the .bat, gitignored] showed `__file__` IS defined but is PyMOL's own launcher (`C:\Users\nglok\.conda\envs\chemtools-win10\Lib\site-packages\pymol\__init__.py`), so `dirname(dirname(__file__))` → `site-packages`, which was appended to `pmg_tk.startup.__path__` — the leaf was then searched in site-packages and not found. (Bare `import serpentrum` passed because cwd is on `sys.path`, masking the bad ROOT in the double-import step.)
- **Fix:** `_resolve_root()` — candidates are `dirname(dirname(__file__))`, `dirname(__file__)`, and `os.getcwd()`; each is accepted only if `serpentrum/__init__.py` exists inside it. The probe also ruled out the namespace-package suspicion: `pmg_tk.startup.__path__` is a plain list, appends persist through failed imports, and `PathFinder.find_spec` works once the correct ROOT is appended.
- **Files modified:** smoke/01_skeleton_smoke.py (only file in this plan)
- **Verification:** Full 7-step green round-trip through real headless Windows PyMOL; all Task 2 greps green
- **Committed in:** `3031fa9`

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Single-file fix inside the plan's own `files_modified`; the corrected ROOT pattern is now a hard rule in the smoke template header so later smokes inherit it. No scope creep.

## Issues Encountered
- None beyond the deviation above. Two headless probe round-trips (~15–20 s each through cmd.exe) were used for root-cause analysis; the probe script is preserved (gitignored) at `tmp/probe_01_04.py` as evidence.

## User Setup Required
None — no external service configuration required.

## Next Phase Readiness
- **01-03 (purity gates):** wire `run_gates --smoke` to the canonical one-liner and grep for exactly one `SMOKE-OK SKELETON` and zero `SMOKE-FAIL`; treat any `SMOKE-FAIL <step>:` line as the failure detail. `smoke/01_skeleton_smoke.py` is 3.6-parseable so the syntax walk can include it.
- **01-05 (offscreen dialog smoke):** copy this file as the template; keep the no-widget rule here intact — `QApplication`/widget construction belongs to 01-05's separate offscreen experiment, not to this skeleton smoke.
- **01-06 (human-verify + AGENTS.md):** document the canonical invocation in AGENTS.md (docstring already carries it verbatim); the visible Plugin-menu item remains human-verify (headless fake menuBar swallows registrations — this smoke only proves registration doesn't raise with `HAVE_QT=True`).
- **All later smokes:** reuse the `_resolve_root()` pattern verbatim; never trust `__file__` under `-cq`.

---
*Phase: 01-plugin-skeleton-purity-harness*
*Completed: 2026-09-06*
