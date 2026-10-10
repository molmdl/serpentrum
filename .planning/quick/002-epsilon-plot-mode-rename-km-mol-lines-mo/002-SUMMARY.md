---
phase: quick-002
plan: 002
subsystem: spectra-ui
tags: [ir-plot, unit-modes, epsilon, km-mol-lines, qpainter, route-a-parity]
requires: [07-05-qt-plot-seam, 07-06-plot-checkpoint, 07-08-plot-embed, "GATE V amendment 2026-10-04 (Multiwfn-parity curve + epsilon axis label)"]
provides:
  - "4-entry UNIT_MODES: 'epsilon (Multiwfn curve)' default (label-only rename) + NEW 'lines (km/mol)' discrete-sticks mode + unchanged absorbance/transmittance"
  - "Scene.sticks (raw (freq, intensity) table values echoed by build_scene) + Scene.segments (the lines paint representation)"
  - "scene_with_unit 'lines' derivation: baseline-rooted vertical segments at the exact table values, no broadening, x window widens LEFT for imaginary modes, loud ValueError on re-derivation"
  - "paint_scene ONE representation branch (curve polyline vs per-mode drawLine) through the unchanged single seam — route-A PNG parity for both representations"
  - "smoke 12 STAGE6 LINES leg (the painter branch's only automated coverage) + manual-gate checklist steps h (renamed default) / h2 (lines mode)"
affects: [08-demo-data-docs-release-audit]
tech-stack:
  added: []
  patterns:
    - "sticks-as-data / segments-as-paint-representation split: the base curve scene carries the RAW mode data; scene_with_unit synthesizes the paint payload, so the panel derive path covers all modes with ZERO GUI changes"
    - "representation branch at the ONE paint seam: same pen (#1f4fff/width 2), same clip rect, same _map_x/_map_y — invert/color/size options apply to sticks for free"
key-files:
  created:
    - ".planning/quick/002-epsilon-plot-mode-rename-km-mol-lines-mo/002-SUMMARY.md"
  modified:
    - "serpentrum/plot_logic.py"
    - "serpentrum/gui_plot.py"
    - "tests/test_plot_logic.py"
    - "smoke/12_plot_smoke.py"
    - "smoke/manual_plot_check.py"
decisions:
  - "Label-only rename: the default combo entry reads 'epsilon (Multiwfn curve)' but the internal mode key STAYS 'intensity' (passthrough semantics; every pre-existing pin byte-holds)"
  - "Chosen shape (plan-pinned, rejected alternatives not revisited): base curve scene echoes sticks; scene_with_unit synthesizes segments; the panel/_derive_scene/tab need ZERO code changes"
  - "A lines scene never re-derives: scene_with_unit raises ValueError for 'lines'/'absorbance'/'transmittance' on a segments-carrying scene ('intensity' stays identity passthrough) — lines never feed the curve-based units"
  - "Combo + axis-label wording is PROVISIONAL: the owner blesses the final labels live at the GATE V amendment round (owner directive 2026-10-10)"
  - "Absorbance/transmittance math byte-frozen (scale-invariant normalization + 10^-A; untouched for the third consecutive approval)"
metrics:
  duration: "~18 min"
  completed: "2026-10-10"
---

# Quick Task 002: Epsilon plot-mode rename + km/mol discrete-lines mode — Summary

**One-liner:** The y-unit combo stops lying after the Multiwfn-parity change — the default entry renames to `'epsilon (Multiwfn curve)'` (label-only; the approved curve and its `'epsilon (L mol-1 cm-1)'` axis untouched) and a NEW `'lines (km/mol)'` mode draws one baseline-rooted vertical stick per mode at the actual table values (Multiwfn discrete-lines style, no broadening, imaginary sticks at negative x), derived purely through `scene_with_unit` and painted through the ONE unchanged seam (route-A PNG parity), with the panel and tab needing zero code changes.

## What was delivered

1. **Pure half (`plot_logic.py`, Task 1 commit `2608cca`).** `Scene` namedtuple gains two trailing fields: `sticks` (the RAW `(freq, intensity)` float pairs echoed by `build_scene` — the table / spectrum_line.txt values, carried unchanged like `n_modes`) and `segments` (the paint representation — `None` for every curve scene). `UNIT_MODES` becomes the 4-entry owner-confirmed table with `'epsilon (Multiwfn curve)'` first (default; internal key stays `'intensity'`). `scene_with_unit` gains a loud `ValueError` guard (a segments-carrying scene never re-derives — lines do not feed the curve-based units) and the `'lines'` derivation: baseline-rooted `((freq, 0.0), (freq, inten))` segments, fwhm-irrelevant (discrete by definition), x window keeps the curve's right bound (3600.0) and widens LEFT to the most-negative stick (-31.9175 on the fixture), empty modes -> `()` segments with the `Y_MAX_FLOOR` axis, real-unit axis label `'IR intensity (km/mol)'` (the table header's literal), test pins: renamed 3-entry literals -> 4-entry + **9 new `TestLinesMode` tests** (sticks echo, segment shape/order, axis labels, y_max headroom over PEAK_INTEN, negative-x widening, empty contract, fwhm irrelevance, passthrough counters, never-re-derives).
2. **GUI half (`gui_plot.py` + smokes, Task 2 commit `496d4e2`).** `paint_scene`'s curve block restructured into ONE representation branch: pen construction (pinned `#1f4fff` / width 2 / clip rect) moves above; a segments-carrying scene draws one vertical `drawLine` per mode through the SAME `_map_x`/`_map_y` (invert_x/invert_y/line_color apply to sticks unchanged); else the behavior-identical QPolygonF polyline. `render_image` inherits the branch via the unchanged seam — route-A PNG parity for the lines representation. **`SpectraPlotPanel` + Spectra tab: zero code changes** (combo populates from the 4-entry `UNIT_MODES`; `_unit_mode` default key unchanged; `_derive_scene` routes `'lines'`). smoke 12 gains the **STAGE6 LINES** leg (pure derive -> 72 baseline-rooted segments -> `render_image` 1280x800 -> valid PNG) — the painter branch's only automated coverage per the 01-05 headless-widget ban; the manual gate checklist's step h names the renamed default and the new step h2 walks the discrete mode.

## Provisional wording (owner blessing pending)

Per the owner directive (2026-10-10, mid-GATE-V, design confirmed by owner option pick): the combo labels — `'epsilon (Multiwfn curve)'` and `'lines (km/mol)'` — and the lines axis label `'IR intensity (km/mol)'` are **PROVISIONAL**. The owner blesses the final wording **live at the GATE V amendment round**; `manual_plot_check.py` steps h/h2 are the blessing surface, and any re-wording is a label-only edit (combo literals in `UNIT_MODES` / the single axis literal in the `'lines'` derivation + their coupled pins). The epsilon-mode axis label `'epsilon (L mol-1 cm-1)'` is byte-unchanged (GATE V 2026-10-04, still pinned at test line 201).

## Verification

- `python3.6 tests/run_gates.py` — default battery green before EACH commit: 995 unittests (986 baseline + exactly the 9 new pins, matching the plan's estimate), gates 1-3 PASS (incl. AST purity — `plot_logic` still PURE, `gui_plot` still GUI-class, no allowlist changes).
- `python3.6 tests/run_gates.py --smoke` (before the Task-2 commit) — **all 11 required smokes PASS**; informational smoke 02 FAIL non-blocking (the known 01-05 dead end). `smoke/12_plot_smoke.py: PASS (sentinel SMOKE-OK)`.
- **Smoke-12 one-liner (documented leg, from repo root):** `timeout 90 cmd.exe /c "C:\\src\\run-conda-pymol.bat -cq smoke\\12_plot_smoke.py"` flushed `STAGE0 APP / STAGE1 SCENE modes=72 imaginary=3 / STAGE2 PNG-FULL 56735 bytes / STAGE3 PNG-NOLABELS 33575 / STAGE4 PNG-EMPTY 8308 / STAGE5 OPTIONS 45219 / STAGE6 LINES 20105 bytes / SMOKE-OK PLOT-RENDER` — verdict by flushed sentinels, exit codes ignored per the .bat contract.
- Headless spot-proof (plan `<verification>` 3): final line `QUICK002-SPOT-OK`.
- Frozen surfaces: `git diff` shows ZERO lines in `spectra.py`, `gui_spectra.py`, `gui.py`, `README.md`, `smoke/14_release_e2e_smoke.py`, `tests/test_gui_pins.py`, `DATA_SOURCES.md`, any `08-*` file; the absorbance/transmittance tests pass byte-UNMODIFIED (the test diff's only removed lines are the three old UNIT_MODES pins + two comments); nothing named `srp_` touched (no viewer work).
- Scope guard: the two code commits touch exactly the plan's 5 `files_modified` (plus this planning file); working tree clean.

## Deviations from Plan

1. **[Rule 2 — truthful docs] `build_scene` docstring signature line.** The plan specified adding one docstring sentence only; the existing `Scene(xs, ys, ..., fwhm)` field list in that docstring would have gone stale (two new trailing fields shipped). Amended the signature line to `..., fwhm, sticks, segments)` beside the plan's verbatim sentence, so the docstring stays truthful. No behavior change.

No bugs, blockers, authentication gates, or architectural decisions encountered; everything else executed plan-verbatim (including the exact seam code, guard order, literals, and commit messages).

## Commits

| Task | Commit | Message |
| ---- | ------ | ------- |
| plan | 1b87255 | docs(quick-002): plan epsilon rename + km/mol discrete-lines mode |
| 1 | 2608cca | feat(quick-002): rename epsilon unit mode + add km/mol discrete-lines mode (pure half) |
| 2 | 496d4e2 | feat(quick-002): paint discrete-lines scenes + smoke/manual gate updates |
| docs | (this commit) | docs(quick-002): record epsilon rename + lines-mode summary |

## Follow-ups

- **GATE V amendment round:** the owner blesses the final combo + lines axis wording live (steps h/h2 of `manual_plot_check.py`); any post-blessing re-wording is a label-only edit with coupled pins (see Provisional wording above).
- README intentionally untouched (line 43's "y unit / color / x direction / invert / size presets" generic wording still holds) — documents follow the owner-blessed wording at the gate, per the plan.
