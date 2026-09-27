# Codebase Concerns

**Analysis Date:** 2026-09-27

This audit covers first-party code only: `serpentrum/`, `tests/`,
`smoke/`, `tools/`, and root files (`AGENTS.md`, `spec.md`,
`opencode.json`). Claims marked **[VERIFIED]** cite file:line evidence in
this repo; claims marked **[SPECULATIVE]** are structural risks inferred
from verified code shape, not observed failures. `.planning/` research
(`PITFALLS.md`) is treated as read-only project context.

The codebase is unusually disciplined: there are **zero**
`TODO`/`FIXME`/`HACK`/`XXX`/`WORKAROUND` markers in first-party Python
**[VERIFIED: repo-wide grep, no hits]**, and purity/modeless/plugin-path
invariants are enforced by AST gates (`tools/check_purity.py`,
`tests/run_gates.py`). The concerns below are the residual, structural
risks — not code smell from neglect.

---

## Tech Debt

**Python 3.6 ceiling (EOL runtime):**
- Issue: The entire plugin is pinned to `python3.6` syntax (`%-formatting`,
  no f-strings/walrus) and the gate runner invokes `sys.executable` under
  WSL 3.6.9. Python 3.6 reached end-of-life 2021-12-23 and receives no
  security fixes.
- Files: `AGENTS.md` (lines 8, 67-69), `tests/run_gates.py:133-136`,
  `tests/test_skeleton.py:1-10`, house style stated in nearly every module
  docstring (e.g. `serpentrum/xtb_runner.py:33`).
- Impact: The *test* interpreter is EOL. At runtime the plugin actually
  runs inside the Windows conda PyMOL 2.5.0 Python (not 3.6), so the
  shipping runtime is not 3.6 — but the 3.6 gate is the only thing keeping
  syntax compatible and it is unmaintained. A future PyMOL/Python upgrade
  could silently diverge from the 3.6-tested surface.
- Fix approach: Migrate the dev/test interpreter to the Python version
  shipped by PyMOL 2.5.0 and re-pin `run_gates.py`; the code is written in
  a conservative style that upgrades cheaply. Note: this is a
  dev-toolchain concern, not a stacked backlog claim.

**Oversized GUI / engine modules:**
- Issue: Several modules are large enough that single-file comprehension
  and safe editing degrade.
- Files (line counts **[VERIFIED]**):
  - `serpentrum/gui_game.py` — **1538 lines** (largest; game loop, HUD,
    placement, teardown, debug tracer)
  - `serpentrum/game_engine.py` — 823 lines
  - `serpentrum/molfile.py` — 694 lines
  - `serpentrum/gui_setup.py` — 672 lines
  - `serpentrum/hud_logic.py` — 571 lines
  - `serpentrum/pymol_bridge.py` — 566 lines
- Impact: `gui_game.py` concentrates timers, wizard lifecycle, placement,
  respawn, HUD, and the `SRP_DEBUG` tracer; edits there carry the highest
  regression surface (it is smoke-covered, not unit-covered — see below).
- Fix approach: If Phase 8 refactors, split `gui_game.py` along the
  existing test seams (tick loop / placement-capture / teardown / debug
  trace). Not urgent — behavior is pinned by smoke 04/05/06/08/10/13.

**Broad `except Exception` swallows edge-on failure silently:**
- Issue: The Apply path computes the head's edge-on transform inside a
  blanket `except Exception: head_m16 = None`.
- Files: `serpentrum/gui_setup.py:600-611`.
- Impact: A malformed `stack_ring` / parse slip renders the head
  as-stored (no edge-on) with **no user-visible or debug signal**. This is
  the same class as the 05-16 "perpendicular-stack" defect that was
  invisible because checks were distance-only.
- Fix approach: Narrow the except to `molfile.MolFileError` /
  `ValueError` and emit an `SRP_DEBUG`-gated log line (or a status line)
  on capture, so a failed edge-on never disappears.

**Viewer-side constants mirrored into tests by value:**
- Issue: Integration tests re-declare bridge/engine constants as literals
  rather than importing them (they cannot import `pymol_bridge` — module
  level `from pymol import cmd`).
- Files: `tests/test_phase5_integration.py:80` (`DISPLAY_Z = 5.0`),
  `tests/test_phase51_integration.py:43` (`TICK_DT = 0.1`),
  `tests/test_phase52_integration.py:58-62` (`TICK_DT`, `BOX_DISPLAY_Z`).
- Impact: Drift risk — changing `pymol_bridge.BOX_DISPLAY_Z`
  (`pymol_bridge.py:66`) or `gui_game.TICK_DT` (`gui_game.py:99`) would
  not fail these tests, only the smokes.
- Fix approach: Acceptable given the purity ban, but add a smoke assertion
  that reads the live constant (smoke 08 already exercises the box path).

**README / docs still "TBD":**
- Issue: `README.md` Usage, Demo Molecules set, Project Structure, and
  Acknowledgements are all `TBD`; `serpentrum/data/DATA_SOURCES.md` is
  DRAFT-headed pending Phase 8 sign-off.
- Files: `README.md` (lines ~30-75), `.planning/ROADMAP.md:29` (Phase 8).
- Impact: Release-audit deliverable, scheduled — not an unplanned gap.

---

## Known Bugs

**Selector-Error noise when the spectra overlay zooms before arrows exist (owner-accepted):**
- Symptoms: In real Windows PyMOL, `zoom_mode_frame()` can fire while
  `srp_mode_vec` is absent, producing benign Selector-Error lines for
  `'srp_mode_vec'` / `'srp_xtbopt or srp_mode_vec'`. The zoom still
  succeeds on `srp_xtbopt`.
- Files: `serpentrum/pymol_bridge.py:552-565`, consumer
  `serpentrum/gui_spectra.py:471-473`.
- Trigger: Clicking a table row on the first record before the CGO arrows
  are loaded — the `object_exists` guard checks both names but `cmd.zoom`
  can still race/emit through the selection parser.
- Workaround: None needed; owner approved the phase **with the noise
  visible**. Candidate fix recorded: zoom only on `srp_xtbopt` when
  `srp_mode_vec` is absent.
- Source: STATE 2026-09-26 (07-10 phase-close). **[VERIFIED]**

**`smoke/02_dialog_smoke.py` is a known informational FAIL (not required):**
- Symptoms: The headless dialog-construction smoke fails by design/known
  limitation and is deliberately excluded from `REQUIRED_SMOKES`.
- Files: `tests/run_gates.py:55-72` (02 absent from `REQUIRED_SMOKES`),
  `.planning/HANDOFF-2026-09-20-phase5-resume.md:35` ("smoke 02
  informational FAIL known").
- Impact: `PluginDialog` construction (and therefore `SpectraTab` import)
  has **no green automated headless check**. See coverage gaps below.
- Workaround: Dialog verdicts are human-verify (STATE decision 01-05:
  offscreen Qt route is a dead end).
- **[VERIFIED]**

---

## Security Considerations

**Subprocess invocation is list-argv, no shell, quote-rejecting:**
- Risk: Command injection via a user-configured xtb path.
- Files: `serpentrum/xtbenv.py:113-191` — `validate_binary_path` rejects
  quote characters; `build_argv` returns a **list** and raises on any
  quote; `serpentrum/xtb_runner.py:206` uses
  `proc.start(argv[0], argv[1:])` (QProcess, no shell).
- Current mitigation: Strong — no `shell=True` anywhere in first-party
  code. **[VERIFIED: `shell=True` grep = 0 hits]**.
- Recommendations: None required. Keep the quote-rejection contract in
  sync if a future option accepts command-line args.

**Uploaded molecule files are parsed defensively but have no size cap:**
- Risk: A malformed or enormous upload can raise (handled) or consume
  unbounded memory / UI-thread time before any gate.
- Files: `serpentrum/molfile.py:107-141` (`read_sdf_text`/`read_sdf`),
  `serpentrum/xyzio.py:118-178` (`read_xyz_text`/`read_xyz`) — both read
  the entire file via `handle.read()` / `text.splitlines()` with no byte
  or atom count limit. Errors are structured (`MolFileError`/`XyzError`
  name the 1-based line + snippet).
- Current mitigation: All parse failures raise a typed, line-numbered
  error; `gui_setup._on_apply` (`gui_setup.py:483-528`) runs parsing on
  Apply. No explicit max file size / max atom guard was found.
- Recommendations: Add an explicit size/atom cap with a user-facing
  message before full parse. **[SPECULATIVE impact — no observed
  incident; the absence of a cap is VERIFIED.]**

**`SRP_SPECTRA_DIR` env override + prefix-guarded `rmtree`:**
- Risk: Recursive delete of a user-writable stable spectra dir.
- Files: `serpentrum/xtb_runner.py:59-60` (override resolution),
  `xtb_runner.py:227-250` (`_drop_prior_stable_dir` normalizes and only
  `rmtree`s a dir that `startswith(root_norm + os.sep)`), plus the spray
  dir deletes at `xtb_runner.py:332`/`357`.
- Current mitigation: The prefix guard prevents deleting outside the
  resolved base; the spray dir name is a `tempfile.mkdtemp` under
  `xtbenv.new_run_dir` (`xtbenv.py:194-207`). `snake_id` is
  game-generated `'run_%d' % epoch` (`gui_game.py:1427`) — no path
  traversal into the stable join (`xtb_runner.py:300-301`).
- Recommendations: None required; document the override in user docs
  (Phase 8).

**`srp_` object-prefix reservation is a deliberate no-undo hazard:**
- Risk: `cleanup_srp` deletes **every** `srp_*` object by name pattern; a
  user who names their own object `srp_*` loses it (PyMOL has no undo,
  PITFALLS F17).
- Files: `serpentrum/pymol_bridge.py:129-143`, `AGENTS.md:76`.
- Current mitigation: Documented policy; cleanup depends on no plugin
  state so it works after `.pse` reload (INFRA-04).
- Recommendations: Surfaced in Phase 8 Help text.

---

## Performance Bottlenecks

**Gaussian broadening is pure-Python O(n_points × n_modes):**
- Problem: `broaden()` (`n_points=800` default) evaluates one `math.exp`
  per mode per grid point.
- Files: `serpentrum/spectra.py:433-475`.
- Cause: numpy is available in the PyMOL runtime but the pure layer
  (correctly) avoids it; the doubled loop is `~800 × n_modes` exp calls.
- Impact: For a ~100-atom snake (~300 real modes) this is ~240k exp
  calls, plus re-derivation on every plot option change
  (`plot_logic.scene_with_unit`). The parse + broaden run **on the UI
  thread** (`gui_spectra.py:294-363`, explicitly noted as "legal … the
  787-line fixture parses in ms").
- Improvement path: Cache the base scene (already done — panels derive
  from the base intensity scene) and, if a large molecule stutters,
  precompute on the QProcess side or vectorize against numpy **only in the
  GUI layer** (pure layer stays numpy-free). **[SPECULATIVE magnitude —
  no measured jank; the structure and UI-thread placement are VERIFIED.]**

**Uncapped xtb threading is mitigated by a measured argv cap:**
- Problem: xtb grabs all cores by default, janking PyMOL rendering during
  spectra.
- Files: `serpentrum/xtb_run.py:73-81` (`DEFAULT_THREAD_ARG = ('-P','4')`),
  calibration note: ~18% extra wall (107.6 s vs 91.4 s at 104 atoms) to
  leave 4 hardware threads for rendering.
- Current mitigation: Shipped and calibrated (SC5). **[VERIFIED]**

**Per-tick viewer coupling is translate-only (good):**
- Problem: Late-game per-tick `cmd.*` chatter scaling with snake length.
- Files: `serpentrum/pymol_bridge.py:179-193` (`move_chain_delta`, ONE
  `cmd.translate` on a wildcard), `game_engine.py` train-follow.
- Current mitigation: No per-tick `cmd.get_model` / CGO rebuild for the
  chain; `chain_atom_counts` (`pymol_bridge.py:457-484`) is
  completion-only. **[VERIFIED]**

---

## Fragile Areas

**WSL↔Windows boundary (the single most common breakage class):**
- Files: `AGENTS.md:4-12`, `tools/winpath.py`, `tests/run_gates.py:145-158`
  and `201-275`.
- Why fragile: Windows PyMOL cannot resolve `/mnt/c/...`; Windows VMD
  needs `C:/...` while `cmd.exe` targets need `C:\...`. Headless smokes
  invoked through `C:\src\run-conda-pymol.bat` **always exit 0 even after
  a Qt C-abort**, so verdicts must use flushed `SMOKE-OK` sentinels, never
  exit codes.
- Safe modification: Any new smoke must flush a sentinel; `run_gates`
  asserts on `'SMOKE-OK' in out and 'SMOKE-FAIL' not in out`
  (`run_gates.py:157`). Windows-only paths cannot be unit-tested in WSL.
- Test coverage: sentinel smokes + human-verify only.

**Module-identity / reload anchor:**
- Files: `serpentrum/__init__.py:10-67` (state on
  `pmg_tk.startup._serpentrum`), pinned by
  `smoke/01_skeleton_smoke.py` reload + double-import steps.
- Why fragile: A stray module-global for mutable live state would
  duplicate on Plugin-Manager reload or a second import name. The anchor
  is the single defense.
- Safe modification: Never add live-state module globals; extend
  `_SerpentrumState` instead.

**Plugin-path safety (hard rule):**
- Files: `tests/run_gates.py:100-116`.
- Why fragile: The dev install points PyMOL's plugin loader at the repo
  root; a stray top-level `*.py` or an `__init__.py` in `tests/`, `smoke/`,
  or `tools/` is autoloaded as a **second plugin** at GUI startup.
- Safe modification: Gate 1 enforces both; never commit either.

**QApplication-missing hard kill for font/renderer access:**
- Files: `AGENTS.md:71`, `smoke/12_plot_smoke.py` stage 0.
- Why fragile: Touching `QPainter`/`QFontMetrics`/`drawText` with no
  `Q*Application` **silently hard-kills the process with no traceback**
  (probe RUN A). Any new renderer smoke must first do
  `app = QApplication.instance() or QApplication([])`.

**Arrow-key steering via Wizard (never `cmd.set_key`):**
- Files: `serpentrum/input.py:1-158`.
- Why fragile: Up/down never fire through `set_key` (C `PyMOL_Special`
  force-grabs), and left/right would leak a session-global
  `cmd.key_mappings` binding. Teardown depends on the saved wizard being
  carried on the live wizard object (`input.py:145-158`).
- Safe modification: Always `install`/`set_active`/`teardown`; never
  touch `key_mappings`.

**xtb cancel/relaunch/double-run lifecycle:**
- Files: `serpentrum/xtb_run.py:98-121` (`can_start`,
  `resolve_status`), `serpentrum/xtb_runner.py:214-221` (`cancel` =
  `proc.kill()`), `xtb_runner.py:328-332` (spray dir deleted **only**
  after `finished` — a pre-finished `rmtree` races xtb's open file handles
  on Windows, `WinError 32`).
- Why fragile: Cancel must win over a lingering `'normal termination'` in
  partially-captured stderr; `finished` does not follow a synchronous
  `FailedToStart` (handled in `_on_error`).
- Test coverage: `smoke/11_xtb_runner_smoke.py` (informational — see
  gaps) + owner live checkpoint.

**PyMOL has no undo + `.pse` desync:**
- Files: `serpentrum/pymol_bridge.py:21-45`, PITFALLS.md F17 / 8.3.
- Why fragile: `.pse` saves viewer objects but **no plugin Python state**;
  cleanup must work in a fresh process from object names only. Restart
  hygiene (`gui_game.rebuild_scene` → `cleanup_srp` before materialize) is
  load-bearing — the 2026-09-19b fix for old-run `srp_seg_*` riding the
  `move_chain_delta` wildcard.

---

## Scaling Limits

**Hessian atom budget is warn-and-proceed, and wins routinely exceed it:**
- Current capacity: `atom_budget=100` default.
- Limit: A default win snake (10 stacked + head = 11 molecules × 12-24
  atoms) runs 130-260 atoms, so the budget is exceeded on the **normal
  win path**; hessian cost scales ~N³.
- Files: `serpentrum/budget_guard.py:1-52` (explicitly documented as
  structurally mandatory warn-and-proceed, never a block),
  `serpentrum/game_engine.py:726-731` (win freezes at cap).
- Scaling path: The warning + revealed counts are shipped; actual wall
  time at cap was calibrated (104 atoms ≈ 91-108 s on the calibration
  machine, `xtb_run.py:74-79`). Larger molecules are user-upload-driven
  and unguarded beyond the warning.

**No documented fallback if QProcess is unavailable in the conda build:**
- Files: `.planning/ROADMAP.md:265` ("fallback = worker+queue+QTimer
  drain (documented, unbuilt)").
- Limit: If `QtCore.QProcess` were missing/behaving differently in the
  Windows conda PyMOL, the async pipeline has no built alternative.
- Current mitigation: `smoke/09_qprocess_smoke.py` probes availability
  (informational), and the shipped pipeline works in the owner's live
  checkpoints. **[VERIFIED risk is documented-but-unbuilt; not an
  observed failure.]**

---

## Dependencies at Risk

**Python 3.6 (EOL) test interpreter** — see Tech Debt. Files:
`AGENTS.md:8`, `tests/run_gates.py:133`.

**xtb 6.7.1 Windows pre-release:**
- Risk: The repo pins the 6.7.1 **pre-release** because 6.7.0's Windows
  build is missing a DLL; a pre-release is by nature less stable.
- Files: `README.md` (Requirements), PITFALLS.md:334, `AGENTS.md:12`.
- Impact: The entire spectra feature depends on this specific binary.
- Migration plan: Pin and log the detected version (detect probe order in
  `xtbenv.detect_binary`, `xtbenv.py:141-167`).

**No dependency lockfile / requirements file:**
- Risk: Runtime deps are assumed to come from PyMOL (`numpy`, PyQt5 via
  `pymol.Qt`); there is no manifest pinning them.
- Files: absence of `requirements.txt` / `pyproject.toml` / lockfile in
  repo root **[VERIFIED]**; policy stated in `README.md` and
  `AGENTS.md:19-22`.
- Impact: Low while the dependency set is "whatever PyMOL ships"; any
  added lib must go through user approval + `3rd_party_lib/` (git-ignored)
  with a license note (`README.md`, PITFALLS security table).

**No matplotlib/scipy (deliberate):**
- Files: PITFALLS.md:339; plot is a custom `QWidget.paintEvent`/`QPainter`
  (`serpentrum/gui_plot.py`). No risk beyond intentional constraint.

---

## Missing Critical Features

**Phase 8 (unplanned/TBD) release deliverables:**
- Problem: Usage docs, 6-button setup Save/Load persistence, Help text,
  demo-data full attribution sign-off, and end-to-end release audit are
  not yet delivered.
- Files: `.planning/ROADMAP.md:29` (Phase 8), `README.md`
  (all TBD sections), STATE.md "Phase 8 unplanned/TBD".
- Blocks: A shippable "1.0". Everything else (Phases 1-7) is COMPLETE.

**Upload-only run has no win condition (owner-acknowledged, C2 opt-in only):**
- Problem: A set with zero stackable species yields an endless run.
- Files: `.planning/debug/resolved/05-upload-only-endless-run.md` (C1/C4
  shipped; **C2 soft Apply-time warning left as owner opt-in**),
  `.planning/HANDOFF-2026-09-20-phase5-resume.md:26`.
- Blocks: Nothing critical; a UX honesty gap for a degenerate set.

**Edge-biased pickup spawn distribution (deferred by owner):**
- Files: `.planning/ROADMAP.md:26`; sketch in 5.3-05-SUMMARY.
- Blocks: Difficulty polish only; `MIN_HEAD_DIST_FACTOR = 0.35` ships.

---

## Test Coverage Gaps

Coverage model: pure modules are unit-tested under WSL python3.6;
GUI/BRIDGE modules are covered by headless Windows PyMOL smokes
(sentinel verdicts) + human-verify. The tradeoff is that WSL cannot test
anything importing `pymol`/`Qt`.

**`serpentrum/gui_spectra.py` has no direct test and no direct smoke:**
- What's not tested: The entire SpectraTab — `_populate_spectrum`
  precedence (g98-first / vibspectrum fallback), degenerate resets,
  table population, row-click vector loading, Run-again/Cancel delegation.
- Files: `serpentrum/gui_spectra.py` (499 lines). Repo-wide grep found
  **zero** references to `gui_spectra`/`SpectraTab` in `tests/` or
  `smoke/`. It is only constructed transitively by `PluginDialog()`
  (`serpentrum/gui.py:107`), i.e. by `smoke/02_dialog_smoke.py` — which is
  a **known informational FAIL and not in `REQUIRED_SMOKES`**.
- Risk: A regression in the shipped Spectra UI would not be caught by the
  gate battery; only `plot_logic`/`spectra_ui` pure helpers are
  unit-tested (`tests/test_plot_logic.py`, `tests/test_spectra_ui.py`) and
  `gui_plot` is smoked (`smoke/12`).
- Priority: High — this is the largest untested surface and a shipped
  feature.

**`serpentrum/xtb_runner.py` (Qt shell) is smoke-only, and its smoke is informational:**
- What's not tested: `XtbRunController` signal wiring, connect-before-start,
  cancel/double-run/relaunch, stable-dir keep-until-replaced.
- Files: `serpentrum/xtb_runner.py` (380 lines); covered by
  `smoke/11_xtb_runner_smoke.py` which is **not** in
  `tests/run_gates.py:55-72` `REQUIRED_SMOKES` (owner instructed no
  promotion, STATE 2026-09-26 06-12).
- Risk: The runner's Qt mechanics are pinned only by an owner-waived,
  non-blocking smoke. The pure decision half (`xtb_run.py`) is
  unit-tested (`tests/test_xtb_run.py`) but the Qt shell is not.
- Priority: Medium-High.

**GUI/BRIDGE modules covered by smokes only (Windows-untestable in WSL):**
- Files/modules: `serpentrum/gui.py`, `gui_game.py` (1538 lines),
  `gui_setup.py` (672 lines), `gui_plot.py`, `input.py`,
  `pymol_bridge.py`, `xtb_runner.py`. No `test_*.py` imports them (grep
  of test imports shows the pure-module set only).
- Risk: Applies to ~4,600 lines of viewer/Qt code. Mitigated by required
  smokes 01/03/04/05/06/07/08/10/12/13 and human-verify, but WSL unit
  tests can never reach them (module-level `from pymol import cmd` in
  `pymol_bridge.py:52` / `input.py:60`).
- Priority: Medium (accepted architecture tradeoff — keep the pure layers
  thick, as the repo already does).

**Windows-only paths are untestable in the WSL unit layer:**
- What's not tested at unit level: WSL→Windows path conversion
  (`tools/winpath.py` is unit-tested, but the real cmd.exe invocation is
  not), `.bat` exit-code swallowing, QProcess-in-conda behavior, xtb.exe
  exec from WSL.
- Files: `tests/run_gates.py:145-158` (smoke leg), `:201-275` (xtb leg);
  `tests/test_winpath.py` covers only the pure conversion.
- Risk: Boundary regressions surface only in `--smoke` / `--xtb` gate runs
  or live checkpoints.
- Priority: Medium; requires Windows access to close.

**Informational-only smokes (non-blocking):**
- `smoke/02_dialog_smoke.py` (known FAIL), `smoke/09_qprocess_smoke.py`,
  `smoke/11_xtb_runner_smoke.py` are run when present but **never fail the
  gate** (`tests/run_gates.py:192-197`).
- Risk: Dialog construction, QProcess availability, and the xtb runner can
  regress without a red gate. The `--xtb` gate (`run_gates.py:201-275`)
  covers the binary invocation but not the runner.

---

## Test Coverage Gaps Summary (module → coverage)

| Module | Unit test | Smoke | Gate-required smoke |
|--------|-----------|-------|---------------------|
| `game_engine.py` | yes (engine_*) | — | — |
| `molfile.py` / `xyzio.py` | yes | — | — |
| `spectra.py` / `spectra_ui.py` / `plot_logic.py` | yes | 12 (plot) | 12 |
| `pymol_bridge.py` | no (bridge) | 03/07/08 | 03/07/08 |
| `input.py` | no (bridge) | 06/13 | 06/13 |
| `xtb_run.py` / `xtbenv.py` | yes | — | — |
| `xtb_runner.py` | no | 11 (info) | **no** |
| `gui.py` | no | 01/02 (02 = info FAIL) | 01 |
| `gui_game.py` | no | 04/05/08/10/13 | 04/05/08/10/13 |
| `gui_setup.py` | no | 04/08 | 04/08 |
| `gui_plot.py` | no | 12 | 12 |
| `gui_spectra.py` | **no** | **none direct** | **no** |

---

*Concerns audit: 2026-09-27*
