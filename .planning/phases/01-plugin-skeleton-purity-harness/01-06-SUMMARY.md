---
phase: 01-plugin-skeleton-purity-harness
plan: 06
subsystem: infra
tags: [gates, agents-md, pitfall-correction, human-verify, pyqt5, pymol, plugin, modeless, single-instance, wsl]

# Dependency graph
requires:
  - phase: 01-plugin-skeleton-purity-harness
    provides: run_gates.py gate runner (01-03, --smoke/--xtb flags from 01-05), 3-tab PluginDialog shell (01-02), headless smoke + anchor pattern (01-04), offscreen dead-end verdict (01-05)
provides:
  - "AGENTS.md gates & conventions section: canonical gate commands, plugin-path safety hard rules, true module identity (pmg_tk.startup.serpentrum), modeless rule, purity classes — inherited by every future phase"
  - ".planning/research/PITFALLS.md dated correction: loader module name is pmg_tk.startup.<name> (pymol.plugins.startup is an attribute alias)"
  - "Full gate-suite evidence (all 5 gates green end-to-end): default + --smoke + --xtb + combined, captured in /tmp/opencode/phase1_gates/"
  - "Human-verify approval: plugin install, single 'serpentrum' menu item → 3-tab modeless dialog, single-instance under double-open + reload — verified in real Windows PyMOL 2.5.0 across 3 launches"
  - "Phase 1 acceptance closed: all 6 plans complete (6/6), SETUP-01/INFRA-01..03/05/06 verified"
affects: [phase-2 pure core, all phases 2-8 (gates + conventions), phase-6 xtb pipeline (xtb gate), phase-8 release audit (gate suite)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "AGENTS.md as the living environment contract: gate commands + trap-avoidance conventions codified once, inherited by every later phase"
    - "Dated correction notes in research records (append, never rewrite history)"
    - "Human-verify checkpoint as the phase acceptance gate for the irreducibly visual halves (menu item, dialog, modelessness)"

key-files:
  created:
    - .planning/phases/01-plugin-skeleton-purity-harness/01-06-SUMMARY.md
  modified:
    - AGENTS.md
    - .planning/research/PITFALLS.md
    - tests/run_gates.py
    - .planning/STATE.md
    - .planning/ROADMAP.md

key-decisions:
  - "Human-verify approved in real Windows PyMOL 2.5.0 (3 separate launches, restart between checks): single menu item → 3-tab modeless dialog; single-instance + reload-via-restart hold [SETUP-01, INFRA-03, INFRA-05]"
  - "Step-6 wording lesson: 're-select plugin directory OR restart PyMOL' confused the user — restart is the simpler, equally valid reload path; future docs should phrase it as 'restart PyMOL OR re-add the plugin directory in Plugin Manager'"
  - "Research corrections are appended as dated notes, never silent rewrites (PITFALLS.md Pitfall-7 correction)"

patterns-established:
  - "Phase-closing ritual: full gate suite green + human-verify of the visual halves + AGENTS.md conventions update"
  - "Gate evidence captured to /tmp/opencode/<phase>_gates/ as one-line-verifiable artifacts"

# Metrics
duration: 4min (auto-tasks; plus human checkpoint wait)
completed: 2026-09-06
---

# Phase 1 Plan 6: AGENTS.md gates + human-verify checkpoint Summary

**Phase 1 closed: gate commands + plugin-path safety + module identity codified in AGENTS.md, all 5 gates green end-to-end (incl. SMOKE-OK SKELETON + xtb normal termination), and human verification in real Windows PyMOL 2.5.0 approved install → single 'serpentrum' menu item → 3-tab modeless dialog with single-instance + reload survival (3 clean launches).**

## Performance

- **Duration:** ~4 min auto-tasks (continuation resume 2026-09-06T14:25:36Z → ~14:30Z) + human checkpoint wait (user verification between agents)
- **Started:** 2026-09-06T14:25:36Z (continuation; prior agent executed Tasks 1–2 and reached the Task 3 checkpoint)
- **Completed:** 2026-09-06T14:30Z
- **Tasks:** 3
- **Files modified:** 3 (code/docs) + 3 (planning docs)

## Accomplishments

- **Task 1** — `AGENTS.md` gained the `## serpentrum plugin gates & conventions (Phase 1)` section: the three gate commands (`python3.6 tests/run_gates.py [--smoke|--xtb]`, smoke-verdict = flushed `SMOKE-OK` sentinels, never exit codes), the smoke one-liner for debugging a single smoke, the plugin-path safety hard rules (NO `__init__.py` in `tests/`/`smoke/`/`tools/`; NO top-level `*.py` at repo root — findPlugins would autoload them), the true module identity (`pmg_tk.startup.serpentrum`; `pymol.plugins.startup` is only an attribute alias; live state anchors on `pmg_tk.startup._serpentrum`), the modeless rule (`.show()` only, AST checker fails `.exec_()`), and the purity classes (entry lazy-imports inside functions; GUI allowlist = pymol.Qt only; everything else under `serpentrum/` pure). `.planning/research/PITFALLS.md` received the dated Pitfall-7 correction note (actual sys.modules key is `pmg_tk.startup.<name>`; append, not rewrite).
- **Task 2** — Full gate suite end-to-end as the phase's machine proof, all captured in `/tmp/opencode/phase1_gates/`: `default.txt` (gates 1–3 PASS, 32 unittests OK), `smoke.txt` (gate 4 PASS, `SMOKE-OK SKELETON` flushed; 02_dialog_smoke reported informational FAIL non-blocking per the 01-05 dead-end verdict), `xtb.txt` (gate 5 PASS, xtb 6.7.1pre "normal termination"), `all.txt` (`--smoke --xtb` combined: gates 1–5 PASS). `tests/run_gates.py` notes now echo the proof lines so verdicts are greppable.
- **Task 3 (human-verify, checkpoint)** — **APPROVED by the user in real Windows PyMOL 2.5.0 GUI.** All observable steps passed: Plugin Manager "Add plugin directory" → repo root → restart; exactly ONE "serpentrum" menu item (under Plugin); click opens the dialog titled "serpentrum" with exactly 3 tabs (Setup / Game / Spectra); modelessness confirmed (viewer rotate/zoom + command line both responsive with dialog open); single instance confirmed (re-click raises the existing dialog, no duplicate); reload path + reopen clean; close/reopen without errors or duplicates. The user launched PyMOL **3 separate times** (restarting between checks) — all passes clean.

## Human Verification Record (Task 3)

**Verdict: approved** — real Windows PyMOL 2.5.0, 3 launches, restarts between checks, every step green. Maps to SETUP-01 (install + single menu item + 3-tab dialog), INFRA-03 (single instance under double-open + reload), INFRA-05 (modelessness).

**Step-6 note (recorded verbatim-ish from the user):** the wording of step 6 ("Plugin-Manager re-select OR restart") was found **confusing** — the user used the restart alternative, which passed. **Doc lesson for future phases:** phrase reload verification as *"restart PyMOL OR re-add the plugin directory in Plugin Manager"* — restart is the simpler, equally valid reload path. No code changes required; the single-instance anchor held across both reload routes exercised.

## Task Commits

Each task was committed atomically:

1. **Task 1: Document gates + plugin conventions in AGENTS.md; correct PITFALLS.md module name** — `986d5c6` (docs)
2. **Task 2: Full gate suite end-to-end; surface proof lines in gate notes** — `a72d0b2` (feat)
3. **Task 3: Human-verify checkpoint — install, single instance, modeless dialog** — no commit (verification task; verdict approved; evidence = user response + this record)

**Plan metadata:** (this commit — `docs(01-06): complete AGENTS.md gates + human-verify checkpoint plan`)

## Files Created/Modified

- `AGENTS.md` — new "serpentrum plugin gates & conventions (Phase 1)" section (gates, smoke one-liner, plugin-path safety, module identity, modeless rule, purity classes)
- `.planning/research/PITFALLS.md` — dated Pitfall-7 correction: module name is `pmg_tk.startup.<name>` (pymol.plugins.startup = attribute alias)
- `tests/run_gates.py` — gate success notes now echo proof lines (SMOKE-OK sentinels, xtb normal termination)
- `.planning/ROADMAP.md` — 01-06 checked off; Phase 1 progress row 6/6, completed 2026-09-06
- `.planning/STATE.md` — position, decision, session continuity updated

## Decisions Made

- **Reload phrasing:** future docs/instructions use "restart PyMOL OR re-add the plugin directory in Plugin Manager" (restart = simpler, equally valid) — learned from the step-6 confusion in this checkpoint.
- **Research correction style:** PITFALLS.md corrections are appended as dated blockquote notes referencing the research section — original wording preserved for traceability.

## Deviations from Plan

None - plan executed exactly as written. (The step-6 wording note is feedback on instruction phrasing, not a plan deviation; no code changes were needed.)

## Issues Encountered

- Step 6 of the human-verify instructions ("Plugin-Manager reload: re-select the plugin directory (or restart PyMOL)") read ambiguously to the user; resolved by using the restart path, which passed. Recorded above as a doc-phrasing lesson for future phases. No product code affected.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **Phase 1 is complete: 6/6 plans executed** (01-01..01-06). All Phase 1 success criteria are now TRUE: 1–3 human-verified (this checkpoint), 4–5 machine-verified (Task 2 gate run).
- The environment contract every later phase inherits lives in `AGENTS.md` — gate commands, plugin-path safety, module identity, modeless rule, purity classes.
- Open items carried forward (from STATE.md): demo-data approval track must start in Phase 2 (gates Phase 8); Phase 4 input spike (up/down keys); Phase 6 QProcess-in-conda calibration; do NOT revisit Qt-offscreen dialog spikes (01-05 dead end).
- Ready for the orchestrator's phase-verification step, then `/gsd-plan-phase 2`.

---
*Phase: 01-plugin-skeleton-purity-harness*
*Completed: 2026-09-06*
