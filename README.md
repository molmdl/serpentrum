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

Demo Set A ("Aromatic pi-stack") ships five PubChem 3D-conformer SDF records (public domain, US Government / NCBI):

- Benzene (CID 241, C6H6, 12 atoms)
- Naphthalene (CID 931, C10H8, 18 atoms)
- Anthracene (CID 8418, C14H10, 24 atoms)
- Phenanthrene (CID 995, C14H10, 24 atoms)
- Biphenyl (CID 7095, C12H10, 22 atoms)

Picked-up molecules stack parallel-displaced: a 3.383 A plane gap plus a 1.231 A lateral offset, composing a 3.60 A centroid-centroid distance at 20.0 deg off-normal. Idealized pairwise geometry - neat Set A crystals are herringbone (see DATA_SOURCES.md). The [JAN2000] rule source is a crystalline corpus - pi-stacking in metal complexes with aromatic nitrogen-containing ligands - so the geometry carries a crystalline-state framing. Biphenyl is non-planar in its ground state: its orthogonal rings clash at the set geometry and the placement is refused - the designed "no invented chemistry" demonstrator.

Full source database / ID / DOI / license per molecule: `serpentrum/data/DATA_SOURCES.md` - the attribution document of record, whose approval is decided at the v1.0 release gate.

## Project Structure

- `serpentrum/` - the plugin package: entry `serpentrum/__init__.py`; GUI (gui.py, gui_setup.py, gui_game.py, gui_spectra.py, gui_plot.py); PyMOL bridge (pymol_bridge.py, input.py); pure core (everything else - zero pymol/Qt/numpy imports).
- `serpentrum/data/` - demo SDFs, `serpentrum/data/manifest.json`, `serpentrum/data/stacking_pi_stack.json`, and `serpentrum/data/DATA_SOURCES.md`.
- `tests/` - WSL unit tests and the gate runner (`tests/run_gates.py`).
- `smoke/` - headless Windows PyMOL smoke scripts.
- `tools/` - repo-side check and build scripts.

## License

BSD 3-Clause - see [LICENSE](LICENSE).

## Acknowledgements

- Molecule geometries: PubChem 3D-conformer records (public domain, US Government / NCBI; acknowledgment requested).
- Stacking geometry basis: Janiak 2000 (DOI 10.1039/b003010o) and measured Crystallography Open Database entries 4003564, 2100607, and 2100608 - cited, never redistributed.
- Full citations, verification status, and licenses: `serpentrum/data/DATA_SOURCES.md`.

---
