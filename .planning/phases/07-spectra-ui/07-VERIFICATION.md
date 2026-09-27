---
phase: 07-spectra-ui
verified: 2026-09-27T23:30:00Z
status: passed
score: 38/38 must-have truths verified (10/10 plans); 3/3 ROADMAP success criteria
re_verification: none (initial verification)
---

# Phase 7: Spectra UI — Verification Report

**Phase Goal:** "The payoff screen: a broadened IR spectrum of the player's own snake, a clickable frequency table that draws mode vectors in 3D, live progress and a saveable plot."
**Verified:** 2026-09-27T23:30:00Z (UTC)
**Status:** **passed**
**Method:** Goal-backward structural verification against the actual codebase — every plan's `must_haves` frontmatter (07-01..07-10) checked at three levels (exists / substantive / wired), key links grepped and read in source, WSL gates re-run by the verifier. Windows smoke/xtb legs NOT re-run (evidence cited from 07-10-SUMMARY.md Task 1 verbatim logs, per verifier hand-off). Human verdicts cited from recorded checkpoint sign-offs.

## Goal Achievement

### Observable Truths — per-plan must_haves

| Plan | Truth (abbreviated) | Status | Evidence (actual code, not SUMMARY claims) |
| ---- | ------------------- | ------ | ------------------------------------------ |
| 07-01 | `freq_label` is the SINGLE shared imaginary formatter (ASCII `-31.9i`; `%.1f` plain) | ✓ VERIFIED | `spectra_ui.py:66-79`. Repo-wide grep: NO hand-rolled variant anywhere in `serpentrum/`; zero U+2212 glyphs; `plot_logic.py:16-20` documents it imports NO formatter (coordination held) |
| 07-01 | `table_rows` lists EVERY mode in file order, `%.4g` intensity | ✓ VERIFIED | `spectra_ui.py:82-97` — no filtering, `%.4g` label; zero-intensity + tiny-nonzero distinction pinned by `test_zero_intensity_listed`, `test_co2_vibspectrum_end_to_end` |
| 07-01 | `mode_arrow_primitives` returns primitives or None (never raises) | ✓ VERIFIED | `spectra_ui.py:100-126` — None on empty atoms / out-of-range / vector-less (vibspectrum); tests `test_out_of_range_none`, `test_vibspectrum_none`, `test_empty_atoms_none` |
| 07-01 | `run_status_lines` builds verdicts solely from the frozen record vocabulary, never re-scans log text | ✓ VERIFIED | `spectra_ui.py:129-146` — reads only `record['status']`/`problems`; echoes the record verbatim (cannot re-pin); `xtb_run` imported at module level and its DONE/FAILED/CANCELLED constants ARE consumed live in `gui_spectra.py:286`; `test_no_log_scanning` pins the no-file-read contract |
| 07-02 | `build_scene` wraps `spectra.broaden`, floors y_max, precomputes ticks, ASCII labels | ✓ VERIFIED | `plot_logic.py:111-133` — calls `spectra.broaden`; `Y_MAX_FLOOR=1.0` floor (`:114`); `nice_ticks` (value,label) pairs; `'wavenumber (cm-1)'`/`'IR intensity (km/mol)'` |
| 07-02 | `nice_ticks` classic 1/2/2.5/5×10ⁿ steps, total on degenerate input | ✓ VERIFIED | `plot_logic.py:66-88` — `_NICE_FACTORS=(1,2,2.5,5,10)`; `hi<=lo` returns single tick (no division); anchors pinned in tests |
| 07-02 | v1 ascending axis is an owner-signable convention; no FWHM control | ✓ VERIFIED + AMENDED | `plot_logic.py:103-109` documents the convention; owner AMENDED at 07-06 round 1 (unit modes / x-direction / y-invert / colors added in `scene_with_unit`, `UNIT_MODES`, `plot_logic.py:140-204`; invert flags in `gui_plot.py:52-83`) — defaults preserve the approved look; round-2 APPROVED |
| 07-02 | `size_presets` pure (label,(w,h)) data | ✓ VERIFIED | `plot_logic.py:207-218`, consumed via `addItem(label, preset)` in `gui_plot.py:369-371` |
| 07-03 | Viewer objects land ONLY under `srp_` prefix | ✓ VERIFIED | `pymol_bridge.py:499-500` — `MODE_VEC_NAME='srp_mode_vec'`, `XTBOPT_NAME='srp_xtbopt'`; cleanup contract docstrings; no non-srp_ load name in the phase-7 path |
| 07-03 | `zoom_mode_frame` frames once, None-safe (never Selector error) | ✓ VERIFIED | `pymol_bridge.py:552-566` — `object_exists` guard on both names, returns False when neither exists |
| 07-03 | Smoke 13 REQUIRED: re-asserts g98≡xtbopt overlay assumption every gate run | ✓ VERIFIED | `smoke/13_mode_arrows_smoke.py` exists (SMOKE-OK ×2); `tests/run_gates.py:69-72` REQUIRED_SMOKES entry with plan-07-03 comment |
| 07-03 | Frozen Phase-2 arrow contract untouched | ✓ VERIFIED | `git log 201fd8d..HEAD -- serpentrum/cgo_build.py` → **0 commits**; `mode_arrows` consumed at `scale=1.0` only (`gui_spectra.py:467`) |
| 07-04 | `log_tail()` returns a COPY of the bounded 500-line tail | ✓ VERIFIED | `xtb_runner.py:118-129` — `return list(self._log_lines)`; `_LOG_TAIL=500` bound maintained at `:282` |
| 07-04 | `spectra_runner` declared anchor field with docstring | ✓ VERIFIED | `__init__.py:55` — real class attribute, documented |
| 07-05 | ONE `paint_scene` seam serves BOTH paintEvent and render_image (route A) | ✓ VERIFIED | `gui_plot.py:85-233` seam; `paintEvent:317-325` and `render_image:236-261` both call it with forwarded option state (PNG parity for unit/invert/color) |
| 07-05 | Empty scene paints axes + centered hint, never crashes | ✓ VERIFIED | `gui_plot.py:113-118` — `EMPTY_HINT='run a calculation to plot a spectrum'`; tiny-rect guard `:141-142` |
| 07-05 | Save Plot = static getSaveFileName → 2× QImage PNG; cancel + `.png` append guarded | ✓ VERIFIED | `gui_plot.py:472-506` — static convenience (no `.exec_` token), `if not path: return`, `.endswith('.png')` append, try/except → status_cb |
| 07-05 | v1 adjustments exactly: size combo + axis toggle (+ owner amendments); QWidget.grab() only a comment | ✓ VERIFIED | `gui_plot.py:352-404` (unit/color/xdir/y-invert/labels/size/save); grab() demoted to comment `:36-38`; NO FWHM, no zoom/pan |
| 07-05 | GUI_MODULES registered in one edit; smoke 12 REQUIRED | ✓ VERIFIED | `tools/check_purity.py:72-74` — `gui_plot.py` + `gui_spectra.py` present; `run_gates.py:64-68` smoke-12 entry; `smoke/12_plot_smoke.py` has the guarded `QApplication.instance() or QApplication([])` construct (`:109-111`) |
| 07-06 | Plot look / reflow / toggle / save-PNG-outside-PyMOL human-verified before tab integration | ✓ HUMAN-CERTIFIED | `smoke/manual_plot_check.py` exists (non-NN_ name — never auto-run); **07-06-SUMMARY: round 2 (2026-09-26) owner typed "approved" in real Windows PyMOL — checkpoint RESOLVED**; commit `acecb92` |
| 07-06 | Ascending-axis convention got its first owner look | ✓ HUMAN-CERTIFIED | Round-1 verdict + four owner amendments recorded (07-06-SUMMARY:47); final sign-off at 07-10 |
| 07-07 | Page 2 is a LIVE SpectraTab; placeholder gone | ✓ VERIFIED | `gui.py:107-108` — `self.spectra_tab = SpectraTab(anchor_state, self.tabs)`; no `_build_spectra_placeholder` remains (grep: zero hits) |
| 07-07 | Live streaming: QPlainTextEdit read-only, 500-block cap, replay BEFORE connect | ✓ VERIFIED | `gui_spectra.py:137-139` (`setReadOnly` + `setMaximumBlockCount(500)`); `gui.py:310-311` — `replay_log(controller.log_tail())` then `log_line.connect` |
| 07-07 | Run-again re-enters the FULL pipeline; contextual button labels; Get Spectra re-enables on every terminal branch | ✓ VERIFIED | `run_again_requested` Signal (`gui_spectra.py:111`) → `gui.py:118-119` connects to `_on_spectra_requested` (the FULL pipeline, `:147-235`) — never `_launch_spectra_run` with stale args. Re-enables: run_finished `gui.py:326-330`, refused-start `:262-268`; precondition failures never disarm. Labels: 'Cancel xtb run' / 'Run again' / 'no xtb run yet' (`gui_spectra.py:172,224,246`) |
| 07-07 | Tab never reaches up; cancel direct on controller; game_tab.log_external still fed | ✓ VERIFIED | `gui_spectra.py:495-497` cancel via anchor-owned runner; emit-only run-again; `gui.py:283-287` log_external mirror |
| 07-08 | Terminal 'ok' record → parse → live fwhm → Scene → panel; construction-time populate on reload | ✓ VERIFIED | `gui_spectra.py:294-363` — `record_spectrum_paths` → `spectra.parse` → `plot_logic.build_scene` → `set_scene`; fwhm read LIVE (`:348-351`, `setup_logic.DEFAULTS` fallback); `reflect_run_state:253-274` routes terminal records through `on_run_finished` at construction |
| 07-08 | Degenerate states never fabricate; corrupt file → clear line | ✓ VERIFIED | `gui_spectra.py:341-347` — `except (spectra.SpectraParseError, OSError, ValueError)` → empty plot/table + `'spectrum could not be read: %s'`; `:326-334` degenerate path; `_refresh_from_record:278-292` resets non-ok records |
| 07-08 | Panel stays data-in; save outcomes via status_cb | ✓ VERIFIED | `gui_spectra.py:170-171` — `SpectraPlotPanel(self, status_cb=self.set_status_line)`; no runner coupling in `gui_plot.py` |
| 07-09 | Table lists EVERY mode via SHARED freq_label, `%.4g` | ✓ VERIFIED | `gui_spectra.py:367-393` — `_populate_table` from `spectra_ui.table_rows(self._spectrum)` only; read-only items; no re-derivation |
| 07-09 | Row r ⇔ `spectrum.modes[r]`; scale=1.0; delete-then-load replace | ✓ VERIFIED | Single-source `self._spectrum` (`:355`); `row + 1` to the selector (`:433`); `cgo_build.mode_arrows(prims[0], prims[1], scale=1.0)` (`:467`); `delete_object('srp_mode_vec')` before load (`:466-468`) |
| 07-09 | Vectors on OPTIMIZED frame; srp_xtbopt once per record (snake_id guard); zoom once per record | ✓ VERIFIED | `gui_spectra.py:439-457` — loads from `record['xtbopt_path']` under `_xtbopt_snake_id` guard (delete-then-reload on change); zoom under `_zoomed_snake_id` guard (`:471-473`); explicit status line `'mode %d: vectors drawn on the optimized structure (srp_xtbopt)'` |
| 07-09 | vibspectrum-only renders table, refuses vectors clearly; vanished objects tolerated | ✓ VERIFIED | `mode_arrow_primitives` None → refusal line `:434-438`; missing xtbopt → `:439-444`; guarded bridge deletes/zoom throughout |
| 07-09 | `show_srp_sticks` sweep before vector draw (d445e5a owner fix) | ✓ VERIFIED | `gui_spectra.py:463` — `pymol_bridge.show_srp_sticks()` before the arrow load; `pymol_bridge.py:537-549` (`hide spheres srp_*` + `show sticks srp_*`); commit `d445e5a` |
| 07-10 | Full gates green incl. both new REQUIRED smokes + --xtb | ✓ VERIFIED (WSL re-run) + CITED (Windows legs) | Verifier re-ran `python3.6 tests/run_gates.py`: **gate 1 PASS, gate 2 PASS, gate 3 PASS — 840 tests, OK, "all gates green"**. Windows legs cited from 07-10-SUMMARY Task 1 (verbatim logs on record): `--smoke` **10/10 REQUIRED PASS** via flushed SMOKE-OK sentinels (01,03,04,05,06,07,08,10,**12 PLOT-RENDER,13 MODE-ARROWS**); `--xtb` **PASS** — xtb 6.7.1pre + 'normal termination of xtb'. Post-e91c7ad re-run also recorded green |
| 07-10 | Complete live flow human-verified; optimized-frame sign-off; [TRAIN] discharges | ✓ HUMAN-CERTIFIED | **07-10-SUMMARY: consolidated checkpoint APPROVED round 2 (2026-09-26), owner verbatim "approved, well done"; BOTH sign-offs recorded — (8) optimized-frame interpretation APPROVED, (9) [TRAIN] discharges a-f ALL approved**; commits `c81e448` (verdict), `e91c7ad` (r1 fix), `d445e5a` (post-approval sticks sweep) |

**Score:** 38/38 must-have truths verified across 10/10 plans (36 structural + 2 human-certified truth-sets with recorded owner sign-offs).

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `serpentrum/spectra_ui.py` | PURE builders | ✓ SUBSTANTIVE | 173 lines (≥80), 5 builders, imports xtb_run |
| `serpentrum/plot_logic.py` | PURE plot half | ✓ SUBSTANTIVE | 232 lines (≥90), Scene/build_scene/nice_ticks/size_presets/mode_caption + owner-amended scene_with_unit |
| `serpentrum/gui_plot.py` | IrPlotWidget + seam + panel | ✓ SUBSTANTIVE | 506 lines (≥150); WIRED (imported by gui_spectra.py:76) |
| `serpentrum/gui_spectra.py` | Live SpectraTab | ✓ SUBSTANTIVE | 499 lines (≥150); WIRED (constructed at gui.py:107) |
| `serpentrum/gui.py` (edited) | Page-2 rewire | ✓ WIRED | SpectraTab construction, run_again connection, replay-before-connect, terminal re-enables, height cap (:84) |
| `serpentrum/pymol_bridge.py` (edited) | Bridge seams | ✓ WIRED | load_mode_arrows/load_xtbopt/show_srp_sticks/zoom_mode_frame all called from gui_spectra |
| `serpentrum/cgo_build.py` | FROZEN — untouched | ✓ UNTOUCHED | 0 commits in `201fd8d..HEAD`; consumed at scale=1.0 |
| `serpentrum/xtb_runner.py` (edited) | log_tail accessor | ✓ WIRED | returns list copy; consumed by gui.py:310 |
| `serpentrum/__init__.py` (edited) | spectra_runner field | ✓ WIRED | declared :55; create-or-reuse at gui.py:254-257 |
| `tests/test_spectra_ui.py` | 110+ lines | ✓ SUBSTANTIVE | 217 lines; all pinned anchors present |
| `tests/test_plot_logic.py` | 110+ lines | ✓ SUBSTANTIVE | 342 lines |
| `smoke/12_plot_smoke.py` | REQUIRED renderer smoke | ✓ WIRED | SMOKE-OK ×2; QApplication guard; in REQUIRED_SMOKES |
| `smoke/13_mode_arrows_smoke.py` | REQUIRED overlay smoke | ✓ WIRED | SMOKE-OK ×2; g98≡xtbopt <1e-3 Å leg; in REQUIRED_SMOKES |
| `smoke/manual_plot_check.py` | Manual harness | ✓ WIRED | non-NN_ name (gate glob `smoke/[0-9][0-9]_*.py` never auto-runs it) |
| `tools/check_purity.py` (edited) | GUI_MODULES entries | ✓ WIRED | gui_plot.py + gui_spectra.py at :72-74 |
| `tests/run_gates.py` (edited) | REQUIRED_SMOKES | ✓ WIRED | 12 + 13 entries with per-plan comments (:55-72) |
| `AGENTS.md` (edited) | QApplication-guard note | ✓ PRESENT | "Renderer smokes need a Q*Application" section |

### Key Link Verification

| From | To | Via | Status |
| ---- | -- | --- | ------ |
| `spectra_ui.freq_label` | table rows (gui_spectra) | `table_rows` → `_populate_table` | ✓ WIRED — single formatter, no second variant repo-wide |
| `plot_logic.build_scene` | `spectra.broaden` | direct call :111 | ✓ WIRED — committed broadener, live fwhm |
| `Scene` | `paint_scene` | paintEvent + render_image | ✓ WIRED — route A single seam |
| `gui_spectra._populate_spectrum` | record g98_path → parse → Scene | `record_spectrum_paths` (g98-first) | ✓ WIRED — precedence tested |
| fwhm read | anchor setup / DEFAULTS | live read :348-351 | ✓ WIRED — never re-pinned |
| `_on_table_cell_clicked` | mode_arrow_primitives → cgo_build.mode_arrows → bridge | BRIDGE seams only | ✓ WIRED — GUI never imports pymol.cmd (purity gate enforces) |
| `gui.py _connect_runner` | controller.log_line/started/run_finished | replay-before-connect :310-313 | ✓ WIRED — dialog-scoped once flag |
| `run_again_requested` | `_on_spectra_requested` full pipeline | gui.py:118-119 | ✓ WIRED — no stale-arg shortcut |
| `spectra_ui.run_status_lines` | xtb_run frozen vocabulary | module import; constants consumed live at gui_spectra:286 | ✓ WIRED — no re-scan of log text |
| smokes 12/13 | run_gates REQUIRED_SMOKES | plan-commented entries | ✓ WIRED |

### Requirements Coverage

| Requirement | Status | Blocking Issue |
| ----------- | ------ | -------------- |
| SPECTRA-01 (Get Spectra → tab switch, real tab) | ✓ SATISFIED (human-certified at 07-10) | none |
| SPECTRA-03 (broadened plot, adjustments, saveable PNG) | ✓ SATISFIED (07-06 round-2 + 07-10 approvals) | none |
| SPECTRA-04 (live progress → log panel) | ✓ SATISFIED (streaming + replay wiring; 07-10 certified) | none |
| SPECTRA-05 (every-mode table, −31.9i, zero-intensity, row-click vectors) | ✓ SATISFIED (structural + 07-10 certified) | none |
| SPECTRA-02/06 (Phase 6 scope) | ✓ unchanged, still satisfied | none |

Note: REQUIREMENTS.md rows for SPECTRA-01/03/04/05 still read "Pending"/`[ ]` — per house flow these rows are orchestrator-owned (07-10-SUMMARY:150); not a code gap.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| serpentrum/pymol_bridge.py | 246 | "Phase-3 placeholder" in docstring | ℹ️ Info | Historical reference to Phase-3 record semantics, not a stub — no action |
| (all other phase files) | — | TODO/FIXME/placeholder/empty-impl scan | — | CLEAN |

No `.exec_()` calls anywhere in `serpentrum/` (modeless rule holds; purity gate enforces). No blocker or warning anti-patterns in any phase-7 file.

### Accepted Limitations (recorded — NOT gaps)

1. **No co2 g98 fixture** — linear-molecule g98 table/vector leg is smoke-only behind `--xtb` real runs (documented in spectra_ui.py docstring + 07-10-SUMMARY Known Limitations).
2. **Zero-intensity coverage is unit-level** — synthetic Mode tuples + synthetic co2 vibspectrum fixture.
3. **g98≡xtbopt generality = one fixture + always-on smoke 13** (<1e-3 Å re-assertion each gate run; one-fixture origin recorded).
4. **Selector-Error zoom noise + small-imaginary guidance line** — deferred v1 cosmetics, owner-approved with the noise visible (07-10-SUMMARY:32).

### Human Verification Required

None outstanding. Both blocking human checkpoints are CLOSED with recorded owner sign-offs:
- **07-06 plot checkpoint:** APPROVED round 2 (2026-09-26, owner typed "approved" in real Windows PyMOL) — `acecb92`.
- **07-10 consolidated live-flow checkpoint:** APPROVED round 2 (2026-09-26, owner verbatim "approved, well done") covering the full SC1/SC2/SC3 flow, the optimized-frame interpretation sign-off, and all [TRAIN] discharges a-f — `c81e448`.

### Gaps Summary

None. All 38 must-have truths across plans 07-01..07-10 verified against the actual codebase at all three levels (existence, substantive, wired); all key links intact; the WSL gate battery re-run green by this verifier (840 tests, gates 1-3 PASS); the Windows smoke/xtb legs evidenced by the verbatim logs recorded in 07-10-SUMMARY.md Task 1; and the user-facing success criteria are human-certified by two recorded round-2 owner approvals. The four accepted limitations above are owner-visible and do not block the goal. Phase goal achieved.

---

_Verified: 2026-09-27T23:30:00Z (UTC)_
_Verifier: OpenCode (gsd-verifier)_
