# Phase 7: Spectra UI — Consumption Seams & Non-Plot UI - Research

**Researched:** 2026-09-25 (UTC)
**Domain:** Phase-6 contract consumption for the Spectra tab — SPECTRA-01 tab wiring, SPECTRA-04 log panel, SPECTRA-05 frequency table + static mode vectors, module/purity layout, xtbopt.xyz overlay decision
**Half covered:** the non-plot half. The plot widget (SPECTRA-03) is the parallel research file's half; the ONLY shared interface is the pure frequency-label formatter (imaginary `-31.9i` convention) — specified in section Q7 and flagged for cross-plan coordination.
**Confidence:** HIGH for all code-contract claims (verified against live repo code + the frozen 06-*.md plan texts with file:line) and for the g98↔xtbopt coordinate identity (live WSL probe); MEDIUM explicitly flagged.
**Status caveat:** Phase 6 is PLANNED, NOT EXECUTED. `serpentrum/xtb_run.py`, `xtb_runner.py`, `budget_guard.py` do not exist on disk. Every Phase-6 symbol below is extracted from the frozen plan texts (`.planning/phases/06-xtb-pipeline/06-*-PLAN.md`), which are the binding contracts Phase 7 consumes.

---

## Summary

Phase 7's non-plot half is largely a **wiring-and-rendering exercise over already-frozen seams**: the parser (`serpentrum/spectra.py`), the CGO arrow builder (`cgo_build.mode_arrows`), the anchor records (`last_run`, and Phase 6's `spectra_run`), and the runner signal vocabulary (`log_line(str)`, `run_finished(status, problems)`) are all specified and mostly already shipped or plan-frozen. The three real design decisions this research resolves:

1. **SPECTRA-05 overlay decision (RESOLVED by probe):** draw mode vectors on the **optimized frame** — load `record['xtbopt_path']` as a new `srp_xtbopt` object and build arrows at `g98.atoms` coordinates. A WSL probe against the committed fixture proves g98's Standard-orientation atom block is **coordinate-identical** (max per-atom |Δ| = 0.0000 Å; max pairwise-distance diff 1e-6 Å) to `xtbopt.xyz`, so vectors + optimized molecule are exactly self-consistent. Drawing at the game-frame snake (`srp_head`/`srp_seg_*`) would attach optimized-frame displacement directions to coordinates that ancopt moved by up to 0.14 Å (pairwise) — qualitatively wrong for the educational payoff.
2. **SPECTRA-04 log panel:** `QPlainTextEdit` read-only with `setMaximumBlockCount(500)`, fed by the controller's `log_line(str)` signal via a plain connect (all Qt work happens on the main thread — no queued connection needed). One gap: Phase 6 freezes the controller's 500-line tail as the **private** `_log_lines`; a late-connecting tab needs a public tail accessor that Phase 7 must add to `xtb_runner.py` (the plan text never defines one).
3. **SPECTRA-01:** the tab switch (model-A, `setCurrentIndex(2)`) and the Get-Spectra button lifecycle are **already shipped** (05-15); Phase 6 (06-09) will interpose the launch pipeline keeping the switch first. Phase 7's entire SPECTRA-01 scope is: **replace the placeholder page content with a live SpectraTab** — and nothing else. The launch actor is GameTab's button → the dialog's pipeline, NEVER the Spectra tab itself.

**Primary recommendation:** build `serpentrum/gui_spectra.py` (GUI class, SpectraTab mirroring the GameTab construction pattern) + `serpentrum/spectra_ui.py` (new PURE module, auto-classified, TDD'd in WSL) containing `freq_label`, `table_rows`, `mode_arrow_primitives`, and status-line builders; add ONE bridge function `load_mode_arrows` + reuse existing `load_molecule`/`delete_object`; mirror-and-upgrade the 06-09 placeholder wiring inside the tab.

---

## Q1 — Pure parser reality (serpentrum/spectra.py, verified)

**Consumption entry points (all shipped):**

| Function | Location | Contract |
|---|---|---|
| `parse(path)` | spectra.py:500-505 | utf-8 open + `parse_text`; format sniffed from CONTENT, never the filename |
| `parse_text(text)` | spectra.py:478-497 | first non-blank line `$vibrational spectrum` → vibspectrum; `'Standard orientation:'` in text → g98; else `SpectraParseError('unrecognized format')` |
| `parse_g98(path)` | spectra.py:298-301 | explicit g98 entry |
| `parse_vibspectrum(path)` | spectra.py:396-399 | explicit vibspectrum entry |
| `real_modes(spectrum, threshold=10.0)` | spectra.py:402-418 | `[m for m in spectrum.modes if abs(m.freq) >= threshold]` — never sign-based, never count-based |
| `broaden(modes, fwhm=16.0, x_min=0.0, x_max=None, n_points=800)` | spectra.py:433-475 | (grid, ys); empty modes → zero curve (pinned); `fwhm <= 0` / `n_points < 2` → ValueError |

**Record shapes (spectra.py:29-38):**
- `Mode = namedtuple('Mode', 'index freq intensity vectors')` — `index` 1-based running across blocks; `freq` float cm⁻¹ (negatives KEPT as negatives); `intensity` float km/mol; `vectors` = list of `(x,y,z)` float tuples, `len(vectors) == n_atoms`.
- `Spectrum = namedtuple('Spectrum', 'n_atoms atoms modes')`; `Atom = namedtuple('Atom', 'atomic_number x y z')`.

**g98 vs vibspectrum (spectra.py:313-321):** vibspectrum carries freq+intensity for ALL 3N modes (trivial included) but `atoms == []` and every `Mode.vectors == ()` — **no vectors, ever**. g98 carries the Standard-orientation atom block + per-atom displacement vectors for the 3N−6 projected modes only. The table's row-click → vectors therefore requires the g98 parse; a vibspectrum-only run must render the table but refuse vector drawing.

**Index-correspondence guarantee (plan 02-12, pinned):** `tests/test_spectra_robustness.py:114-150` — offset = `3*n_atoms − len(g98_modes)` (= 6 for the dimer fixture, computed from the files, NEVER hardcoded); 72/72 modes match within freq 0.01 / intensity 1e-4 (the exact boundary case is mode 53: g98 0.0233 vs vibspectrum 0.02325 at 1e-4 tolerance). g98 mode k ≡ vibspectrum mode k+offset. This is the anchor that lets the table (g98-sourced) and any vibspectrum-sourced display never desync by index.

**Corrupt input:** `SpectraParseError` (ValueError subclass, spectra.py:41-45) carrying stage + 1-based line + ~80-char excerpt; a botched numeric token NEVER surfaces as a bare ValueError (`_to_float`/`_to_int` wrap, :74-91).

**Fixture inventory** (`tests/fixtures/xtb/`, committed, read-in-place per house convention `tests/test_xtbenv.py:1-34`):
- `g98.out` — 26-atom phenol π-dimer, 72 modes in 24 3-column blocks (883 lines)
- `vibspectrum` — same run, 78 modes (6 trivial + 72 real), 82 lines
- `xtbopt.xyz` — same run, 26 atoms, comment = energy/gnorm line
- `dimer2.xyz` (+err/log) — the run INPUT
- `co2.xyz` (+err/log), `phenol.xyz`, `ohess.log`, `bad.log`/`bad.err`/`bad.xyz`, `repro_oh.err/log`, `synthetic/README.md` + `co2_vibspectrum`
- `.planning/research/xtb-spike-fixtures/` holds the superset (adds `hessian`, `xtbhess.xyz`, `xtbrestart`, `charges`, `wbo`, `xtbtopo.mol`, `xtbopt.log`, `co2.xyz`, `dimer.xyz`, `dimer2.*`).
- **GAP (risk 1):** NO co2 `g98.out` fixture exists anywhere — the linear-molecule 5-trivial-mode leg (Pitfall 12.1) cannot be unit-tested end-to-end for vectors today.

**Can a Phase-7 pure test build table data today? YES (probe 2026-09-25, WSL python3.6):**
```
g98 atoms: 26 modes: 72
negative g98 modes: [(1, -31.9175), (2, -23.0766), (3, -18.1086)]
zero-intensity g98 modes: 0
all len(m.vectors) == 26: True
vibspectrum modes: 78 (real after real_modes(): 72)
vibspectrum zero-intensity rows: 6 [1..6]  (the trivial rows)
```
The dimer table = 72 rows (3 negative). Zero-intensity REAL modes exist in xtb generally (CO₂ symmetric stretch, intensity 0.00000, PITFALLS.md:297-299) but not in this fixture's g98 — the table builder must be unit-tested for zero-intensity via synthetic Mode tuples, not the fixture.

---

## Q2 — Frozen Phase-6 contract table (symbol → source plan → shape)

| Symbol | Source | Shape / contract |
|---|---|---|
| `xtb_run.SPECTRA_RUN_KEYS` | 06-02:64,98 | `('snake_id','status','problems','input_path','g98_path','vibspectrum_path','xtbopt_path','log_path')` — **Phase 7 parses from these paths WITHOUT reshaping** (06-02:31-33) |
| `xtb_run.new_spectra_run(snake_id)` | 06-02:99 | `{'snake_id': id, 'status': 'running', 'problems': [], 'input_path': None, 'g98_path': None, 'vibspectrum_path': None, 'xtbopt_path': None, 'log_path': None}` (exact dict) |
| status values | 06-02:64-65 | `'idle'` (or None record) / `'running'` / `'ok'` / `'failed'` / `'cancelled'` — status strings double as state-machine states; `TERMINAL_STATES = frozenset({'ok','failed','cancelled'})` |
| `xtb_run.can_start / resolve_status` | 06-02:114-116 | guard: start only from None/idle/terminal; cancel WINS over verdict |
| `xtb_run.build_run_input(head_atoms, segment_atom_lists, snake_id)` | 06-02:120 | head-first + segments in engine order → `xyzio.write_xyz` text, comment `'serpentrum snake <id>'`; `head_atoms None → ValueError` |
| `xtb_run.KNOWN_ENV_KNOBS / DEFAULT_RUN_KNOBS` | 06-02:117-119; 06-11:79-81 | knobs = `('OMP_NUM_THREADS','MKL_NUM_THREADS','OMP_STACKSIZE')` only; default currently `{}`, **06-11 may change it from 06-CALIBRATION.md** — read live, never pin |
| `XtbRunController` (xtb_runner) | 06-05:100-117 | QObject; signals **started = Signal(); log_line = Signal(str); run_finished = Signal(str, list)**; `start(xyz_text, exe_path, base_dir, snake_id, knobs=None, extra_args=None) -> bool`; `cancel()`; `status()` accessor; `_log_lines` **private** bounded tail (500) — no public accessor frozen (gap, below) |
| `_serpentrum.spectra_run` | 06-05:28-29, Task 1 | written ONLY by the runner's terminal branch (or `_fail_before_start`); Phase 7 consumes paths |
| `_serpentrum.spectra_runner` | 06-05:67; 06-09:62,98 | controller create-or-reuse by the DIALOG at first launch; connect signals ONCE per dialog via a **dialog-scoped** flag (reload reconnects) |
| stable artifact dir | 06-05:65,115(c) | `%TEMP%/srp_spectra/<snake_id>/` holding `snake.xyz`, `g98.out`, `vibspectrum`, `xtbopt.xyz`, `xtb.log`; keep-until-replaced (next start deletes the old dir, prefix-guarded) |
| `last_run['snake_xyz']` | 06-06:13-14, Task 1 | head-inclusive engine-atom xyz text assembled at completion (single write, never a PyMOL re-read); None when the head mirror was unavailable → launch refuses with a clear line |
| `GameTab.log_external(msg)` | 06-06:15, Task 1.3 | public wrapper of `_log` for launch-time lines |
| Launch pipeline `_on_spectra_requested` → `_launch_spectra_run(record, exe)` | 06-09:Tasks 1-2 | `setCurrentIndex(2)` FIRST; refuse lines; counts via `xyzio.read_xyz_text` + `pymol_bridge.chain_atom_counts`; `budget_guard.launch_counts_line`/`launch_budget_warnings` verbatim; `xtbenv.detect_binary`; disarm Get Spectra; create/reuse controller; re-enable Get Spectra on `run_finished` |
| Placeholder affordances Phase 7 replaces | 06-09:58, Task 1 | `self.spectra_status` (QLabel wordwrap), `self.spectra_log` (QTextBrowser read-only, ~200 lines), `self.spectra_run_btn` ('Cancel xtb run' running / 'Run again' terminal) — **"Phase 7 replaces the page CONTENT, the signal contract survives"** (06-09 must_have 3) |
| Slots to preserve or re-implement | 06-09:80 | `_on_runner_started` → status 'xtb running... (async - the dialog stays responsive)'; `_on_runner_log_line` → append; `_on_run_finished(status, problems)` → `'xtb finished: %s' + '; '.join(problems)`, **re-enable game_tab.get_spectra_btn (getattr-guarded)**, flip button to 'Run again' |
| `budget_guard` | 06-01:108-114 | `launch_budget_warnings(mol_stacked, mol_view, at_engine, at_view, atom_budget)` — never blocks/raises; `launch_counts_line(mol_stacked, at_engine, budget)` = `'spectra input: %d molecules (incl. head), %s atoms (budget %s)'` |
| `setup_logic.HESSIAN_WARNING` | 06-11:62; setup_logic.py:118-119 | `'hessian cost scales ~N^3; a ~100-atom snake may take 30-90 s'` — **literal re-pinned from 06-CALIBRATION.md by plan 06-11**; Phase 7 reads `setup_logic.HESSIAN_WARNING` at runtime, never re-pins |
| Event vocabulary (SPECTRA-04) | 06-RESEARCH-guard:98 | frozen as "lines + done-with-verdict" — delivered as `log_line(str)` + `run_finished(status, problems)` |

### Ambiguities the planner MUST know

1. **No public log-tail accessor (gap).** 06-05 freezes `self._log_lines` as a private bounded tail (06-05:69,102) but no getter. A Spectra tab that connects AFTER a launch (dialog reopened / tab first constructed at launch) must not lose early lines — Phase 7 should add a tiny public `log_tail()` accessor to `serpentrum/xtb_runner.py` (a GUI module, no purity issue) OR read lines only going forward plus replay `record['log_path']` at terminal. Recommend the accessor (one task-level edit); flag in the plan.
2. **`_serpentrum.spectra_runner` is never a DECLARED anchor field.** `__init__.py`'s `_SerpentrumState` declares `dialog/controller/setup/game_session/records/stacking_data/last_run` (serpentrum/__init__.py:22-43); 06-05 Task 1 adds only `spectra_run`. `spectra_runner` is `setattr`'d by the dialog at first launch (06-05:67). Phase 7 should add the declared field + docstring (single-writer: Phase 7 owns `__init__.py` after 06-05).
3. **Placeholder widget ownership.** 06-09 attaches the placeholder widgets and all runner-signal slots to the **dialog** (`self.spectra_status` etc., `self._connect_runner`). Phase 7 replacing the page must either keep that wiring in `gui.py` and forward into the tab, or (recommended) move the slots into `gui_spectra.py` and have PluginDialog delegate. Either way the behaviors pinned by 06-09 (Get-Spectra re-enable on terminal, contextual Cancel/Run-again, status text) MUST survive or be explicitly re-implemented.
4. **Run-again re-enters the full pipeline via the dialog.** 06-09 Task 1 (`_on_spectra_run_button`): running → `controller.cancel()`; terminal → re-enter the FULL launch pipeline (re-read last_run, re-emit counts, re-run guard, re-resolve binary, disarm) — NEVER `_launch_spectra_run(record, exe)` with stale values. The launch routine lives in `gui.py`; a Spectra tab button needs a governed path to it (tab → dialog method call; the tab is constructed with `anchor_state` + parent per house pattern).
5. **06-11 outcomes are data-dependent** (06-CALIBRATION.md doesn't exist yet): `DEFAULT_RUN_KNOBS`, possibly a controller `-P N` default (`DEFAULT_THREAD_ARG` + 2-line controller touch), and the `HESSIAN_WARNING` wording. Phase 7 plans must treat these as runtime-read constants, and must not assume `{}`.
6. **No queued-connection need.** Qt 5.12.9 via pymol.Qt; QProcess signals `started/finished/readyReadStandard{Output,Error}` all land on the Qt main thread (06-RESEARCH-runner.md:77) — controller and tab live in the same thread; plain `.connect()` (new-style ONLY, 06-05:60); `cmd.*` in slots is legal.

---

## Q3 — SPECTRA-04 log panel (recommendation)

- **Widget:** `QPlainTextEdit`, `setReadOnly(True)`, `setMaximumBlockCount(500)` — bounded capacity matching the controller's 500-line tail so memory stays flat during streaming. The 06-09 placeholder uses `QTextBrowser` (bounded ~200 lines); "Phase 7 replaces the page CONTENT" explicitly permits the swap. MEDIUM confidence on the performance rationale (QPlainTextEdit's max-block-count is the standard Qt streaming-log mechanism; QTextBrowser would suffice too at this volume — hundreds of lines, not megabytes).
- **Feed:** `controller.log_line.connect(tab.append_log_line)` (plain connect — same thread; never `SIGNAL()` strings, house rule). **Launch actor:** GameTab's Get Spectra → `PluginDialog._on_spectra_requested` (06-09). The Spectra tab NEVER launches; it offers only Cancel/`Run again` (06-09 Task 1 semantics).
- **Early-line buffering:** the tab is constructed with the dialog (all pages at init, gui.py:62-71 — before any run exists), so in the first-launch flow it is connected BEFORE `start()` returns and loses nothing. The loss window is RELOAD (new dialog reuses the anchored live controller) — cover it by replaying `controller.log_tail()` (the Q2-gap accessor) on connect, then connecting `log_line`.
- **Terminal rendering:** `_on_run_finished(status, problems)` → status label uses a pure builder over the frozen status vocabulary ('ok'/'failed'/'cancelled'); problems joined `'; '`. Never re-grep the drained log for 'normal termination' (the substring trap — `'abnormal termination'` contains it; `xtbenv.evaluate_run` owns verdicts, 06-RESEARCH-guard pitfall 8).
- **Modeless discipline:** no `.exec_()` anywhere (AST gate, tools/check_purity.py:192-196); no modal dialogs from the tab mid-run (Pitfall 5). Save-dialog (plot half) is the parallel researcher's concern.

---

## Q4 — SPECTRA-05 table + mode vectors

**a) Table widget:** `QTableWidget` (ARCHITECTURE.md:97 names it) — 3 columns: mode #, frequency label (imaginary convention), IR intensity. Read-only items; row click via `cellClicked(int row, int column)`. Populate from the **parsed g98 Spectrum in mode order** — `spectrum.modes[r]` ⇔ table row r. `real_modes()` need NOT be applied to g98 data (it is a documented no-op there — g98 projects trivial modes out, spectra.py:415-416). vibspectrum-fallback: populate from `real_modes(parse(path))`, show a status note, and refuse vector drawing on row click (no vectors exist). Fixture counts (probe): 72 rows for the dimer; 3 negative (rows 1-3: −31.92, −23.08, −18.11); zero-intensity rows absent from this g98 but REQUIRED to be listed when present (SPECTRA-05).

**b) Atom-order + geometry frames (RESOLVED — the overlay decision):**

Verified today (WSL probe, 2026-09-25, fixture test vs `tests/fixtures/xtb/`):
```
raw per-atom |g98_standard_orientation − xtbopt.xyz|:  min/max/mean = 0.0000 Å
max pairwise-distance diff (rotation-free):  1e-6 Å
xtbopt.xyz vs INPUT dimer2.xyz (centroid-aligned):   max 0.0712 Å, mean 0.0273 Å
max pairwise-distance diff |xtbopt vs input|:        0.1423 Å
symbol order g98 vs xtbopt:  0 mismatches
```
→ **Decision (recommend option i): load `record['xtbopt_path']` into the viewer as `srp_xtbopt` and draw arrows at `spectrum.atoms` (g98) coordinates.** Vectors + molecular frame are coordinate-identical — self-consistent by measurement. Option (ii) — arrows on `srp_head`/`srp_seg_*` — mismatches by up to 0.14 Å in internal geometry (ancopt moved every atom) AND breaks entirely when the game snake was cleaned/replayed; reject it. The g98 vectors are per-atom of the xtb-run structure whose atom order = the run input order = `build_run_input`'s head-first + segments order (06-02:120) — no reordering seam is needed anywhere.

**Object naming (given `srp_` reservation):** mode-vector CGO object and the optimized molecule MUST use `srp_*` names (`srp_mode_vec`, `srp_xtbopt`): `cleanup_srp` wildcard-deletes `srp_*` (pymol_bridge.py:129-143) and a non-`srp_` object would both survive "Cleanup model" AND become an indistinguishable orphan after a `.pse` reload (bridge docstring :21-36 — the prefix IS the fresh-process contract). Semantics:
- New table click → `delete_object('srp_mode_vec')` → build → `load_cgo` (replace, never accumulate).
- `srp_xtbopt` loads once per parse (if already present for the same record, guard `object_exists` and skip; replace when the record's snake_id changes — planner pins the guard).
- New game Apply/Start → `materialize`'s `cleanup_srp` removes both (correct); a mid-flow Restart does NOT remove them (teardown deletes pickups only, gui_game.py:_teardown_round) — acceptable; flag as an intentional keep-until-cleanup.

**c) Bridge seams (minimal, two additions to existing pymol_bridge.py — already BRIDGE):**
- **xtbopt load: REUSE `pymol_bridge.load_molecule(path, srp_name, zoom=0)` (pymol_bridge.py:78-88)** plus a one-line `cmd.show('sticks', name)` — recommend a 4-line wrapper `load_xtbopt(path)` mirroring `materialize_pickup` (:361-375).
- **CGO load: ONE new function** mirroring `load_box` (:91-109):
  `def load_mode_arrows(cgo, name='srp_mode_vec', zoom=0): cmd.load_cgo(list(cgo), name, zoom=0); return name`
  (`delete_object` already exists, :419-428.)
- **REQUIRED smoke pattern:** a new `smoke/12+_*` entry in the numbered series (Phase 6 claims 09-11; tests/run_gates.py:55-61 `REQUIRED_SMOKES` — adding a required smoke means editing that tuple in the plan that adds it; an informational smoke needs no tuple edit). Verdict = flushed SMOKE-OK sentinels in stdout, NEVER exit codes (repo AGENTS.md). Contents: parse fixture g98 from disk (no xtb needed), build arrows via `cgo_build.mode_arrows`, `load_cgo`, assert object exists + `get_extent` sane, print sentinels. A second leg loads the fixture `xtbopt.xyz` and asserts 26 atoms + coordinate agreement with the g98 atom block (<1e-3 Å), which re-verifies the overlay assumption on every gate run — protects against xtb-version drift in the 6.7.1pre-derived assumption.

**d) Index safety:** single-source parse for table+vectors from `record['g98_path']`; fallback `parse(record['vibspectrum_path'])` when g98 absent; NEVER re-merge g98 vectors with vibspectrum rows by hand (Pitfall 12.5 check; 06-RESEARCH-guard pitfall 11). Table row → `spectrum.modes[row]`; `Mode.index` is display-only. Never hardcode trivial counts anywhere (co2 5 vs nonlinear 6 — Pitfall 12.1). The 02-12 correspondence proof (test_spectra_robustness.py:114-150) pins g98 mode k == vibspectrum mode k+6, so the table and any plot-side vibspectrum sourcing cannot disagree about which physical mode a frequency is.

---

## Q5 — SPECTRA-01 wiring (what remains)

- **Shipped (05-15):** Get-Spectra button lifecycle (disabled at construction + every `_teardown_round`, enabled ONLY in `_present_completion` — gui_game.py:312-349,1333,1388); `GameTab.spectra_requested` (class-level, emit-only) → `PluginDialog._on_spectra_requested` → `tabs.setCurrentIndex(2)` (gui.py:77,96-105).
- **Phase 6 ships (06-09):** launch pipeline interposed into `_on_spectra_requested`, keeping the tab switch FIRST.
- **Phase 7's entire SPECTRA-01 scope:** replace the `_TAB_DEFS` placeholder-loop construction of page 2 (gui.py:19-23,62-71) with a live `SpectraTab` page. Nothing else — no signal changes (model-A locked decision 9), no button lifecycle changes (GAME-09), no launch-actor changes. Note gui.py is modified by 06-09; Phase-7 plans list gui.py in ONE plan only (single-writer).

---

## Q6 — Module layout + purity (recommendation)

| File | Class | Content | Purity edit |
|---|---|---|---|
| `serpentrum/gui_spectra.py` (NEW) | GUI | `SpectraTab(QtWidgets.QWidget)`: status label, log panel, run/cancel button, freq `QTableWidget`; pymol.Qt only; relative imports of pure modules + pymol_bridge are exempt (tools/check_purity.py:95-98; the 06-09 "imports from GUI are legal" precedent) | `tools/check_purity.py` `GUI_MODULES` += `'serpentrum/gui_spectra.py'` with the 06-05-style comment; **inert-first edit lands gates-green before the file exists** (entries for not-yet-created files are inert, check_purity.py:56-61) |
| `serpentrum/spectra_ui.py` (NEW, recommended name) | PURE — auto-covered, NO edit | `freq_label`, `table_rows`, `mode_arrow_primitives`, status-line builders (Q7 below). Keep out of `hud_logic.py` (game-HUD scope; the family is spectra-specific >2 builders, the focused-module house rule at 06-RESEARCH-guard open question 4) | none |
| `serpentrum/pymol_bridge.py` (EDIT) | BRIDGE (already) | `load_mode_arrows` + `load_xtbopt` wrapper (Q4c) | none |
| `serpentrum/__init__.py` (EDIT) | ENTRY | declare `spectra_runner = None` (+ maybe `spectra_page = None` not needed — dialog owns the widget) | none |
| `serpentrum/gui.py` (EDIT, 1 plan only) | GUI (already) | page 2 = `SpectraTab(anchor_state, self.tabs)`; keep `_on_spectra_requested` launch pipeline; delegate runner-signal wiring to the tab as decided in Q2-ambiguity 3 | none |
| `plot_widget.py` | GUI (other half) | needs ITS OWN GUI entry — shared-file rule on `tools/check_purity.py` across the phase's two halves: decide in the wave whether one plan owns both allowlist edits or they serialize | cross-half flag |

- **Modeless rule:** `.show()` only at the dialog; the tab constructs widgets, never `.exec_()` (AST gate fails any `.exec_()` outside an allowlist — no allowlist exists).
- **Anchor attrs the page consumes:** `last_run` (+`'snake_xyz'`), `spectra_run` (record), `spectra_runner` (controller, getattr-guarded), `setup` (for `broadening_fwhm` — other half — and hessian wording).
- **StdPy style gate:** python3.6 parseable, %-formatting, no f-strings (06-05:70).

---

## Q7 — Pure half proposal (TDD'd in WSL, zero stubs)

```
# serpentrum/spectra_ui.py  (PURE, stdlib-only)

def freq_label(freq):
    """Imaginary convention: freq < 0 -> '-' + '%.1f' % abs(freq) + 'i'
    (e.g. freq_label(-31.9175) == '-31.9i'); freq >= 0 -> '%.1f'.
    ASCII minus (house UI strings are ASCII — hud_logic patterns; the
    docs' Unicode '−31.9i' is a REQUIREMENTS display convention, pinned
    here as ASCII and the docs note it). SHARED with the plot half —
    the plot's axis/tick labels reuse this formatter."""

def table_rows(spectrum):
    """[(index:int, freq_label:str, intensity_label:str), ...] for EVERY
    spectrum.modes element in order — all modes incl. negatives and
    zero-intensity. intensity_label: '%.4g' is recommended (values go as
    small as 0.00026 in the vibspectrum fixture — '%.2f' would render 0.00,
    hiding SPECTRA-05's zero-intensity distinction)."""

def mode_arrow_primitives(spectrum, mode_index):
    """-> (atoms_xyz, vectors) for spectrum.modes[mode_index-1]... or None
    when vectors are unavailable (vibspectrum parse: every vectors == (),
    or n_atoms == 0). The GUI passes these to cgo_build.mode_arrows
    (atoms, vecs, scale) — the builder is FROZEN (cgo_build.py:134-208):
    directions unit-normalized, ALL arrows uniform length (scale*1.2 A
    default; 0.7 shaft / 0.3 cone). scale is the only knob; v1 ships
    scale=1.0 (SPECTRA-05 static vectors, minimal adjustments) unless the
    planner pins a control."""

def run_status_lines(record):
    """Status-label + log-entry lines derived SOLELY from the frozen
    record vocabulary ('ok'/'failed'/'cancelled', problems). Never
    re-scans log text (substring trap)."""
```
Testing seams already exist: fixture-in-place convention; DI-fake precedent (`xtbenv.detect_binary(which_fn=...)`); `tests/fixtures/xtb/synthetic/` precedent for synthetic fixtures.

---

## Q8 — Risks & pitfalls (planner's verification checklist)

1. **No co2 g98 fixture** — the linear 5-trivial-mode end-to-end table/vector leg can't be unit-tested from fixtures today. Mitigations: synthetic g98 fixture (the `synthetic/co2_vibspectrum` precedent) pinned by a plan, or accept g98-linear leg as smoke-only with a real xtb run (06 gates already run real xtb via `--xtb`).
2. **Overlay assumption = one fixture.** g98≡xtbopt coordinate identity is probed on the dimer (xtb 6.7.1pre). The REQUIRED smoke leg (Q4c) re-asserts `<1e-3 Å` agreement on every gate; on mismatch the plan must fall back (CGO-only arrows at g98 coords, molecule not loaded, warning line) — never silently misalign.
3. **_log_lines private → lost early lines after reload.** Phase 7 adds `log_tail()` to xtb_runner (gap Q2.1) OR accepts terminal-only replay from `record['log_path']`. Decision needed at plan time.
4. **Placeholder-wiring regressions.** Replacing the 06-09 placeholder must preserve: Get-Spectra re-enable on `run_finished` (getattr-guarded), contextual Cancel/'Run again' (full-pipeline re-entry), status/status-log destination of launch lines, `game_tab.log_external` feed. These are pinned behaviors in 06-09 must_haves — list them as must-keep truths in the Phase-7 plan.
5. **Pitfall 2 (main-thread freeze):** the g98 parse + table fill runs on the UI thread — fine (787-line fixture parses in ms; 100-atom snake ≈ 3N−6 ≈ 294 modes, still trivial). NEVER do the xtb run itself on the UI thread (06 owns that).
6. **Pitfall 5 (modals):** this half needs no modals; the plot half's Save-PNG file dialog must apply the pause/refresh discipline — coordinate with the parallel research.
7. **Uniform-length arrows.** `cgo_build.mode_arrows` normalizes direction and draws every nonzero vector at `scale*length_a` (1.2 Å default) — relative per-atom magnitudes are NOT rendered (frozen Phase-2 contract, cgo_build.py:156-162). If the human reviewer wants magnitude-proportional arrows, that is a pinned-constant change in cgo_build + its tests — flag as a plan-time scope decision, do not hand-roll a second builder.
8. **Arrow visibility vs zoom:** `load_cgo(..., zoom=0)` keeps framing untouched; the completion zoom targeted `srp_head or srp_seg_*` (zoom_chain) so `srp_xtbopt`/`srp_mode_vec` won't reframe, but the freshly loaded optimized molecule may sit slightly outside the game-frame zoom — recommend one `cmd.zoom('srp_xtbopt or srp_mode_vec')` bridge one-shot on first vector draw (planner pins wording; ONE call per record, never per click — pitfall 14).
9. **srp_ wildcard collisions:** user must not name objects `srp_*` (INFRA-04 policy); `srp_mode_vec`/`srp_xtbopt` get swept by Setup-Apply `materialize()` cleanup — STATUS line should tolerate their disappearance (all deletes via guarded `delete_object`).
10. **Empty/degenerate records:** failed/cancelled runs have `g98_path=None` → table stays empty and the status carries `problems` — never fabricate rows (Phase-6 SC3 "never fake success"); missing file on disk (temp wiped) → `spectra.parse` raises, catch and surface as a clear line.
11. **Reload semantics:** new dialog reuses anchored live controller; Qt connections of the dead dialog died with it → per-DIALOG `_runner_connected` flag, reconnect fresh (06-09:62 pins this pattern).
12. **Unicode in UI strings:** docs display `−31.9i` (U+2212); pin the formatter to ASCII `-31.9i` in code (hud strings are ASCII) and let docs keep the typographic minus — decide once, note in the plan.
13. **`check_purity` shared-file risk:** the two research halves both need GUI allowlist entries (gui_spectra.py / plot_widget.py). One plan owns the edit or the two serialize on tools/check_purity.py.
14. **python3.6 gateway:** %-formatting only; `namedtuple` records already frozen; no external libs (INFRA-02).

---

## Sources

### Primary (HIGH confidence — live code / live probes, 2026-09-25)
- `serpentrum/spectra.py:29-38,298-301,313-321,396-399,402-418,433-475,478-505` — parser + broadener contracts
- `serpentrum/cgo_build.py:134-208` — frozen `mode_arrows(atoms, vecs, scale, color, base_radius, length_a)` CYLINDER+CONE builder (uniform-length, unit-normalized)
- `serpentrum/pymol_bridge.py:78-88,91-109,129-143,348-358,361-375,419-428,443-455` — load_molecule / load_box / cleanup_srp / zoom_chain / materialize_pickup / delete_object / chain_object_names
- `serpentrum/gui.py:19-23,62-71,96-105` — placeholder page + model-A switch
- `serpentrum/gui_game.py:312-349,1289-1333,1388,1392-1425` — button lifecycle, `_present_completion`, `_log`/`_log_reason` precedent
- `serpentrum/__init__.py:22-48` — anchor declarations
- `tools/check_purity.py:56-63,84-92,95-98,192-196` — allowlists, classify, relative-import exemption, `.exec_` ban
- `tests/run_gates.py:55-61` — REQUIRED_SMOKES tuple (next free number 12 after Phase 6's 09-11)
- `tests/test_spectra_robustness.py:114-150` — g98↔vibspectrum index-correspondence pins
- WSL probes (this research): g98-vs-xtbopt coordinate identity; dimer table counts (72 modes, 3 negative, 0 zero-intensity, 6 trivial in vibspectrum); fixture inventory listing

### Frozen plan contracts (HIGH — binding Phase-6 texts)
- `.planning/phases/06-xtb-pipeline/06-02-PLAN.md` (SPECTRA_RUN_KEYS, status vocabulary, build_run_input, knobs)
- `06-05-PLAN.md` (XtbRunController shell, signals, anchor ownership, terminal branch, tail-500)
- `06-06-PLAN.md` (snake_xyz, log_external)
- `06-09-PLAN.md` (launch pipeline, placeholder affordances, wiring slots, run-again semantics)
- `06-11-PLAN.md` (calibration-derived HESSIAN_WARNING + thread default — data-dependent)
- `06-RESEARCH-guard.md:80-103` (Q5 handoff freeze: artifact set, event vocabulary 'lines + done-with-verdict', 'Phase 7 replaces only page content')

### Secondary (HIGH for shipped-phase contracts)
- `.planning/phases/05-stacking-game-rules/05-15-SUMMARY.md:59-61,105` (last_run keys, model-A, 'Phase 7 replaces ONLY the placeholder page content')
- `05-RESEARCH-gui-lifecycle.md` spectra_handoff ('don't delete the chained snake on Get-Spectra; Phase 7 draws vectors onto it' — superseded in detail by the probe-verified optimized-frame decision above)
- `.planning/research/ARCHITECTURE.md:97,102,268-274` (gui_spectra/spectra module table; flow step 8: QTableWidget ← modes; step 271: `cgo_build.mode_arrows(atoms, vecs, scale)`)
- `.planning/research/PITFALLS.md` pitfalls 2 (main-thread freeze), 5 (modals), 12 (trivial counts 5-vs-6, negatives real, zero-intensity, g98 vector source, degeneracy) — `:48-75,124-140,285-318`
- `.planning/ROADMAP.md` Phase 7 note (table↔vector index match / pitfall 2,12,5) + Phase 6 note (EQ-checkpoint-1: UI verdicts defer to Phase 7)

### [TRAIN] / needs-validation items
- QPlainTextEdit-vs-QTextBrowser performance claim (MEDIUM — standard Qt practice; either works at this volume)
- g98-vs-xtbopt identity beyond the single probed fixture (mitigated by the planned always-on smoke assertion — Q4c/Q8-2)
- 'srp_xtbopt or srp_mode_vec' zoom behavior (viewer-dependent; verify in the smoke/human checkpoint)

## Metadata

**Confidence breakdown:**
- Parser/CGO/bridge contracts: HIGH (shipped, tested, probed)
- Phase-6 contract extraction: HIGH (frozen plan texts; NOTHING assumed from un-written code)
- Overlay decision: HIGH for the measurement, MEDIUM for generality (one fixture) — smoke assertion closes it
- Log-panel widget choice: MEDIUM (two legal widgets; recommendation made)
- Module layout: HIGH (house precedents: 04-05 gui_game, 06-05 xtb_runner entries)

**Research date:** 2026-09-25. **Valid until:** frozen-contract edits (any change to a 06-*-PLAN.md) or 60 days.
