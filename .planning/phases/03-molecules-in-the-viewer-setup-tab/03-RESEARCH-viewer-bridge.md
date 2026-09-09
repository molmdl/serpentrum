# Phase 3 (Viewer / Materialization Bridge half) — Research

**Researched:** 2026-09-10
**Domain:** PyMOL `cmd` API for molecule/CGO object lifecycle, `srp_*` namespace + cleanup, `.pse` session-reload recovery, purity-gate BRIDGE class, camera framing boundary
**Confidence:** HIGH for cmd API behaviors (verified against in-repo `tmp/bioCHEMeleon/` shipped-plugin usage + repo research docs with `[SRC]` pointers); MEDIUM for the purity-class extension + cleanup-wildcard exact semantics (inference from the checker + prescribed-but-unexercised pattern — deliberate human decision + verify-at-execution); LOW for demo-file availability (human-gated, same blocker as the sibling researches).

This research covers the **viewer/materialization half** of Phase 3: the bridge that loads the box CGO + head molecule into the PyMOL viewer under the `srp_*` namespace, the cleanup semantics that survive a fresh process after `.pse` reload (INFRA-04 / SC5), the camera framing boundary vs Phase 4's locked camera, and the `pymol_bridge.py` + `check_purity.py` BRIDGE-class extension. It **builds on and does not contradict** the two sibling researches:
- `03-RESEARCH-setup-ui.md` (Setup-tab UI half — states the handoff contract §6.3; recommends the BRIDGE class §5.2)
- `03-RESEARCH-upload-gate.md` (DATA/loader half — `molfile.py` gate, manifest schema, demo-file checkpoint)

**Repo-only constraint honored:** every claim below is verified from in-repo sources only. `tmp/pymol-src/` does NOT exist in this repo (confirmed: `ls tmp/pymol-src` → absent), so PyMOL-source API claims cite the `[SRC]` pointers already verified in `.planning/research/{STACK,ARCHITECTURE,PITFALLS}.md` PLUS the concrete `cmd.*` usage verified in the shipped `tmp/bioCHEMeleon/biochemeleon/` plugin (which IS in-repo). Unverifiable exact-semantics claims are marked `[ASSUMPTION]`/`[TRAIN]` with a verify-at-execution mitigation.

---

## Summary

The viewer bridge is a thin `cmd`-seam module (`serpentrum/pymol_bridge.py`) that turns pure data (a CGO float list from `cgo_build.box_cgo`, a setup dict from `setup_logic`, molecule file paths from the loader) into PyMOL viewer objects named `srp_box` (CGO) and `srp_head` (molecule), frames them once with `cmd.zoom('srp_*')`, and cleans them up with `cmd.delete('srp_*')`. The single load-bearing architectural fact is that **serpentrum's purity checker currently has NO class that permits `from pymol import cmd`** — the GUI class allows only `pymol.Qt`, ENTRY allows only lazy pymol in bodies, everything else is PURE (bans pymol anywhere). Phase 3 is the first phase that calls `cmd.*`, so it MUST extend `tools/check_purity.py` with a new `BRIDGE_MODULES` allowlist (parallel to `GUI_MODULES`) and create `pymol_bridge.py` as the single cmd-seam the documented architecture reserves (`ARCHITECTURE.md` §2: "pymol_bridge.py — The ONLY module (besides controller/input) importing pymol.cmd"). This validates and refines the sibling UI research's §5.2 recommendation for the viewer side.

The cleanup/session-reload answer (INFRA-04 / SC5) is settled and clean: **`.pse` saves viewer objects (the `srp_box` CGO and `srp_head` molecule survive) but NOT plugin Python state** (`[SRC: PITFALLS.md Pitfall 8.3]`). Therefore `cleanup_srp()` must be a **pure function of object names** — it calls `cmd.delete('srp_*')` with zero dependency on a live controller/game state, so it works identically from the dialog's Cleanup button AND in a fresh process after `.pse` reload where no plugin state exists. This is the key code-shape implication of the purity rules + Pitfall 8.3: the bridge function takes no game-state arguments; it operates solely on the `srp_*` name pattern. serpentrum does NOT need bioCHEMeleon's `backup.py` snapshot/restore machinery (`[SRC: tmp/bioCHEMeleon/biochemeleon/backup.py]`) because — per `ARCHITECTURE.md` Pattern 4 — the game NEVER mutates user molecules; all game artifacts are synthetic `srp_*` objects, so cleanup-by-prefix is safe and complete with no restore step.

**Primary recommendation:** Extend `check_purity.py` with `BRIDGE_MODULES = {'serpentrum/pymol_bridge.py'}` (allows pymol/pmg_tk any level, bans PyQt5/numpy any level, keeps the `.exec_()` ban) + add `serpentrum/gui_setup.py` to `GUI_MODULES`; create `pymol_bridge.py` with the viewer surface `load_molecule(path, srp_name)` / `load_box(preset)` / `place_head(srp_name, preset)` / `cleanup_srp()` / `frame_scene()` / `materialize(setup, candidates)`; load molecules directly into `srp_*` names via `cmd.load(path, object='srp_*', zoom=0)` (load-time naming — no `set_name`/`create` copy needed for the head); build the box via `cgo_build.box_cgo(...)` → `cmd.load_cgo(floats, 'srp_box', zoom=0)`; frame once with `cmd.zoom('srp_*')` + `cmd.refresh()` (NOT a locked camera — that is Phase 4's GAME-02); cleanup via `cmd.delete('srp_*')` (idempotent, name-pattern, fresh-process-safe); reserve the `srp_` prefix and warn if a user object already holds it. Demo SDFs are a human-checkpoint dependency (matching the upload-gate research §6.3); the bridge is smoke-testable with a hand-written fixture SDF.

---

## 1. Verified PyMOL `cmd` Behaviors (each with an in-repo source pointer)

### 1.1 `cmd.load(path, object=name, zoom=0|1)` — load-time object naming (HIGH confidence)

The shipped bioCHEMeleon plugin loads files with the `object=` kwarg controlling the resulting PyMOL object name and `zoom=` controlling auto-zoom:
- `cmd.load(win_path, object=obj_name, zoom=1)` — `demos.py:194`
- `cmd.load(win_path, object=obj_name, zoom=1, format='pdb')` — `demos.py:501`
- `cmd.load(to_windows_path(p), object=obj_name, zoom=1)` — `demos.py:547` (reads `.pdb.gz` natively)

`[SRC: tmp/bioCHEMeleon/biochemeleon/demos.py:194,501,547]`. Native SDF/mol2 format support is verified: `chempy/mol2.py` and `chempy/sdf.py` both ship in 2.5.0 → `.mol2`/`.sdf` load natively via `cmd.load` (`[SRC: ARCHITECTURE.md F18]`); format-support line verified at `importing.py:683` (`[SRC: STACK.md §3 table]`).

**Consequence for the `srp_*` namespace:** to land a loaded molecule in the game namespace, pass the name at load time — `cmd.load(sdf_path, object='srp_head', zoom=0)`. **No `cmd.set_name` and no `cmd.create` copy is needed for the head** (the demo SDF is game data, not a user object to preserve). `cmd.set_name` is `[TRAIN]`/`[ASSUMPTION]` (not exercised in bioCHEMeleon; not needed if load-time naming is used). `zoom=0` suppresses PyMOL's auto-zoom-on-load so the bridge controls framing explicitly (§5).

### 1.2 `cmd.load_cgo(float_list, name, zoom=0)` — CGO object creation (HIGH confidence)

`cmd.load_cgo` creates a compiled-graphics-object from a flat float list:
- Verified signature: `cmd.load_cgo(obj, name, zoom=0)` — `[SRC: ARCHITECTURE.md F15 citing pymol/wizard/box.py:380 (loaded via cmd.load_cgo(obj, name, zoom=0)) + importing.py:300 (load_cgo verified)]`
- The pure builder `cgo_build.box_cgo(min_corner, max_corner, color, linewidth)` already returns the correct float list (`[SRC: serpentrum/cgo_build.py:75-131]` — `[LINEWIDTH, w, BEGIN, LINES, COLOR, r,g,b] + 12 edges + [END, STOP]`, 106 floats; constants copied from verified `pymol/cgo.py:21-65` per `cgo_build.py:52-72`).
- In-tree prior art for box CGO: `pymol/wizard/box.py:261-311` (TRIANGLE_STRIP faces) loaded via `cmd.load_cgo(obj, name, zoom=0)` (`box.py:380`) — `[SRC: ARCHITECTURE.md F15; STACK.md §3 table]`.

**Bridge call:** `cmd.load_cgo(cgo_build.box_cgo(min_c, max_c, color, linewidth), 'srp_box', zoom=0)`. The bridge imports `cgo_build` (PURE) via a relative import (always purity-exempt, `check_purity.py:75-78`) and `cmd` via `from pymol import cmd` (BRIDGE class — §3). `[SRC: serpentrum/cgo_build.py:75-131; ARCHITECTURE.md F15]`

### 1.3 CGO + molecule objects survive `.pse` save/reload (HIGH confidence)

`.pse` session files save **all viewer objects** — including CGO objects and loaded molecules — but **no plugin Python state**:
- "saving a session keeps all viewer objects (the game's box CGO, snake, pickups, vector CGO) but no plugin Python state" — `[SRC: PITFALLS.md Pitfall 8.3, line 203]`
- "Only viewer objects survive; Cleanup-by-name-prefix is the recovery path (Pitfall 8.3)" — `[SRC: PITFALLS.md Integration Gotchas table, line 338]`
- bioCHEMeleon v1-verified: ".pse doesn't save plugin Python state" — `[SRC: PITFALLS.md Pitfall 8.3 citing bioCHEMeleon v1→VMD carry-over matrix row 6]`

**Consequence:** `srp_box` (CGO) and `srp_head` (molecule) both survive a `.pse` save→reopen. After reload in a FRESH process, the objects are on screen but no controller/game state exists. Cleanup must therefore be name-based, not state-based (§4).

### 1.4 `cmd.delete(name)` is idempotent; prefix-wildcard cleanup is prescribed (HIGH for idempotency; MEDIUM for wildcard semantics)

`cmd.delete` is safe on absent objects (idempotent):
- `cmd.delete(BACKUP_PREFIX)  # commanding.py:496 (idempotent)` — `[SRC: tmp/bioCHEMeleon/biochemeleon/backup.py:42]`
- `cmd.delete(backup_name)  # commanding.py:496 (safe on absent objects)` — `[SRC: backup.py:49]`
- Also `backup.py:60`, `mutation.py:561,691,693,824,826,828`, `wizard.py:83` — all use `cmd.delete(name)` and rely on idempotency.

Prefix-wildcard cleanup (`cmd.delete('srp_*')`) is **prescribed** by the architecture but **not directly exercised** in bioCHEMeleon (which used `segi GAME` selectors because its hiders lived inside the user's object — a different model):
- "Cleanup = `cmd.delete` everything matching the prefix" — `[SRC: ARCHITECTURE.md Pattern 4, line 217]`
- "give the Cleanup model button the ability to delete `name serp_*` + restore user objects from the pre-game backup" — `[SRC: PITFALLS.md Pitfall 8.3, line 207]` (note: PITFALLS says `serp_*`; the authoritative prefix is `srp_*` — see §4.1)
- serpentrum's design AVOIDS the backup step: "serpentrum never mutates user molecules. All game artifacts are copies created via `cmd.create` into a `srp_`-prefixed namespace... Cleanup = `cmd.delete` everything matching the prefix. Originals stay pristine, so PyMOL's missing undo (F17) is a non-issue for v1 — the bioCHEMeleon backup/restore machinery is not needed at first." — `[SRC: ARCHITECTURE.md Pattern 4, lines 215-219]`

**Wildcard semantics:** PyMOL's `delete` command performs name-pattern matching (`*` glob on object names) — standard behavior. But the exact match semantics (does `srp_*` match `srp_box` and `srp_head` but not `user_mol`?) are `[ASSUMPTION]` (not directly exercised in-repo). **Mitigation (verify-at-execution):** the Phase-3 smoke MUST assert that after loading `srp_box` + `srp_head` + a non-srp sentinel object, `cmd.delete('srp_*')` leaves exactly the sentinel and removes exactly the two srp objects. `[SRC: ARCHITECTURE.md Pattern 4; PITFALLS.md 8.3; backup.py:42,49 (idempotency)]`

### 1.5 `cmd.get_names('public_objects', enabled_only=True)` — enumerate objects (HIGH confidence)

The object-enumeration API (for the collision guard §4.3 and the cleanup count):
- `cmd.get_names('public_objects', enabled_only=True)` — `[SRC: tmp/bioCHEMeleon/biochemeleon/demos.py:87,94; __init__.py:837; backup.py:11]`
- bioCHEMeleon uses it to list loaded molecule objects (`demos.py:87-94`) and to snapshot names before a `cmd.load` (`__init__.py:837`).
- Underscore-prefixed objects are hidden from `'public_objects'` (`backup.py:11` comment: "underscore => private, hidden from cmd.get_names('public_objects')"). `srp_` is NOT underscore-prefixed, so srp objects ARE visible to `get_names('public_objects')`.

**For the collision guard (§4.3):** enumerate `cmd.get_names('all_objects')` (or `'public_objects'`) and check for any `srp_*` name that the plugin did not create this session. **For the cleanup count:** `len([n for n in cmd.get_names('all_objects') if n.startswith('srp_')])` before delete gives the deleted count for the status label. `[SRC: demos.py:87,94; backup.py:11; __init__.py:837]`

### 1.6 `cmd.create(target, source)` — fresh independent copy (HIGH confidence; NOT needed for Phase-3 head)

`cmd.create` makes a fresh independent copy (creating.py:960):
- `cmd.create(BACKUP_PREFIX, target_obj)  # creating.py:960 (fresh independent copy)` — `[SRC: backup.py:43]`
- `cmd.create(target_obj, backup_name)  # creating.py:960 — fresh copy from backup` — `[SRC: backup.py:61]`
- Also `mutation.py:634,688,690,825,827` with `zoom=0` and state args.

**Phase-3 relevance:** `cmd.create` is the Pattern-4 mechanism for copying a user molecule into the `srp_*` namespace without mutating the original. BUT for the Phase-3 **head** (a demo-set molecule loaded from a shipped SDF), there is no "user original" to preserve — `cmd.load(path, object='srp_head', zoom=0)` creates the game object directly. `cmd.create` becomes relevant in **Phase 5** when pickups are loaded from user uploads and must be copied (not mutated) into `srp_pickup_*` names. **Recommendation: Phase 3 uses load-time naming for the head; defer `cmd.create` to Phase 5 pickups.** This keeps the Phase-3 bridge surface minimal. `[SRC: ARCHITECTURE.md Pattern 4; backup.py:43,61]`

### 1.7 `cmd.translate([dx,dy,dz], 'objname')` — position the head (HIGH confidence)

`cmd.translate` moves an object by a delta vector:
- "positioned by `cmd.translate([dx,dy,dz], 'objname')`" — `[SRC: STACK.md §3 table (pickups row), citing editing.py:1610]`
- "`translate` (editing.py:1610)" — `[SRC: ARCHITECTURE.md F14]`

**Head placement:** the box presets are symmetric about the origin (`setup_logic.BOX_PRESETS`: small `((-12,-12),(12,12))`, medium `((-18,-18),(18,18))`, large `((-25,-25),(25,25))` — `[SRC: serpentrum/setup_logic.py:63-67]`), so box center = `(0, 0, 0)`. A PubChem 3D SDF has its own coordinate origin (not necessarily the molecular centroid). To center the head at the box origin, compute the loaded molecule's centroid and translate by its negative. The centroid is available via `cmd.get_extent('srp_head')` (returns `(min_x,min_y,min_z, max_x,max_y,min_z,...)`; centroid = midpoint of min/max — `[SRC: ARCHITECTURE.md F14: "get_extent (used by bioCHEMeleon __init__.py:387)"]`). **Phase-3 minimum:** `cmd.zoom('srp_*')` frames box+head regardless of head position, so exact centering is a polish step, not a must. `[SRC: setup_logic.py:63-67; STACK.md §3; ARCHITECTURE.md F14]`

### 1.8 `cmd.zoom(selection, ...)` + `cmd.refresh()` — one-shot framing (HIGH confidence)

- `cmd.zoom(selection, buffer, ...)` — `[SRC: ARCHITECTURE.md F16 citing viewing.py:65]`
- `cmd.refresh()` triggers a scene redraw — `[SRC: STACK.md F9 / ARCHITECTURE.md F9: "cmd.refresh() before delayed UI so a redraw lands first"; tmp/bioCHEMeleon/biochemeleon/gui_game.py:303,356 (cmd.refresh() in practice)]`

**Phase-3 framing:** after loading `srp_box` + `srp_head`, call `cmd.zoom('srp_*')` (frame all game objects) then `cmd.refresh()` (force the redraw to land). This is a ONE-SHOT frame so the user sees the materialized scene (SC2: "see a clearly visible boundary box"). It is **NOT** a locked camera — see §5 for the Phase-3/Phase-4 boundary. `[SRC: ARCHITECTURE.md F16; STACK.md F9; gui_game.py:303]`

### 1.9 The Qt main thread IS the PyMOL gui thread — direct `cmd.*` from handlers (HIGH confidence)

Button-click handlers run on the Qt main thread, which is the same thread PyMOL's `cmd` API is safe on. bioCHEMeleon calls `cmd.*` directly inside Qt handlers:
- `cmd.load(pse_path, partial=1)` inside `_on_load` — `[SRC: tmp/bioCHEMeleon/biochemeleon/__init__.py:839]`
- `cmd.count_atoms(obj)` inside `gui_setup.py:_randomize` — `[SRC: gui_setup.py:631]`
- `cmd.load(win_path, object=obj_name, zoom=1)` in finalize — `[SRC: demos.py:194]`

No worker/queue/`QTimer.singleShot` drain is needed for Phase 3's sub-second operations (load a few small SDFs, one box CGO, one head, delete `srp_*`). The drain pattern is reserved for long work (Phase 6 xtb). **The hard rule (Pitfall 6): never `cmd.*` from a `threading.Thread`/`QThread`** — Phase 3 spawns no threads, so trivially satisfied. `[SRC: PITFALLS.md Pitfall 6; ARCHITECTURE.md Pattern 2 + F10; 03-RESEARCH-setup-ui.md §3]`

### 1.10 Runtime paths are Windows paths — the bridge NEVER converts them (HIGH confidence)

The plugin runs inside Windows PyMOL; `QFileDialog` returns Windows paths (`C:\Users\...`); `cmd.load` understands them natively. The `tools/winpath.py` helper is DEV-SIDE ONLY. So the upload path from `QFileDialog` and the demo SDF path from the manifest flow **unchanged** to `cmd.load`. `[SRC: 03-RESEARCH-setup-ui.md §1.6; STATE.md decision 01-05; STACK.md "What NOT to Use" WSL-paths row]`

---

## 2. The `srp_*` Namespace — Prefix, Reservation, Collision Guard

### 2.1 Authoritative prefix: `srp_` (NOT `serp_`)

There is a **discrepancy in the research docs**:
- **STACK.md §3 table** (lines 48-52) uses `serp_boundary`, `serp_snake`, `serp_vectors` — **stale shorthand**.
- **ARCHITECTURE.md Pattern 4** (line 217) uses `srp_head`, `srp_pickup_03`, `srp_box_cgo` — **the canonical pattern**.
- **INFRA-04** (the binding requirement, `REQUIREMENTS.md:67`): "All game-generated objects live in an `srp_*` namespace" — **authoritative**.
- **PITFALLS.md Pitfall 8.3** (line 207) says `serp_*` but references "STACK.md Pattern 4 namespace" — it inherited STACK's stale prefix.
- **Both Phase-3 sibling researches** (2026-09-10) use `srp_*` consistently (`03-RESEARCH-setup-ui.md` §6.3; `03-RESEARCH-upload-gate.md` §8.2).

**Decision: use `srp_`** (per INFRA-04 + ARCHITECTURE.md Pattern 4 + the two most-recent sibling researches). STACK.md §3's `serp_` is stale; flag it for a doc update when ARCHITECTURE.md is next touched (no code impact — Phase 3 code uses `srp_` from the start). `[SRC: REQUIREMENTS.md:67 (INFRA-04); ARCHITECTURE.md Pattern 4; 03-RESEARCH-setup-ui.md §6.3]`

### 2.2 Phase-3 `srp_*` object inventory

| Object name | Type | Created by | Survives `.pse`? |
|---|---|---|---|
| `srp_box` | CGO (LINES, 12 edges) | `cmd.load_cgo(cgo_build.box_cgo(...), 'srp_box', zoom=0)` | YES (Pitfall 8.3) |
| `srp_head` | molecule (loaded SDF) | `cmd.load(sdf_path, object='srp_head', zoom=0)` | YES (Pitfall 8.3) |
| (Phase 5+) `srp_pickup_NN` | molecule copies | `cmd.create` into srp_ namespace | YES |
| (Phase 5+) `srp_snake` | CGO (spheres+cylinders) | `cmd.load_cgo` rebuilt per tick | YES |

Phase 3 creates only `srp_box` + `srp_head`. The cleanup wildcard `srp_*` covers all future srp objects too (forward-compatible). `[SRC: ARCHITECTURE.md Pattern 4; PITFALLS.md 8.3]`

### 2.3 Prefix reservation + collision guard (PROPOSAL — human confirm)

**The risk:** if a USER has loaded an object named `srp_something` (e.g. their own molecule), `cmd.delete('srp_*')` would delete it too — and in a fresh process after `.pse` reload, the plugin CANNOT distinguish game-created `srp_*` from user-created `srp_*` (no plugin state survives; only object names survive).

**Reservation policy (recommended):** the `srp_` prefix is RESERVED for game-generated objects. Document this in the Setup-tab status label and in AGENTS.md/DOCS. This mirrors how bioCHEMeleon reserved `segi='GAME'` + `b=-999` sentinels (`[SRC: tmp/bioCHEMeleon/AGENTS.md "Hider sentinel" + "cleanup_hiders uses segi GAME ALONE"]`) — but serpentrum's reservation is by NAME PREFIX, not by atom-level sentinels (cleaner, because srp objects are whole objects, not atoms hidden inside a user object).

**Guard at materialize-time (live plugin state exists):** before `materialize()` creates srp objects, enumerate `cmd.get_names('all_objects')` and filter for `srp_*`. If any srp object already exists (leftover from a previous game OR a user object with the reserved prefix):
- Default behavior: **delete them first** (cleanup_srp is the first step of materialize — this is the documented Apply path: "cleanup `srp_*` first, then load box + head", `[SRC: 03-RESEARCH-setup-ui.md §6.3]`). This handles the common case (leftover game objects from a previous Apply).
- Edge case: if the user genuinely has their own `srp_*` object, it gets deleted. This is the documented trade-off of prefix reservation — **warn in the status label**: "Objects with the `srp_` prefix will be treated as game-generated and removed on Cleanup; rename user objects to avoid the `srp_` prefix."

**Guard at cleanup-time (fresh process, no plugin state):** `cleanup_srp()` cannot distinguish game vs user srp objects. It deletes ALL `srp_*`. This is the INFRA-04 contract ("removes only game-generated `srp_*` objects" — the "only" is satisfied BY CONSTRUCTION because the prefix is reserved: any `srp_*` object IS game-generated by policy). The fresh-process Cleanup button calls the same `cmd.delete('srp_*')`. `[SRC: ARCHITECTURE.md Pattern 4; PITFALLS.md 8.3; REQUIREMENTS.md INFRA-04]`

**Human-decision item:** confirm the `srp_` prefix reservation + the "delete-all-srp on Cleanup" policy (vs. a more conservative enumerate-and-warn-before-delete that requires a second click). The conservative variant is friendlier but adds a modal step; the delete-all variant matches SC5's "Cleanup model removes only `srp_*`" one-click contract. See §8.

---

## 3. `pymol_bridge.py` Function Inventory + `check_purity.py` Extension Spec

### 3.1 Validating the sibling research's BRIDGE-class recommendation (MEDIUM confidence — human decision)

The sibling UI research (§5.2) recommends adding a `BRIDGE_MODULES` class to `check_purity.py`. **This research validates that recommendation for the viewer side and specifies the exact extension.** The current checker has three classes (`tools/check_purity.py:66-72`):
- **ENTRY** (`serpentrum/__init__.py`): pymol/pmg_tk allowed ONLY lazily in function bodies; module-level pymol = violation (`check_purity.py:113-119`).
- **GUI** (`GUI_MODULES = {'serpentrum/gui.py'}`, `:55`): ONLY `pymol.Qt`/`pymol.Qt.*` import forms; any other pymol/pmg_tk anywhere = violation (`:124-131`).
- **PURE** (default): pymol/pmg_tk/PyQt5/numpy banned anywhere (`:135-138`).

**There is NO class that permits `from pymol import cmd`.** Phase 3 is the first phase that calls `cmd.*` (load, load_cgo, delete, zoom, refresh). The documented architecture reserves `pymol_bridge.py` as "The ONLY module (besides controller/input) importing pymol.cmd" (`[SRC: ARCHITECTURE.md §2 component table]`). `[SRC: tools/check_purity.py:55,60,66-138; ARCHITECTURE.md §2]`

### 3.2 `check_purity.py` extension — exact spec

Add a fourth class, parallel to GUI:

```python
# tools/check_purity.py additions

# Explicit cmd-bridge allowlist — the ONLY modules (besides ENTRY-lazy) that
# may import pymol.cmd. Allows pymol/pmg_tk at module level AND in bodies;
# bans PyQt5/numpy everywhere (Qt stays in GUI modules; numpy never needed
# in the bridge — pure modules do the math).  .exec_() stays banned (the
# bridge builds no dialogs).
BRIDGE_MODULES = {'serpentrum/pymol_bridge.py'}
```

**`classify()` extension** (`check_purity.py:66-72`):
```python
def classify(rel_path):
    if rel_path == ENTRY_MODULE:
        return 'ENTRY'
    if rel_path in GUI_MODULES:
        return 'GUI'
    if rel_path in BRIDGE_MODULES:     # NEW
        return 'BRIDGE'                 # NEW
    return 'PURE'
```

**`_check_import_node()` extension** (`check_purity.py:106-138`) — add a BRIDGE branch mirroring GUI but allowing pymol/pmg_tk roots (not just pymol.Qt):
```python
elif cls == 'BRIDGE':
    # Allow pymol/pmg_tk at ANY level (module + bodies) — this is the
    # cmd-seam. PyQt5/numpy banned anywhere (same as GUI/PURE for those).
    for root in sorted(roots & {'PyQt5', 'numpy'}):
        _flag(out, rel_path, node.lineno,
              'bridge module imports %r (banned anywhere)' % root)
    # pymol/pmg_tk allowed — no flag.
```

The `.exec_()` ban (`check_purity.py:162-169`) stays unchanged — it applies to EVERY class including BRIDGE (the bridge builds no dialogs; `.show()`/modal handling lives in GUI modules). `[SRC: tools/check_purity.py:55,60,66-72,106-138,162-169]`

**Also add `serpentrum/gui_setup.py` to `GUI_MODULES`** (sibling research §5.3): `GUI_MODULES = {'serpentrum/gui.py', 'serpentrum/gui_setup.py'}`. `gui_setup.py` imports `pymol.Qt` (allowed, GUI class) + pure modules + `pymol_bridge` via relative imports (exempt); it calls `pymol_bridge.*` — **never `cmd.*` directly** (GUI class bans it). `[SRC: 03-RESEARCH-setup-ui.md §5.3; check_purity.py:55,75-78]`

### 3.3 `tests/test_purity_gates.py` extension — new fixture cases

The purity self-test (`tests/test_purity_gates.py`) uses fixture trees. Add cases mirroring the existing GUI cases (`:116-153`):
- **BRIDGE clean:** `serpentrum/pymol_bridge.py` with module-level `from pymol import cmd` → 0 violations.
- **BRIDGE clean (body):** `serpentrum/pymol_bridge.py` with `from pymol import cmd` inside a function → 0 violations (BRIDGE allows any level).
- **BRIDGE PyQt5 banned:** `serpentrum/pymol_bridge.py` with `from PyQt5 import QtWidgets` → 1 violation mentioning PyQt5.
- **BRIDGE numpy banned:** `serpentrum/pymol_bridge.py` with `import numpy` inside a function → 1 violation mentioning numpy.
- **BRIDGE `.exec_()` banned:** `serpentrum/pymol_bridge.py` with `dialog.exec_()` → 1 violation mentioning exec_.
- **GUI_MODULES extended:** `serpentrum/gui_setup.py` with `from pymol.Qt import QtWidgets` → 0 violations (mirrors case 5 `:116-125`).
- **GUI gui_setup bare pymol banned:** `serpentrum/gui_setup.py` with `from pymol import cmd` → 1 violation (mirrors case 6 `:128-153`).
- **`test_real_repo_clean` (case 10, `:211-212`):** stays as-is — `check_tree` walks only existing `.py` files, so listing `pymol_bridge.py` in `BRIDGE_MODULES` before it exists does not break the test (the path is never visited). Once `pymol_bridge.py` is created, it must be clean or this test fails. `[SRC: tests/test_purity_gates.py:30-212; check_purity.py:173-194 (check_tree walks existing files only)]`

### 3.4 `pymol_bridge.py` viewer-surface function inventory

The bridge is the single cmd-seam. For Phase 3's viewer half, the surface is (refining sibling research §5.2/§6.3 — the loader functions `load_demo_set`/`load_upload` are the upload-gate research's `molfile.py` + `molecule_data` callers; this list is the VIEWER surface that consumes their output):

```python
# serpentrum/pymol_bridge.py  (BRIDGE class — from pymol import cmd allowed;
#   imports pure modules cgo_build/setup_logic/molecule_data via relative imports)

# --- object lifecycle ---
def load_molecule(path, srp_name, zoom=0):
    """cmd.load(path, object=srp_name, zoom=zoom) -> srp_name (or raises).
    Load-time naming lands the object directly in the srp_* namespace.
    No set_name / create copy needed for the head (demo SDF = game data)."""

def load_box(preset, color=(1.0, 0.4, 0.1), linewidth=2.0, display_z=5.0):
    """Build the boundary-box CGO from setup_logic.BOX_PRESETS[preset] via
    cgo_build.box_cgo(min_corner, max_corner, color, linewidth), then
    cmd.load_cgo(floats, 'srp_box', zoom=0). display_z is the shallow
    z-depth for 2D-plane perception (STACK.md §3 2D variant: 'rectangle +
    shallow depth'). Returns 'srp_box'."""

def place_head(srp_name, preset):
    """Position the head molecule at box center (0,0,0). Computes the
    loaded molecule's centroid via cmd.get_extent(srp_name) and translates
    by its negative via cmd.translate([-cx,-cy,-cz], srp_name). Box presets
    are symmetric about origin (setup_logic.BOX_PRESETS), so center=(0,0,0)."""

def cleanup_srp():
    """cmd.delete('srp_*') — idempotent, name-pattern, fresh-process-safe.
    Pure function of object names: NO dependency on a live controller / game
    state / pmg_tk.startup._serpentrum. Returns the count of deleted objects
    (enumerated via cmd.get_names('all_objects') filtered to srp_ prefix,
    BEFORE the delete). Works in a fresh process after .pse reload (INFRA-04/SC5)."""

def frame_scene():
    """One-shot framing: cmd.zoom('srp_*') + cmd.refresh(). NOT a locked
    camera (Phase 4 owns GAME-02 locked camera). Called once after
    materialize so the user sees the box+head (SC2)."""

# --- orchestration ---
def materialize(setup, candidates):
    """The Apply path (03-RESEARCH-setup-ui.md §6.3). cleanup_srp() first
    (removes leftover srp_*), then load_box(setup['box_preset']), then load
    + place the head (first candidate if setup['head_molecule']=='random';
    the named candidate otherwise), then frame_scene(). Returns a list of
    error strings (empty on success). candidates = molecule records from
    the loader half (molfile/molecule_data); each carries 'file' (path)
    and 'id'. If candidates is empty (no demo data yet / upload not done),
    load box only and return an advisory 'no head molecule loaded' note."""
```

**What does NOT live in the bridge (purity separation):**
- The SDF/mol2 parsing + ring/H/charge gate → `molfile.py` (PURE, upload-gate research §8.2). The bridge CALLS `molfile.read_sdf`/`gate_set` then `cmd.load` on accepted files.
- The manifest/stacking-data loading → `molecule_data.py` (PURE). The bridge calls `molecule_data.load_manifest`/`load_stacking` to resolve candidate paths.
- CGO float-list construction → `cgo_build.py` (PURE). The bridge calls `cgo_build.box_cgo` then `cmd.load_cgo`.
- Setup defaults/validation → `setup_logic.py` (PURE). The bridge reads `BOX_PRESETS[setup['box_preset']]`.
- Dialog/widgets → `gui_setup.py` (GUI class). It calls `pymol_bridge.*` on button click; never `cmd.*` directly.

**Dependency direction (enforced by the purity gate):** `pure (cgo_build, setup_logic, molecule_data, molfile) ← pymol_bridge (cmd) ← gui_setup (pymol.Qt)`. The bridge imports pure modules (relative, exempt) + `pymol.cmd` (BRIDGE allowance). Pure modules never import the bridge (would violate PURE). `[SRC: ARCHITECTURE.md §2 component table + structure rationale; check_purity.py:75-78 (relative imports exempt); 03-RESEARCH-upload-gate.md §8.2; 03-RESEARCH-setup-ui.md §5.2]`

---

## 4. Cleanup + Session-Reload Design (INFRA-04 / SC5)

### 4.1 The `.pse` desync problem and the name-based recovery path

**PITFALLS.md Pitfall 8.3** (the verified base): saving a `.pse` keeps all viewer objects (`srp_box`, `srp_head`) but no plugin Python state. After File→Open Session in a fresh process: the srp objects litter the scene, no controller exists, and the user expects to clean them up. `[SRC: PITFALLS.md Pitfall 8.3, lines 199-208]`

**The recovery path (prescribed):** "Name every game-created object with one prefix and give the Cleanup model button the ability to delete [the prefix] + restore user objects from the pre-game backup. This makes post-session-reload scenes recoverable with one click — even in a fresh PyMOL process where the plugin state never existed." `[SRC: PITFALLS.md Pitfall 8.3, line 207; ARCHITECTURE.md Pattern 4]`

**serpentrum simplification (no backup needed):** bioCHEMeleon needed snapshot/restore (`backup.py`) because it MUTATED user objects (inserted hiders inside the user's molecule). serpentrum's Pattern 4 design NEVER mutates user molecules — all game artifacts are synthetic `srp_*` objects. So cleanup = `cmd.delete('srp_*')` with NO restore step. "Originals stay pristine, so PyMOL's missing undo (F17) is a non-issue for v1 — the bioCHEMeleon backup/restore machinery is not needed at first." `[SRC: ARCHITECTURE.md Pattern 4, lines 215-219; PITFALLS.md F17]`

### 4.2 The fresh-process-safe code shape (the key purity-rule implication)

**SC5 / INFRA-04 requires:** "Cleanup model ... still works in a fresh process after a session save/reload."

**What "fresh process" means:** after `.pse` reload, the user opens the plugin dialog. The dialog reconstructs via the anchor pattern (`__init__.py:37-45`: `state.dialog` is None after a fresh-process load → constructs a new `PluginDialog`). There is NO live game controller, NO engine state, NO record of which srp objects were created. `[SRC: serpentrum/__init__.py:37-45; PITFALLS.md Pitfall 7]`

**Therefore `cleanup_srp()` MUST be a pure function of object names:**
- It takes NO game-state arguments (no controller, no engine, no setup dict).
- It does NOT read `pmg_tk.startup._serpentrum` (the anchor may hold a dialog but no game state in a fresh process).
- It operates SOLELY on the `srp_*` name pattern: enumerate `cmd.get_names('all_objects')`, count those starting with `srp_`, then `cmd.delete('srp_*')`, return the count.
- It is callable from BOTH the Setup-tab Cleanup button (live game) AND the fresh-process Cleanup button (post-reload) — identical code path.

```python
# serpentrum/pymol_bridge.py
from pymol import cmd

SRP_PREFIX = 'srp_'

def cleanup_srp():
    """Delete all srp_* objects. Fresh-process-safe (INFRA-04/SC5).
    Pure function of object names — no controller/game-state dependency.
    Returns the count of objects deleted (for the status label)."""
    before = [n for n in cmd.get_names('all_objects')
              if n.startswith(SRP_PREFIX)]
    cmd.delete('srp_*')   # idempotent; name-pattern glob (verify-at-execution)
    return len(before)
```

**Why this shape satisfies the purity rules:** `pymol_bridge.py` is BRIDGE class (allows `from pymol import cmd`). The function has no Qt, no numpy, no game-engine imports — just `cmd`. It is the single cmd-seam. The GUI's Cleanup button calls `pymol_bridge.cleanup_srp()` and displays the returned count. `[SRC: ARCHITECTURE.md Pattern 4; PITFALLS.md 8.3; REQUIREMENTS.md INFRA-04; tools/check_purity.py BRIDGE spec §3.2]`

### 4.3 The two cleanup invocation paths (both call the same function)

| Path | Trigger | Plugin state? | What happens |
|---|---|---|---|
| **Live Cleanup button** (Setup tab, Phase 3 temporary) | User clicks Cleanup | Yes (dialog + maybe game) | `pymol_bridge.cleanup_srp()` → `cmd.delete('srp_*')` → count shown in status label |
| **Fresh-process Cleanup** (post-`.pse`-reload) | User reopens plugin, clicks Cleanup | No game state (fresh process) | SAME `pymol_bridge.cleanup_srp()` → `cmd.delete('srp_*')` → works because it's name-based |

Both paths call the identical function. SC5's "still works in a fresh process after a session save/reload" is satisfied BY CONSTRUCTION. `[SRC: PITFALLS.md 8.3; 03-RESEARCH-setup-ui.md §7 (temporary Cleanup button); REQUIREMENTS.md INFRA-04]`

### 4.4 Verify-at-execution: the session-reload smoke

The Phase-3 smoke MUST prove SC5 headlessly (the `01_skeleton_smoke.py` template, `[SRC: smoke/01_skeleton_smoke.py]`):
1. `cmd.load_cgo(box_cgo(...), 'srp_box')` + `cmd.load(fixture_sdf, object='srp_head')` → assert both objects exist (`cmd.get_names`).
2. `cmd.save('tmp_session.pse')` → `cmd.delete('srp_*')` → `cmd.load('tmp_session.pse')` (reload; simulates fresh-process object presence).
3. Assert `srp_box` + `srp_head` are present after reload (CGO + molecule survive `.pse` — Pitfall 8.3).
4. `pymol_bridge.cleanup_srp()` → assert both are gone, non-srp sentinel survives, returned count == 2.
5. Flush `SMOKE-OK VIEWER-BRIDGE` sentinel (verdict = flushed sentinel, never exit code per `run_gates.py:140`).

This smoke is the verify-at-execution step for: (a) `cmd.delete('srp_*')` wildcard semantics (§1.4), (b) CGO+ molecule `.pse` survival (§1.3), (c) fresh-process cleanup (§4.2). `[SRC: smoke/01_skeleton_smoke.py (template); run_gates.py:128-141 (smoke verdict = SMOKE-OK sentinel); PITFALLS.md 8.3]`

---

## 5. Camera Guidance — Phase 3 vs Phase 4 Boundary

### 5.1 What Phase 3 MUST do (SC2)

SC2 (`ROADMAP.md:90`): "User can pick a preset box size and see a clearly visible boundary box, and the selected head molecule (default: Random) appears in the viewer." This requires the box+head to be VISIBLE after Apply — which requires framing. `[SRC: ROADMAP.md:90 (SC2)]`

**Phase-3 camera action (one-shot frame):** after `materialize()` loads `srp_box` + `srp_head`, call `cmd.zoom('srp_*')` (frame all game objects with a buffer) then `cmd.refresh()` (force redraw). This is a single framing operation — the user sees the box and head. No view-locking, no ortho mode, no view-matrix save/restore. `[SRC: ARCHITECTURE.md F16 (cmd.zoom); STACK.md F9 (cmd.refresh); ROADMAP.md SC2]`

### 5.2 What Phase 3 MUST NOT do (Phase 4's territory)

Phase 4 owns the **locked camera** (GAME-02: "Gameplay runs on a 2D plane inside the 3D viewer with a locked camera"; SC3: "Play happens on a 2D plane with a locked camera, and the boundary box stays clearly visible throughout"). `[SRC: ROADMAP.md:102,106 (Phase 4 GAME-02/SC3)]`

**Phase 3 must NOT install:**
- `cmd.set('ortho', ...)` (ortho view for 2D play) — Phase 4.
- `cmd.set_view(...)` / view-matrix save+restore — Phase 4 (STACK.md §3 2D variant: "Fixed camera: play field in the xy-plane; lock/ignore view rotation during play; optionally restore view each game start with a saved `cmd.get_view()` matrix").
- A wizard or event-filter that locks rotation — Phase 4.
- Per-tick `cmd.zoom` re-framing — Phase 4/5 (the snake moves; the camera follows or locks).

**The boundary:** Phase 3 = `cmd.zoom('srp_*')` once (one-shot frame so the user sees the configured scene). Phase 4 = locked camera (view matrix save/restore, ortho, view-lock during play). Phase 3 does not pre-install Phase-4 machinery; Phase 4 will add it. This keeps the phases cleanly separable and avoids over-reaching. `[SRC: ROADMAP.md Phase 3 vs Phase 4; STACK.md §3 2D variant; ARCHITECTURE.md F16]`

### 5.3 Box z-depth — a bridge constant (not in setup_logic)

`setup_logic.BOX_PRESETS` gives xy-extents only; z-depth is "display-only and is the bridge's concern" (`setup_logic.py:61-62`). The 2D-plane game variant uses "a rectangle (+ shallow depth for perception)" (`STACK.md §3 2D variant`). **Recommendation:** the bridge defines a `BOX_DISPLAY_Z` constant (e.g. `5.0` Å) and builds the box CGO with `min_corner=(x0, y0, -BOX_DISPLAY_Z)`, `max_corner=(x1, y1, +BOX_DISPLAY_Z)`. This gives the box visual depth in the 3D viewer while the game plays on z=0. The constant lives in `pymol_bridge.py` (or `cgo_build.py` as a default) — NOT in `setup_logic.py` (which owns only the game-logic xy-extents). `[SRC: setup_logic.py:60-67; STACK.md §3 2D variant]`

---

## 6. Head Molecule Materialization

### 6.1 Loading + naming the head

The head is a demo-set molecule (or, in the upload path, the first accepted upload molecule). Load it directly into the `srp_head` name:
```python
cmd.load(head_sdf_path, object='srp_head', zoom=0)
```
Load-time naming (§1.1) — no `set_name`, no `create` copy (the demo SDF is game data, not a user object to preserve). `[SRC: demos.py:194 (cmd.load object= pattern); ARCHITECTURE.md Pattern 4]`

### 6.2 Where the head starts

Box center = `(0, 0, 0)` (all `BOX_PRESETS` are symmetric about the origin, `setup_logic.py:63-67`). The head should start at the box center so `cmd.zoom('srp_*')` frames it centered. A PubChem 3D SDF has its own origin (not necessarily the centroid), so `place_head` translates the loaded molecule's centroid to the origin:
```python
ext = cmd.get_extent('srp_head')   # [min_x,min_y,min_z, max_x,max_y,max_z, ...]
cx = (ext[0] + ext[3]) / 2.0
cy = (ext[1] + ext[4]) / 2.0
cz = (ext[2] + ext[5]) / 2.0
cmd.translate([-cx, -cy, -cz], 'srp_head')
```
`[SRC: ARCHITECTURE.md F14 (get_extent, translate); setup_logic.py:63-67]`

**Phase-3 minimum:** exact centering is polish — `cmd.zoom('srp_*')` frames box+head regardless of head position. If the head SDF's origin is far from its centroid, the zoom will still frame both, just off-center. Recommend implementing `place_head` (it's ~5 lines) but treat exact centering as a nice-to-have verified at human-verify, not a smoke gate.

### 6.3 "Random" head in Phase 3 (LOW confidence — human-confirm, defers to sibling research §9.5)

`setup_logic.DEFAULTS['head_molecule'] = 'random'` (`setup_logic.py:51`). True randomization (`setup_logic.randomize_head(candidates, seed)`) belongs to game-start (Phase 4 — the seed + randomize call are game-start concerns, `[SRC: 03-RESEARCH-setup-ui.md §6.2]`). For Phase 3, "Random" cannot truly randomize. The sibling UI research (§9.5) recommends: **show the first candidate as a placeholder head** with a status note "head will be randomized at game start." This research concurs for the viewer side: `materialize(setup, candidates)` loads `candidates[0]` as `srp_head` when `setup['head_molecule']=='random'`, and the status label notes the placeholder. `[SRC: 03-RESEARCH-setup-ui.md §6.2, §9.5; setup_logic.py:51,253-265]`

### 6.4 Head visibility / representation

GAME-03 (Phase 4/5): "The head renders as spheres and pickups as sticks." For Phase 3's SC2 ("head molecule appears in the viewer"), any visible representation suffices. **Recommendation:** `cmd.show('spheres', 'srp_head')` (matches the eventual game rep; gives a visually distinct head). This is a one-line bridge call after load. It does NOT pre-install Phase-4/5 game rendering (which involves per-tick CGO rebuilds); it's a static show-as-spheres for the Phase-3 preview. `[SRC: REQUIREMENTS.md GAME-03; ROADMAP.md Phase 3 SC2]`

### 6.5 User molecules must never be mutated (HIGH confidence)

`STACK.md §3`: "All rendering via PyMOL objects the game owns; never mutate user molecules mid-game." `ARCHITECTURE.md Pattern 4 / Anti-Pattern 1`: "serpentrum never mutates user molecules. All game artifacts are copies created into a `srp_`-prefixed namespace." For Phase 3, the head is loaded from a demo SDF (game data) — no user molecule is involved. For uploaded molecules used as the head (if the user uploads and picks one), the bridge loads the upload SDF directly into `srp_head` (the upload file is the user's chosen input, not a pre-existing scene object). **No user SCENE object is ever mutated** — the bridge only creates/deletes `srp_*` objects. `[SRC: STACK.md §3; ARCHITECTURE.md Pattern 4 + Anti-Pattern 1]`

---

## 7. Demo-Set Data — Viewer-Bridge Dependency + Recommendation

### 7.1 The viewer bridge's dependency on the loader half

`materialize(setup, candidates)` needs `candidates` = a list of molecule records, each carrying at least `file` (an SDF path) and `id`. These come from the loader half (upload-gate research): `load_demo_set(set_id)` → `molecule_data.load_manifest` + `molfile.read_sdf` + gate → candidate records; `load_upload(path)` → `molfile.read_sdf` + gate → candidate records. `[SRC: 03-RESEARCH-upload-gate.md §4.1 (molecule record), §8.2 (bridge calls molfile); 03-RESEARCH-setup-ui.md §6.3 (handoff contract)]`

**If no demo SDFs exist** (the current state — `serpentrum/data/` has only `DATA_SOURCES.md` + `stacking_pi_stack.json`, NO manifest.json, NO SDF files, `[SRC: serpentrum/data/ directory listing; 03-RESEARCH-upload-gate.md §6.1]`), then `load_demo_set('set_a')` cannot produce candidates (the manifest's `file` references must exist on disk, `molecule_data.py:178-181`). The bridge's `materialize` handles empty candidates gracefully: load box only, return advisory "no head molecule loaded — upload a set or wait for demo data."

### 7.2 The demo-file blocker (matches upload-gate research §6)

The upload-gate research (§6) thoroughly covers the three options:
- **(a) Agent fetches 5 SDFs from PUG REST** — REJECTED by the user's no-network constraint.
- **(b) Human provides SDF files via `checkpoint:human-action`** — RECOMMENDED; the human places 5 PubChem 3D SDFs (CIDs 241/931/8418/995/7095, verified public-domain per `DATA_SOURCES.md §1`) + a draft manifest.json into `serpentrum/data/`.
- **(c) Upload-only Phase 3** — violates SC1 ("choose Demo Set A... and its molecules load").

**This research concurs with option (b)** for the viewer side and adds the viewer-specific implication: until the checkpoint is met, the bridge's demo-set materialization can only be smoke-tested with a hand-written fixture SDF (test data, not a chemistry claim — a minimal methane.sdf in `tests/fixtures/` suffices to prove `cmd.load` + `load_cgo` + `cleanup` end-to-end). SC2's "head molecule appears" can only be human-verified with real demo SDFs after the checkpoint; the upload path provides the head independently (user uploads their own SDF). `[SRC: 03-RESEARCH-upload-gate.md §6; DATA_SOURCES.md §1; AGENTS.md no-fabrication rule]`

### 7.3 What the viewer bridge needs from the human checkpoint

The `checkpoint:human-action` (owned by the loader half, upload-gate research §6.3) delivers:
1. 5 PubChem 3D SDF files in `serpentrum/data/` (benzene.sdf CID 241, etc.).
2. A `manifest.json` (the agent can create this from `DATA_SOURCES.md` metadata + computed `ring_atoms` once the SDFs are present; or the human provides it).

**The viewer bridge consumes only:** the `file` path from each manifest molecule record (via `molecule_data.load_manifest`). It does NOT parse SDFs itself (that's `molfile.py`, PURE). So the bridge is unblocked the moment the SDF files + manifest exist on disk. `[SRC: molecule_data.py:178-181 (file-existence check); 03-RESEARCH-upload-gate.md §5.1, §6.3]`

---

## 8. Open Questions Needing Human Decision

1. **Purity-checker BRIDGE class + `pymol_bridge.py`** (§3.1, §3.2). **Recommendation: YES** — extend `check_purity.py` with `BRIDGE_MODULES = {'serpentrum/pymol_bridge.py'}` (allows pymol/pmg_tk any level, bans PyQt5/numpy, keeps `.exec_()` ban) + add `serpentrum/gui_setup.py` to `GUI_MODULES`. This is the documented architecture and the only clean way to permit `cmd.*` under serpentrum's stricter gate. **Confidence: MEDIUM** (inference from the checker + documented architecture; the alternative of stuffing cmd calls into ENTRY-lazy works but violates "thin entry"). **Needs human approval** because it changes a gate tool. *(Same item as sibling research §9.1 — consolidate.)*

2. **`srp_` prefix reservation + "delete-all-srp on Cleanup" policy** (§2.3). **Recommendation:** reserve `srp_` for game objects; Cleanup = `cmd.delete('srp_*')` deletes all srp-prefixed objects unconditionally (one-click, matches SC5); warn in the status label that user objects with the `srp_` prefix will be treated as game-generated. The conservative alternative (enumerate + warn + require second click) is friendlier but breaks the one-click Cleanup contract. **Confidence: MEDIUM** (policy judgment; the prefix reservation is standard for plugin namespaces). **Needs human approval.**

3. **`cmd.delete('srp_*')` wildcard semantics — verify-at-execution** (§1.4, §4.4). The prefix-wildcard delete is PRESCRIBED by `ARCHITECTURE.md Pattern 4` + `PITFALLS.md 8.3` but not directly exercised in bioCHEMeleon (which used `segi` selectors). **Recommendation:** the Phase-3 smoke MUST assert that `cmd.delete('srp_*')` removes exactly the srp-prefixed objects and leaves non-srp objects intact. **Confidence: MEDIUM** (standard PyMOL globbing; verify in smoke). Not a human decision — a verify-at-execution step.

4. **"Random" head placeholder in Phase 3** (§6.3). **Recommendation:** load `candidates[0]` as `srp_head` with a status note "head will be randomized at game start." **Confidence: LOW** (UX judgment). **Needs human approval.** *(Same item as sibling research §9.5 — consolidate.)*

5. **One-shot `cmd.zoom('srp_*')` framing in Phase 3 vs deferring all camera work to Phase 4** (§5). **Recommendation:** Phase 3 does the one-shot zoom+refresh (SC2 requires the box to be visible); Phase 4 owns the locked camera. **Confidence: MEDIUM** (SC2 implies visibility; the boundary with Phase 4 is clear in the roadmap). **Needs human confirm** that a one-shot zoom is acceptable in Phase 3 (vs. "no camera work until Phase 4").

6. **Demo Set A data availability** (§7). **Recommendation:** `checkpoint:human-action` for the 5 PubChem SDFs + manifest.json (option (b)); viewer bridge smoke-tested with a hand-written fixture SDF. **Confidence: LOW** (human-gated). **Needs human action** (provide the SDFs) + approval (manifest creation). *(Same item as sibling researches §9.2 / §6 — consolidate.)*

7. **`BOX_DISPLAY_Z` value** (§5.3). **Recommendation:** `5.0` Å (shallow depth for 2D-plane perception). **Confidence: LOW** (cosmetic; no in-repo source pins it). **Needs human confirm** or defer to Phase-4 playtesting.

---

## 9. Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---|---|---|---|
| Box CGO float list | Hand-build LINES/VERTEX floats | `cgo_build.box_cgo(min, max, color, linewidth)` (already built + tested) | Pure module exists (`cgo_build.py:75-131`); constants verified from `pymol/cgo.py:21-65` |
| Object naming into srp_* | `cmd.load` then `cmd.set_name` | `cmd.load(path, object='srp_*', zoom=0)` (load-time naming) | `object=` kwarg sets the name at load (`demos.py:194`); set_name is `[TRAIN]` and unnecessary |
| Copying user molecule into srp_* | `cmd.load` then `cmd.create` copy | (Phase 3 head) load directly; (Phase 5 pickups) `cmd.create(srp_name, source)` | Head is game data (no original to preserve); pickups are Phase 5 (`backup.py:43` create pattern) |
| Object enumeration | Custom iteration | `cmd.get_names('all_objects')` / `('public_objects', enabled_only=True)` | Verified API (`demos.py:87,94; backup.py:11`) |
| Cleanup with backup/restore | `backup.py` snapshot/restore machinery | `cmd.delete('srp_*')` (prefix wildcard) | serpentrum never mutates user objects (Pattern 4) → no restore needed; bioCHEMeleon's backup was for a different (mutation) model |
| Camera framing | `cmd.set_view` matrix math | `cmd.zoom('srp_*')` (one-shot) | `cmd.zoom` frames a selection (`viewing.py:65`); set_view is Phase 4's locked-camera concern |
| SDF parsing / ring counting | Custom in the bridge | `molfile.py` (PURE, upload-gate research) + `molecule_data.load_manifest` | Purity separation: parse+gate in PURE module, bridge calls it |

---

## 10. Common Pitfalls (Phase-3 viewer-bridge specific)

### Pitfall V1: `cmd.delete('srp_*')` deletes a user object named `srp_*`
**What goes wrong:** a user has their own object named `srp_my_mol`; Cleanup deletes it; no undo (F17).
**Why:** the `srp_` prefix is reserved but not enforced by PyMOL; any object matching the glob is deleted.
**How to avoid:** reserve + document the prefix (§2.3); warn in the status label. In a fresh process, cannot distinguish — the reservation IS the contract.
**Warning signs:** user reports missing objects after Cleanup; objects named `srp_*` in a pre-game scene. `[SRC: ARCHITECTURE.md Pattern 4; PITFALLS.md F17 (no undo)]`

### Pitfall V2: CGO box invisible because `zoom=0` suppressed framing
**What goes wrong:** `cmd.load_cgo(..., zoom=0)` creates the box but the camera doesn't frame it; the user sees an empty viewer.
**Why:** `zoom=0` suppresses auto-zoom (correct for load — the bridge controls framing); but if `frame_scene()` (`cmd.zoom('srp_*')`) is skipped, nothing frames the box.
**How to avoid:** `materialize` ALWAYS calls `frame_scene()` after loading box+head. The `zoom=0` on load is intentional; the explicit `cmd.zoom('srp_*')` is the framing step.
**Warning signs:** Apply succeeds, objects exist in `get_names`, but viewer looks empty. `[SRC: ARCHITECTURE.md F15 (zoom=0 on load_cgo); F16 (cmd.zoom)]`

### Pitfall V3: Cleanup depends on game state (fails in fresh process)
**What goes wrong:** `cleanup_srp(controller)` reads `controller.game_objects` to know what to delete; in a fresh process after `.pse` reload, `controller` is None → AttributeError.
**Why:** coupling cleanup to live state violates INFRA-04's fresh-process requirement.
**How to avoid:** `cleanup_srp()` takes NO arguments; operates solely on `cmd.get_names` + `cmd.delete('srp_*')` (§4.2). Pure function of object names.
**Warning signs:** Cleanup works during a game but raises after session reload. `[SRC: PITFALLS.md 8.3; REQUIREMENTS.md INFRA-04]`

### Pitfall V4: Mutating a user molecule instead of loading into srp_*
**What goes wrong:** the bridge loads the head into the user's existing object (e.g. via `cmd.load` without `object=`, which defaults to the filename) or calls `cmd.create(user_obj, ...)` merging into the user object.
**Why:** violates Pattern 4 (never mutate user molecules); breaks cleanup (user object now has srp content but a non-srp name).
**How to avoid:** ALWAYS pass `object='srp_head'` (or the appropriate srp_ name) to `cmd.load`. Never `cmd.create` into a non-srp target.
**Warning signs:** user's molecule changes appearance after Apply; Cleanup leaves game geometry behind. `[SRC: ARCHITECTURE.md Pattern 4 + Anti-Pattern 1]`

### Pitfall V5: Installing the locked camera in Phase 3 (over-reaching into Phase 4)
**What goes wrong:** Phase 3 adds `cmd.set('ortho', ...)`, view-matrix save/restore, or a rotation-lock; Phase 4's locked-camera work then conflicts or duplicates.
**Why:** Phase 4 owns GAME-02 (locked camera); Phase 3 only needs SC2 (visible box).
**How to avoid:** Phase 3 does ONLY `cmd.zoom('srp_*')` + `cmd.refresh()` (one-shot frame). No ortho, no set_view, no lock.
**Warning signs:** Phase-4 camera work rewrites Phase-3 framing; viewer locked during Setup (should be interactive). `[SRC: ROADMAP.md Phase 3 SC2 vs Phase 4 GAME-02/SC3]`

---

## 11. State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|---|---|---|---|
| `serp_*` prefix (STACK.md §3, PITFALLS 8.3) | `srp_*` prefix (INFRA-04, ARCHITECTURE.md Pattern 4) | Architecture doc evolution | Use `srp_`; STACK.md §3's `serp_` is stale — flag for doc update |
| bioCHEMeleon `backup.py` snapshot/restore for cleanup | `cmd.delete('srp_*')` prefix-wildcard (no backup) | ARCHITECTURE.md Pattern 4 (serpentrum design) | serpentrum never mutates user objects → no restore needed; simpler, safer cleanup |
| Cleanup coupled to game controller | `cleanup_srp()` pure function of object names | INFRA-04 fresh-process requirement | Works in fresh process after `.pse` reload (no plugin state) |
| `cmd.load` then `cmd.set_name` | `cmd.load(path, object='srp_*', zoom=0)` load-time naming | bioCHEMeleon `demos.py:194` precedent | One call sets the name; no rename step |
| No purity class for `cmd.*` | `BRIDGE_MODULES` class (Phase 3 extension) | Phase 3 (first phase touching cmd) | Permits `from pymol import cmd` in `pymol_bridge.py` only |

---

## 12. Sources

### Primary (HIGH confidence — in-repo code/usage + research-doc [SRC] pointers)
- `tmp/bioCHEMeleon/biochemeleon/demos.py:194,501,547` — `cmd.load(path, object=name, zoom=1)` load-time naming; `:87,94` `cmd.get_names('public_objects', enabled_only=True)`
- `tmp/bioCHEMeleon/biochemeleon/backup.py:42,49,60` — `cmd.delete` idempotent (commanding.py:496); `:43,61` `cmd.create` fresh copy (creating.py:960); `:75,76` `cmd.count_atoms` (querying.py:1412); `:11` underscore-hides-from-public_objects
- `tmp/bioCHEMeleon/biochemeleon/__init__.py:837-839` — `cmd.get_names` before `cmd.load(pse_path, partial=1)` (session merge)
- `tmp/bioCHEMeleon/biochemeleon/gui_game.py:303,356` — `cmd.refresh()` (scene redraw)
- `tmp/bioCHEMeleon/biochemeleon/mutation.py:634,690` — `cmd.create(..., zoom=0)` (zoom kwarg on create)
- `tmp/bioCHEMeleon/AGENTS.md` — `cmd.delete` idempotent; `cmd.fetch` `async_=0`; `cmd.iterate` `ID` uppercase; no `cmd.get_representations()` in 2.5.0; PyMOL-source API verification path
- `serpentrum/cgo_build.py:75-131` — `box_cgo()` pure builder (106 floats, verified constants from `pymol/cgo.py:21-65`); `:52-72` local constants rationale (no `pymol.cgo` import)
- `serpentrum/setup_logic.py:48-67` — DEFAULTS, BOX_PRESETS (xy-extents, z display-only)
- `serpentrum/__init__.py:10-45` — anchor pattern, dialog singleton, lazy import
- `serpentrum/gui.py:42-69` — 3-tab shell, `self.tabs` handle, reserved bottom row
- `serpentrum/molecule_data.py:137-217,333-362` — manifest validation (file-existence check), `interaction_for`
- `tools/check_purity.py:55,60,66-72,106-138,162-169` — GUI_MODULES, BANNED_ROOTS, classify, _check_import_node, `.exec_()` ban
- `tests/test_purity_gates.py:30-212` — fixture-tree test pattern (cases 1-10)
- `tests/run_gates.py:128-141` — smoke verdict = flushed SMOKE-OK sentinel (never exit code)
- `smoke/01_skeleton_smoke.py` — smoke template (named steps + check() + flushed sentinel)
- `.planning/research/PITFALLS.md` — Pitfall 8.3 (`.pse` keeps viewer objects, no plugin state; cleanup-by-prefix recovery), Pitfall 6 (no `cmd.*` from threads), F17 (no undo), Integration Gotchas (session-saves-CGO row)
- `.planning/research/STACK.md` — §3 table (CGO entities, `cmd.load`/`cmd.translate`/`cmd.load_cgo`), F9 (`cmd.refresh()`), "What NOT to Use" (WSL paths), 2D variant (rectangle + shallow depth)
- `.planning/research/ARCHITECTURE.md` — F14 (translate/get_extent), F15 (`cmd.load_cgo(obj, name, zoom=0)` citing `box.py:380`), F16 (`cmd.zoom` citing `viewing.py:65`), F18 (SDF/mol2 native), Pattern 4 (`srp_*` namespace, cleanup-by-prefix, no backup needed), §2 component table (`pymol_bridge.py` = ONLY cmd-seam)
- `.planning/REQUIREMENTS.md:67` — INFRA-04 (`srp_*` namespace, fresh-process cleanup); `:59` DATA-03; Phase-3 traceability
- `.planning/ROADMAP.md:83-96` — Phase 3 goal + SC1-SC5; `:102,106` Phase 4 GAME-02/SC3 (locked camera)
- `.planning/STATE.md` — decisions 01-01..01-06 (anchor, purity, winpath); Phase-2 π-stack APPROVED (3.6 Å @ 20°); "Phase 3 consumes Phase 2's pure halves"

### Sibling researches (HIGH confidence — committed, build on them)
- `.planning/phases/03-molecules-in-the-viewer-setup-tab/03-RESEARCH-setup-ui.md` — §1 (Qt/cmd behaviors), §3 (thread boundary), §5 (BRIDGE class + gui_setup recommendation), §6.3 (handoff contract: materialize/cleanup_srp), §7 (Phase 3/8 control split), §9 (open questions)
- `.planning/phases/03-molecules-in-the-viewer-setup-tab/03-RESEARCH-upload-gate.md` — §4 (molecule record), §5 (manifest schema), §6 (demo-file options → option (b) human checkpoint), §7 (xtb detection wiring), §8 (molfile.py decomposition)

### [ASSUMPTION] / [TRAIN] (marked inline; verify-at-execution)
- `cmd.delete('srp_*')` wildcard match semantics — standard PyMOL globbing; verify in Phase-3 smoke (§4.4)
- `cmd.set_name` — not needed (load-time naming); `[TRAIN]` if ever used
- `BOX_DISPLAY_Z = 5.0` — cosmetic; no in-repo source; human-confirm or Phase-4 playtest

---

## RESEARCH COMPLETE

**Phase:** 3 — Molecules in the Viewer & Setup Tab (Viewer / Materialization Bridge half)
**Confidence:** HIGH (cmd API behaviors — verified against in-repo bioCHEMeleon usage + research-doc [SRC] pointers); MEDIUM (purity-class extension + cleanup-wildcard semantics — inference + prescribed-but-unexercised; verify-at-execution); LOW (demo-file availability — human-gated, same blocker as sibling researches)

### Key Findings

- **Load-time naming lands molecules in `srp_*` directly:** `cmd.load(path, object='srp_head', zoom=0)` — no `set_name`/`create` copy needed for the head (demo SDF = game data). Verified `object=` kwarg pattern in `demos.py:194,501,547`.
- **CGO box + molecule both survive `.pse`** (Pitfall 8.3); plugin Python state does NOT. So `cleanup_srp()` MUST be a pure function of object names (`cmd.delete('srp_*')`, no controller/state args) — works in a fresh process after reload. serpentrum needs NO `backup.py` snapshot/restore (Pattern 4: never mutates user objects).
- **The purity checker has NO class permitting `from pymol import cmd`.** Phase 3 must extend `check_purity.py` with `BRIDGE_MODULES = {'serpentrum/pymol_bridge.py'}` (allows pymol/pmg_tk any level, bans PyQt5/numpy, keeps `.exec_()` ban) + add `gui_setup.py` to `GUI_MODULES`. Validated the sibling UI research's §5.2 recommendation; exact spec in §3.2.
- **Camera boundary:** Phase 3 = one-shot `cmd.zoom('srp_*')` + `cmd.refresh()` (SC2: box visible); Phase 4 = locked camera (GAME-02). Phase 3 must NOT install ortho/set_view/view-lock.
- **Prefix discrepancy resolved:** use `srp_` (INFRA-04 + ARCHITECTURE.md Pattern 4 authoritative); STACK.md §3's `serp_` is stale.
- **Demo-file blocker:** no SDFs/manifest in `serpentrum/data/` (only DATA_SOURCES.md + stacking_pi_stack.json). Human checkpoint for 5 PubChem SDFs (option (b)); viewer bridge smoke-testable with a hand-written fixture SDF.

### Bridge Decomposition Recommendation

Create `serpentrum/pymol_bridge.py` (BRIDGE class) with the viewer surface: `load_molecule(path, srp_name)` / `load_box(preset)` / `place_head(srp_name, preset)` / `cleanup_srp()` (pure function of names — no game-state args) / `frame_scene()` / `materialize(setup, candidates)`. The bridge imports `from pymol import cmd` + pure modules (`cgo_build`, `setup_logic`, `molecule_data`, `molfile`) via relative imports. It NEVER imports Qt (banned in BRIDGE). `gui_setup.py` (GUI class) calls the bridge; never `cmd.*` directly. Dependency direction: `pure ← bridge ← gui`.

### Demo-Set-Data Recommendation

**Option (b): human provides 5 PubChem SDF files via `checkpoint:human-action`** (matching upload-gate research §6.3). The agent cannot fetch (network rejected) and cannot fabricate (AGENTS.md no-fabrication). The viewer bridge is smoke-testable with a hand-written fixture SDF (test data, not a chemistry claim). SC2's "head molecule appears" can only be human-verified after the checkpoint; the upload path provides a head independently.

### Human-Decision Items

1. Approve the purity-checker BRIDGE class + `pymol_bridge.py` (§3, §8.1) — consolidates with sibling research §9.1.
2. Approve the `srp_` prefix reservation + "delete-all-srp on Cleanup" one-click policy (§2.3, §8.2).
3. Confirm one-shot `cmd.zoom('srp_*')` framing in Phase 3 (vs. no camera work until Phase 4) (§5, §8.5).
4. Confirm "Random" head = first-candidate placeholder in Phase 3 (§6.3, §8.4) — consolidates with sibling research §9.5.
5. Provide the 5 PubChem SDF files + approve manifest.json creation (§7, §8.6) — consolidates with sibling researches.
6. Confirm `BOX_DISPLAY_Z = 5.0` Å (§5.3, §8.7) — or defer to Phase-4 playtesting.

### File Created

`.planning/phases/03-molecules-in-the-viewer-setup-tab/03-RESEARCH-viewer-bridge.md`

### Confidence Assessment

| Area | Level | Reason |
|------|-------|--------|
| cmd API (load/load_cgo/delete/get_names/zoom/refresh/translate) | HIGH | Verified against in-repo bioCHEMeleon usage + research-doc [SRC] pointers |
| `.pse` survival of CGO + molecule | HIGH | PITFALLS.md 8.3 verified |
| Cleanup fresh-process design | HIGH | PITFALLS.md 8.3 + ARCHITECTURE.md Pattern 4 + INFRA-04 |
| Purity BRIDGE-class extension | MEDIUM | Inference from checker + documented architecture; human decision |
| `cmd.delete('srp_*')` wildcard semantics | MEDIUM | Prescribed by Pattern 4/8.3; standard PyMOL globbing; verify-at-execution in smoke |
| Camera Phase 3/4 boundary | MEDIUM | SC2 implies visibility; roadmap separates Phase 4 locked camera |
| Demo-file availability | LOW | No SDFs shipped; human-gated; network rejected |
| Head centering / `BOX_DISPLAY_Z` | LOW | Cosmetic; no in-repo source |

**Valid until:** 2026-10-10 (stable domain; re-verify only if the Phase-3 smoke reveals `cmd.delete` wildcard or `.pse` CGO-survival behavior differs from Pitfall 8.3's prescription).

---

*Viewer/materialization-bridge research for: serpentrum Phase 3 — Molecules in the Viewer & Setup Tab*
*Researched: 2026-09-10*
