# Project Research Summary

**Project:** serpentrum
**Domain:** PyMOL 2.5.0 plugin — educational snake game (molecule stacking by known noncovalent geometry) + xtb IR-spectra payoff
**Researched:** 2026-09-06
**Confidence:** HIGH overall — every core mechanism claim verified against `pymol-src`, `tmp/bioCHEMeleon`, `Pymol-script-repo`, or live `xtb.exe` runs; a small set of explicitly flagged items (up/down keys, plot-save, 100-atom timing, stacking distance numbers) carry LOW/MEDIUM confidence and are mapped to phases below

## Executive Summary

serpentrum is a constrained-greenfield PyMOL plugin: the dependency set is fixed by the repo (only what `pymol-open-source` 2.5.0 ships — PyQt5 via `pymol.Qt`, numpy), and the development environment is fixed (WSL dev shell with `python3.6` and **no numpy**, Windows PyMOL runtime, Windows xtb 6.7.1pre invoked from WSL). The research conclusion is that this constraint set is not a limitation but the design: **zero new dependencies are needed**. The game loop is `QtCore.QTimer` on the Qt main thread; rendering is game-owned CGO objects rebuilt per tick (never mutating user molecules — the `srp_*` namespace makes PyMOL's missing undo a non-issue); the spectrum plot is a custom QPainter widget (two verified in-ecosystem precedents; matplotlib is absent from the PyMOL tree); xtb runs as an async subprocess (QProcess preferred) with results drained on the main thread. Architecture follows the bioCHEMeleon-proven layering: pure stdlib-only modules (WSL `python3.6`-testable) ← pymol bridge ← Qt GUI ← composition root.

The single most consequential research finding is an **empirical xtb flag correction**: the assumed pipeline `xtb -o --hess` silently produces **no vibrational output** (exit 0, no error — the optimizer consumes `--hess` as its level argument). The verified command is **`--ohess`** (one-word flag), which produces `vibspectrum`, `g98.out`, and `hessian`. Real outputs for phenol, CO₂, and a π-stacked phenol dimer are committed as fixtures at `.planning/research/xtb-spike-fixtures/` — the spectra parser is therefore **test-driven against reality from day one**, not against docs. Secondary risks are: arrow-key capture inside PyMOL (up/down may conflict with command-history bindings — a scheduled spike with a designed fallback), the plugin-identity double-singleton trap under Plugin-Manager reload (must anchor live state outside module globals from commit one), and modal/threading hazards that freeze the shared Qt event loop (all with verified prevention patterns).

The scientific content has a hard governance constraint: **every citation and distance number must be verified and human-approved** (no fabrication). Live source verification worked (PubChem 3D SDF downloads, COD searches, DOI registries — all VERIFIED live), and four demo-set proposals exist with per-item verification status. But the specific stacking distance numbers (π-stack 3.4 Å game value, COOH dimer O···O, H-bond chains) are **UNVERIFIED until pinned from Janiak 2000 full text or COD CIFs at data-prep**, then approved. Three design decisions remain open for the human: **2D-plane vs 3D** (research recommends 2D + locked camera for v1), the **stacking-fallback policy** for molecules without verified data (silent fallback is forbidden; an explicit approved fallback list is an open requirements question), and **demo-set selection** (MVP recommendation: one set done fully right — Set A or B — beats three done loosely).

### Cross-Cutting Findings That Change the Roadmap

1. **xtb flag correction (empirically verified `[RUN]`):** `-o --hess` silently skips the hessian; **`--ohess`** produces `vibspectrum`/`g98.out`/`hessian`. Real fixtures committed at `.planning/research/xtb-spike-fixtures/` (phenol, CO₂, π-stacked dimer, plus a corrupted-input case proving the exit-128/stderr contract). The spectra phase must start from these fixtures, not docs. This **closes** the LOW-confidence gate STACK.md had flagged — the spectra phase is now de-risked.
2. **Zero new dependencies:** QPainter-based spectrum plot (`dynoplot.py` + `pmg_qt/volume.py` precedents); matplotlib absent from the entire PyMOL tree (grep-verified). Broadening is a numpy (or pure-`math`) Gaussian sum.
3. **Input risk (the one open mechanism question):** arrow keys via a Wizard subclass whose `get_event_mask()` **must** include `event_mask_key + event_mask_special` (4+8) or `do_special` never fires; `up`/`down` `set_key` bindings are accepted by validation code but omitted from the docstring and reserved by the shortcut manager — **spike scheduled in the input phase** with a Qt event-filter fallback designed.
4. **Game loop:** `QTimer` on the Qt main thread (bioCHEMeleon-verified); **never** threads calling `cmd.*` (single-lock API, verified); xtb async via **QProcess** (signals land on the main thread; worker-thread + queue + QTimer-drain is the verified fallback if QProcess misbehaves in the conda build).
5. **Plugin identity:** plugins load as `pymol.plugins.startup.<name>`; a double import or Plugin-Manager reload creates a **second module object with fresh globals** — the `dialog`/controller singleton duplicates and two controllers drive one scene. Anchor live state outside module globals (e.g. on `pymol` package attributes) from the first commit.
6. **Build order:** ARCHITECTURE.md's dependency-driven A–H sequence and PITFALLS.md's pitfall→phase mapping combine into the recommended phase structure below.

## Key Findings

### Recommended Stack

Detail: `.planning/research/STACK.md`. The stack is fixed and fully verified; nothing to install, no pip, no conda, no vendoring.

**Core technologies:**
- **PyMOL open-source 2.5.0** — the only runtime; plugin API (`pymol.cmd`, `pymol.wizard`) verified complete for all game needs
- **Python authored to 3.6-compatible syntax** — so the WSL `python3.6.9` dev gate and the Windows conda runtime both work (bioCHEMeleon-proven discipline; avoid dataclasses/walrus/f-string `=`)
- **PyQt5 via `pymol.Qt`** — always `from pymol.Qt import ...`, never `from PyQt5 import` (PySide2 fallback; grep-gated)
- **numpy (bundled)** — broadening math, geometry; **but pure modules must be stdlib-only at module level** because WSL `python3.6` has no numpy (verified); numpy only as a lazy import inside functions on the Windows runtime side
- **xtb 6.7.1pre (external exe, not a Python dep)** — `--ohess` = opt + numerical hessian → frequencies + IR intensities; invoked as a subprocess in a fresh per-run temp dir

**Hard invocation contract (Pitfall 1):** never `-o --hess`; use `--ohess` (or two-stage `-o` → `--hess` on `xtbopt.xyz`). Success = exit 0 AND stderr contains "normal termination" AND expected output files exist. xtb sprays ~10 files into its CWD → always per-run temp dir + relative filenames.

### Expected Features

Detail: `.planning/research/FEATURES.md`.

**Must have (table stakes):** forward-only 4-arrow steering, eating = stacking growth, boundary + self-collision ends the run, countdown, pause/restart, live score + molecules-remaining, readable head-vs-pickup visuals, setup persistence, standard plugin install, attribution doc — plus the chemistry-credibility stakes: placed geometry **equals the cited distance**, known mode + rule + source per pickup, database-verifiable molecule files (PubChem pipeline VERIFIED live), and an honest failure mode when data is missing.

**Should have (differentiators):** real interaction geometry as gameplay (empty competitive cell — Snakeleev teaches element ID with no geometry), IR spectrum of the *player's own assembly*, clickable frequency table → vectors in 3D, structured per-pickup info box, crashed snake still yields a spectrum, educator-shareable setup files, cap-as-computational-budget teaching moment.

**Defer (v1.x / v2+):** mode animation, speed scaling, upload-with-fallback workflow, mixed-interaction sets, Raman. **Anti-features (do not build):** live spectrum preview during play, physics relaxation at pickup time (deterministic placement at cited geometry instead), silent stacking fallback, crystal-packing reproduction.

### Architecture Approach

Detail: `.planning/research/ARCHITECTURE.md`. Layered plugin package with a strict dependency direction (**pure ← bridge ← GUI/controller**), enforceable by grep gates. Engine owns game truth; PyMOL coordinates are a projection. All slow work is async off the main thread; all `cmd.*` on the main thread.

**Major components:**
1. **Thin entry (`__init__.py`)** — `__init_plugin__` + `addmenuitemqt`, module-level dialog singleton **anchored outside module globals** (reload trap), modeless `.show()` never `.exec_()`
2. **Pure core** (stdlib-only, WSL-tested): `game_engine`, `stacking`, `cgo_build`, `spectra` (g98.out parser + broadening), `xyzio`, `xtbenv`, `setup_logic`, `molecule_data`
3. **`pymol_bridge.py`** — the single cmd seam: load molecules, `cmd.create` into `srp_*` namespace, translate/transform, `load_cgo`, camera, cleanup-by-prefix
4. **`xtb_runner`** — QProcess (or stdlib worker + queue + QTimer drain): `--ohess` in a per-run temp dir, streaming log, cancel, success contract
5. **`input.py` / Wizard** — arrow-key capture with save/restore + event-filter fallback
6. **Qt UI** — 3-tab modeless dialog (Setup/Game/Spectra) + QPainter `plot_widget` + frequency table

### Critical Pitfalls

Detail: `.planning/research/PITFALLS.md` (12 pitfalls, all with verified prevention; top items):

1. **`-o --hess` silently skips the hessian `[RUN]`** — use `--ohess`; assert `vibspectrum`/`g98.out` exist before declaring success; fixtures committed first
2. **Long xtb runs on the Qt main thread freeze the viewer** — measured phenol 0.67 s / 26-atom dimer 1.75 s `[RUN]`; ~100-atom snake plausibly 30–90 s → QProcess + cancel + re-entrancy guard, never `waitForFinished()`
3. **xtb CWD pollution + stderr-based success detection** — success contract = exit 0 + "normal termination" on stderr + files exist; failure prints diagnostics on stdout with exit 128 `[RUN]`
4. **Arrow keys: frame-step conflict, focus stealing, leaked global rebinds** — wizard event-mask override mandatory; save/restore mappings in every teardown path; "click the 3D viewer" UX; up/down spike
5. **Double-singleton on Plugin-Manager reload** — anchor state outside module globals; adopt-existing-instance defense; built in from Phase 1 (painful to retrofit)

Also load-bearing: modal dialogs freeze the game (refresh + 100 ms singleShot before any modal); stacking clash gate is a **prerequisite for valid xtb input** (a clash makes xtb infer covalent bonds → garbage hessian `[RUN]`-verified safe at 3.4 Å); molecule hygiene gate (explicit H, declared charge, electron-count sanity vs xtb's own log); parser edge cases (5 vs 6 trivial modes for linear vs nonlinear, negative frequencies are real, intensity-0 modes, g98.out 3-column blocks are the mode-vector source).

## Implications for Roadmap

Based on combined research, the recommended phase structure follows ARCHITECTURE.md's dependency-driven A–H build order, with PITFALLS.md's pitfall→phase mapping folded in. Phase letters are kept so PITFALLS.md's mapping stays resolvable.

### Phase 1 (A): Plugin Skeleton + Purity Harness
**Rationale:** Pitfalls 5/7/8/9 (module identity, dialog lifetime, modeless discipline, epoch guards) must be built in from commit one — retrofitting state anchoring after GUI code exists is painful. Also establishes the purity gate that every later phase depends on.
**Delivers:** thin entry, modeless 3-tab dialog shell, `srp_*` naming convention, state anchoring, epoch pattern, repo layout, WSL `python3.6` unittest scaffold + grep gates (no pymol/Qt/numpy at module level in pure modules; no `.exec_()` on the main dialog; no `from PyQt5 import`).
**Avoids:** Pitfalls 5, 6 (pattern), 7, 8, 9 (epoch).
**Human-verify:** plugin loads via plugin path; exactly one dialog.

### Phase 2 (B): Pure Core (No PyMOL Needed)
**Rationale:** every pure module is WSL-testable with zero stubs; the spectra parser can be written immediately against the **committed real fixtures** (`.planning/research/xtb-spike-fixtures/`) — this is the fixtures-first rule from Pitfalls 1/12. The demo-data acquisition + citation-approval track starts **here in parallel** (external lead time, human approvals).
**Delivers:** `game_engine`, `stacking`, `cgo_build`, `spectra` (g98.out primary, vibspectrum fallback; 5-vs-6 trivial modes; negative + zero-intensity handling), `xyzio`, `xtbenv` (xtb/xtb.exe detection), `setup_logic`, `molecule_data` manifest schema — all unit-tested on python3.6.
**Implements:** architecture pure layer; features' interaction-dataset-as-data principle.
**Avoids:** Pitfalls 12 (fixtures), 3 (success contract as pure function).

### Phase 3 (C): Molecules in the Viewer
**Rationale:** the bridge subset and molecule validation are prerequisites for any gameplay; headless smokes prove the cmd seam early.
**Delivers:** load mol2/sdf (native formats verified), `cmd.create` `srp_*` copies, box CGO, camera helpers; **load-time validation gate** (explicit H, declared charge, ≤3 rings — Pitfall 11).
**Depends on:** A, B. **Avoids:** Pitfalls 8 (cleanup semantics), 11.

### Phase 4 (D): Game Loop + Input — *research flag*
**Rationale:** first human-verify of keyboard happens here so failure is cheap. The **up/down arrow spike is scheduled in this phase** (the only genuinely open mechanism question).
**Delivers:** Wizard subclass (event mask = key+special) or `cmd.set_key` with save/restore — spike decides; tick QTimer, countdown with epoch guard, pause/restart, translate movement.
**Depends on:** B, C. **Avoids:** Pitfalls 4, 5 (pause semantics), 9.
**Spike:** up/down bindability + focus behavior; fallback = Qt application-level event filter (also solves dialog-focus stealing).

### Phase 5 (E): Stacking + Game Rules Complete
**Rationale:** this is the playable v1 core; the **clash gate is a game rule, not a spectra afterthought** (a clashing append makes xtb infer covalent bonds → garbage hessian; π-stack at 3.4 Å verified safe `[RUN]`).
**Delivers:** deterministic stacking transforms (pure math, applied via bridge), pickup/collision (segment-based, not atom-overlap — molecules at real spacing are a blob)/score/cap, win + crash completion flow (crash still → spectra), centralized `_teardown_round()` + key-restore, charge aggregation for `--chrg`.
**Depends on:** D. **Avoids:** Pitfalls 9, 10, 4-restore, 11-aggregation.
**Verify during implementation:** `transform_selection` matrix layout (read `editing.py:1946` docstring; fallback = `cmd.rotate`+`cmd.translate`).

### Phase 6 (F): xtb Pipeline — *largely de-risked, calibrate here*
**Rationale:** PyMOL-free, buildable in **parallel with D/E** (only the final-snake handoff touches gameplay). The `--ohess` discovery plus committed fixtures already de-risked the pipeline; what remains is runtime calibration.
**Delivers:** QProcess runner (conda-build smoke first; worker+queue fallback), per-run temp dir + success contract, cancel, atom-budget guard (cap ~10 mol / ~100 atoms, warning), end-to-end headless run snake.xyz → real xtb → files in git-ignored `tmp/xtb_runs/`.
**Depends on:** B. **Avoids:** Pitfalls 1, 2, 3, 6, 11-assert, 12-fixtures.
**Calibrate:** ~100-atom `--ohess` wall time (drives warning thresholds), `OMP_NUM_THREADS`/`OMP_STACKSIZE` `[TRAIN]`-flagged — verify with the real capped snake.

### Phase 7 (G): Spectra UI
**Rationale:** pure parts already tested in B; UI is wiring plus the two verified QPainter precedents.
**Delivers:** `gui_spectra`, QPainter plot widget (curve + stick spectrum + click hit-testing), frequency `QTableWidget` (negatives shown as "−31.9i", intensity-0 rows included) → mode-arrow CGO in the viewer, save plot, streaming progress log, pre-modal redraw discipline.
**Depends on:** E, F. **Avoids:** Pitfalls 12 (table↔vector index match), 2 (streaming + cancel UX), 5.
**Human-verify:** plot-to-PNG save (`QWidget.grab()` unverified in PyMOL's Qt build; fallback QPainter→QImage).

### Phase 8 (H): Demo Sets + Polish
**Rationale:** data ships only after citation pinning + human approval (repo hard rule); polish closes the "looks done but isn't" checklist.
**Delivers:** approved demo-set data pack (SDFs + interaction dataset + DATA_SOURCES.md in bioCHEMeleon format), Save/Load Setup persistence (educator shareable), Randomize, Cleanup robustness (works in a fresh process after session reload), help text (focus + negative-frequency explanations).
**Depends on:** B (manifest schema) + the human-approval track running since Phase 2. **Avoids:** Pitfalls 8 (.pse desync), 4 (leak check), UX table.

### Phase Ordering Rationale

- **Dependency-driven:** B needs nothing; C needs A+B; D needs B+C; E needs D; F needs only B (parallel with D/E); G needs E+F; H needs B + external approvals.
- **Pitfall placement:** the expensive-to-retrofit traps (module identity, epoch, modeless gate, purity gate) are Phase 1; the silent-failure traps (`--ohess`, cwd/stderr, parser fixtures) are Phase 2/6; the interactive traps (keys, focus, teardown) are Phase 4/5.
- **Critical-path insight:** the xtb pipeline (F) and the entire spectra parser are de-risked *now* by the fixture spike — the roadmap can treat spectra as a low-uncertainty track rather than a research gamble.
- **External lead time:** demo-set data (distances from COD CIFs / Janiak full text, then human approval) has the longest non-code lead time → starts at Phase 2, lands in Phase 8 (one fully-verified set for MVP).

### Research Flags

Phases likely needing a spike or deeper research during planning:
- **Phase 4 (input):** up/down `set_key` redefinability + Wizard event-mask behavior + focus stealing — the one open mechanism question; spike + human verify, event-filter fallback already designed
- **Phase 6 (xtb):** only calibration remains (QProcess-in-conda smoke, ~100-atom wall time, OMP env `[TRAIN]`) — no open design questions
- **Phase 5 (stacking):** `transform_selection` matrix convention (read docstring; verified fallback exists); non-π stacking modes' opt-stability UNVERIFIED — only π-stack proven `[RUN]`; PROJECT.md already requires research + user approval per mode

Phases with standard patterns (skip research-phase):
- **Phase 1** (bioCHEMeleon-verified skeleton patterns), **Phase 2** (pure logic + committed fixtures), **Phase 3** (verified cmd APIs + smoke harness), **Phase 7** (verified QPainter precedents; parser already fixture-driven), **Phase 8** (persistence + attribution formats verified)

Not a research item but a workflow constraint: **demo-set data approval runs in parallel from Phase 2** and is blocked on human decisions, not code research.

## Open Decisions for the Human

These gate the roadmap and specific phases:

1. **2D-plane vs 3D gameplay** — research recommends **2D + locked camera for v1** (arrow keys map 1:1 to directions — cleanest given verified Left=100/Up=101/Right=102/Down=103 codes; 3D doubles steering ambiguity and complicates collision + stacking). 3D remains possible later (PgUp/PgDn special codes verified) but only with explicit approval. *Decision needed before Phase 2 (engine geometry).*
2. **Stacking-mode fallback policy** — silent fallback is forbidden (educational tool teaching a made-up distance is worse than one that refuses). Options: skip pickups without verified data, or an explicit user-approved fallback list (e.g. generic vdW contact). *Open requirements question; v1.x trigger.*
3. **Demo-set selection** — four proposals, all molecule CIDs VERIFIED live (PubChem): **Set A** aromatic π-stack (benzene/naphthalene/anthracene/phenanthrene/biphenyl), **Set B** carboxylic-acid H-bond dimers (formic/acetic/benzoic acid), **Set C** heteroaromatics (pyridine/pyrazine/furan/thiophene/triazine/imidazole — Janiak 2000 is specifically on-point), **Set D** hydroxyl H-bond chains (phenol/hydroquinone/urea). MVP recommendation: **one set fully verified (A or B)** beats three done loosely. *Decision needed before the data-prep track.*
4. **π-stack distance numbers UNVERIFIED** — the commonly quoted "3.3–3.8 Å" range: upper bound 3.8 Å VERIFIED via Janiak abstract; **3.3 Å lower bound and the prescribed 3.4 Å game value are UNVERIFIED** until pinned from Janiak full text (RSC 403'd during research) or measured from a COD CIF. Same for COOH dimer O···O (~2.6–2.7 Å UNVERIFIED), imidazole N–H···N, O–H···O chains, C–H···N contacts. Every shipped number: pinned at data-prep → human approval. *Gates Phase 8.*
5. **Movement/speed model** — speed increase with snake length is a genre convention (Wikipedia-verified) but deferred to v1.x pending playtesting; constant speed for v1 unless the user overrides.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Every core claim verified against `pymol-src` (file:line), bioCHEMeleon prior art, or live xtb runs; residual LOWs (exact runtime Python/Qt versions, QProcess conda smoke) affect niceties only |
| Features | MEDIUM-HIGH | Genre conventions and chemistry data sources HIGH (live-verified); **specific stacking distance numbers MEDIUM/UNVERIFIED** pending data-prep + human approval |
| Architecture | HIGH | All patterns verified in-repo (bioCHEMeleon, Pymol-script-repo, pymol-src); flagged MEDIUM-LOW items (up/down keys, transform matrix layout, plot save, 100-atom timing) each have a designed fallback and a phase assignment |
| Pitfalls | HIGH | Core pitfalls empirically verified (`[RUN]` xtb spikes executed today; `[SRC]` source reads); `[TRAIN]` items explicitly marked and mapped to Phase 6 verification |

**Overall confidence:** HIGH — unusual for greenfield, because every load-bearing mechanism was verified against local sources and the riskiest external dependency (xtb) was exercised empirically, with fixtures committed.

### Gaps to Address

- **Stacking distance numbers (π-stack 3.4 Å game value, COOH O···O, H-bond chains):** UNVERIFIED — pin from Janiak 2000 full text or COD CIF measurements at data-prep; human approval before shipping. Handles via the Phase-2-started approval track.
- **Up/down arrow key binding:** docstring omits, shortcut manager reserves, but validation code accepts — Phase 4 spike + human verify; event-filter fallback designed.
- **QProcess in the Windows conda PyMOL build:** unverified — one-line smoke at Phase 6 start; worker+queue+drain fallback is verified.
- **`transform_selection` matrix argument layout:** existence verified, layout not read — Phase 5 implementation detail; `cmd.rotate`+`cmd.translate` fallback.
- **Plot-to-PNG save (`QWidget.grab()`):** standard Qt, unverified inside PyMOL's Qt build — human verify Phase 7; QPainter→QImage fallback.
- **~100-atom `--ohess` wall time + OMP env:** extrapolated from measured small runs — Phase 6 calibration with the real capped snake; drives cap-warning thresholds.
- **Non-π stacking opt-stability:** only π-stack verified `[RUN]` (GFN2 preserved the 3.40→3.44 Å stack) — per-mode research + user approval per PROJECT.md before any non-π mode ships.
- **Per-CID PubChem 3D conformer coverage:** benzene verified; others presumed — confirm at data-prep.
- **WSL purity vs numpy:** resolved by rule — pure modules stdlib-only at module level (WSL python3.6 has no numpy, verified); numpy allowed as lazy import inside functions on the Windows runtime side; broadening is fine in pure `math` at serpentrum scale.
- **AA-match purity-gate details:** user deferred direct inspection ("no need for aa-match") — gate adapted from its documented description + bioCHEMeleon's proven test patterns; reminder logged to revisit AGENTS.md/spec.md AA-match references later.
- **Runtime Python/Qt exact versions:** LOW-impact niceties — one-line headless print whenever convenient.

## Sources

Aggregated from the four research files (full per-file citation lists with file:line references in STACK/FEATURES/ARCHITECTURE/PITFALLS.md).

### Primary (HIGH confidence — verified in this repo/environment)
- **`pymol-src` PyMOL 2.5.0 source** — plugin loading/identity, Qt bindings, key mapping/dispatch, Wizard C-layer, CGO constants, movement APIs, chempy format parsers (file:line verified)
- **`tmp/bioCHEMeleon`** — the author's prior PyMOL game plugin: QTimer loop, modeless discipline, worker+queue+drain, wizard lifecycle, purity gates, DATA_SOURCES.md format
- **`Pymol-script-repo`** — plugin precedents: `dynoplot.py` (QPainter plot), `optimize.py`, `outline.py`, `filter.py`/`density.py` (key bindings)
- **Live xtb 6.7.1pre runs `[RUN]` (2026-09-06)** — `-o --hess` vs `--ohess` comparison, phenol/CO₂/π-stacked-dimer outputs, exit-128/stderr contract, timings; **committed fixtures at `.planning/research/xtb-spike-fixtures/`**
- **Live chemistry-database checks (2026-09-06)** — PubChem PUG REST (CID lookups + 3D SDF download VERIFIED), COD (formula search VERIFIED; per-entry CIF inspection pending), CCDC Access Structures (page verified; licensed for bulk), Crossref/OpenAlex/Semantic Scholar (DOI registry VERIFIED)

### Secondary (MEDIUM confidence — existence verified, details pending full text)
- Janiak 2000, *J. Chem. Soc., Dalton Trans.*, DOI 10.1039/b003010o — π-stacking rules VERIFIED via abstract; body text inaccessible (403); 3.3 Å lower bound UNVERIFIED
- Hunter & Sanders 1990, *JACS*, DOI 10.1021/ja00170a016 — model existence VERIFIED (~5,000 cites); details not read
- Arunan et al. 2011 IUPAC H-bond definition, DOI 10.1351/PAC-REC-10-01-02 — existence VERIFIED; numeric criteria not read
- Snakeleev, *J. Chem. Educ.* 2025, DOI 10.1021/acs.jchemed.5c00029 — abstract VERIFIED (Cohen's d 1.23–2.67; >90% engagement); Foldit, *Nature* 2010, DOI 10.1038/nature09304
- Wikipedia "Snake (video game genre)" — genre conventions

### Tertiary (LOW confidence — `[TRAIN]`, validate before relying)
- `OMP_NUM_THREADS` capping / `OMP_STACKSIZE` for large-system hessians — `[TRAIN]` MEDIUM/LOW; verify in Phase 6
- `cmd.h_add` unreliability for arbitrary organics — `[TRAIN]` MEDIUM; moot (policy is never auto-add H)
- Herringbone crystal packing of neat benzene/naphthalene/anthracene — UNVERIFIED; design implication (idealized pairwise geometry, labeled as such) holds regardless

---
*Research completed: 2026-09-06*
*Ready for roadmap: yes*
