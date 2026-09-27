# Phase 8: Demo Data, Docs & Release Audit — RESEARCH: Data Attribution & Demo-Pack Finalization (DATA-01/02/04 + DOCS-02)

**Researched:** 2026-09-27 (read-only session; live re-verification of 4 sources this session)
**Domain:** Demo Set A attribution completion (DATA_SOURCES.md DRAFT→APPROVED), demo-pack coherence audit, DATA-02/04 human-approval checkpoint design
**Confidence:** HIGH (every load-bearing file read in the current tree; key citations re-verified live this session; checkpoint precedents cited by plan file)

## Summary

The honest finding: **almost all of the data substance already landed in Phases 2/3/5.2 — what remains for DATA-01/02/04+DOCS-02 is a small, enumerable completion pass plus the human sign-off act itself.** The stacking dataset `serpentrum/data/stacking_pi_stack.json` is already `status: APPROVED` (Phase 2, 02-11 checkpoint:decision, option-a: 3.60 Å centroid–centroid @ 20° encoded as `distance_a` 3.383 / `lateral_offset_a` 1.231; STATE.md 2026-09-10). The 5 PubChem 3D SDFs + `manifest.json` shipped at 03-05 (human-placed, builder-verified). The [JAN2000] SCOPE CAVEAT landed 2026-09-20, and the Phase-5.2 consent/disclosure surface already carries the "explicit crystalline-state framing" the caveat asked for (DATA_SOURCES.md §2 generic-stack section — the prior decision constrains this research to treat that framing as landed). **What has NOT happened** (STATE.md pending todo, verbatim): "Demo-data FULL DATA_SOURCES.md checklist sign-off (all molecules + attribution) remains Phase 8-gated."

So the DATA_SOURCES.md completion work is exactly three content edits + one status flip + one coupled test-pin edit, followed by ONE blocking human checkpoint that approves the whole attribution document (bioCHEMeleon format, defined below). Everything else (the "bioCHEMeleon format" question, the demo-pack coherent-shipping proof, the audit seams) already exists in-repo and just needs to be re-run/extended, not invented.

**Primary recommendation:** Plan ONE data-completion plan: (Task 1, auto) apply the three content edits (stale shipment NOTE, Chem. Mater. vol/pages from the Crossref record verified this session, license-note date stamps) and re-run the demo-pack audit chain (`tools/build_demo_manifest.py` + `test_demo_data` + `test_stacking_dataset` + a `setloader.load_demo_set` zero-errors probe) — still DRAFT-headed, commit; (Task 2, `checkpoint:human-verify`, blocking) present the final document + audit evidence + the itemized approval checklist from `02-RESEARCH-demo-data.md` §7 (items D/E/F residue) for the full DATA-02/04/DOCS-02 sign-off; (Task 3, conditional auto) on approval flip the header/footer/legend `DRAFT — NOT APPROVED` → approved wording AND update the coupled `'DRAFT'` marker pin in `tests/test_stacking_dataset.py` (it pins the literal 'DRAFT' — a red-suite trap if forgotten), re-run gates, record the verbatim owner approval in the SUMMARY.

## Re-verification this session (live, read-only, 2026-09-27)

| Source | Route | Result |
|--------|-------|--------|
| PubChem CID 241 3D SDF | `https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/241/SDF?record_type=3d` | **HTTP 200**, 12 atoms, OEChem 3D V2000 — matches DATA_SOURCES.md §1 (benzene, 12 atoms) |
| COD 4003564 CIF | `https://www.crystallography.net/cod/4003564.cif` | **HTTP 200** (588 KB); `_journal_paper_doi 10.1021/acs.chemmater.0c01184` confirmed in-file; `# All data on this site have been placed in the public domain` header confirmed |
| COD 2100607 CIF | `https://www.crystallography.net/cod/2100607.cif` | **HTTP 200**; IUCr header confirmed: `# were provided by IUCr Journals ... The file may be used within the scientific community so long as ...` (attribution-requested wording as documented) |
| NCBI policies page (license) | `https://www.ncbi.nlm.nih.gov/home/about/policies/` | **HTTP 200**; sentence verbatim: "Information that is created by or for the US government on this site is within the public domain ... it is requested that in any subsequent use of this work, NLM be given appropriate acknowledgment." |
| Crossref 10.1021/acs.chemmater.0c01184 | `https://api.crossref.org/works/10.1021/acs.chemmater.0c01184` | **HTTP 200**: Liu, K.; Lei, Y.; Fu, H. *Chemistry of Materials* **2020**, **32** (12), **5162–5172** — closes the "vol/pages to be added at data-prep" TODO in DATA_SOURCES.md §[COD4003564] |
| PubChem-specific docs pages | `docs/program-information`, `docs/about-pubchem`, `docs/disclaimer` | **All still 404** (as in the 2026-09-07 session) — the §1 license-note fallback (NCBI-wide policy page as the verified license source) STANDS; human may optionally verify via an interactive browser |

These are recorded as evidence; nothing about them changes DATA_SOURCES.md's existing verification claims. The Crossref vol/pages are NEW content the executor transcribes and the human approves at the checkpoint (no fabrication rule — the value is source-verified above, not invented).

## Q1 — What EXACTLY remains to move DATA_SOURCES.md DRAFT → APPROVED

The "bioCHEMeleon format" (DATA-04) **is defined**: `tmp/bioCHEMeleon/DATA_SOURCES.md` (202 lines) — per-section license blocks; per-molecule subsections with ID / DOI / title / authors / publication / method / notes; an attribution sentence pattern ("Cite: ..."); exams of processing notes and license provenance (e.g. CC-BY 4.0 string captured from the site JS bundle). Serpentrum's current file already follows that shape (02-RESEARCH-demo-data.md §5 says the draft mirrors it: "per-molecule sections: ID, DOI, title, authors, publication, license; per-source license blocks"). The serpentrum file is **176 lines vs the >60-line test floor**; structurally complete.

Itemized status of every remaining item (classification per the objective):

| # | Item (line refs in current file) | Status | Action needed |
|---|----------------------------------|--------|---------------|
| 1 | Title line 1 `(DRAFT — NOT APPROVED)` + footer line 176 + STATUS LEGEND lines 8–10 | **needs human sign-off** | flip to approved wording ONLY at the post-checkpoint task |
| 2 | §1 NOTE lines 23–26: "The PubChem 3D SDF files themselves are NOT part of this plan — they ship in a later phase (Phase 8 ...)" | **stale → needs new content** | SDFs shipped at 03-05 (human-placed, `tools/build_demo_manifest.py` verified); rewrite NOTE to record the 03-05 placement (date, five CIDs, builder cross-checks) |
| 3 | §1 License lines 40–44 (NCBI policy fallback; PubChem docs page 404) | **already-verified-lands-as-is**, optionally re-dated | re-verified 2026-09-27 (above); the plan may stamp the re-verification date; human re-blesses at the checkpoint |
| 4 | §[COD4003564] lines 110–111: "(vol/pages to be added at data-prep from the DOI record.)" | **needs new content** | Crossref-verified this session: *Chem. Mater.* 2020, 32(12), 5162–5172 — transcribe + human approve |
| 5 | [JAN2000] full-text items (3.3 Å lower bound / any 3.4 Å statement) | **already honest; keep UNVERIFIED** | do NOT touch; optional owner institutional-access read (§7 item G of 02-RESEARCH) stays offered-and-skippable at the checkpoint |
| 6 | [JAN2000] SCOPE CAVEAT + generic-upload-stacking section (lines 63–102) | **already landed (2026-09-20 / Phase 5.2)** | nothing to add; the section explicitly holds "the consent + 'user-approved' labeling IS the explicit crystalline-state framing requested for Phase 8" (prior decision — treat as landed) |
| 7 | Herringbone negative-evidence block (lines 132–143) + [HS1990] block (145–150) + §3 UNVERIFIED list (152–161) + §4 precision note (163–170) | **already-verified-lands-as-is** | none — they are compliance evidence (the §3 do-not-ship list must SURVIVE approval; it is evidence the game does not ship 3.3/3.4 Å) |
| 8 | `tests/test_stacking_dataset.py:201` pins literal `'DRAFT'` as a required marker | **coupled edit — red-suite trap** | the post-approval task MUST update this pin in the same commit as the header flip (see Pitfalls) |

Nothing else is missing: every molecule section carries CID, formula, atom count, [VERIFIED] marker; every measured distance carries COD ID + DOI + license header quote; every UNVERIFIED number is named do-not-ship; CSD/CCDC appear nowhere as redistributed data (only cited published values + CIF-sourced measurements of CC0/IUCr-attribution entries — DATA-04-compliant pending the human's blessing of the IUCr wording, which is checklist material).

## Q2 — Demo-pack completeness audit design (DATA-01 coherent-shipping proof)

Every cross-check the objective asks about already has an existing seam; the plan re-runs (and optionally extends) them rather than building new machinery:

| Check | Existing seam | How the audit runs it |
|-------|---------------|------------------------|
| manifest atom/charge/ring counts vs SDF reality | `tools/build_demo_manifest.py` (idempotent; ABORTS on any mismatch; never writes a fabricated manifest) | re-run `python3.6 tools/build_demo_manifest.py` and diff — byte-identical output proves manifest↔SDF↔DATA_SOURCES.md §1 table coherence (its MOLECULES table IS transcribed from DATA_SOURCES.md §1) |
| parser + ≤3-ring gate on the real shipped bytes | `tests/test_demo_data.py` (7 tests, green this session) | part of the gate suite — no new work |
| dataset loads through the validated loader + geometry derives from the file + DOIs cross-link into DATA_SOURCES.md | `tests/test_stacking_dataset.py` (16 tests, green this session) | part of the gate suite — extends with §3/herringbone markers only if the planner wants (see below) |
| `stacking_pi_stack.json` 3.383/1.231 vs DATA_SOURCES.md measured set | test composed-geometry pin: sqrt = 3.60001, atan2 = 19.998° (file-derived, no hardcoded headline) | already proven; the audit prose explains the encoding once (3.555/3.570/3.580 all round to 3.6 → the shipped contract value, measured-vs-rounded stated in the dataset `explanation`) |
| setloader's load path end-to-end | `serpentrum/setloader.py:125 load_demo_set(data_dir='serpentrum/data', set_id='set_a', stacking_path='serpentrum/data/stacking_pi_stack.json')` | **new one-liner probe (pure, WSL-runnable)**: assert `errors == []`, `len(records) == 5`, every record `has_stack_entry is True`, and every record carries a 6-atom `stack_ring` — this is THE direct DATA-01 coherent-shipping proof. Candidate: fold into `test_demo_data.py` as one new test class or ship as `tools/audit_demo_pack.py` (dev-side, purity-exempt — `tools/` has no `__init__.py` and the purity walk only scans `serpentrum/`) |
| KNOWN_SETS ↔ manifest ↔ GUI wiring | `setup_logic.py:44 KNOWN_SETS = ('set_a',)`; `gui_setup.py:97` iterates KNOWN_SETS | text-presence check only; no edit expected (set count is 1 by design) |
| molecule_data.py loader disciplines | `load_manifest` file-existence rule (`:178`), `shipped_interactions` (APPROVED-only, `:333`) | covered by existing suites |

**Optional new-content additions the checkpoint could approve (label clearly as offers, not requirements):** SHA-256 of the 5 shipped SDFs recorded in DATA_SOURCES.md §1 for byte-level traceability (computed this session — anthracene `f2dd5b12…`, benzene `1ce15441…`, biphenyl `ce290049…`, naphthalene `916dc621…`, phenanthrene `46214173…`; full values recomputable on demand). NOT demanded by DATA-01/04; skip unless the owner asks.

## Q3 — [JAN2000] SCOPE CAVEAT: two sanctioned paths evaluated

The caveat's Phase-8 TODO (DATA_SOURCES.md lines 72–75) offers: (a) a verified solution-phase/aqueous geometry check, or (b) explicit crystalline-state framing in UI/help text.

- **Path (a) — a new solution-phase source — is NOT planable without new unverifiable claims.** No solution-phase π-stack geometry source was ever verified anywhere in this repo's evidence trail; any new source found by an agent would still land as a new citation requiring human verification (institutional full-text access plausibly needed — exactly the failure mode that quarantined 3.3/3.4 Å in Phase 2). Per the repo hard rule, an agent plan cannot ship it; it can only offer "owner performs an institutional-access read" as a skippable checkpoint option (same shape as 02-11's option-c, which the owner already declined once by choosing option-a).
- **Path (b) — explicit crystalline-state framing — is mostly LANDED; the remainder belongs to the docs track, not the data plan.** Existing surfaces: (1) the dataset `explanation` field ends "Idealized pairwise geometry - neat Set A crystals are herringbone (see DATA_SOURCES.md)" — rendered **verbatim** in the in-game info box on every Set-A capture (`hud_logic.pickup_block`, `hud_logic.py:94-113`) and in idle tips (`:297-302`); (2) the Phase-5.2 consent note + labels ("illustrative geometry - user-approved [Janiak 2000]", `hud_logic.py:230-244`), owner-approved 11/11 at 5.2-09 and recorded in DATA_SOURCES.md §2 as "the explicit crystalline-state framing requested for Phase 8, landed early"; (3) the SCOPE CAVEAT itself in the shipped attribution doc.
- **What (b) still touches (and which plan owns it):** DOCS-03 in-game help text and DOCS-01 README should each carry ONE crystalline-framing sentence (e.g. that stacking distances are idealized pairwise geometry derived from crystal-structure data) — wordings must be **transcribed from DATA_SOURCES.md/the dataset explanation verbatim or near-verbatim** (no new chemistry claims) and are checkpoint artifacts of the help/docs plan (sibling `08-RESEARCH-help-docs.md`), not the data plan. **Recommendation: keep the data plan GUI-free**; the data plan only guarantees the doc the help text quotes from is final and approved.

## Q4 — Human-approval checkpoint design

**Recommendation: ONE consolidated blocking `checkpoint:human-verify` task (numbered steps + per-step EXPECT lines + verdict table), not per-item checkpoints.** Precedents, by plan file:

- `02-11-PLAN.md` — the canonical DATA-02 artifact pattern: dataset ships DRAFT; **decision-agnostic tests** (assert invariants, green in both states); ONE blocking `checkpoint:decision` with options A/B/C; a defined post-decision action list; decision recorded verbatim in SUMMARY "Decisions Made". NOT reusable verbatim here (that was a number-choice checkpoint) but the "changes ONLY by explicit human decision" + post-decision-actions shape is.
- `5.2-09-PLAN.md` Task 2 — the closest structural model: `checkpoint:human-verify` with `<what-built>` / `<how-to-verify>` (11 numbered steps, EXPECT per step) / `<resume-signal>` ("Type 'approved' ... or describe issues"); per-item approvals ACCUMULATE across rounds (05-16 model: only re-test what changes); followed by a conditional literal-only apply task.
- `06-12-PLAN.md` — gates-first task, then the ONE consolidated phase-close checkpoint; per-step verdicts in a PASS/FAIL table; EQ amendments recorded with commit hashes in the SUMMARY.
- `07-10` (SUMMARY/STATE) — round-based approval: round-1 defect → fix commit → round-2 consolidation APPROVED; plans should expect 1–2 rounds.

**What the executor must present at the DATA-02/04/DOCS-02 checkpoint:**
1. The final DATA_SOURCES.md (post-content-edits) as the approval artifact — with the §3 UNVERIFIED do-not-ship list intact.
2. The itemized checklist from `02-RESEARCH-demo-data.md` §7 residue: item D (approve the attribution document: sources, licenses, verification notes, UNVERIFIED section), item E residue (dataset JSON already APPROVED at Phase 2 — confirm it rides unchanged), item F (idealized-geometry labeling — verify it exists in-game: dataset explanation + info-box render + generic-mode labels).
3. The audit evidence: `build_demo_manifest.py` output (byte-identical), gate results, the setloader probe result, this session's re-verification table (above).
4. Explicit offers: (i) IUCr attribution-wording blessing for the pyrene/naphthalene/phenanthrene entries (open item §8.2 of Phase-2 research); (ii) skippable institutional-access read of Janiak full text (items G/A4 — owner already declined once; record the decline or the read); (iii) optional SDF SHA-256 recording.
5. Resume-signal: owner types "approved" (verbatim-quote the approval in the SUMMARY) or describes amendments; amendments apply in a conditional literal-only task and iterate (per-item accumulation).

**Post-approval apply task (conditional, literal-only):** flip the three header/legend/footer `DRAFT — NOT APPROVED` markers to the approved wording AND edit `tests/test_stacking_dataset.py:198-206` (the `'DRAFT'` marker pin) in the SAME commit; re-run `python3.6 tests/run_gates.py`; commit `docs(08-NN): DATA_SOURCES.md approved — DATA-02/04 sign-off`; record the verbatim owner approval line.

## Q5 — Purity / file-domain map for the data track

| Surface | Kind | Planning consequence |
|---------|------|----------------------|
| `serpentrum/data/DATA_SOURCES.md`, `manifest.json`, `stacking_pi_stack.json` | content files (non-.py) | invisible to the AST purity walk (it scans `serpentrum/**/*.py`); plugin-path-safe (gate 1 only cares about `*.py`/`__init__.py`) |
| `tools/build_demo_manifest.py`, any new `tools/audit_demo_pack.py` | dev-side scripts | purity-exempt; `tools/` must NEVER gain `__init__.py`; stdlib + `serpentrum.molfile` imports only, py3.6 syntax, %-formatting |
| `tests/test_stacking_dataset.py`, `tests/test_demo_data.py` | tests | purity gate does not scan `tests/`; keep `tests/` free of `__init__.py`; sys.path self-insert pattern retained |
| `serpentrum/*.py` pure modules | **NO edits expected** | any pure-module edit would drag the plan through the purity gate for nothing — the data track is data/docs/tests/tools only |
| `serpentrum/gui_*.py` (GUI_MODULES allowlist) | **NO edits in the data plan** | crystalline-framing in help text belongs to the docs plan (gui edits only there, if at all — help text likely lives in pure `*_logic` modules rendered verbatim) |

Net: the data plan should be **GUI-free and pure-module-free** — data files + tests + tools + planning docs only.

## Q6 — Pitfalls specific to this data work

1. **Marker-pin trap (found this session):** `tests/test_stacking_dataset.py:201` requires the literal `'DRAFT'` in DATA_SOURCES.md. Flipping the header without updating that pin turns the suite red in the approval commit. Conversely, the pin must NOT be weakened pre-approval (it guards the governance state machine). Same-commit coupling is the fix.
2. **Never re-fetch/regenerate the shipped SDFs.** The five files were HUMAN-PLACED at 03-05; `manifest.json` and `find_ring_atoms` results key on their exact bytes. PubChem's OEChem pipeline regenerates 3D conformers (CID 241 fetched this session is a fresh 2026-09-26 3D record — byte-different candidates). The audit verifies the shipped bytes; it never replaces them. (Contrast with bioCHEMeleon Pitfall-by-analogy: treat shipped data like committed fixtures.)
3. **No-fabrication hard rule (AGENTS.md / DATA-02):** the approval is a HUMAN act. Plans must encode `checkpoint:human-verify`/`checkpoint:decision` with `gate="blocking"`; the executor may prepare evidence and transcribe source-verified facts (Crossref vol/pages above carry their evidence trail), never assert approval.
4. **IUCr attribution wording is a blessing item, not a license problem.** Pyrene COD entries (2100607/8) and herringbone entries 2311088/5000181 carry "may be used within the scientific community so long as proper attribution is given" headers (re-verified 2100607 this session) — cited, never redistributed (DATA-04-compliant), but the human should still see and bless the wording (Phase-2 research open item §8.2).
5. **Keep the UNVERIFIED list post-approval.** §3's do-not-ship list (3.3/3.4 Å, biphenyl-COD-absent) is governance evidence that the game does NOT ship those numbers (cross-checked by the "no invented data anywhere" part of DATA-02 and the ROADMAP anti-feature "silent fallback stacking ... is worse than refusing"). Approving the document does not delete the quarantine list.
6. **`.pse`/desync family (Pitfall 8, leaked-keys Pitfall 4) — out of scope here.** They gate the release-audit and persistence plans (siblings: `08-RESEARCH-release-audit.md`, `08-RESEARCH-persistence.md`), not data completion. Mentioned only so the planner doesn't duplicate scope.
7. **Planning-doc date convention:** commit/UTC dates authoritative; dev shell is HKT — stamp UTC (`2026-09-27` for this session).
8. **Checksum drift if re-running the builder after SDF edits:** `build_demo_manifest.py` aborts on mismatch — good; but its `ring_atoms` output would differ if anyone swapped SDF bytes. The audit runs the builder and expects **byte-identical** `manifest.json` (git diff empty).

## Architecture Patterns (plan sequencing for the approval gate)

Recommended plan skeleton (mirrors 5.2-09 / 06-12 shape):

```
Task 1 (auto): content edits + full audit chain, STILL DRAFT-headed
  files: serpentrum/data/DATA_SOURCES.md (+ optionally tools/audit_demo_pack.py or test_demo_data extension)
  actions: fix stale NOTE; add Chem. Mater. 32(12) 5162-5172 (Crossref trail);
           re-verification date stamps; run build_demo_manifest.py (expect byte-identical);
           run setloader probe; run python3.6 tests/run_gates.py
Task 2 (checkpoint:human-verify, gate=blocking): full DATA-02/04/DOCS-02 sign-off
  present: final doc diff, itemized checklist (§7 residue D/E/F + IUCr blessing + optional offers), audit evidence
Task 3 (auto, conditional): apply approval literals + coupled test-pin edit + gates + commit
```

Parallelization note: this plan has no intra-phase dependency on the persistence/help/docs plans until the checkpoint (content edits touch only `DATA_SOURCES.md`; the docs plans must not edit it — the data plan is its single writer, mirroring the GUI_MODULES single-writer precedent). Checkpoint rounds serialize against the phase close (DOCS-05 audit evidence cites the APPROVED header), so wave order: data plan's Task 1 can run in wave 1 in parallel with other Phase-8 plans; the checkpoint lands whenever the owner is available; approval blocks only DOCS-05's final requirement-table tick-off for DATA-01/02/04 + DOCS-02.

## Don't Hand-Roll

| Problem | Don't build | Use instead | Why |
|---------|-------------|-------------|-----|
| Proving manifest↔SDF coherence | a new metadata comparator | `tools/build_demo_manifest.py` (re-run; aborts on mismatch; byte-identical output check) | already cross-checks atom counts vs DATA_SOURCES.md table + cyclomatic math + ring_atoms ≥ 3 |
| Proving dataset↔doc DOI cross-links | grep scripts | `tests/test_stacking_dataset.py` (`test_every_dataset_doi_appears_in_sources`, tamper-proofing class) | covers loader schema + geometry derivation + DOI presence |
| End-to-end "demo pack loads" proof | a GUI/manual check | `setloader.load_demo_set(...)` probe (pure, 0-network, WSL) | exact production load path incl. gate + stack_ring computation + has_stack_entry |
| Citation metadata lookup | hand-typed vol/pages | Crossref `api.crossref.org/works/<DOI>` with the trail recorded (done this session for 0c01184) | authoritative registry; keep the evidence in the plan/checkpoint text |
| bioCHEMeleon-format guessing | inventing a new attribution schema | `tmp/bioCHEMeleon/DATA_SOURCES.md` (in-repo template) + 02-RESEARCH-demo-data.md §5 mapping | DATA-04 explicitly says "in the bioCHEMeleon format"; the shape already matches |

## Open Questions

1. **Approved-wording literals for the header/footer/legend flip** — the exact post-approval status string (e.g. "APPROVED 2026-XX-XX" vs "RELEASE — APPROVED") is an owner choice at the checkpoint; the plan should propose one literal and let the owner amend (5.2-09 model: approve-or-amend every DRAFT literal). Planner must draft the literal in the plan, not leave it TBD at execution.
2. **Where the audit probe lives** — extend `tests/test_demo_data.py` with a `TestLoadDemoSetEndToEnd` class (runs inside the existing suite, zero new files) vs a standalone `tools/audit_demo_pack.py` (richer printout, dev-side only). Both are legitimate; the test-suite extension is the lower-friction recommendation because it rides the gate suite forever.
3. **SHA-256 recording** — optional new content (checksums computed this session, listed in Q2); needs an explicit owner yes/no at the checkpoint. Default recommendation: skip (DATA-04 doesn't require it; git already pins content).
4. **Institutional-access Janiak full-text read** — offered-and-skippable for the second time (owner declined at 02-11 option-a). Record the second decline in the SUMMARY if declined again; 3.3/3.4 Å stay quarantined in §3 either way.

## Sources

### Primary (HIGH confidence — read in this session / live-verified)
- `serpentrum/data/DATA_SOURCES.md`, `manifest.json`, `stacking_pi_stack.json` (current tree)
- `.planning/phases/02-pure-core-game-chemistry-logic/02-RESEARCH-demo-data.md` (§5 format spec, §7 checklist, access log)
- `02-11-PLAN.md` / `02-11-SUMMARY.md` (DATA-02 checkpoint:decision pattern + DRAFT independence decision)
- `5.2-09-PLAN.md`, `06-12-PLAN.md` (checkpoint:human-verify structure: numbered steps, EXPECT lines, verdict table, conditional literal-apply task, accumulate-across-rounds)
- `.planning/STATE.md` (pending todo: full checklist sign-off Phase-8-gated; 02-11 DRAFT-headed decision; 5.2-09 consent-label approvals)
- `tmp/bioCHEMeleon/DATA_SOURCES.md` (the DATA-04 "bioCHEMeleon format" — per-molecule ID/DOI/title/authors/publication + per-source license blocks)
- `serpentrum/setloader.py`, `molecule_data.py`, `hud_logic.py`, `setup_logic.py`, `tools/build_demo_manifest.py`, `tests/test_demo_data.py`, `tests/test_stacking_dataset.py`
- Live fetches 2026-09-27: PubChem CID 241 3D SDF (200); COD 4003564 + 2100607 CIFs (200, license headers confirmed); NCBI policies page (200, public-domain sentence verbatim); Crossref 10.1021/acs.chemmater.0c01184 (200 → Chem. Mater. 2020, 32(12), 5162–5172); PubChem docs pages (404 confirmed)

### Secondary
- `ROADMAP.md` Phase 8 success criterion 1; `REQUIREMENTS.md` DATA-01/02/04 + DOCS-02
- `02-RESEARCH-demo-data.md` §8 open items (IUCr wording blessing; precision footnote — §4 already shipped)

## Metadata

**Confidence breakdown:**
- Completion itemization: HIGH (file-level enumeration with line refs)
- Audit seams: HIGH (all seams exist and were exercised this session; baseline suites green: 7 + 16 tests OK)
- Checkpoint design: HIGH (three in-repo precedents cited by plan file)
- Live re-verification: HIGH for the five 200s; honest 404 record for PubChem docs pages

**Research date:** 2026-09-27 (UTC)
**Valid until:** 2026-10-27 (stable — no moving API surface; only the DATA_SOURCES.md content itself changes when the phase executes)

## RESEARCH COMPLETE

**Phase:** 8 — Demo Data, Docs & Release Audit
**Confidence:** HIGH

### Key Findings

- DATA-02's number is already APPROVED (02-11 option-a, dataset `status: APPROVED`); the Phase-8 remainder is the **attribution-document** sign-off: exactly 3 content edits (stale SDF-shipment NOTE, Chem. Mater. vol/pages — Crossref-verified this session, license-note date stamps) + the header/legend/footer flip at the checkpoint.
- The demo-pack coherent-shipping proof (DATA-01) requires NO new machinery: re-run `tools/build_demo_manifest.py` (byte-identical expectation), existing `test_demo_data` + `test_stacking_dataset` suites (green this session, 7+16), plus one pure `setloader.load_demo_set` zero-errors probe as the direct production-load-path proof.
- Hidden coupling: `tests/test_stacking_dataset.py:201` pins the literal `'DRAFT'` — the approval commit must edit that pin in the same commit or the suite goes red (decision-agnostic-suite trap, inverted).
- The [JAN2000] SCOPE CAVEAT is resolved organizationally, not chemically: path (a) (new solution-phase source) is not planable without new unverifiable claims; path (b) (crystalline-state framing) is already landed in-game (dataset explanation rendered verbatim via `pickup_block`; Phase-5.2 consent labels) — its README/help-text residue belongs to the docs plans, which must quote, not paraphrase-new-claims.
- The data plan is GUI-free and pure-module-free: touches only `serpentrum/data/*.md|json`, `tests/`, `tools/`, and planning docs — all purity-walk-invisible surfaces.

### File Created

`.planning/phases/08-demo-data-docs-release-audit/08-RESEARCH-data.md`

### Confidence Assessment

| Area | Level | Reason |
|------|-------|--------|
| Standard stack (existing seams/tools) | HIGH | all exercised this session; suites green |
| Architecture (checkpoint sequencing) | HIGH | 02-11 / 5.2-09 / 06-12 precedents read in full |
| Pitfalls | HIGH | marker-pin trap found by direct inspection; re-verification performed live |
| Citation evidence | HIGH | 5 live 200s + honest 404 record, 2026-09-27 |

### Open Questions

Approved-wording literal for the status flip; audit-probe placement (test class vs tools script); optional SHA-256 recording; second offer of institutional-access Janiak full-text read. All four are checkpoint-askable owner items, none block planning.

### Ready for Planning

Research complete. The planner can now create the DATA-01/02/04 + DOCS-02 plan(s) using the three-task skeleton above.
