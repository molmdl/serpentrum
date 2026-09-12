# Phase 4 (Game Loop & Input) — Research: GAME LOOP + LOCKED CAMERA

**Aspect:** the continuous tick loop that drives the snake (thread model + timer mechanism), per-tick movement rendering, the locked 2D camera (GAME-02), 2D-plane enforcement, constant speed (GAME-08), and countdown/pause mechanics.
**Researched:** 2026-09-12
**Domain:** PyMOL 2.5.0 Qt main-loop / thread affinity (`pmg_qt`), `cmd.*` API locking, movement transforms (`editing.py`), camera/view/mouse APIs (`viewing.py`/`controlling.py`), PyQt5 `QTimer` (via `pymol.Qt`).
**Confidence:** HIGH for the timer/thread model + movement + camera-lock APIs (C++/Python source read directly AND empirically probed headlessly); live GUI behavior (QTimer firing cadence, real mouse-drag lock) is necessarily `[ASSUMPTION-needs-human-verify]` (headless `-cq` has no QApplication / no event loop / no real mouse).

**Bottom line (one line):** Drive the tick with a **`QtCore.QTimer` (100 ms interval) on the Qt main thread** — its `timeout` slot runs on the Qt event loop thread = `glutThread` = the GUI thread (source-verified: PyMOL's own `feedback_timer` is exactly this, `pymol_qt_gui.py:389`; `is_gui_thread()` returns True there, so `cmd.*` is safe with immediate flush); move the head each `('moved',)` tick with **`cmd.translate([dx, dy, 0.0], 'srp_head', camera=0)`** (atomic-coordinate, model-axis, **zero drift verified**: 5×0.3 Å = 1.5 Å exact); lock the camera with **`cmd.set('ortho','on')` + `cmd.zoom('srp_box')` + `cmd.button(btn,mod,'none')` for left/middle/right/wheel × {None,Shft,Ctrl,CtSh}** and restore with **`cmd.mouse()` + `cmd.set('ortho', saved)`**; countdown = epoch-guarded recursive `singleShot` (HUD sibling owns it); pause keeps the wizard active (`set_active(False)`, grab-but-no-op) and stops the tick QTimer + rebases elapsed time.

---

## ANSWER (recommendations first, with confidence labels)

Labels: `[VERIFIED-empirical]` = run today via `cmd.exe /c run-conda-pymol.bat -cq tmp/spike_probe/probe_gameloop*.py` (sentinel-flushed output). `[VERIFIED-source]` = read directly from `pymol-src/` at file:line cited. `[ASSUMPTION-needs-human-verify]` = inference / live-GUI-only.

### Q1 — Tick timer mechanism + THREAD MODEL (the crux)

**Recommendation: a single `QtCore.QTimer(interval=100 ms)` owned by the GameTab widget, `timeout` → `_on_tick` → `engine.step(dt)` + `pymol_bridge` movement. NO Python thread, NO `cmd._call_in_gui_thread` marshaling needed (the slot IS on the GUI thread).**

**Thread model — definitively resolved from `pymol-src/` + empirical probe:**

```
REAL GUI PyMOL launch (execapp, pymol_qt_gui.py:1178-1249):
  prime_pymol()  ->  glutThread = thread.get_ident()   [pymol/__init__.py:376-383]
  app = PyMOLApplication(['PyMOL'])                     [pymol_qt_gui.py:1205]
  window = PyMOLQtGUI()                                 [:1208]
    window.feedback_timer = QtCore.QTimer()             [:389]  <-- PyMOL's OWN QTimer
    feedback_timer.timeout.connect(self.update_feedback) [:391]
    feedback_timer.start(100)                           [:392]
  pymol.cmd._call_in_gui_thread = MainThreadCaller()   [:1225]
  app.exec_()                                           [:1249]  <-- Qt event loop = main thread

THREAD AFFINITY (all one thread = glutThread = the main thread):
  Qt event loop (app.exec_)         ─┐
  QTimer.timeout slots               ├─ ALL run on the Qt main thread = glutThread
  PyMOLQtGUI.keyPressEvent           │   (keyPressEvent is a Qt event handler)
  wizard do_special (via C dispatch) ─┘   (PyMOL_Special -> WizardDoSpecial -> do_special)
  plugin dialog signal/slot handlers      (the modeless QDialog shares the same QApp)

is_gui_thread() (locking.py:80-86):
  return glutThread is None or glutThread == thread.get_ident()
  -> True on the Qt main thread  -> cmd.* safe (unlock does _cmd.flush_now, immediate)
  -> False on a worker thread    -> cmd.* slow (unlock waits on queue w/ backoff)
                                    AND risky (PITFALLS.md #6: corrupts state/deadlocks)

=> QTimer.timeout callback runs on glutThread => is_gui_thread() True =>
   cmd.translate / cmd.set / cmd.button / cmd.zoom are ALL safe, immediate-flush.
   No thread, no queue, no marshaling. This is exactly PyMOL's own feedback_timer pattern.
```

| # | Claim | Confidence |
|---|-------|------------|
| T1 | `prime_pymol()` sets `glutThread = thread.get_ident()` on the launching (main) thread. | `[VERIFIED-source]` `pymol/__init__.py:376-383`; module-level default `glutThread = None` at `:543` |
| T2 | The Qt event loop (`app.exec_()`) runs on that same main thread; PyMOL's own GUI uses a `QtCore.QTimer` (`feedback_timer`, 100 ms singleShot → `update_feedback`) on it. | `[VERIFIED-source]` `pmg_qt/pymol_qt_gui.py:389-392, 1205-1249` |
| T3 | `is_gui_thread()` returns True iff the current thread is `glutThread` (or no GUI). On the Qt main thread → True → `cmd.*` safe (immediate `_cmd.flush_now` in `unlock`); on a worker thread → False → slow queue-wait + state-corruption risk (Pitfall 6). | `[VERIFIED-source]` `pymol/locking.py:40-86`; `[VERIFIED-empirical]` probe: `is_gui_thread=True`, `glutThread=14220` |
| T4 | `QTimer.timeout` callbacks fire on the Qt event loop thread = `glutThread` = the GUI thread. Therefore `cmd.*` called from a `timeout` slot is safe. | `[VERIFIED-source]` (T2+T3; Qt timer-affinity semantics) + `[VERIFIED-empirical]` (`is_gui_thread True` on the headless main thread, which sets glutThread identically) |
| T5 | Headless `-cq` has NO `QApplication` (`QApplication.instance()` is None), so QTimer **firing** cannot be tested headlessly — only constructed. The firing cadence / live behavior is human-verify. | `[VERIFIED-empirical]` probe: `QAPP_INSTANCE None`, `QTIMER_CONSTRUCT_NO_APP True` |
| T6 | The wizard `do_special` route (sibling input research's PRIMARY) runs on the SAME thread: `PyMOLQtGUI.keyPressEvent` (a Qt event handler, `pymol_qt_gui.py:50-54`) → `pymolwidget.pymol.button` → C `PyMOL_Special` → `WizardDoSpecial` → `do_special`. So input and tick share one thread — **no cross-thread synchronization is needed for the engine** (no lock on `request_direction`/`step`). | `[VERIFIED-source]` `pymol_qt_gui.py:50-54`; `pmg_qt/keymapping.py:61-72` (arrows → state=-2 special); sibling `04-RESEARCH-input.md` W2 (C dispatch); `[ASSUMPTION-needs-human-verify]` for live keystroke |
| T7 | `cmd._call_in_gui_thread` (`MainThreadCaller`, `pymol/Qt/utils.py:145-199`) exists for NON-GUI threads to marshal calls onto the GUI thread (emit a `Signal` → blocking wait). The game tick does NOT need it (the QTimer slot is already on the GUI thread). It WOULD be the right tool if a worker thread ever needed `cmd.*` (e.g. a future xtb-runner result callback) — but the verified pattern is worker→queue→QTimer-drain (ARCHITECTURE Pattern 2). | `[VERIFIED-source]` `pymol/Qt/utils.py:145-199`; `pymol_qt_gui.py:1225`; `[VERIFIED-empirical]` `has_call_in_gui_thread=True` |

**Why NOT the alternatives:**
- **Python `threading.Thread`** → `cmd.*` from it is the documented Pitfall 6 (corrupts state / deadlocks; `locking.py:64-78` queue-wait has a `# race conditions` TODO, PYMOL-3248). Rejected.
- **PyMOL-internal hooks** (`do_draw` / frame callbacks / idle hooks) → no documented 10 Hz hook; `do_draw` fires on redraw (uncontrolled cadence, tied to refresh not a fixed clock); there is no `cmd.set('idle_hook')` in 2.5.0. The Qt QTimer is the only fixed-rate, GUI-thread-safe option. Rejected.
- **`cmd._call_in_gui_thread` from a thread** → works but pointless when the QTimer slot is already on the GUI thread; adds a thread + blocking wait for no benefit.

**Consistency with the wizard input route (T6):** the input sibling's PRIMARY (wizard `do_special`) delivers arrow keys on the GUI thread; the tick QTimer also runs on the GUI thread. The engine is pure (no locks needed); `request_direction` (input) and `step` (tick) are called sequentially on the same thread, never concurrently. The max-1 pending buffer + tick-boundary application (engine `step` applies pending at START) is naturally race-free. ✓

### Q2 — Movement rendering (per-tick head translate)

**Recommendation: `cmd.translate([dx, dy, 0.0], 'srp_head', camera=0)` per `('moved', (nx, ny))` tick.** `camera=0` = model/world axes (deterministic, independent of camera orientation). The delta is `heading * SPEED_A_PER_S * dt` (the engine's own increment), so PyMOL atomic coords track engine truth with zero drift.

| # | Claim | Confidence |
|---|-------|------------|
| M1 | `cmd.translate(vector, selection, state, camera, object, object_mode)` — when `object=None` (default), translates the **atomic coordinates** of `selection` (regenerates representation geometries); `camera=0` interprets the vector in **model/world axes**, `camera=1` in camera axes. | `[VERIFIED-source]` `pymol/editing.py:1610-1669` |
| M2 | `cmd.translate([3,0,0], 'srp_head', camera=0)` moves a pseudoatom's extent from `[[0,0,0],[0,0,0]]` to exactly `[[3,0,0],[3,0,0]]`. `camera=1` with the default (axis-aligned) view coincides. | `[VERIFIED-empirical]` probe v2: `TL_EXTENT_X3_camera0`, `TL_EXTENT_Y2_camera1` |
| M3 | **Zero drift over repeated incremental translates:** 5 ticks of `[0.3,0,0]` (camera=0) land at exactly `[[1.5,0,0],[1.5,0,0]]` (no float accumulation error at this scale). | `[VERIFIED-empirical]` probe v2: `TL_5TICKS_0.3A` |
| M4 | `cmd.set_object_ttt(object, ttt)` sets the object's **display (TTT) matrix** — does NOT modify atomic coords; `get_extent` *does* reflect the TTT offset (the displayed position moves). 16-float TTT = identity-rotation + pre-translation in the last row. | `[VERIFIED-source]` `pymol/editing.py:1881-1940`; `[VERIFIED-empirical]` probe v3: `TTT_EXT_AFTER_Y5` shows y shifted +5, `TTT_EXT_reflects_offset True` |
| M5 | `cmd.get_object_ttt(object)` **hard-crashes the process** (C-level segfault, not a catchable Python exception) on both a pseudoatom and a real `cmd.fab('ALA')` molecule. AVOID read-back. | `[VERIFIED-empirical]` probe v1 died at `get_object_ttt`; v2 died at `get_object_ttt` after `set_object_ttt` succeeded |
| M6 | `cmd.transform_object(name, matrix, ...)` permanently transforms an object's atomic coords (16-float matrix). Heavier than `translate`; the right tool for one-shot rigid stacking transforms in Phase 5, NOT for per-tick movement. | `[VERIFIED-source]` `pymol/editing.py:2006-2050` |

**Why `translate` (atomic, camera=0) over `set_object_ttt`:**
1. `translate` is already proven in the bridge (`pymol_bridge.place_head` uses `cmd.translate([-cx,-cy,-cz], srp_name)`) — consistency.
2. `set_object_ttt` leaves atomic coords at their original (origin-centered) positions and only offsets the display. Phase 5's spectra handoff needs the **actual atomic coords** (`cmd.get_coordset`/`get_model`) to write the snake `.xyz` for xtb — a TTT-offset head would silently produce wrong coordinates unless "baked" first. `translate` keeps atomic coords = truth, forward-compatible.
3. `get_object_ttt` (the read-back / verification path) crashes (M5). `translate`'s effect is trivially verifiable via `get_extent` (M2).
4. Drift is a non-issue (M3): 5×0.3=1.5 exact; over a 60 s game at 10 Hz (600 ticks) drift is ~600×machine-epsilon×0.3 ≈ 4e-14 Å — negligible.

**Bridge function contract (the gap the HUD sibling flagged):**
```
pymol_bridge.move_head_delta(dx, dy, dz=0.0):
    cmd.translate([float(dx), float(dy), float(dz)], HEAD_NAME, camera=0)
```
The HUD `_on_tick` computes the delta from engine head positions:
```
# before engine.step:  old = engine.head
# after  engine.step:  for ev in events: if ev[0]=='moved': new = ev[1]
# delta = (new[0]-old[0], new[1]-old[1]); bridge.move_head_delta(*delta, 0.0)
```
(Or simpler: the bridge stores `_head_pos` and computes delta from the absolute `('moved', (nx,ny))` position — re-syncs to engine truth every tick. Either is drift-free given M3.)

**During sweeps (Phase 5+: rigid-pivot turns):** the engine emits `('turning', frac)` and does NOT emit `('moved',)` — the head is the rotation pivot (unchanged), only the chain segments rotate. In **Phase 4** there are no segments yet (`pickups=None`, `segments=[]`), so a turn sweep is degenerate (no visible rotation) and only the heading changes. So in Phase 4 the ONLY bridge movement call is `move_head_delta` on `('moved',)` ticks. Phase 5 adds per-segment `cmd.translate`/`transform_object` for the rigid sweep. ✓

### Q3 — Locked camera (GAME-02)

**Recommendation: at `_begin_play` (countdown end), run `lock_camera()`; at every teardown path (game-over / restart / pause-to-setup / dialog-close), run `unlock_camera(saved)`.**

**Clarifying the "NEVER ortho/set_view" rule:** the 03-06-SUMMARY / STATE.md note "camera = one-shot cmd.zoom('srp_*') only, NEVER ortho/set_view" is a **Phase-3 boundary** — Phase 3 must NOT pre-install Phase-4 camera machinery. **Phase 4 OWNS ortho/set_view/view-lock** (explicitly listed at `03-RESEARCH-viewer-bridge.md §5.2:359-363`). So Phase 4 IS expected to use `cmd.set('ortho')`, `cmd.set_view`, and `cmd.button` rebinding. `[VERIFIED-source]`

**LOCK recipe (concrete, every cmd verified):**
```python
def lock_camera():
    """Lock the camera to a 2D ortho view of the box. Returns saved state."""
    saved = {
        'ortho': cmd.get('ortho'),                     # 'on'/'off' string
        'view': cmd.get_view(),                        # 18-float matrix
        # button_mode is NOT changed by the lock (we rebind individual buttons),
        # so cmd.mouse() can restore the mode defaults without saving it.
    }
    cmd.set('ortho', 'on')                             # ortho: no perspective distortion
    cmd.zoom('srp_box')                                # frame the WHOLE box (not the head)
    cmd.refresh()                                      # force a redraw so the frame lands
    # Disable every rotate/zoom/pan/select mouse action (action 'none' = code 22).
    for btn in ('left', 'middle', 'right', 'wheel'):
        for mod in ('None', 'Shft', 'Ctrl', 'CtSh'):
            cmd.button(btn, mod, 'none')
    return saved
```

**RESTORE recipe:**
```python
def unlock_camera(saved):
    """Restore mouse defaults + ortho + view. Called by EVERY teardown path."""
    cmd.mouse()               # re-applies the current button_mode's default bindings
                              # (controlling.py:648-676 reads button_mode, calls button() per entry)
    cmd.set('ortho', saved['ortho'])
    cmd.set_view(saved['view'])
    cmd.refresh()
```

| # | Claim | Confidence |
|---|-------|------------|
| C1 | `cmd.get('ortho')` returns `'off'` by default; `cmd.set('ortho','on')` → `'on'`; restore works. Ortho gives a flat 2D look (no perspective foreshortening) on the xy play-plane. | `[VERIFIED-empirical]` probe v3: `ORTHO_BEFORE 'off'`, `ORTHO_AFTER_ON 'on'`, `ORTHO_RESTORED 'off'` |
| C2 | `cmd.get_view()` returns an 18-float view matrix (column-major 3x3 rotation, origin, clipping planes, orthoscopic flag); `cmd.set_view(v)` round-trips stably (`v == get_view()` after). The default view looks down -Z with +X right, +Y up — i.e. straight at the xy play-plane (the engine's 2D plane). | `[VERIFIED-source]` `pymol/viewing.py:605-658, 705-752`; `[VERIFIED-empirical]` `VIEW_LEN 18`, `VIEW_STABLE True` |
| C3 | `cmd.button(button, modifier, action)` rebinds a mouse button; action `'none'` (code 22) = no-op. All 16 combos `left/middle/right/wheel × {None,Shft,Ctrl,CtSh}` → `'none'` succeed with no error. | `[VERIFIED-source]` `pymol/controlling.py:57-125` (`'none':22` at :80), `:799-868` (button fn); `[VERIFIED-empirical]` `BUTTON_LOCK_ERRORS none` |
| C4 | `cmd.mouse()` (no action) re-applies the **current `button_mode`'s default bindings** by calling `button()` for each entry in the mode's `mode_list` — so it cleanly UNDOES the per-button `'none'` rebinds (restores rotate/zoom/pan). Default mode = `0` = `'3-Button Viewing'`. `button_mode` is unchanged by the lock (we only rebind individual buttons), so `cmd.mouse()` restores the same mode. | `[VERIFIED-source]` `pymol/controlling.py:648-676`; `[VERIFIED-empirical]` `BUTTON_MODE_BEFORE 0 '3-Button Viewing'`, `BUTTON_MODE_AFTER 0` |
| C5 | The mouse lock via `button('none')` does NOT touch keyboard focus or the input wizard. The wizard's `get_event_mask()` returns `key+special` (12), NOT `pick+select` — so the wizard does NOT capture mouse events; mouse rotation still flows through the button bindings, which we disabled. **Both mechanisms are needed and independent.** | `[VERIFIED-source]` sibling `04-RESEARCH-input.md` W1; `pymol/wizard/__init__.py:6-9,55-56` |
| C6 | The box stays visible throughout because the camera frames `srp_box` (the whole play field), not the head. As the head moves within the box it stays in frame; the box CGO (`srp_box`) is static. If a box preset is so large the head shrinks at the edge, that is a playtesting concern (zoom `buffer` arg), not a lock bug. | `[VERIFIED-source]` `pymol_bridge.frame_scene`/`load_box`; `[ASSUMPTION-needs-human-verify]` for visual framing |

**Save/restore scope note (C4 caveat):** `cmd.mouse()` restores the *mode defaults*, so a user who had *customized individual buttons* beyond the mode default loses those customizations. For v1 (educational game, users on default mode) this is acceptable — document it in Help. A fully lossless restore would need a `get_button` API (does not exist in 2.5.0). `[ASSUMPTION-needs-human-verify]`

### Q4 — 2D plane enforcement

| # | Claim | Confidence |
|---|-------|------------|
| P1 | The boundary box CGO spans z ∈ [−`BOX_DISPLAY_Z`, +`BOX_DISPLAY_Z`] = **[−5.0, +5.0]**, center z=0. Built by `cgo_build.box_cgo((x0,y0,-5),(x1,y1,+5))` via `pymol_bridge.load_box`. | `[VERIFIED-source]` `pymol_bridge.py:62, 100-104` (`BOX_DISPLAY_Z=5.0`, `min_corner=(x0,y0,-BOX_DISPLAY_Z)`); `[VERIFIED-empirical]` `BRIDGE BOX_DISPLAY_Z 5.0` |
| P2 | The game plays on the **z=0 xy-plane**. `place_head` centers the head molecule at the model origin (0,0,0). Per-tick movement translates by `[dx, dy, 0.0]` (dz=0), so the head's z stays 0. | `[VERIFIED-source]` `pymol_bridge.py:108-122` (place_head centers at origin); engine `head=(x,y)` 2D (`game_engine.py:158-161, 645-650`) |
| P3 | The engine enforces 2D by construction: `head`/`heading`/`box_min`/`box_max`/segment centroids are all (x,y) tuples; z lives only inside segment atom records as display-only data (`game_engine.py:21-27, 158-161`). The bridge clamps dz=0 on every translate. **No separate "clamp z" step is needed** — the contract is "movement calls always pass dz=0.0." | `[VERIFIED-source]` `game_engine.py:21-27, 645-650` |
| P4 | Pickups (Phase 5) will likewise sit at z=0 (their atoms carry display z, centroids are xy). Not Phase 4's concern (`pickups=None` in Phase 4). | `[VERIFIED-source]` `game_engine.py:203-207, 262-268` |

### Q5 — Constant speed (GAME-08)

| # | Claim | Confidence |
|---|-------|------------|
| S1 | `SPEED_A_PER_S = 3.0` Å/s (`game_engine.py:55`). `step(dt)` advances `head += heading * SPEED_A_PER_S * dt` — **no length-dependent term**, so speed is constant regardless of snake length. | `[VERIFIED-source]` `game_engine.py:55, 645-650` |
| S2 | Recommended pairing: **tick interval 100 ms (dt=0.1 s) → 0.3 Å/tick = 10 Hz**. This matches the engine's own test parameter (`test_engine_core.py` `DELTA=0.1`) and gives smooth motion. `ARCHITECTURE.md` Pattern 3 mentions "e.g. 250 ms" as an example; the HUD sibling recommends 100 ms. Final feel is a Phase-4 playtesting decision. | `[VERIFIED-source]` HUD sibling `04-RESEARCH-hud.md` Q5/open-q 3; `[ASSUMPTION-needs-human-verify]` for feel |
| S3 | The engine is **pure (no wall-clock)** — `dt` is a parameter to `step()`, timing lives GUI-side (`game_engine.py:41-46` docstring: "NO wall-clock anywhere (pause timing is the GUI's job)"). So "constant speed" = the QTimer fires at a fixed 100 ms interval with a fixed dt; QTimer coalescing under load could jitter the *wall-clock* cadence but each tick advances the head by exactly 0.3 Å (the dt is constant, not derived from wall-clock). | `[VERIFIED-source]` `game_engine.py:41-46, 645-650` |
| S4 | A fixed-interval QTimer does NOT self-correct for coalesced/dropped ticks (if the GUI thread blocks, a coalesced tick advances the head by one 0.3 Å step, not the elapsed-time worth). For Phase 4 (single small head, no heavy work on the GUI thread) this is fine. If drift becomes visible, the alternative is a wall-clock-corrected loop (`dt = (now - last)/1000.0`), but that breaks the engine's determinism + the "constant 0.3 Å/tick" test contract. **Recommend the fixed-dt QTimer** for v1. | `[ASSUMPTION-needs-human-verify]` |

### Q6 — Countdown + pause mechanics

**Countdown (owned by the HUD sibling, restated for coordination):** 3-2-1 via recursive `QTimer.singleShot(1000, ...)`, epoch-guarded (every callback closes over `self._epoch` at schedule time and no-ops if stale; bump epoch on Start/Restart/teardown — Pitfall 9.1). At GO! → `_begin_play`:
1. `saved_cam = pymol_bridge.lock_camera()` (Q3).
2. `input.install(engine.request_direction)` (sibling input — wizard `do_special` PRIMARY).
3. `tick_timer.start()` + `elapsed_timer.start()` (the two QTimers; HUD sibling).
4. `session['start_time'] = time.time()`.

**Pause (RESUME without double-timer leaks):**
1. `engine.pause()` (sets `paused=True` → `step()` no-ops; `game_engine.py:720-727`).
2. `tick_timer.stop()` (single QTimer instance; stop/start is leak-free — no second timer is ever created).
3. `session['_pause_time'] = time.time()` (for elapsed rebase).
4. `input.set_active(False)` — keep the wizard active but `do_special` grabs-and-no-ops (sibling input `set_active`). **Do NOT tear the wizard down on pause.**
5. **Camera stays LOCKED during pause** (the game is still active, just frozen; unlocking would let the user rotate a frozen scene — confusing).
6. `pause_btn` label → "Resume".

**Resume:**
1. `session['paused_accum'] += time.time() - session.pop('_pause_time')` (rebase — Pitfall 9.3).
2. `engine.resume()`.
3. `tick_timer.start()` (same instance).
4. `input.set_active(True)`.
5. `pause_btn` label → "Pause".

**Wizard teardown during pause — RECOMMENDATION: keep the wizard active during pause (`set_active(False)`), tear down ONLY at game-over / restart / quit.** This resolves the input sibling's open-question #5.

Rationale:
- Tearing down + reinstalling the wizard on every pause/resume doubles the `set_wizard(prior)` save/restore surface (more leak paths: Pitfall 4.3, 9.2).
- During pause we WANT arrows grabbed (no left/right movie-frame-step leak, no up/down OrthoSpecial churn beyond the unavoidable) even though they don't steer — `set_active(False)` achieves exactly this (sibling input `do_special` returns True without calling `request_direction`).
- Matches `PITFALLS.md` #4: "pausing may keep bindings but queue them" and the input sibling's `set_active` design.
- The epoch guard + single `_teardown_round()` helper (Pitfall 9.2) handle the real teardown at game-over/restart.

| # | Claim | Confidence |
|---|-------|------------|
| D1 | `engine.pause()`/`resume()` are pure flag flips (`paused=True/False`); `step()` returns `[]` while paused. No wall-clock recorded in the engine. | `[VERIFIED-source]` `game_engine.py:619-620, 720-731` |
| D2 | `QTimer.stop()` + `start()` on the SAME instance is leak-free (no second timer). singleShot countdown chains are the ONLY non-cancellable timers — handled by the epoch guard (Pitfall 9.1). | `[VERIFIED-source]` `PITFALLS.md` #9.1; HUD sibling |
| D3 | Elapsed time is delta-based (`time.time() - start_time - paused_accum`), rebase on resume — pause does NOT inflate elapsed. | `[VERIFIED-source]` `PITFALLS.md` #5, #9.3; HUD sibling Q2 |
| D4 | Camera lock + wizard install happen at `_begin_play` (after countdown); teardown (`unlock_camera` + `input.teardown()` + timers stop) happens in the single `_teardown_round()` called by every end path. | `[VERIFIED-source]` `PITFALLS.md` #9.2 (centralize teardown); this research |

---

## Evidence

### Empirical probe outputs (run 2026-09-12)

`tmp/spike_probe/probe_gameloop2.py` (translate + drift) and `probe_gameloop3.py` (TTT/ortho/view/button/thread/bridge), run via `timeout 120 cmd.exe /c "C:\\src\\run-conda-pymol.bat -cq tmp\\spike_probe\\probe_gameloopN.py"`. Verdict = flushed `SPIKE` sentinels (PyMOL swallows exit codes through the `.bat`).

```
SPIKE START: 3.9.13
SPIKE TL_EXTENT_ORIGIN: [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]
SPIKE TL_EXTENT_X3_camera0: [[3.0, 0.0, 0.0], [3.0, 0.0, 0.0]]      # translate camera=0 works
SPIKE TL_EXTENT_Y2_camera1: [[3.0, 2.0, 0.0], [3.0, 2.0, 0.0]]      # camera=1 coincides (axis-aligned)
SPIKE TL_5TICKS_0.3A: [[1.5, 0.0, 0.0], [1.5, 0.0, 0.0]]            # ZERO DRIFT: 5*0.3=1.5 exact
SPIKE TTT_EXT_BEFORE: [[-1.60.., -3.38.., -3.99..], [8.39.., 5.21.., 1.72..]]
SPIKE TTT_SET_OK_no_crash:                                         # set_object_ttt OK on real molecule
SPIKE TTT_EXT_AFTER_Y5: [[-1.60.., 1.61.., -3.99..], [8.39.., 10.21.., 1.72..]]  # y shifted +5
SPIKE TTT_EXT_reflects_offset: True                                # get_extent reflects TTT
SPIKE ORTHO_BEFORE: 'off'
SPIKE ORTHO_AFTER_ON: 'on'
SPIKE ORTHO_RESTORED: 'off'
SPIKE VIEW_LEN: 18
SPIKE VIEW_SET_ROUNDTRIP_OK: True
SPIKE VIEW_STABLE: True
SPIKE BUTTON_MODE_BEFORE: 0 '3-Button Viewing'
SPIKE BUTTON_LOCK_ERRORS: none                                     # all 16 button('none') calls OK
SPIKE BUTTON_RESTORE_MOUSE_OK: True
SPIKE BUTTON_MODE_AFTER: 0
SPIKE THREAD glutThread: 14220
SPIKE THREAD is_gui_thread: True                                   # main thread = GUI thread
SPIKE THREAD has_call_in_gui_thread: True
SPIKE THREAD QAPP_INSTANCE: None                                   # headless: no QApp
SPIKE THREAD QTIMER_CONSTRUCT_NO_APP: True                         # QTimer builds, won't fire headless
SPIKE BRIDGE BOX_DISPLAY_Z: 5.0
SPIKE BRIDGE BOX_NAME: srp_box
SPIKE BRIDGE HEAD_NAME: srp_head
SPIKE DONE:
```
**Crash note:** `cmd.get_object_ttt` (probe v1/v2) hard-crashed the process (C segfault, no Python exception) on both a pseudoatom and a real `cmd.fab('ALA')` molecule — hence avoided in v3. `set_object_ttt` (write) is fine; only the read-back crashes.

### pymol-src file:line excerpts (read directly, 2026-09-12)

- `pymol-src/modules/pymol/__init__.py:376-383` — `prime_pymol()`: `glutThread = thread.get_ident()` (sets the GUI thread); `:543` module-level `glutThread = None`.
- `pymol-src/modules/pymol/locking.py:26-86` — `lock`/`unlock`/`is_gui_thread`: `is_gui_thread` returns `glutThread is None or glutThread == thread.get_ident()`; `unlock` does `_cmd.flush_now` only if `thread_owns_gui`, else waits on `_cmd.wait_queue` with backoff (the Pitfall-6 race path).
- `pymol-src/modules/pmg_qt/pymol_qt_gui.py:389-392` — PyMOL's OWN `self.feedback_timer = QtCore.QTimer()` (singleShot, 100 ms, → `update_feedback`): the precedent that QTimer-on-Qt-main-loop is idiomatic in PyMOL.
- `pymol-src/modules/pmg_qt/pymol_qt_gui.py:50-54` — `keyPressEvent` → `pymolwidget.pymol.button(*args)` (Qt event handler = GUI thread; the wizard `do_special` path enters here).
- `pymol-src/modules/pmg_qt/pymol_qt_gui.py:1178-1249` — `execapp()`: `app = PyMOLApplication()`, `window = PyMOLQtGUI()`, `cmd._call_in_gui_thread = MainThreadCaller()`, `app.exec_()` (Qt event loop on main thread).
- `pymol-src/modules/pymol/Qt/utils.py:145-199` — `MainThreadCaller`: `__call__` does `if self.thread() is QtCore.QThread.currentThread(): return func()` (direct on GUI thread) else `emit` + blocking wait (marshals non-GUI→GUI).
- `pymol-src/modules/pmg_qt/keymapping.py:61-72` — `keyPressEventToPyMOLButtonArgs`: arrows in `specialMap` → `state=-2` (PyMOL_Special).
- `pymol-src/modules/pymol/editing.py:1610-1669` — `translate(vector, selection, state, camera, object, ...)`: `object=None` → atomic coords; `camera=0` → model axes.
- `pymol-src/modules/pymol/editing.py:1881-1940` — `set_object_ttt(object, ttt, ...)`: 16-float TTT display matrix.
- `pymol-src/modules/pymol/editing.py:2006-2050` — `transform_object(name, matrix, ...)`: permanent atomic transform.
- `pymol-src/modules/pymol/querying.py:102-119` — `get_object_ttt` (crashes empirically — M5).
- `pymol-src/modules/pymol/viewing.py:605-658` — `get_view()`: 18-float view matrix; default view looks down -Z, +X right, +Y up.
- `pymol-src/modules/pymol/viewing.py:705-752` — `set_view(view)`: requires 18 floats.
- `pymol-src/modules/pymol/controlling.py:57-125` — `but_act_code`: `'none': 22` (valid no-op action).
- `pymol-src/modules/pymol/controlling.py:609-686` — `mouse(action=None)`: no-arg reads `button_mode` and re-applies the mode's `mode_list` via `button()` (the restore mechanism).
- `pymol-src/modules/pymol/controlling.py:799-868` — `button(button, modifier, action)`: rebinds; lowercases all args; `act_code = but_act_code[action]`.

---

## Code sketches

### 1. Bridge additions (`serpentrum/pymol_bridge.py`, BRIDGE class — already imports `cmd`)

```python
# --- Phase 4: per-tick movement + locked camera ---------------------------
# movement: cmd.translate atomic, camera=0 (model axes), zero-drift verified.
# camera: ortho + zoom('srp_box') + button('none') lock; cmd.mouse() restores.

# Lock buttons: every rotate/zoom/pan/select combo -> action 'none' (code 22).
_LOCK_BUTTONS = ('left', 'middle', 'right', 'wheel')
_LOCK_MODS = ('None', 'Shft', 'Ctrl', 'CtSh')


def move_head_delta(dx, dy, dz=0.0):
    """Translate srp_head by (dx, dy, dz) in MODEL axes (camera=0).

    Atomic-coordinate translate (object=None path). camera=0 makes the
    vector world/model-space, independent of the (locked) camera orientation.
    Zero drift verified: 5 * [0.3,0,0] -> exactly [1.5,0,0]. Called once per
    ('moved',) tick by the HUD. dz stays 0.0 (2D plane; P3).
    """
    cmd.translate([float(dx), float(dy), float(dz)], HEAD_NAME, camera=0)


def lock_camera():
    """Lock the camera to a 2D ortho view of the box. Returns saved state
    for unlock_camera(). Called at _begin_play (after countdown)."""
    saved = {
        'ortho': cmd.get('ortho'),
        'view': cmd.get_view(),
    }
    cmd.set('ortho', 'on')
    cmd.zoom(BOX_NAME)          # frame the WHOLE box (play field), not the head
    cmd.refresh()
    for btn in _LOCK_BUTTONS:
        for mod in _LOCK_MODS:
            cmd.button(btn, mod, 'none')
    return saved


def unlock_camera(saved):
    """Restore mouse defaults + ortho + view. Called by EVERY teardown path
    (win/lose/restart/pause-to-setup/dialog-close). Idempotent."""
    if saved is None:
        return
    cmd.mouse()                 # re-applies current button_mode's defaults
    cmd.set('ortho', saved['ortho'])
    cmd.set_view(saved['view'])
    cmd.refresh()
```

### 2. HUD `_on_tick` movement seam (in `gui_game.py`, GUI class — calls bridge)

```python
def _on_tick(self):
    sess = self._session
    if sess is None or sess['epoch'] != self._epoch:
        return                       # stale / no session
    engine = sess['engine']
    if engine.paused or engine.finished:
        return
    old_hx, old_hy = engine.head
    events = engine.step(TICK_DT)    # PURE; TICK_DT = 0.1
    moved = False
    for ev in events:
        if ev[0] == 'moved':
            moved = True
        else:
            self._handle_event(ev, engine)
    if moved:
        nx, ny = engine.head
        pymol_bridge.move_head_delta(nx - old_hx, ny - old_hy, 0.0)
        # NB: no cmd.refresh() here -- PyMOL redraws on its own feedback_timer
        # (100 ms); at 10 Hz the head updates ~sync with redraws. If motion
        # looks laggy, add cmd.refresh() (cheap) -- verify live.
    if engine.finished:
        self._end_run(engine)
```

### 3. `_begin_play` / `_teardown_round` (camera + input + timer coordination)

```python
def _begin_play(self, scheduled):
    if scheduled != self._epoch:
        return                       # stale countdown chain (Pitfall 9.1)
    sess = self._session
    sess['start_time'] = time.time()
    sess['status'] = 'playing'
    sess['saved_cam'] = pymol_bridge.lock_camera()         # GAME-02 lock
    if input_route is not None:
        input_route.install(sess['engine'].request_direction)  # sibling input
    self._tick_timer.start()
    self._elapsed_timer.start()
    self._update_remaining()
    self.pause_btn.setEnabled(True)
    self._log('Move with the arrow keys.')

def _teardown_round(self):
    """THE single teardown helper (Pitfall 9.2). Called by EVERY end path."""
    self._tick_timer.stop()
    self._elapsed_timer.stop()
    self._epoch += 1                 # kills stale singleShot countdown chains
    sess = self._session
    if sess is not None:
        if input_route is not None:
            input_route.teardown()   # restore prior wizard
        if sess.get('saved_cam') is not None:
            pymol_bridge.unlock_camera(sess.pop('saved_cam'))
    # Phase 5 adds: delete srp_pickup_*, etc.
```

---

## Pitfalls (game-loop/camera-specific, with verified root causes)

1. **`cmd.*` from a worker thread (Pitfall 6).** `threading.Thread` + `cmd.translate` corrupts state / deadlocks (`locking.py:64-78` queue-wait race, PYMOL-3248). **Use the QTimer slot (already on the GUI thread).** No thread is spawned for the tick.
2. **`get_object_ttt` segfaults.** `[VERIFIED-empirical]` — hard C-level crash on pseudoatom AND real molecule; not catchable. **Never call it.** Use `get_extent` to verify positions, or just trust `translate` (M3: zero drift).
3. **`set_object_ttt` leaves atomic coords at origin** → wrong xtb input in Phase 5 (the spectra handoff reads `get_coordset`/`get_model` for the `.xyz`). **Use `cmd.translate` (atomic) for movement** so atomic coords = engine truth. TTT is display-only.
4. **`translate` default `camera=1` (camera axes).** If the locked view were ever non-axis-aligned, `camera=1` would move the head in camera-space xy ≠ model xy, desyncing from the engine. **Always pass `camera=0`** (model axes) for movement. (`place_head` uses default camera=1 for a one-shot center-to-origin, which is fine only when the view is axis-aligned — Phase 4 movement must be `camera=0`.)
5. **Camera drift / box clipped out of view.** Lock frames `srp_box` (the whole play field), NOT the head. If the head is framed instead, it walks out of frame as it moves. **`cmd.zoom(BOX_NAME)` at lock time.** Do NOT re-zoom per tick (the camera is locked). `[ASSUMPTION-needs-human-verify]` for visual framing at each box preset.
6. **Pause/resume double-timer leak (Pitfall 9.1 variant).** Creating a NEW QTimer on resume → two ticks. **Reuse the same QTimer instance** (`stop()` then `start()`); never `QTimer()` in the resume path. The epoch guard handles stale singleShot countdown chains.
7. **Pause inflates elapsed time (Pitfall 9.3).** `time.time() - start_time` counts paused seconds. **Rebase on resume:** `paused_accum += now - pause_time`. `[VERIFIED-source]` PITFALLS.md #9.3.
8. **Elapsed drift from tick-count accumulation (Pitfall 5).** Accumulating `elapsed += 0.1` per tick undercounts when ticks coalesce. **Always recompute `elapsed = time.time() - start_time - paused_accum`** from the wall clock. HUD sibling owns this.
9. **Leaked mouse lock (Pitfall 9.2).** Forgetting `unlock_camera` on some end path (crash, plugin-close, win-without-teardown) leaves the user with a dead mouse. **Single `_teardown_round()`** called by EVERY path (win/lose/restart/pause-to-setup/dialog-close/plugin-reload). `[VERIFIED-source]` PITFALLS.md #9.2.
10. **`cmd.mouse()` restore loses custom button bindings (C4 caveat).** Restores mode *defaults*, not user customizations. Acceptable for v1; document in Help. No `get_button` API exists for lossless save.
11. **Wizard + mouse lock are independent.** The wizard captures keys (mask 12 = key+special, NOT pick+select); mouse rotation still flows through button bindings. **Both must be installed at `_begin_play` and torn down together.** Forgetting the mouse lock → user can rotate the 2D plane mid-game; forgetting the wizard → no steering.
12. **Plugin-Manager reload duplicates timers (Pitfall 7/8).** The QTimer is widget-owned (`QTimer(self)`) → dies with the rebuilt GameTab; the session anchors on `_serpentrum.game_session` (survives reload); the epoch guard no-ops stale callbacks. But a reload mid-game must also `unlock_camera` + `input.teardown()` the OLD session's state — the anchor's `game_session` should be torn down in `begin_game` before building a new one. `[VERIFIED-source]` HUD sibling Pitfall A.
13. **Ortho not restored after game-over.** If `unlock_camera` is skipped, the user is stuck in ortho. The single-teardown-helper discipline (Pitfall 9 above) covers this; verify in human-verify.
14. **`cmd.zoom('srp_box')` vs `cmd.zoom('srp_*')`.** Framing `srp_*` would include the head (and later pickups), which could shift the frame as objects appear. **Frame `srp_box` only** so the play-field framing is stable regardless of head/pickup positions. (Phase 3's `frame_scene` uses `srp_*` for setup preview — that's a different, one-shot context.)

---

## Human-verify checklist (real Windows PyMOL 2.5.0 — GUI/camera verdicts only)

Headless cannot fire QTimer, generate real key/mouse events, or render. These are the live-GUI gates for THIS aspect (steering keys are the input sibling's checklist; HUD widgets are the HUD sibling's).

1. **Continuous movement at ~10 Hz:** after GO!, the head (spheres) moves forward smoothly without stopping; speed looks constant over ~30 s. [GAME-01, GAME-08]
2. **Movement matches engine truth (no drift/jitter):** let the head run into a wall — it should crash at the box boundary, not earlier/later; the visual position matches where the engine says it is. (If using `move_head_delta`, watch for accumulated offset.)
3. **Camera truly immovable during play:** try left-drag (rotate), middle-drag (zoom), right-drag (pan), wheel (zoom), Shift+left, Ctrl+left — NONE should move the camera. [GAME-02]
4. **Box clearly visible throughout:** the orange boundary box stays fully in frame for the whole run, at every box preset. [GAME-02]
5. **Ortho 2D look:** the view is flat (no perspective) during play; restoring after game-over returns to the user's prior projection (ortho off if it was off).
6. **Mouse restored after game-over:** end a run (crash) → left-drag rotates the view again (default restored); wheel zooms. [no leak — Pitfall 9]
7. **Mouse restored after pause-to-setup / dialog close:** quit mid-game → mouse works normally outside the game.
8. **Pause freezes motion cleanly:** click Pause → head freezes mid-step; click Resume → head moves again, elapsed timer does NOT jump (rebase correct). [GAME-07, Pitfall 9.3]
9. **Restart mid-run:** click Restart → camera re-locks, head returns to origin, NO second snake / NO double timer (epoch guard); camera was unlocked-then-relocked (no leak). [Pitfall 9.1/9.2]
10. **Plugin-Manager reload mid-game:** reload → exactly one dialog/session; the old camera lock + wizard are torn down (mouse works, no orphaned do_special). [Pitfall 7/8]
11. **Countdown head does NOT move:** during 3-2-1 the head is stationary; movement starts only at GO!. [GAME-01]
12. **`cmd.refresh()` need:** if motion looks laggy (head position updates visibly behind the engine), add `cmd.refresh()` after `move_head_delta`. Verify whether PyMOL's own 100 ms `feedback_timer` redraw is sufficient without it. `[ASSUMPTION-needs-human-verify]`

---

## Open questions

1. **Is `cmd.refresh()` needed after each `move_head_delta`?** PyMOL's own `feedback_timer` (100 ms, singleShot, → `update_feedback`) triggers redraws at ~10 Hz, which matches our tick rate — so motion may be smooth WITHOUT an explicit `cmd.refresh()`. But `feedback_timer` is `setSingleShot(True)` and re-armed by `update_feedback`, so its cadence is not guaranteed 10 Hz. If motion looks laggy live, add `cmd.refresh()` (cheap) after the translate. **Human-verify item #12.** `[ASSUMPTION-needs-human-verify]`
2. **Box-preset framing at large presets.** `cmd.zoom('srp_box')` frames the box, but a very large box preset might make the head tiny at the edge. The `buffer` arg of `cmd.zoom` could tune this. Verify each preset looks playable. `[ASSUMPTION-needs-human-verify]`
3. **Fixed-dt QTimer vs wall-clock-corrected loop.** Fixed dt (0.1 s) keeps engine determinism + the test contract but a coalesced tick "loses" wall-clock time. For Phase 4 (no heavy GUI-thread work) this is fine. If a future phase puts load on the GUI thread, revisit. **Recommend fixed-dt for v1.** `[ASSUMPTION-needs-human-verify]`
4. **Exact tick interval feel.** 100 ms (10 Hz, 0.3 Å/tick) is the recommendation; 250 ms (ARCHITECTURE.md example) is slower/chunkier. Playtesting decides. **Planner/playtest decision.**
5. **Whether `cmd.zoom('srp_box')` at lock time or a stored `set_view` matrix is more robust.** `zoom('srp_box')` re-frames dynamically (good if box size changes between runs); a stored matrix is more reproducible. `zoom('srp_box')` is simpler and re-frames each game. **Recommend `zoom('srp_box')`.**
6. **Cross-aspect coordination (with HUD + input siblings):** (a) the HUD owns the two QTimers + the `_on_tick` slot that calls `pymol_bridge.move_head_delta`; (b) the input sibling owns `input.install`/`teardown`/`set_active`; (c) THIS aspect owns `pymol_bridge.move_head_delta`/`lock_camera`/`unlock_camera`. The planner must ensure `_begin_play` calls all three (lock_camera, input.install, timers.start) in the right order, and `_teardown_round` calls all three teardowns. The engine instance is the single shared object in `anchor.game_session['engine']` accessed by both the tick and the input handler (same thread — no sync needed). `[ASSUMPTION-needs-human-verify]`

---

## Sources

### Primary (HIGH confidence — pymol-src read directly + empirical probe)
- `pymol-src/modules/pymol/__init__.py:376-383,543` — `prime_pymol`/`glutThread`.
- `pymol-src/modules/pymol/locking.py:26-86` — `lock`/`unlock`/`is_gui_thread` (the API-lock + flush/queue model).
- `pymol-src/modules/pmg_qt/pymol_qt_gui.py:50-54,389-392,1178-1249` — `keyPressEvent`; PyMOL's own `feedback_timer` (QTimer precedent); `execapp`/`app.exec_`/`_call_in_gui_thread=MainThreadCaller()`.
- `pymol-src/modules/pymol/Qt/utils.py:145-199` — `MainThreadCaller` (GUI-thread marshaling for non-GUI threads).
- `pymol-src/modules/pmg_qt/keymapping.py:61-72` — arrows → state=-2 (PyMOL_Special).
- `pymol-src/modules/pymol/editing.py:1610-1669,1881-1940,2006-2050` — `translate` (camera=0 model axes; object=None atomic), `set_object_ttt` (display matrix), `transform_object` (permanent atomic).
- `pymol-src/modules/pymol/querying.py:102-119` — `get_object_ttt` (crashes empirically).
- `pymol-src/modules/pymol/viewing.py:605-658,705-752` — `get_view` (18 floats), `set_view`.
- `pymol-src/modules/pymol/controlling.py:57-125,609-686,799-868` — `but_act_code` (`'none':22`), `mouse()` (re-applies mode defaults), `button()`.
- `tmp/spike_probe/probe_gameloop2.py`, `probe_gameloop3.py` — empirical probes run 2026-09-12 (output excerpts above). Syntax `python3.6 -m py_compile` OK; run via `cmd.exe /c C:\\src\\run-conda-pymol.bat -cq`.

### Secondary (HIGH — repo code + sibling research, cross-referenced)
- `serpentrum/game_engine.py:21-27,41-46,55,158-161,311-365,560-731` — pure 2D engine, `step(dt)` events, `request_direction`, `pause`/`resume`, SPEED_A_PER_S=3.0.
- `serpentrum/pymol_bridge.py:48-62,100-122,142-152` — `from pymol import cmd` (BRIDGE), `BOX_DISPLAY_Z=5.0`, `load_box` (z ±5), `place_head` (centers at origin, uses `cmd.translate`), `frame_scene` (one-shot zoom).
- `serpentrum/cgo_build.py:75-131` — `box_cgo` from two 3D corners (z ±BOX_DISPLAY_Z).
- `tools/check_purity.py:56-65,118-157` — BRIDGE_MODULES/GUI_MODULES allowlists (movement+camera fns go in `pymol_bridge.py` = BRIDGE; the QTimer slot goes in `gui_game.py` = GUI).
- `.planning/research/PITFALLS.md` #2 (UI freeze), #4 (arrow keys/focus), #5 (modal/delta-timer), #6 (cmd from thread — the rule this research confirms), #9 (epoch/teardown/pause-rebase).
- `.planning/research/ARCHITECTURE.md` F9 (QTimer/singleShot), Pattern 3 (engine-owns-truth tick), state-ownership map (elapsed=GUI-owned).
- `.planning/phases/04-game-loop-input/04-RESEARCH-input.md` — sibling INPUT research (wizard `do_special` PRIMARY; `set_active` for pause; `input.py` = BRIDGE class).
- `.planning/phases/04-game-loop-input/04-RESEARCH-hud.md` — sibling HUD research (two-QTimer design, epoch-guarded countdown, anchored session, `_on_tick` seam).
- `.planning/phases/03-molecules-in-the-viewer-setup-tab/03-RESEARCH-viewer-bridge.md §5.2:359-363` — Phase 4 OWNS ortho/set_view/view-lock (the "NEVER" was Phase-3-scoped).
- `.planning/phases/03-molecules-in-the-viewer-setup-tab/03-06-SUMMARY.md` — proven cmd seams (`get_names('public_objects')`, `get_extent` nested lists, one-shot `zoom('srp_*')`, `BOX_DISPLAY_Z=5.0`).

### Tertiary (LOW — not relied upon for any claim)
- Live QTimer firing cadence / real mouse-drag lock / visual framing — all `[ASSUMPTION-needs-human-verify]` (headless has no QApplication/event loop/mouse).

## Metadata

**Confidence breakdown:**
- Tick timer + thread model: HIGH — source-verified (feedback_timer precedent, glutThread, is_gui_thread, MainThreadCaller) + empirical (is_gui_thread True, glutThread set); QTimer *firing* is human-verify (no event loop headless).
- Movement rendering: HIGH — empirical (translate camera=0 zero-drift; set_object_ttt moves display; get_object_ttt crashes).
- Locked camera: HIGH — empirical (ortho, get_view/set_view, button('none')×16, cmd.mouse() restore all verified); real mouse-drag lock is human-verify.
- 2D plane: HIGH — source + empirical (BOX_DISPLAY_Z=5.0, engine 2D, dz=0 contract).
- Constant speed: HIGH — source (SPEED_A_PER_S, step math) + empirical (0.3 Å/tick exact).
- Countdown/pause: HIGH — source (engine pause/resume, singleShot epoch, delta-timer rebase) + aligned with both sibling researches.

**Research date:** 2026-09-12
**Valid until:** 2026-10-12 (stable PyMOL 2.5.0 codebase; engine/bridge/purity patterns unlikely to shift before Phase 4 execution)

---
*Game-loop + locked-camera research for Phase 4: serpentrum — tick QTimer on the Qt GUI thread, cmd.translate movement, ortho+button('none') camera lock.*
*Researched: 2026-09-12. Valid for: PyMOL 2.5.0 open-source (the installed Windows conda build).*
