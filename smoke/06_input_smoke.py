"""Headless Windows PyMOL input-wizard smoke — 04-04.

Run (from repo root; cwd is /mnt/c-backed so cmd.exe inherits C:\\ cwd):
    timeout 90 cmd.exe /c "C:\\src\\run-conda-pymol.bat -cq smoke\\06_input_smoke.py"

Exit codes through the .bat are ALWAYS 0 (even after a Qt C-abort) —
verdicts are flushed sentinels grepped by tests/run_gates.py --smoke:
    SMOKE-OK INPUT-WIZARD   all steps passed
    SMOKE-FAIL <step>: ...  a step failed (one line per failure)

Machine-proves the INPUT SPIKE's primary mechanism headlessly — every
claim from the research's headless-proven set W1-W6
(04-RESEARCH-input.md, 2026-09-12):
  mask         get_event_mask() == 12 (event_mask_key + event_mask_special)
               — MANDATORY; the base returns pick+select=3 and do_special
               never fires without event_mask_special (W1/pitfall 2)
  dispatch     do_special(100..103) -> 'left'/'up'/'right'/'down' IN ORDER,
               directly callable headless (W3/W6, 2026-09-12 probe)
  unmapped     unknown code still grabs (returns True) and no-ops
  lifecycle    install / set_active / teardown round-trips: idempotent
               install (no double-install), grab-but-no-op pause gate,
               prior-wizard save/restore (W5, bioCHEMeleon pattern)
  no leak      cmd.key_mappings for 'up'/'down' stays None after the full
               lifecycle (S5: the wizard route NEVER mutates the global
               key_mappings; the probe's DEFAULTS_BEFORE showed both None)

NOT proven here (headless has no key events): the LIVE C PyMOL_Special
dispatch on a real keypress (W7) — that is the plan 04-07 human-verify.

Template rules (copied verbatim from smoke/01_skeleton_smoke.py):
  - every print carries flush=True (stdout is block-buffered when piped)
  - NO widget construction (headless C-abort is uncatchable)
  - never add smoke/__init__.py (findPlugins plugin-path safety)
  - NEVER trust __file__ under -cq (resolve ROOT by validating
    serpentrum/__init__.py candidates)
  - verdict = flushed SMOKE-OK/SMOKE-FAIL sentinels ONLY (never exit codes)
"""
import os
import sys


def _resolve_root():
    """Repo root, defensively.

    Under -cq exec, __file__ is PyMOL's launcher module (NOT this script),
    so naive dirname(dirname(__file__)) lands in site-packages. Validate
    every candidate by the presence of serpentrum/__init__.py. Copied
    verbatim from smoke/01_skeleton_smoke.py.
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
from pymol.wizard import Wizard  # noqa: E402
from serpentrum import input as srp_input  # noqa: E402

FAILURES = []

# Shared across steps: do_special forwards direction NAMES here in order.
COLLECTOR = []


def check(name, fn):
    try:
        fn()
        print('SMOKE-STEP OK  %s' % name, flush=True)
    except Exception as exc:
        print('SMOKE-FAIL %s: %r' % (name, exc), flush=True)
        FAILURES.append(name)


def s_build():
    """W1: wizard constructs; event mask is EXACTLY 12 (key + special)."""
    wiz = srp_input.KeySteerWizard(COLLECTOR.append)
    assert wiz.get_event_mask() == 12, \
        'mask %r, expected 12' % wiz.get_event_mask()
    assert wiz.get_event_mask() == (Wizard.event_mask_key +
                                    Wizard.event_mask_special)


def s_do_special_dispatch():
    """W3/W6: do_special(100..103) forwards IN ORDER; True (grab) each."""
    wiz = srp_input.KeySteerWizard(COLLECTOR.append)
    del COLLECTOR[:]
    for code, name in ((100, 'left'), (101, 'up'), (102, 'right'),
                       (103, 'down')):
        grabbed = wiz.do_special(code, 0, 0, 0)
        assert grabbed is True, '%s did not grab' % name
    assert COLLECTOR == ['left', 'up', 'right', 'down'], \
        'dispatch order wrong: %r' % (COLLECTOR,)


def s_unmapped_code():
    """Pitfall 7: unmapped code (F1=1) still grabs, forwards NOTHING."""
    wiz = srp_input.KeySteerWizard(COLLECTOR.append)
    del COLLECTOR[:]
    grabbed = wiz.do_special(1, 0, 0, 0)
    assert grabbed is True, 'unmapped code did not grab'
    assert COLLECTOR == [], 'unmapped code steered: %r' % (COLLECTOR,)


def s_install():
    """W5: install activates our wizard; second install is idempotent."""
    prior = srp_input.install(COLLECTOR.append)
    assert isinstance(cmd.get_wizard(), srp_input.KeySteerWizard), \
        'wizard not installed: %r' % (cmd.get_wizard(),)
    prior2 = srp_input.install(COLLECTOR.append)
    assert prior2 == prior, \
        're-install returned %r, expected %r (idempotent)' % (prior2, prior)
    assert isinstance(cmd.get_wizard(), srp_input.KeySteerWizard), \
        'double-install displaced our wizard'


def s_set_active():
    """Pause gate: set_active(False) grabs-but-no-ops; True steers again."""
    srp_input.set_active(False)
    n0 = len(COLLECTOR)
    grabbed = cmd.get_wizard().do_special(102, 0, 0, 0)
    assert grabbed is True, 'paused key did not grab'
    assert len(COLLECTOR) == n0, 'paused key steered'
    srp_input.set_active(True)
    cmd.get_wizard().do_special(102, 0, 0, 0)
    assert len(COLLECTOR) == n0 + 1, 'resumed key did not steer'


def s_teardown():
    """W5: teardown clears our wizard; idempotent; opaque handle accepted."""
    srp_input.teardown()
    assert cmd.get_wizard() is None, \
        'wizard not cleared: %r' % (cmd.get_wizard(),)
    srp_input.teardown()  # second call: no exception
    srp_input.teardown(handle='opaque')  # route-swap uniformity contract


def s_prior_restore():
    """W5 round-trip: install returns the displaced prior; teardown
    restores it (the bioCHEMeleon save/restore pattern)."""
    pw = Wizard()
    cmd.set_wizard(pw)
    ours = srp_input.install(COLLECTOR.append)
    assert ours is pw, \
        'install returned %r, expected the displaced prior' % (ours,)
    srp_input.teardown()
    assert cmd.get_wizard() is pw, \
        'prior wizard not restored: %r' % (cmd.get_wizard(),)
    cmd.set_wizard()


def s_no_key_leak():
    """S5: after the full lifecycle, global key_mappings for up/down are
    untouched (None by default per the probe's DEFAULTS_BEFORE) — the
    wizard route never mutates cmd.key_mappings."""
    assert cmd.key_mappings.get('up') is None, \
        "key_mappings['up'] leaked: %r" % cmd.key_mappings.get('up')
    assert cmd.key_mappings.get('down') is None, \
        "key_mappings['down'] leaked: %r" % cmd.key_mappings.get('down')


for _name, _fn in [
    ('build', s_build),
    ('do_special_dispatch', s_do_special_dispatch),
    ('unmapped_code', s_unmapped_code),
    ('install', s_install),
    ('set_active', s_set_active),
    ('teardown', s_teardown),
    ('prior_restore', s_prior_restore),
    ('no_key_leak', s_no_key_leak),
]:
    check(_name, _fn)

if FAILURES:
    print('SMOKE-END %d failure(s)' % len(FAILURES), flush=True)
else:
    print('SMOKE-OK INPUT-WIZARD', flush=True)
