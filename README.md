> This is a vibe-coding project. While the human attempt to verify the source of all 
> contents, if you find any issues please contact me.
> 
> !! v1.0 - vibe-coded, review before production/teaching use !!

# serpentrum

Classical snake game in (bio-) molecular viewer stacking molecules,  as an analogue of "self-assembly and spectra calculation".
For students and educators who want an engaging way to explore and study molecular interactions.

---

## Requirements

External binary (for the semi-empirical IR calculation):
- **xtb** (the only external binary): https://github.com/grimme-lab/xtb
  For Windows users: tested with the xtb-6.7.1pre-windows-x86_64 build; the 6.7.0 Windows build is missing a library.

For the viewer and UI:
- **PyMOL 2.5.0** (anaconda build or equivalent)
- PyQt5 (bundled with PyMOL's Qt GUI via pymol.Qt - no extra install)
- numpy (PyMOL build dependency - no extra install)

> No external Python dependencies beyond what PyMOL already ships. If any are introduced later, they will be listed for explicit user approval and either user-installed or vendored into the git-ignored 3rd_party_lib/ directory with their license noted.

## Install

Install via PyMOL's Plugin Manager (universal across Windows/Linux/macOS):

1. In PyMOL: Plugin -> Plugin Manager -> Add plugin directory, then select the repo root (the directory containing the serpentrum/ package with its __init__.py).
2. restart PyMOL OR re-add the plugin directory in Plugin Manager.
3. A single **serpentrum** item appears under the Plugin menu; clicking it opens the 3-tab dialog (Setup / Game / Spectra).

Release alternative (no checkout needed): zip -r serpentrum.zip serpentrum/, then Plugin Manager -> Install from local file and pick the zip.

## Usage

1. **Setup tab** - choose the demo set (head options fill in; Random picks from the set), box preset, head molecule, xtb path (or auto-detect), win cap, and speed tier.
   Canonical values: speed tiers 3.0 / 6.0 (default) / 7.5 / 9.0 A/s; box presets 35 / 55 / 85 A half-widths (medium default); win cap default 10 (range 1-20); atom budget 100 atoms; broadening 16.0 cm-1 FWHM. Past the atom budget, a hessian-cost warning applies: a ~100-atom snake takes about 1-2 min on a typical 4-core/8-thread laptop (measured 84-101 s; thread-capped runs slower, up to ~5 min single-threaded).
2. **Start** - Start applies the setup and materializes the box and head first, then a 3-2-1 countdown runs and the dialog switches to the Game tab.
3. Steer with the 4 arrow keys. If the keys seem dead, click the 3D viewer first; when the dialog takes focus the game auto-pauses.
4. Completion (win or crash) enables **Get Spectra**.
5. **Get Spectra** - the xtb run streams into the live log on the Spectra tab (with Cancel / Run again); the plot follows with y unit / color / x direction / invert / size presets; **Save Plot (PNG)** writes the figure; clicking a table row draws that vibration's mode vectors on the optimized structure.

Spectra artifacts default to srp_spectra under the current working directory (SRP_SPECTRA_DIR env override). The **Cleanup** button removes only the srp_* PyMOL objects created by the game (name-pattern based; do not name your own objects srp_*).

## Demo Molecules set

TBD

Full attribution in `DATA_SOURCES.md`.

## Project Structure

```
#TBD
```

## License

BSD 3-Clause — see [LICENSE](LICENSE).

## Acknowledgements

Demo data courtesy of `TBD`

---
