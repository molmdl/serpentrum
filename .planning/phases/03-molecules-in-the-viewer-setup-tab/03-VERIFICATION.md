---
phase: 03-molecules-in-the-viewer-setup-tab
verified: 2026-09-12T00:00:00Z
status: passed
score: 5/5 success criteria verified (32/32 plan-level truths verified)
re_verification: false
---

# Phase 3: Molecules in the Viewer & Setup Tab — Verification Report

**Phase Goal:** The user can configure a game in the Setup tab — demo set or upload, box preset, head molecule, xtb path, win cap — and see the box and chosen head molecule materialize in the viewer, with unsafe uploads rejected at the load-time gate.
**Verified:** 2026-09-12
**Status:** passed
**Re-verification:** No — initial verification

## Verification Method

Goal-backward: the 5 ROADMAP success criteria were checked against the actual code at three levels (existence → substantive → wired), then cross-checked against each plan's `must_haves` frontmatter (8 plans, 32 truths). Machine-checkable evidence was re-run fresh (`python3.6 tests/run_gates.py` — exit 0, 433 tests, 3 gates PASS). Human-verify claims were checked against the 03-08-SUMMARY checkpoint record and confirmed by the two fix commits (`ae27ffe`, `e8b3a9d`) it references. SUMMARY claims were not trusted — every claim below was traced to code.

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Demo Set A from dropdown (or SDF/mol2 upload) loads molecules into the scene; >3-ring uploads rejected with a clear reason [SETUP-02, DATA-03] | ✓ VERIFIED | `gui_setup.py:85-89` demo combo (KNOWN_SETS + Upload sentinel); `_on_apply` routes `load_demo_set`/`load_upload` → `pymol_bridge.materialize` (lines 421-447); `molfile.gate_molecule` rejects `ring_count > 3` with exact reason `'%s: has %d rings (limit is 3)'` (molfile.py:581-583); rejection surfaces via 'Upload rejected' modal (gui_setup.py:426-435); human-verified: tetracene modal in real PyMOL (03-08-SUMMARY step 4 PASS) |
| 2 | Preset box sizes; clearly visible boundary box; selected head molecule (default Random) appears [SETUP-03, SETUP-04] | ✓ VERIFIED | `BOX_PRESETS` small/medium/large (setup_logic.py:64-68); box combo populated from presets (gui_setup.py:98-100); `load_box` builds CGO via `cgo_build.box_cgo` → `cmd.load_cgo('srp_box', zoom=0)` with linewidth 3.0 (post-fix e8b3a9d) for visibility; `materialize` loads head → spheres rep → centroid centered → `cmd.zoom('srp_*')+refresh` (pymol_bridge.py:176-204); head combo defaults 'Random' userData 'random' → `records[0]` (pymol_bridge.py:166-168); human-verified steps 2,3,5 PASS |
| 3 | xtb auto-detect (handles `xtb` and `xtb.exe`) or manual path overriding detection [SETUP-05] | ✓ VERIFIED | `xtbenv.detect_binary` probes `which('xtb.exe')` (Windows-first) then `which('xtb')` (xtbenv.py:141-167); valid `configured_path` short-circuits ahead of detection (override semantics); GUI: auto checkbox disables field + sets `xtb_path=None`; detect result surfaces on toggle AND on Apply (gui_setup.py:307-355, 460-466 — post-fix ae27ffe); `_xtb_path_problems` delegates to `xtbenv.validate_binary_path` (setup_logic.py:119) with cross-check test (test_setup_logic.py:403); human-verified step 8 PASS |
| 4 | Win cap defaults to safe budget (~10 mol / ~100 atoms); hessian ~N³ warning when raised [SETUP-06] | ✓ VERIFIED | DEFAULTS: `win_cap_molecules: 10`, `atom_budget: 100` (setup_logic.py:56-57); spinbox range 1..20 (gui_setup.py:114-115); `HESSIAN_WARNING` = 'hessian cost scales ~N^3; a ~100-atom snake may take 30-90 s' (setup_logic.py:74-75); `_on_cap_changed` shows warning inline when >10, hides at ≤10, fired on valueChanged AND apply_state (gui_setup.py:297-305, 286); human-verified step 9 PASS |
| 5 | Cleanup removes only `srp_*` objects (user molecules untouched); works in fresh process after .pse save/reload [INFRA-04] | ✓ VERIFIED | `cleanup_srp` is a pure function of object names — no controller/state args, counts via `cmd.get_names('public_objects')`, deletes by `'srp_*'` pattern, returns count (pymol_bridge.py:125-139); load-time `object=` naming keeps everything in srp_* namespace; `smoke/03_viewer_bridge_smoke.py` proves .pse survival + wildcard cleanup + non-srp sentinel survival; human-verified steps 6 ('ATP' survived, zero srp_*) and 7 (.pse save → PyMOL restart → reload → cleanup works) PASS; documented in AGENTS.md:75 |

**Score:** 5/5 success criteria verified · 32/32 plan-level `must_haves` truths verified

### Plan-Level Must-Haves (all 8 plans)

| Plan | Truths | Key artifact evidence |
|------|--------|----------------------|
| 03-01 purity BRIDGE class | 4/4 | `BRIDGE_MODULES = {'serpentrum/pymol_bridge.py'}`, GUI_MODULES extended to `{gui.py, gui_setup.py}` (check_purity.py:58,65); 7 new BRIDGE/GUI fixture tests (test_purity_gates.py:207-305); gate 2 PASS in fresh run |
| 03-02 molfile | 5/5 | 618-line pure module: `count_rings` (cyclomatic E−V+C), `read_sdf` multi-record + M CHG, `write_sdf_text` round-trip, `find_ring_atoms`, `gate_molecule`/`gate_set`; 338-line test + 5 committed fixtures |
| 03-03 xtb-path unification | 3/3 | `setup_logic.py:119 return validate_binary_path(path)`; stale docstring rationale gone; test matrix green unmodified (433 OK) |
| 03-04 setloader | 5/5 | `load_demo_set` verifies manifest atom_count/charge/ring_count vs parsed reality (setloader.py:184-196); `UPLOAD_SET_ID='__upload__'` keying → `has_stack_entry=False`; multi-record split into `srp_upload_` tempdir (setloader.py:292-309); errors not exceptions |
| 03-05 demo data | 4/4 | 5 SDFs (CIDs 241/931/8418/995/7095) + manifest.json verified: schema 1, set_a 'Aromatic pi-stack', atoms 12/18/24/24/22, rings 1/2/3/3/2, ring_atoms lengths 6/10/14/14/12; `tests/test_demo_data.py` real-file regression in the green 433 |
| 03-06 pymol_bridge | 4/4 | Scene contract exact (cleanup→box→head→spheres→center→frame); `cleanup_srp` stateless; smoke sentinels `SMOKE-OK VIEWER-BRIDGE`/`SMOKE-OK VIEWER-DEMO` both in REQUIRED_SMOKES (run_gates.py:56-57) and recorded in SUMMARYs |
| 03-07 SetupTab | 5/5 | 479-line live form, full widget inventory; Apply flow: validate → setloader → head-combo repopulate → materialize → status; `_loading` guard; anchor `pmg_tk.startup._serpentrum.setup` initialized via `setup_logic.new_setup()` in `_anchor()` (`__init__.py:25-28`); zero `.exec_`, zero direct cmd imports |
| 03-08 gates + checkpoint | 2/2 | Gates re-run fresh: exit 0, 433 tests, gates 1-3 PASS; checkpoint record: 10/10 steps PASS, 'APPROVED' (03-08-SUMMARY.md:59,71,116); fix commits ae27ffe + e8b3a9d exist in history |

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `tools/check_purity.py` | BRIDGE class + gui_setup allowlist | ✓ VERIFIED | 235 lines; classify() BRANCH, GUI/BRIDGE module sets |
| `serpentrum/molfile.py` | pure SDF/mol2 + gate | ✓ VERIFIED | 618 lines; all 03-02 exports present; MolFileError |
| `serpentrum/setloader.py` | demo/upload records | ✓ VERIFIED | 323 lines; load_demo_set/load_upload contract |
| `serpentrum/pymol_bridge.py` | cmd-seam | ✓ VERIFIED | 204 lines; SRP_PREFIX/BOX_DISPLAY_Z/load_box/load_molecule/place_head/cleanup_srp/frame_scene/materialize |
| `serpentrum/gui_setup.py` | SetupTab form | ✓ VERIFIED | 479 lines; 5 QGroupBox sections + status + temp buttons |
| `serpentrum/gui.py` | Setup as page 0 | ✓ VERIFIED | SetupTab(anchor_state) → addTab 'Setup'; tabs handle + reserved row intact |
| `serpentrum/__init__.py` | anchor setup field | ✓ VERIFIED | `_anchor()` lazy-creates `state.setup = setup_logic.new_setup()` |
| `serpentrum/data/` | manifest + 5 SDFs + stacking | ✓ VERIFIED | manifest.json values match parsed reality (test-enforced); stacking_pi_stack.json present |
| `tests/fixtures/molfile/` | 5 fixtures | ✓ VERIFIED | methane.sdf, benzene_naphthalene.sdf, acetate.sdf, benzene_noh.sdf, benzene.mol2 — no `__init__.py` |
| `smoke/03_viewer_bridge_smoke.py`, `smoke/04_demo_e2e_smoke.py` | headless smokes | ✓ VERIFIED | Both flush SMOKE-OK sentinels; registered in run_gates REQUIRED_SMOKES |
| `tools/build_demo_manifest.py` | manifest builder | ✓ VERIFIED | 168 lines; parses via molfile, aborts on mismatch |
| `AGENTS.md` | srp_ reservation | ✓ VERIFIED | Line 75 documents prefix reservation + fresh-process INFRA-04 rationale |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `gui_setup._on_apply` | `setloader.load_demo_set/load_upload` | routing by combo currentData | ✓ WIRED | gui_setup.py:422-435; rejection errors → 'Upload rejected' modal |
| `gui_setup._on_apply` | `pymol_bridge.materialize/cleanup_srp` | the ONLY GUI→cmd path | ✓ WIRED | gui_setup.py:447, 477; zero direct cmd imports in GUI (gate-enforced) |
| `gui_setup` | `setup_logic.validate` | live status + Apply gate | ✓ WIRED | gui_setup.py:328, 414; errors block Apply |
| `pymol_bridge.load_box` | `cgo_build.box_cgo` | pure builder feeds cmd seam | ✓ WIRED | pymol_bridge.py:102-104 |
| `pymol_bridge.materialize` | setloader records | `records[i]['file']`/`['id']` | ✓ WIRED | pymol_bridge.py:198-202; bridge never parses SDFs (docstring + code confirm) |
| `setloader` | `molfile` + `molecule_data` | parse/gate/split + interaction_for | ✓ WIRED | setloader.py:47-48, 178, 281, 80-81 |
| `setup_logic._xtb_path_problems` | `xtbenv.validate_binary_path` | direct delegation | ✓ WIRED | setup_logic.py:119; cross-check test at test_setup_logic.py:403 |
| `gui.py`/`__init__.py` | anchor state | `run_plugin_gui → PluginDialog(anchor_state=state) → SetupTab` | ✓ WIRED | __init__.py:42-46; gui.py:43,49; collect_state writes back to anchor |
| `tests/test_*` | fixtures + real data | fixtures-first + real-file regression | ✓ WIRED | 433 tests green on fresh run |

### Requirements Coverage

| Requirement | Status | Blocking Issue |
|-------------|--------|----------------|
| SETUP-02 (demo dropdown / upload) | ✓ SATISFIED | — |
| SETUP-03 (preset box sizes) | ✓ SATISFIED | — |
| SETUP-04 (head molecule, default random) | ✓ SATISFIED | — |
| SETUP-05 (xtb path, auto-detect, xtb/xtb.exe) | ✓ SATISFIED | — |
| SETUP-06 (win cap + hessian warning) | ✓ SATISFIED | — |
| DATA-03 (≤3-ring gate, skip policy) | ✓ SATISFIED | — |
| INFRA-04 (srp_* namespace, fresh-process cleanup) | ✓ SATISFIED | — |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| serpentrum/gui.py | 9, 51 | 'placeholder' (Game/Spectra tabs) | ℹ️ Info | Intentional Phase-4/7 scope boundary, per ROADMAP |
| serpentrum/pymol_bridge.py | 158 | 'Phase-3 placeholder head' | ℹ️ Info | Documented semantics: records[0] at Apply; true randomization is game-start (Phase 4) |
| serpentrum/setloader.py | 35-38 | tempdir lifecycle note | ℹ️ Info | srp_upload_ tempdirs left to OS temp cleanup — documented, acceptable |

No TODO/FIXME/HACK, no empty handlers, no `console.log`-only or stub returns in any Phase-3 artifact. No `.exec_()` anywhere in GUI/BRIDGE (AST-gate enforced).

### Automated Evidence (re-run fresh during this verification)

- `python3.6 tests/run_gates.py` → **exit 0**: gate 1 (syntax + plugin-path safety) PASS, gate 2 (purity AST) PASS, gate 3 (unittest) PASS — **433 tests, 0 failures**.
- Recorded sentinel evidence (per SUMMARYs, not re-run per instruction): `SMOKE-OK SKELETON`, `SMOKE-OK VIEWER-BRIDGE`, `SMOKE-OK VIEWER-DEMO`; xtb 6.7.1pre 'normal termination'.
- Both smokes are regression-protected in `REQUIRED_SMOKES` (tests/run_gates.py:56-57).

### Human Verification Required

None outstanding. The full user-visible contract (SC1–SC5) was human-verified in real Windows PyMOL 2.5.0 across two checkpoint rounds, recorded as **APPROVED** in 03-08-SUMMARY.md (10/10 steps PASS), including:
- Upload rejection modal with reason 'tetracene: has 4 rings (limit is 3)' + acceptance path (step 4/5)
- Cleanup with a user-owned object ('ATP' survived; `cmd.get_names` → `['ATP']`, zero srp_*) (step 6)
- INFRA-04 fresh-process proof: .pse save → full PyMOL restart → session reload → Cleanup removes exactly srp_* again (step 7)
- xtb auto-detect status surfacing (step 8) and win-cap hessian warning (step 9)
The two checkpoint-round fixes (`ae27ffe` xtb-detect-on-toggle, `e8b3a9d` box linewidth) are present in git history and verified in code.

### Known Accepted Deviations (documented — not gaps)

1. `cmd.get_names('public_objects')` used instead of `all_objects` (raises in PyMOL 2.5.0) — documented in cleanup_srp docstring; semantics equivalent for the cleanup count.
2. `cmd.get_extent` nested-list unpacking — pinned to observed 2.5.0 return shape, documented in place_head.
3. Box z-depth analysis deferred to Phase 5 WITH measured extents (anthracene 9.526 Å < 10.0 Å depth; edge-on presentation forced by the 2D engine) — corrected note in 03-08-SUMMARY, options A/B recorded. Display depth 5.0 Å (`BOX_DISPLAY_Z`) is intentional for 2D-plane perception.
4. `smoke/02_dialog_smoke.py` informational FAIL — offscreen-Qt dead end, decision 01-05 (Phase 1 scope; the live-dialog contract is covered by human verification).

### Gaps Summary

None. All 5 success criteria are satisfied by substantive, wired artifacts; all 32 plan-level must-have truths verified; all 7 mapped requirements satisfied; the automated gate suite is green on a fresh run; and every user-visible claim was either machine-verified here or human-approved at the recorded checkpoint. Phase goal achieved.

---

_Verified: 2026-09-12_
_Verifier: OpenCode (gsd-verifier)_
