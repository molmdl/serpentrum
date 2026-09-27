"""Headless Windows PyMOL release end-to-end CHAIN smoke — 08-04 (DOCS-05).

Run (from repo root; cwd is /mnt/c-backed so cmd.exe inherits C:\\ cwd):
    timeout 90 cmd.exe /c "C:\\src\\run-conda-pymol.bat -cq smoke\\14_release_e2e_smoke.py"

Exit codes through the .bat are ALWAYS 0 (even after a Qt C-abort) —
verdicts are flushed sentinels grepped by tests/run_gates.py --smoke:
    STAGE0 APP                    guarded QApplication([]) exists
    STAGE1 SETUP records=5 cap=2  demo set load + small-cap setup validates
    STAGE2 MATERIALIZE            srp_box + srp_head present after materialize
    STAGE3 WIN ...                scripted engine run reaches 'won' (cap 2)
    STAGE4 XYZ atoms=54           head-inclusive xyz handoff round-trips
    STAGE5 SPECTRA ...            fixture g98 parse -> broadened Scene
    STAGE6 PNG ...                render_image -> temp PNG (magic bytes +
                                  reload 1600x1000 @ 800x500 scale 2)
    STAGE7 ROUNDTRIP ...          save_setup -> load_setup -> merge -> validate
    STAGE8 CLEANUP ...            cleanup_srp removes srp_*; user object survives
    SMOKE-OK RELEASE-E2E          all stages passed
    SMOKE-FAIL <stage>: ...       a stage failed (one line per failure)

This is DOCS-05's one genuinely NEW mechanical artifact: the release flow
legs are each proven elsewhere (materialize in smoke 04, bridge seams in
05/07/08, counts in 10, parse->plot->PNG in 12, arrows in 13) — but nothing
walked setup -> play -> complete -> (fixture) spectra -> IR plot -> save in
ONE headless run (08-RESEARCH-release-audit.md sec 1). Stages 3-5 chain the
pure engine, the SHIPPED xyz handoff seam (xtb_run.build_run_input — the
exact codec gui.py:167 consumes at completion), and the fixture spectra
tail. The hessian run itself stays out of the REQUIRED battery by owner
disposition (06-12 EQ-smoke-1; the real ~100 s run exceeds the global 90 s
SMOKE_TIMEOUT) — the real flow is the phase-closing human checkpoint.

Template rules (copied from smoke/01, 04, 12):
  - every print carries flush=True (stdout is block-buffered when piped)
  - NO widget construction (headless C-abort is uncatchable) — module
    seams ONLY (render_image is a module function; a bare QApplication
    is probe-safe)
  - stage 0 = the LOAD-BEARING app guard (probe RUN A: font access with
    no Q*Application silently hard-kills the process) BEFORE any render
  - never add smoke/__init__.py (findPlugins plugin-path safety)
  - NEVER trust __file__ under -cq (resolve ROOT by validating
    serpentrum/__init__.py candidates)
  - verdict = flushed SMOKE-OK/SMOKE-FAIL sentinels ONLY (never exit codes)
  - no spectra dir is touched: the fixture tail needs no SRP_SPECTRA_DIR
    redirect and writes nothing stable (one temp PNG, removed in-stage)
"""
import os
import sys
import tempfile


def _resolve_root():
    """Repo root, defensively (copied from smoke/01_skeleton_smoke.py).

    Under -cq launch, __file__ is PyMOL's launcher module (NOT this
    script), so naive dirname(dirname(__file__)) lands in
    site-packages. Validate every candidate by the presence of
    serpentrum/__init__.py.
    """
    candidates = []
    if '__file__' in globals():
        _f = os.path.abspath(__file__)
        candidates.append(os.path.dirname(os.path.dirname(_f)))
        candidates.append(os.path.dirname(_f))
    candidates.append(os.getcwd())
    for _c in candidates:
        if os.path.isfile(os.path.join(_c, 'serpentrum', '__init__.py')):
            return _c
    return os.getcwd()


ROOT = _resolve_root()
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from pymol import cmd  # noqa: E402 (available inside PyMOL runtime)
from pymol.Qt import QtWidgets, QtGui  # noqa: E402

FAILURES = []
STATE = {}

G98_PATH = os.path.join(ROOT, 'tests', 'fixtures', 'xtb', 'g98.out')
SENTINEL_FIXTURE = os.path.join(ROOT, 'tests', 'fixtures', 'molfile',
                                'methane.sdf')
PNG_MAGIC = b'\x89PNG'
DT = 0.1  # the shipped cadence: QTimer 100 ms -> step(0.1) (gui_game.py:88-90)


def check(name, fn):
    try:
        fn()
    except Exception as exc:
        print('SMOKE-FAIL %s: %r' % (name, exc), flush=True)
        FAILURES.append(name)


def _extent_center(atoms):
    """gui_game._extent_center in miniature: extent-midpoint translate.

    pure-mirror helper so the head atom list below equals the pose
    materialize + place_head give srp_head (mirror == viewer); only the
    COUNT is asserted downstream, but the honest pose keeps the smoke's
    xyz a truthful snake (head-first order is build_run_input's).
    """
    xs = [a[1] for a in atoms]
    ys = [a[2] for a in atoms]
    zs = [a[3] for a in atoms]
    ox = (min(xs) + max(xs)) / 2.0
    oy = (min(ys) + max(ys)) / 2.0
    oz = (min(zs) + max(zs)) / 2.0
    return [(a[0], a[1] - ox, a[2] - oy, a[3] - oz) for a in atoms]


def _mirror_atoms(record):
    """Origin-centered edge-on (sym, x, y, z) atoms for one demo record.

    gui_game._mirror_atoms' demo half: stack_ring records take
    orientation.edge_on_atoms — the exact pose the pickup m16 lands in
    the viewer, so engine-side capture geometry mirrors the viewer 1:1.
    """
    from serpentrum import molfile, orientation
    parsed = molfile.read_sdf(record['file'])[0]
    assert 'stack_ring' in record, \
        'demo record %r has no stack_ring (set_a pin)' % (record['id'],)
    return orientation.edge_on_atoms(
        parsed['elements'], parsed['coords'], record['stack_ring'])


def s0_app():
    # Stage 0 — THE APP GUARD (probe RUN A): font access without a
    # Q*Application SILENTLY HARD-KILLS the process. Adopt an existing
    # app or construct a BARE one (no widgets — probe stage3 proves
    # this is safe headless). Never construct a second app (warns).
    # MUST run before stage 6's render leg.
    global _APP
    _APP = QtWidgets.QApplication.instance()
    if _APP is None:
        _APP = QtWidgets.QApplication([])
    print('STAGE0 APP', flush=True)


def s1_setup_load():
    # Stage 1 (setup leg): real shipped Demo Set A -> 5 records (smoke
    # 04's pattern) + a SMALL-cap setup dict that validates clean. The
    # cap=2 game below is the 06-12-proven cap-3 class scaled down.
    from serpentrum import setloader, setup_logic
    records, errs = setloader.load_demo_set(
        setloader.package_data_dir(), 'set_a', setloader.default_stacking_path())
    assert errs == [], 'load_demo_set errors: %r' % (errs,)
    assert len(records) == 5, 'expected 5 records, got %d' % len(records)
    assert records[0]['id'] == 'benzene', \
        'first record id %r, expected benzene (manifest order)' \
        % records[0]['id']
    setup = setup_logic.new_setup()
    setup['win_cap_molecules'] = 2      # small cap -> quick scripted win
    setup['head_molecule'] = 'benzene'  # explicit (== 'random' -> records[0])
    setup['box_preset'] = 'medium'
    errors, _warnings = setup_logic.validate(setup)
    assert errors == [], 'scripted setup validate errors: %r' % (errors,)
    STATE['records'] = records
    STATE['setup'] = setup
    # The head mirror (gui_game._build_head_state's demo half): edge-on +
    # extent-centered -> the exact srp_head pose, head-FIRST in the xyz.
    STATE['head_atoms'] = _extent_center(_mirror_atoms(records[0]))
    # User-sentinel object, pre-created so stage 8 can prove cleanup
    # leaves non-srp_* objects untouched (smoke 04 pattern).
    cmd.load(SENTINEL_FIXTURE, object='user_release_e2e')
    print('STAGE1 SETUP records=5 cap=2 head=benzene atoms=%d'
          % len(STATE['head_atoms']), flush=True)


def s2_materialize():
    # Stage 2 (setup -> scene leg): materialize loads srp_box + srp_head
    # (cleanup-first contract: only srp_* are deleted; the stage-1 user
    # sentinel is untouched).
    from serpentrum import pymol_bridge
    errs = pymol_bridge.materialize(STATE['setup'], STATE['records'])
    assert errs == [], 'materialize errors: %r' % (errs,)
    names = cmd.get_names('public_objects')
    assert 'srp_box' in names, 'srp_box not found after materialize'
    assert 'srp_head' in names, 'srp_head not found after materialize'
    n = cmd.count_atoms('srp_head')
    assert n == len(STATE['head_atoms']), \
        'srp_head atoms %d != mirror %d' % (n, len(STATE['head_atoms']))
    print('STAGE2 MATERIALIZE srp_box+srp_head atoms=%d' % n, flush=True)


def s3_scripted_win():
    # Stage 3 (play leg): drive the SHIPPED pure GameEngine headless to a
    # win. Pickups are placed ON the straight-ahead head path via the
    # shipped spawn.build_pickup_seed seam (naphthalene at x=6, then
    # anthracene at x=18), so no steering is ever needed; the loop just
    # calls step(0.1) — the same dt the 100 ms QTimer feeds in the real
    # game loop (jitter is absorbed by the timer, scripted dt is
    # equivalent). The first 5 'moved' ticks are ALSO mirrored into the
    # viewer via pymol_bridge.move_head_delta (smoke 05-proven seam) —
    # no gui_game wiring is rebuilt.
    from serpentrum import game_engine, pymol_bridge, setup_logic, spawn
    setup = STATE['setup']
    by_id = dict((r['id'], r) for r in STATE['records'])
    rec_n, rec_a = by_id['naphthalene'], by_id['anthracene']
    pickups = [
        spawn.build_pickup_seed(rec_n, 'p1', (6.0, 0.0),
                                _mirror_atoms(rec_n)),
        spawn.build_pickup_seed(rec_a, 'p2', (18.0, 0.0),
                                _mirror_atoms(rec_a)),
    ]
    box_min, box_max = setup_logic.BOX_PRESETS[setup['box_preset']]
    engine = game_engine.GameEngine(
        head=(0.0, 0.0), heading='right',
        box_min=box_min, box_max=box_max,
        pickups=pickups,
        cap=setup['win_cap_molecules'],
        atom_budget=setup['atom_budget'],
        speed_a_per_s=setup['speed'])
    ticks = 0
    mirrored = 0
    step_len = engine.speed_a_per_s * DT
    while not engine.finished:
        events = engine.step(DT)
        ticks += 1
        assert ticks < 1000, \
            'scripted win did not finish in 1000 ticks (drifted script?)'
        for ev in events:
            if ev[0] == 'stacked':
                # The engine capture seam is COUNTER-ONLY — attaching the
                # frozen segment is the controller's call (both gui_game's
                # _handle_stack_event and the pure suite's capture()
                # helper in tests/test_phase5_integration.py call this
                # same counter-neutral seam after their placement leg,
                # which smokes 08/10 already cover live).
                engine.attach_segment(ev[1]['molecule_id'],
                                      ev[1]['centroid'], ev[1]['atoms'])
            elif ev[0] == 'moved' and mirrored < 5:
                pymol_bridge.move_head_delta(
                    engine.heading[0] * step_len,
                    engine.heading[1] * step_len, 0.0)
                mirrored += 1
    assert engine.result == 'won', \
        'scripted run ended %r (expected won)' % (engine.result,)
    assert engine.molecules_stacked == 2, \
        'molecules_stacked %d != 2 (cap)' % engine.molecules_stacked
    assert len(engine.segments) == 2, \
        'segments %d != 2' % len(engine.segments)
    STATE['engine'] = engine
    print('STAGE3 WIN ticks=%d stacked=2 atoms=%d mirrored=%d'
          % (ticks, engine.atoms_total, mirrored), flush=True)


def s4_handoff_xyz():
    # Stage 4 (complete -> run-input leg): assemble the SHIPPED handoff
    # text — xtb_run.build_run_input over the live engine atoms,
    # head-FIRST (EQ-xyz-1; the exact codec gui_game anchors at
    # completion and gui.py:167 re-parses at launch time) — then parse
    # it back and pin the head-inclusive count: len(head) +
    # engine.atoms_total (mirror of the gui.py:167 cross-check).
    from serpentrum import xtb_run, xyzio
    engine = STATE['engine']
    snake_xyz = xtb_run.build_run_input(
        STATE['head_atoms'], [seg['atoms'] for seg in engine.segments],
        'smoke14_run')
    comment, atoms = xyzio.read_xyz_text(snake_xyz)
    expected = len(STATE['head_atoms']) + engine.atoms_total
    assert len(atoms) == expected, \
        'round-trip atom count %d != expected %d (head %d + engine %d)' \
        % (len(atoms), expected, len(STATE['head_atoms']),
           engine.atoms_total)
    assert comment == 'serpentrum snake smoke14_run', \
        'comment %r != build_run_input contract' % (comment,)
    STATE['snake_xyz'] = snake_xyz
    print('STAGE4 XYZ atoms=%d comment=%r' % (len(atoms), comment),
          flush=True)


def s5_spectra_tail():
    # Stage 5 (spectra leg): the fixture tail — committed real g98
    # (26 atoms / 72 modes / 3 imaginary, smoke 12's pinned contract) ->
    # plot_logic.build_scene. Fixture-fed by owner disposition (06-12
    # EQ-smoke-1): real hessian runs stay OUT of the REQUIRED battery.
    from serpentrum import spectra, plot_logic
    spectrum = spectra.parse_g98(G98_PATH)
    assert spectrum.n_atoms == 26, 'n_atoms %r != 26' % (spectrum.n_atoms,)
    assert len(spectrum.modes) == 72, \
        'modes %r != 72' % (len(spectrum.modes),)
    scene = plot_logic.build_scene(spectrum.modes)
    assert scene.n_modes == 72, 'scene n_modes %r' % (scene.n_modes,)
    assert scene.n_imaginary == 3, \
        'scene n_imaginary %r != 3' % (scene.n_imaginary,)
    STATE['scene'] = scene
    print('STAGE5 SPECTRA modes=%d imaginary=%d y_max=%.2f'
          % (scene.n_modes, scene.n_imaginary, scene.y_max), flush=True)


def s6_save_png():
    # Stage 6 (save leg): route-A render to a TEMP PNG and re-assert the
    # smoke-12 contract (magic bytes + reload dims 1600x1000 = 800x500 @
    # scale 2 + sane size), then remove the temp file — writes nothing
    # stable (EQ-artifact-1 hygiene; no spectra dir is touched at all).
    from serpentrum import gui_plot
    img = gui_plot.render_image(STATE['scene'], (800, 500), scale=2)
    assert img.width() == 1600 and img.height() == 1000, \
        'image %dx%d != 1600x1000' % (img.width(), img.height())
    tmp = os.path.join(tempfile.gettempdir(), 'srp_smoke14_release.png')
    ok = img.save(tmp, 'PNG')
    try:
        assert ok, 'QImage.save(%r, PNG) returned False' % tmp
        with open(tmp, 'rb') as fh:
            data = fh.read()
        assert data[:4] == PNG_MAGIC, \
            'first bytes %r != PNG magic' % (data[:4],)
        reload_img = QtGui.QImage(tmp)
        assert reload_img.width() == 1600 and reload_img.height() == 1000, \
            'reload %dx%d != 1600x1000' % (reload_img.width(),
                                           reload_img.height())
        assert len(data) > 1000, \
            'suspiciously small PNG: %d bytes' % len(data)
    finally:
        os.remove(tmp)
    print('STAGE6 PNG %d bytes 1600x1000' % len(data), flush=True)


def s7_setup_roundtrip():
    # Stage 7 (SETUP-08 pure leg): save_setup -> text -> load_setup ->
    # merge_defaults -> validate, asserted zero-error, and the loaded
    # dict reproduces the scripted config EXACTLY (the headless half of
    # "Save Setup -> Load Setup on a fresh install reproduces the exact
    # configuration"; the button leg is this phase's own SETUP-07/08
    # work + the closing human checkpoint).
    from serpentrum import setup_logic
    setup = STATE['setup']
    text = setup_logic.save_setup(setup)
    loaded = setup_logic.load_setup(text)  # RAISES SetupError loudly
    merged = setup_logic.merge_defaults(loaded)
    errors, _warnings = setup_logic.validate(merged)
    assert errors == [], 'loaded setup validate errors: %r' % (errors,)
    assert loaded == setup, \
        'round-trip mismatch: %r != %r' % (loaded, setup)
    for key in ('box_preset', 'head_molecule', 'win_cap_molecules',
                'speed'):
        assert loaded[key] == setup[key], \
            'key %s round-tripped to %r (expected %r)' \
            % (key, loaded[key], setup[key])
    print('STAGE7 ROUNDTRIP keys=%d box=%s head=%s cap=%d speed=%.1f'
          % (len(loaded), loaded['box_preset'], loaded['head_molecule'],
             loaded['win_cap_molecules'], loaded['speed']), flush=True)


def s8_cleanup():
    # Stage 8 (hygiene leg): cleanup_srp deletes every srp_* object by
    # name pattern (srp_box + srp_head here = exactly 2) while the
    # stage-1 user-sentinel object SURVIVES untouched (smoke 04's
    # INFRA-04 / srp_-reservation assertion).
    from serpentrum import pymol_bridge
    n = pymol_bridge.cleanup_srp()
    assert n == 2, \
        'cleanup_srp removed %d, expected 2 (srp_box + srp_head)' % n
    names = cmd.get_names('public_objects')
    assert 'srp_box' not in names, 'srp_box survived cleanup_srp'
    assert 'srp_head' not in names, 'srp_head survived cleanup_srp'
    assert 'user_release_e2e' in names, \
        'user_release_e2e did not survive cleanup_srp'
    print('STAGE8 CLEANUP removed=2 user-sentinel-ok', flush=True)


_APP = None
for _name, _fn in [
    ('stage0_app', s0_app),
    ('stage1_setup_load', s1_setup_load),
    ('stage2_materialize', s2_materialize),
    ('stage3_scripted_win', s3_scripted_win),
    ('stage4_handoff_xyz', s4_handoff_xyz),
    ('stage5_spectra_tail', s5_spectra_tail),
    ('stage6_save_png', s6_save_png),
    ('stage7_setup_roundtrip', s7_setup_roundtrip),
    ('stage8_cleanup', s8_cleanup),
]:
    if not FAILURES:
        check(_name, _fn)

if FAILURES:
    print('SMOKE-END %d failure(s)' % len(FAILURES), flush=True)
else:
    print('SMOKE-OK RELEASE-E2E', flush=True)
