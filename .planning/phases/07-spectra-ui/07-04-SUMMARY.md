---
phase: 07-spectra-ui
plan: 04
subsystem: infra
tags: [qt, qprocess, xtb, pymol, plugin, anchor-state, log-replay]

# Dependency graph
requires:
  - phase: 06-xtb-pipeline
    provides: XtbRunController with frozen signals/status()/_log_lines bounded tail (06-05); dialog create-or-reuse wiring (06-09)
  - phase: 5.2-stacking-game-rules
    provides: shared-file ordering release on serpentrum/__init__.py (5.2-09 wrap)
provides:
  - "XtbRunController.log_tail() — public read-only accessor returning a COPY of the bounded 500-line log tail (early-line replay seam for late-connecting UIs)"
  - "_SerpentrumState.spectra_runner — declared anchor field with the live-object contract docstring (dialog-scoped Qt connections; controller survives Plugin-Manager reload)"
affects: [07-spectra-ui (plans 07-05 through 07-07 — the Spectra tab consumes both seams)]

# Tech tracking
tech-stack:
  added: []
  patterns: ["replay-then-connect: late-connecting UI replays controller.log_tail() before connecting log_line, closing the reload/double-connect early-line hole", "anchor discipline: every live object on _SerpentrumState is DECLARED with a docstring contract, never setattr'd into undocumented existence"]

key-files:
  created: []
  modified:
    - serpentrum/xtb_runner.py
    - serpentrum/__init__.py

key-decisions:
  - "log_tail() returns list(self._log_lines) — explicit copy semantics so callers can never mutate controller state; _log_lines stays the ONLY writer-owned private list (06-05 frozen)"
  - "spectra_runner declared adjacent to spectra_run (end of the anchor block) so the frozen 06-05 spectra_run declaration does not shift; spectra record/controller stay colocated"

patterns-established:
  - "Read-only accessor pair on the runner shell: status() + log_tail(), both copy-out, zero locks (same-thread Qt signal delivery)"

# Metrics
duration: 3min
completed: 2026-09-26
---

# Phase 7 Plan 04: Seam-Gap Closures Summary

**Early-line replay seam (XtbRunController.log_tail copy-out accessor) and declared spectra_runner anchor field — the two research-flagged Phase-6 seam gaps closed with 21 additive lines, zero behavior change.**

## Performance

- **Duration:** 3 min
- **Started:** 2026-09-26T17:41:59Z
- **Completed:** 2026-09-26T17:45:15Z
- **Tasks:** 2/2
- **Files modified:** 2

## Accomplishments
- `XtbRunController.log_tail()` appended immediately after `status()` (the 06-05 thin-shell accessor region): returns `list(self._log_lines)` — a COPY of the bounded 500-line tail. A UI that connects AFTER a launch (dialog reopened; plugin reloaded onto a live controller whose old Qt connections died with the dead dialog) replays this tail before connecting `log_line`, so lines emitted before the connect are never lost. Closes 07-RESEARCH-spectra-seam.md Q2 ambiguity 1.
- `_SerpentrumState.spectra_runner = None` declared with the full contract docstring: an XtbRunController create-or-reused by the dialog at first launch (gui.py, 06-09); Qt connections are DIALOG-scoped and re-connected fresh; the controller object survives Plugin-Manager reload like dialog/controller; consumed by the Spectra tab (07-07) via getattr guards. Closes Q2 ambiguity 2 — the field was previously only `setattr`'d into undocumented existence.
- Both edits strictly additive: combined diff vs base 33fe3ec = 2 files, 21 insertions, 0 deletions. Signals, terminal branch, copy-out policy, spray-dir deletion, anchor bootstrap — all byte-stable frozen 06-05/06-06 contracts.

## Task Commits

Each task was committed atomically:

1. **Task 1: XtbRunController.log_tail() public accessor** - `49e08eb` (feat)
2. **Task 2: declare the spectra_runner anchor field** - `ab76ca0` (feat)

**Plan metadata:** `docs(07-04): complete seam-gap closures plan` (final commit of this plan, carrying this SUMMARY)

## Files Created/Modified
- `serpentrum/xtb_runner.py` — +13 lines: `log_tail()` accessor next to `status()`; returns `list(self._log_lines)` (copy semantics; `_log_lines` stays the only private writer-owned list)
- `serpentrum/__init__.py` — +8 lines: `spectra_runner = None` declared on `_SerpentrumState` after the frozen `spectra_run` declaration, with the live-object contract docstring

## Decisions Made
- **Copy-out, not reference:** `log_tail()` returns `list(self._log_lines)` so a UI mutating the replayed list (e.g. trimming for display) can never corrupt controller state. Matches the read-only contract of `status()`; no locks needed (same-thread Qt signal delivery per 06-RESEARCH-runner).
- **Placement after `spectra_run`:** the anchor block is append-only by house discipline; `spectra_runner` was declared at the end (adjacent to `spectra_run`) rather than between `last_run` and `spectra_run`, so the frozen 06-05 `spectra_run` attribute/comment lines do not shift. The spectra record and its controller now read as one pair.

## Deviations from Plan

None - plan executed exactly as written. (The plan's "after the last_run declaration" placement guide was honored at the end of the anchor block — `spectra_run`, added by 06-05 after `last_run`, is the last declared group; appending there is the only edit that keeps both snippets verbatim AND leaves every existing declaration byte-stable.)

## Issues Encountered
None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- **07-05/07-06 (seam consumers) unblocked:** `controller.log_tail()` is the sanctioned early-line read; `anchor.spectra_runner` is a first-class getattr-guardable field.
- **07-07 (Spectra tab) contract available:** replay `controller.log_tail()` on connect, then `log_line.connect(...)` going forward; the reload hole is closed by construction.
- Combined branch diff is additive-only (2 files, +21/-0) — merge is a guaranteed clean fast-forward; no overlap hazards with other wave-1 plans (`xtb_runner.py` and `__init__.py` are this plan's owned files).
- Gate evidence: `python3.6 tests/run_gates.py` green after each task — 796/796 unittests, gates 1-3 PASS (syntax + plugin-path safety, AST purity, scoped unittest discovery).

---
*Phase: 07-spectra-ui*
*Completed: 2026-09-26*
