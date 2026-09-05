# serpentrum

## What This Is

A PyMOL plugin implementing an educational snake game in which the snake is built by stacking real small molecules — an analogue of "self-assembly and spectra calculation". The player steers a molecular head around a bounded box to pick up small molecules that stack onto the snake using known stacking modes and intermolecular distances; the completed snake is then relaxed by xtb and its vibrational (IR) spectrum is calculated and plotted. For students and educators who want an engaging way to explore molecular interactions.

## Core Value

Playing snake by stacking real molecules with known stacking geometry, then seeing the IR spectrum of the molecule you assembled, computed end-to-end inside PyMOL via xtb.

## Requirements

### Validated

<!-- Shipped and confirmed valuable. -->

(None yet — ship to validate)

### Active

<!-- Current scope. Building toward these. -->

- [ ] Installable as a standard PyMOL plugin (Plugin Manager); dev/testing installs via plugin path
- [ ] Setup tab: demo-set dropdown or user upload of small molecules (≤3 rings); preset box sizes; head molecule choice (default random); xtb path + env resources (default auto-detect); snake win cap (molecule count, user-set, safe default, with warning when raised beyond safe atom budget)
- [ ] Bottom action row (6 buttons): Reset, Randomize, Save Setup, Load Setup, Cleanup model, Start
- [ ] Start jumps to Game tab, countdown 3-2-1, then gameplay begins
- [ ] Game tab: rolling info box, elapsed timer, molecules-remaining-before-win, pause/resume toggle, restart
- [ ] Gameplay in the OpenGL viewer: box boundary clearly displayed; head in sphere representation; pickups in stick representation; arrow-key steering
- [ ] Pickup stacks molecule onto snake using known stacking mode + known distance (mainly chain append); molecule and atom counts tracked (hidden, used to double-check the cap before xtb)
- [ ] Collision with boundary or snake stops further stacking (game over) but the snake is still "complete"; win when snake length exceeds the cap
- [ ] After completion: clear viewer, focus the snake, show snake length + total score (molecule count), activate "Get Spectra"
- [ ] Spectra tab: xtb optimization + hessian on the final snake; broadened IR spectrum plot (frequencies + intensities, Gaussian broadening); minimal plot adjustments (size, labels); save plot; calculation progress log
- [ ] Spectra tab: frequency table — clicking a row shows the vibrational vectors on the snake in the OpenGL viewer (no animation in v1)
- [ ] Demo molecule sets pre-downloaded with verified sources and documented attribution (DATA_SOURCES.md), with known stacking + intermolecular distances from a database
- [ ] Works in the established environment: WSL dev shell, Windows PyMOL 2.5.0, Windows xtb invoked from WSL (proven pipeline in test_wsl_winxtb.sh)

### Out of Scope

- "Generate and export" button — listed in the original spec's 7 buttons but undefined; dropped for v1 (6 buttons)
- Vibrational mode animation — spec explicitly defers (v1 shows static vectors only)
- Non-IR spectra (Raman, UV-Vis, NMR) — v1 is broadened IR from the xtb hessian
- Molecule sets with unknown stacking modes — only if research validates a fallback; requires user approval before inclusion
- External Python dependencies beyond pymol-open-source ships — any addition needs a written list, explicit user approval, and either user install or vendoring into `./3rd_party_lib/` (git-ignored, license noted)

## Context

- Sibling project AA-match established the GSD workflow patterns for PyMOL plugins in this environment (pure-module gates, headless smokes, module-identity rules); its AGENTS.md is prior art worth mirroring.
- `tmp/bioCHEMeleon` is the author's previous PyMOL game plugin — similar UI and mechanisms; code may be borrowed. `Pymol-script-repo` and `pymol-src` symlinks provide plugin and PyMOL 2.5.0 source references (git-ignored).
- `test_wsl_winxtb.sh` + `tmp/xtb_test/` contain a proven Windows-xtb-from-WSL run (phenol, `-o --hess`); xtb 6.7.1 is symlinked at `xtb-6.7.1` (Windows pre-release; 6.7.0 Windows build is missing a library).
- Code must detect `xtb` vs `xtb.exe` to support multiple OSes.
- README currently has placeholder sections; the vibe-coding warning block at the top must be preserved in any rewrite. (It also contains a leftover "sECDpent" name from another project — fix when README is rewritten.)
- All claims, citations, DOIs, PDB IDs, molecule sources MUST be verified against a source and explicitly approved by the human — no fabrication.
- Open design questions deferred to research: 2D plane vs 3D; movement/steering model (arrow-key mapping); speed behavior (constant vs increasing); stacking fallback for molecules without known stacking data.

## Constraints

- **Environment**: WSL Ubuntu dev shell; no installs, no conda envs, no pip. `python3.6` for syntax checks/unit tests only; `tclsh` available. PyMOL 2.5.0 runs in a Windows conda env (headless via `cmd.exe /c C:\src\run-conda-pymol.bat -cq <script>`); WSL→Windows path conversion required.
- **Dependencies**: only what `pymol-open-source` ships (PyQt5 via `pymol.Qt`, numpy); extra libs need written list + explicit user approval, vendored into `./3rd_party_lib/` with license noted.
- **Code quality**: efficient, traceable, clean, safe; structured repo.
- **UI**: simple, user-friendly, clear but sufficient in-game explanation.
- **Attribution**: all demo data cited with verified sources (DATA_SOURCES.md); nothing made up.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| 2D vs 3D, movement model, speed — deferred to research | Spec says "depends on research"; user wants research-informed choice with approval | — Pending |
| Stacking = known stacking mode + known distance, mainly chain append | Chemistry-faithful self-assembly analogue; unknown modes need research + user approval | — Pending |
| Broadened IR spectrum as the v1 spectra plot | User choice; xtb hessian provides frequencies + IR intensities | — Pending |
| Score = molecule count only | Simplest; directly mirrors the win condition | — Pending |
| Snake cap: user-set, safe default (~10 molecules / ~100 atoms), warning if exceeded | Hessian cost grows ~N³; atom guard runs before xtb | — Pending |
| Drop "Generate and export" button (v1 has 6 buttons) | Listed but undefined in spec; inherited from AA-match template | — Pending |
| Crashed snake still proceeds to spectra | Losing only stops further stacking; the current snake is still calculable | — Pending |
| Demo sets: ≤3 rings, known stacking, research proposes / user approves | Verified-source constraint; stacking data must come from a real database | — Pending |
| Spectra available on any completed snake (win or crash) | Keeps core value reachable in every run | — Pending |

---
*Last updated: 2026-09-06 after initialization*
