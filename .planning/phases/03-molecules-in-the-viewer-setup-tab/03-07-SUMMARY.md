---
phase: 03-molecules-in-the-viewer-setup-tab
plan: 07
subsystem: ui
tags: [pymol, qt, setup-tab, gui, pymol-bridge, anchor-persistence]

# Dependency graph
requires:
  - phase: 03-01
    provides: "purity checker BRIDGE class + gui_setup GUI allowlist entry"
  - phase: 03-04
    provides: "setloader (load_demo_set / load_upload) — pure record building"
  - phase: 03-06
    provides: "pymol_bridge (materialize / cleanup_srp) — the cmd-seam"
provides:
  - "SetupTab(QWidget) form: 5 QGroupBox sections + status label + temporary Apply/Cleanup buttons"
  - "collect_state / apply_state round-trip with _loading guard"
  - "Apply path: validate -> setloader routing -> head-combo repopulation -> pymol_bridge.materialize"
  - "gui.py page-0 registration (SetupTab as Setup tab; Game/Spectra placeholders remain)"
  - "Anchored setup dict on pmg_tk.startup._serpentrum.setup (survives close/reopen + reload)"
affects: [03-08, Phase 4, Phase 8]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "collect_state/apply_state round-trip with _loading guard (bioCHEMeleon pattern)"
    - "Anchor-backed setup dict write-back (pmg_tk.startup._serpentrum.setup)"
    - "Static QMessageBox.warning for blocking errors (no blocking-call token in source)"
    - "Inline QLabel for hessian advisory; persistent status label for validate() verdicts"
    - "Bridge-only cmd access from GUI (gui_setup -> pymol_bridge, never direct cmd)"

key-files:
  created:
    - serpentrum/gui_setup.py
  modified:
    - serpentrum/gui.py
    - serpentrum/__init__.py

key-decisions:
  - "Demo combo __upload__ sentinel is UI routing truth only; setup dict demo_set always holds a KNOWN_SETS value"
  - "apply_state calls _on_cap_changed after _loading=False (minor order swap vs plan text — necessary because _on_cap_changed guards with _loading)"
  - "xtb detect_binary result is advisory in Phase 3 (shown in status label); blocking is Phase 6"
  - "Molecule set group uses QVBoxLayout (not QFormLayout) so the upload row can be shown/hidden as a unit"

patterns-established:
  - "collect_state/apply_state with _loading guard: the Setup-tab state round-trip pattern"
  - "Anchor-backed dict write-back: collect_state writes to self._anchor.setup on every field change"
  - "Bridge-only cmd access: GUI modules call pymol_bridge, never import pymol.cmd directly"
  - "Static modal pattern: QMessageBox.warning(self, title, body) for one-shot blocking errors"

# Metrics
duration: 20min
completed: 2026-09-10
---

# Phase 3 Plan 07: SetupTab Form Summary

**SetupTab QWidget with 5 grouped config sections wired to setloader + pymol_bridge, anchored setup dict surviving reload, gui.py page-0 registration**

## Performance

- **Duration:** 20 min
- **Started:** 2026-09-10T19:25:28Z
- **Completed:** 2026-09-10T19:45:00Z
- **Tasks:** 3
- **Files modified:** 3 (1 created, 2 modified)

## Accomplishments
- Created `serpentrum/gui_setup.py` (443 lines): SetupTab(QWidget) with the full researched widget inventory — demo-set dropdown (Set A + Upload...), box-preset dropdown, head-molecule dropdown (default Random), xtb auto-detect checkbox + path field + Browse, win-cap spinbox (1..20) with inline hessian warning QLabel, persistent status label, and two temporary buttons (Apply / Show in Viewer, Cleanup)
- Wired the Apply path end-to-end: validate -> setloader routing (demo vs upload via combo currentData) -> head-combo repopulation from loaded records -> pymol_bridge.materialize -> success status with xtb detect note + validate warnings
- Registered SetupTab as page 0 in gui.py (PluginDialog gains anchor_state=None kwarg); Game/Spectra placeholder loop preserved for pages 1-2; reserved Phase-8 bottom row byte-identical; find_existing untouched
- Anchored the live setup dict on `pmg_tk.startup._serpentrum.setup` (added `setup = None` to `_SerpentrumState`; initialized to `new_setup()` on first anchor creation only via lazy `from . import setup_logic` inside `_anchor` — ENTRY purity preserved)
- All gates green: syntax + safety + purity + 433 tests; all grep contracts clean (zero exec_, zero from-PyQt5/import-PyQt5, zero cmd. in gui_setup, zero banned pymol imports in gui_setup)

## Task Commits

Each task was committed atomically:

1. **Task 1: SetupTab form + Apply/Cleanup handlers** — `a899958` (feat)
2. **Task 2: gui.py page-0 registration + __init__.py anchor setup field** — `a58dc32` (feat)
3. **Task 3: contract grep sweep + gate pass** — `57f7257` (chore)

## Files Created/Modified
- `serpentrum/gui_setup.py` — SetupTab(QWidget): the full configuration form (5 sections + status + temp buttons); collect_state/apply_state with _loading guard; _on_apply routes through setloader + pymol_bridge; _on_cleanup calls cleanup_srp; ZERO cmd imports, ZERO blocking-call tokens
- `serpentrum/gui.py` — PluginDialog(anchor_state=None) constructs SetupTab as page 0; _TAB_DEFS reduced to Game/Spectra only; reserved bottom row + Phase-8 comment byte-identical; find_existing unchanged
- `serpentrum/__init__.py` — _SerpentrumState.setup field (None); _anchor() initializes state.setup = new_setup() on first creation; run_plugin_gui passes anchor_state=state; pre-existing comment cleaned of banned literal

## Decisions Made
- **Demo combo __upload__ routing:** the combo's '__upload__' userData is UI routing truth only — collect_state() maps it to the last real set (self._last_real_set, initialized 'set_a') so the setup dict's demo_set always holds a KNOWN_SETS value. _on_apply branches on currentData() to route through setloader.load_upload vs load_demo_set.
- **apply_state _on_cap_changed ordering:** the plan text says "_on_cap_changed(); self._loading False" but _on_cap_changed guards with _loading (returns early). Swapped to "self._loading = False; _on_cap_changed()" so the hessian label is correctly set after widget population. Also added _refresh_status() at the end of apply_state to initialize the status label.
- **Molecule set group layout:** used QVBoxLayout instead of QFormLayout for the Molecule set group so the upload row (Browse + path field) can be shown/hidden as a unit via setVisible on a container QWidget. Other groups use QFormLayout per the research.
- **xtb detect is advisory:** detect_binary result is appended to the success status label ('xtb: <path>' or 'xtb not found - set a manual path or add xtb to PATH'). Blocking is Phase 6.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed pre-existing __init__.py comment containing banned literal**
- **Found during:** Task 3 (contract grep sweep)
- **Issue:** __init__.py line 47 had a code comment `# MODELESS — .show() never .exec_() (INFRA-05)` containing the `exec_(` banned literal. While the AST checker is comment-proof, the 01-02 lesson says to "keep the discipline" — banned literals should not appear anywhere in the codebase.
- **Fix:** Changed to `# MODELESS - .show() only, never a blocking modal (INFRA-05)`
- **Files modified:** serpentrum/__init__.py
- **Verification:** `grep -n "exec_(" serpentrum/__init__.py` returns no matches
- **Committed in:** 57f7257 (Task 3 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Trivial comment hygiene fix. No scope creep.

## Issues Encountered
- **apply_state _on_cap_changed ordering:** the plan's stated order ("_on_cap_changed(); self._loading False") would make _on_cap_changed a no-op due to its _loading guard. Resolved by swapping the order (set _loading=False first, then call _on_cap_changed). This is a correctness fix, not a deviation — the plan's intent is clear, the ordering was imprecise.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- SETUP-02/03/04/05/06 each have their Setup-tab control live and wired to the pure layer (setloader/setup_logic/xtbenv) and the cmd-seam (pymol_bridge)
- Error surfacing per research: static QMessageBox.warning for blocking errors, inline QLabel for hessian advisory, persistent status label for validate() verdicts
- Live setup dict anchored on pmg_tk.startup._serpentrum (survives close/reopen + reload)
- Registration contract and reserved Phase-8 row untouched
- No cmd/PyQt5/exec_/thread violations; gates green; 433 tests pass
- **Hand-off to 03-08 (human-verify checklist):**
  1. Form completeness: all 5 sections visible with correct widgets
  2. Apply materialization: Demo Set A -> box + head appear in viewer (SC1, SC2)
  3. Rejection modal: upload a >3-ring molecule -> "Upload rejected" modal with per-molecule reasons (SC1, DATA-03)
  4. Hessian warning label: win cap > 10 shows inline warning; <= 10 hides it (SC4)
  5. xtb status: after Apply, status shows xtb detect result (resolved path or not-found advisory) (SC3)
  6. Cleanup count: Cleanup button removes srp_* objects, shows count in status (SC5/INFRA-04)
  7. Anchor persistence: close/reopen preserves setup dict; reload preserves it too
  8. Upload routing: "Upload..." reveals Browse + path row; demo set hides it

---
*Phase: 03-molecules-in-the-viewer-setup-tab*
*Completed: 2026-09-10*
