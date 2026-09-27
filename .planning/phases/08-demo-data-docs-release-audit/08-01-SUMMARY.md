---
phase: 08-demo-data-docs-release-audit
plan: 01
type: execute
wave: 1
status: complete
date: 2026-09-28
gate: D
role: GATE D decision record — the phase's only checkpoint:decision
---

# 08-01 — GATE D Decision Record (consolidated)

**Date:** 2026-09-28 (UTC)
**Format:** one numbered sheet, four items + confirm-or-amend; answered by the owner in two rounds (round 1 answered items 1–4 with a verification request; round 2 confirmed item 1 as c-staleness after a code investigation).

## Verbatim owner answers

**Round 1 (2026-09-28):**
> "1=b-full, 2=b-two-tier, 3=amend, 4=confirm-all
> but im not sure, double chek: can the head be actually randomized at the moment or its current fixed to be benzene? i also found no more options other than random in the demo set? I remember used to have like 5-6 options other than random? this maybe a bug or changed decision there?"

**Round 2 (2026-09-28, after the code investigation below):**
> "arent u going to remove apply, and its confusing to only show after apply. suppose after choosing the demo set the options should be there.
> 1=c-staleness for item 1"

## Investigation facts (code-verified, presented to owner before round 2)

- `randomize_head` exists (setup_logic.py:357-369, seeded, unit-tested) but has ZERO production call sites — head randomization was never wired.
- `pymol_bridge.py:255-256`: `if head_id == 'random': return records[0]` — deterministic; records[0] of set_a = benzene (CID 241, manifest order: benzene, naphthalene, anthracene, phenanthrene, biphenyl).
- Head combo items: fresh dialog = "Random" ONLY; after any successful Apply = "Random" + the 5 molecule names (6 items) via `_populate_head_combo` (gui_setup.py:451-474, called from _on_apply :580-581). Never was richer (git: a899958 03-07 built it this way; nothing removed). Plan-conformant, not a defect.
- The Apply status line "head will be randomized at game start" (gui_setup.py:627-628) is FACTUALLY FALSE today (deterministic benzene).
- Owner's "5-6 options" memory = the post-Apply head combo (Random + 5 molecules).

## Contract mapping (chosen option → exact contract the consuming plan implements)

### (1) Randomize scope — CHOSEN: `d1-option-c-staleness`

- **08-05 implements:** `randomize_setup(setup, candidates, seed=None)` writes CONCRETE values for ALL of: `head_molecule` (via existing `randomize_head` seam, from candidates), `box_preset` (from BOX_PRESETS), `win_cap_molecules` (validate-legal range), `speed` (a SPEED_TIERS value), `broadening_fwhm` (validate-legal range). Consent key NEVER touched. Seed-deterministic (private random.Random).
- **08-09 owes the staleness text fix:** the Apply/Start success status clause "head will be randomized at game start" must be corrected — the `'random'` default STAYS deterministic records[0] (= benzene) for Save→Load reproduction safety; only the FALSE wording changes. Text-only edit.
- **08-08 additionally (owner round-2 directive):** the Head combo must repopulate WITHOUT Apply — see "Owner directive" below.

### (2) Negative-frequency wording — CHOSEN: `d2-option-b-two-tier`

`imaginary_note(freqs)` (08-06 implements, spectra_ui.py, co-located after freq_label/table_rows; 08-09 renders in the Spectra log):

- No negative → `None`.
- Any freq < 0 with ALL imaginary modes `< 20.0` (strict):
  `'%d small imaginary mode(s) (<20i cm-1): soft inter-stack modes, physical for molecular stacks'`
- Any imaginary mode `>= 20.0`:
  `'%d large imaginary mode(s) (>=20i cm-1): possible saddle point - check the structure'`
- Boundary `-20.0` → the SADDLE line (strict `<` threshold). Count = number of imaginary modes. All ASCII. The ≥20i tier has never been observed here (wording owner-approved now).

### (3) README '!! Under Development !!' sub-line — CHOSEN: `d3-option-amend`

Line 4 final literal (08-07 writes; 08-03 pins byte-for-byte):

> `> !! v1.0 - vibe-coded, review before production/teaching use !!`

The vibe warning block (README lines 1-2) is preserved byte-identical.

### (4) Recorded defaults — CHOSEN: `d4-confirm-all` (all seven AS DRAFTED)

| # | Default | Disposition |
|---|---------|-------------|
| 1 | xtb_path: save-as-is + normalize-on-load (`normalize_loaded` rewrites a foreign path to None + note `'xtb path not found on this machine - using auto-detect'`) | CONFIRMED |
| 2 | generic_stack_consent carried in shared files (never randomized; save/load carries it) | CONFIRMED |
| 3 | Save-file default name `serpentrum_setup.json` | CONFIRMED |
| 4 | SETUP-08 proof = one-machine two-session | CONFIRMED |
| 5 | Selector-Error cosmetic fix stays DEFERRED | CONFIRMED |
| 6 | `hud_logic.idle_tip` stays UNWIRED | CONFIRMED |
| 7 | Data-blessing offers: IUCr attribution wording OFFERED; optional 2nd Janiak access attempt OFFERED; SHA-256 recording = SKIP default | CONFIRMED |

## Owner directive (round 2 — GATE D amendment, folded into 08-08)

> "arent u going to remove apply, and its confusing to only show after apply. suppose after choosing the demo set the options should be there."

CONFIRMED behaviors:
- **Apply IS removed** — 08-08 already removes the temp `Apply / Show in Viewer` button (bottom row replaces the temp row; `_on_apply` survives only as the internal Start-first apply+validate path, 04-06 contract).
- **NEW (08-08 scope):** the Head combo repopulates at DEMO-SET-SELECTION time, not only post-Apply: selecting Demo Set A immediately repopulates Random + the 5 molecule names (read-only `setloader.load_demo_set`, no materialize); an upload repopulates after its browse-load succeeds. The post-Apply repopulation stays (harmless, same source).

## Checkpoint inventory note

This is the phase's only checkpoint:decision; GATE V (08-11) is the only checkpoint:human-verify.
