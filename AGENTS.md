# AGENTS.md


## Environment — the WSL/Windows split (read first)

This is the single most common way to break things. Both viewers run on Windows; development happens in WSL Ubuntu.

- **Dev shell is WSL Ubuntu.** Do NOT install anything, do NOT create conda envs, do NOT `pip install`. `python3.6` (3.6.9) is for syntax checks and unit tests ONLY. (`opencode.json` denies `pip*`, `apt*`, `conda*`, `rm*`.) `tclsh` (Tcl 8.5/8.6) is available for tcl syntax checks and `tcltest` pure-layer unit tests.
- **PyMOL 2.5.0 runs in a Windows conda env**, not WSL. Accessed via `setenv.bat`. Headless PyMOL CAN be run from WSL via `cmd.exe /c C:\\src\\run-conda-pymol.bat -cq <script>`. See `pymol/AGENTS.md` for the full staging + headless command.
- **WSL→Windows path guard applies to both viewers:** Windows PyMOL can't resolve `/mnt/c/...` (needs `C:\...` backslashes); Windows VMD can't resolve `/mnt/c/...` either (needs `C:/...` forward slashes). Each viewer has its own path-converter helper.

- A tested example script of running the windows xtb from WSL is in `test_wsl_winxtb.sh`. Note that the code may need to detect xtb/xtb.exe to support multiple OS.

## Code & UI standards (spec.md constraints)

- Code must be efficient, traceable, clean, and safe; the repo must be structured.
- UI must be simple and user-friendly, with clear but sufficient in-game explanation.

## Dependencies & attribution (spec.md constraints)

- **PyMOL:** Assume only what `pymol-open-source` ships (PyQt5 via `pymol.Qt`, numpy). Any additional Python lib must be user-approved. See `pymol/AGENTS.md`.
- Do NOT make up anything. ALL claims and citations (DOIs, PDB IDs, sources) MUST BE VERIFIED against a source and explicitly approved by a human. 

## GSD workflow (`.planning/`)

This repo uses the OpenCode "get-shit-done" workflow. `.planning/` is the source of truth for scope and state:
- `PROJECT.md` (what & why), `ROADMAP.md` (phase plan), `STATE.md` (current position), `REQUIREMENTS.md` (requirement IDs).
- `research/` — `STACK.md`, `ARCHITECTURE.md`, `PITFALLS.md`, `FEATURES.md`, `SUMMARY.md`. Read these before non-trivial viewer work; they encode verified API behavior and the pitfalls behind the viewer-specific AGENTS.md domain rules.
- `phases/<NN-name>/` — `NN-MM-PLAN.md`, `NN-MM-SUMMARY.md`, optional `RESEARCH.md` / `VERIFICATION.md` / `UAT.md`.
- Commit style: Conventional Commits with phase-plan scope, e.g. `feat(02-03):`, `docs(02-03):`, `test(02-01):`, `fix(02):`. Planning docs are committed (`commit_docs: true`).

## Parallel subagent execution (worktree/branch protocol)

When `/gsd-execute-phase` runs **≥2 plans in parallel** (one wave with
multiple autonomous plans), each `gsd-executor` subagent commits on a
**shared git index** — concurrent `git add`/`git commit` calls race and
sweep in each other's staged files. To eliminate this collision class:

- **One worktree per parallel plan.** Before spawning a wave, the
  orchestrator creates a git worktree (or branch) per parallel plan:
  `git worktree add tmp/exec-04-01 -b exec/04-01` (etc.). Each agent is
  spawned with `workdir=tmp/exec-04-01` so it commits on an isolated
  index — zero shared-index races.
- **Merge back in dependency order.** After all agents in the wave return,
  the orchestrator merges/fast-forwards each branch into the base in
  dependency order (`git merge exec/04-01`, then `exec/04-02`, ...). Real
  conflicts (same file touched by two plans — should be rare given
  disjoint `files_modified` frontmatter) are resolved explicitly here.
- **Single-plan waves skip this.** Waves with one plan (no parallelism)
  need no worktree — commit directly on the base branch. The protocol
  only applies when ≥2 plans run concurrently.
- **TDD multi-commit safety.** Each agent can still do atomic
  RED/GREEN/REFACTOR commits freely on its own branch — the per-task
  commit granularity is preserved (unlike an orchestrator-owned commit
  gate, which would collapse TDD's commit boundaries).

Orchestrators: if `parallelization: true` in `.planning/config.json` and a
wave has >1 plan, use this protocol. See `.planning/quick/001-*` for the
rationale + rejected alternatives (message-board lock, orchestrator commit
gate).

## serpentrum plugin gates & conventions (Phase 1)

Every future phase runs these gates before committing. Run them from the repo root in WSL.

- **Gates (WSL):**
  - `python3.6 tests/run_gates.py` — default gate: syntax walk + plugin-path safety + AST purity + scoped unittest discovery.
  - `python3.6 tests/run_gates.py --smoke` — headless Windows PyMOL smokes via `cmd.exe`. Verdict = flushed `SMOKE-OK` sentinels in output, NEVER exit codes (PyMOL swallows rc through the .bat).
  - `python3.6 tests/run_gates.py --xtb` — Windows xtb invoked from WSL: direct exec of the .exe, `/mnt/c`-backed cwd, bare relative args; asserts `normal termination` in output.
- **Smoke one-liner** (debugging a single smoke, no staging copy): `timeout 90 cmd.exe /c "C:\\src\\run-conda-pymol.bat -cq smoke\\01_skeleton_smoke.py"` from repo root.
- **Plugin-path safety (hard rules):** the dev install points PyMOL's plugin loader at the repo root → **NO `__init__.py`** in `tests/`, `smoke/`, or `tools/`; **NO top-level `*.py`** at the repo root. Either would be autoloaded as a plugin at GUI startup (enforced by `run_gates` gate 1).
- **Module identity:** the plugin loads as **`pmg_tk.startup.serpentrum`** — `pymol.plugins.startup` is only an attribute alias to the same module object. Smokes/asserts key on the `pmg_tk` name; live state anchors on `pmg_tk.startup._serpentrum` (never module globals — reload/double-import would duplicate them).
- **Modeless rule:** the main dialog opens via `.show()` only, never `.exec_()`; the AST purity checker fails any `.exec_()` until a later phase adds an explicit child-dialog allowlist.
- **Purity classes:** entry (`serpentrum/__init__.py`) lazy-imports pymol/pmg_tk inside functions only; GUI modules are an explicit allowlist in `tools/check_purity.py` (pymol.Qt only); everything else under `serpentrum/` is pure — zero pymol/Qt/numpy anywhere.
- **srp_ prefix reservation:** the `srp_` object-name prefix is RESERVED for game-generated PyMOL objects. Cleanup (`pymol_bridge.cleanup_srp`) deletes every `srp_*` object by name pattern — this works in a fresh process after `.pse` reload because it depends on no plugin state (INFRA-04). Users must not name their own objects `srp_*` (PyMOL has no undo — PITFALLS.md F17).

