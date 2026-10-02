# Codebase Concerns

**Analysis Date:** 2026-10-02

This audit covers first-party code only: `serpentrum/`, `tests/`, `smoke/`,
`tools/`, and root files (`AGENTS.md`, `spec.md`, `README.md`,
`opencode.json`). Claims cite file:line evidence in this repo unless marked
**[SPECULATIVE]**. `.planning/research/PITFALLS.md` and the phase summaries
are treated as read-only project context.

State at this update: Phases 1-7 complete and human-approved. **Phase 8
(Demo Data, Docs & Release Audit) is 10/11 plans executed and is blocked on
the consolidated **GATE V** owner checkpoint** (`.planning/phases/08-*/08-11-
SUMMARY.md`, `status: checkpoint-presented`). The default gate battery is
green: **937 unittests OK**, gates 1-3 PASS (`python3.6 tests/run_gates.py`,
re-verified 2026-10-02). There are **zero** `TODO`/`FIXME`/`HACK`/`XXX`/
`WORKAROUND` markers in first-party Python; the only `TODO` tokens live in
`serpentrum/data/DATA_SOURCES.md:78,166` (Phase-8 data tasks, see below).

The concerns below are residual structural risks and the live Phase-8
release blockers — not code smell from neglect.

---

## Tech Debt

**Python 3.6 ceiling (EOL test interpreter):**
- Issue: The gate runner and unit suite run under WSL `python3.6` (3.6.9),
  which reached end-of-life 2021-12-23 and receives no security fixes. All
  modules are written in a 3.6-compatible style (`%`-formatting, no
  f-strings/walrus).
- Files: `AGENTS.md:8`, `tests/run_gates.py:133-136` (`sys.executable`),
  `tests/test_skeleton.py`, house-style docstrings throughout `serpentrum/`.
- Impact: The runtime plugin actually executes inside the Windows conda
  PyMOL 2.5.0 Python (not 3.6), so this is a *dev-toolchain* ceiling — but
  it is the only thing keeping syntax compatibility honest, and it is
  unmaintained.
- Fix approach: Re-pin the dev/test interpreter to the Python shipped by
  PyMOL 2.5.0; the conservative style upgrades cheaply.

**Oversized GUI / engine modules (grew since last audit):**
- Issue: Several modules are large enough that single-file comprehension and
  safe editing degrade. `gui_game.py` grew 1538 → **1572** lines and
  `gui_setup.py` grew 672 → **953** lines (Phase 8 added the bottom action
  row + save/load handlers + hints).
- Files (line counts confirmed `wc -l` 2026-10-02):
  - `serpentrum/gui_game.py` — **1572** (largest: game loop, HUD, placement,
    respawn, teardown, debug tracer)
  - `serpentrum/gui_setup.py` — **953** (now second; setup widgets, apply,
    save/load, hints)
  - `serpentrum/game_engine.py` — 823
  - `serpentrum/molfile.py` — 694
  - `serpentrum/spawn.py` — 581
  - `serpentrum/hud_logic.py` — 571
  - `serpentrum/pymol_bridge.py` — 566
  - `serpentrum/gui_spectra.py` — 517
  - `serpentrum/gui_plot.py` — 507
- Impact: `gui_game.py` remains the highest-regression surface; it is
  smoke-covered, not unit-covered. `gui_setup.py` is now also large with no
  unit coverage.
- Fix approach: Split along existing test seams (tick loop / placement-
  capture / teardown / debug trace for `gui_game`; save-load / hints /
  widget-build for `gui_setup`). Not urgent — behavior is pinned by required
  smokes 04/05/06/08/10/12/13/14.

**Broad `except Exception` swallows edge-on failure silently:**
- Issue: The Apply path computes the head's edge-on transform inside a
  blanket `except Exception: head_m16 = None` — a malformed `stack_ring` /
  parse slip renders the head as-stored (flat) with **no user-visible or
  debug signal**.
- Files: `serpentrum/gui_setup.py:867-880` (the `try`/`except Exception` at
  :879-880).
- Impact: Same failure class as the 05-16 perpendicular-stack defect that
  was invisible because checks were distance-only.
- Fix approach: Narrow to `molfile.MolFileError`/`ValueError` and emit an
  `SRP_DEBUG`-gated log line or status line on capture.

**Other blanket `except Exception` sites (lower severity, but a pattern):**
- Files:
  - `serpentrum/gui_game.py:1145` — placement error; logs and rejects the
    pickup, then continues (acceptable, but catches everything).
  - `serpentrum/gui_plot.py:501` — PNG save failure; surfaces an error
    string to the status label (acceptable).
  - `serpentrum/pymol_bridge.py:480` — `chain_atom_counts` swallows any
    `cmd.get_model` failure as count `0` **silently**; a vanished chain
    object becomes a desync signal rather than an exception. Documented
    intent, but a wrong count can silently feed the budget-guard cross-check.
- Fix approach: Keep the visible-failure sites; for `pymol_bridge:480`
  consider an `SRP_DEBUG`-gated log on the zero path.

**Dead / unwired code: `hud_logic.idle_tip`:**
- Issue: `idle_tip()` is defined and unit-tested but has **no consumer** in
  `serpentrum/` (grep: definition + tests only).
- Files: `serpentrum/hud_logic.py:297`, pinned by
  `tests/test_hud_content.py:289-299`.
- Impact: Low — carried, non-functional surface. Recorded GATE V disposition
  is UNWIRED, so it is intentionally left in place for now.
- Fix approach: Either wire it into the idle HUD tick or delete it at a
  future cleanup.

**Viewer-side constants mirrored into tests by value:**
- Issue: Integration tests re-declare bridge/engine constants as literals
  (they cannot import `pymol_bridge` — module-level `from pymol import cmd`).
- Files: `tests/test_phase5_integration.py:80` (`DISPLAY_Z = 5.0`),
  `tests/test_phase51_integration.py:43` (`TICK_DT = 0.1`),
  `tests/test_phase52_integration.py:58-62`.
- Impact: Drift risk — changing `pymol_bridge.BOX_DISPLAY_Z` or
  `gui_game.TICK_DT` would not fail these tests, only the smokes.
- Fix approach: Acceptable under the purity ban; rely on required smokes as
  the live-constant assertion.

**Hardcoded canonical counts / literal families duplicated across tooling:**
- Issue: The canonical 46 requirement IDs are hardcoded in
  `tools/audit_requirements.py:37-42` **and** re-hardcoded in
  `tests/test_audit_requirements.py`; pinned control literals are hardcoded
  in `tools/check_docs.py:101-121`; the smoke roster is hardcoded in
  `tests/run_gates.py:57-83`.
- Impact: Adding/removing a requirement or smoke requires editing multiple
  sites; the deliberate duplication is a drift alarm (good), but it is a
  maintenance tax.

---

## Known Bugs

**Selector-Error noise when the spectra overlay zooms before arrows exist (owner-accepted, deferred):**
- Symptoms: In real Windows PyMOL, `zoom_mode_frame()` can fire while
  `srp_mode_vec` is absent, producing benign Selector-Error lines for
  `'srp_mode_vec'` / `'srp_xtbopt or srp_mode_vec'`; the zoom still succeeds
  on `srp_xtbopt`.
- Files: `serpentrum/pymol_bridge.py` (`zoom_mode_frame`), consumer
  `serpentrum/gui_spectra.py` (`_on_table_cell_clicked`).
- Trigger: Clicking a table row on the first record before the CGO arrows
  are loaded.
- Workaround: None needed; owner approved Phase 7 with the noise visible and
  recorded it DEFERRED at GATE V dispositions. Candidate fix: zoom only on
  `srp_xtbopt` when `srp_mode_vec` is absent.

**`smoke/02_dialog_smoke.py` is a known informational FAIL (not required):**
- Symptoms: The headless dialog-construction smoke fails by design/known
  limitation and is deliberately excluded from `REQUIRED_SMOKES`.
- Files: `tests/run_gates.py:57-83` (02 absent from `REQUIRED_SMOKES`),
  `.planning/HANDOFF-2026-09-20-phase5-resume.md` ("smoke 02 informational
  FAIL known"); re-probed dead 2026-09-28 (`tests/test_gui_pins.py:1-14`
  docstring).
- Impact: `PluginDialog` construction (and therefore `SpectraTab` import)
  has **no green automated headless check**. Dialog verdicts stay
  human-verify (STATE decision 01-05: offscreen Qt route is a dead end).

**README claims biphenyl placement refusal as live gameplay (stale after quick-001):**
- Symptoms: `README.md:57` states "its orthogonal rings clash at the set
  geometry and the placement is refused - the designed 'no invented
  chemistry' demonstrator", but since 2026-10-01 quick-001 biphenyl is
  **excluded from all live gameplay pools** (`GAMEPLAY_EXCLUDED_MOLS`), so
  this refusal is now TEST-only and never observed in play.
- Files: `README.md:57`, `serpentrum/spawn.py:146`, `serpentrum/
  setup_logic.py:95-99`, `.planning/quick/001-remove-biphenyl-from-gameplay-
  spawn-pool/PHASE8-NOTE.md`.
- Impact: Player-facing documentation overstates a live behavior; a
  documented corrective text is queued as a GATE V (08-11) wording item.
- Workaround (pending GATE V): replace with "Biphenyl stays in the demo
  manifest (loadable, viewable, CID-cited) but is excluded from live gameplay
  pools since 2026-10-01; it ships as the permanent refuse-path demonstrator
  in the test suite."

---

## Security Considerations

**Subprocess invocation is list-argv, no shell, quote-rejecting:**
- Risk: Command injection via a user-configured xtb path.
- Files: `serpentrum/xtbenv.py` (`validate_binary_path` rejects quote
  characters; `build_argv` returns a list), `serpentrum/xtb_runner.py:206`
  (`proc.start(argv[0], argv[1:])` — QProcess, no shell).
- Current mitigation: Strong — no `shell=True` anywhere in first-party code
  (repo-wide grep = 0 hits).
- Recommendations: None required; keep the quote-rejection contract in sync
  if a future option accepts command-line args.

**Uploaded molecule files are parsed defensively but have no size/atom cap:**
- Risk: A malformed or enormous upload can consume unbounded memory /
  UI-thread time before any gate.
- Files: `serpentrum/molfile.py:117,140` (`splitlines` / `read()`),
  `serpentrum/xyzio.py:129,178` (`read()`), `serpentrum/setloader.py`
  (`read_sdf`, multi-record split). No explicit max byte size / max atom
  guard was found.
- Current mitigation: All parse failures raise typed, line-numbered errors
  (`MolFileError`/`XyzError`).
- Recommendations: Add an explicit size/atom cap with a user-facing message
  before full parse. **[SPECULATIVE impact — no observed incident; absence of
  a cap is confirmed.]**

**`SRP_SPECTRA_DIR` env override + prefix-guarded `rmtree`:**
- Risk: Recursive delete of a user-writable stable spectra dir.
- Files: `serpentrum/xtb_runner.py:59-60` (override resolution),
  `xtb_runner.py:232-250` (`_drop_prior_stable_dir` normalizes and only
  `rmtree`s a dir that starts with the resolved base + `os.sep`), plus
  spray-dir deletes at `xtb_runner.py:332,357`.
- Current mitigation: Prefix guard prevents deleting outside the resolved
  base; spray dir is a `tempfile.mkdtemp` under `xtbenv.new_run_dir`. The
  default base is now `<cwd>/srp_spectra` (06-12 owner amendment), which the
  user can override. Document the override in user docs at release.
- Recommendations: None required.

**`srp_` object-prefix reservation is a deliberate no-undo hazard:**
- Risk: `cleanup_srp` deletes **every** `srp_*` object by name pattern; a
  user who names their own object `srp_*` loses it (PyMOL has no undo,
  PITFALLS F17). Users can also place their own objects and lose them to
  `begin_game`'s hard clean.
- Files: `serpentrum/pymol_bridge.py` (`cleanup_srp`), `AGENTS.md:76`.
- Current mitigation: Documented policy (README + in-game Cleanup text);
  cleanup depends on no plugin state so it works after `.pse` reload
  (INFRA-04).
- Recommendations: Ensure the Phase-8 Help text surfaces the reservation
  prominently.

---

## Performance Bottlenecks

**Gaussian broadening is pure-Python O(n_points × n_modes), on the UI thread:**
- Problem: `broaden()` (default `n_points=800`) evaluates one `math.exp` per
  mode per grid point; the parse + broaden run on the UI thread.
- Files: `serpentrum/spectra.py` (`broaden`),
  `serpentrum/gui_spectra.py` (`_populate_spectrum`).
- Cause: numpy is available in the PyMOL runtime but the pure layer
  (correctly) avoids it.
- Impact: A ~100-atom snake (~300 real modes) ≈ 240k `exp` calls, plus
  re-derivation on option changes. **[SPECULATIVE magnitude — no measured
  jank; the structure and UI-thread placement are confirmed.]**
- Improvement path: Cache the base scene (already done); if a large molecule
  stutters, vectorize against numpy **only in the GUI layer** (pure layer
  stays numpy-free).

**Uncapped xtb threading mitigated by a measured argv cap:**
- Problem: xtb grabs all cores by default, janking PyMOL rendering.
- Files: `serpentrum/xtb_run.py:81` (`DEFAULT_THREAD_ARG = ('-P', '4')`),
  calibration ~84-101 s @ `-P 4` for 104 atoms.
- Current mitigation: Shipped and calibrated (SC5).

**Per-tick viewer coupling is translate-only (good):**
- Files: `serpentrum/pymol_bridge.py` (`move_chain_delta`, one
  `cmd.translate` on a wildcard), train-follow in `game_engine.py`.
- Current mitigation: No per-tick `cmd.get_model` / CGO rebuild for the
  chain; `chain_atom_counts` is completion-only.

---

## Fragile Areas

**WSL↔Windows boundary (the single most common breakage class):**
- Files: `AGENTS.md:4-12`, `tools/winpath.py`, `tests/run_gates.py`
  (`run_smoke`, `gate_xtb`).
- Why fragile: Windows PyMOL cannot resolve `/mnt/c/...`; Windows VMD needs
  `C:/...` while `cmd.exe` targets need `C:\...`. Headless smokes invoked
  through `C:\src\run-conda-pymol.bat` **always exit 0 even after a Qt
  C-abort**, so verdicts must use flushed `SMOKE-OK` sentinels, never exit
  codes.
- Safe modification: Any new smoke must flush a sentinel; `run_gates` asserts
  `'SMOKE-OK' in out and 'SMOKE-FAIL' not in out`.
- Test coverage: sentinel smokes + human-verify only; Windows-only paths
  cannot be unit-tested in WSL.

**Module-identity / reload anchor:**
- Files: `serpentrum/__init__.py` (live state on
  `pmg_tk.startup._serpentrum`), pinned by
  `smoke/01_skeleton_smoke.py` reload + double-import steps.
- Why fragile: A stray module-global for mutable live state would duplicate
  on Plugin-Manager reload or a second import name. The anchor is the single
  defense.
- Safe modification: Never add live-state module globals; extend
  `_SerpentrumState` instead.

**Plugin-path safety (hard rule):**
- Files: `tests/run_gates.py` (`gate_syntax_safety`).
- Why fragile: The dev install points PyMOL's plugin loader at the repo
  root; a stray top-level `*.py` or an `__init__.py` in `tests/`, `smoke/`,
  or `tools/` is autoloaded as a **second plugin** at GUI startup.
- Safe modification: Gate 1 enforces both; never commit either.

**QApplication-missing hard kill for font/renderer access:**
- Files: `AGENTS.md:71`, `smoke/12_plot_smoke.py` stage 0,
  `smoke/14_release_e2e_smoke.py` stage 0.
- Why fragile: Touching `QPainter`/`QFontMetrics`/`drawText` with no
  `Q*Application` **silently hard-kills the process with no traceback**. Any
  new renderer smoke must first do
  `app = QApplication.instance() or QApplication([])`.

**Arrow-key steering via Wizard (never `cmd.set_key`):**
- Files: `serpentrum/input.py` (`KeySteerWizard`, `install`/`teardown`).
- Why fragile: Up/down never fire through `set_key` (C `PyMOL_Special`
  compatibility skip), and left/right would leak a session-global
  `cmd.key_mappings` binding. Teardown depends on the saved wizard being
  carried on the live wizard object.
- Safe modification: Always `install`/`set_active`/`teardown`; never touch
  `key_mappings`.

**xtb cancel/relaunch/double-run lifecycle:**
- Files: `serpentrum/xtb_run.py` (`can_start`, `resolve_status`),
  `serpentrum/xtb_runner.py` (`cancel` = `proc.kill()`; spray dir deleted
  **only** after `finished` — a pre-finished `rmtree` races xtb's open file
  handles on Windows, `WinError 32`).
- Why fragile: Cancel must win over a lingering `'normal termination'` in
  partially-captured stderr; `finished` does not follow a synchronous
  `FailedToStart` (handled in `_on_error`).
- Test coverage: `smoke/11_xtb_runner_smoke.py` (informational) + owner live
  checkpoint.

**PyMOL has no undo + `.pse` desync:**
- Files: `serpentrum/pymol_bridge.py` (cleanup contract), PITFALLS.md F17 /
  8.3, `serpentrum/gui_game.py` (`rebuild_scene` → `cleanup_srp` before
  materialize).
- Why fragile: `.pse` saves viewer objects but **no plugin Python state**;
  cleanup must work in a fresh process from object names only. Restart
  hygiene is load-bearing.

**Setup load trusts the caller to validate:**
- Files: `serpentrum/setup_logic.py:336-361` — `load_setup` only checks JSON
  validity, dict shape, and `schema_version`; it does **not** fully validate
  the payload. The GUI (`serpentrum/gui_setup.py:730+`) calls
  `merge_defaults` → `normalize_loaded` → `validate` before use.
- Why fragile: Any future caller that uses `load_setup` directly without
  `validate` accepts an untrusted dict. The contract is documented but not
  enforced by construction.

---

## Scaling Limits

**Hessian atom budget is warn-and-proceed, and wins routinely exceed it:**
- Current capacity: `atom_budget=100` default.
- Limit: A default win snake (10 stacked + head) runs 130-260 atoms, so the
  budget is exceeded on the **normal win path**; hessian cost scales ~N³.
- Files: `serpentrum/budget_guard.py` (documented structural
  warn-and-proceed, never a block), `serpentrum/game_engine.py` (win freezes
  at cap).
- Scaling path: Warning + revealed counts shipped; actual wall time at cap
  calibrated (~84-101 s @ `-P 4` for 104 atoms). Larger uploads beyond the
  warning are unguarded.

**QProcess fallback is documented but unbuilt:**
- Files: `.planning/ROADMAP.md` ("fallback = worker+queue+QTimer drain
  (documented, unbuilt)").
- Limit: If `QtCore.QProcess` were missing/behaving differently in the
  Windows conda PyMOL, the async pipeline has no built alternative.
- Current mitigation: `smoke/09_qprocess_smoke.py` probes availability
  (informational); shipped pipeline works in owner checkpoints.

---

## Dependencies at Risk

**Python 3.6 (EOL) test interpreter** — see Tech Debt. Files:
`AGENTS.md:8`, `tests/run_gates.py:133`.

**xtb 6.7.1 Windows pre-release:**
- Risk: The repo pins the 6.7.1 **pre-release** because 6.7.0's Windows
  build is missing a DLL; a pre-release is by nature less stable.
- Files: `README.md` (Requirements), `AGENTS.md:12`,
  `tests/run_gates.py` (`XTB_EXE_REL`), `serpentrum/xtbenv.py`
  (`detect_binary`).
- Impact: The entire spectra feature depends on this specific binary.
- Migration plan: Pin and log the detected version.

**No dependency lockfile / requirements file:**
- Risk: Runtime deps are assumed to come from PyMOL (`numpy`, PyQt5 via
  `pymol.Qt`); there is no manifest pinning them.
- Files: absence of `requirements.txt`/`pyproject.toml`/lockfile in repo
  root; policy in `README.md` and `AGENTS.md:19-22`.
- Impact: Low while the dependency set is "whatever PyMOL ships"; any added
  lib must go through user approval + `3rd_party_lib/` (git-ignored).

**No matplotlib/scipy (deliberate):**
- Files: PITFALLS.md; plot is a custom `QWidget.paintEvent`/`QPainter`
  (`serpentrum/gui_plot.py`). No risk beyond the intentional constraint.

---

## Missing Critical Features

**Phase 8 release close (GATE V pending — the live release blocker):**
- Problem: The final owner sign-off has not run. 10 requirements remain
  `Pending`: `SETUP-07`, `SETUP-08`, `DATA-01`, `DATA-02`, `DATA-04`,
  `DOCS-01`, `DOCS-02`, `DOCS-03`, `DOCS-04`, `DOCS-05`.
- Files: `.planning/phases/08-demo-data-docs-release-audit/08-11-SUMMARY.md`
  (`status: checkpoint-presented`), `.planning/REQUIREMENTS.md:20-21,59-79`
  (unchecked) and `:133-172` (Pending rows),
  `python3.6 tools/audit_requirements.py --release` currently exits 1 naming
  exactly those 10 rows.
- Blocks: A shippable v1.0. Everything else (Phases 1-7 + 5.1/5.2/5.3) is
  complete and human-approved.

**DATA_SOURCES.md is DRAFT — NOT APPROVED:**
- Problem: The attribution document of record is DRAFT-headed and carries
  two open `TODO`s; the release gate must flip it to APPROVED together with
  a coupled test marker pin in the **same commit**.
- Files: `serpentrum/data/DATA_SOURCES.md:1` (DRAFT header), `:78` (solution-
  phase geometry TODO), `:166` ([JAN2000] aqueous/solution-phase geometry
  TODO), footer DRAFT at `:183`; coupled pin at
  `tests/test_stacking_dataset.py:201`.
- Impact: Attribution/correctness gate. The `[JAN2000]` scope caveat (metal-
  complex crystalline corpus transferability to free neutral hydrocarbons /
  solution phase) is unverified — crystalline-state framing is the current
  honest position.
- Fix approach: GATE V Section A approval + same-commit `DRAFT`→`APPROVED`
  flip and marker-pin edit.

**Biphenyl Phase-8 reconciliation incomplete:**
- Problem: quick-001 (2026-10-01) excluded biphenyl from live gameplay, but
  Phase-8 docs still present it as a playable/stackable species (see Known
  Bugs README item). Historical 08-* verification records stay as-written.
- Files: `README.md:57`, `.planning/quick/001-*/PHASE8-NOTE.md`.
- Blocks: DOCS-01 claim-accuracy sign-off.

**SETUP-08 proof scope is one-machine two-session only:**
- Problem: The educator Save→Load reproduction requirement is proven on one
  machine across two sessions; multi-machine behavior is a documented
  acceptance note, not tested.
- Files: `.planning/phases/08-*/08-11-SUMMARY.md` (recorded default
  "SETUP-08 proof scope"), `tests/test_setup_logic.py`,
  `smoke/14_release_e2e_smoke.py` STAGE7.
- Blocks: Nothing critical; a reproducibility-confidence gap.

**Upload-only run win condition (resolved as consent-gated):**
- Problem: A set with zero stackable species historically yielded an endless
  run; Phase 5.2 added the generic-π-stack consent (STACK-06) so ring-bearing
  uploads can win. Ring-less upload-only sets remain unwinnable by design
  ("no invented chemistry").
- Files: `serpentrum/generic_stack.py`, `setup_logic.py`,
  `.planning/debug/resolved/05-upload-only-endless-run.md`.
- Blocks: Nothing critical; an acknowledged UX honesty boundary.

**Edge-biased pickup spawn distribution (deferred by owner):**
- Files: `.planning/phases/5.3-randomized-pickup-spawning/5.3-05-SUMMARY.md`.
- Blocks: Difficulty polish only; `MIN_HEAD_DIST_FACTOR = 0.35` ships.

---

## Test Coverage Gaps

Coverage model: pure modules are unit-tested under WSL python3.6 (937 tests
green 2026-10-02); GUI/BRIDGE modules are covered by headless Windows PyMOL
smokes (sentinel verdicts) + human-verify. WSL cannot test anything importing
`pymol`/`Qt`.

**`serpentrum/gui_spectra.py` has no direct test and no direct smoke:**
- What's not tested: The entire SpectraTab — `_populate_spectrum`
  precedence (g98-first / vibspectrum fallback), degenerate resets, table
  population, row-click vector loading, Run-again/Cancel delegation.
- Files: `serpentrum/gui_spectra.py` (517 lines). Repo-wide grep finds
  **zero** references to `gui_spectra`/`SpectraTab` in `tests/` or `smoke/`
  except incidental text pins (`tests/test_help_text.py`,
  `tests/test_spectra_ui.py`, `tools/check_docs.py`, `tools/check_purity.py`).
  It is constructed transitively only by `PluginDialog()`
  (`serpentrum/gui.py`), i.e. by `smoke/02_dialog_smoke.py` — a **known
  informational FAIL not in `REQUIRED_SMOKES`**.
- Risk: The largest shipped untested surface. Pure helpers
  (`plot_logic`/`spectra_ui`) are unit-tested and `gui_plot` is smoked
  (`smoke/12`), but the tab itself is not.
- Priority: High.

**`serpentrum/xtb_runner.py` (Qt shell) is smoke-only, informational:**
- What's not tested: `XtbRunController` signal wiring, connect-before-start,
  cancel/double-run/relaunch, stable-dir keep-until-replaced.
- Files: `serpentrum/xtb_runner.py` (380 lines); covered by
  `smoke/11_xtb_runner_smoke.py` which is **not** in `REQUIRED_SMOKES`
  (`tests/run_gates.py:57-83`; owner instructed no promotion, 06-12).
- Risk: Qt mechanics pinned only by an owner-waived, non-blocking smoke. The
  pure half (`xtb_run.py`) is unit-tested.
- Priority: Medium-High.

**GUI/BRIDGE modules covered by smokes only (Windows-untestable in WSL):**
- Files: `serpentrum/gui.py`, `gui_game.py` (1572), `gui_setup.py` (953),
  `gui_plot.py`, `input.py`, `pymol_bridge.py`, `xtb_runner.py`,
  `gui_spectra.py`. No `test_*.py` imports them (module-level
  `from pymol import cmd` in `pymol_bridge.py`/`input.py`).
- Risk: Applies to ~5,000 lines of viewer/Qt code. Mitigated by required
  smokes 01/03/04/05/06/07/08/10/12/13/14 and human-verify.
- Priority: Medium (accepted tradeoff — keep the pure layers thick).

**Windows-only paths are untestable in the WSL unit layer:**
- What's not tested at unit level: WSL→Windows path conversion
  (`tools/winpath.py` is unit-tested, but the real cmd.exe invocation is
  not), `.bat` exit-code swallowing, QProcess-in-conda behavior, `xtb.exe`
  exec from WSL.
- Files: `tests/run_gates.py` (`run_smoke`, `gate_xtb`);
  `tests/test_winpath.py` (pure conversion only).
- Risk: Boundary regressions surface only in `--smoke`/`--xtb` gate runs or
  live checkpoints.
- Priority: Medium; requires Windows access to close.

**Informational-only smokes (non-blocking):**
- `smoke/02_dialog_smoke.py` (known FAIL), `smoke/09_qprocess_smoke.py`,
  `smoke/11_xtb_runner_smoke.py` are run when present but **never fail the
  gate** (`tests/run_gates.py` informational loop).
- Risk: Dialog construction, QProcess availability, and the xtb runner can
  regress without a red gate. `--xtb` covers the binary invocation but not
  the runner.

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
| `gui.py` | no (source pins) | 01/02 (02 = info FAIL) | 01 |
| `gui_game.py` | no | 04/05/08/10/13 | 04/05/08/10/13 |
| `gui_setup.py` | no (source pins) | 04/08 | 04/08 |
| `gui_plot.py` | no | 12 | 12 |
| `gui_spectra.py` | **no** | **none direct** | **no** |
| `spawn.py` / `setup_logic.py` | yes | 14 (round-trip) | 14 |
| release chain | — | 14 | 14 |

---

*Concerns audit: 2026-10-02*
