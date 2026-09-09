---
phase: 02-pure-core-game-chemistry-logic
verified: 2026-09-10T02:00:00Z
status: passed
score: 4/4 phase success criteria verified (all supporting must-haves from 14 plans verified)
gaps: []
---

# Phase 2: Pure Core — Game & Chemistry Logic Verification Report

**Phase Goal:** Every game and chemistry rule exists as a stdlib-only pure module, unit-tested on WSL python3.6 with zero stubs — spectra parsing driven by the committed real xtb fixtures (`.planning/research/xtb-spike-fixtures/`), and the human demo-data approval track started.
**Verified:** 2026-09-10T02:00:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (Phase Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Stacking is data-driven: interaction mode + distance + citation load from a validated data file, never code constants; tests prove placement math reproduces the file's stored geometry [STACK-02] | ✓ VERIFIED | `serpentrum/data/stacking_pi_stack.json` holds mode `pi_stack`, `distance_a: 3.383`, `lateral_offset_a: 1.231`, citation `janiak2000`, `status: APPROVED`. `stacking.py` contains NO hardcoded stacking geometry (only clash-gate constants `CLASH_THRESHOLD_A=2.5`, `PLANARITY_TOL_A=0.15`). Integration tests derive expectations FROM THE FILE: `test_stage1_dataset` asserts `expected_centroid == sqrt(d²+l²)`; `test_stage3b` proves measured placement matches within 1e-4; `test_composed_centroid_rounds_cleanly` (3.60 Å) and `test_off_normal_angle_is_twenty_degrees` (20°) pass. Validator tamper-proofing proven (`test_mangled_dataset_is_rejected`). |
| 2 | Spectra parser on committed real xtb fixtures (phenol, CO₂, π-stacked dimer) extracts frequencies, IR intensities, mode vectors — negatives and zero-intensity included — and fails loudly on the corrupt fixture | ✓ VERIFIED | `parse_g98` on `tests/fixtures/xtb/g98.out`: 26 atoms, 72 modes, first frequency −31.9175, per-atom 3-float vectors, negatives kept (`test_spectra_g98`, all pass). `parse_vibspectrum`: dimer 78 modes (real modes 7/8/9 negative kept), CO₂ 8 modes with 5 trivial/3 real and the zero-intensity 2593 cm⁻¹ row honestly omitted by `real_modes` default (threshold-documented). `broaden()`: Gaussian, CO₂ synthetic peak at ~2350 family, empty-modes zero curve, zero-intensity mode exact-zero contribution. Unified `parse_text`/`parse` dispatcher + g98↔vibspectrum index correspondence (72 modes, 0 mismatches, offset=6). Loud failures: `bad.log` raises `SpectraParseError` naming the missing frequency section; `******` overflow and mid-file truncation raise with line numbers (`test_spectra_robustness`). |
| 3 | xtb success contract (exit 0 + "normal termination" on stderr + expected output files) and `xtb`/`xtb.exe` detection are unit-tested pure functions | ✓ VERIFIED | `serpentrum/xtbenv.py:51 evaluate_run(exit_code, stderr_text, expected_files, present_files)` — pure, 3 legs tested independently (`test_leg_independence`); fixture-driven cases: success fixtures pass, `repro_oh` (stderr success WITHOUT files) rejected, bad fixture fails with problem names. `detect_binary` (line 141): configured path → `which_fn('xtb.exe')` Windows-conda-first → `which_fn('xtb')` Linux fallback, dependency-injected `which_fn`; probed order + fallthrough tested (`test_windows_conda_env_probed_before_linux`, `test_invalid_configured_path_falls_through_to_which`, `test_nothing_found_returns_none`). |
| 4 | Full python3.6 unittest suite passes on WSL with zero sys.modules stubs and stdlib-only pure modules [INFRA-02 discipline] | ✓ VERIFIED | `python3.6 tests/run_gates.py` → all 3 gates green (syntax+plugin-path, purity AST, unittest). `python3.6 -m unittest discover -s tests -p "test_*.py"` → **Ran 383 tests … OK** (0.890 s). `grep -rn "sys.modules\[" tests/ serpentrum/ tools/` → **zero hits**. `python3.6 tools/check_purity.py` → `check_purity: clean`. All pure-module imports are stdlib-only: `math`, `json`, `os`, `random`, `collections`, `shutil`, `tempfile`, `collections.namedtuple`. Zero TODO/FIXME/placeholder code markers in `serpentrum/*.py` and `serpentrum/data/*.json`. |

**Score:** 4/4 phase success criteria verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `serpentrum/spectra.py` | g98 + vibspectrum parsers, real_modes filter, broaden, unified dispatcher | ✓ VERIFIED | 505 lines; public API `parse_g98_text/parse_g98`, `parse_vibspectrum_text/parse_vibspectrum`, `real_modes`, `broaden`, `parse_text`, `parse`; stdlib imports only; zero stub patterns |
| `serpentrum/xtbenv.py` | 3-leg success contract + detection + argv/rundir | ✓ VERIFIED | 207 lines; `evaluate_run`, `validate_binary_path`, `detect_binary`, `build_argv`, `new_run_dir`; pure |
| `serpentrum/xyzio.py` | .xyz writer/reader | ✓ VERIFIED | 178 lines; round-trips all 4 xyz fixtures, fixed-point second write byte-identical |
| `serpentrum/stacking.py` | placement math + clash gate | ✓ VERIFIED | 305 lines; `ring_frame`, `place_pickup`, `check_clash`; reproduces dimer2 fixture exactly |
| `serpentrum/molecule_data.py` | manifest + stacking schemas, validated loader | ✓ VERIFIED | 362 lines; bool-trap rejection, path contract, DRAFT/APPROVED shipping policy |
| `serpentrum/game_engine.py` | continuous-2D engine, rules, rigid-pivot turns | ✓ VERIFIED | 785 lines; core + rules + turns (sweep, refusal 3-leg, epoch safety) |
| `serpentrum/setup_logic.py` | defaults, validation, save/load, randomize | ✓ VERIFIED | 265 lines; never-raises validator, sorted-key JSON round-trip, seeded RNG |
| `serpentrum/cgo_build.py` | local CGO constants + box + mode arrows | ✓ VERIFIED | 235 lines; 15 constants pinned to verified table; box_cgo 106-float stream; arrow/sphere builders |
| `serpentrum/data/stacking_pi_stack.json` | validated stacking dataset, APPROVED | ✓ VERIFIED | schema_version 1; one interaction `pi_stack_pd`; APPROVED; 3 citations all `approved: true` |
| `serpentrum/data/DATA_SOURCES.md` | attribution document | ✓ VERIFIED | DRAFT-headed (intentional — full DATA-02/04 sign-off is Phase 8; NOT a gap); required markers asserted by `test_stacking_dataset.TestDataSourcesAttribution` |
| `tests/fixtures/xtb/` | fixture copies | ✓ VERIFIED | Exactly 17 files, **all byte-identical** to `.planning/research/xtb-spike-fixtures/` (cmp OK on every file) + `synthetic/` (plan-created inputs, not source copies — as designed) |
| `tests/test_*.py` | 18 test modules | ✓ VERIFIED | 383 test methods, all pass on python3.6 |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| dataset JSON | placement math | `molecule_data.load_stacking` → `stacking.place_pickup` | ✓ WIRED | Integration STAGE 1/3b: (d, l) read from file, composed centroid 3.60001 Å @ 19.998° reproduced by real placement on the dimer2 ring frame within 1e-4 |
| fixtures | parser | `tests/fixtures/xtb/*` → `parse_g98`/`parse_vibspectrum`/`parse` | ✓ WIRED | Byte-identity test + 5 parser test modules consume only the copies (single-copy rule) |
| xtb run artifacts | contract | `evaluate_run` on fixture bytes | ✓ WIRED | `test_evaluate_run_fixtures` drives all legs from `ohess.err/.log`, `repro_oh.*`, `bad.*` |
| dataset | loader schema | JSON → `load_stacking` validator | ✓ WIRED | Loads clean as shipped; mangled variants rejected with exact research-derived messages |
| pure modules | integration chain | `test_integration_pure_core.py` | ✓ WIRED | 6-stage chain (dataset→geometry→placement+clash→xtb contract→spectra→xyz round-trip) all pass |

### Requirements Coverage

| Requirement | Status | Blocking Issue |
|-------------|--------|----------------|
| STACK-02 (Phase 2) | ✓ SATISFIED (code) | None. Note: REQUIREMENTS.md tracker row still reads "Pending" while Phase 1 rows read "Complete" — tracker flip is orchestrator housekeeping at phase close, not phase work. ℹ️ Info only. |
| SPECTRA-03/05 pure halves | ✓ SATISFIED | Broadening + table-data (frequencies/intensities/vectors incl. negatives & zero-intensity) ready for Phase 7 UI wiring |
| SPECTRA-02 / SETUP-05 pure halves | ✓ SATISFIED | Success contract + xtb/xtb.exe detection ready for Phase 6 async runner |
| INFRA-02 discipline | ✓ HELD | Purity AST gate green; zero sys.modules stubs; stdlib-only |
| DATA-02 (approval track started) | ✓ SATISFIED (for this phase) | Human decision made: option-a APPROVED; full DATA-02/04 checklist sign-off deliberately deferred to Phase 8 |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `serpentrum/game_engine.py` | 52 | word "placeholder" in docstring — describes a deliberately pinned tunable speed constant (3.0), asserted by `test_speed_constant_pinned` | ℹ️ Info | None — documented design, not an unfinished stub |
| `serpentrum/gui.py` | 7, 13 | "placeholder tabs" | ℹ️ Info | Phase 1 declared scope; real tabs land Phases 3/4/7 per ROADMAP |
| `serpentrum/molecule_data.py` | 29 | docstring mentions "3.6 A" | ℹ️ Info | Documentation reference to research, not a code constant; actual geometry flows from the JSON |
| `.planning/REQUIREMENTS.md` | 144 | STACK-02 tracker row "Pending" | ℹ️ Info | Orchestrator housekeeping at phase close; substance verified |

No 🛑 Blocker or ⚠️ Warning anti-patterns. Zero TODO/FIXME/XXX/HACK in shipped modules or data JSON.

### Plan-Scope Leak Check

- `serpentrum/data/` contains exactly `DATA_SOURCES.md` + `stacking_pi_stack.json` — **no stray `demos/` dir**.
- No GUI/pymol/PyMOL imports in any pure module (grep hits are docstrings only; the authoritative AST purity gate is green).
- All 14 plans have SUMMARYs; all 14 plans' scopes delivered (verified via tests + artifacts above).

### Documented Plan-Text Corrections (verified correct — NOT gaps)

| Plan | Correction | Verified |
|------|-----------|----------|
| 02-01 | Displacement-row token formula: row = 2 + (coords/ncols) tokens (plan's 2+3·ncols was self-contradictory); committed fixture still parses 11-token rows / 3-float tuples | ✓ 02-01-SUMMARY:43-46,136-140 |
| 02-08 | box_cgo = 106 floats (8 header + 96 vertex + 2 footer; plan said 90, forgot VERTEX opcodes); empty spheres 5 (plan said 4) | ✓ 02-08-SUMMARY:51,106-109 |
| 02-12 | Phenol eigvals 39 = 3N (first 6 ≈0 trivial, remaining 33 = 3N−6 real, min 218.56) | ✓ 02-12-SUMMARY:17,76 |
| 02-13 | Boundary-refusal position (4,6) not (4,10) — rotation arithmetic fixed, refusal conclusion unchanged | ✓ 02-13-SUMMARY:102-103 |

### Human Verification Required

None outstanding for this phase's goal. The one blocking human decision (02-11 checkpoint) was **resolved: option-a APPROVED** — dataset carries `status: APPROVED` with `distance_a 3.383` / `lateral_offset_a 1.231` (3.383 = 3.6·cos20°, 1.231 = 3.6·sin20° → composed 3.60001 Å @ 19.998°), all three citation `approved: true`. `DATA_SOURCES.md` intentionally remains DRAFT-headed (full DATA-02/04 checklist sign-off is Phase 8) — per plan, **not a gap**. Visual/runtime behavior (viewer rendering, spectra UI) is Phase 3+/7 scope.

### Gaps Summary

**No gaps.** All four phase success criteria verified against the actual codebase: 383/383 tests green on WSL python3.6, all three gates green, purity clean, zero `sys.modules` stubs, zero code-level TODO/FIXME markers, 17 fixture copies byte-identical to the committed research fixtures, stacking geometry lives exclusively in the validated APPROVED JSON file and the placement math provably reproduces it. All four documented executor plan-text corrections confirmed accurate.

### Evidence Log (commands run)

```
python3.6 tests/run_gates.py                  → all 3 gates green, exit 0
python3.6 -m unittest discover -s tests -p "test_*.py"
                                              → Ran 383 tests in 0.890s — OK
python3.6 tools/check_purity.py               → check_purity: clean
grep -rn "sys.modules\[" tests/ serpentrum/ tools/  → 0 hits
cmp tests/fixtures/xtb/<f> .planning/research/xtb-spike-fixtures/<f>  → 17/17 identical
grep -E "3\.383|1\.231|3\.60" serpentrum/{stacking,game_engine,molecule_data}.py
                                              → docstring mentions only; no code constants
grep -rn -E "TODO|FIXME|XXX|HACK" serpentrum/*.py serpentrum/data/*.json → 0 hits
grep -E "^(import|from) " serpentrum/*.py     → stdlib only (math/json/os/random/collections/shutil/tempfile/namedtuple)
cat serpentrum/data/stacking_pi_stack.json    → APPROVED, option-a values, 3 approved citations
```

---

_Verified: 2026-09-10T02:00:00Z_
_Verifier: OpenCode (gsd-verifier)_
