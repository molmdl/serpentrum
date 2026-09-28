# Requirements: serpentrum

**Defined:** 2026-09-06
**Core Value:** Playing snake by stacking real molecules with known stacking geometry, then seeing the IR spectrum of the molecule you assembled, computed end-to-end inside PyMOL via xtb.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Setup & Configuration

> UI note: the popup dialog (tabs, layout, widget patterns) may borrow from `tmp/bioCHEMeleon`'s popup UI — the author's prior PyMOL game plugin.

- [x] **SETUP-01**: Plugin installs as a standard PyMOL plugin (Plugin Manager or plugin path) and shows a single "serpentrum" menu item that opens one 3-tab dialog (Setup / Game / Spectra)
- [x] **SETUP-02**: Setup tab lets the user choose the demo set from a dropdown (v1 ships Set A) or upload their own small-molecule SDF/mol2 set
- [x] **SETUP-03**: Setup tab offers preset box sizes via dropdown
- [x] **SETUP-04**: Setup tab lets the user select the head molecule from the set, with "random" as default
- [x] **SETUP-05**: Setup tab lets the user set the xtb path and xtb env resources, defaulting to auto-detect; detection handles both `xtb` and `xtb.exe`
- [x] **SETUP-06**: Setup tab lets the user set the win cap (snake molecule count), with a safe default (~10 molecules / ~100 atoms) and a visible warning when raised beyond the safe atom budget (hessian cost ~N³)
- [ ] **SETUP-07**: Bottom action row has 6 buttons: Reset, Randomize, Save Setup, Load Setup, Cleanup model, Start
- [ ] **SETUP-08**: Save Setup writes a setup file that another user (e.g. educator) can Load Setup to reproduce the exact game configuration

### Gameplay

> Turn model (DECIDED 2026-09-06, user-approved): **rigid chain pivot** — pairwise stacking transforms stay frozen at cited geometry at all times; a turn sweeps the whole chain around the head (animated over a few ticks); a turn whose sweep would hit the boundary or body is refused; 180° reversal forbidden. Implemented as GAME-10.

- [x] **GAME-01**: Clicking Start switches to the Game tab, counts down 3-2-1, then starts movement
- [x] **GAME-02**: Gameplay runs on a 2D plane inside the 3D viewer with a locked camera; the box boundary is clearly displayed at all times
- [x] **GAME-03**: The head renders as spheres and pickups as sticks; the snake moves forward continuously and the 4 arrow keys steer it (cannot stop)
- [x] **GAME-04**: Picking up a molecule stacks it onto the snake; molecule count and atom count are tracked (hidden, used for the pre-xtb atom-budget check)
- [x] **GAME-05**: Hitting the boundary or the snake's own body (segment-based collision: head-centroid vs chain segments) ends the run, but the snake is still "complete"
- [x] **GAME-06**: The player wins when snake length exceeds the configured cap
- [x] **GAME-07**: Game tab shows a rolling info box, elapsed timer, molecules-remaining-before-win, a pause/resume toggle, and a restart button that resets to the initial state
- [x] **GAME-08**: Snake speed is constant for v1
- [x] **GAME-09**: On completion (win or crash): viewer clears, camera focuses the completed snake, info box shows snake length + total score (molecule count), and "Get Spectra" activates
- [x] **GAME-10**: Turning rotates the entire chain as a rigid body (stacking geometry immutable at all times); a turn whose sweep would collide with the boundary or body is refused; 180° reversal is forbidden *(shipped owner-amended 2026-09-20: rigid sweep + train-follow tail, immutable 3.60 Å spacing; turn pre-check refuses 180° only)*
- [x] **GAME-11**: Setup tab offers a game speed/difficulty selector with named tiers (speed constant within a run per GAME-08); the choice persists via Save/Load Setup; default = the v1 baseline speed (3.0 Å/s) *(inserted 2026-09-20 with Phase 5.1 — owner playtesting feedback)* — **DELIVERED Phase 5.1 (verified 2026-09-25)**: 4-tier selector shipped; owner feel-check AMENDED the values (all drafts too slow — "only expert feel like playing"): relaxed 3.0 / normal 6.0 / fast 7.5 / expert 9.0 A/s, default tier 'normal' = 6.0; v1 baseline 3.0 survives as 'relaxed' + engine kwarg fallback; persistence via schema backcompat proven pure-layer (Save/Load buttons are Phase 8)

### Molecular Stacking

- [x] **STACK-01**: Each pickup is placed deterministically at the dataset-stored geometry (translate/rotate onto the stack position) — placed geometry equals the cited distance
- [x] **STACK-02**: Stacking data is a data file (not code): interaction mode + distance + citation per molecule pair; v1 dataset = π-stack, parallel-displaced (Set A)
- [x] **STACK-03**: A pickup without a verified dataset entry is skipped (not placed), with the info box stating why — no invented chemistry
- [x] **STACK-04**: Info box shows per-pickup structured content (interaction name, distance, one-line explanation, citation short-code), plus idle chemistry tips, early controls hints, and an end-of-run interaction breakdown
- [x] **STACK-05**: A clash gate rejects stacking placements that would collide (protecting xtb from inferring spurious covalent bonds)
- [x] **STACK-06**: User-consented generic π-stack fallback for uploads carrying a canonical planar 6-ring — placement reuses the already-approved idealized Set-A geometry (3.60 Å @ 20°), every in-game surface labels it "generic (illustrative geometry — user-approved)", consent is OFF by default and persisted; uploads without a planar 6-ring still skip *(promoted from v2 with Phase 5.2, 2026-09-20 — owner request)*

### Spectra

- [x] **SPECTRA-01**: "Get Spectra" switches to the Spectra tab
- [x] **SPECTRA-02**: Spectra tab runs `xtb --ohess` (optimization + numerical hessian) on the final snake asynchronously — UI stays responsive, run uses a fresh per-run temp dir, success = exit 0 + "normal termination" on stderr + expected output files, and the run can be cancelled
- [x] **SPECTRA-03**: Spectra tab plots a broadened IR spectrum (frequencies + IR intensities, Gaussian broadening) with minimal adjustments (plot size, axis labels) and a save-plot button
- [x] **SPECTRA-04**: Spectra tab streams calculation progress into a log panel
- [x] **SPECTRA-05**: Spectra tab shows a frequency table; clicking a row draws that mode's displacement vectors on the snake in the OpenGL viewer (static vectors, no animation); negative frequencies display as imaginary (e.g. −31.9i) and zero-intensity modes are listed
- [x] **SPECTRA-06**: Before launching xtb, the hidden molecule/atom counts are re-checked against the configured cap with a warning if exceeded

### Demo Data & Attribution

- [ ] **DATA-01**: v1 ships Demo Set A (aromatic π-stack: benzene, naphthalene, anthracene, phenanthrene, biphenyl) with PubChem 3D SDFs (CID-cited) and the π-stack interaction dataset
- [ ] **DATA-02**: Every shipped distance number is pinned from a real source (Janiak 2000 full text or a measured COD CIF) and explicitly approved by the human before shipping — no invented data anywhere
- [x] **DATA-03**: Uploaded molecule sets are size-gated (≤3 rings); uploaded molecules without stacking dataset entries follow the skip policy (STACK-03)
- [ ] **DATA-04**: DATA_SOURCES.md documents every molecule (source DB, ID, DOI, license, attribution) in the bioCHEMeleon format; CSD/CCDC data is never redistributed (cite published values only; prefer CC0 COD for shipped measurements)

### Infrastructure & Environment

- [x] **INFRA-01**: The full pipeline works in the established environment: WSL python3.6 test suite, headless Windows PyMOL 2.5.0 smokes via cmd.exe, Windows xtb invoked from WSL with path conversion
- [x] **INFRA-02**: Pure modules import stdlib + other pure modules only (no pymol/Qt/numpy at module level or in function bodies); Qt imports go through `pymol.Qt` (never `from PyQt5 import`); tests use zero sys.modules stubs
- [x] **INFRA-03**: Plugin live state is anchored outside module globals so Plugin-Manager reload or double import never creates duplicate controllers
- [x] **INFRA-04**: All game-generated objects live in an `srp_*` namespace; Cleanup model removes only game-generated objects and works in a fresh process after a session save/reload
- [x] **INFRA-05**: The dialog is modeless; the Qt main thread is never blocked (no modal dialogs during play, no synchronous xtb waits, no threads calling cmd.*)
- [x] **INFRA-06**: All code parses under python3.6 (py_compile gate) and matches the Windows conda runtime discipline

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

- **STACK-06**: ~~User-approved generic fallback list~~ **PROMOTED to v1 2026-09-20** (Phase 5.2 — generic π-stack, Setup-consented, labeled illustrative; see v1 STACK-06)
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

| Requirement | Phase | Status | Evidence |
|-------------|-------|--------|----------|
| SETUP-01 | Phase 1 | Complete | mech: tests/test_skeleton.py + smoke/01_skeleton_smoke.py; code: serpentrum/__init__.py lazy pmg_tk.startup.serpentrum entry; human: 01-06 live checkpoint APPROVED 2026-09-06 (3 clean launches, single menu item, 3-tab dialog) |
| SETUP-02 | Phase 3 | Complete | mech: tests/test_setup_logic.py + smoke/04_demo_e2e_smoke.py; code: serpentrum/gui_setup.py demo-set dropdown + upload path; human: 03-08 live checkpoint APPROVED (10 of 10 steps) 2026-09-12 |
| SETUP-03 | Phase 3 | Complete | mech: tests/test_setup_logic.py (box-preset pins) + smoke/03_viewer_bridge_smoke.py; code: serpentrum/gui_setup.py preset dropdown + serpentrum/pymol_bridge.py srp_box (BOX_DISPLAY_Z); human: 03-08 live checkpoint APPROVED (10 of 10) 2026-09-12 |
| SETUP-04 | Phase 3 | Complete | mech: tests/test_setup_logic.py + tests/test_gui_pins.py (eager head-combo pin, 08-08); code: serpentrum/gui_setup.py head dropdown with random default; human: 03-08 live checkpoint APPROVED (10 of 10) 2026-09-12 |
| SETUP-05 | Phase 3 | Complete | mech: tests/test_xtbenv.py + tests/test_winpath.py; code: serpentrum/xtbenv.py validate_binary_path (xtb + xtb.exe) + tools/winpath.py; human: 03-08 live checkpoint (xtb auto + manual legs) APPROVED 2026-09-12 |
| SETUP-06 | Phase 3 | Complete | mech: tests/test_setup_logic.py + tests/test_budget_guard.py; code: serpentrum/gui_setup.py win-cap control + hessian warning + serpentrum/budget_guard.py; human: 03-08 live checkpoint (win-cap warning step) APPROVED 2026-09-12 |
| SETUP-07 | Phase 8 | Pending | mech: tests/test_gui_pins.py (6-label order + single Start-route pins, 08-08); code: serpentrum/gui.py 6-button bottom row (Reset, Randomize, Save Setup, Load Setup, Cleanup model, Start); human: GATE V (08-11) approval |
| SETUP-08 | Phase 8 | Pending | mech: tests/test_setup_logic.py save/load round-trip + smoke/14_release_e2e_smoke.py stage7 setup_roundtrip; code: serpentrum/setup_logic.py save_setup/load_setup/merge_defaults; human: GATE V (08-11) approval |
| GAME-01 | Phase 4 | Complete | mech: tests/test_gui_pins.py (single setCurrentIndex(1) Start-route pin); code: serpentrum/gui_game.py 3-2-1 countdown + movement start; human: 04-09 closing checkpoint APPROVED (12 of 12 live steps) 2026-09-14 |
| GAME-02 | Phase 4 | Complete | mech: smoke/05_loop_camera_smoke.py; code: serpentrum/pymol_bridge.py camera lock (GAME-02 scope) + srp_box boundary display; human: 04-09 closing checkpoint APPROVED (12 of 12) 2026-09-14 |
| GAME-03 | Phase 4 | Complete | mech: tests/test_engine_core.py + smoke/06_input_smoke.py; code: serpentrum/input.py KeySteerWizard (do_special route) + serpentrum/pymol_bridge.py head spheres / pickup sticks; human: 04-07 keys checkpoint APPROVED 2026-09-13 |
| GAME-04 | Phase 5 | Complete | mech: tests/test_phase5_integration.py + smoke/08_stack_place_smoke.py + smoke/10_chain_count_smoke.py; code: serpentrum/game_engine.py capture + serpentrum/placement.py + serpentrum/pymol_bridge.py chain_atom_counts; human: 05-16 7-round live checkpoint APPROVED 2026-09-18..20 |
| GAME-05 | Phase 5 | Complete | mech: tests/test_engine_rules.py (boundary + body-crash legs); code: serpentrum/game_engine.py collision checks + complete-snake-on-crash; human: 05-16 deliberate-crash rounds APPROVED 2026-09-18..20 |
| GAME-06 | Phase 5 | Complete | mech: tests/test_engine_win_desync.py; code: serpentrum/game_engine.py cap -> won emission; human: cap-3 win at 06-12 live checkpoint APPROVED (12 of 12) 2026-09-26 |
| GAME-07 | Phase 4 | Complete | mech: tests/test_hud_logic.py + tests/test_hud_content.py; code: serpentrum/hud_logic.py + serpentrum/gui_game.py info box, timer, remaining-before-win, pause/resume, restart; human: 04-09 closing checkpoint APPROVED (12 of 12) 2026-09-14 |
| GAME-08 | Phase 4 | Complete | mech: tests/test_engine_speed.py; code: serpentrum/game_engine.py constant speed_a_per_s within a run; human: 04-09 closing checkpoint APPROVED (12 of 12) 2026-09-14 |
| GAME-09 | Phase 5 | Complete | mech: smoke/10_chain_count_smoke.py (completion count channel); code: serpentrum/gui_game.py completion view + camera focus + info recap + Get Spectra arming; human: 05-16 win/crash completion rounds APPROVED 2026-09-18..20 |
| GAME-10 | Phase 5 | Complete (owner-amended contract — see note) | mech: tests/test_engine_turns.py + tests/test_engine_tail_follow.py + smoke/07_transform_sweep_smoke.py; code: serpentrum/game_engine.py rigid chain sweep + train-follow tail (immutable 3.60 A spacing); human: 05-16 7-round live checkpoint APPROVED 2026-09-18..20 (owner-amended: 180-deg refuse only, REFUSE_WALL removed) |
| GAME-11 | Phase 5.1 | Complete | mech: tests/test_engine_speed.py + tests/test_phase51_integration.py; code: serpentrum/setup_logic.py SPEED_TIERS (relaxed/normal/fast/expert) + persistence; human: 5.1-06 feel-check APPROVED 2026-09-25 (owner-amended values 3.0/6.0/7.5/9.0 A/s, default normal 6.0) |
| STACK-01 | Phase 5 | Complete | mech: tests/test_stacking_math.py + tests/test_placement.py; code: serpentrum/stacking.py ring_frame + serpentrum/placement.py deterministic transform; human: 05-16 live DBG pins (dot=1.000000 d=3.6000) APPROVED 2026-09-18..20 |
| STACK-02 | Phase 2 | Complete | mech: tests/test_stacking_dataset.py; code: serpentrum/data/stacking_pi_stack.json (data file with citations, not code); human: pi-stack geometry APPROVED 2026-09-10 (3.60 A @ 20 deg, distance_a 3.383, lateral_offset_a 1.231) |
| STACK-03 | Phase 5 | Complete | mech: tests/test_generic_stack.py + tests/test_phase5_integration.py (skip taxonomy); code: serpentrum/generic_stack.py pre-resolved skips + serpentrum/hud_logic.py reasoned HUD lines; human: 05-16 skip/refuse rounds APPROVED 2026-09-18..20 (no invented chemistry) |
| STACK-04 | Phase 5 | Complete | mech: tests/test_hud_content.py; code: serpentrum/hud_logic.py structured pickup content + idle tips + early hints + end-of-run recap; human: 05-16 info-box content accepted APPROVED 2026-09-18..20 |
| STACK-05 | Phase 5 | Complete | mech: tests/test_placement.py (clash-refuse pins) + smoke/08_stack_place_smoke.py; code: serpentrum/placement.py REFUSE_ATOM clash gate (biphenyl 1.87 A demonstrator); human: 05-16 rounds 3-4 APPROVED 2026-09-20 (REFUSE_WALL removed, clash gate kept) |
| STACK-06 | Phase 5.2 | Complete | mech: tests/test_generic_stack.py + tests/test_phase52_integration.py; code: serpentrum/generic_stack.py consent-gated generic pi-stack entry (OFF default, persisted, labeled illustrative); human: 5.2-09 feel-check APPROVED (11 of 11 steps) 2026-09-26 |
| SPECTRA-01 | Phase 7 | Complete | mech: tests/test_gui_pins.py (wiring pins); code: serpentrum/gui.py Get Spectra -> live SpectraTab tab switch; human: 07-10 consolidated checkpoint APPROVED round 2 2026-09-26 ("approved, well done") |
| SPECTRA-02 | Phase 6 | Complete | mech: tests/test_xtb_run.py + smoke/11_xtb_runner_smoke.py (informational real-xtb success/cancel contracts); code: serpentrum/xtb_runner.py QProcess controller + serpentrum/xtb_run.py verdict/state contract; human: 06-12 live checkpoint APPROVED (12 of 12) 2026-09-26 ("xtb finished: ok") |
| SPECTRA-03 | Phase 7 | Complete | mech: smoke/12_plot_smoke.py STAGE2 (PNG magic bytes + reload) + tests/test_plot_logic.py; code: serpentrum/gui_plot.py route-A paint_scene/render_image + save-plot; human: 07-06 round-2 APPROVED 2026-09-26 + 07-10 final sign-off 2026-09-26 |
| SPECTRA-04 | Phase 7 | Complete | mech: smoke/11_xtb_runner_smoke.py (informational streaming legs) + tests/test_xtb_run.py; code: serpentrum/xtb_runner.py log_tail + serpentrum/gui_spectra.py 500-block log panel (replay-first); human: 06-12 live-log responsive verdict APPROVED 2026-09-26 |
| SPECTRA-05 | Phase 7 | Complete | mech: tests/test_spectra_ui.py + smoke/13_mode_arrows_smoke.py; code: serpentrum/spectra_ui.py table/arrow seams + serpentrum/gui_spectra.py row-click -> srp_mode_vec on srp_xtbopt; human: 07-10 APPROVED round 2 incl. optimized-frame sign-off 2026-09-26 |
| SPECTRA-06 | Phase 6 | Complete | mech: tests/test_budget_guard.py; code: serpentrum/budget_guard.py + serpentrum/gui.py pre-launch count gate; human: 06-12 head-inclusive counts (54 + 12 = 66) APPROVED (12 of 12) 2026-09-26 |
| DATA-01 | Phase 8 | Pending | mech: tests/test_demo_data.py TestLoadDemoSetEndToEnd (08-02) + smoke/04_demo_e2e_smoke.py; code: serpentrum/data/ manifest.json + 5 PubChem 3D SDFs (CID-cited); human: GATE V (08-11) data approval |
| DATA-02 | Phase 8 | Pending | mech: tests/test_stacking_dataset.py pinned literals; code: serpentrum/data/stacking_pi_stack.json (3.60 A @ 20 deg from verified sources); human: partial approval 2026-09-10 (Phase 2 pi-stack), full sign-off GATE V (08-11) |
| DATA-03 | Phase 3 | Complete | mech: tests/test_setloader.py + tests/test_molfile.py; code: serpentrum/setloader.py <=3-ring gate + upload skip policy (STACK-03); human: 03-08 live checkpoint (upload reject + accept legs) APPROVED 2026-09-12 |
| DATA-04 | Phase 8 | Pending | mech: tools/check_docs.py data-citation checks + tests/test_docs_audit.py; code: serpentrum/data/DATA_SOURCES.md bioCHEMeleon-format checklist (08-02 edits); human: GATE V (08-11) data approval |
| INFRA-01 | Phase 1 | Complete | mech: tests/run_gates.py full battery (gates + 11 REQUIRED smokes + --xtb leg); code: tools/ gate and path toolchain (check_purity.py, check_docs.py, winpath.py); human: full env exercised at every live checkpoint (01-06, 03-08, 04-09, 05-16, 06-12, 07-10; 2026-09-06..2026-09-26) |
| INFRA-02 | Phase 1 | Complete | mech: tools/check_purity.py AST gate + tests/test_purity_gates.py; code: tools/check_purity.py GUI/BRIDGE allowlists (everything else pure, zero pymol/Qt/numpy); human: purity gate green at every phase close since 01-06 (2026-09-06) |
| INFRA-03 | Phase 1 | Complete | mech: tests/test_skeleton.py (anchor + single-instance pins); code: serpentrum/__init__.py anchor pmg_tk.startup._serpentrum (never module globals); human: 01-06 reload survival verified APPROVED 2026-09-06 |
| INFRA-04 | Phase 3 | Complete | mech: smoke/04_demo_e2e_smoke.py cleanup + user-object sentinel leg; code: serpentrum/pymol_bridge.py cleanup_srp (srp_* namespace only); human: 03-08 .pse fresh-process survival APPROVED 2026-09-12 |
| INFRA-05 | Phase 1 | Complete | mech: tools/check_purity.py exec-token ban + tests/test_xtb_run.py (async runner contract); code: serpentrum/xtb_runner.py QProcess async + modeless dialog (show() only); human: 01-06 modelessness APPROVED 2026-09-06 + 06-12 responsive live-log verdict 2026-09-26 |
| INFRA-06 | Phase 1 | Complete | mech: tests/run_gates.py gate 1 py_compile walk; code: py3.6 discipline across serpentrum/ (stdlib-compatible, no newer syntax); human: gates green at every phase close through 07-10 (2026-09-26) |
| DOCS-01 | Phase 8 | Pending | mech: tools/check_docs.py README-claims families + tests/test_docs_audit.py; code: README.md (08-07 rewrite; vibe block pinned byte-exact); human: GATE V (08-11) approval |
| DOCS-02 | Phase 8 | Pending | mech: tools/check_docs.py DATA_SOURCES citation checks + tests/test_docs_audit.py; code: serpentrum/data/DATA_SOURCES.md (08-02 CID/DOI edits); human: GATE V (08-11) data approval |
| DOCS-03 | Phase 8 | Pending | mech: tests/test_help_text.py; code: serpentrum/help_text.py + gui wiring (08-09 game/spectra/before-apply/after-apply hints rendered); human: GATE V (08-11) approval |
| DOCS-04 | Phase 8 | Pending | mech: tools/check_docs.py (7 check families) + tests/test_docs_audit.py (23 tests); code: tools/check_docs.py (doc-vs-code harness, gate-3 discovered); human: GATE V (08-11) reproduce steps (Section C) |
| DOCS-05 | Phase 8 | Pending | mech: smoke/14_release_e2e_smoke.py SMOKE-OK RELEASE-E2E + tools/audit_requirements.py; code: tools/audit_requirements.py (4 checks + --release) + tests/test_audit_requirements.py; human: GATE V (08-11) closing checkpoint |

*Reconciled 2026-09-28 (UTC) — Phase 8 plan 08-10: checkbox list aligned with table statuses; Evidence column added; Phase-8 rows flip at the GATE V (08-11) closing checkpoint.*

**Coverage:**
- v1 requirements: 46 total (44 original + GAME-11 with Phase 5.1 + STACK-06 promoted from v2 with Phase 5.2, 2026-09-20)
- Mapped to phases: 46
- Unmapped: 0 ✓

> Count corrected from 41 → 44 during roadmap creation (2026-09-06): the listed ID ranges (SETUP-01..08, GAME-01..10, STACK-01..05, SPECTRA-01..06, DATA-01..04, INFRA-01..06, DOCS-01..05) sum to 44. Each requirement maps to exactly one phase — see ROADMAP.md for phase goals and success criteria.

---
*Requirements defined: 2026-09-06*
*Last updated: 2026-09-14 — Phase 4 complete (verified 40/40 must-haves): GAME-01, GAME-02, GAME-03, GAME-07, GAME-08 marked Complete*
*2026-09-20 — GAME-11 added (Phase 5.1 inserted): Setup-selectable game speed/difficulty, constant per run (GAME-08 intact), persisted, default = baseline 3.0 Å/s. Coverage 44 → 45. GAME-10 behavior note: 05-16 checkpoint owner overrides amended the in-run turn model (turn pre-check refuses 180° only; REFUSE_WALL placement gate removed; chain may extend outside the box — only the head is box-bound) — statuses to be finalized at Phase 5 completion.*
*2026-09-20b — **Phase 5 COMPLETE** (05-VERIFICATION: passed — 48/48 plan must-have truths, 3 verified-as-owner-amended; 5/5 success criteria; 7-round human checkpoint 2026-09-18..20): GAME-04, GAME-05, GAME-06, GAME-09, GAME-10, STACK-01, STACK-03, STACK-04, STACK-05 → Complete. GAME-10 shipped contract = owner-amended: rigid chain sweep with train-follow tail (immutable 3.60 Å spacing), turn pre-check refuses 180° only, REFUSE_WALL removed (chain may extend outside box; only head box-bound), REFUSE_ATOM clash gate intact (STACK-05).*
*2026-09-20c — STACK-06 PROMOTED v2 → v1 (Phase 5.2 inserted, owner request): generic π-stack for canonical-planar-6-ring uploads, Setup-consented (OFF default), labeled "illustrative — user-approved"; plan before Phase 5.1, execute sequentially. Coverage 45 → 46.*
