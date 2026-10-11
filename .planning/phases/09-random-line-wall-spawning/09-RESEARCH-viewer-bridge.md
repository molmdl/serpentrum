# Phase 9: Random Line-Wall Spawning — Research: Viewer/Bridge/Smoke

**Researched:** 2026-10-12
**Domain:** CGO rendering through pymol_bridge, srp_* object lifecycle, headless smoke coverage (INFRA/BRIDGE half of Phase 9)
**Confidence:** HIGH (all claims verified against current source with file:line; every API claim is repo-proven — no fabricated PyMOL facts)
**Scope note:** the engine policy (wall geometry sampling, non-overlap math, crash semantics) is a sibling research; this document covers WHAT THE VIEWER/BRIDGE/SMOKE NEED and the exact seams the planner must touch. No CONTEXT.md exists in this phase dir (checked 2026-10-12); the owner verbatim request in ROADMAP.md:334 is the only locked input.

**Primary recommendation:** add ONE pure builder `wall_cgo` in cgo_build.py (vertical LINES fence, ±BOX_DISPLAY_Z band, red, linewidth 3.0), TWO thin bridge functions in pymol_bridge.py (`load_line_wall` + `delete_walls`), ONE teardown line in gui_game.py, and ONE new REQUIRED smoke `smoke/15_line_wall_smoke.py`. No purity allowlist edits. No QApplication in the smoke.

---

## 1. Verified viewer/bridge behavior (file:line evidence)

### 1.1 The box builder — the exact template a wall builder clones

`serpentrum/cgo_build.py` is PURE (auto-classified; `import math` only — cgo_build.py:50). Its box builder emits a `BEGIN, LINES` block with ONE `LINEWIDTH` header and ONE `COLOR` header:

- Header: `[LINEWIDTH, w, BEGIN, LINES, COLOR, r, g, b]` — 8 floats (cgo_build.py:126).
- Per edge: `[VERTEX, x, y, z, VERTEX, x, y, z]` — 8 floats (cgo_build.py:127-129).
- Trailer: `[END, STOP]` — 2 floats (cgo_build.py:130). Total 106 floats for 12 edges.
- Builder default `color=(1.0, 0.4, 0.1)`, `linewidth=2.0` (cgo_build.py:75).

Local opcode constants (cgo_build.py:58-72) exist for everything a wall needs (`LINES=1.0`, `BEGIN=2.0`, `END=3.0`, `VERTEX=4.0`, `COLOR=6.0`, `LINEWIDTH=10.0`, `STOP=0.0`) — **no new opcodes, no `pymol.cgo` import, no constant additions.** The module docstring lists the public builders (cgo_build.py:41-48) — a 4th entry is a docstring edit, nothing more.

The mini CGO interpreter in `tests/test_cgo_build.py:29-73` already parses LINES/VERTEX/END/STOP streams (note: `TRIANGLE_STRIP=5.0` is NOT in the `_OPERANDS` table at test_cgo_build.py:29-40 — do NOT build the wall as filled triangles; LINES needs zero test-harness changes).

### 1.2 Box appearance today (both "box colors", and the 3.0 linewidth decision)

- `pymol_bridge.py:74-75`: `DEFAULT_BOX_COLOR = (1.0, 0.4, 0.1)` warm orange, `DEFAULT_BOX_LINEWIDTH = 3.0`.
- Commit `e8b3a9d` (2026-09-12, fix(03-08)): "thicken boundary box default linewidth 2.0 -> 3.0 … so the box is clearly visible on a dark background (human feedback: 'box too thin')" — verified via `git show e8b3a9d`. This is the recorded linewidth-visibility precedent: **anything thinner than 3.0 was already human-rejected once** for on-screen visibility. 03-VERIFICATION.md:27 records the same ("linewidth 3.0 (post-fix e8b3a9d) for visibility").

### 1.3 The load pattern (load_box → cmd.load_cgo) and the replace pattern (07-09)

- `load_box(preset, color=DEFAULT_BOX_COLOR, linewidth=DEFAULT_BOX_LINEWIDTH)` (pymol_bridge.py:91-109): reads `setup_logic.BOX_PRESETS[preset]` for **xy only**, extends z itself to `±BOX_DISPLAY_Z` (pymol_bridge.py:104-105), and calls `cmd.load_cgo(cgo_build.box_cgo(...), BOX_NAME, zoom=0)` (pymol_bridge.py:106-108).
- `load_mode_arrows(cgo, name=MODE_VEC_NAME, zoom=0)` (pymol_bridge.py:503-515) is the CGO-through-bridge precedent for named overlay objects; its docstring pins the REPLACE contract: *"Replace semantics live in the caller: delete_object(name) first, then load (07-09 wires this)"* (pymol_bridge.py:511-512). Live proof of delete-then-load: smoke/13 stage 2 (`pb.delete_object(pb.MODE_VEC_NAME)` then `pb.load_mode_arrows(cgo)`, smoke/13:113-115).
- `reload_head` (pymol_bridge.py:378-406) is the molecule-world "one live object per kind" reload fix (delete-if-exists → load → show → recenter), proving delete-then-load is also the canonical "one live object per kind" mechanism.
- Guarded deletes: `delete_object(name)` checks `object_exists` first because `cmd.delete` on a missing name raises a Selector error (pymol_bridge.py:419-428). Pattern-deletes (`delete_pickups()`, pymol_bridge.py:409-416 → `cmd.delete('srp_pickup_*')`) are idempotent and tolerate vanished objects by construction.

### 1.4 cleanup_srp sweeps ANY srp_wall name — verified wildcard contract

`cleanup_srp()` (pymol_bridge.py:129-143) counts objects with `n.startswith(SRP_PREFIX)` where `SRP_PREFIX = 'srp_'` (pymol_bridge.py:61,140-141) and executes `cmd.delete(SRP_PREFIX + '*')` (pymol_bridge.py:142). Both `srp_wall` and `srp_wall_<n>` match. Live wildcard proof: smoke/03 `s_cleanup_wildcard` (smoke/03:114-121, count==2, non-srp sentinel survives) and the module docstring contract (pymol_bridge.py:21-36, INFRA-04 / .pse-reload fresh-process recovery; AGENTS.md "srp_ prefix reservation"). srp_ is RESERVED for game objects — a wall MUST be srp_-prefixed or it escapes cleanup and orphans after `.pse` reload (pymol_bridge.py:30-36, 491-496).

### 1.5 Restart hygiene sweeps walls for free (rebuild_scene ordering)

`gui_game.rebuild_scene(setup, records_by_id)` is MODULE-LEVEL (gui_game.py:161-206) and runs `pymol_bridge.cleanup_srp()` FIRST — "ORDER IS LOAD-BEARING" (gui_game.py:164-175, the 05-16 re-test fix C root cause) — before `load_box` and `reload_head`. Any `srp_wall*` objects from a prior run are purged on every Start/Restart with ZERO new wiring. This ordering is pinned headless by smoke/08 `s_sceneclr`/`SCENECLR` (smoke/08:401-444, calls `gui_game.rebuild_scene` directly — the headless-safe module seam).

### 1.6 Completion flow: pickups get an EXPLICIT teardown delete; walls need the same

`_end_run` (gui_game.py:1382-1402) = verdict log → `_teardown_round` (call at :1400) → `_present_completion` (:1402). Inside `_teardown_round`, THE single teardown helper (gui_game.py:1482-1530), step (f) is `pymol_bridge.delete_pickups()` at **gui_game.py:1524** — pickups die on EVERY end path; the chain (`srp_head`/`srp_seg_*`) and `srp_box` SURVIVE, and `_present_completion` frames the chain with `zoom_chain` ('srp_head or srp_seg_*' — pymol_bridge.py:348-358; 05-15-SUMMARY: "live pickups die, chain survives, camera unlocks").

**Consequence for walls:** a wall would NOT be deleted at completion by any existing call (teardown pattern-deletes `srp_pickup_*` only, pymol_bridge.py:416; zoom_chain never frames walls). A stale wall would survive into the completion view until the next begin_game sweep. The planner must add ONE line in `_teardown_round` beside :1524 — the locked-decision-8 seam ("Phase-5 additions go INTO _teardown_round, never a second helper"; 05-11-SUMMARY patterns-established). Recommended call: `pymol_bridge.delete_walls()`.

### 1.7 Where "the next mol" spawns (the wall's timing neighbor)

`_respawn_pickup` (gui_game.py:1205-1257) is the one-spawn-per-resolution gate: `spawn_mod.build_pickup_seed(...)` (:1245-1246) → `engine.pickups.append(seed)` (:1251) → `pymol_bridge.materialize_pickup(record['file'], name, self._pickup_m16(record, centroid))` (:1255-1256). It is invoked from `_handle_stack_event`'s resolution tail (:1160) and from the cooldown resume in `_on_tick` (:728-732). The wall's viewer materialization call belongs in this same resolution/respawn neighborhood — WHICH call site exactly is an engine-policy/gui-research decision (capture-tick vs cooldown-respawn-tick), not an infrastructure one.

### 1.8 Crash display path is reason-agnostic — a wall crash needs NO new HUD plumbing

`_handle_event`'s `('crashed', X)` branch prints `'crashed into %s' % ev[1]` + `_dbg_event(engine, 'crashed', result=ev[1])` (gui_game.py:770-772). An engine crash reason naming the wall (e.g. `'wall'`) flows through unchanged, including the free `'DBG event crashed ... result=wall'` trace line (hud_logic.py:443-470 `debug_event_trace`).

### 1.9 Smoke registry + verdict mechanics (run_gates.py)

- `REQUIRED_SMOKES` tuple: tests/run_gates.py:55-76 — 11 entries (01,03,04,05,06,07,08,10,12,13,14). A missing required smoke FAILS the gate (run_gates.py:35-37,174-179). Registration precedent: append at tuple end with a per-plan comment; SMOKE_TIMEOUT untouched (08-04-SUMMARY:73 "REQUIRED_SMOKES append at tuple end with per-plan comment").
- `run_smoke` is ONE `cmd.exe /c C:\src\run-conda-pymol.bat -cq <script>` subprocess PER script, run SEQUENTIALLY (run_gates.py:149-162 loop at :174-180), `cwd=ROOT` (repo root is /mnt/c-backed, relative script path with `\` conversion at :151 — no staging-dir copy for smokes; scripts resolve ROOT at runtime via `_resolve_root()`, smoke/03:36-53). Per-script timeout 90 s (run_gates.py:79).
- **Verdict = flushed sentinels ONLY:** `passed = 'SMOKE-OK' in out and 'SMOKE-FAIL' not in out` (run_gates.py:161); exit codes through the .bat are always 0 and never trusted (run_gates.py:22-24,159-160). Gate output echoes the first SMOKE-OK line per smoke (run_gates.py:184-188).
- **Gate cost per REQUIRED smoke ≈ one Windows PyMOL launch.** Measured precedent: smoke 14 (9 stages incl. spectra parse + PNG render) "flushes SMOKE-OK RELEASE-E2E in ~15 s (90 s SMOKE_TIMEOUT untouched)" (08-04-SUMMARY:58). A minimal smoke-13-class smoke costs the launch plus seconds of script. Today's battery = 11 launches.
- Smoke numbering: glob `smoke/[0-9][0-9]_*.py` (run_gates.py:171); slots 01..14 exist (02 is the standing informational FAIL — the 01-05 offscreen dead end; 09/11 informational) → **next free slot: 15.**
- WSL→Windows path guard: smokes are never passed `/mnt/c/...` raw; the gate passes the RELATIVE path with backslashes (run_gates.py:151) and the .bat leg inherits a Windows cwd. `tools/winpath.py` exists for harness/gate use only (winpath.py:3-8 BOUNDARY) — a wall smoke needs NO path conversion, same as smokes 03-14.

### 1.10 No wall code exists anywhere (greenfield)

`grep -rn wall serpentrum/` returns only doc-text ("box walls", "wall-clock"). GameEngine has no wall state; boundary crash is `('crashed', 'boundary')` via `box_min/box_max` + `BOUNDARY_MARGIN_A = 1.0` (game_engine.py:110-115, 673-684). Everything wall-shaped in the viewer/bridge is new code.

---

## 2. Rendering contracts for Phase 9

### 2.1 Wall geometry: vertical LINES fence spanning the full z band

**What:** one straight 2D segment (x1,y1)→(x2,y2) on the movement plane, rendered as a **4-edge LINES rectangle** ("fence") filled to the box's display depth:

```python
out = [LINEWIDTH, w, BEGIN, LINES, COLOR, r, g, b]
for (a, b) in [(p1_bot, p2_bot), (p2_bot, p2_top), (p2_top, p1_top), (p1_top, p1_bot)]:
    out.extend([VERTEX, ax, ay, az, VERTEX, bx, by, bz])
out.extend([END, STOP])
```
i.e. bottom edge (z=-BOX_DISPLAY_Z), top edge (z=+BOX_DISPLAY_Z), two vertical edges at the endpoints — exactly the box's own z-vertical pattern (cgo_build.py:117-124) shrunk to one segment. 8 header + 32 edge + 2 trailer = **42 floats**, parseable by the existing mini interpreter unchanged.

**Why the full z band (not flat at z=0):**
- The locked camera looks **down -z at the xy plane** (pymol_bridge.py:352-355: "The saved default view looks down -z at the xy plane"; camera = ortho, view locked by `lock_camera`, pymol_bridge.py:196-212). EVERY xy-plane drawing is face-on, never "edge-on" — the box's own z=±5 rectangles render as full on-screen rectangles today. So z-band choice does NOT affect locked-camera visibility; the edge-on worry applies only to post-unlock oblique views.
- Under the locked camera the fence projects to EXACTLY the 2D collision segment (verticals collapse to endpoint dots; top/bottom edges coincide with the segment) — **on-screen visual truth == the engine's 2D collision truth at the play plane.**
- After unlock (completion view, paused exploration), a flat z=0 line becomes viewing-angle-ambiguous, while a floor-to-ceiling fence still reads as a "wall" (the owner's word) from any angle. 3D presence = free with 4 LINES; a z=0 flat segment is NOT recommended.
- A z-filled fence matches the box's own z extent (±BOX_DISPLAY_Z, pymol_bridge.py:66), so the wall visually spans floor-to-ceiling like a fence inside the box — no TRIANGLE_STRIP fill (untested opcode in the interpreter, needs no fill), no skew (a single skewed line (x1,y1,-5)→(x2,y2,+5) projects the same under the lock but looks like a skewer, not a wall, at any oblique angle).

### 2.2 Color + linewidth (obstacle vs boundary)

| Object | Color | Linewidth | Source |
|---|---|---|---|
| srp_box (boundary) | warm orange (1.0, 0.4, 0.1) | 3.0 | pymol_bridge.py:74-75 |
| mode arrows (overlay) | blue (0.2, 0.6, 1.0) | n/a | cgo_build.py:134 |
| **srp_wall (recommended)** | **pure red (1.0, 0.0, 0.0)** | **3.0** | this research |

- **Color: pure red (1.0, 0.0, 0.0).** Maximally distant from the orange boundary in hue, visibly distinct from pickup sticks (element-colored) and the blue mode arrows; red is the conventional hazard/obstacle color, so the wall reads "don't touch me," while orange stays "the box." High-contrast on the dark background for which linewidth 3.0 was already tuned (e8b3a9d).
- **Linewidth: 3.0** — the e8b3a9d human-verified visibility floor. The color already differentiates wall from boundary; a heavier wall width (e.g. 4.0) is a feel-check-tunable parameter the owner can request later, but research recommends starting at parity with the box (3.0) so only color carries semantics.

### 2.3 Naming + lifecycle

- **Name: `srp_wall`** for the single-live-wall policy (one wall at a time, replaced per spawn event) — matching the singular-object precedent (`srp_box`, `srp_head`, `srp_mode_vec`, pymol_bridge.py:69,70,499). **If the engine policy accumulates walls instead** (progressive difficulty), the precedent is `srp_seg_<n>` (index-keyed at capture time, gui_game.py:1079) → `srp_wall_<n>`. cleanup_srp sweeps BOTH forms (1.4). This is an engine-policy decision mirrored into the bridge as a name ARGUMENT — the bridge function takes `name=WALL_NAME` and stays policy-agnostic (mirrors `load_mode_arrows(cgo, name=...)`, pymol_bridge.py:503).
- **Replace pattern: delete-then-load per spawn event** — the 07-09 caller contract (pymol_bridge.py:511-512) with `delete_object(name)` guard before load. "Load-once-per-run" is impossible in both policies: in the single-wall policy the object must move per spawn; in the accumulating policy each spawn loads a new name.
- **Deletion contract:** bridge function `delete_walls()` -> `cmd.delete('srp_wall*')` — mirrors `delete_pickups()` (pymol_bridge.py:409-416 "idempotent. Used by teardown AND by the completion flow"). Use the `srp_wall*` pattern (not `srp_wall_*`) so it covers BOTH the singular `srp_wall` and indexed `srp_wall_<n>` forms.

### 2.4 Bridge function signatures to add (pymol_bridge.py)

```python
# --- Phase 9: random line-wall (viewer half; engine owns the 2D truth) --
WALL_NAME = 'srp_wall'
DEFAULT_WALL_COLOR = (1.0, 0.0, 0.0)
DEFAULT_WALL_LINEWIDTH = 3.0

def load_line_wall(p1_xy, p2_xy, color=DEFAULT_WALL_COLOR,
                   linewidth=DEFAULT_WALL_LINEWIDTH, name=WALL_NAME):
    """Build + load ONE line-wall CGO as ``name`` (delete-then-load is the
    CALLER's job -- the 07-09 load_mode_arrows contract, pymol_bridge:511).
    Reads the ENGINE-owned 2D endpoints, derives z from BOX_DISPLAY_Z
    (display-only -- the load_box precedent at :104-105); returns name."""
    cmd.load_cgo(cgo_build.wall_cgo(
        (p1_xy[0], p1_xy[1], -BOX_DISPLAY_Z),
        (p2_xy[0], p2_xy[1], BOX_DISPLAY_Z)), name, zoom=0)
    return name

def delete_walls():
    """Delete every srp_wall* object (pattern delete, mirrors
    delete_pickups :409-416; idempotent -- teardown AND completion)."""
    cmd.delete('srp_wall*')
```

(Exact wall_cgo argument shape per 2.1 — endpoints + the two z extremes; the z values can equally be derived inside `wall_cgo` from a `z_depth` argument; planner's choice, but the BRIDGE must own the ±BOX_DISPLAY_Z call the way `load_box` does at pymol_bridge.py:104.)

**No new imports** — `cmd`, `cgo_build` are already in place (pymol_bridge.py:52,54). Bridge purity carries: BRIDGE allows pymol/pmg_tk at any level, bans PyQt5/numpy always, bans `.exec_()` (check_purity.py:166-172,200-207). Functions stay thin: "its correctness is pinned by the headless Windows PyMOL smoke" (pymol_bridge.py:12-19).

### 2.5 Engine/bridge geometry split (who owns what)

- **Engine (PURE) owns the 2D wall endpoints** — collision math, spawn sampling, and non-overlap-with-new-mol checks are gameplay (game_engine.py:64-69 purity/NO-RNG pattern; the spawner's clearance-gate precedent `next_after(head_xy, heading, chain_atoms, live_centroids)` spawn.py:417). **Bridge does NO gameplay math** — "the bridge is just the cmd-calling surface that turns pure data into PyMOL viewer objects" (pymol_bridge.py:12-17); the controller's viewer-read discipline: "the ONLY cmd calls here are transform/rename/materialize WRITES" (gui_game.py:952-954).
- **Bridge derives z from its own `BOX_DISPLAY_Z = 5.0`** (pymol_bridge.py:63-66; "z is display-only and lives here"). Precedent: `load_box` reads xy presets in the bridge/`setup_logic` and z-extends at pymol_bridge.py:104-105; `_handle_stack_event` reads `display_z = pymol_bridge.BOX_DISPLAY_Z` for the placement gate (gui_game.py:981). The wall z-band MUST equal the box's (±BOX_DISPLAY_Z) for visual containment.
- Per-tick budget is untouched: walls are static once loaded — **zero** wall calls per movement tick (Pattern 5: "Per-tick PyMOL calls are exactly ONE", 05-RESEARCH-pymol-mechanics.md:85-87; verified operators `move_chain_delta`/`sweep_chain` never select walls).
- CGO walls are inert to chain transforms even if accidentally caught in a selection ("CGOs are not transformed", pymol_bridge.py:189-191,341-342; P5-7) — but keep walls OUT of chain selections by name anyway (they are — `srp_wall*` is not matched by `'srp_head or srp_seg_*`).

---

## 3. Smoke plan

### 3.1 Recommendation: NEW REQUIRED smoke 15 (`smoke/15_line_wall_smoke.py`)

**One line:** NEW smoke 15, not an extension — walls are a new object kind + a new bridge channel + new engine rules, and the repo precedent is one-mechanism-per-numbered-smoke (07 transforms, 13 mode arrows, 14 the release chain); extension would either muddy smoke 05's "loop camera" identity or mutate smoke 14, whose value is the frozen GATE V v1 release-chain evidence (08-04-SUMMARY:22-26: the artifact is the chaining of already-proven legs).

| | Option | Cost (every --smoke battery) | Fit |
|---|---|---|---|
| **Recommended** | new smoke/15_line_wall_smoke.py, REQUIRED | ~1 PyMOL launch, ≈10-15 s (launch + seconds of light script; smoke 14 measured ~15 s total incl. spectra+PNG, 08-04-SUMMARY:58) | follows smoke-13 template class exactly; failure surface isolated |
| Alternative | extend smoke 05 or 08 | 0 extra launches (new stages in existing launch) | couples unrelated identities; smoke-05 wall stages add crash-drive state into a camera test; smoke-08 into the stacking-placement test |
| Rejected | extend smoke 14 | 0 extra launches | rewrites frozen v1 release-evidence artifact with feature churn |

Gate-bloat note for the owner: the battery's marginal cost is one launch ≈ 15 s worst case; wall coverage as its own REQUIRED smoke keeps the increment minimal AND keeps future wall regressions diagnosable per-smoke (the existing smoke 13 registration comment pattern, run_gates.py:69-71).

### 3.2 Smoke skeleton (stages + sentinels; every stage has an in-repo precedent)

Follows smoke 01 template rules verbatim (flush=True prints, NO widget construction, NO smoke/__init__.py, `_resolve_root()` per smoke/03:36-53, sentinel verdicts only). NO QApplication stage — see 3.4.

```
STAGE1 WALL-LOADED  spans=...    wall CGO loads as srp_wall via load_line_wall;
                                  object_exists name; get_extent: finite,
                                  non-degenerate, xy span == expected endpoints,
                                  z span == ±BOX_DISPLAY_Z (10.0 total)
                                  [precedent: smoke/03 s_box_load + smoke/13
                                   stage2 extent asserts, smoke/13:107-128]
STAGE2 WALL-REPLACE               delete_object(srp_wall) + load_line_wall at NEW
                                  endpoints -> extent MOVED exactly to the new
                                  expected values (07-09 replace contract)
                                  [precedent: smoke/13:111-117 delete-then-load]
STAGE3 WALL-SPAWN tick=N          (needs the phase-9 engine API): scripted capture
                                  drive exactly like smoke/14 stage 3 (pickups on
                                  the +x path, step(0.1) loop, attach_segment per
                                  'stacked', smoke/14:187-246) with the wall policy
                                  ON; assert the engine's wall state + the newly
                                  spawned pickup appear on the SAME tick's event
                                  list -> then mirror-load BOTH via the bridge
                                  (materialize_pickup + load_line_wall) like the
                                  controller does; assert both names public
STAGE4 WALL-CRASH tick=N          engine seeded with a wall directly across the
                                  +x path (e.g. p1=(3,-3) p2=(3,3), heading
                                  'right'); step(0.1) until finished; assert
                                  result=='crashed' with the wall as the crash
                                  reason, finished==True (the reason-agnostic
                                  'crashed into %s' HUD seam, gui_game:770-772)
                                  [precedent: smoke/14 stage-3 drive loop]
STAGE5 WALL-DELETE removed=N      bridge contract: load wall(s) + verify
                                  delete_walls() removes exactly srp_wall*,
                                  non-srp sentinel + pickups survive
                                  [precedent: smoke/03 s_cleanup_wildcard]
STAGE6 SCENECLR-WALL              rebuild_scene(setup, records_by_id) with wall
                                  leftovers staged (LOAD-BEARING order pin) ->
                                  srp_wall* gone, fresh srp_box+srp_head present
                                  [precedent: smoke/08 s_sceneclr, smoke/08:401-444]
(optional STAGE PSE-WALL           save .pse / delete srp_* / reload -> srp_wall
                                  survives, cleanup_srp removes it fresh-process;
                                  [precedent: smoke/03 s_pse_survival, smoke/03:100-111])
SMOKE-OK LINE-WALL                final flushed verdict
```

**What is provable headless (all precedented):** (a) object existence + expected extent via `cmd.get_names('public_objects')` / `cmd.get_extent` (extent read-back on a CGO object is live-proven for `srp_mode_vec` in smoke/13:118-126; a LINES-only CGO's extent is indirectly proven by `cmd.zoom(BOX_NAME)` inside `lock_camera` (pymol_bridge.py:207, live-passed by smoke/05) — direct `get_extent` on a LINES CGO is a VERIFY-AT-EXECUTION point at first smoke run; if it misbehaves the fallback is name-presence + the pure WSL builder tests pinning exact floats); (b) a deliberate head-drive into the wall ending the run through the engine's real crash path — standard pure-engine script (smoke/14 stage 3 pattern, no gui_game widget needed); (c) wall gone after completion-path hygiene — provable via the bridge functions (STAGE5) and via module-level `rebuild_scene` (STAGE6), since `_teardown_round` is a widget method that CANNOT run headless (01-05 offscreen dead end, STATE.md Blockers).

**What is NOT headless-provable** (goes to source-scan pins + the phase-closing human checkpoint): the `_teardown_round` wiring line and the exact controller spawn call-site. Pin them with the TestDebugTailBinding source-scan pattern (tests/test_hud_content.py:895-925: read `gui_game.py` source, slice between `def _handle_stack_event`/`def _dbg_capture_line` markers, assert content) — e.g. a `TestWallWiring` asserting `delete_walls` appears inside the `_teardown_round` slice and the wall load call inside the spawn seam slice.

### 3.3 Registration edit (exact, one hunk)

Append to `REQUIRED_SMOKES` (tests/run_gates.py:55-76) after the smoke-14 entry:

```python
                    # 15 = random line-wall render + wall-crash + restart
                    # hygiene (Phase 9) — viewer channel, replace-per-spawn,
                    # cleanup sweep on every end path
                    'smoke/15_line_wall_smoke.py')
```
(Tuple append + comment, the 08-04 pattern — 08-04-SUMMARY:73; nothing else in run_gates.py changes. `git diff` shows ONLY the tuple append, the 08-04 discipline.)

### 3.4 No QApplication stage needed

The wall is CGO lines only — no QFontMetrics, no QPainter, no drawText. The AGENTS.md renderer rule ("any headless smoke touching QPainter/fonts MUST first do `app = QApplication.instance() or QApplication([])`") applies only to paint legs; smoke 03/05/13 load CGOs and call `cmd.refresh()` with NO app guard and never crash — direct precedent that a CGO-only smoke needs none. Do NOT copy smoke 12 stage 0 / smoke 14 stage 0 (both guard only because stage PNG render legs paint fonts).

### 3.5 WSL pure-layer coverage riding gate 3 (zero Windows cost)

- `tests/test_cgo_build.py`: new `TestWallCgo` class — 42-float structure, mini-interpreter parse, endpoint/z/color/linewidth propagation, all-floats (the TestBoxCgo pattern, :129-222).
- Source-scan wiring pins in `tests/test_hud_content.py` (3.2 above).
- Engine wall tests (state, spawn policy, clearance, crash) ride the WSL unittest gate — engine-policy research's plans own them.

---

## 4. Purity/allowlist impact

**None. Zero edits to tools/check_purity.py.**

- `pymol_bridge.py` is already BRIDGE-class (`BRIDGE_MODULES`, check_purity.py:84) — new functions and constants land with no registration. No new imports beyond the existing `pymol`/relative-`cgo_build` (the two classes' edge cases: PyQt5/numpy banned, `.exec_()` banned — the design uses none).
- `cgo_build.py` is PURE by default (not in any allowlist — check_purity.py:95-103 `classify` falls through to PURE; "a future pure module is automatically covered", check_purity.py:30-31) — a `wall_cgo` builder needs no registration; it must keep stdlib-only (`math` already imported).
- **New modules are RECOMMENDED AGAINST strongly:** a new bridge-ish module would need a deliberate `BRIDGE_MODULES` edit (check_purity.py:84), a new GUI module a `GUI_MODULES` edit — both targets for this work already exist. hud_logic (DBG line builder) is already PURE (hud_logic.py:4). No structural changes anywhere.
- Gate 1 plugin-path safety: no `__init__.py` in tests/smoke/tools, no root-level `*.py` (nothing this phase creates touches those — a new `smoke/15_*.py` matches the safe numbered pattern, run_gates.py:171).

## 5. Debug tracer spec (Q10)

### 5.1 Exact wiring facts (verified)

- `SRP_DEBUG=1` is read ONCE per run at `begin_game`: `session['debug'] = os.environ.get('SRP_DEBUG') == '1'` (gui_game.py:425) — the ONLY env read; consumers are cheap `session.get('debug')` gates (33c13e7 debug-session doc: "gui_game.py:425 … the ONLY SRP_DEBUG read in python").
- DBG builders live PURE in hud_logic.py: `debug_capture_trace` (:383-420 — the `dot=1.000000 d=3.6000` format: `'DBG capture %s %s %s'` + `dot=%.6f` + `d=%.4f plane=%.4f lat=%.4f` + `box=(%.1f,%.1f)/(%.1f,%.1f)` + `stacked=%d pickups=%d`), `debug_event_trace` (:443-470), `debug_turn_request` (:557-576), `debug_spawn_cooldown*` (:423-440). A wall builder joins this family.
- The crash event trace for a wall crash comes FREE via `_dbg_event` (gui_game.py:771-772) — `'DBG event crashed ... result=wall'` needs zero new code.
- **33c13e7 lesson (2026-10-11, MUST be honored):** the capture seam's `debug_tail = None` binding is UNCONDITIONAL precisely because debug-gated locals + unconditional consumers broke non-debug spawning for weeks (commit message: "bind debug_tail unconditionally"; regression pins TestDebugTailBinding). Any wall DBG locals get the same unconditional-bind discipline.

### 5.2 Recommended wall DBG line (so the feel-check can verify non-overlap live)

New pure builder `debug_wall_trace(wall_id, p1, p2, new_mol_id, new_centroid, gap, tick=None)` in hud_logic.py, called (gated by `session.get('debug')`) from the controller's wall-spawn seam, UNCONDITIONALLY computed data, output:

```
DBG wall spawn <wall_id> p1=(%.2f,%.2f) p2=(%.2f,%.2f) len=%.4f new_mol=<pid>@(%.2f,%.2f) gap=%.4f
```

- `p1`/`p2` — the engine's 2D endpoints; `len` — segment length (span sanity, `%...s` aligned with the `d=%.4f` precedent).
- `new_mol` — the pid + spawn centroid of the molecule spawned at the same tick (`build_pickup_seed`'s `(record, pid, centroid)` triple is exactly the data, gui_game.py:1244-1246).
- `gap` — the engine's OWN pure-computed min 2D clearance between the wall span and the new mol's atoms/centroid (the `lateral_gap` precedent: pure sqrt decomposition at hud_logic.py:1194-1195; NEVER a viewer read — the 05-13 discipline "zero get_model/get_extent/get_names anywhere in gui_game", 05-13-SUMMARY:37).
- `gap > 0` on every spawn line is the live-auditable proof of the owner's "should not overlap the newly spawn mol" invariant; the strict invariant assertion belongs in the pure engine spawn tests (engine-policy research), with the DBG line printing the same value for the human feel-check.

## 6. Plan-slicing hints

Natural task granularity derived from the actual work (no padding; engine-policy plans are the sibling researcher's, so slice the INFRA tasks around their API seam):

1. **pure builder plan** — `cgo_build.wall_cgo` + `TestWallCgo` (WSL TDD, RED→GREEN; the 42-float contract). Zero dependencies.
2. **bridge plan** — `WALL_NAME`/`DEFAULT_WALL_*` constants + `load_line_wall` + `delete_walls` in `pymol_bridge.py`; no purity edits; verification = default gates (bridge is not WSL-testable — pymol at module level, pymol_bridge.py:12-15; correctness lands with the smoke).
3. **gui wiring plan** (depends on the engine-policy plan's spawn-event design) — wall load/mirror at the respawn/capture seam, `delete_walls()` line in `_teardown_round` beside :1524, `hud_logic.debug_wall_trace` DBG builder + gated call, source-scan regression pins (`TestWallWiring`, the TestDebugTailBinding pattern), plus the unconditional-bind discipline from 33c13e7 for any debug-only locals. Gates + pin tests only (gui_game touched → battery smoked at plan close, the 05-14 precedent).
4. **smoke plan** (depends on 1+2, and on the engine wall API for STAGE3/STAGE4) — `smoke/15_line_wall_smoke.py` + REQUIRED registration hunk + full `--smoke` battery; verify-at-execution notes: get_extent on a LINES CGO, extent tolerances (float32 storage → 1e-5..1e-3 tolerance classes per smoke/05:96-99).
5. **phase-closing human checkpoint** (repo convention; GUI verdicts are human-verify only, STATE.md Blockers "Offscreen route closed") — wall visibility/orange-vs-red readability live, wall-crash round, walls never overlapping the new mol live with SRP_DEBUG=1, wall gone at completion + Restart.

The viewer/bridge work (1,2) is fully parallelizable with the engine-policy plans; 3 needs the engine event contract frozen; 4 needs both. No new modules; no allowlist edits; no new imports; no CI/timing risks (no per-tick calls anywhere).

---

## Sources

### Primary (HIGH confidence — direct file:line verification)
- serpentrum/cgo_build.py (full read; builder + constants, :50-235)
- serpentrum/pymol_bridge.py (full read; :52-143 cmd-seam/cleanup, :361-428 pickup loads/guarded deletes, :487-515 CGO channel + replace contract)
- serpentrum/game_engine.py (824 lines; no wall state, crash seam :673-702)
- serpentrum/gui_game.py (1588 lines; rebuild_scene :161-206, respawn :1205-1257, teardown :1482-1530, completion :1382-1475, SRP_DEBUG :425, dbg :783-831)
- serpentrum/hud_logic.py (:370-576 DBG builders; formats at :402-420, :455-470)
- tests/run_gates.py (:55-76 registry, :149-162 run_smoke, :79 timeout, :161 sentinel verdict)
- tests/test_cgo_build.py (:22-73 mini interpreter, :129-222 box tests)
- tools/check_purity.py (:72-104 allowlists, :166-207 exec_ ban)
- tools/winpath.py (boundary :3-8)
- smoke/03, 05, 08, 12, 13, 14 (full reads — stage structures, sentinels, _resolve_root, wall-relevant precedents)
- smoke/02 informational status, smoke numbering glob (run_gates.py:171)

### Secondary (repo planning record)
- .planning/phases/03-*/03-06-SUMMARY.md ('public_objects' + get_extent shape, materialize contract) and 03-VERIFICATION.md:27 (linewidth 3.0 post-fix e8b3a9d for visibility)
- git show e8b3a9d (linewidth 2.0→3.0 human feedback), git show 33c13e7 (unconditional debug_tail binding + TestDebugTailBinding)
- .planning/phases/05-*/05-RESEARCH-pymol-mechanics.md (Pattern 4 completion order; Pattern 5 one-call-per-tick; P5-3 zoom-after-unlock; P5-7 CGO not transformed)
- .planning/phases/08-*/08-04-SUMMARY.md (:58 ~15 s smoke cost; :73 registration practice)
- 05-11/05-13/05-15/3-RESEARCH-viewer-bridge summaries (teardown-extension locked decision 8; viewer-read discipline; load-time naming)
- AGENTS.md (srp_ reservation, gates, renderer QApplication rule, WSL/Windows guard)
- .planning/ROADMAP.md:323-335 (Phase 9 verbatim owner request); .planning/STATE.md (offscreen dead end; Phase 9 unplanned)

## Metadata

**Confidence breakdown:**
- Viewer/bridge behavior: HIGH — every claim read from current source with line cites; no training-data PyMOL claims.
- Wall builder spec (42-float LINES fence): HIGH structure (opcode machinery verified), MEDIUM on the exact aesthetic (color/linewidth are feel-check items by nature — pinned to proven values orange/3.0 contrast).
- Smoke plan: HIGH on mechanics (all precedented), MEDIUM on STAGE3/STAGE4 details (need the phase-9 engine API — flagged as the dependency), LOW/verify-at-execution on `get_extent` over a LINES-only CGO (strong indirect evidence via zoom(BOX_NAME); direct read unproven in-repo).
- Purity impact: HIGH — classification rules read directly; zero edits.
- DBG spec: HIGH (formats mirrored from live builders).

**Research date:** 2026-10-12
**Valid until:** stable as long as pymol_bridge/cgo_build/run_gates keep their current shape; re-verify only if engine-policy research chooses the accumulating-wall policy in a way that changes the name pattern (bridge signature is name-agnostic by design).
