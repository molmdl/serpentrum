---
phase: 06-xtb-pipeline
plan: 12
subsystem: infra
tags: [xtb, qprocess, gates, human-checkpoint, phase-close]

# Dependency graph
requires:
  - phase: 06-xtb-pipeline (plans 06-01..06-11)
    provides: the complete launch/cancel/relaunch pipeline — budget_guard, xtb_run state machine, XtbRunController, launch pipeline, spectra placeholder tab, calibration-applied literals
  - phase: 05.2 (plan 5.2-09)
    provides: shared-file ordering for setup_logic/gui edits; the blocking human-verify checkpoint model (numbered steps, per-step EXPECT, verdict table)
provides:
  - "final gate verdicts on the completed phase tree (default + --smoke + --xtb) plus the re-verified post-directive legs"
  - "the ONE blocking live human-verify checkpoint of the pipeline in real Windows PyMOL — APPROVED 12/12 with ONE amendment (EQ-artifact-1 dir contract)"
  - "EQ decisions record for Phase 6 + Phase-7 handoff notes (spectra_run keys, artifact dir contract, runner signal vocabulary, deferred UI scope)"
affects: [07-spectra, phase wrap-up, REQUIREMENTS close-out]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Phase-closing gate triplet: default + --smoke + --xtb legs recorded verbatim before the blocking checkpoint; post-amendment legs re-run and recorded beside them"
    - "5.2-09 checkpoint model reused: per-step EXPECT lines referencing symbols, verdict table, per-item approvals accumulate"
    - "Env-over-CWD constants for user-settable dirs (SRP_SPECTRA_DIR || <cwd>/srp_spectra) — no schema churn for a path preference (research Q7 precedent)"

key-files:
  created:
    - .planning/phases/06-xtb-pipeline/06-12-SUMMARY.md
  modified:
    - serpentrum/xtb_runner.py
    - smoke/11_xtb_runner_smoke.py
    - .gitignore

key-decisions:
  - "EQ-smoke-1: smokes 09/11 stay INFORMATIONAL by default (depend on the local xtb.exe fallback list); REQUIRED promotion only on explicit owner instruction — owner instructed NONE at 06-12"
  - "EQ-checkpoint-1: the live checkpoint covers the pipeline + placeholder affordances; Spectra PLOT/TABLE/LOG-PANEL verdicts DEFERRED to Phase 7"
  - "EQ-artifact-1 (owner directive, 06-12): stable spectra artifacts dir is USER-SETTABLE via SRP_SPECTRA_DIR with default <cwd>/srp_spectra (was %TEMP%/srp_spectra); spray dir stays in %TEMP% — scratch stays scratch"

patterns-established:
  - "Phase close = gates task + ONE blocking checkpoint + conditional fix/finalize task; SUMMARY drafted at gates, finalized at owner approval"

# Metrics
duration: ~25 min (Task 1 gates ~5 min + owner checkpoint playtime out-of-band + Task 3 amendment/re-run/finalize)
completed: 2026-09-26
---

# Phase 6 Plan 12: Phase-Close Gates + Checkpoint Summary

**Full gate suite green on the completed Phase-6 tree (796 unittests, 8/8 required smokes, Windows xtb probe PASS) and the blocking live pipeline checkpoint APPROVED 12/12 in real Windows PyMOL — with ONE owner amendment landed and re-verified: the spectra artifacts dir is now user-settable (SRP_SPECTRA_DIR env, default `<cwd>/srp_spectra`, off %TEMP%); Phase 6 CLOSED**

## Performance

- **Duration:** ~25 min agent-side (owner checkpoint playtime out-of-band between Tasks 1 and 3)
- **Started:** 2026-09-26T16:33:34Z
- **Completed:** 2026-09-26T16:57Z
- **Tasks:** 3 of 3 (Task 1 gates; Task 2 BLOCKING human-verify — APPROVED; Task 3 amendment + finalize)
- **Files modified:** 4 (xtb_runner.py, smoke 11, .gitignore, this SUMMARY)

## Task-1 Gate Results (recorded 2026-09-26T16:33-16:45Z, pre-checkpoint tree)

### Leg 1: `python3.6 tests/run_gates.py` — GREEN
- **796 tests ran, OK** (3.101 s); gates 1-3 PASS; `run_gates: all gates green`
- **Count delta:** 796 vs the **785** phase-entry baseline (06-11-SUMMARY: 786 = 785 + 1 DEFAULT_THREAD_ARG pin; the merged 06-10 10-scenario `test_phase6_integration.py` suite contributes the other 10) → **+11 vs 785**. Longer-horizon anchor: 755 at Phase-6 entry (06-03-SUMMARY) → **+41 across the phase**.

### Leg 2: `python3.6 tests/run_gates.py --smoke` — GREEN
- REQUIRED smokes **8/8 PASS** via flushed SMOKE-OK sentinels: 01 SKELETON, 03 VIEWER-BRIDGE, 04 VIEWER-DEMO, 05 LOOP-CAMERA, 06 INPUT-WIZARD, 07 TRANSFORM, 08 EDGEON, 10 CHAIN-COUNT (the new chain-count smoke).
- Informational: 02_dialog FAIL (non-blocking — the KNOWN 01-05 dead end), 09_qprocess PASS, 11_xtb_runner PASS.

### Leg 3: `python3.6 tests/run_gates.py --xtb` — GREEN
- `xtb gate: * xtb version 6.7.1pre (5071a88) compiled by 'Marcel@Raven' on 2024-07-23 (rc=0)`; `xtb gate: normal termination of xtb`.

**Zero fixes needed — the merged phase tree (waves 1-3) was gate-green across all three legs on first run.**

## Task-3 Re-verification (post-amendment tree, 2026-09-26T16:50-16:57Z)

After the owner-directed artifact-dir amendment (048d929):

- `python3.6 tests/run_gates.py` — GREEN: **796 tests ran, OK** (3.030 s); gates 1-3 PASS.
- Direct smoke 11 (real xtb runs): `timeout 300 cmd.exe /c "C:\src\run-conda-pymol.bat -cq smoke\11_xtb_runner_smoke.py"` → **`SMOKE-OK XTB-RUNNER`**, all 8 steps: `PROBE ARUN elapsed_ms: 78 status: ok problems: []`, `PROBE SPRAY leftover: []`, restart-after-completion True, tick-at-`running` proof, `PROBE CANCEL ... status: cancelled`, after-cancel restart `ok`, no-double-run guard refused with the 'already active' line, bad-exe path `failed` (never raised). Stable-dir assertions ran against the env-overridden STABLE_ROOT (all 5 artifacts present on success; snake.xyz+xtb.log only on cancel — no fake success).
- `python3.6 tests/run_gates.py --smoke` — GREEN: 796 tests OK; required smokes 8/8 PASS; informational: 02 FAIL (known dead end, non-blocking), 09 PASS, **11 PASS (informational)**.
- No `./srp_spectra` left in the repo root (smoke overrides the env; the CWD default is gitignored anyway).

## Task 2: CHECKPOINT — live pipeline feel-check verdict (owner, real Windows PyMOL 2.5.0, cap-3 game to a win)

**Verdict: APPROVED — 12/12 PASS, with ONE directive (amendment) applied in Task 3.**

| Step | Covers | Verdict | Owner evidence |
|------|--------|---------|----------------|
| 1. Launch preconditions (refuse without a completed snake) | SC-pipeline | **PASS** | Live log: the refuse-precondition line fired; nothing started; no crash |
| 2. Play + complete | SC-pipeline | **PASS** | Completion lines verbatim from the live log: `YOU WIN` / `score: 3 molecule(s) stacked` / `snake: 4 molecules (incl. head)` / `atoms: 54 (spectra input size)`; Get Spectra activated |
| 3. Launch: counts line + async start (SC1+SC4) | SC1, SC4 | **PASS** | Live log: `spectra input: 4 molecules (incl. head), 66 atoms (budget 100)` followed by `xtb running... (async - the dialog stays responsive)`; log lines streamed |
| 4. Responsiveness during the run (SC1) | SC1 | **PASS** | Owner's own words: "xtb real-time log responsive yes" — viewer rotation/menus/HUD stayed live during the run |
| 5. Cancel mid-run (SC2) | SC2 | **PASS** | Cancel produced the HONEST failure text — `xtb finished: cancelled - exit code 62097 != 0; stderr lacks 'normal termination' (got: ''); missing expected output file(s): g98.out, vibspectrum` — never a fake 'ok' |
| 6. Relaunch after cancel (SC2) | SC2 | **PASS** | 'Run again' started a fresh run; completion `xtb finished: ok`; no stuck state |
| 7. No double-run (SC2) | SC2 | **PASS** | Guard line + exactly one active run (owner confirmed via the single status stream) |
| 8. Completion + artifacts (SC3) | SC3 | **PASS** | `xtb finished: ok`; the owner MOVED the run's artifacts into the repo-local `tmp/srp_spectra/run_2/` for evidence — listing below shows all five files; no leftover spray dir |
| 9. Failure paths (SC3) | SC3 | **PASS** | Owner: step 9 "pass" — clear failure lines on the bad/missing-binary path; cancelled/failed runs NEVER displayed success wording (see step-5 literal) |
| 10. Head-inclusive proof (SC4) | SC4 | **PASS (by log arithmetic)** | HUD `atoms: 54` (head-excluded) + benzene head `atom_count` 12 = **66** = the counts line's `M`. The head-exclusion trap is visibly absent (54+12=66) |
| 11. Calibration wording (SC5) | SC5 | **PASS-by-pin** | No over-budget warning fired (66 <= 100 — correct suppression); the 06-11 amended literal is unit-pinned and renders via the same status path proven live. Owner-noted-and-amendable literal: "hessian cost scales ~N^3; a ~100-atom snake takes about 1-2 min on a typical 4-core/8-thread laptop (measured 84-101 s; thread-capped runs slower, up to ~5 min single-threaded)" |
| 12. Deferred scope | EQ-checkpoint-1 | **PASS** | Spectra tab showed ONLY the temporary status/log/cancel affordances; plot/table/log-panel UX explicitly accepted as Phase 7 scope |

### Step-8 artifact evidence (owner-staged `tmp/srp_spectra/run_2/`, gitignored)

```
-rwxrwxrwx 1 ... 381967 ... g98.out
-rwxrwxrwx 1 ...   3460 ... snake.xyz
-rwxrwxrwx 1 ...  12611 ... vibspectrum
-rwxrwxrwx 1 ...  33389 ... xtb.log
-rwxrwxrwx 1 ...   5291 ... xtbopt.xyz
```

All five contract files present from the owner's real win-to-`ok` run.

### Owner directive (the one amendment — applied as Task 3's fix)

> Spectra artifacts dir must be USER-SETTABLE with default `srp_spectra` under CWD (was %TEMP%).

Resolution (048d929, constants/env over schema churn per research Q7):

- `serpentrum/xtb_runner.py`: new `_stable_base()` resolver — `os.environ.get('SRP_SPECTRA_DIR') or os.path.join(os.getcwd(), 'srp_spectra')` (documented in the docstring: default under CWD; env override = the user seam). The snake_id subdir, keep-until-replaced policy, and rmtree prefix guard are UNCHANGED — the guard now checks the new base prefix consistently in BOTH `start()` (`_drop_prior_stable_dir`) and `_on_finished` (copy-out). The SPRAY dir (`xtbenv.new_run_dir(base_dir)`) stays in `tempfile.gettempdir()` — scratch stays scratch.
- `serpentrum/gui.py` `_launch_spectra_run`: VERIFIED no change needed (its `base_dir` feeds only the spray dir).
- `.gitignore`: `srp_spectra/` added (a user running PyMOL with the repo root as cwd must not pollute the tree).
- `smoke/11_xtb_runner_smoke.py`: sets `SRP_SPECTRA_DIR` to a fresh `mkdtemp` before any run step (repo stays clean regardless of PyMOL's cwd) and asserts artifacts under it; `%TEMP%/srp_spectra` expectations retired; informational disposition recorded (EQ-smoke-1, no promotion instructed).
- Re-verified green (see Task-3 Re-verification above).

**Old → new stable-dir resolution (exact change):**
```python
# OLD (both in _drop_prior_stable_dir and _on_finished):
os.path.join(tempfile.gettempdir(), 'srp_spectra', ...)
# NEW (single resolver used in both places):
os.path.join(_stable_base(), ...)   # _stable_base() =
    # os.environ.get('SRP_SPECTRA_DIR') or os.path.join(os.getcwd(), 'srp_spectra')
```

## SC5 cross-check (no live step — verified by artifacts)

- **06-CALIBRATION.md (06-07):** 104-atom `--ohess` wall 84-101 s uncapped / -P 4 on the calibration machine; QProcess user-perceived 91.4-107.6 s; OMP_STACKSIZE dispositioned NOT NEEDED (no uncapped run crashed); atom_budget STAYS 100.
- **06-11-SUMMARY.md:** HESSIAN_WARNING literal carries the measured numbers; DEFAULT_THREAD_ARG = ('-P','4') shipped; '30-90' audit shows only superseded-value citations.

## EQ Decisions Record (Phase 6, final dispositions)

- **EQ-xyz-1 (engine-xyz handoff):** game completion ANCHORS `snake_xyz` text on the run record; Get Spectra consumes the anchored text — no re-serialization at launch, no viewer round-trip.
- **EQ-guard-1 (budget-guard module placement):** `budget_guard` lives PURE (no pymol/Qt); the launch pipeline composes it with `chain_atom_counts` + `read_xyz_text` in gui's thin shell.
- **EQ-guard-2 (warning disposition):** budget warnings are LOG-ONLY heads-up lines (never block the run): head-inclusive counts line always, hessian warning line only when over budget — correct suppression proven live (66 <= 100 fired nothing).
- **EQ-desync-1 (desync severity):** a count desync between completion-time and launch-time manifests is surfaced as a clear line and the launch proceeds on the fresh re-check — informational, never a silent stale run.
- **EQ-omp-1 (threading outcome):** **DEFAULT_THREAD_ARG = ('-P','4')** ships as the default cap (06-CALIBRATION measured 84-101 s at -P 4 for a ~100-atom snake; an explicit caller-supplied `extra_args` still wins). OMP_STACKSIZE: NOT NEEDED.
- **EQ-artifact-1 (artifact policy):** copy-out-then-keep-until-replaced: terminal branch copies artifacts into the stable dir and deletes the spray dir; the NEXT start prefix-guarded-removes the prior stable dir. **AMENDED by owner directive at 06-12:** stable base is now `SRP_SPECTRA_DIR` env or `<cwd>/srp_spectra` default (WAS `%TEMP%/srp_spectra`); spray stays in %TEMP%. Committed as 048d929; smoke 11 re-proves the contract under the env override.
- **EQ-binary-1 (binary resolution):** candidate order SRP_XTB_PATH env → `xtbenv.detect_binary(None)` (PATH probes) → the verified `C:\xtb-6.7.1\bin\xtb.exe` fallback, SMOKE-ONLY; a missing binary yields the clear 'xtb not found — set the xtb path on the Setup tab' line, never a crash (proven live, step 9).
- **EQ-smoke-1 (smoke promotion):** smokes 09/11 stay INFORMATIONAL by default (they depend on the local xtb.exe fallback list); REQUIRED promotion only on explicit owner instruction — **at 06-12 the owner instructed NO promotion**; smoke 11's docstring now records this.
- **EQ-ux-1 / EQ-ux-2 (placeholder affordances):** the Spectra tab ships a TEMPORARY status label + streaming log area (both line-capped) plus a Cancel/Run-again button and the game-tab info box carrying the same lines — the full plot/table/log-panel UX is Phase 7.
- **EQ-checkpoint-1 (checkpoint scope):** the 06-12 live checkpoint covers the PIPELINE + placeholder affordances only; Spectra PLOT/TABLE/LOG-PANEL verdicts are explicitly DEFERRED to Phase 7 — owner accepted (step 12 PASS).

## Phase-7 Handoff Notes

- **spectra_run record (frozen shape, `xtb_run.SPECTRA_RUN_KEYS`):** `snake_id`, `status` ('ok'/'failed'/'cancelled'), `problems` (list of strings), `input_path`, `g98_path`, `vibspectrum_path`, `xtbopt_path`, `log_path`. Written ONLY by the controller's terminal branch onto `anchor.spectra_run`. 'ok' implies g98/vibspectrum/xtbopt paths non-None; failed/cancelled may carry None paths — Phase 7 must tolerate them (never fabricate curves/rows from a degenerate record) and must handle deleted files (the dir is user-reachable now).
- **Artifact dir contract (owner-amended at 06-12):** stable root = `SRP_SPECTRA_DIR` env var, default `<cwd>/srp_spectra`; per-run snake_id subdir holds `snake.xyz`, `xtb.log`, `g98.out`, `vibspectrum`, `xtbopt.xyz`; keep-until-replaced (next run's start removes the prior snake's dir, prefix-guarded against the SAME resolved base — note: changing the env var between runs orphans old dirs rather than deleting them; the record's absolute paths are the truth for reads). The spray scratch dir remains `srp_*` in %TEMP% and never survives a terminal branch. Repo-root runs cannot pollute the tree (`srp_spectra/` is gitignored). NOTE: Phase-7 plan docs (07-RESEARCH-spectra-seam, 07-08/07-09) still cite the pre-amendment `%TEMP%/srp_spectra` default — read via the record paths, not a re-derived location.
- **Runner signal vocabulary (connect exactly these):** `started()` on launch; `log_line(str)` per decoded stdout/stderr line (verbatim, CRLF-tolerant); `run_finished(status, problems)` exactly once per terminal branch (including the synchronous FailedToStart path, which emits BEFORE `start()` returns — connect first). Controller API: `start(xyz_text, exe_path, base_dir, snake_id, knobs=None, extra_args=None) -> bool`; `cancel()`; `status()`. Guarded no-double-run returns False with an 'already active' log line.
- **Placeholder widgets are TEMPORARY:** Phase 7 replaces the Spectra page CONTENT (plot/table/log-panel); the launch pipeline + runner-signal contracts + the record shape SURVIVE.
- **Cancel honesty contract:** a killed run reports `cancelled` with the real failure lines (exit code, stderr verdict, missing files) — Phase 7 must never render success affordances for non-'ok' statuses.

## Task Commits

1. **Task 1: Final full-gates pass on the completed phase tree** — `a341119` (docs)
2. **Task 2: CHECKPOINT — live pipeline feel-check** — owner verdict returned out-of-band (no commit; approvals recorded here)
3. **Task 3a: Owner directive applied (artifacts dir user-settable)** — `048d929` (fix)
4. **Task 3b: Phase close-out SUMMARY finalized** — `(this commit)` (docs)

## Deviations from Plan

### Owner-directed amendment (sanctioned by the checkpoint verdict)

**1. [Owner directive — EQ-artifact-1 amendment] Stable artifacts dir moved off %TEMP%; user-settable with CWD default**
- **Found during:** Task 2 checkpoint verdict (owner: "spectra artifacts dir must be USER-SETTABLE with default 'srp_spectra' under CWD")
- **Fix:** `_stable_base()` resolver (env `SRP_SPECTRA_DIR` → `<cwd>/srp_spectra`); guard prefix updated in both use sites; `.gitignore` entry; smoke 11 pins the env override and asserts under it; gui verified unchanged
- **Files modified:** `serpentrum/xtb_runner.py`, `.gitignore`, `smoke/11_xtb_runner_smoke.py`
- **Verification:** default gates green (796 tests); direct smoke 11 run `SMOKE-OK XTB-RUNNER` (all 8 steps, artifacts asserted under the env dir); `--smoke` battery green
- **Committed in:** `048d929`

No rule-1/2/3 auto-fixes were needed — the tree was gate-green on first run and the checkpoint reported zero defects.

**Total deviations:** 1 (owner-directed amendment, sanction recorded with the checkpoint verdict).
**Impact on plan:** Minimal-surface change (one resolver + two call-site prefixes + test/gitignore); no schema churn; spray/scratch behavior untouched.

## Issues Encountered

None. Task 1 needed zero fixes; the checkpoint produced zero defect reports (only the one directive above).

## Authentication Gates

None.

## User Setup Required

None - no external service configuration required. (`SRP_SPECTRA_DIR` is an OPTIONAL user seam; the CWD default works out of the box and is documented in xtbrunner's `_stable_base` docstring.)

## Next Phase Readiness

- **Phase 6 CLOSED** — gates green on the final tree, checkpoint APPROVED 12/12, every EQ decision recorded with its final disposition, the artifact-dir amendment landed and re-verified.
- **Phase 7 (spectra presenter)** inherits: the frozen `spectra_run` contract + signal vocabulary + the NEW artifact dir contract (env/default documented above), with the explicit license to replace the placeholder page content. The plot/table/log-panel UX verdicts are Phase 7's checkpoint (EQ-checkpoint-1), accepted by the owner at step 12.

---
*Phase: 06-xtb-pipeline*
*Completed: 2026-09-26*
