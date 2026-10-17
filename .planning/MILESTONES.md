# Project Milestones: serpentrum

## v1 — Playable Release (Shipped: 2026-10-18)

**Delivered:** The complete playable v1 of serpentrum — a PyMOL 2.5.0 plugin snake game where real small molecules stack onto the snake at human-approved cited π-stack geometry (3.60 Å @ 20°, Janiak 2000 + measured CC0 COD), and the assembled snake's IR spectrum is computed end-to-end via a real async, cancellable `xtb --ohess` run and explored through a broadened IR plot plus a clickable frequency table with static vibrational-mode vectors — plus two post-release gameplay refinements under the same umbrella: randomized pickup spawning and accumulating red line-wall obstacles (cap 5, fairness clearances).

**Phases completed:** 1–9 + inserted 5.1/5.2/5.3/9.1 (13 phases, 127 plans)

**Requirements:** 46/46 Complete — GATE V owner sign-off 2026-10-10 (data approval / 6-button + educator round-trip / release close incl. real xtb); milestone audit PASSED 2026-10-18 (46/46 requirements, 13/13 phases, 8/8 integration seams, 6/6 E2E flows, zero critical gaps).

**Key accomplishments:**

- Full arrow-key-steered game inside PyMOL (2D locked camera, countdown/HUD/pause/restart, owner-tuned speed tiers 6.0/9.0/11.0/13.0 Å/s, accumulated line-wall obstacles)
- Chemistry-faithful stacking: data-driven dataset + clash gate + refuse-and-skip integrity (no invented chemistry); user-consented, labeled generic π-stack for ring-bearing uploads
- Async cancellable xtb pipeline with a verified success contract (exit 0 + "normal termination" + expected files), streamed live log, calibrated ~104-atom budget guard
- Spectra payoff: Gaussian-broadened IR plot (unit/color/direction options, exact presets, PNG save) + frequency table → static mode vectors on the optimized structure (imaginary modes as −31.9i)
- Human-certified release: GATE V data sign-off with CID/DOI/license attribution, educator Save/Load Setup round-trip, end-to-end release smoke; 46/46 requirements with a 136-path evidence ledger
- Discipline held to the end: AST purity gates (zero external deps), anchored single-instance modeless dialog, 1084 WSL unittests + 12 headless Windows-PyMOL smokes + `--xtb` gate — 17 owner checkpoint occasions, all approved

**Stats:**

- 513 files created/modified, 104,764 insertions (659 commits)
- 39,527 lines of Python across 106 files (shipped plugin core `serpentrum/*.py` = 13,506)
- 13 phases, 127 plans, 256 tasks (228 auto, 11 TDD, 17 checkpoints)
- ~42 days from 2026-09-05 to ship (2026-10-18)
- Battery green at close: 1084 unittests + 12/12 required smokes + xtb normal termination + docs audit 7/7 + requirements audit 46/46

**Git range:** `feat(01-01)` → `feat(9.1-07)` (2a1c72b → b16f38b)

**Archives:** [milestones/v1-ROADMAP.md](milestones/v1-ROADMAP.md) · [milestones/v1-REQUIREMENTS.md](milestones/v1-REQUIREMENTS.md) · [milestones/v1-MILESTONE-AUDIT.md](milestones/v1-MILESTONE-AUDIT.md)

**What's next:** Not yet defined — run `/gsd-new-milestone` (questioning → research → requirements → roadmap) to shape the next release; candidate backlog (v2 deferred items + owner-flagged quick candidates) recorded in PROJECT.md.

---
