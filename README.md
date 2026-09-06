> This is a vibe-coding project. While the human attempt to verify the source of all 
> contents, if you find any issues please contact me.
> 
> !! Under Development !!

# serpentrum

Classical snake game in (bio-) molecular viewer stacking molecules,  as an analogue of "self-assembly and spectra calculation".
For students and educators who want an engaging way to explore and study molecular interactions.

---

## Requirements

For the semi-empirical calculation to get the spectrum, download the right format of xtb, xtb4stda, std2 for your OS:
- **xtb**: https://github.com/grimme-lab/xtb (for Windows user: tested with `xtb-6.7.1pre-windows-x86_64.zip`. the 6.7.0 version is missing a library.)

For the viewer and UI:
- **PyMOL 2.5.0** (anaconda build or equivalent)
- PyQt5 (bundled with PyMOL's Qt GUI — no extra install)
- numpy (PyMOL build dependency — no extra install)

> No external Python dependencies beyond what PyMOL already ships. If any are introduced later, they will be listed for explicit user approval and either user-installed or vendored into `./3rd_party_lib/` (git-ignored) with their license noted.

## Install

Install via PyMOL's **Plugin Manager** (universal across Windows/Linux/macOS):

1. In PyMOL: `Plugin → Plugin Manager → Install New Plugin`
2. Point the file picker at the `serpentrum/` package directory
3. The plugin registers a **serpentrum** item under the Plugins menu

## Usage

> TBD

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
