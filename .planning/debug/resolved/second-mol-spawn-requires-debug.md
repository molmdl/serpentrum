---
status: resolved
trigger: "2nd molecule never spawns without enabling debug mode. Direct run `cmd.exe /mnt/c/src/run-conda-pymol.bat`: only 1st mol spawns, 2nd never appears after pickup. With `cmd.exe /c \"set SRP_DEBUG=1&& C:\\src\\run-conda-pymol.bat\"`: spawning works correctly."
created: 2026-10-11T00:00:00Z
updated: 2026-10-11T03:00:00Z
---

## Current Focus

RESOLVED. Root cause CONFIRMED by a live GUI-mode differential repro (same /c launch form, SRP_DEBUG on vs off), FIXED with a one-line unconditional `debug_tail = None` binding in `gui_game._handle_stack_event`, regression pinned Red->Green (3 new source-scan pins in tests/test_hud_content.py TestDebugTailBinding), gates 998 green, live re-verified in BOTH arms (non-debug pick_0002 spawns with zero exceptions; debug arm byte-identical incl. the DBG capture line).

## Symptoms

expected: After picking up the 1st molecule, the game should spawn the 2nd pickup (and keep spawning subsequent ones after each capture resolution).
actual: Without SRP_DEBUG=1, only the 1st mol spawns. After pickup, the 2nd never spawns. With SRP_DEBUG=1 set, spawning works correctly.
errors: None reported by the user. (In fixed-hindsight: the info box DOES log a subtle "placement error: local variable 'debug_tail' referenced before assignment" per capture — easy to miss while watching the 3D viewer; GUI PyMOL stdout/stderr invisibility in the direct-run case compounds this.)
reproduction: 1) Run PyMOL directly from WSL: `cmd.exe /mnt/c/src/run-conda-pymol.bat` (no env vars). 2) Start the serpentrum game, pick up the 1st molecule. 3) Observe: no 2nd mol ever spawns. Contrast: `cmd.exe /c "set SRP_DEBUG=1&& C:\\src\\run-conda-pymol.bat"` → 2nd mol spawns fine after pickup.
started: Discovered during current testing (2026-10-11, quick-003 rounds). The slash traceback: present since the 05-16 SRP_DEBUG tracer landed in _handle_stack_event — every historical verification ran with the tracer ON (all recorded live checkpoints used SRP_DEBUG=1), which silently bound the variable and masked the defect for every non-debug player since.

## Eliminated

- hypothesis: SRP_DEBUG gates the respawn call itself
  evidence: gui_game.py:1145 `self._respawn_pickup(session, engine)` runs unconditionally inside the capture try block; the cooldown-resume spawn (_on_tick:728-732) is also unconditional (only its log line is gated). spawn.py/placement.py/game_engine.py/pymol_bridge.py/input.py contain zero SRP_DEBUG reads.
  timestamp: 2026-10-11T00:30Z

- hypothesis: debug's extra placement.tail_frame call mutates shared state the spawn path needs (debug accidentally fixing the non-debug break)
  evidence: placement.py read in full — tail_frame/resolve are pure (no input mutation; resolve recomputes tail_frame internally anyway).
  timestamp: 2026-10-11T00:40Z

- hypothesis: viewer materialize of the 2nd pickup silently fails (cmd.load error codes / path/environment)
  evidence: probe arm B materialized pick_0002 fine; arm A never reached materialize at all (exception before respawn). No path/load difference between arms.
  timestamp: 2026-10-11T02:00Z

- hypothesis: the true variable is the cmd.exe launch form (direct vs /c + set-chain) rather than SRP_DEBUG
  evidence: arm B (/c form, SRP_DEBUG=1) worked and arm A (/c form, NO SRP_DEBUG) failed in the SAME launch form — opposite outcomes on the env var alone; the launch form is not the variable.
  timestamp: 2026-10-11T02:05Z

- observation (probe-env artifact, NOT the user's bug — recorded for the class): in the probe GUI launches, pymol's `_pymol.session` was observed switching from a healthy `Session_Storage` (probe start) to a plain `dict` whose keys are EXACTLY the game session dict's keys, between dialog construction and GO! — making any KeySteerWizard construction raise AttributeError (pymol.Wizard._validate_instance: `session.wizard_storage = {}` on a dict) from inside `_begin_play`. The exception is swallowed at the singleShot boundary; `_tick_timer.start()` never runs; the snake freezes with no traceback anywhere visible. Worked around in the probe by pre-installing the wizard while session storage is healthy (input.install's idempotent isinstance early-return then constructs NO wizard at GO!). The user's real runs install the wizard fine (their snakes move in both arms), so this is not THIS bug — but it is a second live instance of the same swallow-and-continue class; if a wizard ever starts failing silently in real runs, check `type(cmd._pymol.session)` first.
  timestamp: 2026-10-11T02:10Z

## Evidence

- timestamp: 2026-10-11T00:00Z
  checked: repo-wide grep for SRP_DEBUG and environ/getenv
  found: gui_game.py:425 `'debug': os.environ.get('SRP_DEBUG') == '1'` stored in the session dict — the ONLY SRP_DEBUG read in python. Consumers of session['debug']: gui_game lines 669 (steer adapter choice), 730/877/1225 (pure log gates), 1044 (pre-resolution tail-frame computation). STACK.md/INTEGRATIONS.md document the tracer; test files pin the builders.
  implication: the complete debug-affected surface is tiny; every consumer must be audited for execution-difference (not just logging).

- timestamp: 2026-10-11T00:05Z
  checked: gui_game.py full read
  found: the five debug gates wrap logging / the steer adapter choice only; `self._respawn_pickup(session, engine)` (line 1145) is unconditional inside the capture try block.
  implication: the respawn CALL is not debug-gated — static reading alone cannot explain the symptom; the divergence must be a runtime effect (exception/state) invisible to pure inspection.

- timestamp: 2026-10-11T00:10Z
  checked: spawn.py, placement.py, game_engine.py full reads
  found: all pure, zero debug reads; after a placed 1st capture the respawn gate provably passes (live=0, can_spawn True, cooldown impossible) and `next_after` cannot return None on real presets. Engine discards the captured pid BEFORE emitting ('stacked', pickup).
  implication: python state at capture time cannot block the 2nd spawn in EITHER arm — the failure must occur between the pickup-block log and the respawn call.

- timestamp: 2026-10-11T00:15Z
  checked: pymol_bridge.py full read; smoke/14 (release E2E) + smoke/06 (input) coverage
  found: materialize_pickup is thin cmd forwarding, no debug coupling; NO automated smoke drives the gui_game capture/respawn seam (smoke 14 drives the raw engine; smokes run -cq without SRP_DEBUG but bypass _handle_stack_event entirely) — the seam is covered only by human verification, which always ran with SRP_DEBUG=1.
  implication: a GUI-mode, non-debug-only defect in the capture seam is invisible to the entire automated battery — matches the symptom timeline.

- timestamp: 2026-10-11T01:00Z
  checked: live GUI probe infrastructure (positional startup script in GUI-mode PyMOL; JSONL telemetry; exemcepthook capture of swallowed slot exceptions)
  found: GUI-mode PyMOL accepts a positional .py (stdout prints go to the PyMOL text pane — file telemetry required); WSL WSLENV (no flags) shares env vars with cmd.exe launches; direct `cmd.exe /mnt/c/...bat` and `/c "..."` forms both resolve WSL paths, pass args, inherit the repo cwd; a startup script exception kills pymol -> probes must be exception-proof; PyQt slot exceptions are swallowed via sys.excepthook (installed in the probe to capture them).
  implication: a faithful, fully-observed REAL-GUI game run is automatable from WSL — enabling a controlled differential.

- timestamp: 2026-10-11T01:30Z
  checked: seeded offline setup search (pure layer, real set_a records): speed=9.133 makes spawner.first place pick_0001 (benzene) at (18.50, 1.47) — inside the 3.0 A capture band of the straight +x head path (capture guaranteed at t~5.5 s), 2nd spawn legal.
  found: zero-steering repro is possible; no human input confound.
  implication: deterministic capture in a REAL GUI session.

- timestamp: 2026-10-11T01:45Z (THE REPRO — two arms, same /c launch form, only SRP_DEBUG differs)
  checked: arm A (NO SRP_DEBUG): countdown -> GO! -> head moves -> capture of benzene at t=6.10 -> "+ Benzene: pi-pi stacking ..." line -> engine.pickups=[pick_0001] only, spawner.issued=1, live=[], NO pick_0002, NO srp_pickup_pick_0002 object; info box then shows "placement error: local variable 'debug_tail' referenced before assignment" on every subsequent observation; stacked=1/srp_seg_1 (attach already happened). arm B (SRP_DEBUG=1): same run -> DBG capture line -> pick_0002 (naphthalene) at (49.45, 37.45), spawner.issued=2, live=[pick_0002], srp_pickup_pick_0002 in the viewer.
  found: THE SMOKING GUN — the failing arm raises UnboundLocalError inside _handle_stack_event AFTER pickup_block/attach but BEFORE _respawn_pickup; the except branch logs 'placement error' (user-missable) and the RESPAWN IS SKIPPED. Debug binds the same local via the trace path and works. Captured live: `n_exc 0` after pre-install workaround, info_last from samples: "placement error: local variable 'debug_tail' referenced before assignm...".
  implication: ROOT CAUSE CONFIRMED — the only execution-relevant consumer difference of the debug gate in the capture seam is the BINDING of the `debug_tail` local; its consumers at (pre-fix) lines 1085/1121 run unconditionally.

- timestamp: 2026-10-11T02:30Z (Red -> Green)
  checked: tests/test_hud_content.py TestDebugTailBinding.test_debug_tail_bound_unconditionally against pre-fix code
  found: FAIL (1 != 2) — the pin reproduces the defect at source level (only the skip-branch binding exists pre-fix).
  implication: regression coverage drives the fix (TDD).

- timestamp: 2026-10-11T02:45Z (post-fix live verification, both arms)
  checked: arm A (NO SRP_DEBUG, post-fix): capture at t=5.55 -> spawner.issued=2 -> pick_0002 (naphthalene, (49.45, 37.45)) IN engine.pickups, live AND viewer (srp_pickup_pick_0002 visible in samples t=6.37-10.04 until the legitimate boundary-crash teardown); ZERO excepthook events; NO 'placement error' line in the full info box. arm B (SRP_DEBUG=1, post-fix): byte-identical behavior + the DBG capture trace line intact (dot=1.000000, plane=3.3830, lat=1.2310), no regression.
  found: the 2nd mol now spawns in the non-debug arm; the debug arm is unchanged; both runs converge to the identical deterministic spawn (same seed -> same pickup positions).
  implication: fix VERIFIED live end-to-end in the real GUI environment, plus gates: python3.6 tests/run_gates.py -> syntax/purity/unittest ALL GREEN, 998 tests (995 + 3 new pins).

## Resolution

root_cause: `serpentrum/gui_game.py` `_handle_stack_event` bound the local `debug_tail` ONLY on (a) the skip path or (b) the SRP_DEBUG=1 trace gate (`if session.get('debug'): debug_tail = placement.tail_frame(...)`), while consuming it UNCONDITIONALLY on BOTH the placed branch (pre-fix line 1085) and the refused branch (pre-fix line 1121) via `if debug_tail is not None:`. In NON-debug runs every NON-skip capture resolution therefore raised `UnboundLocalError: local variable 'debug_tail' referenced before assignment` — on the placed path AFTER `engine.attach_segment` + the viewer rename + the `+ <name>: ...` pickup-block line (the capture LOOKS successful to the player) but BEFORE `self._respawn_pickup(session, engine)` (line 1145, inside the same try) — so the 2nd pickup never spawned. The exception was caught by the function-level except, printing an easy-to-miss "placement error: ..." line into the scrolling info box; with no console attached in the direct-run launch the traceback went nowhere. SRP_DEBUG=1 runs bound the variable via the tracer path and spawned fine — which is also why EVERY historical human verification (all recorded live checkpoints ran with SRP_DEBUG=1 per the phase summaries/STATE.md) masked the bug since the 05-16 tracer landed.

fix: one-line unconditional binding (plus explanatory comment) in `serpentrum/gui_game.py` immediately before the trace gate: `debug_tail = None` — the placed/refused consumers now always see None in non-debug sessions and the trace payload in debug sessions; debug output is byte-identical to before. Regression pins: `tests/test_hud_content.py` `TestDebugTailBinding` (3 source-scan pins: two binding sites incl. the unconditional pre-gate init — the RED driver; exactly two `if debug_tail is not None:` consumers; binding precedes gate + first consumer).

verification: (1) TDD: the primary pin is RED against the pre-fix code (count 1 != 2), GREEN post-fix. (2) WSL gates ALL GREEN post-fix: `python3.6 tests/run_gates.py` — gate 1 syntax+plugin-path PASS, gate 2 purity PASS, gate 3 unittest PASS (998 tests = 995 baseline + 3 new). (3) LIVE end-to-end in real GUI-mode Windows PyMOL 2.5.0, same seeded zero-steering repro both arms (setup speed=9.133 -> pick_0001 benzene (18.50, 1.47) on the +x path): arm A (SRP_DEBUG off) captures at t=5.55 and NOW RESPAWNS pick_0002 (naphthalene, (49.45, 37.45)) present in engine.pickups + live_pickup_ids + the VIEWER (object srp_pickup_pick_0002 in sampled public objects), spawner.issued=2, zero swallowed exceptions, NO 'placement error' line in the info box; arm B (SRP_DEBUG=1) byte-identical to its pre-fix run including the full DBG capture trace line (dot=1.000000 d=3.6000 plane=3.3830 lat=1.2310) — no debug-mode regression. The repro harness (temporary probe driving a REAL GameTab dialog in GUI-mode PyMOL from WSL, removed after verification) is recorded here: a future GUI-only failure class can re-use the technique (positional startup script + WSLENV env passing + file-telemetry + sys.excepthook swallow-capture + input.install pre-install workaround for the unrelated `_pymol.session` pollution observed in probe launches).

files_changed:
  - serpentrum/gui_game.py (capture seam: unconditional `debug_tail = None` binding + comment)
  - tests/test_hud_content.py (TestDebugTailBinding — 3 regression source-scan pins)
