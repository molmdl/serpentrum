---
status: open
trigger: "GATE V 2026-10-04 re-test: plugin dialog flickers while being moved; during resize the top of the window escapes above the scene"
created: 2026-10-04T00:00:00Z
updated: 2026-10-04T00:00:00Z
---

## Current Focus

OPEN, authorized 2026-10-04 to run IN PARALLEL with the paused GATE V (owner directive). NOT a release blocker: owner verdict at GATE V round = B13 PASS ("height is ok"); quirk is cosmetic. Default disposition if unfixed by close: C10-DEFERRED (07-10 round-2 precedent — approved with visible benign cosmetic noise).

## Symptoms

expected: moving the plugin dialog is flicker-free; resizing keeps the window within sane screen bounds.
actual: (1) the window "keep[s] blinking" while it is being moved; (2) when resizing (top edge), "the top of window go above the scene".
errors: none — console shows only the pre-existing known families (QWindowsWindow::setGeometry DPI warning on first show, 07-10 r2 (d) DEFERRED; Selector-Error srp_mode_vec lines, 07-10 DEFERRED). No traceback, no new log lines.
reproduction: real Windows PyMOL 2.5.0 (conda), plugin loaded from repo root @ 75cd278, open the serpentrum dialog, drag the window by its title bar; drag the top resize handle upward.
started: 2026-10-04, GATE V live re-test after the 08-12/08-13 insertion commits (the two added Setup rows + tooltips are the newest layout deltas; correlation unproven).

## Eliminated

- NOT the dialog-too-tall class — fixed at 07-10 r1 (e91c7ad: log 110 / table 150 caps + screen-height cap); the owner confirms height is OK at the current content.
- NOT a Python/log error — console clean of anything new during the quirk.
- NOT headless-probeable — offscreen dialog construction is a DEAD END in this Qt build (01-05); GUI verdicts are human-verify only. The debug loop is: agent analyzes/patches, OWNER eyeballs live.

## Evidence

- timestamp: 2026-10-04
  checked: owner live test (GATE V round)
  found: verbatim "height is ok tho when i move window keep blinking, and until i try to resize the top of window go above the scene"; first observed after 08-12 Performance rows (53dd655) + 08-13 tooltips (f6a3dc5) landed; the dialog cap machinery itself ships since e91c7ad (2026-09-27).
  implication: regression window is 2026-09-27..2026-10-04 IF the quirk is new, but owner may simply not have moved/resized the window before — establish recency first (ask owner: did this happen before this week?).

- timestamp: 2026-10-04
  checked: the suspect constraint machinery (source, unverified hypothesis)
  found: gui.py PluginDialog applies the 07-10 screen cap: setMaximumHeight(max(560, int(avail.height() * 0.92))) alongside setMinimumWidth(450); child scroll/cap widgets (SpectraTab log 110 / table 150) resize within.
  implication: a TOP-EDGE resize changes y AND height simultaneously; with a max-height constraint active, Qt's geometry negotiation can visibly fight (repeated clamp -> flicker) and the top edge can transiently sit above the clamped envelope — matches "top goes above the scene".

- timestamp: 2026-10-04
  checked: repaint-storm alternative (unverified)
  found: moving a window normally does not repaint children; but a per-tick HUD/QTimer path (GameTab) or the plot widget's paintEvent could churn IF something drives updates during move.
  implication: cheap discriminator — see Repro discriminators (b); only pursue if the constraint hypothesis fails.

- timestamp: 2026-10-04
  checked: environment constants
  found: Windows 10 / Intel Iris OpenGL 4.6 / 8 cores; PyMOL 2.5.0 conda; the plugin dialog is a Qt child of the PyMOL main window (pmg_tk startup module identity).

## Repro discriminators (owner A/B, ~2 min each — run these first, they halve the hypothesis space)

a. Resize from the BOTTOM edge only. QUIET bottom + flickering top => top-edge/max-height negotiation is causal (supports C2, skip C4).
b. Flicker while moving on the GAME tab (no plot) vs SPECTRA tab (plot visible). Tab-dependent => paint churn (C4); tab-independent => constraint/window-manager (C2/C5).
c. Scratch build with the setMaximumHeight cap temporarily disabled: quirk gone => constraint machinery causal; quirk stays => Windows/Qt window-manager interplay (C5) or repaint churn (C4).

## Candidates

- C1: DEFER as a C10 cosmetic disposition at GATE V close (07-10 round-2 precedent). Ship-blocker: NO.
- C2: enforce the screen cap in a resizeEvent override (clamp during the event) instead of setMaximumHeight — quieter negotiation; MUST preserve the 07-10 approved look byte-visually (caps live, no layout change).
- C3: map the exact Qt warning emission during a move (capture stderr live, not just at first show) — decides whether this joins the DEFERRED DPI-warning family.
- C4: repaint-storm fix (widget flags) — ONLY if discriminator (b) is tab-dependent; verify flags empirically, do NOT assert from memory.
- C5: Windows display-scaling interplay — capture the scaling factor + the exact geometry values Qt reports during the quirk (owner paste), analyze setGeometry call sites.

## Constraints for the fixing agent

- NEVER regress the 07-10 approved dialog contract (log 110 / table 150 caps, screen-height cap, 6-button row fit, setMinimumWidth(450)).
- Modeless discipline: NO .exec_() anywhere; AST purity gate must stay green.
- Any candidate fix = gates green (`python3.6 tests/run_gates.py`) + OWNER live eyeball (GUI verdicts human-verify only) + amendment protocol record if landed during GATE V; otherwise post-release quick task.
- If root cause proves to be deep Windows/Qt behavior with no quiet fix: recommend C1 defer with the evidence recorded, do NOT force a risky fix.
