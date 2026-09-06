# Requirements: serpentrum

**Defined:** 2026-09-06
**Core Value:** Playing snake by stacking real molecules with known stacking geometry, then seeing the IR spectrum of the molecule you assembled, computed end-to-end inside PyMOL via xtb.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Setup & Configuration

> UI note: the popup dialog (tabs, layout, widget patterns) may borrow from `tmp/bioCHEMeleon`'s popup UI — the author's prior PyMOL game plugin.

- [ ] **SETUP-01**: Plugin installs as a standard PyMOL plugin (Plugin Manager or plugin path) and shows a single "serpentrum" menu item that opens one 3-tab dialog (Setup / Game / Spectra)
- [ ] **SETUP-02**: Setup tab lets the user choose the demo set from a dropdown (v1 ships Set A) or upload their own small-molecule SDF/mol2 set
- [ ] **SETUP-03**: Setup tab offers preset box sizes via dropdown
- [ ] **SETUP-04**: Setup tab lets the user select the head molecule from the set, with "random" as default
- [ ] **SETUP-05**: Setup tab lets the user set the xtb path and xtb env resources, defaulting to auto-detect; detection handles both `xtb` and `xtb.exe`
- [ ] **SETUP-06**: Setup tab lets the user set the win cap (snake molecule count), with a safe default (~10 molecules / ~100 atoms) and a visible warning when raised beyond the safe atom budget (hessian cost ~N³)
- [ ] **SETUP-07**: Bottom action row has 6 buttons: Reset, Randomize, Save Setup, Load Setup, Cleanup model, Start
- [ ] **SETUP-08**: Save Setup writes a setup file that another user (e.g. educator) can Load Setup to reproduce the exact game configuration

### Gameplay

> Turn model (DECIDED 2026-09-06, user-approved): **rigid chain pivot** — pairwise stacking transforms stay frozen at cited geometry at all times; a turn sweeps the whole chain around the head (animated over a few ticks); a turn whose sweep would hit the boundary or body is refused; 180° reversal forbidden. Implemented as GAME-10.

- [ ] **GAME-01**: Clicking Start switches to the Game tab, counts down 3-2-1, then starts movement
- [ ] **GAME-02**: Gameplay runs on a 2D plane inside the 3D viewer with a locked camera; the box boundary is clearly displayed at all times
- [ ] **GAME-03**: The head renders as spheres and pickups as sticks; the snake moves forward continuously and the 4 arrow keys steer it (cannot stop)
- [ ] **GAME-04**: Picking up a molecule stacks it onto the snake; molecule count and atom count are tracked (hidden, used for the pre-xtb atom-budget check)
- [ ] **GAME-05**: Hitting the boundary or the snake's own body (segment-based collision: head-centroid vs chain segments) ends the run, but the snake is still "complete"
- [ ] **GAME-06**: The player wins when snake length exceeds the configured cap
- [ ] **GAME-07**: Game tab shows a rolling info box, elapsed timer, molecules-remaining-before-win, a pause/resume toggle, and a restart button that resets to the initial state
- [ ] **GAME-08**: Snake speed is constant for v1
- [ ] **GAME-09**: On completion (win or crash): viewer clears, camera focuses the completed snake, info box shows snake length + total score (molecule count), and "Get Spectra" activates
- [ ] **GAME-10**: Turning rotates the entire chain as a rigid body (stacking geometry immutable at all times); a turn whose sweep would collide with the boundary or body is refused; 180° reversal is forbidden

### Molecular Stacking

- [ ] **STACK-01**: Each pickup is placed deterministically at the dataset-stored geometry (translate/rotate onto the stack position) — placed geometry equals the cited distance
- [ ] **STACK-02**: Stacking data is a data file (not code): interaction mode + distance + citation per molecule pair; v1 dataset = π-stack, parallel-displaced (Set A)
- [ ] **STACK-03**: A pickup without a verified dataset entry is skipped (not placed), with the info box stating why — no invented chemistry
- [ ] **STACK-04**: Info box shows per-pickup structured content (interaction name, distance, one-line explanation, citation short-code), plus idle chemistry tips, early controls hints, and an end-of-run interaction breakdown
- [ ] **STACK-05**: A clash gate rejects stacking placements that would collide (protecting xtb from inferring spurious covalent bonds)

### Spectra

- [ ] **SPECTRA-01**: "Get Spectra" switches to the Spectra tab
- [ ] **SPECTRA-02**: Spectra tab runs `xtb --ohess` (optimization + numerical hessian) on the final snake asynchronously — UI stays responsive, run uses a fresh per-run temp dir, success = exit 0 + "normal termination" on stderr + expected output files, and the run can be cancelled
- [ ] **SPECTRA-03**: Spectra tab plots a broadened IR spectrum (frequencies + IR intensities, Gaussian broadening) with minimal adjustments (plot size, axis labels) and a save-plot button
- [ ] **SPECTRA-04**: Spectra tab streams calculation progress into a log panel
- [ ] **SPECTRA-05**: Spectra tab shows a frequency table; clicking a row draws that mode's displacement vectors on the snake in the OpenGL viewer (static vectors, no animation); negative frequencies display as imaginary (e.g. −31.9i) and zero-intensity modes are listed
- [ ] **SPECTRA-06**: Before launching xtb, the hidden molecule/atom counts are re-checked against the configured cap with a warning if exceeded

### Demo Data & Attribution

- [ ] **DATA-01**: v1 ships Demo Set A (aromatic π-stack: benzene, naphthalene, anthracene, phenanthrene, biphenyl) with PubChem 3D SDFs (CID-cited) and the π-stack interaction dataset
- [ ] **DATA-02**: Every shipped distance number is pinned from a real source (Janiak 2000 full text or a measured COD CIF) and explicitly approved by the human before shipping — no invented data anywhere
- [ ] **DATA-03**: Uploaded molecule sets are size-gated (≤3 rings); uploaded molecules without stacking dataset entries follow the skip policy (STACK-03)
- [ ] **DATA-04**: DATA_SOURCES.md documents every molecule (source DB, ID, DOI, license, attribution) in the bioCHEMeleon format; CSD/CCDC data is never redistributed (cite published values only; prefer CC0 COD for shipped measurements)

### Infrastructure & Environment

- [ ] **INFRA-01**: The full pipeline works in the established environment: WSL python3.6 test suite, headless Windows PyMOL 2.5.0 smokes via cmd.exe, Windows xtb invoked from WSL with path conversion
- [ ] **INFRA-02**: Pure modules import stdlib + other pure modules only (no pymol/Qt/numpy at module level or in function bodies); Qt imports go through `pymol.Qt` (never `from PyQt5 import`); tests use zero sys.modules stubs
- [ ] **INFRA-03**: Plugin live state is anchored outside module globals so Plugin-Manager reload or double import never creates duplicate controllers
- [ ] **INFRA-04**: All game-generated objects live in an `srp_*` namespace; Cleanup model removes only game-generated objects and works in a fresh process after a session save/reload
- [ ] **INFRA-05**: The dialog is modeless; the Qt main thread is never blocked (no modal dialogs during play, no synchronous xtb waits, no threads calling cmd.*)
- [ ] **INFRA-06**: All code parses under python3.6 (py_compile gate) and matches the Windows conda runtime discipline

### Documentation & Audit

- [ ] **DOCS-01**: README documents install, usage, and the demo set, and keeps the vibe-coding warning block at the top; every README claim matches actual behavior
- [ ] **DOCS-02**: DATA_SOURCES.md ships complete (see DATA-04)
- [ ] **DOCS-03**: In-game help covers controls, a "click the 3D viewer" focus hint, what negative frequencies mean, and a next-action hint on every screen — clear but sufficient, no walls of text
- [ ] **DOCS-04**: Documentation audit: docs are verified against actual code behavior (README steps reproduce, UI help text matches real controls and dataset values)
- [ ] **DOCS-05**: End-to-end release audit: full flow (setup → play → complete → xtb → IR plot → save) verified headless + human checkpoints; all v1 requirements checked and traceability complete

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Demo Data

- **DATA-05**: Additional demo sets: Set B (carboxylic-acid H-bond dimers), Set C (heteroaromatics), Set D (hydroxyl H-bond chains)
- **DATA-06**: In-plugin provenance (per-molecule source popup / DATA_SOURCES.md link)

### Gameplay

- **GAME-09-v2**: Vibrational-mode animation (v1 ships static vectors only)
- **GAME-10-v2**: Speed increases with snake length (genre convention; pending playtesting)
- **GAME-11-v2**: 3D free-steering mode (needs key-mapping design + explicit approval)

### Stacking

- **STACK-06**: User-approved generic fallback list (e.g. vdW contact) for uploads without dataset entries
- **STACK-07**: Mixed-interaction sets (chain alternates π-stack / H-bond links)

### Spectra

- **SPECTRA-07**: Raman spectra (xtb provides it; IR first)

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| "Generate and export" button | Listed in the original spec's 7 buttons but never defined; dropped for v1 (6 buttons) |
| Live spectrum preview during gameplay | Hessian ~N³ cost kills frame rate and the atom budget; payoff stays at end-of-run |
| Physics-based relaxation at pickup time | Slow, nondeterministic gameplay; pre-empts the xtb payoff; deterministic placement at cited geometry instead |
| Silent stacking fallback for unknown molecules | Teaching a made-up distance is worse than refusing (educational integrity) |
| Reproducing real crystal packing (herringbone etc.) | Chaotic chain geometry; game uses idealized pairwise interaction geometry, labeled as such |
| Multiplayer / .io variants | Network stack far beyond a classroom plugin |
| Raman/UV-Vis/NMR in v1 | One spectrum done well; Raman deferred to v2 |
| External Python dependencies | Only what pymol-open-source ships (PyQt5 via pymol.Qt, numpy); extras need written list + user approval + vendoring |
| Vibrational-mode animation in v1 | Spec explicitly defers; static vectors only |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| SETUP-01 | Phase 1 | Complete |
| SETUP-02 | Phase 3 | Pending |
| SETUP-03 | Phase 3 | Pending |
| SETUP-04 | Phase 3 | Pending |
| SETUP-05 | Phase 3 | Pending |
| SETUP-06 | Phase 3 | Pending |
| SETUP-07 | Phase 8 | Pending |
| SETUP-08 | Phase 8 | Pending |
| GAME-01 | Phase 4 | Pending |
| GAME-02 | Phase 4 | Pending |
| GAME-03 | Phase 4 | Pending |
| GAME-04 | Phase 5 | Pending |
| GAME-05 | Phase 5 | Pending |
| GAME-06 | Phase 5 | Pending |
| GAME-07 | Phase 4 | Pending |
| GAME-08 | Phase 4 | Pending |
| GAME-09 | Phase 5 | Pending |
| GAME-10 | Phase 5 | Pending |
| STACK-01 | Phase 5 | Pending |
| STACK-02 | Phase 2 | Pending |
| STACK-03 | Phase 5 | Pending |
| STACK-04 | Phase 5 | Pending |
| STACK-05 | Phase 5 | Pending |
| SPECTRA-01 | Phase 7 | Pending |
| SPECTRA-02 | Phase 6 | Pending |
| SPECTRA-03 | Phase 7 | Pending |
| SPECTRA-04 | Phase 7 | Pending |
| SPECTRA-05 | Phase 7 | Pending |
| SPECTRA-06 | Phase 6 | Pending |
| DATA-01 | Phase 8 | Pending |
| DATA-02 | Phase 8 | Pending |
| DATA-03 | Phase 3 | Pending |
| DATA-04 | Phase 8 | Pending |
| INFRA-01 | Phase 1 | Complete |
| INFRA-02 | Phase 1 | Complete |
| INFRA-03 | Phase 1 | Complete |
| INFRA-04 | Phase 3 | Pending |
| INFRA-05 | Phase 1 | Complete |
| INFRA-06 | Phase 1 | Complete |
| DOCS-01 | Phase 8 | Pending |
| DOCS-02 | Phase 8 | Pending |
| DOCS-03 | Phase 8 | Pending |
| DOCS-04 | Phase 8 | Pending |
| DOCS-05 | Phase 8 | Pending |

**Coverage:**
- v1 requirements: 44 total
- Mapped to phases: 44
- Unmapped: 0 ✓

> Count corrected from 41 → 44 during roadmap creation (2026-09-06): the listed ID ranges (SETUP-01..08, GAME-01..10, STACK-01..05, SPECTRA-01..06, DATA-01..04, INFRA-01..06, DOCS-01..05) sum to 44. Each requirement maps to exactly one phase — see ROADMAP.md for phase goals and success criteria.

---
*Requirements defined: 2026-09-06*
*Last updated: 2026-09-06 — roadmap created; traceability populated (44/44 mapped)*
