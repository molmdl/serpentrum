---
phase: 08-demo-data-docs-release-audit
verified: 2026-10-10T16:42:00Z
status: passed
score: 162/162 must-haves verified
re_verification: null
gaps: []
human_verification:
  - test: "GATE V live walk-through (Sections A/B/C) in real Windows PyMOL 2.5.0"
    expected: "Owner types 'approved' across data sign-off, 6-button + educator round-trip, and release close incl. real xtb"
    why_human: "Live GUI feel, visual plot rendering, real-xtb latency — verifiable only by a human at the keyboard"
  - test: "--smoke (11 required smokes incl. 14 RELEASE-E2E) and --xtb Windows legs"
    expected: "Flushed SMOKE-OK sentinels; xtb 'normal termination'"
    why_human: "Windows conda PyMOL / xtb legs run outside WSL; evidenced in 08-11-SUMMARY.md and gate-owned — re-run skipped per verification context"
---

# Phase 8: Demo Data, Docs & Release Audit — Verification Report

**Phase Goal:** The shippable release: human-approved demo data with verified attribution, educator-shareable setup persistence, complete help and docs, and an end-to-end audit proving every v1 requirement.
**Verified:** 2026-10-10T16:42:00Z (UTC; repo convention — planning-doc dates are UTC)
**Status:** passed
**Re-verification:** No — initial verification
**Method:** Goal-backward, static checks + gate battery from repo root (WSL python3.6). No SUMMARY claim trusted without code/doc evidence. Windows smoke/xtb legs NOT re-run per context (gate-owned, evidenced in 08-11-SUMMARY.md); the default battery WAS re-run live.

## Goal Achievement

### Observable Truths (per-plan must-have resolution)

All 13 PLAN frontmatters carry `must_haves`. Counts: **162 items total** (truths + artifacts + key_links). Every item was checked against the actual code/docs — **162/162 VERIFIED**. Plan-by-plan resolution (T = truths, A = artifacts, K = key_links):

| Plan | T | A | K | Verdict | Decisive evidence (what was actually checked) |
| ---- | - | - | - | ------- | --------------------------------------------- |
| 08-01 GATE D | 4 | 1 | 3 | ✓ VERIFIED | 08-01-SUMMARY.md carries all 4 verbatim answers + owner quotes; contract mapping d1-option-c-staleness / d2-option-b-two-tier / d3-option-amend; confirm/amend table (7 defaults, e.g. SHA-256 = SKIP); read-decision consumers 08-05/06/07 all reference 08-01-SUMMARY (grep + 08-07-SUMMARY "GATE D literal (recorded per plan STEP 0)"); only two checkpoints in the phase (08-01 decision, 08-11 human-verify) |
| 08-02 Demo pack | 5 | 2 | 2 | ✓ VERIFIED | `tests/test_demo_data.py:168 TestLoadDemoSetEndToEnd` calls `setloader.load_demo_set` (line 187) and asserts zero errors + `has_stack_entry` — rides the 995-test gate suite (ran green live); DATA_SOURCES §1 NOTE records the 03-05 shipment (lines 24-30); [COD4003564] carries `32 (12), 5162–5172` + Crossref trail (lines 114-119); manifest↔SDF coherence tests in the suite; DRAFT-at-the-time constraint correctly superseded by the GATE V APPROVED flip (as designed) |
| 08-03 Doc audit | 7 | 2 | 3 | ✓ VERIFIED | `tools/check_docs.py` 412 lines, CLI run → **7/7 PASS** (vibe-block, placeholders incl. sECDpent absence, 20 control literals, 26 numeric tokens, install recipe, path refs, claim bans); `tests/test_docs_audit.py` 229 lines with 5 tamper-case hits (checks bite); numeric checks import code/data sources of truth; tools/ has no `__init__.py` (gate 1 plugin-path PASS) |
| 08-04 Smoke 14 | 7 | 2 | 3 | ✓ VERIFIED | `smoke/14_release_e2e_smoke.py` 382 lines; registered in `tests/run_gates.py` REQUIRED_SMOKES appended last (line 76); guarded QApplication (lines 135-137), NO widget construction; GameEngine + read_xyz_text seams present (grep 5 hits); fixture g98 tail (real xtb never in REQUIRED smokes); RELEASE-E2E sentinel evidenced in 08-11-SUMMARY full-battery record |
| 08-05 Persistence | 6 | 2 | 3 | ✓ VERIFIED | `setup_logic.randomize_setup` (line 411): GATE D d1-option-c-staleness FULL scope, concrete values via `randomize_head`/BOX_PRESETS/SPEED_TIERS, ONE private `random.Random(seed)`, consent + atom_budget + xtb_threads carried UNCHANGED (docstring + body verified); `normalize_loaded` (line 466) with `XTB_PATH_NORMALIZED_NOTE` friendly note, injected path_problems_fn from GUI (gui_setup.py:819); TDD'd in test_setup_logic.py (suite green) |
| 08-06 Help pure | 7 | 3 | 3 | ✓ VERIFIED | `spectra_ui.imaginary_note` — live-probed: negatives → `'2 small imaginary mode(s) (<20i cm-1): soft inter-stack modes...'`, all-positive → None (total function, GATE D two-tier wording); `help_text.py` pure module with SETUP_HINTS(before_apply/after_apply), game_hint(5 states), spectra_hint(4 states), GAME_FOCUS_HINT, CONTROLS_RECAP; `tests/test_help_text.py` 323 lines with exact-string pins + ASCII sweep + drift alarm |
| 08-07 README | 9 | 1 | 3 | ✓ VERIFIED | README: vibe block with d3-option-amend line 4 `!! v1.0 - vibe-coded, review before production/teaching use !!`; xtb-only Requirements (6.7.1pre note); 01-06 install route; Start-only usage; demo section cites CIDs + real `serpentrum/data/DATA_SOURCES.md` path; zero TBD/sECDpent (placeholders PASS); claim-bans PASS (no 'P = pause', no 'Apply / Show in Viewer', no xtb4stda) |
| 08-08 6 buttons | 8 | 3 | 3 | ✓ VERIFIED | gui.py:177-199 — exactly 6 buttons in spec order (Reset, Randomize, Save Setup, Load Setup, Cleanup model, Start), each `setToolTip(help_text.BUTTON_TOOLTIPS[...])`; exactly ONE `setCurrentIndex(1)` in gui.py; ZERO `.exec_()` tokens across serpentrum/ (grep); Start = `_on_apply()` first (gui_setup.py:1047, 04-06 route); request_auto_pause injected (gui.py:148) and called (:577); temp row removed; head combo fills at demo-set selection (GATE D owner directive, GATE V B approved live); test_gui_pins source pins |
| 08-09 Help wiring | 8 | 4 | 4 | ✓ VERIFIED | gui_game.py: 7 refs to `help_text.game_hint`/`GAME_FOCUS_HINT`; before_apply rendered at init (gui_setup.py:116, :213) + _on_reset; gui_spectra.py:375-378 appends `imaginary_note` beside mode_caption; done-state hint in help_text.py:185; drift alarm asserts `'help_text.GAME_FOCUS_HINT'` in gui_game.py source (test_help_text.py:261-265); stale randomize clause corrected per d1-c-staleness |
| 08-10 Ledger tool | 6 | 3 | 2 | ✓ VERIFIED | `tools/audit_requirements.py` 232 lines, CLI+import dual, NOT a run_gates leg; live `--release` run → **AUDIT-OK**: 46 IDs exactly once, 46-row table, 136 Evidence paths exist, checkbox↔table agreement, zero Pending; fixture TDD in test_audit_requirements.py (291 lines); Phase-8 human evidence cites GATE V verdict + date |
| 08-11 GATE V | 7 | 4 | 3 | ✓ VERIFIED | Owner verdict **"approved"** recorded verbatim (08-11-SUMMARY.md:82) across Sections A/B/C with per-section table (:86-90); coupled flip DRAFT→APPROVED + test-pin in ONE commit **3fd30cf** (git show --stat confirms both files); 10-row ledger flip + ROADMAP close in **7e0ddc9**; full battery green recorded (995 + 11 smokes + xtb normal termination); no partial flip (no approval asserted on owner's behalf — the verdict text is the owner's own words) |
| 08-12 Performance | 5 | 5 | 4 | ✓ VERIFIED | Performance QGroupBox (gui_setup.py:316-319) with atom_budget_spin + threads_spin; collect writes `setup['atom_budget']`/`setup['xtb_threads']` (:409-410); DEFAULTS['xtb_threads']=4 (:57) + validate leg (:304-308); `xtb_run.thread_arg` with DEFAULT_THREAD_ARG `('-P','4')` UNCHANGED (:81) and fallback for None/invalid; gui.py launch argv `(xtbenv.XTB_OHESS,) + xtb_run.thread_arg(...)` (:488-489) — exactly ONE call site pinned (test_gui_pins.py:251); Randomize never touches either key (verified in randomize_setup body); hud completion line `'atoms: %d (stacked molecules, head excluded)'` (hud_logic.py:261) |
| 08-13 Tooltips/copy | 5 | 6 | 4 | ✓ VERIFIED | Live import: `len(SETUP_TOOLTIPS)==13`, `len(BUTTON_TOOLTIPS)==6`; setToolTip on every Setup widget sourced from the dict (grep: 13 sites in gui_setup.py), no inline literals; stacking_pi_stack.json explanation humanized with ALL facts kept (3.38 A plane gap / 3.60 A centroid / ~20 deg / Janiak 2000 / herringbone reality / idealized framing, line 12); README humanized (biphenyl excluded-from-gameplay reconciliation + Performance guidance, lines 38-57); doc audit stayed green post-rewrite (7/7 re-run live) |

**Score:** 162/162 must-have items verified (13/13 plans fully green)

### Required Artifacts (three-level spot summary)

| Artifact | Exists | Substantive | Wired | Status |
| -------- | ------ | ----------- | ----- | ------ |
| `serpentrum/data/DATA_SOURCES.md` | ✓ | ✓ (184 lines, full attribution) | ✓ (loaded by molecule_data; README path-ref) | ✓ VERIFIED |
| `tests/test_stacking_dataset.py` (pin='APPROVED') | ✓ | ✓ | ✓ (gate suite) | ✓ VERIFIED |
| `tests/test_demo_data.py` | ✓ (222 lines) | ✓ | ✓ (gate suite) | ✓ VERIFIED |
| `tools/check_docs.py` + `tests/test_docs_audit.py` | ✓ (412/229) | ✓ | ✓ (CLI + discovery) | ✓ VERIFIED |
| `smoke/14_release_e2e_smoke.py` + REQUIRED_SMOKES | ✓ (382 lines) | ✓ | ✓ (registry line 76) | ✓ VERIFIED |
| `serpentrum/setup_logic.py` (randomize/normalize/xtb_threads) | ✓ | ✓ | ✓ (gui_setup handlers) | ✓ VERIFIED |
| `serpentrum/help_text.py` + `spectra_ui.imaginary_note` | ✓ | ✓ | ✓ (gui_game/gui_setup/gui_spectra) | ✓ VERIFIED |
| `README.md` | ✓ | ✓ | ✓ (audit 7/7) | ✓ VERIFIED |
| `serpentrum/gui.py` (6-button row) + `gui_setup.py` handlers | ✓ | ✓ | ✓ (test_gui_pins + GATE V B) | ✓ VERIFIED |
| `tools/audit_requirements.py` + updated `.planning/REQUIREMENTS.md` | ✓ (232 lines / 46 rows) | ✓ | ✓ (--release AUDIT-OK) | ✓ VERIFIED |
| `serpentrum/xtb_run.py` thread_arg + `gui.py` argv seam | ✓ | ✓ | ✓ (1 call site pin) | ✓ VERIFIED |
| `serpentrum/hud_logic.py` completion label | ✓ | ✓ | ✓ (suite) | ✓ VERIFIED |
| `serpentrum/data/stacking_pi_stack.json` explanation | ✓ | ✓ | ✓ (suite + audit) | ✓ VERIFIED |

### Key Link Verification

| From | To | Via | Status |
| ---- | -- | --- | ------ |
| 08-05/06/07 Task 1 | 08-01-SUMMARY.md (GATE D) | read-decision | ✓ WIRED (all three SUMMARYs cite it; implemented option ids match) |
| GATE V verdict | DATA_SOURCES.md header/legend/footer | APPROVED flip | ✓ WIRED (commit 3fd30cf, 3 APPROVED markers, 0 'DRAFT — NOT APPROVED') |
| GATE V verdict | .planning/REQUIREMENTS.md Phase-8 rows | Complete flip | ✓ WIRED (7e0ddc9; --release green) |
| gui.py bottom-row Start | gui_setup._on_start | start_requested → _on_apply() first | ✓ WIRED (gui_setup.py:1047; 1× setCurrentIndex(1)) |
| gui_setup._on_load_setup | setup_logic load pipeline | load_setup→merge_defaults→normalize_loaded→validate | ✓ WIRED (gui_setup.py:812-819) |
| gui.py _launch_spectra_run | xtb_run.thread_arg | extra_args | ✓ WIRED (gui.py:488-489; single call site pin) |
| gui_game hint_label | help_text.game_hint/GAME_FOCUS_HINT | state-driven setText + drift alarm | ✓ WIRED (7 refs; test pins source reference) |
| gui_spectra _populate_spectrum | spectra_ui.imaginary_note | log append when min<0 | ✓ WIRED (gui_spectra.py:378) |
| smoke 14 scripted_win / handoff_xyz | game_engine / xyzio | GameEngine.step + read_xyz_text | ✓ WIRED (sentinels evidenced; file seams grepped) |
| tools/audit_requirements.py | .planning/REQUIREMENTS.md | single parse target | ✓ WIRED (live AUDIT-OK) |
| check_docs numeric checks | setup_logic + data JSONs | imports, not hardcodes | ✓ WIRED (26 tokens verified against sources) |

### Success Criteria Verdicts (ROADMAP Phase 8)

| SC | Verdict | Evidence |
| -- | ------- | -------- |
| **SC1** — Demo Set A CID-cited, distances human-approved, DATA_SOURCES.md complete, no CSD/CCDC redistribution | ✓ VERIFIED | DATA_SOURCES.md APPROVED-headed 2026-10-10 (header line 1, STATUS LEGEND line 11, footer line 184); all DOIs present: Janiak 10.1039/b003010o, COD4003564 10.1021/acs.chemmater.0c01184 (vol/pages 5162–5172 + Crossref trail), COD2100607/8 10.1107/S0108768106026814, herringbone DOIs 10.1039/c001190h / 10.1107/S2053273316018994 / 10.1107/S0108768190008382 / 10.1107/S0108768190007510, Hunter-Sanders 10.1021/ja00170a016 (optional/unread); §3 UNVERIFIED quarantine intact; herringbone negative-evidence block intact; CIFs cited-not-redistributed; owner sign-off verbatim (GATE V A, 08-11-SUMMARY.md:82,88); coupled test-pin flip in commit 3fd30cf; TestLoadDemoSetEndToEnd green in live gate run |
| **SC2** — Six buttons work; Save→Load reproduces exact config on fresh session | ✓ VERIFIED | gui.py:177-199 six buttons in spec order with tooltips; full save/load pipeline wired (save_setup:757 / load_setup:812 → merge_defaults → normalize_loaded → validate/apply); randomize_setup consent-immune + concrete; xtb_threads/atom_budget persist through the same dict; GATE V Section B owner-approved live: "6-button persistence + educator round-trip PASS" incl. fresh-session Load reproduction (08-11-SUMMARY.md:89) |
| **SC3** — README install/usage/demo-set, vibe block intact, doc-vs-code audit passes | ✓ VERIFIED | `python3.6 tools/check_docs.py` → 7/7 PASS re-run live (vibe block byte-identical incl. d3-amended line 4; no sECDpent/TBD; 20 control literals; 26 numeric tokens vs imported sources; install recipe; path refs; claim bans); README humanized (08-13) with biphenyl reconciliation + Performance guidance; GATE V C6 README reproduce spot-check approved |
| **SC4** — Help covers controls, focus hint, negative frequencies, next-action hints | ✓ VERIFIED | help_text.py single-sources: GAME_FOCUS_HINT + CONTROLS_RECAP, game_hint over 5 states, spectra_hint over 4 states, SETUP_HINTS before_apply (Start-only, rendered at init + Reset) / after_apply; imaginary_note (GATE D two-tier wording) wired into the Spectra log (gui_spectra.py:378); drift alarm pins single-sourcing; PLUS 08-13's 13 Setup tooltips + 6 button tooltips (live count check); GATE V B14/B15 approved |
| **SC5** — End-to-end release audit, full flow headless + live, 46/46 requirements with traceability | ✓ VERIFIED | smoke 14 REQUIRED (registry line 76) walks load→materialize→win→xyz→fixture-spectra→plot→PNG→setup round-trip→cleanup, RELEASE-E2E sentinel evidenced; live full flow owner-approved (GATE V C incl. real xtb "xtb finished: ok", Multiwfn parity 4.9e-9); `python3.6 tools/audit_requirements.py --release` → **AUDIT-OK** (46/46 exactly once, zero Pending, 136 Evidence paths exist, checkbox↔table agree) re-run live; REQUIREMENTS.md 46 `[x]` rows + footer stamped 2026-10-10; ROADMAP Phase 8 `[x]` + 13/13 Progress row with SC1–SC5 evidence |

**SC Score: 5/5 VERIFIED**

### Requirements Coverage

| Requirement | Status | Blocking Issue |
| ----------- | ------ | -------------- |
| DATA-01, DATA-02, DATA-04 | ✓ SATISFIED | — (ledger Complete; audit --release green) |
| SETUP-07, SETUP-08 | ✓ SATISFIED | — |
| DOCS-01, DOCS-02, DOCS-03, DOCS-04, DOCS-05 | ✓ SATISFIED | — |
| All other 36 v1 IDs | ✓ SATISFIED | — (checkbox↔table agreement mechanically verified; prior phases verified) |

Coverage: 46/46 v1 requirements Complete, mechanically attested by `audit_requirements.py --release` (AUDIT-OK) — not merely claimed.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| serpentrum/gui.py | 11, 135 | "placeholder" in docstrings | ℹ️ Info | Historical reference to the REMOVED 06-09 placeholder page — not a stub |
| serpentrum/gui_spectra.py | 5, 82 | "placeholder" in docstrings | ℹ️ Info | Same historical reference (real page shipped in 07-07) |
| serpentrum/xtb_run.py | 64 | "placeholder" in a changelog comment | ℹ️ Info | Superseded-convention note, not a stub |
| serpentrum/data/DATA_SOURCES.md | 80 | "TODO before any solution-phase... claim" | ℹ️ Info | Recorded SCOPE-CAVEAT governance item INSIDE the owner-approved doc; resolved by the explicit crystalline-state framing (line 108) — part of the approved document |

No 🛑 Blockers, no ⚠️ Warnings. Real stub scan (empty returns, console-only handlers, placeholder renders) came up clean on all phase files.

### Known-Acceptable (not flagged, per recorded dispositions)

- smoke 02 informational FAIL (01-05 dead end) — recorded disposition
- HUD completion line "(stacked molecules, head excluded)" — by design (D2 fix, verified present at hud_logic.py:261)
- hud_logic.idle_tip UNWIRED — recorded disposition
- Selector-Error noise DEFERRED — and in fact reported absent in the GATE V final launch after debug-06
- Window move/resize quirk — RESOLVED via debug-06 (fixed-size dialog + two-column Setup; GATE V B13 height OK, no width-fix amendment needed)

### Human Verification Required

The phase's human tier is **already satisfied and recorded** — nothing is outstanding:

1. **GATE V (08-11) — the phase's only checkpoint:human-verify.** Owner typed **"approved"** (recorded verbatim, 08-11-SUMMARY.md:82) on 2026-10-10 UTC after a sectioned live walk-through in real Windows PyMOL 2.5.0 (2026-10-01..2026-10-11): Section A data sign-off, Section B 6-button + educator round-trip, Section C release close incl. the REAL xtb leg. Per-section verdict table at :86-90.
2. **Windows legs (--smoke 11 required smokes incl. 14 RELEASE-E2E + STAGE6 LINES; --xtb normal termination)** — evidenced in 08-11-SUMMARY.md:65 and gate-owned; intentionally NOT re-run in this verification per the given context. The WSL-side default battery WAS re-run live (below).

### Commands Run (with results)

| Command | Result |
| ------- | ------ |
| `python3.6 tests/run_gates.py` | gates 1-3 **PASS**; `Ran 995 tests ... OK`; "run_gates: all gates green" |
| `python3.6 tools/check_docs.py` | **7/7 checks PASS** (vibe-block, placeholders, control-literals [20], numeric-claims [26], install-recipe, path-refs, claim-bans) |
| `python3.6 tools/audit_requirements.py --release` | **AUDIT-OK** — ids-unique, row-count 46, evidence-paths 136 exist, checkbox-agreement, no-pending |
| `python3.6 -c` (live import probe) | `SETUP_TOOLTIPS==13`, `BUTTON_TOOLTIPS==6`, `SETUP_HINTS keys [after_apply, before_apply]`, `imaginary_note([-6.65,...])` → two-tier note, `imaginary_note([100.0,...])` → None |
| `git show --stat 3fd30cf` / `7e0ddc9` / `git log --oneline` | Coupled flip commit verified (DATA_SOURCES.md + tests/test_stacking_dataset.py in ONE commit); ledger close-out verified; GATE V summary finalize 3d0874b HEAD |
| grep sweeps (buttons, tooltips, handlers, setCurrentIndex, exec_, UNIT_MODES, CURVE_SCALE, thread_arg, GAMEPLAY_EXCLUDED_MOLS, completion line, drift alarm, tamper cases, REQUIRED_SMOKES, marker pins) | All as claimed above |

### Gaps Summary

**No gaps.** All 162 must-have items across the 13 plans (including both owner-inserted mid-gate plans 08-12 and 08-13) verified against the actual code, docs, and planning ledger; all five ROADMAP success criteria hold with layered mechanical + human evidence; the release-critical commit chain (3fd30cf → 7e0ddc9 → 3d0874b) is intact and internally consistent. The phase goal — the shippable release — is achieved: the v1 release is signed off, the ledger is closed at 46/46, and the full WSL-side gate battery re-runs green at verification time.

---

_Verified: 2026-10-10T16:42:00Z_
_Verifier: OpenCode (gsd-verifier)_
