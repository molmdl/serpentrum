# Phase 8: In-Game Help + Documentation (DOCS-01/03/04) - Research

**Researched:** 2026-09-27
**Domain:** Documentation surfaces (README, in-game help text, doc-vs-code audit) for the serpentrum PyMOL plugin
**Confidence:** HIGH for the text-surface inventory + seam analysis (read directly from shipped code and gates); MEDIUM for help-text wording/cutoffs (owner sign-off required); LOW for nothing material here — no unverified external claims, every fact below cites a repo file+line

## Summary

All six research questions were answered against the shipped code, the planning record, and the
human-verify checkpoints. The plugin already has a substantial, owner-approved text surface: every
tab renders at least one help-adjacent label, and two of the four DOCS-03 bullets are already
satisfied (controls hints exist; the "click the 3D viewer" focus hint exists in THREE places). The
real gaps are: the negative-frequencies explanation line (a deferred seam, now in DOCS-03 scope),
and a *state-aware* next-action hint per screen (today's hints are static or absent).

The README has four structural TBD sections (Usage / Demo set / Project Structure / Acknowledgements),
one wrong-or-unverified install recipe (it does not match the 01-06 human-verified install route),
one broken internal reference (`DATA_SOURCES.md` actually lives at `serpentrum/data/`),
and an over-claimed xtb prerequisites list (xtb4stda/std2 are never invoked by the v1 `xtb --ohess`
pipeline). The "leftover sECDpent name" claimed in PROJECT.md/ROADMAP.md is **absent from README.md
(and spec.md)** — it persists only inside `.planning/` prose; the audit should *verify absence*, not
assume a fix is needed.

Recommended architecture: one new PURE module `serpentrum/help_text.py` (auto-classified PURE,
zero registration edits) holding the new help strings as builders/constants, consumed by thin GUI
wiring — the hud_logic/spectra_ui/budget_guard pattern proven across 95 plans — plus a mechanical
audit tool `tools/check_docs.py` (+ `tests/test_docs_audit.py` wrapper, the check_purity dual
CLI/import precedent) that greps every doc claim against code literals and data JSON.

**Primary recommendation:** Put new help text in a PURE `help_text.py`, pin it with py3.6 unit
tests (the audit then asserts doc strings == these literals), and make DOCS-04 a two-leg audit:
mechanical `check_docs.py` (in the WSL gate) + a Windows-PyMOL reproduce checklist (UAT md,
the manual_plot_check.py convention).

---

## 1. Text-Surface Inventory (per tab)

Every existing user-visible string surface, with file+line and DOCS-03 coverage verdict.

### 1a. Setup tab — `serpentrum/gui_setup.py` (+ `setup_logic.py`)

| Surface | File:Line | Current text (source of truth in parens) | Notes |
|---|---|---|---|
| Group titles | gui_setup.py:169,186,192,198,210,218,226 | 'Molecule set', 'Box', 'Head molecule', 'xtb', 'Win cap', 'Speed', 'Generic stacking' | audit-assertable literals |
| Row labels | gui_setup.py:172,178,188,194,200,206,212,220 | 'Demo set:', 'File:', 'Preset:', 'Head:', 'Mode:', 'Path:', 'Molecules:', 'Tier:' | |
| Demo combo items | gui_setup.py:97-100 | 'Demo Set A' house pattern + 'Upload...' (`_UPLOAD_SENTINEL`) | built from `setup_logic.KNOWN_SETS` |
| Upload placeholder | gui_setup.py:104-105 | 'Click Browse to choose a .sdf or .mol2 file' | |
| xtb auto checkbox | gui_setup.py:118-119 | 'Auto-detect (use xtb from PATH)' | |
| xtb path placeholder | gui_setup.py:121 | 'Manual xtb executable path' | |
| Hessian warning (cap > 10) | gui_setup.py:127-130,376-384 ← setup_logic.HESSIAN_WARNING (setup_logic.py:132-135) | 'hessian cost scales ~N^3; a ~100-atom snake takes about 1-2 min on a typical 4-core/8-thread laptop (measured 84-101 s; thread-capped runs slower, up to ~5 min single-threaded)' | CALIBRATED numbers (06-CALIBRATION.md) — README must quote these or nothing |
| Generic consent checkbox | gui_setup.py:143-145 | 'Allow generic pi-stack for uploads (illustrative geometry - user-approved)' | 5.2-09 owner-approved DRAFT literal |
| Generic consent sub-line | gui_setup.py:146-149 | 'reuses the approved Set A pi-stack geometry (3.60 A @ 20 deg off-normal) for uploads carrying a planar aromatic 6-ring' | ALWAYS-visible word-wrapped QLabel — the precedent for any new hint sub-line |
| Status label states | gui_setup.py:153,409-413,426-434,539-540,619-620,649,671-672 | 'ready' / 'errors: …' / 'warning: …' / 'xtb: <path>' / 'xtb not found - set a manual path or add xtb to PATH' / 'load errors: …' / 'load failed: …' / success parts join (623-649: 'Box + head materialized' + 'head will be randomized at game start' + 'xtb: …' + absorbed `hud_logic.stack_mode_note` C2 clause) / 'Cleanup removed %d srp_* object(s)' | success status contains NO next-action clause — 'press Start' never stated |
| Modals | gui_setup.py:507-508,537-538,617-618 | QMessageBox.warning titles 'Cannot apply', 'Upload rejected'/'Cannot load set', 'Load failed' | |
| Temp buttons | gui_setup.py:158-161 | 'Apply / Show in Viewer', 'Cleanup', 'Start' | Phase 8 replaces with canonical 6-button row (gui.py:129-130 reserved) — DOCS copy must track whichever ships |

**DOCS-03 coverage here: none of the four bullets** (no controls text — correct, controls are not
Setup's concern; no next-action hint — GAP 1).

### 1b. Game tab — `serpentrum/gui_game.py` (+ `hud_logic.py`, `input.py`)

| Surface | File:Line | Current text | Notes |
|---|---|---|---|
| **Hint label (static)** | gui_game.py:320-323 | 'Click Start on the Setup tab. Steer with arrow keys; click the 3D viewer first if keys seem dead.' | **Focus hint EXISTS (DOCS-03 bullet 2)** — but NEVER updates per state → GAP 3 |
| **Wizard prompt (viewer-focus hint #2)** | input.py:92-95 (`KeySteerWizard.get_prompt`) | 'serpentrum: click the 3D viewer, then steer with arrow keys' | **Focus hint EXISTS** — rendered in PyMOL wizard area during play |
| Auto-pause line (focus hint #3) | gui_game.py:1313-1314 | 'auto-paused (dialog took focus - click Resume, then the 3D viewer)' | from `request_auto_pause` (focusInEvent safety net, gui.py:333-345) |
| Countdown | gui_game.py:299,616-622 | 'ready' → '3','2','1' → 'GO!' (label + info-box echo) | |
| Pre-run info lines | gui_game.py:450-465 | `hud_logic.stack_mode_note` (C1 zero-stackable), `hud_logic.generic_consent_note` (STACK-06 disclosure), `hud_logic.speed_note` ('speed: normal (6.0 A/s) - steering cadence and turn time are unchanged'), 'Get ready...' | once per run, owner-approved order |
| Play lines | gui_game.py:658,748,751,754,1106,1283,1294,1353 | 'Move with the arrow keys.' / 'crashed into %s' / `budget_text()` ('atom budget exceeded - spectra on this snake may be slow') / 'YOU WIN' / `resume_note` ('placement refused - run continues (cap not reached yet)') / 'paused' / 'resumed' / 'run over: %s' | |
| Pickup/skip lines | gui_game.py:1060,1501-1522 ← hud_logic.py:94-118 | `pickup_block` ('+ <name>: pi-pi stacking (parallel-displaced), 3.38 A plane gap (centroid 3.60 A @ 20.0 deg off-normal) - <VERBATIM explanation> [Janiak 2000]') — values COMPOSED from dataset (distance_a=3.383, lateral_offset_a=1.231 → sqrt/atan2) | dataset-VERBATIM chemistry; no fabrication surface; ReasonCoalescer '(xN)' anti-spam (hud_logic.py:314-355) |
| Skip-reason map | hud_logic.py:57-78 | SKIP_NO_ENTRY 'no verified stacking entry for this molecule (no invented chemistry)' / SKIP_MODE / SKIP_NO_RING / SKIP_GENERIC_NO_RING 'no aromatic ring for generic pi-stack' / SKIP_NONPLANAR / REFUSE_ATOM 'placement clashes' | |
| Turn refusal (DEFENSIVE) | hud_logic.py:492-516 | 'turn refused: <reason> (+ why clause)' | engine emits none since 2026-09-20 owner directive (180-only refusal, dropped at request time) |
| Completion lines | gui_game.py:1401-1406 ← hud_logic.py:247-294 | 4 count lines ('result:', 'score: %d molecule(s) stacked', 'snake: %d molecules (incl. head)', 'atoms: %d (spectra input size)') + breakdown_lines (stacked/refused groups with citation) | NO next-action clause → GAP 3 (Get Spectra enable is affordance-only) |
| HUD row | gui_game.py:308-309,332-336 | 'Elapsed:' + '0:00' / 'Molecules' + 'Remaining: N/-' | |
| Buttons | gui_game.py:311-318,1282,1293 | 'Pause'/'Resume' (checkable), 'Restart', 'Get Spectra' (enabled only by `_present_completion`, gui_game.py:1430) | |
| External feed | gui_game.py:1524-1533 ← gui.py:270-287 | `log_external` mirrors launch/verdict lines into the info box | |
| idle tips | hud_logic.py:297-302 (`idle_tip`) | 'tip: <VERBATIM dataset explanation>' round-robin | **built + pinned in tests/test_hud_content.py but NO GUI CALLER (grep: zero call sites in gui_game.py)** — flagged in Open Questions Q5 |

**DOCS-03 coverage here: controls ✓ (hint_label + wizard prompt), focus hint ✓ (THREE
instances), negative-freq ✗ (not Game's screen), next-action ✗ (static hint only).**

### 1c. Spectra tab — `serpentrum/gui_spectra.py` (+ `gui_plot.py`, `plot_logic.py`, `spectra_ui.py`, `budget_guard.py`, `gui.py`)

| Surface | File:Line | Current text | Notes |
|---|---|---|---|
| Initial status | gui_spectra.py:130-132 | 'Spectra tab - complete a game, then press Get Spectra on the Game tab. Progress streams here.' | pre-run next-action EXISTS (static) |
| Run button states | gui_spectra.py:172-175,222-226,246-248 | 'no xtb run yet' (disabled) → 'Cancel xtb run' → 'Run again' (+ tooltips) | per-state flip precedent for hints |
| Started line | gui_spectra.py:222-223 | 'xtb running... (async - the dialog stays responsive)' | 06-09 pinned verbatim |
| Verdict lines | gui_spectra.py:241-245 ← spectra_ui.run_status_lines (spectra_ui.py:129-146) | 'xtb finished: ok/failed/cancelled' + 'problems: …' | **PINNED tests** (tests/test_spectra_ui.py:157-182) — do NOT extend signature |
| Launch/refuse lines | gui.py:32-33,195-196,200-205,216-229,268 | _NO_SNAKE_LINE 'no completed snake to run - play a game to completion first (Get Spectra activates on win or crash)' / 'plugin state unavailable - reopen the plugin' / 'run input is corrupt: …' / counts+warnings via `budget_guard` / 'xtb not found - set the xtb path on the Setup tab (auto-detect found nothing)' / 'xtb run did not start (see log)' | warn-and-proceed vocabulary |
| vibspectrum fallback note | gui_spectra.py:339-340 | 'showing vibspectrum - no displacement vectors available (table only)' | |
| Parse failure | gui_spectra.py:346 | 'spectrum could not be read: %s' | |
| **Plot caption (imaginary COUNT only)** | gui_spectra.py:361-363 ← plot_logic.mode_caption (plot_logic.py:221-232) | '%d modes; %d below 0 (imaginary) - see the table' | **counts only — no meaning → GAP 2 (the negative-freq deliverable)** |
| Frequency table | gui_spectra.py:149-151 | headers 'mode', 'frequency (cm-1)', 'IR intensity (km/mol)'; rows via spectra_ui.table_rows with freq_label '-31.9i' ASCII convention (spectra_ui.py:66-79) | table CLICKABILITY is never stated anywhere → GAP 3 |
| Row-click lines | gui_spectra.py:435-437,441-443,454-456,477-479 | refusals ('this spectrum has no displacement vectors (vibspectrum fallback) - vectors need the g98 output'; 'the optimized structure file is unavailable - cannot draw mode vectors'; 'the optimized structure could not be loaded: %s') + 'mode %d: vectors drawn on the optimized structure (srp_xtbopt)' | owner-signed-off framing (07-10) |
| Plot panel controls | gui_plot.py:353-386 | 'y unit:' (UNIT_MODES: 'IR intensity (km/mol)' default / 'absorbance (arb.)' / 'transmittance (arb.)'), 'color:' (blue/red/black), 'x: ascending'/'x: descending', 'Invert y axis', 'Show axis labels', 'Plot size:' (medium 640x400 default/large 800x500/wide 960x500), 'Save Plot (PNG)' | 07-06 owner-approved surface |
| Save outcomes | gui_plot.py:484,501,504 | 'nothing to save - run a calculation first' / 'plot save failed: %s' / 'plot saved: %s' | |
| Log/table caps | gui_spectra.py:144,164 | log 110px / table 150px (07-10 owner directive) | layout frozen — new hint widgets risk churn |

## 2. DOCS-03 Gap List

| DOCS-03 bullet | Status today | Gap |
|---|---|---|
| **Controls covered** | PARTIAL — arrow-keys covered (gui_game.py:320-323, input.py:95); Pause/Resume/Restart/Get-Spectra are visible buttons with no textual summary | Add ONE controls/controls-recap line (paste-style: 'arrow keys steer (no 180-degree turns); Pause/Resume + Restart are buttons') — verify GAME-10 amended contract (180-only refusal) before quoting |
| **"Click the 3D viewer" focus hint** | ✅ EXISTS in three places (gui_game.py:320-323; input.py:95; gui_game.py:1313-1314) | No new text needed; audit must pin the literal so the three instances never drift; recommend single-sourcing through help_text |
| **Negative frequencies explained** | ❌ MISSING — only a count caption (plot_logic.py:231-232) + deferred seam note (.planning/STATE.md:115) | The deferred optional-P7 line is now REQUIRED DOCS-03 scope. Seam analysis in §3 |
| **Next-action hint on every screen** | ❌ PARTIAL — Spectra initial status + Get Spectra enable affordance exist; Setup has none; Game hint is static | GAP 1 (Setup: after Apply success, never says 'press Start'), GAP 2 (nothing says the table is clickable), GAP 3 (hints never change with state). FEATURES.md sufficiency principle (line 250): 'every screen shows what to do next' |

## 3. Negative-Frequencies Line (deferred STATE.md:115 seam)

**Exact constraint from STATE.md pending-todo:** "OPTIONAL Phase-7 UX: one guidance line in
run_status_lines (07-01 seam) when min(freq) < 0 — e.g. 'N small imaginary mode(s) < 20i cm⁻¹:
soft inter-stack modes, physical for molecular stacks'. Large |imag| (>~50i) would indicate a
saddle point — worth a stronger warning if ever observed."

**Ground truth about the named seam:** `spectra_ui.run_status_lines(record)` (spectra_ui.py:129-146)
takes only the frozen spectra_run record; frequencies are NOT in the record (record keys frozen by
`xtb_run.SPECTRA_RUN_KEYS`) — they live in the parsed Spectrum (`gui_spectra.py:355`,
`self._spectrum` — the 07-08 single-source parse). Its signature/literals are pinned by
tests/test_spectra_ui.py:157-182 and the never-re-scan-log contract (07-VERIFICATION.md:25).

**Recommendation — do NOT touch run_status_lines.** Add a new PURE builder in spectra_ui.py
(co-located with freq_label/table_rows, same module, same test file family):

```python
def imaginary_note(freqs):  # freqs: iterable of float
    """One ASCII guidance line when min(freq) < 0, else None ..."""
```

TDD-able in python3.6 exactly like the 07-01 matrix: `imaginary_note([]) -> None`,
`imaginary_note([100.0, 5.0]) -> None`, `imaginary_note([-6.65, 100.0]) -> '1 small imaginary
mode(s) (<20i cm-1): soft inter-stack modes, physical for molecular stacks'` (ASCII-ized per the
house rule that shipped fmt strings are ASCII — freq_label U+2212 precedent, spectra_ui.py:11-15;
table header already uses 'cm-1', gui_spectra.py:151).

**Render site:** `gui_spectra.SpectraTab._populate_spectrum` after `self._populate_table()`
(gui_spectra.py:358), appended to the log panel EXACTLY where `mode_caption` already appends
(gui_spectra.py:361-363) — the one-place flow that already handles the imaginary count.
Consumers that must stay stable: all five spectra_ui pinned builders; plot_logic.mode_caption
(counts-only, owner-approved at 07-10).

**Cutoffs (need owner sign-off):** `|freq| < 20` = benign: owner-measured against real run
tmp/srp_spectra/run_2 (−6.65/−5.05/−3.97/−1.81, all below xtb's −20 cm⁻¹ imaginary-classification
cutoff — MEDIUM confidence on the xtb convention, HIGH on the measured values, both in
STATE.md:115). `> ~50i` saddle-point warning tier: LOW confidence / never observed here — do not
ship a fabricated tier without owner approval; simplest ship = the single benign line with the
<20i clause, stronger tier deferred or explicitly approved.

## 4. README Rewrite Scope (DOCS-01)

Current README.md is 57 lines; vibe block at lines 1-4 (blockquote 1-2 + '> !! Under Development !!'
line 4). Sections: Requirements (13-23), Install (25-31), Usage **TBD** (33-35), Demo Molecules set
**TBD** (37-41), Project Structure **TBD** (43-47), License (49-51), Acknowledgements **TBD** (53-55).

### 4a. Verified-source facts per section

| Section | Fill material (verified in-repo) |
|---|---|
| Requirements | xtb ONLY — v1 pipeline invokes `xtb --ohess` (xtbenv.py:34 `XTB_OHESS`; xtb_runner.py:164-168). **xtb4stda/std2 are never used → trim from the prereq list** (UV/vis tooling, out of IR scope). Keep: tested with `xtb-6.7.1pre-windows-x86_64.zip`, "6.7.0 missing a library" (owner-verified, PROJECT.md:49; xtb-6.7.1 symlink at repo root). Keep PyMOL 2.5.0 anaconda / PyQt5 via `pymol.Qt` / numpy — matches AGENTS.md dependency rule. Keep line-23 no-external-deps policy block |
| Install | **Current text is NOT the human-verified route.** Verified route (01-06-SUMMARY.md:67, APPROVED 2026): `Plugin → Plugin Manager → Add plugin directory → select the REPO ROOT (contains serpentrum/ with __init__.py) → restart PyMOL` → single 'serpentrum' item under the Plugin menu (entry registers via `addmenuitemqt`, serpentrum/__init__.py:70-75). Release alternative (01-RESEARCH-skeleton.md:148): `zip -r serpentrum.zip serpentrum/` → Plugin Manager → Install from local file. Reload phrasing LOCKED (01-06 decision, STATE.md:63): "restart PyMOL OR re-add the plugin directory in Plugin Manager" |
| Usage | Flow: Setup tab → choose demo set/box/head/xtb/cap/speed tier → 'Apply / Show in Viewer' → 'Start' → 3-2-1 countdown → steer with 4 arrow keys (click viewer first if keys dead; auto-pause on dialog focus) → completion (win or crash) → 'Get Spectra' → xtb streams live log (cancel/Run again) → plot (unit/color/direction/size/Save PNG) → click a table row for mode vectors on the optimized structure. Values: SPEED_TIERS relaxed 3.0 / normal 6.0 (**default**) / fast 7.5 / expert 9.0 A/s (setup_logic.py:118-123; DEFAULTS['speed']=6.0, line 58); BOX_PRESETS small ±35 / medium ±55 (default) / large ±85 Å (setup_logic.py:97-101); win cap 1..20 default 10 (gui_setup.py:126; DEFAULTS 55); atom_budget 100 (DEFAULTS 56); broadening fwhm 16.0 (DEFAULTS 57); hessian cost numbers (HESSIAN_WARNING); artifacts dir `SRP_SPECTRA_DIR` override, default `<cwd>/srp_spectra` (06-12 owner amendment, commit 048d929); Cleanup removes only `srp_*` objects (INFRA-04); **NO keyboard pause — 'P = pause' in .planning/research/FEATURES.md:246 was a proposal, NEVER shipped** |
| Demo set | serpentrum/data/manifest.json: Set A = benzene (CID 241, C6H6, 12 atoms), naphthalene (CID 931, 18), anthracene (CID 8418, 24), phenanthrene (CID 995, 24), biphenyl (CID 7095, 22), all PubChem 3D SDF (public domain — DATA_SOURCES.md §1). Stacking: `stacking_pi_stack.json` — pi_stack_pd 'pi-pi stacking (parallel-displaced)', distance_a 3.383 Å + lateral_offset_a 1.231 Å ⇒ centroid-centroid 3.60 Å @ 20.0° off-normal, citations janiak2000 / COD 4003564 / COD 2100607 (+2100608), status APPROVED. Framing MUST carry 'idealized pairwise geometry' label + herringbone negative-evidence framing (DATA_SOURCES.md §2) and the [JAN2000] SCOPE CAVEAT crystalline-state framing (STATE.md:118 pending-todo — Phase 8 TODO). **Fix line 41: file lives at `serpentrum/data/DATA_SOURCES.md`, not repo root**; note its header today says 'DRAFT — NOT APPROVED' (DOCS-02 coupling) and its §1 NOTE is STALE (claims SDFs "ship in a later phase (Phase 8)" — they shipped in Phase 3, 03-05) |
| Project Structure | Verifiable skeleton: `serpentrum/` package (entry/__init__.py; GUI gui.py, gui_setup.py, gui_game.py, gui_spectra.py, gui_plot.py; BRIDGE pymol_bridge.py, input.py; pure core everything else), `serpentrum/data/` (SDFs + manifest.json + stacking JSON + DATA_SOURCES.md), `tests/`, `smoke/`, `tools/` |
| Acknowledgements | PubChem acknowledgment (public domain, 'acknowledgment requested' — DATA_SOURCES.md §1); Janiak 2000 + COD entries cited not redistributed. Couples to DOCS-02 sign-off |

### 4b. sECDpent truth check

`grep -rni "sECDpent"` across the repo (2026-09-27): **only two hits, both inside .planning/
(PROJECT.md:51 and ROADMAP.md:300 — meta-references to the claim itself).** README.md and spec.md
are clean. The "leftover name" is already absent; the Phase-8 deliverable on this bullet is an
audit assertion (absence pinned), not a fix. Report this to the planner honestly: the planning-docs
claim is stale.

### 4c. Vibe block

Requirement text: "keeps the vibe-coding warning block at the top" — the block is lines 1-4 as
one unit (warning + '!! Under Development !!'). **Owner decision candidate:** at a release-audit
phase, whether 'Under Development' stays, is amended (e.g. versioned), or drops while keeping the
warning block (see Open Questions Q2). The audit tool should pin whichever survives.

## 5. Doc-vs-Code Audit Method (DOCS-04)

Two legs, matching the repo's established dual discipline (WSL headless gates + Windows human smokes).

### Leg A — mechanical (WSL, python3.6, in-gate)

New `tools/check_docs.py` — stdlib-only, CLI+importable (the `tools/check_purity.py` dual precedent),
wrapped by `tests/test_docs_audit.py` so it runs inside `tests/run_gates.py` gate 3 (unittest
discover). Precedents for importing production constants from an audit test: tests/test_demo_data.py
(cross-verifies manifest vs parsed reality — the direct template), tests/test_purity_gates.py
(tree-walking pattern).

Checks (each = one assertion block; doc corpus = README.md + any help literals pinned in help_text.py):
1. **Vibe block:** README lines 1-4 byte-identical to the approved block text.
2. **No placeholders:** zero 'TBD' tokens in README; zero 'sECDpent' in README/spec/user docs.
3. **Control-name literals** quoted in docs exist in code: buttons 'Apply / Show in Viewer',
   'Cleanup', 'Start', 'Pause', 'Resume', 'Restart', 'Get Spectra', 'no xtb run yet',
   'Cancel xtb run', 'Run again', 'Save Plot (PNG)', 'Browse'; group titles (§1a table);
   tab names 'Setup'/'Game'/'Spectra'; wizard prompt literal.
4. **Numeric claims vs sources of truth** (import, not grep, where possible): SPEED_TIERS
   (3.0/6.0/7.5/9.0) + DEFAULTS['speed']=6.0; BOX_PRESETS half-widths (35/55/85) + default 'medium';
   win-cap default 10/range 1..20 (gui_setup.py:126); atom_budget 100; fwhm 16.0; stacking values
   3.383/1.231 (+ composed 3.60/20.0) from `serpentrum/data/stacking_pi_stack.json` via
   `molecule_data.load_stacking`; demo molecule CIDs + atom counts from `manifest.json` via
   `setloader`; hessian numbers 84-101 s / ~5 min / 104 atoms / 4-core-8-thread from
   `setup_logic.HESSIAN_WARNING` (the drift-pin pattern: budget_guard already reuses it verbatim,
   budget_guard.py:42-47).
5. **Install recipe:** README contains the 01-06-verified phrases ('Add plugin directory',
   'restart PyMOL'); NEGATIVE assertion: the false 'Install New Plugin → point at the package
   directory' phrasing is absent.
6. **Path refs:** every back-ticked path in README exists on disk (catches the
   `DATA_SOURCES.md` vs `serpentrum/data/DATA_SOURCES.md` bug class, and future renames).
7. **Claim-ban list:** docs never mention un-shipped features ('P = pause', xtb4stda/std2 as
   prerequisites, animation, 'Generate and export').

### Leg B — human reproduce-steps (Windows PyMOL 2.5.0)

A UAT checklist md (the smoke/manual_plot_check.py + 06-12/07-10 checkpoint convention), walking:
install from scratch (Add plugin directory → restart) → Setup Apply → Start → countdown → steer →
capture → deliberate crash AND win → Get Spectra → launch → streaming log → cancel → Run again →
table row click → vectors on optimized structure → Save PNG → README steps compared line-by-line
(with checkboxes). Artifact: signed checklist recorded in the plan's SUMMARY (the 01-06/06-12/07-10
precedent of verbatim owner verdicts).

### Traceability precedent

06/07 phases recorded per-plan truths in `NN-VERIFICATION.md` tables (e.g.
.planning/phases/07-spectra-ui/07-VERIFICATION.md rows per plan) updated from state; REQUIREMENTS.md's
Traceability table (REQUIREMENTS.md:121-172) is the phase-level ledger — DOCS-04 rows land there
(DOCS-01/03/04 → Phase 8 → Complete) after both legs pass; the audit tool output is the
machine-checkable leg cited in the verdict.

## 6. Help-Text Architecture (Q5 answer)

**Recommendation: ONE new PURE module `serpentrum/help_text.py`.**

- **Purity:** new modules under `serpentrum/` auto-classify PURE (tools/check_purity.py:26-27,56-57,
  95-103) — zero registration edits; GUI modules import it via relative import (purity-exempt,
  the `from . import hud_logic` precedent in gui_setup.py:41 and `spectra_ui` in gui_spectra.py:74-75).
- **Testability:** all strings py3.6-TDD-able in WSL (the hud_logic._REASON_TEXT map →
  tests/test_hud_content.py pattern; budget_guard verdict builders → tests/test_budget_guard.py).
- **Drift control:** single source for literals that exist in multiple widgets today (the focus
  hint triplicated in §1b), and for literals that the audit tool will pin (leg A check 3/4). House
  precedent: HESSIAN_WARNING single-sourced in setup_logic and reused verbatim by budget_guard.
- **Do NOT move one-off widget labels** (group titles, row labels, button names): they are widget
  construction with no test value; leave as inline GUI literals and let the audit leg A pin them.
- Lived rule honored: GUI text changes only in GUI_MODULES files — wiring (setText calls) lands in
  gui_setup/gui_game/gui_spectra; strings land in the PURE module.
- Naming/routing: `help_text.SETUP_HINTS`, `help_text.game_hint(state)`, `help_text.spectra_hint(state)`,
  `help_text.imaginary_note(freqs)` (the last co-locatable inside spectra_ui instead near freq_label —
  planner's choice; either way it is PURE and TDD'd).

**Rejected alternative (inline literals only):** no drift control, no WSL test coverage, and the
audit tool would have to scrape GUI modules for strings — grep-brittle vs import-pin.

## 7. Next-Action Hint Design (Q6 answer)

One hint line per tab, state-driven, reusing EXISTING update seams — no new state machine:

| Screen | States (existing vocab to branch on) | Hint content (all verifiable claims) | Render seam (existing) |
|---|---|---|---|
| Setup | idle/with-materialized-scene | before Apply: 'choose settings, press Apply / Show in Viewer to preview'; after Apply: '… press Start to play' | append clause into status parts join (gui_setup.py:623-649) — the absorbed-C2-clause precedent (636-638) |
| Game | session['status']: 'countdown'/'playing'/'paused'/'over' (gui_game.py:405,642,1280,1352) | idle: 'Click Start on the Setup tab…' (current literal); playing: steer+focus text; paused: 'paused - Resume to continue'; over: 'press Get Spectra to compute the IR spectrum' | `hint_label.setText(...)`, called from `_set_idle_state`, `_begin_play`, `_apply_pause_state`, `_present_completion` — the four sites that already flip state |
| Spectra | record status 'running'/DONE/FAILED/CANCELLED (xtb_run) | pre-run: current initial literal; running: current started literal; done: 'click a table row to draw that vibration on the optimized structure; Save Plot (PNG) writes a file'; failed/cancelled: verdict + Run-again vocab (exists) | `set_status_line` — already called at on_runner_started (222-223), on_run_finished (241-245), and could append the table-click hint after `_populate_table` (gui_spectra.py:358) |

**Layout safety (07-10 approval frozen):** NO new pinned layout indices on Spectra (the
[0]-[4] order is FINAL); prefer writing into the existing status label or a next-line log append;
on Game, reuse the existing hint_label; on Setup, reuse the status join or a 5.2-05-style
always-visible sub-line ONLY if the status join proves too crowded (smallest visual diff wins —
dialog-height owner directive is fresh).

## 8. Common Pitfalls (prevention for the planner)

1. **Fabrication-by-doc:** every number in README/help must come from a code/importable source
   (data JSON, setup_logic, HESSIAN_WARNING) — quote the *encoding* values (3.383/1.231) plus the
   composed display (3.60/20.0) exactly as hud_logic.pickup_block composes them; never '3.4 A'
   (UNVERIFIED per DATA_SOURCES.md §3).
2. **Stale-claim trap:** planning docs asserted README contains 'sECDpent' — it does not. Audit
   must verify, not assume. Same class: DATA_SOURCES.md §1 NOTE's stale 'ship in a later phase'
   line; PROJECT.md:51's claim text itself.
3. **Unverified-install trap:** the current README recipe does not match the 01-06 human-verified
   route; shipping it un-audited repeats the 01-06 step-6 confusion class. Pin the verified wording.
4. **Controls drift:** 'P = pause' (FEATURES.md:246) was a proposal, never shipped; hessian
   numbers accepted live by owner are 84-101 s / ~5 min single-threaded — pre-calibration text
   ('30-90 s', in 02 research) must never be quoted.
5. **Signature-churn trap:** run_status_lines/freq_label/table_rows signatures+literals are pinned
   by tests — extend via new builders, never by editing pinned ones (07-01 plan contract).
6. **ASCII drift:** suggest U+2212/Å/°/⁻¹ text will fight the shipped ASCII house convention
   (freq_label header notes; hessian warning; 'cm-1' table header) — ship 'A', 'deg', 'cm-1', '-31.9i'.
7. **Triplication drift:** the focus-hint exists in 3 places — adding a 4th instance inline is how
   divergence happens; single-source in help_text.
8. **Layout churn:** Spectra pinned layout [0]-[4] + owner height caps (07-10) — a new hint WIDGET
   is a layout change; text-into-existing-label is not.
9. **Approval-gate coupling:** DATA_SOURCES.md is DRAFT-NOT-APPROVED; README's demo/acknowledgement
   depth couples to the DOCS-02 sign-off (another Phase-8 plan). Sequencing: land DOCS-02 approval
   (or at minimum the [JAN2000] crystalline-framing TODO from STATE.md:118) BEFORE DOCS-01's demo
   section copy-edit freezes wording.
10. **Date convention:** planning-doc stamps are UTC (git commits authoritative) — dev shell is HKT
    (STATE.md:134); do not stamp from local time.

## 9. Open Questions (owner-decision candidates)

1. **Deferred Selector-Error cosmetic fix (07-10 (d)):** noise lines when `zoom_mode_frame` fires
   before arrows exist; owner approved phase WITH it visible; candidate fix recorded in 07-10 (a):
   "zoom only on srp_xtbopt when srp_mode_vec absent" — one-function change in
   `pymol_bridge.zoom_mode_frame` (bridge module) + smoke 13 re-run. **Recommend: present to owner
   as an OPTIONAL scope item for the DOCS/audit phase; default stays DEFERRED** (it is cosmetic and
   touches an owner-approved flow).
2. **'!! Under Development !!' line (README line 4):** keep/amend/drop at release while preserving
   the vibe-warning block. Requirement text protects the warning block; the sub-line is ambiguous.
3. **Negative-freq wording + cutoffs:** the <20i benign clause (owner-flagged 2026-09-26, declined
   at the 07-10 checkpoint but now REQUIRED by DOCS-03) and the >~50i saddle tier (LOW confidence,
   unobserved) need owner sign-off before the wording pins.
4. **DOCS-02 sequencing:** approve/sign DATA_SOURCES.md before DOCS-01's demo section freezes copy
   (DRAFT header today; §1 stale SDF note; [JAN2000] scope-caveat crystalline-framing TODO — all
   writable now but the *approval* is a human act).
5. **`hud_logic.idle_tip` dead builder:** built + pinned (05-09, tests/test_hud_content.py:289-305),
   but no GUI caller exists (grep confirms zero call sites in gui_game.py). STACK-04 mentions 'idle
   chemistry tips'. Options: (a) wire it in (touch owner-approved Game tab — needs sign-off),
   (b) record the requirement note as v1-accepted-shipped-without (breakdown + per-pickup content
   already cover educational density), (c) docs-only mention. **Flag for owner.**
6. **Audit-tool shape:** recommend `tools/check_docs.py` (CLI+import) + thin
   `tests/test_docs_audit.py` wrapper so it runs in `tests/run_gates.py` gate 3 — mirrors
   check_purity/run gates exactly; alternative (a standalone gate 5 in run_gates.py) is heavier.
7. **Hint render surface on Spectra:** status-label clause vs a permanent word-wrapped sub-line
   (5.2-05 pattern) — sub-line is clearer but adds a widget under the fresh layout freeze; planner
   should pick status-clause-first.

## Sources

**Repo (HIGH confidence — read directly, 2026-09-27):**
- README.md (full 57 lines); spec.md; AGENTS.md; opencode/config
- `serpentrum/`: gui_setup.py, gui_game.py, gui_spectra.py, gui_plot.py, gui.py, hud_logic.py,
  spectra_ui.py, plot_logic.py, setup_logic.py, budget_guard.py, input.py, xtb_run.py,
  xtb_runner.py (argv via xtbenv), pymol_bridge.py:537-566, __init__.py, data/manifest.json,
  data/stacking_pi_stack.json, data/DATA_SOURCES.md
- `tools/check_purity.py` (module classification + dual CLI/import); `tests/run_gates.py` (gates);
  tests/test_spectra_ui.py:157-182, tests/test_hud_content.py:289-305
- `.planning/`: STATE.md (lines 115, 118 pending-todos; 98 07-10(d)), PROJECT.md:49-53,
  REQUIREMENTS.md (DOCS-01/03/04, traceability, GAME-04), ROADMAP.md:292-302,
  research/FEATURES.md:238-250, phases/01-*/01-06-SUMMARY.md:67,95 + 01-RESEARCH-skeleton.md:142-148,
  phases/07-*/07-10-SUMMARY.md, phases/07-*/07-01-PLAN.md/SUMMARY.md (pin contracts)

**External sources: none fetched** — every needed fact is in-repo verified (install route
human-approved at 01-06; dataset values owner-approved at DATA-02; hessian numbers from
06-CALIBRATION.md; the xtb −20 cm⁻¹ imaginary classification measured by owner on a real run per
STATE.md:115 — MEDIUM (owner-verified, not independently re-verified this session)).

## Metadata

**Confidence breakdown:**
- Text-surface inventory: HIGH — every entry cites file+line in shipped code
- Gap analysis: HIGH — greps confirm absence/presence
- README fill material: HIGH (all repo-verified); install-route correction HIGH (01-06 APPROVED)
- Negative-freq cutoffs/wording: MEDIUM (owner-measured, needs owner re-signoff to pin)
- Audit design: HIGH (three in-repo precedents: check_purity, run_gates, test_demo_data)

**Research date:** 2026-09-27
**Valid until:** 2026-10-27 (planning-stable: ships with the codebase; no fast-moving external deps)

## RESEARCH COMPLETE
