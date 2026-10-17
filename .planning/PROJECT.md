# serpentrum

## What This Is

A PyMOL 2.5.0 plugin implementing an educational molecular snake game — **shipped as v1 (2026-10-18)**. The player steers a molecular head around a bounded box on a 2D locked-camera plane to pick up small molecules that stack onto the snake at cited, human-approved π-stack geometry (3.60 Å @ 20°); accumulating random line-wall obstacles and owner-tuned speed tiers keep navigation challenging; on win or crash the completed snake goes to a real, async `xtb --ohess` calculation whose broadened IR spectrum is plotted, explored via a clickable frequency table with static vibrational-mode vectors, and exportable as PNG — end-to-end inside PyMOL. For students and educators who want an engaging way to explore molecular interactions.

## Core Value

Playing snake by stacking real molecules with known stacking geometry, then seeing the IR spectrum of the molecule you assembled, computed end-to-end inside PyMOL via xtb.

## Current State

**Shipped:** v1 — Playable Release (2026-10-18). GATE V owner sign-off 2026-10-10; milestone audit PASSED 2026-10-18 (46/46 requirements, 13/13 phases, 8/8 cross-phase seams, 6/6 E2E flows, zero critical gaps).

- 13 phases, 127 plans, 256 tasks in ~42 days (2026-09-05 → 2026-10-18); 659 commits, 513 files, 104,764 insertions
- ~13.5k LOC shipped plugin core (`serpentrum/`); ~39.5k Python total incl. tests/smokes/tools (106 files)
- Test battery runnable from WSL (`python3.6 tests/run_gates.py`), green at close: 1084 unittests + 12 required headless Windows-PyMOL smokes + `--xtb` real-run gate + docs audit 7/7 + requirements audit 46/46
- 17 owner checkpoint occasions recorded (install pilot, keys pilot, 7-round stacking checkpoint, 5.1/5.2/5.3/9/9.1 feel-checks, 06-12/07-06/07-10 live closes, GATE D, GATE V) — all approved
- Release record + archives: `.planning/MILESTONES.md`, `.planning/milestones/v1-ROADMAP.md`, `v1-REQUIREMENTS.md`, `v1-MILESTONE-AUDIT.md`

## Requirements

### Validated

<!-- Shipped and confirmed valuable. -->

- ✓ All 46 v1 requirements shipped and human-certified — v1 (GATE V 2026-10-10; audit re-attested 2026-10-18). Full per-ID evidence ledger: `milestones/v1-REQUIREMENTS.md`
  - Setup & Configuration: SETUP-01..08 — 3-tab dialog, demo/upload sets (≤3 rings), box presets, head choice, xtb path + thread controls, win cap + budget warning, 6-button row, educator Save/Load round-trip
  - Gameplay: GAME-01..11 — countdown → play, 2D locked camera, arrow-key steering, stacking capture, lethal collisions (boundary/body/accumulated line-walls), win cap, HUD/pause/restart, constant per-run speed, completion flow, owner-amended rigid turns, speed-tier selector
  - Molecular Stacking: STACK-01..06 — cited-geometry placement, data-file dataset, honest skips with reasons, structured HUD content + recap, clash gate, consent-gated generic π-stack for uploads
  - Spectra: SPECTRA-01..06 — tab flow, async cancellable `xtb --ohess` with verified success contract, broadened IR plot + PNG save, streaming log, frequency table → static mode vectors on the optimized structure, pre-launch budget re-check
  - Demo Data & Attribution: DATA-01..04 — Demo Set A (CID-cited PubChem 3D SDFs), human-approved pinned distances, upload gate, DATA_SOURCES.md attribution; no CSD/CCDC redistribution
  - Infrastructure & Environment: INFRA-01..06 — WSL + Windows pipeline, purity gates, anchored single-instance state, `srp_*` viewer hygiene incl. fresh-process, modeless + never-blocking, python3.6 discipline
  - Documentation & Audit: DOCS-01..05 — README (vibe block intact), complete DATA_SOURCES.md, in-game help, doc-vs-code audits, end-to-end release audit

### Active

<!-- Current scope. Building toward these. -->

(None yet — the next milestone's requirements are defined via `/gsd-new-milestone`.)

## Next Milestone Goals

Not yet defined — created via `/gsd-new-milestone` (questioning → research → requirements → roadmap). Candidate backlog on record:

- **Deferred v2 items (from the v1 requirements archive):** additional demo sets (Set B carboxylic-acid H-bond dimers, Set C heteroaromatics, Set D hydroxyl H-bond chains), in-plugin provenance popups, vibrational-mode animation, speed increasing with snake length, 3D free-steering mode, mixed-interaction stacking sets, Raman spectra
- **Owner-flagged small items:** IR intensity plot title fix (2026-10-10, scope undefined until pickup), per-box-preset wall-count cap (9.1-09 feel-check, needs owner GO), edge-biased pickup spawn distribution (5.3-05, sketch on file)

### Out of Scope

- Vibrational-mode animation — deferred with spec; tracked as a v2 candidate
- Raman/UV-Vis/NMR — one spectrum done well in v1; Raman tracked for a future milestone
- Live spectrum preview during gameplay — hessian ~N³ cost kills frame rate and the atom budget
- Physics-based relaxation at pickup time — deterministic cited-geometry placement instead
- Silent stacking fallback for unknown molecules — educational integrity: refuse and explain
- Reproducing real crystal packing (herringbone etc.) — idealized pairwise geometry, labeled as such
- Multiplayer / .io variants — network stack out of classroom scope
- External Python dependencies — only what pymol-open-source ships; additions need a written list, owner approval, and vendoring

## Context

- Produced in the established environment: WSL Ubuntu dev shell (python3.6 tests, no installs); Windows PyMOL 2.5.0 in conda (headless smokes via `cmd.exe`); Windows xtb 6.7.1 invoked from WSL. Operational rules live in root `AGENTS.md` and `pymol/AGENTS.md`.
- All shipped numbers are human-approved: the 3.60 Å @ 20° π-stack geometry is pinned by Janiak 2000's verified qualitative rule plus measured CC0 COD organics; molecule SDFs are CID-cited PubChem 3D; DATA_SOURCES.md documents source DB, ID, DOI, license per molecule. On-record caveat: Janiak's corpus is metal complexes — the shipped distance is COD-measured for free neutral hydrocarbons; solution-phase geometry unverified.
- Game-feel constants are single-table data (SPEED_TIERS, wall constants in `wall.py`) — retunes are one-line data edits with derived tests (5.1 / quick-003 precedent).
- Known owner-accepted limitations and parked candidates live in STATE.md (Pending Todos) and the v1 audit §8; nothing blocks gameplay or spectra.
- `tmp/bioCHEMeleon` (author's prior PyMOL game plugin) remains available as prior art for future UI work.

## Constraints

- **Environment**: WSL Ubuntu dev shell; no installs, no conda envs, no pip. `python3.6` for syntax checks/unit tests only; `tclsh` available. PyMOL 2.5.0 runs in a Windows conda env (headless via `cmd.exe /c C:\src\run-conda-pymol.bat -cq <script>`); WSL→Windows path conversion required.
- **Dependencies**: only what `pymol-open-source` ships (PyQt5 via `pymol.Qt`, numpy); extra libs need a written list + explicit user approval, vendored into `./3rd_party_lib/` with license noted.
- **Code quality**: efficient, traceable, clean, safe; structured repo.
- **UI**: simple, user-friendly, clear but sufficient in-game explanation.
- **Attribution**: all demo data cited with verified sources (DATA_SOURCES.md); nothing made up. All claims/citations must be verified and explicitly human-approved.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| 2D plane + locked camera; constant speed within a run (owner-tuned tier selector) | Research-informed, user-approved; simplest collision model | ✓ Good — shipped; GAME-11 tiers 6.0/9.0 default/11.0/13.0 Å/s |
| Turn model = rigid chain pivot; shipped owner-amended (train-follow tail, 180°-only refusal) | Cited stacking geometry must survive every frame | ✓ Good — verified as the replacement contract at the live checkpoint |
| Stacking = dataset-cited mode + distance; refuse-and-skip unknowns | Educational integrity — no invented chemistry | ✓ Good — biphenyl kept as the designed REFUSE_ATOM demonstrator |
| π-stack geometry 3.60 Å @ 20° human-approved (Janiak rule + measured CC0 COD) | Every shipped number must be sourced + approved | ✓ Good — DATA-02 signed off at GATE V; scope caveat recorded |
| Generic π-stack for uploads behind explicit Setup consent (STACK-06, promoted v2→v1) | Upload-only games winnable without fabricated chemistry | ✓ Good — OFF default, labeled illustrative everywhere |
| Score = molecule count; win cap ~10 mols / ~100 atoms + budget warning | Mirrors the win condition; guards hessian ~N³ cost | ✓ Good |
| 6 buttons — "Generate and export" dropped | Listed in spec but undefined | ✓ Good |
| Crashed snake still completes → Get Spectra | Core value reachable in every run | ✓ Good |
| Broadened IR plot + static mode vectors on the optimized frame | xtb --ohess supplies frequencies + intensities; optimized frame is the correct geometry | ✓ Good — owner sign-off 07-10 |
| xtb via async QProcess + verified success contract + calibrated budget guard | UI never blocks; never fake success | ✓ Good — 84–101 s @ 104 atoms, `-P 4` |
| Anchor live state on `pmg_tk.startup._serpentrum` + AST purity gates | Reload/double-import safety; zero external deps | ✓ Good — green across all 13 phases |
| Parallel plan execution via git worktrees (disjoint `files_modified`) | Eliminates shared-index commit races | ✓ Good — zero merge conflicts every parallel wave |
| Post-release changes via dated route-(b) requirement amendments | Closed GATE V ledger keeps its meaning; zero audit-tool churn | ✓ Good — GAME-05 Phases 9 + 9.1 |
| Fixed-size dialog + no move/resize handlers | Windows 200%-DPI geometry-negotiation fix | ✓ Good — flicker gone ("pass this") |
| Parked feel candidates (edge-bias spawns; per-preset wall cap; small-imaginary log line) | Feel-check deferral with sketches on file | — Pending owner GO |

---
*Last updated: 2026-10-18 after v1 milestone*
