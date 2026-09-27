---
phase: 08-demo-data-docs-release-audit
plan: 07
subsystem: docs
tags: [readme, docs-01, release, install-route, gate-d, vibe-block, audit-tokens, ascii]

# Dependency graph
requires:
  - phase: 08-demo-data-docs-release-audit (08-01)
    provides: "GATE D decision record: d3-option-amend vibe-block line-4 literal, d1-c-staleness, d4-confirm-all, owner head-combo directive"
  - phase: 01-plugin-skeleton-purity-harness (01-06)
    provides: "APPROVED install route (Add plugin directory -> repo root -> restart PyMOL OR re-add) + locked reload phrasing"
  - phase: 03 (demo data) / 07 (spectra UI)
    provides: "manifest.json CIDs + atom counts, stacking_pi_stack.json tokens + herringbone sentence, Start-only flow seams"
provides:
  - "Release README.md with zero placeholders (DOCS-01): GATE D-decided vibe block, xtb-only requirements, 01-06-verified install route, Start-only usage with audit tokens, demo-set section pointing at the attribution document of record"
  - "The token contract 08-03's mechanical audit pins against code/data literals"
affects: [08-03 (doc-vs-code mechanical audit), 08-11 (GATE V reproduce-steps leg), 08-08/08-09 (README already matches their Start-only + head-combo-at-demo-set-selection flow)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Docs-as-contract: every numeric/flow claim in README sourced from a code or data literal (setup_logic defaults/pinned warning, stacking JSON, manifest.json) so the mechanical audit can grep-pin it"
    - "ASCII-only README matching the shipped-text house convention (A / deg / cm-1 / -> arrows)"

key-files:
  created:
    - .planning/phases/08-demo-data-docs-release-audit/08-07-SUMMARY.md
  modified:
    - README.md

key-decisions:
  - "Vibe block line 4 = GATE D d3-option-amend literal EXACTLY: '> !! v1.0 - vibe-coded, review before production/teaching use !!' (lines 1-2 preserved byte-identical, incl. line-1 trailing space)"
  - "Usage section is Start-only: 'Apply / Show in Viewer' never appears; the 04-06 apply+materialize-inside-Start path is documented as the sole entry point"
  - "xtb is the ONLY external binary prerequisite; xtb4stda/std2 mentions removed (v1 never invokes them)"
  - "DATA_SOURCES.md phrased as 'the attribution document of record, whose approval is decided at the v1.0 release gate' - no premature APPROVED assertion before GATE V"

patterns-established:
  - "Every backticked token that looks like a path in README is a full repo-relative path verified to exist on disk (12/12)"

# Metrics
duration: 6min
completed: 2026-09-27
---

# Phase 8 Plan 7: README rewrite (DOCS-01) Summary

**Release README rewritten end-to-end: GATE D-decided vibe block ("!! v1.0 - vibe-coded, review before production/teaching use !!"), xtb-only prerequisites, the 01-06 human-verified install route, Start-only usage flow with every numeric token sourced from code/data literals, and a demo-set section that defers attribution approval to GATE V - zero placeholders, pure ASCII, audit-ready.**

## Performance

- **Duration:** ~6 min
- **Started:** 2026-09-27T18:19:31Z
- **Completed:** 2026-09-27T18:25:22Z
- **Tasks:** 2
- **Files modified:** 1 (README.md)

## Accomplishments

- **Task 1 (front sections):** Vibe block lines 1-2 preserved byte-identical (including the line-1 trailing space, verified with `cat -A`); line 4 replaced with the GATE D d3-option-amend literal. Requirements trimmed to xtb as the only external binary (6.7.1pre-windows-x86_64 tested note + 6.7.0 missing-a-library note kept); xtb4stda/std2 fully removed. Install section now carries the 01-06-APPROVED route verbatim phrases ("Add plugin directory" -> repo root containing the `serpentrum/` package -> "restart PyMOL OR re-add the plugin directory in Plugin Manager") plus the zip release alternative; the false "Install New Plugin" recipe is gone. Usage documents the Start-only flow: Setup tab -> Start (applies + materializes box/head first per 04-06, then the 3-2-1 countdown, dialog switches to Game tab) -> 4 arrow keys (click-the-viewer focus hint + dialog-focus auto-pause) -> completion -> Get Spectra -> live log (Cancel / Run again) -> plot controls -> Save Plot (PNG) -> table-row mode vectors; canonical tokens present: speeds 3.0/6.0 (default)/7.5/9.0 A/s, box presets 35/55/85 A half-widths (medium default), win cap default 10 (range 1-20), atom budget 100, broadening 16.0, calibrated HESSIAN_WARNING numbers (84-101 s, up to ~5 min single-threaded, ~100-atom / 4-core-8-thread). Head combo documented per the GATE D owner directive ("choose the demo set - head options fill in; Random picks from the set") without claiming randomization of the default pick. Cleanup (srp_* only) and SRP_SPECTRA_DIR artifacts documented; no 'P = pause' claim.
- **Task 2 (back sections):** Demo Set A section with all five CIDs (241/931/8418/995/7095) + atom counts, stacking tokens 3.383 / 1.231 / 3.60 A / 20.0 deg, the herringbone sentence transcribed verbatim from `serpentrum/data/stacking_pi_stack.json`, the [JAN2000] crystalline-scope caveat transcribed from DATA_SOURCES.md section 2, and the biphenyl orthogonal-rings clash refusal as the designed "no invented chemistry" demonstrator. `serpentrum/data/DATA_SOURCES.md` referenced as the attribution document of record with approval explicitly deferred to the v1.0 release gate (no premature APPROVED claim). Project Structure uses only full repo-relative backticked paths that exist on disk (12/12 verified). License confirmed BSD 3-Clause against LICENSE; Acknowledgements give the PubChem public-domain acknowledgment and the cited-never-redistributed Janiak/COD entries.
- **GATE D literal (recorded per plan STEP 0):** `> !! v1.0 - vibe-coded, review before production/teaching use !!`

## Task Commits

Each task was committed atomically:

1. **Task 1: README front sections - GATE D vibe block, xtb-only requirements, verified install route, Start-only usage** - `1411026` (docs)
2. **Task 2: README back sections - demo set, project structure, license/acknowledgements + token verification** - `211597e` (docs)

**Plan metadata:** (this commit - `docs(08-07): complete README rewrite plan`)

## Files Created/Modified

- `README.md` - full release rewrite (79 lines, pure ASCII); every claim traceable to a code or data literal

## Decisions Made

- **Path-token rule:** any backticked path-like token in README is a full repo-relative path that exists on disk (e.g. `serpentrum/data/manifest.json`), so 08-03 check 6 passes mechanically. Bare filenames inside a directory bullet (gui.py, etc.) are written as plain text, not backticked paths.
- **No new claims:** hessian wording quotes only the calibrated `setup_logic.HESSIAN_WARNING` numbers (never the pre-calibration '30-90 s'); stacking values quote the dataset encoding (3.383/1.231) plus the composed display (3.60/20.0); never '3.4 A' (UNVERIFIED per DATA_SOURCES.md section 3).

## Deviations from Plan

None - plan executed exactly as written. (The full-repo-relative backticked-path normalization in the Project Structure section is the plan's own "every backticked path must exist on disk" requirement, satisfied within Task 2 before commit.)

## Issues Encountered

None.

**Stale-planning-claim note (recorded honestly per the plan, no edit made):** PROJECT.md:51 claims the README contains a leftover "sECDpent" name from another project to be fixed in this rewrite. Verified 2026-09-27: `grep -in sECDpent README.md spec.md` returns ZERO hits (the name survives only inside `.planning/` prose: PROJECT.md:51 and ROADMAP.md:300), matching 08-RESEARCH-help-docs.md section 4b. No fix was needed; absence is the audit assertion. PROJECT.md was NOT edited here (out of plan scope).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **DOCS-01 satisfied:** README documents install, usage, and the demo set with the vibe-coding warning block intact (sub-line = d3-option-amend literal); every claim matches actual behavior.
- **Token contract established for 08-03:** banned greps (TBD / sECDpent / xtb4stda / 'P = pause' / 'Apply / Show in Viewer' / 'Install New Plugin' / 'Generate and export') all return zero; required greps ('Add plugin directory', 'restart PyMOL', `serpentrum/data/DATA_SOURCES.md`, all five CIDs, 3.383/1.231/3.60 A/20.0 deg) all present; pure ASCII; `python3.6 tests/run_gates.py` all green (844 tests, gates 1-3 PASS).
- **Forward coupling:** the README's Start-only flow and demo-set-selection head combo match the release state 08-08 (Apply removal + head-combo repopulation) and 08-09 (staleness text fix) implement; 08-11's reproduce-steps segment can walk the Usage section line-by-line.

---
*Phase: 08-demo-data-docs-release-audit*
*Completed: 2026-09-27*
