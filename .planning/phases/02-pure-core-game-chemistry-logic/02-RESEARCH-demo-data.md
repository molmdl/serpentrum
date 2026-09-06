# Phase 2 — Demo-Data Approval Track (Set A π-stack): Research & Verification

**Researched:** 2026-09-07 (live web + COD measurement session)
**Domain:** π-stack parallel-displaced distance pinning for Demo Set A (benzene, naphthalene, anthracene, phenanthrene, biphenyl)
**Confidence:** HIGH for the measured COD values and the abstract-verified Janiak rule. The original 3.4 Å game candidate is **UNVERIFIED** — no accessible source states it. Best verified alternatives pinned below.

---

## 0. Headline result

1. **Janiak 2000 full text is not legally accessible anywhere** (Unpaywall: `oa_status: closed`, `has_repository_copy: false`; RSC 403). What is verifiable is the **abstract** (retrieved via the OpenAlex record, reconstructed word-for-word from its inverted index): the usual π interaction is *offset/slipped* stacking; *ring normal vs centroid vector ≈ 20°*; *centroid–centroid distances up to **3.8 Å***. The abstract contains **no 3.3 Å and no 3.4 Å** — both remain UNVERIFIED.
2. **Measured pinning from CC0 COD crystal structures (computed this session, script + arithmetic in §3):** true parallel-displaced π-stacks measure **3.555–3.580 Å ring-centroid–centroid** (interplanar 3.345–3.478 Å, lateral offset 0.83–1.20 Å, plane angles 0.0–2.7°) in three independent structures — pyrene ×2 (homomolecular stack) and a phenanthrene·TCNB charge-transfer stack (phenanthrene is a Set A molecule).
3. **All four neat Set A crystals measured are herringbone — they contain NO π-stack** (closest contacts 4.6–5.1 Å at 50–86°; the only near-parallel contacts are lattice translations with 4.5–5.4 Å offset = zero ring overlap). This *verifies by measurement* what project research had flagged UNVERIFIED, and confirms the design decision to use **idealized pairwise interaction geometry, labeled as such**.
4. **Recommendation to the human:** store **3.6 Å centroid–centroid** (all three measured stacks round to 3.6; within Janiak's ≤3.8 Å rule) with a ~20° ring-normal angle for the displaced geometry. Alternatives offered in the approval checklist (§7). 3.4 Å is offered only with the explicit caveat that no accessible source supports it.

---

## 1. Access log (what worked / what failed)

Every route tried this session, recorded factually:

| # | Source / route | Result |
|---|----------------|--------|
| 1 | OpenAlex `api.openalex.org/works/doi:10.1039/b003010o` | **OK** — full record incl. abstract (inverted index), 4497 citations, closed OA status |
| 2 | Semantic Scholar `api.semanticscholar.org/graph/v1/paper/DOI:10.1039/b003010o` | **OK** — record; abstract elided by publisher; `openAccessPdf: CLOSED` |
| 3 | Unpaywall `api.unpaywall.org/v2/10.1039/b003010o?email=...` (2 attempts, 2nd with valid-format email) | **OK on 2nd** — `oa_status: closed`, `has_repository_copy: false`, `oa_locations: []` → **no legal OA copy exists anywhere** |
| 4 | RSC landing page `pubs.rsc.org/en/content/articlelanding/2000/dt/b003010o` | **403** (same as during original project research) |
| 5 | Crossref `api.crossref.org/works/10.1039/b003010o` | **OK** — bibliographic metadata (issue 21, pp. 3885–3896, 2000, RSC, 4420 cites); **no abstract deposited** |
| 6 | SciSpace paper page (found via search) | **405** on direct fetch; its search-result snippet independently corroborates the abstract's opening wording verbatim |
| 7 | DuckDuckGo HTML search for `"b003010o" pdf` | **OK** — surfaced only RSC (paywalled), SciSpace (abstract), and **Sci-Hub mirrors — NOT used** (inappropriate for this repo's citation workflow; the human may read the paper via institutional access if desired) |
| 8 | OpenAlex `doi:10.1021/ja00170a016` (Hunter & Sanders 1990) | **OK** — title/venue/pages (JACS 112(14), 5525–5534, 1990, 5315 cites) verified; closed, no usable abstract text |
| 9 | COD search `crystallography.net/cod/result.php?formula=...` (C6H6, C10H8, C14H10, C12H10, C16H10, C12H6F6, C20H10N4, C24H12N4, text=biphenyl) | **OK** — all searches returned; CC0 site license stated on every results page |
| 10 | COD CIF downloads `crystallography.net/cod/{id}.cif` via curl (10 entries) | **OK** — all HTTP 200 |
| 11 | PubChem PUG REST CIDs 241/931/8418/995/7095 property lookup + 3D SDF download | **OK** — all 5 CIDs verified, all 5 have 3D SDF records (atom counts match formulas exactly) |
| 12 | PubChem license docs (`/docs/program-information`, `/docs/general_information`) | **404** (paths changed); NCBI policies page `ncbi.nlm.nih.gov/home/about/policies/` fetched OK — US-government-created data is public domain, acknowledgment requested; PubChem listed as a resource with its own terms |
| 13 | benzene·hexafluorobenzene (C12H6F6) in COD | **0 results** — the classic cofacial benzene cocrystal is not in COD |
| 14 | neat biphenyl in COD | **absent** — formula C12H10 returns only acenaphthene (isomer); text search finds 2278 biphenyl-*derivative* structures but not the neat crystal |

---

## 2. Pinned candidate values

All computed values are **measured this session from downloaded CC0 COD CIFs** (method, script and sanity checks in §3). Quoted values carry the exact source location.

### 2.1 Literature rule (Janiak 2000, abstract — the verifiable part)

Exact abstract text (reconstructed mechanically from the OpenAlex inverted index; opening confirmed verbatim by an independent SciSpace snippet):

> "A geometrical analysis has been performed on π–π stacking in metal complexes with aromatic nitrogen-containing ligands based on a Cambridge Structural Database search and on X-ray data of examples in the recent literature. It is evident that a face-to-face π–π alignment where most of the ring-plane area overlaps is a rare phenomenon. **The usual π interaction is an offset or slipped stacking, i.e. the rings are parallel displaced. The ring normal and the vector between the ring centroids form an angle of about 20° up to centroid–centroid distances of 3.8 Å.** Such a parallel-displaced structure also has a contribution from π–σ attraction, the more so with increasing offset. […]"

| Claim | Status | Location |
|-------|--------|----------|
| Usual π interaction = offset/slipped (= parallel-displaced) stacking | **VERIFIED** | Janiak 2000 abstract (OpenAlex W2142594455) |
| Ring normal vs centroid-vector angle ≈ 20° | **VERIFIED** | same |
| Centroid–centroid distances **up to 3.8 Å** (upper bound of usual stacking) | **VERIFIED** | same |
| Face-to-face (eclipsed) alignment is rare | **VERIFIED** | same |
| "3.3 Å lower bound" (the commonly quoted 3.3–3.8 range) | **UNVERIFIED** — not in the abstract; full text paywalled/closed everywhere (Unpaywall) | — |
| "3.4 Å" game candidate | **UNVERIFIED** — no accessible source states this number | — |

### 2.2 Measured parallel-displaced π-stacks (COD, computed 2026-09-07)

| COD entry | Material (formula) | Conditions | Definition | d (Å) | perp (Å) | offset (Å) | plane angle | DOI of source paper | License header |
|-----------|--------------------|-----------|------------|-------|----------|------------|-------------|---------------------|----------------|
| **4003564** | phenanthrene·TCNB 1:1 cocrystal (C24H12N4) | RT | D···A mixed stack, closest six-ring pair | **3.555** | 3.345 | 1.204 | 2.7° | 10.1021/acs.chemmater.0c01184 | public domain ("placed in the public domain by the contributors") |
| 2100607 | pyrene (C16H10) | 298 K, ambient | homomolecular stack along b, closest six-ring pair | **3.570** | 3.472 | 0.829 | 0.0° | 10.1107/S0108768106026814 | IUCr-provided, attribution-requested wording |
| 2100608 | pyrene (C16H10) | compressed | same | **3.580** | 3.478 | 0.851 | 0.0° | 10.1107/S0108768106026814 | IUCr-provided, attribution-requested wording |
| 2100607 (alt) | pyrene — same-ring translation | 298 K | ring i of molecule ↔ ring i of +b image | 3.852 | 3.458 | 1.697 | 0.0° | same | same |

**Measured normal-tilt angles** (angle of the inter-centroid vector off the ring normal): pyrene asin(0.829/3.570) = **13.4°**; phenanthrene·TCNB asin(1.204/3.555) = **19.8°** — consistent with Janiak's CSD-derived "about 20°".

**All three closest-pair values round to 3.6 Å at 0.1 Å precision.**

### 2.3 Measured herringbone reality of neat Set A crystals (negative evidence)

| COD entry | Material | T / P | Shortest intermolecular six-ring contact | Interpretation | DOI |
|-----------|----------|-------|------------------------------------------|----------------|-----|
| 7238223 | benzene | 150 K, ambient | **5.092 Å @ 85.6°** | T-shaped edge-to-face (herringbone); **no π-stack** | 10.1039/c001190h |
| 2311088 | naphthalene | 293 K | **4.651 Å @ 50.6°** | tilted edge-to-face; no ring-overlap stack | 10.1107/S2053273316018994 |
| 5000168 | anthracene (Brock & Dunitz) | RT | **4.598 Å @ 51.2°** | herringbone; no π-stack | 10.1107/S0108768190008382 |
| 5000181 | phenanthrene (Petricek et al.) | 295 K | **4.681 Å @ 57.5°** | herringbone; no π-stack | 10.1107/S0108768190007510 |

(In every structure the only near-parallel contacts are pure lattice translations with lateral offsets 4.5–5.4 Å — parallel planes, zero ring overlap, i.e. not π-stacks. Benzene 4501702 — 295 K at 150 MPa, DOI 10.1021/cg1002594 — is also available in `/tmp/opencode/cifs/` but was not needed; the 150 K ambient entry carries the clean conclusion.)

### 2.4 Molecule geometry (PubChem — re-verified live 2026-09-07)

| Molecule | CID | Formula | 3D SDF | Atoms in 3D record |
|----------|-----|---------|--------|--------------------|
| Benzene | 241 | C6H6 | **VERIFIED** (HTTP 200, OEChem 3D V2000) | 12 (6C+6H) ✓ |
| Naphthalene | 931 | C10H8 | **VERIFIED** | 18 ✓ |
| Anthracene | 8418 | C14H10 | **VERIFIED** | 24 ✓ |
| Phenanthrene | 995 | C14H10 | **VERIFIED** | 24 ✓ |
| Biphenyl | 7095 | C12H10 | **VERIFIED** | 22 ✓ |

This closes the "per-CID 3D conformer coverage" gap from project research (previously only benzene was confirmed).

---

## 3. Measurement record (reproducibility)

**Pipeline:** COD CIF (curl) → pure-stdlib python3.6 analyzer (`/tmp/opencode/cif_geom.py`, full listing in Appendix A) → symmetry expansion → molecule clustering → six-ring perception → closest intermolecular ring-centroid contacts with plane angle / perpendicular separation / lateral offset.

**Reproduce:**
```bash
curl -sS -o 2100607.cif https://www.crystallography.net/cod/2100607.cif   # etc.
python3.6 /tmp/opencode/cif_geom.py 2100607.cif
```

**Sanity checks performed (all passed):**
- Molecular formulas from clustering exactly match expected per structure (C6H6 ×4; C10H8 ×2; C14H10 ×2; C16H10 ×2; phenanthrene·TCNB cell contains 4×C14H10 + 4×TCNB).
- Six-ring counts per molecule: benzene 1, naphthalene 2, anthracene 3, phenanthrene 3, pyrene 4 ✓.
- Anthracene-vs-phenanthrene discrimination by terminal-ring geometry (anthracene collinear: 4.885 = 2.442+2.442; phenanthrene bent: 4.270 vs path 4.880) — used to prove COD 4003564's donor is **phenanthrene** (4.295 vs 4.914), matching the phenanthrene control entry 5000181.
- Raw C···C contacts across the pyrene stack: all 3.52–3.59 Å (no clashes — cross-checked with an independent script after the first analyzer run produced one spurious contact).
- Cell volume recomputed from parsed cell params matches CIF value (naphthalene: 342.56 vs 342.438 Å³) — cell-matrix conversion verified.
- Two analyzer bugs were caught and fixed during the session (inconsistent unfold frames; lattice shifts as scalar lengths instead of lattice vectors — the latter only matters for monoclinic cells). Final numbers are internally consistent across the fixed script and the independent check script.

**Precision:** computed from CIF-deposited coordinates. Experimental uncertainties ~0.01 Å (4003564, modern refinement) to ~0.03–0.05 Å (2100607, large cell esds a=15.35(9)). The 0.1 Å-rounded teaching value is robust.

---

## 4. Parallel-displacement finding

**What "parallel-displaced" means quantitatively, from verified sources:**
- The displacement is real and universal: Janiak's CSD analysis (abstract, VERIFIED) says face-to-face eclipsed alignment is *rare*; the usual mode is offset stacking.
- The **~20° angle** between the ring normal and the inter-centroid vector is the abstract's CSD-statistical descriptor (VERIFIED). Measured exemplars: 13.4° (pyrene), 19.8° (phenanthrene·TCNB) — bracketing it.
- Lateral offsets measured: **0.83–1.20 Å** at centroid distances 3.55–3.58 Å.

**Recommendation for the game geometry:** do NOT attempt a per-molecule measured displacement (each Set A molecule's neat crystal is herringbone — there is no per-molecule "correct" displacement to copy). Represent displacement as **idealized pairwise geometry**: pickup placed at the stored centroid–centroid distance with its ring plane parallel to the head molecule's, displaced laterally so the ring-normal-to-centroid-vector angle ≈ **20°** (offset = d·sin 20° ≈ 1.23 Å at d = 3.6 Å), azimuth chosen consistently (e.g., along the stacking axis used by the game). Every parameter in that construction is verified: 20° (Janiak abstract), d (measured COD stacks). Alternatively represent displacement purely qualitatively (any small visible offset, labeled schematic) — human's choice in §7. The azimuth direction itself is arbitrary in the idealized model and must be labeled as such.

---

## 5. Draft DATA_SOURCES.md content (bioCHEMeleon format)

Format mirrors `tmp/bioCHEMeleon/DATA_SOURCES.md` (per-molecule sections: ID, DOI, title, authors, publication, license; per-source license blocks). **Everything below is DRAFT pending human approval (DATA-02/DATA-04).** DOIs below were read from the CIF files themselves (`_journal_paper_doi`) or registry records as noted.

```markdown
# DATA_SOURCES.md — serpentrum demo data sources & licenses (DRAFT — NOT APPROVED)

All external data sources for the serpentrum Demo Set A (aromatic π-stack).
Every PubChem CID, DOI, and COD entry is listed here with its license and
verification status. Every shipped distance must be explicitly approved by a
human before this file's status changes from DRAFT (repo hard rule; DATA-02).

STATUS LEGEND: VERIFIED = checked against a live source on 2026-09-07 with the
location recorded in .planning/phases/02-*/02-RESEARCH-demo-data.md.
UNVERIFIED = no accessible source; do not ship.

## 1. Molecule geometry files (PubChem 3D SDF) — public domain (US Gov / NCBI)

Molecule 3D structures are PubChem 3D-conformer SDF records (generated by
PubChem's OEChem pipeline), fetched from the PubChem PUG REST API:
  https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{CID}/SDF?record_type=3d
All five CIDs verified live 2026-09-07 (record downloaded, atom count matches
molecular formula). License: NCBI/PubChem — information created by or for the
US government on NCBI sites is within the public domain; acknowledgment
requested (https://www.ncbi.nlm.nih.gov/home/about/policies/, verified
2026-09-07). PubChem-specific terms apply to PubChem-hosted content.

### Benzene — CID 241  [VERIFIED]
- Formula: C6H6. 3D SDF: 12 atoms, V2000 3D record (OEChem).
### Naphthalene — CID 931  [VERIFIED]
- Formula: C10H8. 3D SDF: 18 atoms.
### Anthracene — CID 8418  [VERIFIED]
- Formula: C14H10. 3D SDF: 24 atoms.
### Phenanthrene — CID 995  [VERIFIED]
- Formula: C14H10. 3D SDF: 24 atoms.
### Biphenyl — CID 7095  [VERIFIED]
- Formula: C12H10. 3D SDF: 22 atoms. (Non-planar ground state; the game's
  stacking geometry is an idealized pairwise model, labeled as such.)

### License
Public domain (US Government, NCBI policy; acknowledgment requested). Note:
the PubChem-specific documentation page could not be fetched this session
(404); the NCBI-wide policy page is the verified source for the license
statement. Human approval covers this license note.

## 2. π-stack interaction rule + measured distances (literature + COD)

### [JAN2000] Janiak 2000 — π-stacking rule  [VERIFIED — abstract only]
- Christoph Janiak. "A critical account on π–π stacking in metal complexes
  with aromatic nitrogen-containing ligands."
  J. Chem. Soc., Dalton Trans., 2000, issue 21, 3885–3896.
- DOI: 10.1039/b003010o
- What is used from it (ABSTRACT ONLY, verified via the OpenAlex record
  W2142594455, corroborated by SciSpace snippet):
  * the usual π interaction is offset/slipped ("parallel displaced") stacking;
  * ring normal vs centroid-vector angle ≈ 20°;
  * centroid–centroid distances up to 3.8 Å;
  * face-to-face eclipsed stacking is rare.
- NOT verified (full text closed everywhere — Unpaywall 2026-09-07,
  `has_repository_copy: false`; RSC 403): any statement of a 3.3 Å lower
  bound or a 3.4 Å value. DO NOT SHIP either number unless a human verifies
  them from an authorized full-text copy.
- License: © Royal Society of Chemistry. Cited, not redistributed.

### [COD4003564] Phenanthrene·TCNB cocrystal — measured mixed π-stack  [VERIFIED]
- COD entry 4003564 (CC0 / public domain; COD header: "placed in the public
  domain by the contributors"). https://www.crystallography.net/cod/4003564.cif
- Source paper: Liu, K.; Lei, Y.; Fu, H. "A General Synthetic Strategy to a
  Library of Luminescent All-Organic Core–Shell Microstructures."
  Chemistry of Materials, 2020. DOI: 10.1021/acs.chemmater.0c01184
  (DOI read from the CIF's _journal_paper_doi; vol/pages to be added at
  data-prep from the DOI record.)
- Measured (centroid–centroid, closest six-ring pair, phenanthrene···TCNB
  stack): 3.555 Å; interplanar 3.345 Å; lateral offset 1.204 Å; plane angle
  2.7°. Measurement script + commands recorded in the research document.

### [COD2100607] / [COD2100608] Pyrene — measured homomolecular π-stack  [VERIFIED]
- COD entries 2100607 (298 K, ambient) and 2100608 (compressed).
  https://www.crystallography.net/cod/2100607.cif , .../2100608.cif
  Entry headers: IUCr-provided data — "may be used within the scientific
  community so long as proper attribution is given to the journal article"
  (we cite the article; the CIF itself is not redistributed).
- Source paper: Fabbiani, F. P. A.; Allan, D. R.; Parsons, S.; Pulham, C. R.
  "Exploration of the high-pressure behaviour of polycyclic aromatic
  hydrocarbons: naphthalene, phenanthrene and pyrene."
  Acta Crystallographica Section B, 2006, 62, 826–842.
  DOI: 10.1107/S0108768106026814
- Measured (centroid–centroid, closest six-ring pair): 2100607: 3.570 Å
  (interplanar 3.472, offset 0.829, 0.0°); 2100608: 3.580 Å (3.478, 0.851).
  Ring-centroid distance for the same-ring translation along b: 3.852 Å
  (interplanar 3.458). Measurement script + commands in the research doc.

### Herringbone reality of neat Set A crystals (context / negative evidence)  [VERIFIED]
Neat crystals of benzene, naphthalene, anthracene and phenanthrene do NOT
contain parallel-displaced π-stacks; their closest intermolecular ring
contacts are edge-to-face (herringbone-type) at 4.6–5.1 Å / 50–86°
(measured from COD 7238223 benzene 150 K (DOI 10.1039/c001190h);
2311088 naphthalene 293 K (DOI 10.1107/S2053273316018994); 5000168 anthracene
(DOI 10.1107/S0108768190008382, Brock & Dunitz, Acta Cryst. B 46, 795–806,
1990); 5000181 phenanthrene (DOI 10.1107/S0108768190007510, Petricek et al.,
Acta Cryst. B 46, 830–832, 1990)). The game therefore uses idealized pairwise
interaction geometry from the interaction literature, and says so in the
info box. (COD entries 7238223/5000168 carry clean public-domain headers;
2311088/5000181 carry IUCr attribution wording — cited, not redistributed.)

### [HS1990] Hunter & Sanders 1990 — π-interaction model  [existence VERIFIED, unread]
- Hunter, C. A.; Sanders, J. K. M. "The nature of π–π interactions."
  J. Am. Chem. Soc. 1990, 112 (14), 5525–5534. DOI: 10.1021/ja00170a016
  (verified via OpenAlex: title/venue/pages/citations; closed access, full
  text not read). Optional conceptual citation only; no number is taken
  from it unless a human verifies one from an authorized copy.

## 3. Known UNVERIFIED items (do not ship without human verification)
- "3.3–3.8 Å" as a range (3.3 lower bound): UNVERIFIED.
- "3.4 Å": UNVERIFIED — no accessible source states it.
- Biphenyl: no neat-crystal measurement available in COD (absent); biphenyl
  uses the set's generic approved rule, labeled idealized.
- PubChem-specific license page: 404 this session; NCBI policy page used.
```

---

## 6. Draft stacking-dataset JSON content (status: DRAFT)

Schema per mission (mode id, distance Å, citation short-code, one-line explanation, status) plus an explicitly-marked optional definition field (final schema is the sibling track's decision — content below is the DATA).

```json
{
  "set": "A",
  "name": "Aromatic pi-stack",
  "status": "DRAFT",
  "interactions": [
    {
      "mode_id": "pi_stack_parallel_displaced",
      "distance": 3.6,
      "distance_unit": "angstrom",
      "definition": "centroid-centroid between closest six-membered-ring pairs, planes parallel (displaced, not eclipsed)",
      "citation": "JAN2000;COD4003564;COD2100607",
      "explanation": "Aromatic rings attract face-to-face but sit slightly offset in real crystals (~20 deg off-normal); measured parallel-displaced stacks: 3.555-3.580 A; usual stacking up to 3.8 A (Janiak 2000)",
      "geometry": {"ring_normal_angle_deg": 20, "lateral_offset_angstrom": 1.23},
      "status": "DRAFT"
    }
  ],
  "applies_to_molecules": ["241", "931", "8418", "995", "7095"],
  "notes": "Idealized pairwise geometry (neat Set A crystals are herringbone - see DATA_SOURCES.md). Biphenyl non-planar in isolation; idealized stacking labeled as such."
}
```

If the human selects the exact-measured option instead, `distance` becomes `3.57` with citation `COD2100607` (and `COD4003564` as corroboration). If the plane-to-plane option is selected, `distance` becomes `3.5` with `definition` switched to "perpendicular interplanar separation" and citation `COD2100607;COD2100608`.

**xtb/clash note:** changing the placement distance from the previously-assumed 3.4 Å to 3.5–3.6 Å only *increases* clearance — the empirically verified clash-gate safety (π-stack at 3.4 Å preserved by GFN2 optimization, project research `[RUN]`) is not invalidated; re-run the Phase 5/6 smoke at the final value anyway.

---

## 7. Human-approval checklist (single decision package)

Approve each item; any NO sends the item back with the listed alternative. Nothing ships (Phase 8) without these YESes.

- [ ] **A. π-stack game value** — choose ONE:
  - **A1 (RECOMMENDED): 3.6 Å**, centroid–centroid (six-ring), parallel-displaced. Basis: three measured CC0 stacks (3.555 / 3.570 / 3.580) all round to 3.6; consistent with Janiak's ≤3.8 Å abstract rule.
  - A2: **3.57 Å** — exact measured pyrene value (COD 2100607), maximum traceability, no rounding.
  - A3: **3.5 Å** — but as *plane-to-plane* (interplanar) definition (pyrene 3.472/3.478). Note: switches the measurement definition away from the citation convention.
  - A4: keep **3.4 Å** — **only if** a human first verifies a 3.4 statement in Janiak 2000 or Hunter–Sanders full text via authorized institutional access (no accessible source states it; RSC 403; Unpaywall closed). Without that, A4 = shipping an unverified number (forbidden).
- [ ] **B. Displacement representation** — choose ONE:
  - **B1 (RECOMMENDED):** displaced geometry from verified parameters: ring-normal angle 20° (Janiak abstract) → lateral offset = d·sin 20° ≈ 1.23 Å at d=3.6; azimuth arbitrary-but-consistent, labeled idealized.
  - B2: purely qualitative displacement (small visible offset, info box says "schematic").
- [ ] **C. Definition wording** — approve "centroid–centroid between closest six-membered-ring pairs, planes parallel, displaced not eclipsed" as the dataset `definition` string (or the A3 wording).
- [ ] **D. DATA_SOURCES.md draft** (§5) — approve sources, licenses, verification notes, and the UNVERIFIED section as the shipped attribution document (status DRAFT→APPROVED).
- [ ] **E. Dataset JSON draft** (§6) — approve content (status DRAFT→APPROVED), including `applies_to` covering all five Set A CIDs.
- [ ] **F. Idealized-geometry labeling** — approve the info-box phrase stating the geometry is idealized pairwise (because neat Set A crystals are herringbone — measured fact, §2.3).
- [ ] **G. Optional (closes last gap):** if the human has institutional access to RSC/ACS, verify from the Janiak 2000 body text (a) the 3.3 Å lower bound, (b) whether any table states a 3.4 Å or similar "typical" centroid distance; record page/quote in DATA_SOURCES.md. Also optionally read Hunter–Sanders for its face-to-face distances. Skippable — A1/A2 don't depend on it.

---

## 8. Open items

1. **3.3 Å / 3.4 Å provenance** — likely lives in the Janiak 2000 body (Table/statistics) or H&S 1990; unverifiable without authorized full text. Handled by checklist item G / A4 caveat.
2. **COD entry license wording variants** — pyrene entries (2100607/8) and naphthalene 2311088 / phenanthrene 5000181 carry IUCr attribution-requested wording vs clean public-domain headers elsewhere. All are *cited*, none *redistributed* — DATA-04 compliant, but the human should bless the wording in §5 (item D).
3. **Neat biphenyl absent from COD** — biphenyl ships on the generic rule only. If a per-molecule measured anchor for biphenyl is ever wanted, a biphenyl cocrystal could be measured from COD (derivative structures exist there) — deferred; not needed for v1.
4. **Measurement scripts are in `/tmp/opencode/`** (scratch) — Appendix A embeds the final analyzer; the execution plan that creates the dataset must commit the script alongside it (traceability requirement from project research).
5. **Schema finalization** is the sibling track's call; if fields are renamed/added, map §6 content into the final schema without altering the numbers.
6. **Precision footnote** for DATA_SOURCES.md: computed distances carry experimental uncertainties of ~0.01–0.05 Å (per-entry refinement quality); at the shipped 0.1 Å rounding this is immaterial — but the note should ship with the dataset.

---

## Sources

### Primary (HIGH confidence — live-verified 2026-09-07)
- OpenAlex record W2142594455 — Janiak 2000 abstract (inverted index, reconstructed verbatim) + OA status; https://api.openalex.org/works/doi:10.1039/b003010o
- Crossref record — Janiak 2000 bibliographic metadata; https://api.crossref.org/works/10.1039/b003010o
- Unpaywall — Janiak 2000: closed, no repository copy; https://api.unpaywall.org/v2/10.1039/b003010o
- OpenAlex record — Hunter & Sanders 1990 metadata; https://api.openalex.org/works/doi:10.1021/ja00170a016
- COD entries + CIFs (CC0 site license stated on all pages): 4003564, 2100607, 2100608, 7238223, 2311088, 5000168, 5000181, 4501702 (+2100348 downloaded) — measured this session
- PubChem PUG REST — CIDs 241/931/8418/995/7095 + 3D SDFs (all verified)
- NCBI policies page — public-domain status; https://www.ncbi.nlm.nih.gov/home/about/policies/

### Secondary (MEDIUM confidence)
- SciSpace search snippet — corroborates Janiak abstract opening verbatim (page itself 405 on fetch)
- PubChem license note rests on the NCBI-wide policy page (PubChem-specific docs page 404 this session)

### Not used / not appropriate
- Sci-Hub mirrors (surfaced by search) — not used for the citation workflow; flagged for the human's optional institutional access instead.

---

## Appendix A — measurement script (final version)

`python3.6 cif_geom.py <entry>.cif` — prints molecules, six-ring counts, closest intermolecular ring-centroid contacts (d, plane angle, perpendicular separation, lateral offset) and the nearest near-parallel contact. Pure stdlib (math/re/sys/collections). Method: CIF parse → symmetry expansion (wrap to cell) → covalent clustering (fractional min-image) → per-molecule BFS unfolding in ONE consistent fractional frame → six-ring perception (DFS 6-cycles) → Newell normals → contacts over ±1 lattice images using proper lattice vectors.

```python
#!/usr/bin/env python3.6
# cif_geom.py - measure intermolecular ring-centroid contacts from a CIF.
import math, re, sys
from collections import deque, Counter

COV = {'C': 0.76, 'H': 0.31, 'N': 0.71, 'O': 0.66, 'S': 1.05, 'F': 0.57,
       'CL': 1.02, 'BR': 1.20, 'I': 1.39}

def strip_unc(v): return float(re.sub(r'\(\d+\)', '', v))

def parse_cif(path):
    lines = open(path).read().splitlines()
    tags = {}; loops = []; i = 0; n = len(lines)
    while i < n:
        line = lines[i].strip()
        if not line or line.startswith('#'): i += 1; continue
        if line.startswith(';'):
            buf = [line[1:]]; i += 1
            while i < n and not lines[i].strip().startswith(';'):
                buf.append(lines[i]); i += 1
            i += 1; continue
        if line.lower().startswith('loop_'):
            i += 1; tl = []
            while i < n and lines[i].strip().startswith('_'):
                tl.append(lines[i].strip().split()[0].lower()); i += 1
            rows = []
            while i < n:
                s = lines[i].strip()
                if (not s) or s.startswith('#') or s.startswith('_') or s.lower().startswith('loop_') or s.startswith('data_'):
                    break
                toks = re.findall(r"'[^']*'|\"[^\"]*\"|\S+", s)
                rows.append([t.strip("'\"") for t in toks]); i += 1
            loops.append((tl, rows)); continue
        if line.startswith('_'):
            parts = line.split(None, 1); key = parts[0].lower()
            if len(parts) == 1:
                i += 1
                if i < n and lines[i].strip().startswith(';'):
                    buf = [lines[i].strip()[1:]]; i += 1
                    while i < n and not lines[i].strip().startswith(';'):
                        buf.append(lines[i]); i += 1
                    tags[key] = '\n'.join(buf); i += 1
                elif i < n:
                    tags[key] = lines[i].strip().strip("'\""); i += 1
            else:
                tags[key] = parts[1].strip().strip("'\""); i += 1
            continue
        i += 1
    return tags, loops

def get_symops(tags, loops):
    ops = []
    for tl, rows in loops:
        for cand in ('_symmetry_equiv_pos_as_xyz', '_space_group_symop_operation_xyz'):
            if cand in tl:
                k = tl.index(cand)
                for r in rows:
                    if len(r) > k: ops.append(r[k].replace(' ', '').lower())
    if not ops: raise SystemExit('no symmetry ops found')
    return ops

def eval_frac(s):
    if '/' in s:
        a, b = s.split('/'); return float(a) / float(b)
    return float(s)

def op_parse(s):
    comps = s.split(',')
    mat = [[0.0]*3 for _ in range(3)]; tr = [0.0]*3
    for r, comp in enumerate(comps):
        for t in re.findall(r'[+-]?[^+-]+', comp):
            sign = 1.0
            if t.startswith('+'): t = t[1:]
            elif t.startswith('-'): sign = -1.0; t = t[1:]
            m = re.match(r'^([0-9./]*)\*?([xyz])$', t)
            if m:
                coef = eval_frac(m.group(1)) if m.group(1) else 1.0
                mat[r]['xyz'.index(m.group(2))] += sign * coef
            else:
                tr[r] += sign * eval_frac(t)
    return mat, tr

def apply_op(mat, tr, f):
    return [mat[r][0]*f[0]+mat[r][1]*f[1]+mat[r][2]*f[2]+tr[r] for r in range(3)]

def cell_matrix(a, b, c, al, be, ga):
    al, be, ga = map(math.radians, (al, be, ga))
    ca, cb, cg = math.cos(al), math.cos(be), math.cos(ga); sg = math.sin(ga)
    v = math.sqrt(1-ca*ca-cb*cb-cg*cg+2*ca*cb*cg)
    return [[a,0,0],[b*cg,b*sg,0],[c*cb,c*(ca-cb*cg)/sg,c*v/sg]]

def frac2cart(M, f):
    return [M[0][0]*f[0]+M[1][0]*f[1]+M[2][0]*f[2],
            M[1][1]*f[1]+M[2][1]*f[2], M[2][2]*f[2]]

def sub(u, v): return [u[0]-v[0], u[1]-v[1], u[2]-v[2]]
def dot(u, v): return u[0]*v[0]+u[1]*v[1]+u[2]*v[2]
def norm(u): return math.sqrt(dot(u, u))
def unit(u):
    n = norm(u); return [u[0]/n, u[1]/n, u[2]/n]

def frac_mindelta(fj, fi):
    d = [fj[k]-fi[k] for k in range(3)]
    for k in range(3): d[k] -= round(d[k])
    return d

def newell_normal(pts):
    nx = ny = nz = 0.0; k = len(pts)
    for i in range(k):
        p, q = pts[i], pts[(i+1) % k]
        nx += (p[1]-q[1])*(p[2]+q[2]); ny += (p[2]-q[2])*(p[0]+q[0]); nz += (p[0]-q[0])*(p[1]+q[1])
    return unit([nx, ny, nz])

def canon(cyc):
    rots = []
    for r in range(len(cyc)):
        c = cyc[r:]+cyc[:r]; rots.append(tuple(c)); rots.append(tuple(reversed(c)))
    return min(rots)

def main(path):
    tags, loops = parse_cif(path)
    a=strip_unc(tags['_cell_length_a']); b=strip_unc(tags['_cell_length_b']); c=strip_unc(tags['_cell_length_c'])
    al=strip_unc(tags['_cell_angle_alpha']); be=strip_unc(tags['_cell_angle_beta']); ga=strip_unc(tags['_cell_angle_gamma'])
    M = cell_matrix(a,b,c,al,be,ga)
    avec=frac2cart(M,[1,0,0]); bvec=frac2cart(M,[0,1,0]); cvec=frac2cart(M,[0,0,1])
    ops = [op_parse(s) for s in get_symops(tags, loops)]
    atoms = []
    for tl, rows in loops:
        if '_atom_site_fract_x' in tl:
            ix=tl.index('_atom_site_fract_x'); iy=tl.index('_atom_site_fract_y'); iz=tl.index('_atom_site_fract_z')
            il=tl.index('_atom_site_label') if '_atom_site_label' in tl else None
            it=tl.index('_atom_site_type_symbol') if '_atom_site_type_symbol' in tl else None
            io=tl.index('_atom_site_occupancy') if '_atom_site_occupancy' in tl else None
            for r in rows:
                lab = r[il] if il is not None else 'X'
                el = re.sub(r'[^A-Za-z]','',r[it]).upper() if it is not None else re.sub(r'[^A-Za-z]','',lab).upper()[:2]
                if el not in COV: el = el[:1]
                occ = strip_unc(r[io]) if io is not None else 1.0
                atoms.append((lab, el, [strip_unc(r[ix]),strip_unc(r[iy]),strip_unc(r[iz])], occ))
            break
    print('cell: a=%.4f b=%.4f c=%.4f al=%.2f be=%.2f ga=%.2f  Z=%s  T=%s' %
          (a,b,c,al,be,ga,tags.get('_cell_formula_units_z','?'),tags.get('_cell_measurement_temperature','?')))
    occs = set(o for _,_,_,o in atoms)
    if any(o < 0.99 for o in occs): print('WARNING: partial occupancies: %s' % sorted(occs))
    expanded = []; seen = set()
    for lab, el, f, occ in atoms:
        for oi,(mat,tr) in enumerate(ops):
            g = apply_op(mat,tr,f); w = tuple(x % 1.0 for x in g)
            key = (el,)+tuple(round(x,3) for x in w)
            if key in seen: continue
            seen.add(key); expanded.append((el, list(w)))
    n_at = len(expanded)
    parent = list(range(n_at))
    def find(x):
        while parent[x]!=x: parent[x]=parent[parent[x]]; x=parent[x]
        return x
    bonds = []
    for i in range(n_at):
        ei = expanded[i][0]
        if ei not in COV: continue
        for j in range(i+1,n_at):
            ej = expanded[j][0]
            if ej not in COV or (ei=='H' and ej=='H'): continue
            df = frac_mindelta(expanded[j][1], expanded[i][1])
            if norm(frac2cart(M,df)) < (COV[ei]+COV[ej])*1.25:
                bonds.append((i,j,df)); ri,rj=find(i),find(j)
                if ri!=rj: parent[rj]=ri
    mols = {}
    for i in range(n_at): mols.setdefault(find(i),[]).append(i)
    moladj = {root:{} for root in mols}
    for i,j,df in bonds:
        if find(i)==find(j):
            moladj[find(i)].setdefault(i,[]).append((j,df))
            moladj[find(i)].setdefault(j,[]).append((i,[-x for x in df]))
    molinfo = {}
    for root, idxs in mols.items():
        fpos = {idxs[0]: list(expanded[idxs[0]][1])}; dq = deque([idxs[0]])
        while dq:
            u = dq.popleft()
            for v, df in moladj[root].get(u, []):
                if v not in fpos:
                    fpos[v] = [fpos[u][k]+df[k] for k in range(3)]; dq.append(v)
        pos = {i: frac2cart(M,fpos[i]) for i in idxs}
        cnt = Counter(expanded[i][0] for i in idxs)
        formula = ''.join('%s%d'%(e,cnt[e]) for e in sorted(cnt))
        cen = [sum(p[k] for p in pos.values())/len(pos) for k in range(3)]
        molinfo[root] = {'pos': pos, 'centroid': cen, 'formula': formula}
    print('molecules in cell: %d' % len(mols))
    for root in sorted(molinfo): print('  mol %d: %s' % (root, molinfo[root]['formula']))
    rings = {}; ring_seen = set()
    for root, mi in molinfo.items():
        cidx = [i for i in mi['pos'] if expanded[i][0]=='C']
        cadj = {i:[] for i in cidx}
        for ii in range(len(cidx)):
            for jj in range(ii+1,len(cidx)):
                i,j = cidx[ii],cidx[jj]
                if norm(sub(mi['pos'][j],mi['pos'][i])) < 1.9:
                    cadj[i].append(j); cadj[j].append(i)
        csetm = set(cidx)
        def find_cycles(st):
            out = []; path = [st]
            def dfs(cur, dep):
                if dep == 6:
                    if st in cadj[cur]: out.append(list(path))
                    return
                for nx in cadj[cur]:
                    if nx in path or nx not in csetm: continue
                    path.append(nx); dfs(nx, dep+1); path.pop()
            dfs(st, 1); return out
        for st in cidx:
            for cyc in find_cycles(st):
                key = canon(cyc)
                if key in ring_seen: continue
                ring_seen.add(key); rings[len(rings)] = (root, list(key))
    ringdata = {}
    for rid,(root,ats) in rings.items():
        pts = [molinfo[root]['pos'][i] for i in ats]
        cen = [sum(p[k] for p in pts)/len(pts) for k in range(3)]
        ringdata[rid] = (cen, newell_normal(pts), root)
    print('six-rings per molecule: %s' % {k:v for k,v in sorted(Counter(r[0] for r in rings.values()).items())})
    contacts = []
    for A in sorted(molinfo):
        for B in sorted(molinfo):
            for na in (-1,0,1):
                for nb in (-1,0,1):
                    for nc in (-1,0,1):
                        if A==B and na==0 and nb==0 and nc==0: continue
                        shift = [na*avec[k]+nb*bvec[k]+nc*cvec[k] for k in range(3)]
                        cenA_m = molinfo[A]['centroid']; cenB_m = molinfo[B]['centroid']
                        if norm([cenB_m[k]+shift[k]-cenA_m[k] for k in range(3)]) > 12.0: continue
                        for ridA,(cenA_,nA,rootA) in ringdata.items():
                            if rootA != A: continue
                            for ridB,(cenB_,nB,rootB) in ringdata.items():
                                if rootB != B: continue
                                cenB2 = [cenB_[k]+shift[k] for k in range(3)]
                                dv = sub(cenB2,cenA_); d = norm(dv)
                                if d > 8.0: continue
                                ang = math.degrees(math.acos(max(-1.0,min(1.0,abs(dot(nA,nB))))))
                                perp = abs(dot(dv,nA)); off = math.sqrt(max(0.0,d*d-perp*perp))
                                contacts.append({'A':A,'B':B,'n':(na,nb,nc),'rA':ridA,'rB':ridB,
                                                 'd':d,'ang':ang,'perp':perp,'off':off})
    uniq = {}
    for ct in contacts:
        k1 = (ct['A'],ct['B'],ct['n'],ct['rA'],ct['rB'])
        k2 = (ct['B'],ct['A'],tuple(-x for x in ct['n']),ct['rB'],ct['rA'])
        k = min(k1,k2)
        if k not in uniq or ct['d'] < uniq[k]['d']: uniq[k] = ct
    final = sorted(uniq.values(), key=lambda x: x['d'])
    groupmin = {}
    for ct in final:
        nn = tuple(-x for x in ct['n'])
        gk = ((ct['A'],ct['n']),(ct['B'],nn)) if (ct['A'],ct['n']) <= (ct['B'],nn) else ((ct['B'],nn),(ct['A'],ct['n']))
        if gk not in groupmin or ct['d'] < groupmin[gk]['d']: groupmin[gk] = ct
    final = sorted(groupmin.values(), key=lambda x: x['d'])
    print('\nclosest intermolecular ring-centroid contacts (unique, d<8 A):')
    print('%-4s %-4s %-10s %-8s %-8s %-8s %-8s' % ('A','B','n(img)','d/A','ang','perp/A','off/A'))
    for ct in final[:14]:
        print('%-4d %-4d %-10s %-8.3f %-8.1f %-8.3f %-8.3f' % (ct['A'],ct['B'],str(ct['n']),ct['d'],ct['ang'],ct['perp'],ct['off']))
    para = [c for c in final if c['ang'] < 15.0]
    if para:
        best = para[0]
        print('\nnearest near-parallel (angle<15 deg) ring-centroid contact:')
        print('  d=%.3f A  perp=%.3f A  offset=%.3f A  angle=%.1f deg  mols %d-%d img %s' %
              (best['d'],best['perp'],best['off'],best['ang'],best['A'],best['B'],best['n']))
    else:
        print('\nno near-parallel ring-centroid contact under 8 A')
    if final:
        print('shortest contact overall: d=%.3f A ang=%.1f deg' % (final[0]['d'], final[0]['ang']))

if __name__ == '__main__':
    main(sys.argv[1])
```

---

*Research completed: 2026-09-07. All numbers above are either quoted with an exact verifiable location or explicitly marked UNVERIFIED. Nothing in this document ships without human approval (§7).*

## RESEARCH COMPLETE
