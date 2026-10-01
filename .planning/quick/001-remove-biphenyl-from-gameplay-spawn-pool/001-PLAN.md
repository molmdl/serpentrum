---
phase: quick-001
plan: 001
type: execute
wave: 1
depends_on: []
files_modified:
  - serpentrum/spawn.py
  - serpentrum/gui_game.py
  - serpentrum/gui_setup.py
  - serpentrum/setup_logic.py
  - tests/test_spawn.py
  - tests/test_gui_pins.py
  - .planning/quick/001-remove-biphenyl-from-gameplay-spawn-pool/PHASE8-NOTE.md
autonomous: true

must_haves:
  truths:
    - "A gameplay run never spawns a set_a biphenyl pickup (serve pool = the 4 eligible species; all four still served cyclically)"
    - "The Setup head combo never offers set_a biphenyl and Randomize can never select it"
    - "A stale saved setup with head_molecule='biphenyl' degrades to the first eligible head (benzene) in the GAMEPLAY head path"
    - "biphenyl stays in the shipped manifest/dataset and stays viewable (pymol_bridge._select_head_record + materialize untouched)"
    - "The biphenyl REFUSE_ATOM refusal fixtures stay green UNCHANGED (tests/test_placement.py TestBiphenylRefusal, tests/test_phase5_integration.py test_s4)"
    - "An UPLOADED molecule whose id happens to be 'biphenyl' keeps the DESIGNED cycle-and-skip behavior (set-aware exclusion)"
  artifacts:
    - path: "serpentrum/spawn.py"
      provides: "GAMEPLAY_EXCLUDED_MOLS constant + is_gameplay_excluded + effective_head_id + self-filtering PickupSpawner serve order"
      contains: "GAMEPLAY_EXCLUDED_MOLS"
    - path: "serpentrum/gui_setup.py"
      provides: "head combo skips gameplay-excluded records (import from pure spawn module)"
      contains: "is_gameplay_excluded"
    - path: "serpentrum/gui_game.py"
      provides: "gameplay head resolution via spawn_mod.effective_head_id (fallback upstream of the untouched bridge resolver)"
      contains: "effective_head_id"
    - path: "serpentrum/setup_logic.py"
      provides: "dated amendment comment: refuse path now TEST-only"
      contains: "quick-001"
    - path: "tests/test_spawn.py"
      provides: "exclusion + resolver pins; existing pool-size pins re-derived from the 4-record eligible pool"
      contains: "TestGameplayExclusion"
    - path: "tests/test_gui_pins.py"
      provides: "GUI wiring source-scan pins (offscreen Qt construction is banned — 01-05)"
      contains: "TestGameplayExclusionWiring"
    - path: ".planning/quick/001-remove-biphenyl-from-gameplay-spawn-pool/PHASE8-NOTE.md"
      provides: "Phase-8 follow-up note (explicitly out of scope here)"
  key_links:
    - from: "serpentrum/spawn.py PickupSpawner.__init__"
      to: "self._order (serve pool)"
      via: "is_gameplay_excluded filter BEFORE any rng draw (GAME-07 seed-stream shape preserved for the surviving pool)"
      pattern: "is_gameplay_excluded"
    - from: "serpentrum/gui_setup.py _populate_head_combo"
      to: "spawn.is_gameplay_excluded"
      via: "skip excluded records when populating the combo (single seam: display + _head_candidates/Randomize + collect_state all inherit)"
      pattern: "spawn\\.is_gameplay_excluded"
    - from: "serpentrum/gui_game.py _build_head_state"
      to: "spawn_mod.effective_head_id -> pymol_bridge._select_head_record"
      via: "fallback resolution upstream of the UNTOUCHED bridge resolver"
      pattern: "effective_head_id"
---

<objective>
Remove the shipped set_a biphenyl from REAL gameplay — the pickup spawn pool AND head selection — while keeping it in the shipped dataset/manifest for TDD + smoke fixtures and viewer display.

Purpose: probe-proven 2026-10-01 (pure-math probe, real shipped SDFs, python3.6): the shipped biphenyl conformer has rings locked at 90.00 deg (documented permanent-refuse decision), so (a) every biphenyl PICKUP always REFUSE_ATOM (min 0.688–2.145 A < 2.5 A gate — never stacks after pickup) and (b) a biphenyl HEAD makes every first capture refuse (head target min 1.715–1.944 A both headings; segment target min 1.279–1.283 A) — a run can never progress. Biphenyl as a spawn/head option is a gameplay trap, not a demonstrator.

Output: single-source exclusion constant + spawner self-filter (pure core), head-combo filter + gameplay head fallback (GUI seams), pin tests, dated amendment comments, and a Phase-8 follow-up note. Phase-8 files NOT touched (owner directive).
</objective>

<execution_context>
@~/.config/opencode/get-shit-done/workflows/execute-plan.md
@~/.config/opencode/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@serpentrum/spawn.py
@tests/test_spawn.py
@tests/test_gui_pins.py

Read-on-demand (targeted ranges only — large GUI files, keep context lean):
- serpentrum/gui_game.py lines 476-561: `_build_engine` (spawner construction ~519-521) + `_build_head_state` (~540-561, calls `pymol_bridge._select_head_record(setup, list(records_by_id.values()), [])` at ~554).
- serpentrum/gui_setup.py lines 47-58 (imports), 521-545 (`_populate_head_combo`), 561-574 (`_head_candidates`), 364-375 (apply_state head findData fallback).
- serpentrum/setup_logic.py lines 88-101 (the BOX_PRESETS comment block ending "...biphenyl's genuine atom clash stays the designed refuse demonstrator).")

Verified facts you can rely on (do NOT re-derive):
- Manifest anchored order: benzene, naphthalene, anthracene, phenanthrene, biphenyl (biphenyl LAST — 'random' head = records[0] = benzene is already safe; no change needed there).
- setloader stamps `'set': set_id` on every record (setloader.py ~line 114); uploads carry `'set': '__upload__'` (03-04).
- gui_game already imports the spawner: `from . import spawn as spawn_mod` (gui_game.py line 75).
- gui_setup already imports pure siblings (`from . import setloader`, `setup_logic`, ...) — GUI importing PURE modules is allowed by the purity gate.
- test_spawn.py has NO biphenyl references today, but its cycle/exhaust pins derive arithmetic from `self.records` (all 5) — they WILL fail when the serve pool drops to 4; Task 1 updates them (test_spawn.py is NOT in the do-not-touch list).
- Offscreen Qt construction is a DEAD END (01-05) — GUI widget behavior cannot be unit-tested headless; test_gui_pins.py source-scan pins are the established pattern for GUI seams.

HARD CONSTRAINTS (violating any of these fails the task):
- python3.6 syntax ONLY (%-formatting, no f-strings) in all shipped code/tests.
- spawn.py stays PURE (stdlib only; no new imports needed).
- Do NOT modify: serpentrum/data/* (manifest/SDFs), tests/test_demo_data.py, tests/test_placement.py (incl. TestBiphenylRefusal), tests/test_phase5_integration.py (incl. test_s4), serpentrum/pymol_bridge.py (`_select_head_record` viewer contract stays byte-identical), any .planning/phases/08-* file, ROADMAP.md, STATE.md.
- Gates before every commit (repo root, WSL): `python3.6 tests/run_gates.py`. Do NOT run --smoke (slow Windows PyMOL leg; the data path is untouched — note as post-execution optional).
- Commit style: Conventional Commits with scope (quick-001). One atomic commit per task.
</context>

<tasks>

<task type="auto">
  <name>Task 1: Spawn-pool exclusion — constant + spawner self-filter + pins (pure core)</name>
  <files>serpentrum/spawn.py, tests/test_spawn.py</files>
  <action>
CHOSEN SHAPE — filter INSIDE PickupSpawner (single choke point): every caller (gui_game today, tests, future callers) inherits the exclusion; it is testable purely in tests/test_spawn.py; the alternative (gui_game call-site filter) was rejected because it would leave test_spawn pins serving biphenyl and any future caller exposed. House style: single-source named constant with a dated owner-approval comment.

1. serpentrum/spawn.py — after EXHAUST_COOLDOWN_TICKS (~line 127, still in the pinned-policy constants block) add:

```python
# 2026-10-01 (quick-001, owner-approved): the SHIPPED set_a biphenyl is
# EXCLUDED from gameplay pools (pickup spawn serve order + head
# selection). Probe-proven root cause: the shipped conformer's two
# rings are locked at 90.00 deg (documented permanent-refuse decision),
# so EVERY biphenyl stack at dataset geometry clashes (min
# 0.688-2.145 A < the 2.5 A gate -> always REFUSE_ATOM, never stacks
# after pickup) and a biphenyl HEAD makes every first capture refuse
# (min 1.715-1.944 A as head target, 1.279-1.283 A as segment target)
# -> a run can never progress. The manifest/dataset entry is KEPT (TDD
# + smoke fixtures + viewer display; tests/test_demo_data.py contract
# unchanged). (set, id) pairs -- SET-AWARE so an UPLOADED molecule that
# happens to carry the id 'biphenyl' keeps its DESIGNED cycle-and-skip
# pedagogy (03-04: uploads never inherit set_a's stacking entry) and
# its generic-consent stacking path.
GAMEPLAY_EXCLUDED_MOLS = (('set_a', 'biphenyl'),)


def is_gameplay_excluded(record):
    """True iff the record is gameplay-excluded (GAMEPLAY_EXCLUDED_MOLS).

    Keyed on (record['set'], record['id']): the manifest loader stamps
    'set' on every record and uploads carry '__upload__' (03-04).
    Missing keys -> (None, ...) -> never matches (safe default:
    unlisted records are never excluded). PURE.
    """
    return (record.get('set'), record.get('id')) in GAMEPLAY_EXCLUDED_MOLS
```

2. PickupSpawner.__init__ (~line 236): replace `self._order = list(records)` with:

```python
# 2026-10-01 quick-001: the serve pool is the ELIGIBLE records --
# GAMEPLAY_EXCLUDED_MOLS filtering happens HERE (single choke point) so
# every caller inherits it. Filtering runs BEFORE any rng draw, so the
# seed-stream shape for the surviving pool is unchanged (GAME-07
# determinism intact). self._records stays the UNFILTERED input.
self._order = [record for record in records
               if not is_gameplay_excluded(record)]
```

(Leave `self._records = list(records)` at line 218 untouched.)

3. Docstring amendments (wording ONLY, behavior untouched):
   - Module docstring CYCLIC bullet (~lines 17-20): the cycle order is now the ELIGIBLE records (GAMEPLAY_EXCLUDED_MOLS filtered); set_a serves 4 species; the species-reuse rationale now reads the 4-mol pool + cap 10.
   - Module docstring DEMOTE bullet (~line 24): "never permanently excluded" gains "(within the pool; the ONE upstream gameplay exclusion is GAMEPLAY_EXCLUDED_MOLS, quick-001 2026-10-01)".
   - PickupSpawner class docstring `records:` param (~lines 184-186): note gameplay-excluded records are dropped from the serve order at construction.

4. tests/test_spawn.py — update the pool-size-derived pins to the 4-record eligible pool (SpawnTestBase gains the eligible list; expectations derive from it; NO test file other than test_spawn.py may be touched):
   - SpawnTestBase.setUpClass (~line 124-135): after the existing `assert len(cls.records) == 5` add
     `cls.eligible = [r for r in cls.records if not spawn.is_gameplay_excluded(r)]` and `assert len(cls.eligible) == 4`. `make_spawner` stays UNCHANGED (it still passes all 5 records — the spawner self-filters, which is exactly what the pins then prove).
   - TestCycleAndIds.test_cycle_records_in_list_order_wrapping (~369-394): `expected_ids = [r['id'] for r in self.eligible]`; comment "one full cycle of 5 + 3 wrapped" -> "of 4 + 4 wrapped".
   - TestDemoteAfterRefuse.test_single_refuse_is_not_permanent_exclusion (~447-464): comment "pool of 5" -> "pool of 4"; `range(len(self.records))` -> `range(len(self.eligible))`.
   - TestDemoteAfterRefuse.test_full_streak_pauses_then_auto_resumes (~466-500): `ids = [r['id'] for r in self.eligible]`.
   - TestDemoteAfterRefuse.test_placed_resolution_resets_consecutive_counter (~518): `range(len(self.records) - 1)` -> `range(len(self.eligible) - 1)`.
   - TestDemoteAfterRefuse.test_unknown_molecule_id_is_ignored (~529): `pool_size == len(self.eligible)`.
   - TestExhaustCooldown._paused_spawner (~559) and test_repause_requires_fresh_pool_size_streak (~626): `range(len(self.records) - 1)` -> `range(len(self.eligible) - 1)`.
   - tests/test_spawn.py module docstring: add the new pin group (12. Exclusion) to the numbered list.
   (records[0] = benzene = eligible[0] — tests referencing self.records[0] as the serve front stay correct unchanged.)

5. tests/test_spawn.py — new pin class `TestGameplayExclusion(SpawnTestBase)`:
   - test_excluded_constant_pins_set_a_biphenyl: `spawn.GAMEPLAY_EXCLUDED_MOLS == (('set_a', 'biphenyl'),)`.
   - test_predicate_is_set_aware: `spawn.is_gameplay_excluded` True for the real demo biphenyl record (find it in self.records); False for the real benzene record; False for a synthetic upload record `{'id': 'biphenyl', 'set': '__upload__'}`; False for a record missing 'set' (`{'id': 'biphenyl'}`).
   - test_spawner_never_serves_biphenyl_across_seeds: for seed in (1, 42, 2026, 1234): build via self.make_spawner(seed), drive 8 legal spawns mirroring TestDeterminism._drive's live-list pattern (first() then next_after with the growing live list), collect served ids; assert 'biphenyl' NEVER served and ALL four eligible ids appear across the sweep.
   - test_upload_biphenyl_still_served: minimal synthetic records `[{'id': 'mol_a', 'set': 'set_a'}, {'id': 'biphenyl', 'set': '__upload__'}]` with matching atoms_by_id (use _dummy_atoms('C') for both); spawner serves BOTH within len(records) spawns (designed upload cycle-and-skip preserved — the skip itself lives in the controller, not here).
  </action>
  <verify>python3.6 -m unittest tests.test_spawn -v — all green (updated pins + 4 new); then python3.6 tests/run_gates.py from repo root — full default battery green (840 baseline + 4 new ≈ 844).</verify>
  <done>PickupSpawner built with the full 5-record demo set has pool_size 4 and never serves 'biphenyl' across seeds; set-aware predicate proven; upload-id collisions unaffected; spawn.py still PURE (no new imports); docstrings amended.</done>
  Commit: `feat(quick-001): exclude set_a biphenyl from the pickup spawn pool`
</task>

<task type="auto">
  <name>Task 2: Head-selection exclusion — pure resolver + combo filter + gameplay fallback + pins</name>
  <files>serpentrum/spawn.py, serpentrum/gui_game.py, serpentrum/gui_setup.py, tests/test_spawn.py, tests/test_gui_pins.py</files>
  <action>
1. serpentrum/spawn.py — add the PURE head-resolution pre-pass (next to the exclusion constant; gui_game already imports spawn as spawn_mod — no import change needed there):

```python
def effective_head_id(setup, records):
    """Gameplay head-resolution pre-pass (quick-001, 2026-10-01).

    Returns the head id the GAMEPLAY head path should resolve:
      - 'random' (or a missing key) -> 'random' unchanged;
      - a named id with NO gameplay-excluded record among ``records``
        -> unchanged (INCLUDING ids absent from records entirely --
        the bridge resolver keeps its advisory + box-only degradation);
      - a named id matching a gameplay-excluded record (a stale saved
        setup naming set_a biphenyl) -> the id of the FIRST record
        (anchored order) that is not excluded; when no eligible record
        exists the original id is returned (box-only scene).

    The VIEWER materialize path (pymol_bridge._select_head_record) is
    deliberately NOT routed through this -- biphenyl stays loadable and
    viewable from the manifest. PURE.
    """
    head_id = setup.get('head_molecule', 'random')
    excluded_ids = set(record['id'] for record in records
                       if is_gameplay_excluded(record))
    if head_id not in excluded_ids:
        return head_id
    for record in records:
        if not is_gameplay_excluded(record):
            return record['id']
    return head_id
```

2. serpentrum/gui_game.py `_build_head_state` (~lines 553-555): resolve the head through the pre-pass, leaving `pymol_bridge._select_head_record` itself UNTOUCHED:

```python
        # 2026-10-01 quick-001 (owner-approved): a stale saved setup
        # naming a gameplay-excluded molecule degrades to the FIRST
        # ELIGIBLE record (probe-proven: a biphenyl head makes every
        # first capture REFUSE_ATOM -> a run can never progress). The
        # VIEWER materialize path is untouched -- biphenyl stays
        # viewable from the manifest.
        records = list(records_by_id.values())
        effective = dict(setup)
        effective['head_molecule'] = spawn_mod.effective_head_id(
            setup, records)
        record = pymol_bridge._select_head_record(effective, records, [])
```

   (Replaces the current direct call at ~line 554; everything else in the method unchanged.)

3. serpentrum/gui_setup.py:
   - Add `from . import spawn` to the pure-sibling import block (alphabetical: between setloader and setup_logic, ~line 56-57).
   - `_populate_head_combo` (~line 534): skip excluded records:

```python
        for record in records:
            if spawn.is_gameplay_excluded(record):
                # 2026-10-01 quick-001: the gameplay-excluded demo
                # molecule is never OFFERED as a head (never selectable
                # -> collect_state can never emit it; _head_candidates/
                # Randomize inherit the filter for free; a stale saved
                # setup naming it degrades to Random via apply_state's
                # findData miss). The VIEWER path is untouched.
                continue
            self.head_combo.addItem(record['name'], record['id'])
```

   - `_head_candidates` docstring (~561-568): add one line — excluded demo molecules are absent from the combo, so the candidate list (and randomize_setup) inherits the exclusion.
   - Do NOT touch anything else: the Apply/materialize path (~line 872) and collect_state stay as-is (with the combo filtered they can never produce an excluded head id; a loaded stale JSON degrades to Random via the findData miss at ~line 364-375 BEFORE Start's collect_state normalizes it).

4. tests/test_spawn.py — new pin class `TestEffectiveHeadId(SpawnTestBase)`:
   - test_excluded_head_falls_back_to_first_eligible: `spawn.effective_head_id({'head_molecule': 'biphenyl'}, self.records) == 'benzene'` (anchored order: benzene first).
   - test_random_and_eligible_ids_pass_through: `'random'` -> 'random'; missing key -> 'random'; `{'head_molecule': 'naphthalene'}` -> 'naphthalene'.
   - test_missing_id_stays_unchanged: `{'head_molecule': 'no_such_mol'}` -> 'no_such_mol' (bridge advisory + box-only path preserved).
   - test_upload_biphenyl_head_not_excluded: records `[{'id': 'biphenyl', 'set': '__upload__'}]` -> returns 'biphenyl' (generic-consent upload path preserved).

5. tests/test_gui_pins.py — new class `TestGameplayExclusionWiring` (source-scan pattern, same _read + slicing style as TestEagerHeadPopulation):
   - gui_setup.py: `'from . import spawn'` present AND `'is_gameplay_excluded'` inside the `_populate_head_combo` body slice (find 'def _populate_head_combo(' .. next '\n    def ').
   - gui_game.py: `'spawn_mod.effective_head_id'` inside the `_build_head_state` body slice.
  </action>
  <verify>python3.6 -m unittest tests.test_spawn tests.test_gui_pins -v — all green (8 new); python3.6 tests/run_gates.py — full battery green. Also confirm via git diff that serpentrum/pymol_bridge.py shows NO changes.</verify>
  <done>Head combo cannot offer/select set_a biphenyl; gameplay head path degrades a stale 'biphenyl' head_molecule to benzene via the pure resolver; viewer resolver untouched; wiring pinned source-scan style.</done>
  Commit: `feat(quick-001): exclude set_a biphenyl from head selection (combo filter + gameplay fallback)`
</task>

<task type="auto">
  <name>Task 3: Amendment comments + Phase-8 note + full gate battery</name>
  <files>serpentrum/setup_logic.py, .planning/quick/001-remove-biphenyl-from-gameplay-spawn-pool/PHASE8-NOTE.md</files>
  <action>
1. serpentrum/setup_logic.py — the BOX_PRESETS comment block ends (~line 95-96) with "...and biphenyl's genuine atom clash stays the designed refuse demonstrator)." Append directly after that clause, inside the same comment block:

```
# 2026-10-01 (quick-001, owner-approved): set_a biphenyl is now EXCLUDED
#   from the gameplay spawn pool + head selection (serpentrum/spawn.py
#   GAMEPLAY_EXCLUDED_MOLS) -- the refuse path is TEST-only from here
#   on: REFUSE_ATOM stays reachable via the direct-seeded fixtures
#   (tests/test_placement.py TestBiphenylRefusal,
#   tests/test_phase5_integration.py test_s4), which BYPASS the spawn
#   pool and stay green UNCHANGED. Placement machinery
#   (placement.REFUSE_ATOM) is untouched.
```

2. Write .planning/quick/001-remove-biphenyl-from-gameplay-spawn-pool/PHASE8-NOTE.md — short, factual:

```markdown
# Phase-8 follow-up: biphenyl gameplay exclusion (quick-001, 2026-10-01)

quick-001 removed set_a biphenyl from REAL gameplay (pickup spawn pool +
head selection) via `spawn.GAMEPLAY_EXCLUDED_MOLS`. The dataset/manifest
entry is INTENTIONALLY KEPT (TDD + smoke fixtures + viewer display;
tests/test_demo_data.py contract unchanged; DATA_SOURCES sign-off flow
unaffected).

Per owner directive, NO phase-8 file was touched in quick-001. Phase 8
(08-01..08-10, Demo Data / Docs / Release Audit) MUST follow up:

- Update any 08-* docs / release-audit language that presents biphenyl
  as a playable or stackable species (demo docs, controls recap,
  requirements recap). Biphenyl remains: loadable + viewable from the
  manifest, ABSENT from the gameplay pickup pool and head combo.
- Re-scope STACK-05 "refuse demonstrator" wording if it implies
  gameplay reachability: the REFUSE_ATOM path is now TEST-only
  (direct-seeded fixtures in tests/test_placement.py +
  tests/test_phase5_integration.py). Suggest phrasing: "permanent
  refuse-path demonstrator in the test suite; excluded from live
  gameplay pools since 2026-10-01 (probe-proven always-clash geometry)".
- Optionally note in player-facing docs that the demo set offers 4
  stackable species (+ uploads).

Post-execution optional (NOT run in quick-001): the full --smoke battery
— smoke/04 exercises only the data path (manifest -> setloader ->
materialize -> head switch -> cleanup_srp), never the gameplay spawn
pool, and is unaffected by design.
```

3. Run the FULL default gate battery as the final check (no --smoke).
  </action>
  <verify>python3.6 tests/run_gates.py — green (840 baseline + ~8 new pins ≈ 848; exact total printed by the gate). git status shows NO modifications outside the plan's files_modified list (in particular: nothing under serpentrum/data/, no tests/test_placement.py / test_phase5_integration.py / test_demo_data.py changes, no .planning/phases/08-* changes, no pymol_bridge.py changes).</verify>
  <done>Refuse-demonstrator language carries a dated TEST-only amendment; the Phase-8 follow-up note exists in the quick dir; full default gate battery green; forbidden-file list provably untouched.</done>
  Commit: `docs(quick-001): refuse-demonstrator amendment comment + Phase-8 follow-up note`
</task>

</tasks>

<verification>
1. `python3.6 tests/run_gates.py` from repo root — green (840 baseline + ~8 new pins).
2. Refusal fixtures UNCHANGED and green: `python3.6 -m unittest tests.test_placement tests.test_phase5_integration tests.test_demo_data -v` (these files must show NO diff in `git status`).
3. Behavioral spot-proof (headless, pure): `python3.6 -c` one-liner or the new pins themselves — spawner over the 5 demo records: pool_size == 4, 8 seeded spawns never return 'biphenyl'; `spawn.effective_head_id({'head_molecule': 'biphenyl'}, records) == 'benzene'`.
4. Viewer contract intact: `git diff serpentrum/pymol_bridge.py` is empty; tests/test_demo_data.py green unchanged (biphenyl still in the manifest).
5. Scope guard: `git status` lists ONLY the plan's files_modified.
</verification>

<success_criteria>
- All three task commits landed with scope (quick-001); every commit preceded by a green `python3.6 tests/run_gates.py`.
- GAMEPLAY_EXCLUDED_MOLS + is_gameplay_excluded + effective_head_id live in PURE spawn.py with dated owner-approved comments; PickupSpawner self-filters its serve order before any rng draw (GAME-07 determinism preserved for the surviving pool).
- Head combo never offers set_a biphenyl; Randomize inherits the filter; stale saved setups with head_molecule='biphenyl' degrade to benzene in the gameplay head path only.
- biphenyl remains in the shipped dataset/manifest and remains viewable (bridge viewer path untouched); upload id-collisions keep the designed cycle-and-skip behavior.
- PHASE8-NOTE.md written; zero phase-8 files touched.
</success_criteria>

<output>
After completion, create `.planning/quick/001-remove-biphenyl-from-gameplay-spawn-pool/001-SUMMARY.md`
</output>
