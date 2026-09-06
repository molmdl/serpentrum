# Phase 1 Research: Purity Gates & Test/Environment Harness

**Researched:** 2026-09-06 (all `[RUN]` claims executed today in this WSL dev shell)
**Scope:** INFRA-01, INFRA-02, INFRA-06 — gate commands + harness mechanics only (skeleton mechanics INFRA-03/05/SETUP-01 are the sibling researcher's scope).
**Confidence:** HIGH — every gate command below was executed and its exit behavior observed in this environment.

## Summary

Every gate the phase needs has a verified, runnable form: `python3.6 -m py_compile` (3.6.9, catches 3.7+/3.8+ *syntax*), an AST-based purity checker (stdlib `ast` — precisely distinguishes module-level vs function-body imports, immune to bioCHEMeleon's docstring false-positive problem), scope-limited `unittest discover`, and — for the Windows legs — `cmd.exe /c C:\src\run-conda-pymol.bat -cq` (works from repo root with **no staging copy**, because the repo lives on `/mnt/c`) plus direct WSL exec of `xtb.exe` from a `/mnt/c` cwd.

Live probes closed three unknowns: (1) runtime Python is **3.9.13** / Qt **5.12.9** (PyQt5) — closes STACK.md Open Question 2; (2) `pymol.Qt` and `pymol.plugins.addmenuitemqt` import headlessly and `addmenuitemqt` *calls* safely (raises catchable `QtNotAvailableError`), but widget **construction** C-aborts uncatchably — the human-verify boundary is exactly "anything that constructs a QWidget"; (3) **exit codes through the .bat are always 0** (even after the C-abort), so smokes must assert printed sentinels, never exit codes.

INFRA-02 reading confirmed: "no pymol/Qt/numpy at module level **or in function bodies**" [SRC: .planning/REQUIREMENTS.md:65] means pure modules never import them, period — grep/AST-enforceable as "zero matches". ARCHITECTURE.md:355's lazy-numpy allowance applies only to *non-pure* modules; the :356 gate (`grep -rnE "from pymol|import pymol|from PyQt5|import numpy" …` must return zero) matches the strict reading.

**Primary recommendation:** one entry point `python3.6 tests/run_gates.py` running 3 WSL-native gates (py_compile walk → AST purity check → unittest discover subprocess) + 2 flag-gated Windows gates (`--smoke`, `--xtb`); fail with `file:line` messages and exit 1.

## Q1. Existing proven patterns

### test_wsl_winxtb.sh (4 lines, repo root)
```bash
CWD=`pwd`                      # [SRC: test_wsl_winxtb.sh:2]
cd tmp/xtb_test                # cwd on /mnt/c → Windows process inherits C:\ cwd
${CWD}/xtb-6.7.1/bin/xtb.exe phenol.xyz --ohess > phenol_ohess.log 2>&1
```
Exe invoked via **WSL-style absolute path**, args are **bare relative filenames**, cwd is a `/mnt/c` dir. Re-verified today: `--version` → `xtb version 6.7.1pre (5071a88) compiled 2024-07-23`, `normal termination of xtb`, exit 0 `[RUN]`.

### bioCHEMeleon gate commands (all documented [SRC: tmp/bioCHEMeleon/AGENTS.md])
| Gate | Command | AGENTS.md line |
|---|---|---|
| Syntax | `python3.6 -m py_compile biochemeleon/*.py` | :31 |
| Unittest | `python3.6 -m unittest tests.test_setup_state -v` | :34 |
| Purity grep (must return ZERO) | `grep -rnE "import Tkinter\|…\|from PyQt5 import\|import PyQt5" biochemeleon/` | :39 |
| Modeless gate | `grep -rnE "\.exec_\(\)" biochemeleon/` (hits allowed only on child dialogs) | :43 |
| Headless smoke | `cd tmp/bioCHEMeleon && timeout 90 cmd.exe /c "C:\\src\\run-conda-pymol.bat -cq smoke\\phase3_smoke.py" 2>&1 \| tail -50` | :19 |

### bioCHEMeleon tests & the stub lesson
5 test files (`test_setup_state/game_controller/registry/persistence/generators.py`). Every one stubs first:
```python
if 'pymol' not in sys.modules:
    sys.modules['pymol'] = MagicMock()
    sys.modules['pymol.Qt'] = MagicMock()
```
[SRC: tmp/bioCHEMeleon/tests/test_setup_state.py:13-17, test_game_controller.py:24-26; AGENTS.md:74]
**Why stubs were needed:** `biochemeleon/__init__.py` imports `from pymol.Qt import …` at *module level* [SRC: ARCHITECTURE.md F23, :39]. **Implication for serpentrum (INFRA-02 zero-stub mandate):** the entry module must not import pymol/Qt at module level (defer into `__init_plugin__`), and tests import only pure modules — then no stub is possible or needed. Verified feasible: `unittest discover` + pure-module imports run clean under 3.6 with zero stubs `[RUN]`.

## Q2. Gates verified in this environment today

| Check | Command | Result |
|---|---|---|
| Interpreter | `python3.6 --version` | `Python 3.6.9` `[RUN]` |
| No numpy | `python3.6 -c "import numpy"` | `ModuleNotFoundError: No module named 'numpy'` `[RUN]` |
| Stdlib present | `python3.6 -c "import subprocess, argparse, unittest, glob, ast, py_compile, sys, os, tempfile, shutil"` | all OK `[RUN]` |
| py_compile syntax gate | `python3.6 -m py_compile <file>` | walrus file → `SyntaxError`, rc=1; clean files → rc=0 `[RUN]` |
| Purity grep | `grep -rnE "from pymol\|import pymol\|from PyQt5\|import numpy" <dir>` | catches module-level **and** function-body imports; exit 0 = matches (gate FAIL), exit 1 = clean (gate PASS) `[RUN]` |
| unittest discovery | `python3.6 -m unittest discover -s <dir> -p "test_*.py" -v` | works; ran 1 test, rc 0 `[RUN]` |

**Grep-gate semantics gotcha:** grep exits **0 when matches found** — the gate passes on rc 1. Invert in the harness.
**Grep false positives (verified):** a docstring containing the literal text `from PyQt5 import` trips the grep `[RUN]`; bioCHEMeleon hit this exact bug [SRC: bioCHEMeleon AGENTS.md:38].

### Recommended: AST purity checker (verified under 3.6)
Because INFRA-02 bans imports "in function bodies" too, plain grep cannot express the entry-module rule (module-level banned, lazy allowed). A ~90-line stdlib-`ast` checker does it precisely — verified `[RUN]` on a scratch tree:
- pure module with `import numpy` in a function body → FAIL `pure module imports 'numpy'` (file:line)
- pure module, docstring mentioning "from PyQt5 import" → PASS (no false positive)
- entry `__init__.py` with `from pymol import cmd` at module level → FAIL `entry imports 'pymol' at module level`
- entry `__init__.py` with lazy `from pymol.plugins import addmenuitemqt` inside `__init_plugin__` → PASS
- exit 1 on any violation, 0 clean

Implementation notes that mattered (from the verification run):
- "module-level" = **direct child of the module body** — do NOT `ast.walk()` into FunctionDef from `tree.body`, or lazy imports get misflagged (bug caught during verification).
- "never anywhere in pure modules" = walk all nodes, flag any `Import`/`ImportFrom` whose root module ∈ {`pymol`, `PyQt5`, `numpy`}.
- Whole-package rule: any `ImportFrom` with module starting `PyQt5` → FAIL (must go through `pymol.Qt`) [SRC: PITFALLS.md:335, STACK.md:160].
- Modeless gate: same AST walk can flag `Call(func=Attribute(attr='exec_'))` hits with file:line, replacing the grep allowlist dance; the raw grep stays as the documented manual equivalent [SRC: PITFALLS.md:133].

### unittest discovery must be scoped to tests/
Verified failure mode: `discover -s .` wandered into package dirs, tried importing `entry/__init__.py` → `ModuleNotFoundError: No module named 'pymol'`, rc 1 `[RUN]`. The harness must use `discover -s tests` only — which also structurally enforces "tests import pure modules only".

## Q3. Headless Windows PyMOL smoke mechanics

**run-conda-pymol.bat** (user directed: don't read, just call): documented behavior [SRC: bioCHEMeleon AGENTS.md:13-20] — passes args through to `python …/pymol/__init__.py %*`; `-cq` = command-line, quiet (no GUI). Observed `[RUN ×3]`: accepts `-cq <script>` with a Windows-style relative script path and executes it.

**Staging: NONE needed for headless smokes.** The repo is on `/mnt/c`, so from repo root:
```bash
timeout 90 cmd.exe /c "C:\\src\\run-conda-pymol.bat -cq tmp\\smoke_probe.py" 2>&1 | tail -40
```
works directly — cmd.exe inherits cwd `C:\Users\nglok\Desktop\WORKDIR\molmdl\serpentrum` `[RUN]`. bioCHEMeleon's `wsl2win_cp.sh` staging was for the Plugin-Manager *install* flow, not the headless run. `tmp/` is gitignored [SRC: .gitignore:22] — suitable for probe scratch; committed smoke scripts should live in `smoke/`.

**Probe results `[RUN]`** (script printed `sys.version`, imported `pymol`, `pymol.Qt.QtWidgets`, `pymol.plugins.addmenuitemqt`; output flushed line-by-line):
```
PROBE python: 3.9.13 | packaged by conda-forge | (main, May 27 2022 …) [MSC v.1929 64 bit (AMD64)]
PROBE pymol import OK, __version__ = n/a
PROBE pymol.Qt.QtWidgets import OK: <module 'PyQt5.QtWidgets' from 'C:\Users\nglok\.conda\envs\chemtools-win10\…'>
PROBE QT_VERSION_STR = 5.12.9
PROBE addmenuitemqt import OK: <function addmenuitemqt at 0x…>
PIPED-EXIT=0
```

**Probe 2/3 — what a smoke may call headlessly `[RUN]`:**
| Action | Result |
|---|---|
| `from pymol.Qt import QtWidgets` (import only) | OK |
| `addmenuitemqt("…", cb)` **call** | raises **catchable** `QtNotAvailableError()` — try/except works |
| `QtWidgets.QDialog()` construction | Qt C-level abort: `QWidget: Must construct a QApplication before a QWidget` — **uncatchable, process dies** |
| Exit code after C-abort, through the .bat | **still 0** (twice) |

**Consequences for the harness (all verified):**
1. **Sentinel assertion, never exit codes:** smoke scripts print `SMOKE-OK <name>` / `SMOKE-FAIL <reason>` with `flush=True`; the harness greps captured output for the sentinel. (Python stdout is block-buffered when piped — unflushed prints were lost when the process aborted `[RUN]`.)
2. Phase-1 headless smoke CAN assert: plugin package imports under the real loader name `pymol.plugins.startup.serpentrum` [SRC: PITFALLS.md:172], `__init_plugin__` exists/callable, Qt import path works, `addmenuitemqt` callable (wrapped in try/except).
3. CANNOT assert headlessly: dialog construction/show/tab visuals → **human-verify checkpoint** [SRC: ARCHITECTURE.md:351].
4. Unverified open option (one-line spike, optional): `QT_QPA_PLATFORM=offscreen` + explicit `QApplication` construction *before* widget construction might enable headless dialog-construction asserts. Do not rely on it unverified.

## Q4. Windows xtb invocation from WSL (INFRA-01 third leg)

**Proven pattern (re-verified today):** from a `/mnt/c` cwd, exec the exe by WSL-style path with bare relative args `[RUN]`:
```bash
CWD=$(pwd) && cd tmp/xtb_test && timeout 60 ${CWD}/xtb-6.7.1/bin/xtb.exe --version 2>&1
# → "xtb version 6.7.1pre (5071a88) … normal termination of xtb", exit 0
```
Exe lives at `<repo>/xtb-6.7.1/bin/xtb.exe` [RUN: exists].

**Path-conversion rules (dev side):**
| Element | Rule | Evidence |
|---|---|---|
| exe path (direct exec) | WSL-style `/mnt/c/…` OK | test_wsl_winxtb.sh:4 + `[RUN]` |
| exe path (via `cmd.exe /c`) | Windows-style `C:\…` required | probe `[RUN]` (bat called as `C:\src\…`) |
| cwd | must be a `/mnt/c`-visible dir → Windows inherits matching `C:\` cwd | bioCHEMeleon AGENTS.md:22 + `[RUN]` |
| file args | bare relative filenames — never absolute `/mnt/c` paths | test_wsl_winxtb.sh:4 |
| WSL→Windows string conversion | only in dev/headless helpers (`to_windows_path`, `/mnt/c/X` → `C:\X`) | [SRC: bioCHEMeleon demos.py:59-74, PITFALLS.md:333] |
| **Plugin runtime** | **no conversion at all** — Windows PyMOL + Windows exe + temp-dir cwd + relative names | [SRC: STACK.md:83, PITFALLS.md:333] |

**Fixtures (phase-2 parser input; confirmed non-trivial today):**
- **Authoritative:** `.planning/research/xtb-spike-fixtures/` — `g98.out` 68 047 B, `hessian` 100 078 B, `vibspectrum` 5 071 B (non-empty), `ohess.log`/`repro_oh.log`/`co2.log`/`dimer2.log` (33–53 KB each), plus corrupted-input case `bad.xyz`/`bad.log`/`bad.err` [RUN: ls; SRC: SUMMARY.md:18].
- `tmp/xtb_ohess_test/` has a real `g98.out` with `Frequencies --` blocks but its `vibspectrum` is **0 bytes** (partial run) — *not* fixture-grade; do not point the parser at it `[RUN: wc -c]`.

## Q5. Unified harness design (feasibility verified under 3.6)

```
serpentrum/            # plugin package (purity classes enforced by gate)
smoke/                 # headless Windows PyMOL scripts (cmd-only), print sentinels
tests/                 # WSL python3.6 unittest — pure modules ONLY, zero stubs
  run_gates.py         # single entry point
tools/
  check_purity.py      # AST purity/hygiene checker (stdlib ast, py3.6)
```
[SRC: ARCHITECTURE.md:136-137 layout; bioCHEMeleon AGENTS.md commands]

**Single entry:** `python3.6 tests/run_gates.py [--smoke] [--xtb]`

| # | Gate | Where | Mechanism (all verified) |
|---|---|---|---|
| 1 | Syntax (INFRA-06) | WSL | walk package `.py`, `py_compile.compile(f, doraise=True)`; any failure → file:line, exit 1 |
| 2 | Purity/hygiene (INFRA-02) | WSL | `tools/check_purity.py` (AST): pure modules zero pymol/Qt/numpy anywhere; entry module-level ban + lazy allow; whole-package `from PyQt5` ban; `.exec_()` report; exit 1 + file:line |
| 3 | Unit tests | WSL | subprocess `python3.6 -m unittest discover -s tests -v` (scope-limited; rc propagates) |
| 4 | Headless PyMOL smoke (INFRA-01) | Windows | `timeout 90 cmd.exe /c "C:\\src\\run-conda-pymol.bat -cq smoke\\01_smoke.py"`, capture output, assert `SMOKE-OK` sentinel present (never exit code) |
| 5 | xtb probe (INFRA-01) | Windows | direct exec `xtb.exe --version` from `/mnt/c` cwd; assert `normal termination` in output |

Gates 1–3 are the default, WSL-native, sub-second run. Gates 4–5 are flag-gated (Windows-dependent, ~30–90 s). Harness skeleton feasibility verified: `subprocess`, `argparse`, `unittest`, `glob`, `ast`, `py_compile`, `tempfile`, `shutil` all import and behave under 3.6 `[RUN]`; `subprocess.run` → `cmd.exe` works with `stdout=subprocess.PIPE` `[RUN]`.

**3.6 harness-code constraint (verified gotcha):** `subprocess.run(capture_output=True)` is **3.7+** — `TypeError` under 3.6 `[RUN]`. Use `stdout=subprocess.PIPE, stderr=subprocess.PIPE`.

## Q6. py3.6 syntax discipline (what the gate catches — and doesn't)

**Caught automatically by the py_compile gate (SyntaxError under 3.6):**
- Walrus `:=` — verified `[RUN]` (file rejected, rc 1)
- Same class (not individually run, same parse-failure mechanism): f-string `=` specifier (3.8), positional-only `/` params (3.8)

**NOT caught by py_compile — parses fine, fails only at import time `[RUN]`:**
- `from dataclasses import dataclass` (3.7 stdlib) — compiled OK under 3.6; would ImportError at runtime. Same gap: `importlib.metadata`, `math.isqrt`, `typing.Protocol/Final` (3.8).
- `subprocess.run(capture_output=…)` kwarg (3.7+) `[RUN]`
→ These are caught by gate 3 (unittest imports every pure module under 3.6) as long as tests exercise the imports; note this residual gap in the plan.
**Safe under 3.6 (verified compile):** f-strings, variable annotations, `typing.List` comments, underscore literals `[RUN]`.

## Don't Hand-Roll

| Problem | Don't build | Use instead |
|---|---|---|
| Module-level vs lazy import detection | regex heuristics | stdlib `ast` checker (verified) |
| Windows invocation plumbing | custom path munging in gates | the two verified one-liners above |
| Smoke pass/fail | exit-code checks | printed sentinels + grep (exit codes lie through the .bat) `[RUN]` |
| Syntax gate | custom parser | `py_compile` (stdlib, verified) |

## Common Pitfalls (verified today)

1. **Exit-code trust through run-conda-pymol.bat** — always 0, even after Qt C-abort `[RUN ×2]`. Assert sentinels.
2. **Unflushed prints lost on abort** — block-buffered stdout when piped; every smoke print needs `flush=True` `[RUN]`.
3. **Grep gate inverted exit** — passes on rc 1, fails on rc 0.
4. **Docstring/comment false positives in grep gates** — bioCHEMeleon shipped this bug [SRC: AGENTS.md:38]; AST checker avoids it `[RUN]`.
5. **`ast.walk` into function bodies when checking "module level"** — misflags lazy imports (caught during verification).
6. **unittest discovery without `-s tests`** — imports package modules, crashes on missing `pymol` `[RUN]`.
7. **`capture_output=` kwarg** — 3.7+ only `[RUN]`.
8. **`tmp/xtb_ohess_test/vibspectrum` is 0 bytes** — partial run; use the committed research fixtures only `[RUN]`.

## Planning Implications

**Harness tasks (suggested order):**
1. `tools/check_purity.py` — AST checker (pure-module ban; entry module-level ban; PyQt5 ban; `.exec_()` report) + self-test against known-bad fixtures (like the scratch tree used here).
2. `tests/run_gates.py` — gates 1–3 wired, `--smoke`/`--xtb` flags, exit-1 aggregation with file:line messages.
3. `tests/` scaffold — first pure-module unittest, zero stubs; `discover -s tests` scoped.
4. `smoke/01_env_smoke.py` — the verified probe content as a permanent sentinel script (python/Qt versions, pymol.Qt import, addmenuitemqt try/except), wired to `--smoke`; xtb `--version` probe wired to `--xtb`.
5. Wire gates into AGENTS.md commands section.

**Verified (no human needed):** every command in this doc; runtime Python 3.9.13 / Qt 5.12.9 facts; addmenuitemqt catchable; no-staging headless run; xtb direct exec; fixture locations.

**Needs human-verify:** visible 3-tab dialog behavior (QApplication/widgets cannot be asserted headlessly `[RUN]`); optional later spike: `QT_QPA_PLATFORM=offscreen` QApplication-first construction (unverified).

## Sources

- [RUN] all table rows above — executed 2026-09-06 in this WSL shell
- [SRC] tmp/bioCHEMeleon/AGENTS.md:13-24, 31-46, 74 (gates, headless pattern, stub rationale)
- [SRC] .planning/REQUIREMENTS.md:64-69 (INFRA-01/02/06 wording); ROADMAP.md:39-40, 54
- [SRC] .planning/research/ARCHITECTURE.md:38-39 (F22/F23), 136-137, 351-356 (gate, testability split)
- [SRC] .planning/research/PITFALLS.md:133 (modeless gate), 172 (loader identity), 333-335 (path/Qt rules)
- [SRC] .planning/research/STACK.md:116-132 (dev tools), 160, 198-199 (open questions → closed by probes)
- [SRC] test_wsl_winxtb.sh:1-4; .gitignore:22 (tmp ignored)
