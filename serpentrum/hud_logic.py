"""serpentrum.hud_logic -- pure display helpers for the Game tab HUD (plan 04-02).

PURE module: stdlib only (no pymol / pmg_tk / PyQt5 / numpy --
check_purity auto-classifies PURE). The wall clock lives in the GUI
(game_engine has NO wall-clock by design, 04-RESEARCH-gameloop.md
Q5/S3); only the formatting lives here, so GAME-07's elapsed timer and
molecules-remaining label math stay WSL-testable while the widgets stay
human-verify-only (01-05).

python3.6 syntax (%-formatting).
"""


def format_elapsed(seconds):
    """Render elapsed seconds as 'M:SS' (minutes not zero-padded,
    seconds zero-padded to 2).

    Fractional seconds are FLOORED (75.9 -> '1:15', never '1:16') via
    int(); negatives are clamped to 0 first (a tick landing before
    start_time must never render negative -- PITFALLS.md 9.3 style).
    """
    if seconds < 0.0:
        seconds = 0.0
    total = int(seconds)
    return '%d:%02d' % (total // 60, total % 60)


def remaining_text(value):
    """Render the molecules-remaining label (GAME-07).

    'Remaining: N' for a concrete count; 'Remaining: -' when the cap is
    None (remaining unknown -- Phase 4 never hits this with the default
    setups, but the engine allows cap=None).
    """
    if value is None:
        return 'Remaining: -'
    return 'Remaining: %d' % value
