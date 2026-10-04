"""serpentrum/dialog_fit.py -- PURE placement math for the FIXED-SIZE
plugin dialog (debug session 06, round 3).

Round 2 froze the dialog's SIZE (min == max) but nothing ever set its
POSITION: Qt's default dialog placement centers the widget on its
PARENT (the PyMOL main window), and at the owner's ~92%-of-screen
dialog height that default landed the frame's BOTTOM edge below the
screen. Round 3 placement policy:

* at construction (pre-show): CENTER the widget rect on the
  available-geometry rect (screen minus taskbar), then CLAMP so the
  window FRAME (widget plus frame margins) fits inside the same rect;
* on the plot-preset refreeze (dialog already visible): clamp the
  CURRENT position under the NEW size with minimal shift -- a grown
  dialog must never bottom out, and the user's chosen placement is
  otherwise preserved;
* never via move/resize event handlers (debug session 06 closed that
  regression class in round 1) -- one-shot position computation at
  well-defined call points only.

Arithmetic on the owner's 200%-scaling machine (measured identities
in the debug file: 926 = 450*2+26, 1613 = 771*2+71, 1693 = 811*2+71;
available height 882 logical px at cap basis max(560, int(*0.92))
== 811; real frame margins left/right 6.5, top 29, bottom 6.5
LOGICAL px -- Windows sizes title bars in logical px, so the logical
margins are scale-invariant):

* cap regime (dialog 811 of 882): centered widget top = (882-811)//2
  = 35 >= the 29-logical top frame margin, so the frame top lands
  6 px INSIDE the screen; the clamp interval [32, 63] contains 35,
  so centering survives the clamp unchanged;
* 560-floor regime (avail < 609 and sizeHint taller than the cap):
  the 8%-of-avail headroom no longer guarantees 35 px per side --
  e.g. avail 608, dialog 560 centers at top 24, which would put the
  frame top 5 px ABOVE the avail top; the margin-aware clamp moves
  the widget down to 32 so the frame top sits 3 px inside;
* degenerate regime (avail shorter than size + margins, e.g. avail
  < 578 for a 560-tall dialog): NO fitting position exists at all;
  the clamp pins the frame TOP edge to the avail top (the title bar
  stays visible and grabbable) and lets the overflow ride on the
  bottom -- stock Windows oversized-dialog behavior, deterministic
  least-bad.

All inputs and outputs are LOGICAL px (Qt device-independent) plain
tuples: avail (ax, ay, aw, ah); size (w, h); margins (left, top,
right, bottom); positions (x, y). No Qt imports -- gui.py owns the
thin Qt call sites (py3.6).
"""

# Window frame-margin estimates in LOGICAL px, used only when the real
# native margins are unavailable (the construction-time clamp runs
# PRE-SHOW: windowHandle() is None until Qt creates the native window
# at show time). Based on the owner's 200% capture -- native top 58,
# sides 13, bottom 13 (= logical 29 / 6.5 / 6.5) -- and the fact that
# a 100%-scaled title bar measures the same ~29 logical px. The
# estimates round OUTWARD (32 top, 8 sides/bottom) so a fallback fit
# never undercounts the frame. MSWindowsFixedSizeDialogHint (round 3)
# removes the frame's sizing borders; the title bar remains, so the
# top margin stays the binding constraint.
FALLBACK_FRAME_MARGINS = (8, 32, 8, 8)  # (left, top, right, bottom)


def centered_top_left(avail, size):
    """Center the widget rect on the available rect -- the one-shot
    construction base; clamped_position adds the frame-fit guarantee.
    Integer floor division: Qt geometry is integral, so positions
    stay pixel-exact."""
    ax, ay, aw, ah = avail
    w, h = size
    return (ax + (aw - w) // 2, ay + (ah - h) // 2)


def clamped_position(avail, size, margins, current):
    """Clamp widget top-left CURRENT so the FRAME (widget rect grown
    by margins) fits inside the available rect with minimal shift.

    avail:    (ax, ay, aw, ah) available-geometry rect, logical px.
    size:     (w, h) the fixed widget size, logical px.
    margins:  (left, top, right, bottom) frame margins, logical px.
    current:  (x, y) desired widget top-left (either the centered
              construction base or the live position at refreeze).

    Per-axis policy: clamp into the closed interval
    [edge + margin, opposite_edge - size - margin]; if the interval
    is EMPTY (frame-augmented size exceeds the axis span) pin to the
    interval's LOWER bound -- the frame top/left edge sits at the
    avail edge, the title bar stays reachable, overflow rides on the
    bottom/right. Deterministic, no re-entrancy, no loops.
    """
    ax, ay, aw, ah = avail
    w, h = size
    ml, mt, mr, mb = margins
    x, y = current
    x = _axis_clamp(x, ax + ml, ax + aw - w - mr)
    y = _axis_clamp(y, ay + mt, ay + ah - h - mb)
    return (x, y)


def _axis_clamp(value, lo, hi):
    """Clamp VALUE into [lo, hi]; when the interval is empty there is
    no frame-fitting position on this axis at all -- pin to lo (title
    bar / left edge stays visible) instead of splitting the error."""
    if lo > hi:
        return lo
    if value < lo:
        return lo
    if value > hi:
        return hi
    return value
