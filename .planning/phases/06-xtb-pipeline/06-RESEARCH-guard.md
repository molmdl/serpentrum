# Phase 6: xtb Pipeline — Guard + Integration Surfaces - Research

**Researched:** 2026-09-24
**Domain:** pre-launch atom-budget guard (SPECTRA-06), final-snake -> XYZ export, Phase 7 handoff seams
**Half covered:** SPECTRA-06 guard + run input + Phase 7 handoff. NOT covered: the async runner mechanics (QProcess smoke / drain / cancel) — those gate via the ROADMAP's QProcess-in-conda smoke (`.planning/ROADMAP.md:226`).
**Confidence:** HIGH for every code-contract claim (all verified against live repo code with file:line); MEDIUM explicitly flagged for the N^3 cost model extrapolation and the optimized-vs-game-geometry vector-overlay detail.

## Summary (up front)

The seams this half needs are **already frozen by prior phases** — most importantly Phase 5 plan 05-15, whose SUMMARY pins the Phase 6/7 consumption contract verbatim (`.planning/phases/05-stacking-game-rules/05-15-SUMMARY.md:105`): `_serpentrum.last_run = {'result','molecules_stacked','atoms_total','chain_objects','snake_id'}` — counts for the SPECTRA-06 re-check, `chain_objects` for the viewer-extraction .xyz handoff, `snake_id` for run bookkeeping. Phase 6 should implement guard + export + launch-API against exactly this record and not invent a parallel channel.

Two load-bearing verification findings change the guard design:

1. **WARN-NOT-BLOCK is structurally mandatory.** A default-parameter WIN snake (set_a molecules, 12-24 atoms each, `serpentrum/data/manifest.json`) routinely exceeds `atom_budget=100` (win = 10 stacked + head = 11 molecules => 130-260 atoms). The in-run budget warning is already "never a hard stop" (`serpentrum/game_engine.py:719-724`: fires once, run continues), and SETUP-06's Setup-tab precedent shows warnings never block Apply (`serpentrum/gui_setup.py:369-373` status label, `:574-575` appended to success message; `QMessageBox.warning` reserved for errors). SPECTRA-06 wording is "exceeding it shows a **warning**" (`.planning/REQUIREMENTS.md:55`). The guard warns and lets the run proceed.

2. **`atoms_total` EXCLUDES the head** (pinned: `tests/test_phase5_integration.py:267-273` "atoms_total == sum of the captured pickups' atoms_n (head excluded -- engine counters never include the head)"), yet `hud_logic.completion_lines` labels it `'atoms: %d (spectra input size)'` (`serpentrum/hud_logic.py:189`, expected literal pinned in `tests/test_hud_content.py:172,180`). The completion HUD therefore under-reports the true xtb input size by the head's atom count. **The guard must count head-inclusive atoms from what will actually be run** — i.e. from the viewer chain objects it is about to export — and must not reuse `last_run['atoms_total']` as the full truth.

**Primary recommendation:** Phase 6 adds three seams — (a) a PURE guard function `(snake_molecules, snake_atoms, setup) -> [warning strings]` reusing `setup_logic.HESSIAN_WARNING`, (b) a BRIDGE export `pymol_bridge.chain_xyz(chain_object_names) -> (elements, coords)` via `cmd.get_model` feeding `xyzio.write_xyz`, (c) a launch API hooked INSIDE `gui.py._on_spectra_requested` (the composition root, already wired by Phase 5) that runs the re-check, logs any warnings, and then hands the exported XYZ + run dir to the runner. Everything else Phase 7 needs (parse/broaden input formats, artifact paths, live-state anchor shape) flows from the frozen seams documented below.

---

## Q1. Guard inputs: where do the hidden molecule/atom counts live at completion time?

**Evidence (Phase 5 completion path, HIGH):**

- `_present_completion(engine)` runs after teardown on BOTH win and crash (`serpentrum/gui_game.py:1291-1333`; win/crash share the IDENTICAL path — locked decision 8, docstring inline).
- It anchors `_serpentrum.last_run = {'result': engine.result, 'molecules_stacked': engine.molecules_stacked, 'atoms_total': engine.atoms_total, 'chain_objects': pymol_bridge.chain_object_names(), 'snake_id': 'run_%d' % session['epoch']}` (`serpentrum/gui_game.py:1326-1331`; anchor slot documented at `serpentrum/__init__.py:39-43` "written at completion, consumed by the Spectra stage (Phases 6/7)"). Reload-safe: the anchor object survives Plugin-Manager reload because it lives on `pmg_tk.startup` (`serpentrum/__init__.py:10-48`). It does NOT survive a `.pse` reload (`.planning/research/PITFALLS.md:203`: viewer objects survive, no plugin Python state).
- Engine counters: `molecules_stacked` and `atoms_total` count CAPTURED pickups only (`serpentrum/game_engine.py:714-716`: `molecules_stacked += 1; atoms_total += pickup['atoms_n']`; rolled back on refuse via `reject_pickup` `:809`). Head excluded — pinned by `tests/test_phase5_integration.py:267-273`.
- Per-molecule atom counts ARE persisted from load time: setloader records carry `'atom_count'` from the molfile parse, cross-checked against the manifest (`serpentrum/setloader.py:108-109,210`; schema validated in `serpentrum/molecule_data.py:154-157`). The live records list is anchored at `_serpentrum.records` (`serpentrum/__init__.py:32-35`). BUT: `last_run['chain_objects']` names (`srp_head`, `srp_seg_<n>` — `serpentrum/gui_game.py:975-976`) carry ORDER, not molecule ids, so records-based counting cannot reconstruct per-molecule contributions post-hoc without the session's `stacked_history` (which dies with the session).
- Molecular count incl. head = `len(engine.segments) + 1` as used by the completion HUD (`serpentrum/gui_game.py:1321`).

**Conclusion:** Two count channels exist: (a) `last_run` engine counters — molecule count exact but head-excluded (`molecules_stacked` = stacked only; the completion HUD adds +1), atom count head-EXCLUDED; (b) the viewer chain objects named in `last_run['chain_objects']` — counting atoms there (BRIDGE class, `cmd.get_model`/`count_atoms` per object) counts EXACTLY what the export will ship to xtb, is reload-desync-proof against the engine counters, and includes the head. **The guard should compare its cap against channel (b), with channel (a) as a consistency cross-check (a mismatch = desync warning, not a new cap decision).** The pure math (summation + comparison) is PURE; the counting read is BRIDGE.

## Q2. Guard semantics: warn vs block; molecule cap vs atom cap; win-cap interplay

**SETUP-06 precedent (HIGH):** `setup_logic.validate()` returns `(errors, warnings)` — never raises for invalid input (`serpentrum/setup_logic.py:203-224`). The single warning is `HESSIAN_WARNING = 'hessian cost scales ~N^3; a ~100-atom snake may take 30-90 s'`, fired when `win_cap_molecules > 10 OR atom_budget > 100` (`:114-119,271-277`). At the Setup tab, warnings never block: `gui_setup.py` errors -> modal + abort (`:462-464`) but warnings only decorate the status label / success message (`:369-373,574-575`), and `save_setup` explicitly serializes despite warnings (`setup_logic.py:285-293` "warnings do NOT block save").

**Win-cap interplay (HIGH, decisive):**
- Win condition: `molecules_stacked >= cap` -> `('won',)`, `finished=True` (`serpentrum/game_engine.py:726-731`). `molecules_stacked` therefore never exceeds `win_cap_molecules` — it stops AT the cap (a refused capture at cap un-finishes and play resumes, `tests/test_phase5_integration.py:507-526` G2 contract). PROJECT scope states the player-facing rule as "win when snake length exceeds the cap" (`.planning/PROJECT.md:30`) — physical chain length incl. head = `molecules_stacked + 1` = `cap + 1` at a win.
- In-run atom-budget warning: fires ONCE when `atoms_total > atom_budget` and play continues — "Budget warning: once per run, never a hard stop" (`game_engine.py:719`'s inline comment at `:720-724`); text is COUNT-FREE by GAME-04 (`hud_logic.budget_text()`, `serpentrum/hud_logic.py:127-131`).
- Therefore at default settings (`win_cap_molecules=10`, `atom_budget=100`, `serpentrum/data/manifest.json` 12-24 atoms/molecule), a WIN snake can carry well over 100 atoms. **A blocking guard would make the default win path un-runnable.** Guard = warn-and-proceed. This matches SPECTRA-06's wording ("with a warning if exceeded", `.planning/REQUIREMENTS.md:55`) and the setup_logic docstring contract: "The win-cap/atom-budget warning here is the PURE half of SETUP-06 / SPECTRA-06; the actual pre-xtb re-check lives in Phase 6's runner" (`serpentrum/setup_logic.py:15-16`).

**Which cap triggers what (recommendation, grounded in the above):**
- `atom_budget` is the ONLY hessian-cost knob the caps table carries (`validate()` doc: atom_budget has no hard max — "see warning", `setup_logic.py:214`). `snake_atoms > atom_budget` -> hessian-cost warning (reuse `HESSIAN_WARNING`, see Q3).
- `win_cap_molecules` cannot be "exceeded" by a legal run (win freezes at the cap). A molecule-count re-check is the SPECTRA-06 "hidden counts re-checked" consistency leg — surface actual counts at launch (they are revealed at completion anyway, GAME-09/`hud_logic.py:180-189`), and treat `len(chain_objects) != molecules_stacked + 1` as a DESYNC signal (stale chain after a partial scene), not a policy violation.

## Q3. Guard shape: the PURE function

House pattern (HIGH): pure display/builder functions whose callers inject data —
`hud_logic.stack_mode_note(records) -> line|None` (`serpentrum/hud_logic.py:134-156`), `speed_note(tier_name, speed)` (`:159-177`), `completion_lines(...)`, `budget_text()`. GUI logs once; the pure layer composes sentences, never reads viewers or setup directly (speed_note: "hud_logic only renders sentences and never imports setup_logic", `:171-174`).

Proposed shape (planner refines naming/placement):

```
# PURE (stdlib-only, python3.6 %-formatting)
def launch_budget_warnings(snake_molecules, snake_atoms, win_cap, atom_budget):
    """SPECTRA-06 pre-launch re-check -> list of ONE-LINE warning strings
    ([] = clean). Never raises; never blocks — warn-and-proceed (Q2).
    Counts are HEAD-INCLUSIVE (the true xtb input size; last_run
    atoms_total is head-excluded, test_phase5_integration.py:267-273).
    """
```

Behavior contract pinned by precedent:
- Atom overage carries the REVEALED counts (game is over; GAME-04's count-free rule applied to play only — `completion_lines` reveals counts at completion, `hud_logic.py:180-189`) suffixed to the `HESSIAN_WARNING` literal reused verbatim from `setup_logic.py:118-119` so SETUP-06 and SPECTRA-06 wording never drift (drift-pin precedent: `test_module_constants_guard_against_drift`, `tests/test_xtbenv.py:298`; `XTB_OHESS` guarded constant, `xtbenv.py:34`).
- Returns data, not exceptions (validate()'s "errors are DATA, not exceptions" contract, `setup_logic.py:205-206`).
- Placement: a guard builder fits `hud_logic`-style builder modules; the cap literals come from the CALLER passing `setup` values (never re-read setup inside the builder — the speed_note precedent). Do NOT extend `setup_logic.validate()` — that function validates CONFIG at edit time; the re-check validates the RUN at launch time (setup_logic:15-16 already assigns the runtime half to Phase 6's runner).

## Q4. Snake -> XYZ export: coordinate source

**Verified seam (HIGH):** `move_head_delta`/`move_chain_delta` use atomic-coordinate `cmd.translate(..., camera=0)` "so atomic coords stay = engine truth (Phase-5 xtb coord handoff)" (`serpentrum/pymol_bridge.py:165-172`, comment names this exact handoff). Per tick the viewer objects and the pure mirrors move by the SAME engine delta (`serpentrum/gui_game.py:649-667`; head mirror kept equal in pure math, no readback). Engine segment atoms likewise train-follow/rotate in pure math (`game_engine.py:471-520,544-552`). Both channels are drift-free-truthful at completion.

**Authoritative source = the viewer objects, via `pymol_bridge.chain_object_names()`:**
- The 05-15 handoff contract freezes it: "chain_objects for the viewer-extraction .xyz handoff" (`.planning/phases/05-stacking-game-rules/05-15-SUMMARY.md:105`).
- `chain_object_names()` already exists and returns sorted `srp_head`/`srp_seg*` public-object names; "Completion-ONLY read (framing / xyz handoff)" (`serpentrum/pymol_bridge.py:443-455`). It is the export's membership list AND comes from `last_run` — reload-safe by construction (works even after Plugin-Manager reload; engine/session mirrors do not).
- No coord-reading helper exists yet in the bridge (grep: only `get_extent` is used; `get_extent/get_model are safe` noted at `pymol_bridge.py:320-323`). New BRIDGE function needed, e.g. `chain_xyz(names) -> (elements, coords)` via `cmd.get_model(name)` reading each atom's symbol + coord — pure concatenation, zero math. ARCHITECTURE's researched spectra flow already specifies exactly this: "1. extract final snake coords (cmd.get_coordset / get_model)" and the state-ownership map pins "get_coordset only at spectra handoff" (`.planning/research/ARCHITECTURE.md:258, ~290`).
- Element symbols come from the SDF-loaded objects (demo set + uploads load via `cmd.load`, e.g. `reload_head`/`materialize_pickup`, `pymol_bridge.py:363-419`) — symbols are present in the model; `xyzio.write_xyz` validates counts; symbol legality is enforced on READ (`xyzio.py:88-89` + `read_xyz_text:157-160`), so an exported junk symbol would be caught on any re-parse and by xtb itself — an optional belt-and-braces self-check is `xyzio.read_xyz_text(write_xyz(...))` in the launch API before launch.
- Comment-line house style: free text, sanitized of newlines by the writer (`xyzio.py:96`); tests use short human labels (`tests/test_xyzio.py:50,85,111,122`). Recommend comment carrying `snake_id` (e.g. `'serpentrum snake run_3'`) — free-form, no parser impact.

## Q5. Phase 7 handoff contract: what Phase 6 must freeze

**(a) Per-run dir contents.** An `--ohess` run sprays (`PITFALLS.md:82` measured set + committed fixtures in `.planning/research/xtb-spike-fixtures/`): `g98.out`, `vibspectrum` (the two consumed), plus `hessian`, `xtbopt.xyz`, `xtbopt.log`, `xtbrestart`, `charges`, `wbo`, `xtbtopo.mol`, `.xtboptok`. Consumed by `spectra.py`: ONLY `g98.out` (atoms + freqs + intensities + per-atom vectors — F21, `ARCHITECTURE.md:37` Proven-facts table) with `vibspectrum` as the freq/intensity fallback (no vectors — `spectra.py:315-322`; Pitfall 12.4 `PITFALLS.md:295`). Everything else is debris. `xtbenv.EXPECTED_FILES = ('g98.out', 'vibspectrum')` (`serpentrum/xtbenv.py:39`) is the success contract — verbatim reuse.
- `run_dir = xtbenv.new_run_dir(base_dir)` (`xtbenv.py:194-207`; `srp_`-prefixed `mkdtemp`). `base_dir` ownership is unassigned today — recommend the runner resolve it from `tempfile.gettempdir()` INSIDE Windows PyMOL (never a `/mnt/c/...` path at runtime: anti-pattern STATIC `STACK.md:168`; never the PyMOL session dir: `xtbenv.py:203-205`, `PITFALLS.md:82` stale-vibspectrum trap).
- `xtbenv`'s own scope note says the runner "owns ... copying g98.out / vibspectrum out, and deleting it afterwards" (`xtbenv.py:201-203`). **Freeze decision needed (open question #1 below):** keep the copied artifacts (g98.out, vibspectrum, input snake.xyz, and — needed for Phase 7's vector overlay decision — `xtbopt.xyz`, the optimized geometry whose Standard-orientation atom block g98 carries) until the NEXT run replaces them; a now-delete would strand Phase 7's parser.

**(b) Run record / live-state anchor.** Precedent: a new attribute on `_SerpentrumState` in `serpentrum/__init__.py` (exactly how `records`, `stacking_data`, `last_run` landed, `:32-43`). Never module globals, never a second singleton (`PITFALLS.md:177-190` Pitfalls 7/8). Suggested frozen shape for Phase 7:
```
state.spectra_run = None | {
    'snake_id': str,            # from last_run
    'xyz_path': str,            # exported input (kept)
    'g98_path': str | None,     # copied-out artifact
    'vibspectrum_path': str | None,
    'status': 'idle'|'running'|'ok'|'failed'|'cancelled',
    'problems': [str],          # from xtbenv.evaluate_run RunVerdict
    'log': [...] or log_path    # drained stdout/stderr tail for SPECTRA-04
}
```
SPECTRA-04's log streaming consumes the runner's stdout/stderr drain (`.planning/ROADMAP.md:236` Phase 7 SC1: progress streams live into the log panel) — Phase 6 must emit line events from the drain/QProcess read; Phase 7 renders them. Freeze the EVENT vocabulary (lines, done-with-verdict) not the widget.
**(c) Parser/broadener input formats (HIGH, already frozen by Phase 2):**
- `spectra.parse(path)` — format-sniffing dispatcher; documented default: "the Phase-6 runner tries g98.out first and falls back to vibspectrum" (`serpentrum/spectra.py:478-506`). Explicit `parse_g98(path)` / `parse_vibspectrum(path)` exist (`:298-301,396-399`).
- The g98 atom block is the OPTIMIZED geometry's Standard orientation keyed by atomic number (`spectra.py:100-157`) and its ` Atom AN` header sizes the displacement rows (`:57,204-218`) — so the runner MUST run xtb on the snake's OWN xyz or the g98 atom block / vector rows cannot match the snake (n_atoms mismatch = loud parse failure, `spectra.py:133-148,222-247`).
- `broaden(modes, fwhm=16.0, x_min=0.0, x_max=None, n_points=800)` (`:433-475`); `real_modes(spectrum, threshold=10.0)` (`:402-418`). `fwhm` comes from `setup['broadening_fwhm']` (default 16.0, `setup_logic.py:57`).
- Phase 7 vector overlay (click row -> arrows, `ARCHITECTURE.md:271` `cgo_build.mode_arrows(atoms, vecs, scale)`): g98 atoms/vectors are in the OPTIMIZED frame, the viewer snake is the GAME frame — they diverge after `--ohess`'s ancopt stage. Flagged as MEDIUM-confidence design gap (Phase 7 owns it); Phase 6 needs only to PRESERVE `xtbopt.xyz` alongside g98.out so Phase 7 has the optimized frame available without a re-run.

**Re-entrancy:** Get Spectra is enabled ONLY by `_present_completion` and re-disabled on every teardown (`gui_game.py:1333,1388`); PITFALLS 2 explicitly prescribes "disable the Get-Spectra button while a run is in flight" (`PITFALLS.md:66-68`). ROADMAP SC2 requires "no double-runs" (`.planning/ROADMAP.md:222`). The launch API must own this disarm.

## Q6. Warning UX surface in Phase 6 (no Spectra tab yet)

Phase 5's pattern for shipping not-yet-UI'd behavior: PURE builders + BRIDGE helpers + a Qt signal wired only to a placeholder surface — then the anchor record documents the future consumer (`serpentrum/gui_game.py:312-349` button+signal; `serpentrum/gui.py:74-77,101-110` model-A switch to the placeholder page; `serpentrum/__init__.py:39-43`). Phase 6's equivalent:

1. PURE guard (Q3) — exists standalone, unit-tested (Q8).
2. BRIDGE export `chain_xyz(...)` (Q4) + run-input writer (`xyzio.write_xyz_file` into `new_run_dir`) — standalone, smoke-verified.
3. Launch API at the COMPOSITION ROOT: extend `PluginDialog._on_spectra_requested` (`serpentrum/gui.py:99-110`), which today only does `tabs.setCurrentIndex(2)`. Phase 6 interposes: read `last_run` -> bridge-count/export -> PURE guard -> log warnings INTO THE GAME-TAB INFO BOX (it remains visible and is the established one-line-log channel; Phase 7 owns the future Spectra log) -> kick the runner -> disarm Get Spectra. The GameTab -> Dialog `spectra_requested` signal contract DOES NOT CHANGE (locked decision 9 / model-A, `gui.py:99-110` docstring).
4. Bottom 6-button row (Phase 8, SETUP-07/08): the reserved layout already exists empty at `serpentrum/gui.py:78-81` (`buttons.addStretch(1)`; buttons land in Phase 8 per `.planning/ROADMAP.md:250` and `.planning/research/FEATURES.md:105`, ARCHITECTURE's designed row `ARCHITECTURE.md:94`). **Phase 6 adds NOTHING to this row** — guard output goes to the info box / future Spectra log, never new bottom buttons.
5. Modal discipline: any warning must not be a blocking QMessageBox mid-flow without pause-rebase care (`PITFALLS.md:134`); the game is over at launch time (post-completion), so the modal freeze risk is moot — but warn-and-proceed semantics argue for log lines, not a gate dialog. If the planner wants a confirm-on-megasnake dialog, it is a GUI-class QMessageBox child (allowed, no `.exec_()` — AST purity gate, repo AGENTS.md) and must be an explicit scope line.

## Q7. Calibration inputs + claim hygiene

- **Verified [RUN] cost measurements:** phenol 13 atoms `--ohess` 0.67 s wall / 0.28 s hessian; 26-atom pi-dimer 1.75 s / 1.03 s (`PITFALLS.md:56-60`). The "~N^3" scaling is the eigensolver cost MODEL; the PROJECT cap is "~10 molecules / ~100 atoms" (`.planning/PROJECT.md:71` decision row "Hessian cost grows ~N^3; atom guard runs before xtb"). The "30-90 s" projection for ~100 atoms is EXPLICITLY MEDIUM confidence ("extrapolation", `PITFALLS.md:71`; `SUMMARY.md:67`). `HESSIAN_WARNING` hardcodes the 30-90 s wording (`setup_logic.py:118-119`) — calibration (SC5, `.planning/ROADMAP.md:225`) may justify editing that literal + pins in `tests/test_setup_logic.py`; treat as an owner-visible diff (speed-tier precedent, `setup_logic.py:99-106`).
- **What SC5 actually tunes:** the warning THRESHOLD is `atom_budget` (existing key; default 100, `setup_logic.py:56`). No new schema key is needed for the guard — `merge_defaults` (`setup_logic.py:138-156`) is the proven backcompat seam IF calibration motivates any new key, but prefer constants + a research-note update over schema churn. OMP env (`OMP_NUM_THREADS` cap / `OMP_STACKSIZE`) is `[TRAIN]`-flagged unverified (`SUMMARY.md:111,197`; `PITFALLS.md:333,431`) — it lives in the runner's env-dict build (runner half), NOT in the guard. Distinguish in plans: VERIFIED = the two measured points + success-contract files; ASSUMED = N^3 exponent specifics, 30-90 s range, OMP necessity.

## Q8. Test seam (python3.6, zero stubs)

- Convention: `tests/` has NO `__init__.py` (plugin-path safety, enforced by run_gates gate 1); every test file self-inserts the repo root on `sys.path`; discovery `python3.6 -m unittest discover -s tests -p "test_<name>.py" -v`; fixtures read IN PLACE from `.planning/research/xtb-spike-fixtures/` (`tests/test_xtbenv.py:1-21,30-34`). Dependency-injection over sys.modules stubs everywhere (e.g. `detect_binary(which_fn=...)`, `xtbenv.py:141-167`).
- New pure tests: `tests/test_<guard>.py` covering: clean run -> `[]`; atoms over budget -> exactly the HESSIAN_WARNING-carrying line WITH revealed counts; molecule-count desync -> desync line; non-numeric/None inputs never crash (validate()'s bool-is-int trap precedent, `setup_logic.py:175-179`). No stubs needed — signature is `(ints, ints, ints, ints) -> [str]`.
- Counting math (head-inclusive summation over per-object atom counts) can be tested pure by injecting an `atom_count_fn(name) -> int` callable (detect_binary's `which_fn` precedent) with a fake dict — keeps the BRIDGE thin and the policy WSL-testable.
- Existing suites to extend, NOT duplicate: `tests/test_xtbenv.py` (contract pins), `tests/test_xyzio.py` (writer). Phase 3's counting tests are the `tests/test_molfile.py`/`test_setloader.py` family (`setloader.py:143` atom_count cross-checks) — the guard reuses their validated `atom_count` fields; no new counting function may be written (see dont_hand_roll).
- The bridge export half is smoke-only (Windows PyMOL): new `smoke/09_chain_xyz_smoke.py` in the `smoke/` series pattern (01-08 exist; SMOKE-OK sentinel verdict, never exit codes — repo AGENTS.md gates); purity gates (`tools/check_purity.py:62-75`) must be re-run: new GUI module => add to `GUI_MODULES` only if Qt-touching (NOT expected); bridge additions stay inside `pymol_bridge.py` (already BRIDGE).

## Open questions for the planner

1. **Artifact lifetime.** Keep g98.out/vibspectrum/snake.xyz/xtbopt.xyz copied out of the run dir until the next run replaces them (recommended), or delete at xtb completion per `xtbenv.py:201-203`'s "deleting it afterwards" note? The note predates Phase 7's needs; Phase 7's parser/vector overlay consumes artifacts AFTER the run ends. Decide per-run dir vs stable per-snake dir (`snake_id`-keyed).
2. **Launch UX for an over-budget snake.** Log-lines-only (recommended, matches SETUP-06 warn-and-proceed precedent + avoids modal mid-flow, `PITFALLS.md:134`) vs a confirm dialog ("N atoms > budget 100; run may take ~30-90 s. Proceed?"). A dialog is GUI-class QMessageBox-child legal but is a scope decision — currently NOTHING in the requirements demands confirmation.
3. **Desync leg severity.** If `len(chain_objects) != molecules_stacked + 1` (stale scene / partial cleanup / `.pse` reloaded scene with chain but `last_run is None`): warn-and-launch anyway, or refuse launch with a 'rebuild the scene' line? Note `.pse` semantics (`PITFALLS.md:203-207`): chain objects CAN outlive plugin state entirely — a fresh process can legitimately have a chain and no `last_run`; guard against None-record crashes at minimum.
4. **Guard module placement.** New small PURE module (e.g. `budget_guard`-style) vs appending builder functions to `hud_logic.py` (its SPECTRA-06 stake is documented at `hud_logic.py:181` docstring). Both are purity-legal; the house pattern favors a small focused module once a function family exceeds ~2 builders.
5. **Runner env (runner-half dependency).** The guard needs nothing from SC5's calibration beyond possibly an edited `HESSIAN_WARNING` literal + re-pinned `tests/test_setup_logic.py` tuples; OMP belongs to the runner env dict, out of this half.

## dont_hand_roll (existing code that MUST be reused)

| Need | Reuse | Why |
|------|-------|-----|
| Cap constants + defaults | `setup_logic.DEFAULTS['win_cap_molecules'] / ['atom_budget']` (`setup_logic.py:55-56`) | single source; `validate()` range rules pinned |
| Hessian warning text | `setup_logic.HESSIAN_WARNING` (`setup_logic.py:118-119`) | SETUP-06 wording parity; drift pinned by tests |
| Caps validation | `setup_logic.validate()` (never-raises, `:203-279`) | launch API hand-rolls nothing about setup legality |
| Per-molecule atom counts at load | setloader records' `atom_count` (`setloader.py:108-109,210`; schema `molecule_data.py:154-157`) | manifest-cross-checked already |
| Chain membership / names | `pymol_bridge.chain_object_names()` (`pymol_bridge.py:443-455`) | completion-only, reload-safe, frozen by 05-15:105 |
| In-run + completion counts | engine `molecules_stacked`/`atoms_total`; `hud_logic.completion_lines` (`game_engine.py:714-731`, `hud_logic.py:180-189`) | counters already hidden-in-play/revealed-at-completion |
| XYZ write/read | `xyzio.write_xyz / write_xyz_file / read_xyz_text` (`xyzio.py:81-178`) | fixture-proven, symbol validation, newline-safe comment |
| Run contract + run dir | `xtbenv.evaluate_run / detect_binary / build_argv / new_run_dir` (`xtbenv.py:51-207`); `EXPECTED_FILES`, `XTB_OHESS` | 3-leg contract fixture-pinned; list-argv quote safety; bare-relative cwd contract |
| Spectra parse/broaden | `spectra.parse / parse_g98 / parse_vibspectrum / real_modes / broaden` (`spectra.py:285-505`) | Phase 2 frozen input formats for Phase 7 |
| Live-state anchor | `_serpentrum` via `_anchor()` (`__init__.py:10-48`; add attribute to `_SerpentrumState`) | reload-safe singleton; NEVER module globals |
| Handoff record shape | `_serpentrum.last_run` 5-key dict (`gui_game.py:1326-1331`; 05-15-SUMMARY.md:105) | frozen contract — extend via NEW attribute, don't reshape |
| Hard-clean recovery | `pymol_bridge.cleanup_srp()` (`pymol_bridge.py:129-145`) | fresh-process-safe; guard must never masquerade as cleanup |
| Test harness conventions | `tests/test_xtbenv.py:1-34` (sys.path insert, fixture-in-place, no stubs, DI fakes) | python3.6 gate compatibility |

## Common pitfalls for this half

1. **Head-excluded atom count.** Using `last_run['atoms_total']` as the xtb input size undercounts by the head's atoms (pinned `test_phase5_integration.py:267-273`; the HUD label calling it 'spectra input size' at `hud_logic.py:189` is a known approximation of the revealed count, NOT the guard's number). Guard counts must be head-inclusive = counted from the chain objects being exported.
2. **Blocking on overage.** A default win snake can exceed `atom_budget` (set_a 12-24 atoms x 11 molecules; win freezes `molecules_stacked` exactly at cap, `game_engine.py:726-731`). Blocking = the shipped win path cannot produce a spectrum. Warn-and-proceed only.
3. **Reusing `validate()` warnings as the launch re-check.** `validate()` warns about CONFIG EXCEEDS SAFE DEFAULTS (user raised the sliders); the launch re-check warns about THE RUN EXCEEDS THE BUDGET (actual counts). Same literal, different trigger data — do not call `validate()` for Q3's output.
4. **Count-free wording leak.** `budget_text()`'s no-digit rule (`hud_logic.py:127-131` + `tests/test_hud_content.py:19-20`) applies to PLAY only (GAME-04). At launch the counts are revealed; the launch warning SHOULD include them — but don't regress the in-run line.
5. **Viewer-vs-engine coordinate divergence if read mid-run.** Export must happen at the completion-steady-state only (post `_present_completion`), never during play; `chain_object_names()` is completion-only by contract. Reading the teardown-purged scene (pickups deleted, `gui_game.py:1354-1358`) is fine — chain survives teardown by design.
6. **`.pse`/reload state holes.** `last_run` is None in a fresh process even when chain objects persist (`PITFALLS.md:203-207`). The launch API must handle `last_run is None` and count-from-viewer fallbacks without raising — never assume engine/session mirrors exist (they die with the tab; the anchor record survives Plugin-Manager reload only).
7. **Path mistakes that break the contract.** Running xtb with a non-bare input path or wrong cwd re-reads a STALE vibspectrum as success (`PITFALLS.md:82`; cwd contract `xtbenv.py:180-185`); launching from the PyMOL session dir sprays ~10 files into the user's folder (`xtbenv.py:203-205`); passing `/mnt/c/...` at runtime fails inside Windows PyMOL (`STACK.md:168`). new_run_dir + bare argv + tempdir base are load-bearing.
8. **stderr substring trap when surfacing verdicts.** `'abnormal termination'` CONTAINS `'normal termination'` — `evaluate_run` handles the order for you (`xtbenv.py:90-99`); any UI-side scan of the drained log must NOT re-grep naively (use the RunVerdict).
9. **Purity drift.** Guard math PURE (python3.6, %-formatting, no f-strings); counting/read BRIDGE (`pymol_bridge.py`); launch wiring GUI (`gui.py`, already allowlisted). A new PURE module needs no purity-table edit; a new GUI module must be added to `GUI_MODULES` consciously (`tools/check_purity.py:55-75`). Re-run `python3.6 tests/run_gates.py` accordingly.
10. **Signal-contract erosion.** Do NOT change `spectra_requested`'s signature or have GameTab reach the tab widget (model-A / locked decision 9, `gui.py:99-110`): Phase 7 replaces only the placeholder page content (05-15-SUMMARY.md:61), and the bottom 6-button row is Phase 8's (`FEATURES.md:105`).
11. **g98 geometry frame confusion (for the Phase 7 freeze doc).** g98.out atoms/vectors are the OPTIMIZED frame; the viewer snake is the GAME frame. Phase 6 only needs to PRESERVE `xtbopt.xyz` (and the input xyz) so Phase 7 can choose the overlay frame without re-running (MEDIUM confidence — no in-repo decision found; do not invent an alignment scheme in Phase 6).
12. **Comment-line corruption.** Multi-line comments break the xyz frame — the writer sanitizes (`xyzio.py:96`), but pass a single-line `snake_id` comment anyway; don't embed user text.

## Sources

- Live code (HIGH, verified 2026-09-24): `serpentrum/setup_logic.py`, `xtbenv.py`, `xyzio.py`, `spectra.py`, `game_engine.py`, `gui_game.py`, `gui_setup.py`, `gui.py`, `pymol_bridge.py`, `hud_logic.py`, `__init__.py`, `setloader.py`, `molecule_data.py`, `tools/check_purity.py`, `tests/test_xtbenv.py`, `test_xyzio.py`, `test_hud_content.py`, `test_phase5_integration.py`, `serpentrum/data/manifest.json`.
- Planning docs (HIGH): `.planning/requirements` (REQUIREMENTS.md:19,30,55; ROADMAP.md:215-238,250; PROJECT.md:24,30,71), `.planning/phases/05-stacking-game-rules/05-15-SUMMARY.md:15-18,59,105`.
- Research docs (HIGH for [RUN] items, MEDIUM for extrapolations): `.planning/research/PITFALLS.md:56-82,134,177-212,248-253,289-320,333-338,431-446`; `STACK.md:71-99,103-105,152,168,192,198`; `SUMMARY.md:18,66-67,111,135,171,197`; `ARCHITECTURE.md:35-37,94-106,180-181,240-270,284`; `FEATURES.md:95-110`.

**Metadata**
- Standard stack: HIGH (all modules exist in-repo, pinned by tests)
- Guard semantics (warn-not-block): HIGH (three independent precedents + requirement wording)
- Launch seam placement: HIGH (Phase 5's own pattern)
- Phase 7 artifact set: HIGH for consumed files; MEDIUM for xtbopt.xyz preservation rationale
- N^3 cost model / 30-90 s window: MEDIUM (explicitly extrapolated from two [RUN] points)
- Research date: 2026-09-24. Valid until: ~60 days (stable internal-contract research; no external libs involved)
