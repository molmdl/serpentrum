---
phase: 01-plugin-skeleton-purity-harness
verified: 2026-09-06T22:30:57+08:00
status: passed
score: 5/5 must-haves verified
---

# Phase 1: Plugin Skeleton & Purity Harness — Verification Report

**Phase Goal:** The plugin installs into real PyMOL and opens a stable, single-instance, modeless 3-tab dialog — with the purity gates and test harness every later phase must pass, built in from commit one.
**Verified:** 2026-09-06T22:30:57+08:00
**Status:** **passed**
**Re-verification:** No — initial verification

## Goal Achievement

### ROADMAP Success Criteria (must-haves)

| # | Criterion (ROADMAP) | Status | Evidence |
|---|---------------------|--------|----------|
| 1 | Install via plugin path → single "serpentrum" menu item opens the 3-tab dialog (Setup / Game / Spectra) [SETUP-01] | ✓ VERIFIED | **Human-verified & approved** in real Windows PyMOL 2.5.0 (01-06-SUMMARY: 3 separate launches — one menu item, dialog titled "serpentrum", exactly 3 tabs). Static mechanisms confirmed by source read: `addmenuitemqt('serpentrum', run_plugin_gui)` at `serpentrum/__init__.py:34`; 3× `addTab(page, label)` loop over `_TAB_DEFS` (Setup/Game/Spectra) at `serpentrum/gui.py:47-55`; `setWindowTitle('serpentrum')` at gui.py:44 |
| 2 | Double-open / Plugin-Manager reload still yields exactly one dialog with live controls — anchor outside module globals [INFRA-03] | ✓ VERIFIED | **Human-verified** (re-click raises existing dialog; reload-via-restart clean). Anchor code: `_anchor()` sets/reads `pmg_tk.startup._serpentrum` (`__init__.py:20-26`) — never module globals. Adopt defense: `run_plugin_gui` reuses `state.dialog` else `PluginDialog.find_existing()` scanning `QApplication.topLevelWidgets()` (`gui.py:62-69`). Runtime proof: headless smoke steps `reload_survival` + `double_import_adoption` passed inside flushed `SMOKE-OK SKELETON` (gate 4 PASS this session) |
| 3 | Dialog is modeless; viewer + command line stay responsive [INFRA-05] | ✓ VERIFIED | **Human-verified** (rotate/zoom + command line responsive with dialog open). Static: `run_plugin_gui` uses `.show()/.raise_()/.activateWindow()` (`__init__.py:43-45`), zero `.exec_()` anywhere in the package; AST checker bans `.exec_()` with file:line (`check_purity.py:165-169`) — enforcement proven by passing fixture test `test_exec_call_flagged`; real tree is checker-clean (gate 2 PASS) |
| 4 | WSL python3.6 gate runs green: py_compile under 3.6, pure modules stdlib-only (AST gate), Qt only via `pymol.Qt` [INFRA-02, INFRA-06] | ✓ VERIFIED | **Ran live this session:** `python3.6 tests/run_gates.py` → gates 1–3 PASS, 32 unittests OK, RC=0. AST checker (216 lines, stdlib-only) distinguishes module-level vs lazy imports, is docstring-blind, and bans `PyQt5`/`numpy` everywhere — all 10 fixture self-tests green (`test_purity_gates.py`); gui.py imports Qt exclusively via `from pymol.Qt import QtWidgets` (gui.py:11) |
| 5 | Environment contract: headless Windows PyMOL smoke via cmd.exe, WSL python3.6 suite runs, Windows xtb invocable from WSL with path conversion [INFRA-01] | ✓ VERIFIED | **Ran live this session:** `python3.6 tests/run_gates.py --smoke` → gate 4 PASS with flushed `SMOKE-OK SKELETON` (verdict = sentinels, never exit codes, per run_gates.py:140); `python3.6 tests/run_gates.py --xtb` → gate 5 PASS: winpath sanity `/mnt/c/... → C:/...` OK, direct WSL exec of `xtb-6.7.1/bin/xtb.exe --version` returned `xtb version 6.7.1pre (5071a88)` + `normal termination of xtb` |

**Score:** 5/5 must-haves verified

### Per-Plan Must-Have Detail (6/6 plans)

| Plan | Must-have | Status | Evidence |
|------|-----------|--------|----------|
| 01-01 | Entry imports under py3.6, zero sys.modules stubs | ✓ | `test_skeleton.py` 3 tests pass (32/32); module level of `__init__.py` is stdlib-only by read |
| 01-01 | Anchor on `pmg_tk.startup._serpentrum`, not module globals | ✓ | `__init__.py:20-26`; smoke `reload_survival` + `double_import_adoption` PASS |
| 01-01 | `run_plugin_gui` reuses anchor dialog else adopts orphan | ✓ | `__init__.py:37-45` + `gui.py:62-69` |
| 01-02 | 3 tabs Setup/Game/Spectra, title 'serpentrum' | ✓ | gui.py:14-24, 47-55, 44; human-approved; smoke 02 asserts same labels (informational) |
| 01-02 | Modeless `.show()`, zero `.exec_()` (checker-enforced) | ✓ | `__init__.py:43`; checker rule + passing enforcement test |
| 01-02 | Qt exclusively via `pymol.Qt` | ✓ | gui.py:11 only Qt import in package |
| 01-03 | Default `run_gates` green, RC 0 | ✓ | Live run this session |
| 01-03 | Banned imports fail with file:line; lazy-vs-module-level distinguished; docstring no false-positive | ✓ | checker impl + fixture cases 1–4, 6, 9 all pass |
| 01-03 | `--smoke` verdicts = flushed SMOKE-OK sentinels only | ✓ | run_gates.py:138-141 (`'SMOKE-OK' in out and 'SMOKE-FAIL' not in out`); live gate 4 PASS |
| 01-04 | Headless PyMOL: loader-name import, `__init_plugin__` clean, HAVE_QT=True | ✓ | smoke steps `loader_namespace`, `import_under_loader_name`, `menu_registration` PASS (SMOKE-OK SKELETON flushed) |
| 01-04 | Reload / double-import never duplicates anchor; no Qt at import | ✓ | smoke steps `no_qt_at_import`, `reload_survival`, `double_import_adoption` PASS |
| 01-05 | Windows xtb from WSL, asserts 'normal termination' | ✓ | gate 5 PASS live: `xtb version 6.7.1pre` + `normal termination of xtb` |
| 01-05 | Pure unit-tested winpath (both forms, strict /mnt validation) | ✓ | winpath.py 72 lines; 21 tests pass incl. 8 ValueError cases |
| 01-05 | 02 dialog smoke informational, never silently passes | ✓ | gate 4 note: `informational smoke smoke/02_dialog_smoke.py: FAIL (non-blocking)` — the documented offscreen dead end, correctly reported as FAIL (not silent pass), gate stays green |
| 01-06 | Human-verified install / menu / 3-tab [SETUP-01] | ✓ | 01-06-SUMMARY Human Verification Record: **verdict "approved"**, 3 launches |
| 01-06 | Human-verified single instance double-open + reload [INFRA-03] | ✓ | same record |
| 01-06 | Human-verified modeless responsiveness [INFRA-05] | ✓ | same record |
| 01-06 | Full gate suite green end-to-end | ✓ | default + --smoke + --xtb all re-run green this session |
| 01-06 | AGENTS.md documents gates, path-safety, module identity, modeless rule | ✓ | AGENTS.md § "serpentrum plugin gates & conventions": `tests/run_gates.py` commands (L67-69), `pmg_tk.startup.serpentrum` identity + anchor rule (L72), modeless/`.exec_()` rule, purity classes |
| 01-06 | PITFALLS.md dated loader-name correction | ✓ | PITFALLS.md:174 "CORRECTED 2026-09-06 … sys.modules key is pmg_tk.startup.<name>" (appended note, not rewrite) |

### Required Artifacts (3-level: exists / substantive / wired)

| Artifact | Expected | Lines (min) | Exists | Substantive | Wired | Status |
|----------|----------|-------------|--------|-------------|-------|--------|
| `serpentrum/__init__.py` | anchor + entry + lazy GUI open | 45 (40) | ✓ | ✓ no stubs, module-level stdlib-only | ✓ loaded by PyMOL loader as `pmg_tk.startup.serpentrum` (smoke-proven) | ✓ VERIFIED |
| `serpentrum/gui.py` | PluginDialog, 3 tabs, find_existing | 69 (55) | ✓ | ✓ no stubs, pymol.Qt only | ✓ lazily imported by `run_plugin_gui` | ✓ VERIFIED |
| `tools/check_purity.py` | AST purity checker + CLI | 216 (90) | ✓ | ✓ stdlib-only, check_tree importable | ✓ imported by run_gates gate 2 + test_purity_gates | ✓ VERIFIED |
| `tests/run_gates.py` | gates 1–5, flag-gated | 307 (80) | ✓ | ✓ all five gates implemented | ✓ canonical entry (AGENTS.md; run live ×3 this session) | ✓ VERIFIED |
| `tests/test_skeleton.py` | zero-stub import + entry API | 43 (15) | ✓ | ✓ | ✓ discovered by gate 3 (3 tests) | ✓ VERIFIED |
| `tests/test_purity_gates.py` | checker self-test fixtures + real-repo clean | 216 (60) | ✓ | ✓ 10 cases | ✓ discovered by gate 3 (10 tests) | ✓ VERIFIED |
| `tools/winpath.py` | both conversion forms, strict validation | 72 (25) | ✓ | ✓ | ✓ imported by gate 5 sanity + test_winpath | ✓ VERIFIED |
| `tests/test_winpath.py` | happy paths + ValueError + no-mutation | 103 (25) | ✓ | ✓ 21 tests | ✓ discovered by gate 3 | ✓ VERIFIED |
| `smoke/01_skeleton_smoke.py` | required headless smoke, sentinels | 130 (60) | ✓ | ✓ 7 ordered steps | ✓ invoked by gate 4; SMOKE-OK SKELETON flushed live | ✓ VERIFIED |
| `smoke/02_dialog_smoke.py` | experimental offscreen smoke, informational | 134 (40) | ✓ | ✓ QT_QPA_PLATFORM-first ordering | ✓ auto-discovered by gate 4 as informational | ✓ VERIFIED |
| `AGENTS.md` | gates & conventions section | — | ✓ | ✓ | ✓ contains `tests/run_gates.py` | ✓ VERIFIED |
| `.planning/research/PITFALLS.md` | dated pmg_tk.startup correction | — | ✓ | ✓ | ✓ contains `pmg_tk.startup` | ✓ VERIFIED |

### Key Link Verification

| From | To | Via | Status | Evidence |
|------|----|----|--------|----------|
| `__init_plugin__` | `addmenuitemqt('serpentrum', run_plugin_gui)` | lazy import inside function body | ✓ WIRED | `__init__.py:33-34`; exercised live in smoke step `menu_registration` |
| `_anchor()` | `pmg_tk.startup._serpentrum` | attribute on loader package object | ✓ WIRED | `__init__.py:20-26`; smoke `anchor_identity`/`reload_survival` PASS |
| `run_plugin_gui` | `serpentrum.gui.PluginDialog` | lazy `from .gui import` + `.show()` | ✓ WIRED | `__init__.py:40-45`; adopt-then-show order correct |
| `find_existing()` | `QApplication.topLevelWidgets()` | orphan scan | ✓ WIRED | `gui.py:62-69` |
| `gui.__init__` | 3× `QTabWidget.addTab` | loop over `_TAB_DEFS` | ✓ WIRED | `gui.py:47-55`; labels confirmed by human + smoke 02 assertions |
| `run_gates` gate 2 | `check_purity.check_tree()` | sys.path insert of tools/ + import | ✓ WIRED | run_gates.py:104-108; gate 2 PASS live |
| `run_gates` gate 3 | unittest discover (scoped) | subprocess `[sys.executable, '-m', 'unittest', 'discover', '-s', 'tests']` | ✓ WIRED | run_gates.py:116-119; 32 tests ran live |
| `run_gates --smoke` | headless Windows PyMOL | `cmd.exe /c C:\src\run-conda-pymol.bat -cq <script>` + sentinel grep | ✓ WIRED | run_gates.py:57,128-141; gate 4 PASS, `SMOKE-OK SKELETON` echoed live |
| `run_gates --xtb` | Windows `xtb.exe` | direct WSL exec + `to_windows_path` sanity + content assert | ✓ WIRED | run_gates.py:62,195-258; gate 5 PASS live with both proof lines |
| `smoke/01` | `pmg_tk.startup.serpentrum` | `__path__.append` + importlib.import_module | ✓ WIRED | smoke lines 67-74; PASS live |
| `smoke/01` epilogue | gate 4 sentinel grep | `print('SMOKE-OK SKELETON', flush=True)` | ✓ WIRED | smoke lines 127-130; sentinel captured in gate output live |
| AGENTS.md | gate commands | canonical docs for future phases | ✓ WIRED | AGENTS.md:67-69 |

### Requirements Coverage

| Requirement | Status | Blocking Issue |
|-------------|--------|----------------|
| SETUP-01 | ✓ SATISFIED | none (human-approved + static mechanisms verified) |
| INFRA-01 | ✓ SATISFIED | none (gates 4 + 5 green live this session) |
| INFRA-02 | ✓ SATISFIED | none (AST gate + 32 tests green; zero stubs) |
| INFRA-03 | ✓ SATISFIED | none (anchor + adopt defense; smoke + human evidence) |
| INFRA-05 | ✓ SATISFIED | none (.show() only; exec_ ban enforced; human-approved) |
| INFRA-06 | ✓ SATISFIED | none (py_compile gate green under python3.6.9) |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `serpentrum/gui.py` | 13-23 | "placeholder" wording for the 3 tabs | ℹ️ Info | Intentional by design — Phase 1 ships placeholder tab shells; real content lands Phases 3/4/7 per ROADMAP. Not a stub: tab widgets are real, labeled, and human-verified |
| `serpentrum/`, `tools/`, `tests/` | — | `__pycache__` .pyc files present | ℹ️ Info | Normal Python byte-cache artifacts; gate 1's AST/py_compile checks operate on source |
| `tests/test_purity_gates.py` | 160-189 | `PyQt5`/`exec_()` strings | ℹ️ Info | Deliberate known-bad fixture literals for checker self-tests — the whole point of the file; not real violations (checker is docstring/string-blind and reports the real tree clean) |

No 🛑 Blocker or ⚠️ Warning patterns found. No TODO/FIXME anywhere in source.

### Human Verification Required

**None outstanding.** The irreducibly human halves (criteria 1–3: install → single menu item → 3-tab dialog; single instance under double-open/reload; modelessness) were **human-verified and approved by the user in real Windows PyMOL 2.5.0** at the 01-06 checkpoint — 3 separate launches with restarts between checks, every step green (recorded as "Human Verification Record — Verdict: approved" in 01-06-SUMMARY.md). This verification session re-validated the static mechanisms that make those observations hold (anchor placement, adopt-defense, `.show()`-only, checker enforcement) rather than re-running the GUI.

### Gaps Summary

None. All 5 ROADMAP success criteria verified against the actual codebase: artifacts exist, are substantive (all exceed plan minimum line counts), and are wired (every plan-level key link confirmed by source read **and** exercised live in this session's gate runs). Live machine evidence from this verification session:

- `python3.6 tests/run_gates.py` → gates 1–3 PASS, 32 unittests OK, RC=0
- `python3.6 tests/run_gates.py --smoke` → gate 4 PASS, `SMOKE-OK SKELETON` flushed; 02_dialog_smoke reported informational FAIL (non-blocking) — the documented offscreen dead end, correctly non-silent
- `python3.6 tests/run_gates.py --xtb` → gate 5 PASS, `xtb version 6.7.1pre (5071a88)` + `normal termination of xtb`, winpath sanity `/mnt/c/... → C:/...` OK

Phase 1 goal achieved. Ready to proceed to Phase 2.

---

_Verified: 2026-09-06T22:30:57+08:00_
_Verifier: OpenCode (gsd-verifier)_
