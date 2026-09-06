# Roadmap: serpentrum

**Created:** 2026-09-06
**Depth:** comprehensive (8 phases)
**Coverage:** 44/44 v1 requirements mapped — 0 unmapped, 0 duplicated (count corrected from 41; see Coverage note)

## Overview

A PyMOL plugin game: steer a molecular head around a bounded box, stack real small molecules onto the snake at cited noncovalent geometry, then compute and explore the assembled snake's IR spectrum via xtb — all end-to-end inside PyMOL 2.5.0 (Windows), developed from a WSL shell. The build order follows the researched dependency sequence (ARCHITECTURE.md's A–H with PITFALLS.md's pitfall→phase mapping folded in; research phase letters kept in parentheses so PITFALLS.md's mapping stays resolvable): traps that are expensive to retrofit (module identity, purity gates, modeless discipline) land first; the empirically de-risked xtb pipeline (`--ohess`, committed fixtures) runs as a parallel track; demo data ships only after citation pinning and explicit human approval.

**Core value:** Playing snake by stacking real molecules with known stacking geometry, then seeing the IR spectrum of the molecule you assembled, computed end-to-end inside PyMOL via xtb.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

- [x] **Phase 1: Plugin Skeleton & Purity Harness** - Installable plugin, single-instance modeless 3-tab dialog, purity/test harness built in from commit one *(research A)*
- [ ] **Phase 2: Pure Core — Game & Chemistry Logic** - All game/chemistry rules as stdlib-only WSL-tested modules; spectra parser fixture-first; demo-data approval track starts *(research B)*
- [ ] **Phase 3: Molecules in the Viewer & Setup Tab** - Configure a game in the Setup tab; box + head molecule materialize in the viewer; uploads gated *(research C)*
- [ ] **Phase 4: Game Loop & Input** - Arrow-key steered movement on a 2D locked-camera plane with countdown, HUD, pause/restart *(research D — input spike)*
- [ ] **Phase 5: Stacking & Game Rules Complete** - Pickups stack at cited geometry; rigid-pivot turns; collisions end runs; win/crash both reach spectra *(research E)*
- [ ] **Phase 6: xtb Pipeline** - Async cancellable `xtb --ohess` with verified success contract and calibrated atom-budget guard *(research F — parallel track)*
- [ ] **Phase 7: Spectra UI** - Broadened IR plot, clickable frequency table → static mode vectors, streaming log, saveable plot *(research G)*
- [ ] **Phase 8: Demo Data, Docs & Release Audit** - Human-approved Set A + attribution, 6-button setup persistence, help/docs, end-to-end audit *(research H)*

## Phase Details

### Phase 1: Plugin Skeleton & Purity Harness *(research phase A)*

**Goal**: The plugin installs into real PyMOL and opens a stable, single-instance, modeless 3-tab dialog — with the purity gates and test harness every later phase must pass, built in from commit one.
**Depends on**: Nothing (first phase)
**Requirements**: SETUP-01, INFRA-01, INFRA-02, INFRA-03, INFRA-05, INFRA-06
**Success Criteria** (what must be TRUE):
  1. User can install via plugin path (or Plugin Manager) and click a single "serpentrum" menu item that opens the 3-tab dialog (Setup / Game / Spectra). [SETUP-01]
  2. Opening the menu item twice, or reloading via Plugin Manager, still yields exactly one dialog with live controls — no duplicate controllers (live state anchored outside module globals). [INFRA-03]
  3. The dialog is modeless: PyMOL's viewer and command line stay responsive while it is open. [INFRA-05]
  4. The WSL python3.6 gate runs green: all modules py_compile under 3.6, pure modules import stdlib only (grep gate), Qt only via `pymol.Qt`. [INFRA-02, INFRA-06]
  5. The environment contract holds: a headless Windows PyMOL smoke via cmd.exe exercises the plugin, the WSL python3.6 suite runs, and Windows xtb is invocable from WSL with path conversion. [INFRA-01]
**Plans**: 6 plans (4 waves)

Plans:
- [x] 01-01-PLAN.md — Plugin package skeleton: anchored single-instance entry point + zero-stub import test (Wave 1)
- [x] 01-02-PLAN.md — 3-tab modeless dialog shell, Setup / Game / Spectra placeholders (Wave 2, parallel)
- [x] 01-03-PLAN.md — Purity gate: AST checker + run_gates runner (syntax walk, plugin-path safety, scoped unittest, --smoke) (Wave 2, parallel)
- [x] 01-04-PLAN.md — Headless Windows PyMOL skeleton smoke: loader namespace, anchor reload/double-import, flushed sentinels (Wave 2, parallel)
- [x] 01-05-PLAN.md — Offscreen dialog smoke + xtb probe gate (--xtb) + WSL→Windows path-conversion helper (Wave 3)
- [x] 01-06-PLAN.md — AGENTS.md gate docs + full gate run + human-verify checkpoint: install, single instance, modeless (Wave 4)

Notes: Avoids the expensive-to-retrofit traps — module identity double-singleton (Pitfall 5), dialog lifetime (7), modeless freeze pattern (2), epoch guards (9). Human-verify: plugin loads via plugin path; exactly one dialog.

### Phase 2: Pure Core — Game & Chemistry Logic *(research phase B)*

**Goal**: Every game and chemistry rule exists as a stdlib-only pure module, unit-tested on WSL python3.6 with zero stubs — spectra parsing driven by the committed real xtb fixtures (`.planning/research/xtb-spike-fixtures/`), and the human demo-data approval track started.
**Depends on**: Phase 1
**Requirements**: STACK-02 (this phase also builds the pure halves of later phases' requirements — flagged per criterion below)
**Success Criteria** (what must be TRUE):
  1. Stacking is data-driven: interaction mode + distance + citation load from a validated data file, never code constants; unit tests prove the placement math reproduces the file's stored geometry. [STACK-02]
  2. The spectra parser, run against the committed real xtb fixtures (phenol, CO₂, π-stacked dimer), extracts frequencies, IR intensities and mode vectors — negatives and zero-intensity modes included — and fails loudly on the corrupt fixture. (Pure half of SPECTRA-03/05; user-facing in Phase 7.)
  3. The xtb success contract (exit 0 + "normal termination" on stderr + expected output files) and `xtb`/`xtb.exe` detection are unit-tested pure functions. (Pure half of SPECTRA-02 / SETUP-05.)
  4. The full python3.6 unittest suite passes on WSL with zero sys.modules stubs and stdlib-only pure modules. [holds the INFRA-02 discipline]
**Plans**: TBD (expected 3–4; module groups are independent and parallelizable: engine+stacking+xyzio ∥ spectra parser+fixtures ∥ xtbenv+setup_logic+molecule_data)

Notes: Fixtures-first rule (Pitfalls 1/12); success contract as a pure function (Pitfall 3). **Parallel human track starts here:** pin π-stack distances from Janiak 2000 full text or COD CIFs → explicit human approval (DATA-02) — longest non-code lead time; gates Phase 8.

### Phase 3: Molecules in the Viewer & Setup Tab *(research phase C)*

**Goal**: The user can configure a game in the Setup tab — demo set or upload, box preset, head molecule, xtb path, win cap — and see the box and chosen head molecule materialize in the viewer, with unsafe uploads rejected at the load-time gate.
**Depends on**: Phases 1, 2
**Requirements**: SETUP-02, SETUP-03, SETUP-04, SETUP-05, SETUP-06, DATA-03, INFRA-04
**Success Criteria** (what must be TRUE):
  1. User can choose Demo Set A from the dropdown (or upload an SDF/mol2 set) and its molecules load into the scene; uploads exceeding 3 rings are rejected with a clear reason. [SETUP-02, DATA-03]
  2. User can pick a preset box size and see a clearly visible boundary box, and the selected head molecule (default: Random) appears in the viewer. [SETUP-03, SETUP-04]
  3. User can leave xtb path/env on auto-detect (handling both `xtb` and `xtb.exe`) or set a manual path that overrides detection. [SETUP-05]
  4. The win cap defaults to the safe budget (~10 molecules / ~100 atoms) and shows the hessian-cost (~N³) warning when raised beyond it. [SETUP-06]
  5. "Cleanup model" removes only game-generated `srp_*` objects (user molecules untouched) and still works in a fresh process after a session save/reload. [INFRA-04]
**Plans**: TBD (expected 3; bridge/loader + validation gate, box/camera/cleanup, and setup-tab UI are separable — parallelizable with explicit file boundaries)

Notes: Avoids molecule-hygiene traps (Pitfall 11) and cleanup semantics (8). Human-verify: uploaded set loads; box renders.

### Phase 4: Game Loop & Input *(research phase D — research flag)*

**Goal**: The snake moves under arrow-key control on a 2D locked-camera plane with countdown, HUD, pause and restart — the first playable (if not yet stackable) motion.
**Depends on**: Phases 2, 3
**Requirements**: GAME-01, GAME-02, GAME-03, GAME-07, GAME-08
**Success Criteria** (what must be TRUE):
  1. User clicks Start, the dialog switches to the Game tab, counts down 3-2-1, then the head moves forward continuously without stopping. [GAME-01]
  2. User can steer with all four arrow keys (up/down spike resolved with the designed fallback if needed); movement never stops. [GAME-03]
  3. Play happens on a 2D plane with a locked camera, and the boundary box stays clearly visible throughout. [GAME-02]
  4. User sees the rolling info box, elapsed timer and molecules-remaining, and pause/resume + restart work mid-run. [GAME-07]
  5. Speed is constant regardless of snake length. [GAME-08]
**Plans**: TBD (expected 3; the input spike should precede/steer HUD wiring — loop+countdown can be a parallel plan once the spike lands)

Notes: **Spike scheduled here (the one open mechanism question):** up/down `set_key` bindability + Wizard event-mask behavior + focus stealing; fallback = Qt application-level event filter (verified design). First human-verify of keys happens here so failure is cheap. Avoids Pitfalls 4, 5 (pause semantics), 9. Pickup stick rendering arrives with pickups in Phase 5.

### Phase 5: Stacking & Game Rules Complete *(research phase E)*

**Goal**: The complete v1 game: pickups stack onto the chain at cited geometry, turns pivot the whole chain rigidly, collisions end runs, and both wins and crashes hand a complete snake to the spectra stage.
**Depends on**: Phase 4
**Requirements**: GAME-04, GAME-05, GAME-06, GAME-09, GAME-10, STACK-01, STACK-03, STACK-04, STACK-05
**Success Criteria** (what must be TRUE):
  1. User picks up a molecule and it appends at the dataset-stored stacking geometry — the placed distance equals the cited value — with molecule/atom counts tracked, and the info box shows interaction name, distance, one-line explanation and citation. [GAME-04, STACK-01, STACK-04; dataset from STACK-02]
  2. A turn sweeps the entire chain as a rigid body; a sweep that would hit the boundary or body is refused; 180° reversal is impossible. [GAME-10]
  3. Hitting the boundary or the snake's own body (segment-based) ends the run but leaves the snake complete; the player wins when length exceeds the cap. [GAME-05, GAME-06]
  4. On completion (win or crash): the viewer clears, the camera focuses the completed snake, length + score (molecule count) display, and "Get Spectra" activates. [GAME-09]
  5. Pickups without a verified dataset entry are skipped with the reason in the info box, and the clash gate rejects placements that would collide. [STACK-03, STACK-05]
**Plans**: TBD (expected 3–4; stacking transforms+clash gate ∥ turn+collision+scoring rules ∥ completion flow — separable around the shared engine)

Notes: The clash gate is a game rule, not a spectra afterthought (a clashing append makes xtb infer covalent bonds → garbage hessian; π-stack at 3.4 Å verified safe `[RUN]`). Verify during implementation: `transform_selection` matrix layout (read `editing.py:1946` docstring; fallback = `cmd.rotate`+`cmd.translate`). Avoids Pitfalls 9, 10, 4-restore, 11-aggregation.

### Phase 6: xtb Pipeline *(research phase F — parallel track, largely de-risked)*

**Goal**: The final snake can be handed to a real, cancellable, async `xtb --ohess` run with a verified success contract and a calibrated atom-budget guard — while the UI never blocks.
**Depends on**: Phase 2 only — **run in parallel with Phases 3–5** (F∥D/E from research); merge before Phase 7
**Requirements**: SPECTRA-02, SPECTRA-06
**Success Criteria** (what must be TRUE):
  1. User launches a spectra run and `xtb --ohess` starts on the final snake in a fresh per-run temp dir, asynchronously — dialog and viewer stay responsive during the run. [SPECTRA-02]
  2. User can cancel a running calculation, and a new run can start after cancel or completion (no double-runs). [SPECTRA-02]
  3. Success is declared only on the verified contract (exit 0 + "normal termination" + expected output files); corrupted input surfaces a clear failure, never a fake success. [SPECTRA-02]
  4. Before launch, the hidden molecule/atom counts are re-checked against the configured cap; exceeding it shows a warning. [SPECTRA-06]
  5. A capped ~100-atom snake completes `--ohess` headless with measured wall time; warning threshold and OMP environment calibrated from the measurement. [SPECTRA-06]
**Plans**: TBD (expected 2–3; the QProcess-in-conda smoke gates the runner plan — atom-guard + calibration can run as parallel plans once the smoke lands)

Notes: PyMOL-free; the only gameplay touchpoint is the final-snake xyz handoff. Smoke first: QProcess in the Windows conda PyMOL build (one-line smoke); fallback = worker+queue+QTimer drain (verified pattern). Avoids Pitfalls 1, 2, 3, 6, 11-assert, 12-fixtures. `[TRAIN]` items (OMP env) verified here.

### Phase 7: Spectra UI *(research phase G)*

**Goal**: The payoff screen: a broadened IR spectrum of the player's own snake, a clickable frequency table that draws mode vectors in 3D, live progress and a saveable plot.
**Depends on**: Phases 5, 6
**Requirements**: SPECTRA-01, SPECTRA-03, SPECTRA-04, SPECTRA-05
**Success Criteria** (what must be TRUE):
  1. User clicks "Get Spectra", the dialog switches to the Spectra tab, and the calculation's progress streams live into the log panel. [SPECTRA-01, SPECTRA-04]
  2. User sees a Gaussian-broadened IR spectrum with axis labels and adjustable size, and Save Plot writes a PNG viewable outside PyMOL. [SPECTRA-03]
  3. The frequency table lists every mode (negatives shown as imaginary, e.g. −31.9i; zero-intensity included), and clicking a row draws that mode's static displacement vectors on the snake in the viewer. [SPECTRA-05]
**Plans**: TBD (expected 3; plot widget ∥ table+vectors ∥ log/save are independent UI pieces — parallelizable)

Notes: Pure parser already tested in Phase 2; UI is wiring plus the two verified QPainter precedents (`dynoplot.py`, `pmg_qt/volume.py`). Human-verify: plot-to-PNG save (`QWidget.grab()` unverified in PyMOL's Qt build; fallback QPainter→QImage). Avoids Pitfalls 12 (table↔vector index match), 2 (streaming + cancel UX), 5.

### Phase 8: Demo Data, Docs & Release Audit *(research phase H)*

**Goal**: The shippable release: human-approved demo data with verified attribution, educator-shareable setup persistence, complete help and docs, and an end-to-end audit proving every v1 requirement.
**Depends on**: Phases 5, 6, 7 + the human-approval track (running since Phase 2)
**Requirements**: DATA-01, DATA-02, DATA-04, SETUP-07, SETUP-08, DOCS-01, DOCS-02, DOCS-03, DOCS-04, DOCS-05
**Success Criteria** (what must be TRUE):
  1. Demo Set A ships with CID-cited PubChem 3D SDFs; every stacking distance pinned from a verified source and explicitly human-approved; DATA_SOURCES.md documents source DB, ID, DOI and license per molecule; no CSD/CCDC data redistributed. [DATA-01, DATA-02, DATA-04, DOCS-02]
  2. All six bottom-row buttons work (Reset, Randomize, Save Setup, Load Setup, Cleanup model, Start), and Save Setup → Load Setup on a fresh install reproduces the exact game configuration. [SETUP-07, SETUP-08]
  3. README documents install, usage and the demo set with the vibe-coding warning block intact (and the leftover "sECDpent" name fixed), and the doc-vs-code audit passes — README steps reproduce; help text matches real controls and dataset values. [DOCS-01, DOCS-04]
  4. In-game help covers controls, the "click the 3D viewer" focus hint, what negative frequencies mean, and a next-action hint on every screen. [DOCS-03]
  5. End-to-end release audit: the full flow (setup → play → complete → xtb → IR plot → save) passes headless with human checkpoints, and all v1 requirements are checked off with complete traceability. [DOCS-05]
**Plans**: TBD (expected 3–5; data pack (gated on approvals) ∥ persistence+buttons ∥ help text ∥ docs/audits — parallelizable once their inputs exist)

Notes: Data ships only after citation pinning + human approval (repo hard rule — no fabrication). Avoids Pitfalls 8 (.pse desync), 4 (leak check), UX table.

## Execution Waves (parallelization: true)

Dependency-driven waves:

```
Wave 1:  Phase 1                              (skeleton + harness)
Wave 2:  Phase 2                              (pure core; starts human demo-data approval track)
Wave 3:  Phase 3 → Phase 4 → Phase 5          (sequential chain)
         ∥ Phase 6                             (xtb pipeline — depends only on Phase 2)
Wave 4:  Phase 7                              (needs Phase 5 + 6)
Wave 5:  Phase 8                              (needs Phases 5–7 + approvals resolved)
```

- **F∥D/E parallelism (from research):** Phase 6 is PyMOL-free and depends only on Phase 2 — schedule its plans concurrently with the Phase 3→4→5 chain. The only gameplay touchpoint is the final-snake xyz handoff.
- **Worktree protocol:** whenever a wave runs ≥2 plans in parallel (e.g., Phase 6 alongside Phase 3/4/5 plans), each plan commits in its own worktree/branch per AGENTS.md, merged back in dependency order.
- **Human track:** demo-set data prep (pin π-stack distances from Janiak 2000 full text or COD CIFs → human approval) starts at Phase 2 and gates Phase 8 — the longest non-code lead time; blocked on human decisions, not code research.
- **Research flags for planning:** Phase 4 (input spike — up/down keys), Phase 6 (calibration only), Phase 5 (`transform_selection` matrix convention; fallback verified).

## Coverage

| Category | Requirements | Phases |
|----------|--------------|--------|
| Setup & Configuration | SETUP-01..08 | 1, 3, 8 |
| Gameplay | GAME-01..10 | 4, 5 |
| Molecular Stacking | STACK-01..05 | 2, 5 |
| Spectra | SPECTRA-01..06 | 6, 7 |
| Demo Data & Attribution | DATA-01..04 | 3, 8 |
| Infrastructure & Environment | INFRA-01..06 | 1, 3 |
| Documentation & Audit | DOCS-01..05 | 8 |

**Total: 44/44 v1 requirements mapped — 0 unmapped, 0 duplicated.**

> **Count note:** REQUIREMENTS.md previously said "41 total"; the listed ID ranges (SETUP-01..08, GAME-01..10, STACK-01..05, SPECTRA-01..06, DATA-01..04, INFRA-01..06, DOCS-01..05) sum to **44**. All 44 are mapped exactly once; REQUIREMENTS.md's Coverage block is corrected accordingly.

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8
(Phase 6 runs in parallel with Phases 3–5 — see Execution Waves.)

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Plugin Skeleton & Purity Harness | 6/6 | Complete (verified 5/5 must-haves) | 2026-09-06 |
| 2. Pure Core — Game & Chemistry Logic | 0/TBD | Not started | - |
| 3. Molecules in the Viewer & Setup Tab | 0/TBD | Not started | - |
| 4. Game Loop & Input | 0/TBD | Not started | - |
| 5. Stacking & Game Rules Complete | 0/TBD | Not started | - |
| 6. xtb Pipeline | 0/TBD | Not started | - |
| 7. Spectra UI | 0/TBD | Not started | - |
| 8. Demo Data, Docs & Release Audit | 0/TBD | Not started | - |
