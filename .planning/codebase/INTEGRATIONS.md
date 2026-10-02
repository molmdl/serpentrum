# External Integrations

**Analysis Date:** 2026-10-02

> **Scope note:** serpentrum has **no network integrations at runtime**. There is no database, no authentication provider, no HTTP client, no webhook, no cloud service, and no telemetry. Its "integrations" are local *external processes* (a Windows xtb executable and the Windows PyMOL host) plus data files whose provenance was verified offline during research. This document records those explicitly and states the absences rather than inventing services.

## APIs & External Services

**None at runtime.** No `requests`, `urllib`, `http`, `socket`, SDK, or API-key usage appears anywhere in `serpentrum/` (verified by import grep — PURE modules are stdlib-only and import no network package). `opencode.json` gates `curl *`/`wget *` to "ask", but nothing in the shipped plugin calls them.

**Data-provenance sources (data-prep / research time only, not runtime code):**
- **PubChem PUG REST API** — `https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{CID}/SDF?record_type=3d` was used to fetch the five Demo Set A 3D SDFs. The fetched files are **committed** in `serpentrum/data/` (`benzene.sdf`, `naphthalene.sdf`, `anthracene.sdf`, `phenanthrene.sdf`, `biphenyl.sdf`); the plugin never fetches them again. Attribution/license/verification status is tracked in `serpentrum/data/DATA_SOURCES.md`, whose status line is currently **DRAFT — NOT APPROVED** (approval is a v1.0 release gate, DATA-02). Auth: none (public API). CIDs: benzene 241, naphthalene 931, anthracene 8418, phenanthrene 995, biphenyl 7095.
- **Crystallography Open Database (COD)** — measured π-stack distances (entries 4003564, 2100607, 2100608) were read from `https://www.crystallography.net/cod/*.cif` during research; **no CIF is redistributed**. Recorded in `DATA_SOURCES.md`.
- **OpenAlex / DOI records** — used to verify citations (`10.1039/b003010o` Janiak 2000, `10.1021/acs.chemmater.0c01184`, `10.1107/S0108768106026814`). Citations are stored as data in `serpentrum/data/stacking_pi_stack.json` (`citations` map) and are **not** fetched at runtime.

## Data Storage

**Databases:**
- None. No SQL/NoSQL client, no ORM, no connection string. Game state is in-memory dicts anchored on `pmg_tk.startup._serpentrum` (`serpentrum/__init__.py:20-81`).

**File Storage (local filesystem only):**
- **Shipped read-only data** — `serpentrum/data/`:
  - `manifest.json` — Demo Set A molecule metadata (5 molecules: id, name, file, `source_db`, `source_id`, `atom_count`, `charge`, `ring_count`, `ring_atoms`); loaded by `serpentrum/molecule_data.py`.
  - `stacking_pi_stack.json` — the π-stack interaction dataset (mode, `distance_a` 3.383, `lateral_offset_a` 1.231, citation key, `status: APPROVED`); loaded by `serpentrum/molecule_data.py`.
  - The five PubChem SDF geometry files. Gameplay spawn/head pools exclude biphenyl per quick task 001 (its geometry is refused as a demonstrator), while the file remains shipped.
  - `DATA_SOURCES.md` — attribution and approval-status ledger (still DRAFT — NOT APPROVED).
- **Generated xtb artifacts (kept)** — written to `<SRP_SPECTRA_DIR or cwd>/srp_spectra/<snake_id>/`: `g98.out`, `vibspectrum`, `xtbopt.xyz`, `snake.xyz`, `xtb.log` (`serpentrum/xtb_runner.py:298-325`). Keep-until-replaced policy; git-ignored. Live examples present at `srp_spectra/run_1/` and `srp_spectra/run_4/`.
- **Scratch xtb spray dir** — a fresh per-run `tempfile.mkdtemp(prefix='srp_', dir=base_dir)` (`serpentrum/xtbenv.py`), into which `snake.xyz` is written and xtb sprays ~10 files; deleted on the terminal branch (`serpentrum/xtb_runner.py`).
- **Test fixtures** — `tests/fixtures/molfile/*` (SDF/MOL2), `tests/fixtures/xtb/*` (real captured xtb outputs: `g98.out`, `vibspectrum`, `.err`/`.log`, `xtbopt.xyz`), `tests/fixtures/calib_snake_{52,104}.xyz`, plus `.planning/research/xtb-spike-fixtures/` (dimer/ohess/hessian captures).

**Caching:**
- None (no cache service). `.gitignore` lists `cache`/`**/cache/**` but no caching code exists.

## External Processes (the real integrations)

### 1. xtb executable (`xtb.exe` / `xtb`) — semi-empirical QM run

- **What it is:** external Windows/Linux binary, not a Python package. v1.0/**6.7.1pre** (Windows x86_64 zip per `README.md`). Release 6.7.0 is noted as missing a library.
- **Invocation (plugin runtime):** `QtCore.QProcess` launched with a **list argv** built by `serpentrum/xtbenv.build_argv` — never a shell string. Base args `[exe, 'snake.xyz']` plus `--ohess` and the calibrated `('-P', '4')` thread cap (`serpentrum/xtb_run.py:81`). `--ohess` is locked as a one-word constant `XTB_OHESS` (`serpentrum/xtbenv.py:34`); `-o --hess` is explicitly forbidden (silently skips the Hessian).
- **Working-directory contract:** `cwd` = a fresh `srp_*` temp dir; input filename is a bare relative name. This means **no WSL↔Windows path translation ever happens at plugin runtime** (`serpentrum/xtbenv.py`; `tools/winpath.py` docstring).
- **Binary resolution order:** configured path (validated) → `which('xtb.exe')` → `which('xtb')` → `None` (`serpentrum/xtbenv.py:141-167`). Optional env seam `SRP_XTB_PATH` (used by smokes/dev).
- **Success contract (3 legs):** exit code `0` **AND** stderr contains `normal termination` (checked *after* rejecting `abnormal termination`, which contains it as a substring) **AND** expected files `g98.out` + `vibspectrum` present (`serpentrum/xtbenv.evaluate_run:51-110`).
- **Consumers:** controller `serpentrum/xtb_runner.py` (`XtbRunController`, QProcess, signals only, no polling); output parser `serpentrum/spectra.py` (g98 core) and `serpentrum/plot_logic.py`; UI `serpentrum/gui_spectra.py`, plot widget `serpentrum/gui_plot.py`. xtb is also invoked directly from tests/gates: `tests/run_gates.py:205-278` (`--xtb` gate), `tools/measure_calib_qprocess.py`, `test_wsl_winxtb.sh`.

### 2. Windows PyMOL host + `cmd.exe` bridge (dev/test only)

- **Production runtime:** the plugin *is* a PyMOL plugin; it uses the in-process `pymol.cmd` and `pymol.wizard` APIs (`serpentrum/pymol_bridge.py`, `serpentrum/input.py`) — not an external process.
- **Dev/test bridge:** headless Windows PyMOL is driven from WSL by invoking `cmd.exe /c C:\src\run-conda-pymol.bat -cq <script>`. The `.bat` and `setenv.bat` are **external** to this repo (`C:\src\`); only the invocations are in-repo. Implemented in `tests/run_gates.py` (`run_smoke`, `SMOKE_BAT` at line 78, 90 s timeout) and documented per-script in each `smoke/NN_*.py` header. Smoke verdicts come from flushed `SMOKE-OK` sentinels, never from the `.bat` exit code (always 0).
- **WSL→Windows path conversion:** `tools/winpath.py` (dev/harness only) — `to_windows_path('/mnt/c/x') → 'C:/x'`, `to_windows_backslash('/mnt/c/x') → 'C:\x'`; strict validation, raises on non-mount paths. Exercised by `tests/run_gates.py` and `tests/test_winpath.py`.

## Authentication & Identity

**Auth Provider:**
- None. No login, OAuth, token, or identity concept exists in the plugin.

## Monitoring & Observability

**Error Tracking:**
- None. No Sentry/Rollbar/etc. Errors surface as Qt status labels/log lines or the `RunVerdict.problems` strings (`serpentrum/xtbenv.py`).

**Logs:**
- In-app only: the Spectra tab displays xtb stdout+stderr streamed via `QProcess` signals; a bounded 500-line tail (`_LOG_TAIL`, `serpentrum/xtb_runner.py:45`) is persisted to `xtb.log` in the kept run dir.
- Opt-in debug tracing to the PyMOL log via `SRP_DEBUG=1` (`serpentrum/hud_logic.py`, `serpentrum/gui_game.py`).

## CI/CD & Deployment

**Hosting:**
- None (a desktop PyMOL plugin). Distribution is via PyMOL's Plugin Manager pointing at the `serpentrum/` package directory, or a dev install by adding the repo path (`README.md:27-34`, `spec.md:13`). Release alternative: zip the `serpentrum/` package and install via Plugin Manager.

**CI Pipeline:**
- None detected (no `.github/`, `.gitlab-ci.yml`, or CI config). The equivalent is the local gate runner `python3.6 tests/run_gates.py` (`--smoke`, `--xtb` flags), run manually from the WSL repo root.

## Environment Configuration

**Required env vars (all optional; sensible fallbacks):**
- `SRP_XTB_PATH` — explicit xtb executable (probed first; falls back to PATH detection).
- `SRP_SPECTRA_DIR` — kept-spectra root; default `<cwd>/srp_spectra`.
- `SRP_DEBUG=1` — enable live debug traces.
- `OMP_NUM_THREADS`, `MKL_NUM_THREADS`, `OMP_STACKSIZE` — the only xtb env knobs accepted; defaults to no overrides (`serpentrum/xtb_run.py:88`).
- Windows-side: none codified in-repo (secrets/env are external).

**Secrets location:**
- None. No credentials, API keys, or tokens are used or stored. `.gitignore` nonetheless excludes `*.env`, `**/secrets.toml`, `**/auth.json`.

## Webhooks & Callbacks

**Incoming:**
- None.

**Outgoing:**
- None. Everything is local process invocation and local file I/O.

---

*Integration audit: 2026-10-02*
