# Phase 8: Demo Data, Docs & Release Audit — RESEARCH: End-to-End Release Audit (DOCS-05)

**Researched:** 2026-09-27
**Domain:** Release harness design (headless e2e smoke chaining + requirement traceability + closing human checkpoint) for the serpentrum PyMOL plugin
**Confidence:** HIGH (every load-bearing contract read in the current tree; precedents cited by file:line)

## Summary

DOCS-05 asks for two things: (1) the full release flow — **setup → play → complete → xtb → IR plot → save** — proven headless with human checkpoints, and (2) all 46 v1 requirements (44 original + GAME-11 + STACK-06, **NOT** "44") checked off with complete traceability. The honest finding from mapping the flow onto the existing harness is that **every leg is already proven somewhere except the *chaining***: materialize (smoke 04), bridge seams (05/07/08), chain counts + xyz handoff shape (smoke 10 + `gui.py:167`), the real xtb controller (smoke 11, informational), parse→plot→PNG save (smoke 12), mode arrows (smoke 13). What does not exist today is a single headless run that walks a configured setup through a scripted engine win and hands the played snake's atoms forward into the spectra tail, writing a PNG. That chain-glue smoke is the plan's main new artifact.

The real-xtb question is already dispositioned by owner directive (06-12, EQ-smoke-1): xtb-exe-dependent smokes stay **INFORMATIONAL** unless the owner explicitly instructs promotion, and the owner instructed none. A REQUIRED release smoke must therefore use the committed `tests/fixtures/xtb/g98.out` fixture for its spectra tail (exactly smoke 12's pattern); the real-xtb full-size flow (104 atoms ≈ 84–101 s, which exceeds the harness's fixed 90 s per-smoke timeout) belongs in the one blocking human checkpoint, exactly as 06-12 (12/12 live, "xtb finished: ok") and 07-10 (consolidated checkpoint APPROVED round 2) ran it. Traceability is a docs artifact with partial mechanical checking; note the checkbox list in `REQUIREMENTS.md` currently **disagrees** with its own traceability table (e.g. SETUP-01, STACK-06, INFRA-01/02/03/05/06 read `[ ]` while the table says Complete) — reconciling this IS part of the DOCS-05 work item, not an error to report.

**Primary recommendation:** Add `smoke/14_release_e2e_smoke.py` as a **REQUIRED** gate smoke (fits SMOKE_TIMEOUT=90 comfortably): load Demo Set A → materialize → drive the pure `game_engine.GameEngine` headless (dt-parameterized `step()`, scripted `request_direction`, tiny cap → `'won'`) → `xyzio.write_xyz` + `read_xyz_text` round-trip (mirrors `gui.py:167`) → fixture `g98.out` parse → `plot_logic.build_scene` → `gui_plot.render_image` → PNG written + magic-byte/reload assertions. Keep real xtb (full game at small cap, cancel/run-again, PNG-opened-outside-PyMOL) in the phase-closing checkpoint; build the audit artifact as an evidence column/table over all 46 v1 IDs plus a `tools/` script that mechanically checks ID↔status↔evidence-file integrity.

## Standard Stack

### Core (all EXISTING — the audit adds glue, not new dependencies)

| Component | Location | Role in the audit |
|-----------|----------|-------------------|
| `tests/run_gates.py` | gate harness | registry to extend (REQUIRED_SMOKES tuple, `:55-72`) |
| `smoke/14_release_e2e_smoke.py` (NEW) | headless chain proof | the one new smoke |
| `game_engine.GameEngine` | `serpentrum/game_engine.py:266` (speed kwarg, `:556 step(dt)`, `:368 request_direction`, `:243 cap → ('won',)`) | pure, WSL-testable, dt-deterministic play leg |
| `pymol_bridge` | `materialize` / `move_head_delta` / `chain_atom_counts` | viewer seams already proven by smokes 04/05/10 |
| `xyzio.write_xyz` / `read_xyz_text` | `serpentrum/xyzio.py:81,111` | the engine→xtb handoff codec; the exact roundtrip gui.py asserts at `:167` |
| `spectra.parse_g98` + `plot_logic.build_scene` | Phase 2/7 pure halves | spectra tail (fixture-fed) |
| `gui_plot.render_image` | route-A PNG seam | save leg without widget construction (smoke 12 calls it directly headless) |
| `setup_logic.save_setup`/`load_setup`/`merge_defaults` | `setup_logic.py:313`+, SCHEMA_VERSION=1 hard-reject at `:251` | SETUP-08 pure round-trip; Save/Load **buttons** are this phase's own scope |

### Supporting

| Artifact | Why it matters to the plan |
|----------|----------------------------|
| `tests/fixtures/xtb/g98.out` | committed real g98 (26 atoms, 72 modes, 3 imaginary) — the fixture spectra tail |
| `smoke/11_xtb_runner_smoke.py` | informational real-controller proof; SRP_SPECTRA_DIR tempdir redirect pattern (`:110-111`) |
| `smoke/12_plot_smoke.py` | QApplication stage-0 guard to copy verbatim (`:109-111`); PNG magic-byte + reload-dims assertions (`:89-100`) |
| `06-CALIBRATION.md` | measured 104-atom `--ohess`: 84–101 s uncapped/`-P 4`; 52 atoms 6.3–6.7 s; co2-class ms-scale (smoke 11 `:5`) |
| `07-VERIFICATION.md` | the per-plan must_haves + evidence format to mirror at whole-v1 scale |

**Nothing to install.** External deps stay at "what pymol-open-source ships" (PyQt5 via `pymol.Qt`, numpy) — the out-of-scope table bans extras.

## 1. Flow-Leg Coverage Matrix

| Flow leg | Existing proof today | Gap for DOCS-05 |
|----------|----------------------|-----------------|
| **setup** (config → viewer scene) | smoke 04 REQUIRED: manifest→setloader→materialize→head switch→cleanup on real Set A bytes; pure setup_logic fully unit-tested | NONE at mechanical level. GUI dropdown/preset/head widgets = human-only (01-05 decision, headless widget construction is a dead end) |
| **play** (countdown → move → pickup) | smokes 05 (loop camera), 06 (input wizard), 07 (transform sweep), 08 (stack place) REQUIRED; engine fully covered by 840 WSL unittests | **GAP — no headless scripted full game.** No smoke drives engine→win in one run |
| **complete** (win → handoff) | 06-12 live checkpoint (cap-3 win, counts 54+12=66 arithmetic) — human; `gui.py:167` uses `xyzio.read_xyz_text(snake_xyz)` as completion cross-check | **GAP — headless win→xyz handoff never exercised in one chain** |
| **xtb** | smoke 11 INFORMATIONAL (REAL co2 success + dimer cancel/guard/failure contracts); gate 5 `--xtb` version probe; 06-12 live full run — human | real-exe runs can't be REQUIRED (EQ-smoke-1 owner disposition); the *shape* can be chained with fixtures |
| **IR plot** | smoke 12 REQUIRED stages 1–5 (fixture g98 → scene → render legs incl. options parity) | tail is proven standalone; needs chaining into the e2e |
| **save** | (a) PNG: smoke 12 STAGE2 route-A `img.save` + magic bytes + reload 1600×1000; (b) Save Setup: pure round-trip `save_setup`/`load_setup` unit-tested (`test_phase51_integration.py`) — **GUI buttons are Phase-8 scope**; (c) spectra artifacts: smoke 11 keep-until-replaced + SRP_SPECTRA_DIR + gitignored `srp_spectra/` | button wiring is this phase's own SETUP-07/08 work; the headless audit exercises (a)+(b pure)+(c via smoke 11 cite) |

**Net:** two gaps are mechanical and new — the scripted-play leg and the one-run chaining of complete→(fixture) spectra→PNG save. Everything else is assembly + citation.

## 2. Recommended E2E Harness Design

### New smoke: `smoke/14_release_e2e_smoke.py` — REQUIRED

- **Name/number:** `14` is the next free slot (files exist 01–13; gate glob is `smoke/[0-9][0-9]_*.py`).
- **Template obligations (verbatim house pattern, copied across all smokes):** `_resolve_root()` validating `serpentrum/__init__.py` candidates (NEVER trust `__file__` under `-cq`); `flush=True` on every print; named step fns + `check()` runner; sentinels `SMOKE-OK RELEASE-E2E` / `SMOKE-FAIL <step>`; **NO widget construction** (C-abort is uncatchable); no `smoke/__init__.py`.
- **QApplication stage-0 guard:** any render leg touches fonts — copy smoke 12's stage-0 construct verbatim (`QApplication.instance() or QApplication([])`) BEFORE `render_image`. Importing `gui_plot` is safe; only widget *construction* is banned.
- **Step sequence (all ≤ ~90 s total with a wide margin):**
  1. `stage0_app` — guarded QApplication (smoke 12 `:109-111`).
  2. `setup_load` — `setloader.load_demo_set('set_a', ...)` 5 records (smoke 04 pattern) + `setup_logic.new_setup()` with a **small cap** (e.g. `win_cap` 2–3).
  3. `materialize` — `pymol_bridge.materialize(setup, records)` → `srp_box` + `srp_head` asserted.
  4. `scripted_win` — construct `game_engine.GameEngine(head=..., heading=..., speed_a_per_s=6.0, cap=N)` with scripted pickups placed on the head path; loop `engine.step(dt=0.1)` (the shipped cadence is a 100 ms QTimer with dt=0.1, `gui_game.py:88-90` — jitter is absorbed by the timer, so scripted dt is equivalent) plus scripted `request_direction` calls; assert `engine.result == 'won'` and `engine.finished`. Optionally mirror a few head moves via `pymol_bridge.move_head_delta` (proven by smoke 05) to keep a viewer-visible snake — do NOT rebuild gui_game wiring wholesale.
  5. `handoff_xyz` — `xyzio.write_xyz(elements, coords)` from the engine atoms, then `xyzio.read_xyz_text(text)` round-trip; assert the atom count equals the engine's `atoms_total` + head count — this is identical to the shipped completion cross-check `gui.py:167`.
  6. `spectra_tail_fixture` — `spectra.parse_g98(tests/fixtures/xtb/g98.out)` → 26 atoms / 72 modes / 3 imaginary (smoke 12's pinned contract), `plot_logic.build_scene(modes)` → scene asserts.
  7. `save_png` — `gui_plot.render_image(scene, (800,500), scale=2)` → temp PNG; assert magic bytes `\x89PNG`, reload dims 1600×1000, size > 1000 (smoke 12 `:89-100`), and `os.remove` cleanup.
  8. `setup_roundtrip` (SETUP-08 pure leg) — `save_setup(setup)` → text → `load_setup(text)` → `merge_defaults` → validate; assert the loaded dict reproduces the scripted config exactly (tier/box/head/cap). This is the headless half of "Save Setup → Load Setup on a fresh install reproduces the exact configuration."
  9. `cleanup` — `pymol_bridge.cleanup_srp()`; user-object sentinel survives (smoke 04 pattern).
- **Timeout budget:** pure-stepping a cap-3 win is sub-second; materialize ~2–5 s; parse+scene+PNG ~3–8 s (smoke 12 completes well inside 90 s). Total comfortably < 90 s — **no harness timeout change needed.**
- **Speed params:** use the `request_direction`/`speed_a_per_s` kwargs directly (engine ctor, `game_engine.py:256`); the shipped SHIPPED defaults are relaxed 3.0 / normal 6.0 / fast 7.5 / expert 9.0 Å/s (`setup_logic.SPEED_TIERS:118`), but speed hardly matters when ticks are driven by a Python loop — what matters is `cap` small and pickups scripted near the head path.

### Real xtb decision: fixtures in the REQUIRED smoke; real flow = human checkpoint

Precedent and mechanics, read from the tree:

- **06-12 EQ-smoke-1 (recorded, owner-visible):** "smokes 09/11 stay INFORMATIONAL by default (depend on the local xtb.exe fallback list); REQUIRED promotion only on explicit owner instruction — owner instructed NONE at 06-12" (`06-12-SUMMARY.md` key-decisions; STATE.md 2026-09-26 (c)).
- **Timeout physics:** the harness applies one fixed `SMOKE_TIMEOUT = 90` s to every smoke (`run_gates.py:75`). A real 104-atom `--ohess` measures **84–101 s** uncapped/`-P 4` (06-CALIBRATION), i.e. it *races or exceeds* the timeout; `-P 2` is 100–153 s (exceeds); single-threaded is 4.5–5 min. Even a "small" real sull-size win (cap-3, 66 atoms) sits in the awkward ~30–60 s band where Windows-perf variance makes a *REQUIRED* gate flaky.
- **What must NOT be attempted:** raising `SMOKE_TIMEOUT` globally just for smoke 14 (every other smoke's worst-case gate time inflates); or adding a per-smoke timeout table just to allow flakes (harness complexity for negative value).
- **Why smoke 11 CAN do real runs:** it uses co2 (~0.25 s) and dimer2 killed at 300 ms — sub-second real runs asserted as success/cancel, never a full hessian. A smoke-14 real-co2 variant was considered and rejected: it adds the exact machine-dependence EQ-smoke-1 excluded, for zero new contract coverage over smoke 11 itself.
- **Semantics of "passes headless with human checkpoints" (mirroring prior phases):** headless = the full harness (`tests/run_gates.py` + `--smoke` incl. smoke 14 + `--xtb`), human checkpoints = the one blocking live flow. This is exactly how 06-12 and 07-10 closed.

## 3. Requirement Traceability Mechanism

**Current state (read, not remembered):** `REQUIREMENTS.md` holds 46 v1 IDs (the Coverage note says 46; older "44" phrasing in handoffs is stale). Statuses as of Phases 1–7 close:

- **Traceability table Phase-8 Pending:** SETUP-07, SETUP-08, DATA-01, DATA-02, DATA-04, DOCS-01, DOCS-02, DOCS-03, DOCS-04, DOCS-05 (10 IDs).
- **Checkbox list `[ ]` mismatches to reconcile:** SETUP-01, SETUP-07/08, STACK-06, DATA-01/02/04, INFRA-01/02/03/05/06, DOCS-01..05 read `[ ]` while the table marks SETUP-01, STACK-06, INFRA-01/02/03/05/06 **Complete**. INFRA-04 is the only one consistent (`[x]` + Complete). This divergence is normal house flow — checkboxes/rows are orchestrator-owned and often lag (07-VERIFICATION.md:107) — but DOCS-05's "checked off" is precisely the reconciliation point.

**Recommended artifact:** an evidence-augmented traceability table — either an added **Evidence** column in `REQUIREMENTS.md`'s table, or a sibling `08-REQUIREMENTS-AUDIT.md` in the phase dir that the plan owns (update path is a planner choice; in-place keeps a single source, sibling keeps phase history — both fit house style; the 07-VERIFICATION must_haves|Status|Evidence table is the format to mirror per row).

**Evidence per ID = 3-tier citation, mirroring 07-VERIFICATION:**
1. **Mechanical** — unit test file / smoke number / artifact path (e.g. GAME-10 → `tests/test_game_engine.py` + smoke 07; SPECTRA-03 → smoke 12 STAGE2).
2. **Structural** — code file:line (e.g. SETUP-07 → `serpentrum/gui.py` 6-button row once this phase lands it).
3. **Human-certified** — checkpoint doc + verdict + date (e.g. DATA-02 → the Phase-8 closing checkpoint data sign-off; the 12/12 and 10-step records show exactly how these read).

**Mechanically checkable vs. manual:**

- *Scriptable* (a `tools/` script — e.g. `tools/audit_requirements.py`, python3.6, auto-covered by gate 1's syntax walk; `tools/` already hosts `check_purity.py`, `build_calibration_snake.py`, `measure_calib_qprocess.py`): (a) every listed v1 ID appears exactly once in the traceability table with a non-Pending status; (b) every Evidence file/exec-path referenced actually exists on disk; (c) the checkbox list and the table statuses agree post-flip; (d) `REQUIRED_SMOKES` files all exist (`run_gates.py` already self-fails a missing one — don't duplicate that, just cite it).
- *Manual* (cannot be scripted): evidence *correctness* (does smoke 12 actually prove "save-plot button"?), owner sign-offs, doc-vs-behavior wording audits (DOCS-04), DATA-02's "explicitly approved by the human" clause. These land in the closing checkpoint.
- Do **not** make the audit script a gate-6 in run_gates.py: the gates' contract is code guarantees, the audit is release paperwork — coupling them makes every doc-only edit re-run the whole battery. Run it as a verification task in the DOCS-05 plan + cite it in 08-VERIFICATION.

**Where prior verifiers got evidence:** 07-VERIFICATION's method — goal-backward against actual code (exists/substantive/wired), gates re-run by the verifier, Windows legs *cited* from SUMMARY verbatim logs (not re-run), human verdicts cited from recorded sign-offs. The whole-v1 audit should do the same at requirement granularity: per phase, point at the phase VERIFICATION/SUMMARY docs rather than re-deriving 95 plans of evidence.

## 4. Human Checkpoint Design (phase-closing, blocking — ONE, consolidated)

Precedents: 06-12 (12 numbered steps, 12/12 PASS, one amendment landed and re-verified), 07-10 (10 steps + 2 named sign-offs, round-1 defect → fix → round-2 APPROVED, `autonomous: false`, `type: execute` + `checkpoint:human-verify gate="blocking"`). The Phase-8 closing checkpoint should be the same shape and must NOT be attempted until SETUP-07/08 buttons, the data pack (DATA-01/02/04), docs plans (DOCS-01..04), and smoke 14 all land.

**Draft steps (planner to refine against the actual Phase-8 deliverables):**

1. **Environment prep:** real Windows PyMOL 2.5.0 + plugin loaded; fresh session; `SRP_DEBUG=1` if tracer lines are wanted; `SRP_SPECTRA_DIR` noted (default `<cwd>/srp_spectra`, gitignored).
2. **Setup exercise (SETUP-02..06):** demo-set dropdown, box presets, head select, xtb path autodetect, win cap with over-budget warning.
3. **6-button row walk (SETUP-07):** Reset, Randomize, Save Setup → file, Load Setup → every control reproduces the saved config exactly (compare all fields), Cleanup model removes only `srp_*`, Start.
4. **Fresh-install reproduction (SETUP-08):** the saved file loads in a second fresh session → identical game configuration.
5. **Play to completion:** small cap (cap-3 class — the 06-12 proven size) → win → completion state → Get Spectra activates.
6. **Real xtb leg (SPECTRA-02):** launch on the played snake, progress streams live, GUI responsive, cancel honest-text leg, run again → `xtb finished: ok`.
7. **IR plot + save (SPECTRA-03):** plot renders; size presets; Save Plot → PNG opens **outside** PyMOL and matches the screen.
8. **Table + vectors (SPECTRA-05):** row click → mode vectors on `srp_xtbopt`.
9. **Docs/hhelp spot-check (DOCS-01/03/04):** README install steps reproduce; in-game help matches real controls/dataset values; focus hint + negative-frequency note verified on screen.
10. **SIGN-OFF A — data pack (DATA-01/02/04, DOCS-02):** DATA_SOURCES.md full checklist approval; DRAFT heading flip; the Janiak SCOPE CAVEAT PHI (STATE.md:118 — explicit crystalline-state framing) confirmed handled in docs/help.
11. **SIGN-OFF B — the audit table:** all 46 IDs Complete with evidence; checkbox list reconciled with the traceability table.
12. **Restart hygiene (carry-over step from 07-10:10):** new game → prior `srp_xtbopt`/`srp_mode_vec` gone; Spectra tab degrades gracefully.

**Executor staging obligations (the 07-10 pattern):** the checkpoint step list is authored in the plan with per-step EXPECT lines; any defect → numbered fix list → targeted fix plans → checkpoint re-runs (the 05-16 7-round precedent says never approve with a known-broken step). Manual harness scripts (non-`NN_` names, never auto-run) are the support mechanism — `smoke/manual_wizard_keys_check.py` and `smoke/manual_plot_check.py` are the two existing exemplars; DOCS-05 may want a `smoke/manual_release_flow_check.py` only if a step needs scripted assist (a live-play helper); otherwise the numbered checklist suffices.

## 5. Gates Registry Notes

- **Registry:** `REQUIRED_SMOKES` tuple, `tests/run_gates.py:55-72`. Entries carry a per-plan comment (`# (Phase 6, plan 06-04 — ...)`, `# 12 = plot renderer via the paint_scene seam (Phase 7, plan 07-05)`) — copy that style: `# 14 = release e2e chain (Phase 8, plan 08-XX)`.
- **Mechanics of "required":** a required entry MISSING from the glob-found set fails the gate with "created by plan 01-04" phrasing (`:170-173`); informational smokes (any other `NN_*.py`) run when present and never fail (`:192-197`).
- **`SMOKE_TIMEOUT = 90`** is per-smoke and global (`:75`) — smoke 14 must fit; it does (fixture tail). Do not touch it.
- **Ordering:** the harness runs required smokes first (tuple order), then informational (`:170-197`). Appending `14` at the END of the tuple keeps the historical 01/03/04/05/06/07/08/10/12/13 prefix intact and reads naturally (chain-proof last: it depends on Phase 8's own setup leg existing… note smoke 14's `setup_roundtrip` step does not need the Phase-8 GUI buttons — pure layer only — so no cross-plan ordering hazard).
- **Budget:** current `--smoke` leg = 10 required + 3 informational × ≤90 s worst-case. Adding 14 = +≤90 s worst, ~+15–30 s actual. Fine.
- **Verdict discipline (unchanged):** flushed `SMOKE-OK` present AND `SMOKE-FAIL` absent; exit codes through the `.bat` are always 0 and never trusted (`:155-158`).
- **Glass-box note for the verifier:** the gate leg output echoes the literal sentinel line into gate notes (`:181-184`) — the release audit artifact may cite gate-log verbatim lines as evidence, exactly like 07-VERIFICATION:55.

## 6. What "save" Means in the Flow Tail (setup → … → IR plot → save)

All three "save" surfaces exist and each has proven coverage; **the audit must cite all three** (SC5's tail word is the plot save, but a requirements-complete read exercises everything):

1. **Save Plot PNG (SPECTRA-03)** — `gui_plot.render_image` route A → 2× QImage → `img.save(path,'PNG')`. Proven headless by smoke 12 STAGE2 (magic bytes + reload 1600×1000 + size gate). Smoke 14 re-asserts in-chain.
2. **Save Setup (SETUP-08)** — pure `save_setup`/`load_setup` JSON round-trip exists TODAY (`setup_logic.py:313+`, SCHEMA_VERSION=1 hard-reject at `:251`, `merge_defaults` backcompat seam at `:138-156`); unit-tested incl. Phase-5.1/5.2 keys (`test_phase51_integration.py`). **The bottom-row BUTTONS are Phase-8 scope** (reserved empty row `gui.py:78-81`; owner reconfirmed 5.2-09 "Save/Load buttons stay Phase 8"). DOCS-05 exercises the fresh-install reproduction leg in the human checkpoint after the buttons land; smoke 14 covers the pure half.
3. **Spectra artifacts keep-until-replaced** — stable dir `<SRP_SPECTRA_DIR>/<snake_id>` (owner-amended 048d929; default `<cwd>/srp_spectra`, gitignored), asserts in smoke 11 (`:322-327`, cancel-leg no-masquerade `:434-446`). Cited, not re-run, by the audit.

## Architecture Patterns

The one pattern worth restating for the plan: **smokes are contract replay, not GUI replay.** Every REQUIRED smoke (04/05/07/08/10/12/13) drives module seams directly (bridge functions, pure engine, renderer functions) and never constructs the dialog — because the 01-05 probe showed headless widget construction C-aborts uncatchably. The shipped game loop (gui_game's two Qt-parent-owned QTimers, `gui_game.py:284-290`) therefore cannot and need not be replayed headless; the pure engine underneath it is cadence-parameterized (`step(dt)`), so a scripted loop IS the same movement math the timers feed. GUI-floor behaviors (countdown, wizard keys, HUD, buttons) stay human-checkpoint territory — that boundary is the house's settled discipline, not a compromise.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Scripted-play engine | a smoke-local mini game loop | `game_engine.GameEngine` + `step(dt)` + `request_direction` | the pure engine IS the shipped game math; re-implementing pickups/win logic in the smoke invents a second contract to maintain |
| XYZ serialization in the smoke | string-format coords by hand | `xyzio.write_xyz` / `read_xyz_text` | the completion cross-check `gui.py:167` already consumes this exact codec — the smoke must prove the real path, not a lookalike |
| PNG verification | PIL/image deps or pixel diffing | QImage reload + magic-byte + dims asserts (smoke 12 `:89-100`) | banned extra deps; the reload round-trip is the established, sufficient check |
| Machine-traceability spreadsheet in a new format | a bespoke audit schema | the 07-VERIFICATION must_haves|Status|Evidence table shape + a `tools/` integrity grep | house format is proven and the verifier already expects it |
| Real-xtb gate enforcement | raising SMOKE_TIMEOUT / per-smoke timeout dict | fixtures for REQUIRED + human checkpoint for real runs | owner dispositioned (EQ-smoke-1); 104-atom real runs exceed 90 s; flakiness makes REQUIRED impossible |

**Key insight:** DOCS-05 is about 90% *assembly and citation of evidence that already exists* — the risk is inventing new machinery where the harness already has the seam (engine, xyzio, render_image, fixture, registry). The genuinely new code is one smoke file and one small audit-integrity script.

## Common Pitfalls

### Pitfall 1: Putting a real ~100 s xtb run in a REQUIRED smoke
**What goes wrong:** 84–101 s (uncapped/`-P 4`) races/exceeds the fixed 90 s `SMOKE_TIMEOUT`; on a loaded Windows box it flakes the whole gate battery red.
**Why it happens:** "end-to-end" gets read as "real hessian headless" without checking the calibration table or the EQ-smoke-1 disposition.
**How to avoid:** fixture spectra tail in smoke 14; real flow in the closing checkpoint. If ever tempted to extend a timeout, note the timeout is per-smoke-global (`run_gates.py:75`) and every existing smoke inherits it.
**Warning signs:** `--smoke` intermittently failing only on smoke 14 with a TIMEOUT note.

### Pitfall 2: Constructing widgets in the headless smoke
**What goes wrong:** `PluginDialog()` or `GameTab()` under `-cq` silently C-aborts; no traceback; gates see only a missing sentinel.
**Why:** uncatchable under headless Qt (01-05 probe; every smoke docstring repeats it).
**Avoid:** module seams only — `render_image` is a module function and safe; `SpectraTab()` is not.

### Pitfall 3: Font access without a QApplication
**What goes wrong:** QFontMetrics/drawText with no Q*Application hard-kills the process with no error (probe RUN A).
**Avoid:** stage-0 `QtWidgets.QApplication.instance() or QApplication([])`, copied verbatim from smoke 12 `:109-111` BEFORE any render leg, even if a prior step "seems" to have made one.

### Pitfall 4: Trusting exit codes or `__file__`
**What goes wrong:** `.bat` exit codes are always 0 (even after a Qt abort); `__file__` is PyMOL's launcher module under `-cq`.
**Avoid:** flushed-sentinel verdicts only; `_resolve_root()` validating `serpentrum/__init__.py` candidates, copied verbatim.

### Pitfall 5: Reconciling REQUIREMENTS.md blindly
**What goes wrong:** treating every `[ ]` checkbox as "not done" and flagging completed-phase work as gaps (07-VERIFICATION:107 records this exact confusion for SPECTRA rows), or conversely flipping checkboxes without evidence.
**Why:** checkbox list and traceability table have different owners/cadences (orchestrator-owned between phase closes).
**Avoid:** the audit table is the place where reconciliation happens deliberately, per ID, with evidence cited; mismatch is input data, not a finding.

### Pitfall 6: Spraying artifacts or emitting srp_ leaks in the smoke
**What goes wrong:** a smoke writing into the repo tree or leaving stable dirs violates the EQ-artifact-1 contract (`SRP_SPECTRA_DIR` redirect, spray-vs-stable hygiene asserted by smoke 11).
**Avoid:** if smoke 14 needs a spectra dir at all, set `os.environ['SRP_SPECTRA_DIR'] = tempfile.mkdtemp(...)` BEFORE any run step (smoke 11 `:110-111`); with the fixture tail design it needs none — keep it that way. End with `cleanup_srp()` + user-sentinel assertion.

### Pitfall 7: Plugin-path safety regressions
No `__init__.py` in `tests/`/`smoke/`/`tools/`; no top-level `*.py` at repo root; smoke file must match `[0-9][0-9]_*.py` to be picked up (and a manual harness must NOT match it). Gate 1 enforces all three — don't let the plan add dev helpers in the wrong place.

### Pitfall 8: Count drift ("44 requirements")
Actual count is **46** (44 + GAME-11 + promoted STACK-06; REQUIREMENTS.md:175). Handoffs quoting 44 are stale. The audit script should fail loudly on a count mismatch rather than silently adopting the wrong total.

## Code Examples

### Engine-led scripted win (the play leg core)
```python
# Source: serpentrum/game_engine.py (:266 ctor, :368 request_direction,
# :556 step, :243 cap/win emission); speed constants from
# setup_logic.SPEED_TIERS (:118). House smoke template from smoke/04.
import os, sys, time
from serpentrum import game_engine, setup_logic

# scripted pickups placed along the head path (records from setloader,
# smoke 04's s_real_data_load pattern)
engine = game_engine.GameEngine(
    head=(0.0, 0.0), heading='right', ...,
    speed_a_per_s=6.0,   # 'normal' tier literal; any tier kwarg works
    cap=2)               # tiny cap -> quick scripted win
while not engine.finished:
    events = engine.step(0.1)   # the shipped cadence: QTimer 100 ms, dt=0.1 (gui_game.py:88-90)
assert engine.result == 'won', 'scripted run ended %r' % (engine.result,)
```

### Save-Setup round-trip (SETUP-08 pure leg)
```python
# Source: serpentrum/setup_logic.py (save_setup :313+, load_setup,
# merge_defaults :138-156, SCHEMA_VERSION hard-reject :251)
from serpentrum import setup_logic
text = setup_logic.save_setup(setup)
loaded, errs = setup_logic.load_setup(text)
assert errs == [], errs
merged = setup_logic.merge_defaults(loaded['settings'])
assert merged['box_preset'] == setup['box_preset']  # ...every audited key
```

### Render-save assertion (PNG leg)
```python
# Source: smoke/12_plot_smoke.py stages 0/2 (QApplication guard :109-111;
# magic-bytes + reload-dims :89-100); gui_plot.render_image route A.
_APP = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
img = gui_plot.render_image(scene, (800, 500), scale=2)
ok = img.save(tmp, 'PNG')
assert ok and open(tmp, 'rb').read(4) == b'\x89PNG'
```

## State of the Art (harness evolution relevant to this plan)

| Old Approach | Current Approach | When | Impact |
|--------------|------------------|------|--------|
| Real-xtb REQUIRED promotion "when stable" | Real-xtb legs stay INFORMATIONAL; promotion only on explicit owner instruction | 06-12 (EQ-smoke-1, 2026-09-26) | smoke 14 must be fixture-tailed |
| Stable artifacts in %TEMP | SRP_SPECTRA_DIR env override, default `<cwd>/srp_spectra`, gitignored | 048d929 (06-12 amendment) | smokes/checkpoints redirect or cite it; never assume %TEMP |
| Plot save via QWidget.grab() (fallback) | Route A: single paint_scene seam → 2× QImage → img.save | 07-05 (probe-verified) | smoke 12/14 assert this path only |
| "uncapped xtb is fine" | DEFAULT_THREAD_ARG ('-P','4') + measured 84–101 s @104 atoms | 06-11 via 06-CALIBRATION | checkpoint's real-run expectation ~1–2 min at played sizes |
| Checkbox list trusted as status | Traceability table is inter-phase truth; checkbox reconciliation is a DOCS-05 deliverable | 07-VERIFICATION:107 | audit operates on evidence, not box states |

## Open Questions

1. **Smoke 14 REQUIRED vs informational.** Recommendation REQUIRED (the whole point of DOCS-05 is machine-enforced chain-proof; it has no xtb.exe dependency so EQ-smoke-1 doesn't bar it). But 12/13 were promoted as phase plans created them, so confirm the planner/owner doesn't want one informational soak-run first.
2. **Audit artifact home:** in-place Evidence column in `REQUIREMENTS.md` vs sibling `08-REQUIREMENTS-AUDIT.md`. In-place = single source of truth; sibling = phase history. Planner picks; the `tools/` integrity script should point at only one.
3. **Who flips Status/checkboxes:** the DOCS-05 plan's own final task vs the phase-close orchestrator handoff (the 07 pattern left rows "orchestrator-owned"). Needs an explicit assignment in the plan so the audit isn't double-owned.
4. **Does the closing checkpoint include a far-side "educator" reproduction machine?** SETUP-08 literally says "another user can Load Setup to reproduce" — one-machine two-session proof (step 4 draft) may suffice for v1; multi-machine is an owner question.
5. **Manual harness for the release checkpoint:** is a `manual_release_flow_check.py` live-play assist needed (e.g., scripted direction feeding to speed the owner through the play leg)? 07-10/06-12 ran with plain checklists; recommend checklist-only unless the owner wants the assist.
6. **Scope of DOCS-04 hookup:** the doc-vs-code audit (README steps reproduce, help text matches) is its own Phase-8 plan (DOCS-04) — the release audit cites it as an ID rather than re-performing it. Confirm this citation-only treatment.

## Sources

### Primary (HIGH confidence) — all read in the current tree
- `tests/run_gates.py` (full file): REQUIRED_SMOKES `:55-72`, SMOKE_TIMEOUT `:75`, sentinel-only verdict `:155-158`, required/informational split `:170-197`, --xtb gate `:201-275`.
- `smoke/04_demo_e2e_smoke.py` (full): setloader→materialize chain, template rules, `_resolve_root`.
- `smoke/11_xtb_runner_smoke.py` (full): informational disposition reasons, SRP_SPECTRA_DIR redirect `:110-111`, real-run contracts, keep-until-replaced asserts.
- `smoke/12_plot_smoke.py` (full): QApplication stage-0 `:109-111`, fixture contract `:119-131`, PNG asserts `:89-100,134-149`.
- `smoke/10_chain_count_smoke.py` (full): count channel + 0-on-missing desync policy.
- `smoke/05_loop_camera_smoke.py` (head): loop/camera seams, template obligations.
- `.planning/ROADMAP.md:292-305`: Phase 8 goal, requirements, all 5 success criteria; plan structure hint `:303`.
- `.planning/REQUIREMENTS.md` (full): 46-count note `:175`, all ID texts + checkbox/table statuses `:121-172`.
- `.planning/STATE.md`: 840 unittests + 10/10 smokes baseline; 06-12 verdicts incl. EQ-smoke-1 + 048d929 (line 90); Janiak PHI (line 118); DATA_SOURCES DRAFT-gating (line 117).
- `.planning/phases/06-xtb-pipeline/06-CALIBRATION.md` (full): measured 104-atom 84–101 s, 52-at 6.3–6.7 s, QProcess perceived 91–108 s, `-P 4` recommendation.
- `.planning/phases/06-xtb-pipeline/06-12-SUMMARY.md` (frontmatter): EQ-smoke-1 verbatim disposition; checkpoint model note.
- `.planning/phases/07-spectra-ui/07-10-PLAN.md` (full): gates-task + checkpoint-task shape, step/EXPECT/sign-off grammar, round/fix protocol.
- `.planning/phases/07-spectra-ui/07-VERIFICATION.md` (full): must_haves|Status|Evidence format, method paragraph `:14`, orchestrator-owned-row note `:107`, accepted-limitations section.
- `serpentrum/game_engine.py`, `serpentrum/setup_logic.py`, `serpentrum/gui.py`, `serpentrum/gui_game.py`, `serpentrum/xyzio.py` (targeted greps + reads at the cited lines).

### Secondary (MEDIUM confidence)
- `.planning/codebase/TESTING.md`, `STACK.md`, `STRUCTURE.md` — house harness conventions (readable repo docs written from earlier verified state; confirmed consistent with the actual files read directly above).

### Tertiary (LOW confidence)
- None used. No external sources needed — this is repo-internal harness research.

## Metadata

**Confidence breakdown:**
- Flow-leg coverage + e2e design: HIGH — read directly from the harness, smokes, engine, and CALIBRATION numbers in-tree.
- Gates registry + checkpoint format: HIGH — `run_gates.py` and 07-10-PLAN/06-12-SUMMARY read verbatim.
- Traceability mechanism: HIGH for mechanics (files read); the in-place-vs-sibling + ownership choices are deliberately left as planner Open Questions (they are preference, not evidence).
- Real-xtb decision: HIGH — owner disposition recorded in 06-12-SUMMARY frontmatter and STATE.md.

**Research date:** 2026-09-27
**Valid until:** ~30 days or until any of: `run_gates.py` registry edit, new smoke 14 lands, Phase-8 SETUP-07/08 buttons land (afterwards the checkpoint draft's step 2–5 details should be re-checked against actual UI wiring).
