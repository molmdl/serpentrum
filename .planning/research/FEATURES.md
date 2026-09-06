# Feature Research

**Domain:** Educational molecular-viewer game (PyMOL plugin) — snake gameplay + molecular stacking + spectra payoff
**Researched:** 2026-09-06
**Confidence:** MEDIUM-HIGH (game conventions and chemistry data sources HIGH; specific stacking distance numbers MEDIUM — see verification flags)

**Verification method note:** All chemistry claims below were checked against live sources on 2026-09-06: PubChem PUG REST (CID lookups + 3D SDF download tested), Crossref/OpenAlex/Semantic Scholar (DOI registry lookups), COD (crystallography.net live searches), CCDC Access Structures (page fetched). Claims I could NOT confirm from a source are explicitly marked **UNVERIFIED**. Nothing in this document should be redistributed as-is; every citation requires explicit human approval before it ships in DATA_SOURCES.md (repo constraint).

---

## Feature Landscape

### Table Stakes (Users Expect These)

Snake-genre conventions verified against the genre's documented history (Wikipedia "Snake (video game genre)"; Blockade 1976 → Nokia 1998 lineage):

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Forward-only movement, steered by 4 arrow keys, cannot stop | Defining trait of the genre since Blockade (1976); Wikipedia-documented | LOW | Already in spec; arrow-key capture inside PyMOL OpenGL viewer is the real work (focus/keyboard handling) |
| Eating = growth | Core snake loop; "item eaten → snake gets longer" is the universal convention | LOW | Growth here = molecule stacked onto chain (already in spec) |
| Boundary collision ends the run | Present in essentially all snake implementations | LOW | Spec already has it; PyMOL must draw the box clearly |
| Self-collision ends the run | Genre-defining tension; difficulty grows with length | MEDIUM | Self-collision detection in 3D is harder than 2D grid; see DESIGN flag below |
| Countdown before play | Standard in arcade-style games; spec already has 3-2-1 | LOW | |
| Pause/resume + restart mid-game | Expected in any game with a timer | LOW | Already in spec |
| Live score + progress-to-win (molecules remaining) | Standard HUD | LOW | Already in spec (molecules-remaining-before-win) |
| Clear boundary + readable object states (head vs pickups) | Player must parse the scene instantly | MEDIUM | Spec: head=spheres, pickups=sticks; needs visual-distinctness testing in PyMOL |
| Setup persistence (save/load) | Any configurable tool is expected to remember configuration | LOW | Already in spec |
| Installs as a standard PyMOL plugin | PyMOL users expect Plugin Manager install | LOW | Already in spec |
| Attribution visible in-app or in a doc | Educational tools are expected to cite data sources; bioCHEMEleon's DATA_SOURCES.md is the repo's own precedent | LOW | Format mirror: `tmp/bioCHEMeleon/DATA_SOURCES.md` (read; structure verified) |

Chemistry-credibility table stakes (what makes it feel *scientific* rather than reskinned snake):

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Placed stacking geometry actually equals the cited distance | If the info box says "π-stack, 3.4 Å" the molecules must be at 3.4 Å — educators will measure | MEDIUM | Apply the interaction transform (translate/rotate pickup onto stack position) deterministically from the dataset's stored geometry |
| Known interaction mode per pickup (name + rule + source) | The educational claim IS the feature | LOW | Data ships with the demo sets: mode, distance, citation per molecule pair |
| Molecule files from a verifiable database | Repo constraint: no invented data | LOW | PubChem 3D SDF pipeline **verified working live** (CID 241 fetched: valid 3D V2000 record, 12 atoms) |
| Honest failure mode when data is missing | An educational tool must not silently invent chemistry | LOW | If no stacking entry exists for a pickup: skip it, or use only user-approved fallback (see Anti-Features) |

### Differentiators (Competitive Advantage)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Real interaction geometry as gameplay | No other chemistry snake game teaches *interactions* with real distances — closest verified prior art (Snakeleev, J. Chem. Educ. 2025, DOI 10.1021/acs.jchemed.5c00029) teaches element *identification* with no geometry | MEDIUM | This is the project's core idea; keep it central in messaging and UI |
| IR spectrum of the molecule *the player assembled* | Unique payoff: a computed physical observable of the player's own construction. Snakeleev/Foldit/Happy Atoms offer no such artifact | HIGH | Already in spec (xtb opt + hessian → broadened IR); the differentiator framing matters for educators |
| Clickable frequency table → vectors drawn in the 3D viewer | Connects "peak on a plot" ↔ "atoms that move" — a known student difficulty in IR spectroscopy | MEDIUM | Already in spec (static vectors, no animation in v1) |
| Per-pickup chemistry info (rolling info box) | Each pickup is a micro-lesson: interaction name, distance used, one-line why, citation short-code | LOW | Spec has "generic rolling info box"; this fills it with structured content |
| Crashed snake still yields a spectrum | Every run ends in a physical result — keeps the payoff reachable (already a stated key decision) | LOW | |
| Educator shareable setups | Setup save/load files double as lesson plans (a teacher ships the class a .setup file) | LOW | Zero extra build cost beyond spec — just document the use |
| Game cap as an explicit computational budget (atoms + warning) | Teaches cost-of-computation (hessian ~N³ scaling); rare in games, valuable in classrooms | LOW | Already in spec (~10 mol / ~100 atoms default) |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Vibrational-mode animation | "Vectors are hard to read" | Spec explicitly defers (v1 static vectors); animation adds a timeline/rendering subsystem with real complexity in a Qt+OpenGL plugin | Static vectors + frequency-table highlight (v1); animation as v2 candidate |
| Physics-based self-assembly at pickup time (simulate relaxation as you stack) | Sounds like "real science" | Force-field relaxation per pickup = slow, nondeterministic gameplay, and it pre-empts the xtb payoff at the end; geometry must stay faithful to the *cited* distance, not a force field's whim | Deterministic placement at the cited geometry; the "real physics" is the end-of-run xtb relaxation + spectrum |
| Live spectrum preview during gameplay | "See it build up" | Hessian cost grows ~N³; kills frame rate and the atom budget; scope explosion | Spectrum only after completion (spec) |
| Silent fallback stacking for molecules without known modes | Lets any molecule set "just work" | Violates the no-invented-data constraint; an educational tool teaching a made-up distance is worse than one that refuses | Explicit, user-approved fallback list (e.g., generic van-der-Waals contact) — flagged as an OPEN requirement question |
| Reproducing real crystal packing (herringbone etc.) | "The crystal is the truth" | Snake chains need a consistent, steerable stacking rule; crystal packing of simple aromatics is edge-to-face dominated (flagged UNVERIFIED below) and would make chains geometrically chaotic | Idealized pairwise interaction geometry from the interaction literature, clearly labeled as such in the info box |
| Multiplayer / .io variants | Genre familiarity | Network stack + scope far beyond a classroom plugin | Single-player with timer (spec) |
| Raman/UV-Vis/NMR tabs | More spectroscopy = more teaching | v1 scope: IR only (spec); extra spectra multiply the xtb/output-format work | One spectrum done well |
| Auto-detected stacking for arbitrary user uploads | Convenience | Stacking data for arbitrary molecules cannot be database-verified — collides with the attribution constraint | Allow upload for *geometry* (size-checked), but require the user to either pick an approved interaction rule or accept an approved generic fallback |

## Feature Dependencies

```
[PubChem-sourced molecule files (SDF)]
    └──requires──> [Verified CID table + download pipeline]   (VERIFIED live)
                        └──requires──> [DATA_SOURCES.md attribution format]  (bioCHEMEleon precedent)

[Stacking placement]
    └──requires──> [Interaction dataset: mode + distance + citation per pair]
                        └──requires──> [Verified distance numbers]  (partially VERIFIED — see Demo Sets)
                        └──requires──> [Human approval of every citation]  (repo constraint)

[Stacking placement] ──enhances──> [Rolling info box]  (info box reads the same dataset)

[IR spectrum payoff]
    └──requires──> [Completed snake]  (win or crash)
    └──requires──> [Atom-count cap + warning]  (guards hessian cost)

[Clickable frequency table]
    └──requires──> [IR spectrum calculation]
    └──requires──> [Vibrational vectors parsed from xtb output]  (STACK researcher's domain)

[Snake self-collision detection] ──conflicts──> [Molecules at realistic inter-molecular spacing]
    (a snake of molecules with real vdW radii is mostly one big blob; collision must use
     head-centroid proximity to chain segments, not atom-level overlap — DESIGN decision needed)
```

### Dependency Notes

- **Stacking placement requires the interaction dataset:** the dataset is the single source of truth for both the game transform and the info-box text — build it as data, not code.
- **IR payoff requires the cap:** without the atom-budget guard, an ambitious player waits ~forever for a hessian; the cap is what makes the promise "every run ends in a spectrum" deliverable.
- **Self-collision conflicts with realistic spacing:** if molecules are placed at true stacking distances (~3.4 Å between centroids), atom-level collision tests fire constantly. Collision should be segment-based (head vs chain segments with a tuned radius). This is a design decision to settle at requirements time.

## MVP Definition

### Launch With (v1)

Matches spec; features research adds nothing mandatory beyond spec except content design for the info box and demo-set data packaging.

- [ ] Setup tab: demo-set dropdown (≥1 shipped set), box size presets, head choice, xtb path, cap with warning — spec
- [ ] 6-button action row — spec
- [ ] Game tab: info box, timer, molecules-remaining, pause, restart — spec
- [ ] Gameplay: boundary display, sphere head, stick pickups, arrow-key steering, deterministic stacking at cited distance, collision → game over, win at cap — spec
- [ ] Completion → snake shown, score = molecule count, "Get Spectra" — spec
- [ ] Spectra tab: xtb opt + hessian → broadened IR plot (Gaussian), progress log, plot save, frequency table with click→vectors — spec
- [ ] **Demo set A or B shipped with: molecule SDFs (PubChem, CID-cited), interaction dataset (mode + distance + citation), DATA_SOURCES.md** — this research's data chain (see Demo Sets section)
- [ ] Info box structured content: interaction name + distance + one-liner + citation short-code — fills the spec's "generic rolling info box"

### Add After Validation (v1.x)

- [ ] Additional demo sets (Set C/D from below) — trigger: Set A/B validated with students
- [ ] In-plugin link to DATA_SOURCES.md / per-molecule source popup — trigger: educator feedback requests provenance in-app
- [ ] Optional stacking fallback list (user-approved, e.g. generic contact distance) — trigger: user-upload feature needs it
- [ ] Vibrational-mode animation — trigger: educator demand after static vectors ship
- [ ] Speed increases with snake length — classic convention (BBC Micro Snake, 1982, Wikipedia-verified); trigger: playtesters find constant speed too easy

### Future Consideration (v2+)

- [ ] User molecule-upload workflow with approved-fallback rules — why defer: needs its own approval workflow design
- [ ] Mixed-interaction sets (chain alternates π-stack / H-bond links) — why defer: multiplies dataset validation work
- [ ] Raman (xtb can provide it) — why defer: IR first, per spec
- [ ] Quiz gates / scoring by chemistry knowledge — why defer: gamification depth after core loop validated (Snakeleev's "diets" model is the precedent to study)

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Core snake loop in PyMOL viewer | HIGH | MEDIUM | P1 |
| Deterministic stacking at cited geometry | HIGH | MEDIUM | P1 |
| Demo set with verified data + attribution | HIGH | MEDIUM (data prep + approval) | P1 |
| IR spectrum + broadened plot | HIGH | MEDIUM-HIGH | P1 |
| Frequency table → vectors | MEDIUM-HIGH | MEDIUM | P1 |
| Structured info-box content | MEDIUM | LOW | P1 |
| Cap + atom-budget warning | MEDIUM | LOW | P1 |
| Save/load setups (educator sharing) | MEDIUM | LOW | P2 |
| More demo sets | MEDIUM | MEDIUM | P2 |
| Mode animation | MEDIUM | MEDIUM-HIGH | P3 |
| Speed scaling | LOW-MEDIUM | LOW | P3 |
| Upload + fallback rules | MEDIUM | MEDIUM-HIGH | P3 |

## Competitor Feature Analysis

| Feature | Snakeleev (verified) | Foldit (verified) | Happy Atoms (site verified only) | serpentrum (plan) |
|---------|---------------------|-------------------|----------------------------------|-------------------|
| Snake mechanic | ✓ apples→elements | ✗ | ✗ | ✓ molecules |
| What you learn | Element identification + classification ("diets") | Protein folding / structure | Molecular building + polarity | Noncovalent interactions + spectra |
| 3D molecular viewer | ✗ (2D) | ✓ (custom) | partial (AR companion) | ✓ PyMOL OpenGL |
| Real interaction geometry | ✗ | ✓ (folding energy) | ✗ | ✓ cited distances |
| Computed physical observable | ✗ | partial (game energy scores) | ✗ | ✓ IR spectrum of YOUR assembly |
| Peer-reviewed learning outcome | ✓ Cohen's d 1.23–2.67, >90% engagement | ✓ Nature 2010 paper | unverified | (aspiration) |
| Audience fit | Students (general chemistry) | Citizen scientists | Younger students | Students + educators in molecular modeling courses |

**Reading:** serpentrum occupies an empty cell — *snake gameplay + real 3D molecular geometry + a computed spectrum payoff*. Snakeleev proves the genre-education marriage works and publishes well (J. Chem. Educ. 2025, CC-BY). Foldit proves "game actions produce a real scientific artifact" motivates. serpentrum's plan combines both mechanisms at small-molecule scale.

**Snakeleev design elements worth borrowing (from its verified abstract):** thematic framing ("diets" → for serpentrum: interaction families per set), measurable pre/post learning gains, short-session design (largest gains in first 10 minutes → keep default cap low so a run is minutes, not tens of minutes).

## Demo Molecule Sets (requested proposals)

> Data-chain verification status: **PubChem CID lookups + 3D SDF download: VERIFIED working live** (2026-09-06). **COD formula/text search: VERIFIED working live** (returns entries for every formula tested). **COD per-entry CIF content: URL pattern known, individual entries NOT yet inspected** (measurement deferred to data-prep). **CCDC Access Structures: free but CAPTCHA-gated manual access; bulk/programmatic access requires a licensed CSD System** (verified from CCDC page text) — cite CSD-derived *published* values, never redistribute CSD data. **RCSB PDB: CC0 per policy** (per bioCHEMEleon DATA_SOURCES.md precedent).

### Verified literature anchors for ALL sets

| Claim | Status | Source |
|-------|--------|--------|
| π–π stacking is usually offset/slipped (parallel-displaced), not face-to-face full-overlap | **VERIFIED** (abstract, CSD-based analysis) | Janiak 2000, *J. Chem. Soc., Dalton Trans.*, DOI 10.1039/b003010o (Crossref + OpenAlex, ~4,500 citations) |
| Ring normals of stacked partners form ~20° angles; centroid–centroid distances **up to 3.8 Å** | **VERIFIED** (abstract) | same |
| Face-to-face stacked dimers are rare in crystals; some "π-stacking" claims are actually C–H···π | **VERIFIED** (abstract) | same |
| The standard geometric/electrostatic model of π–π interactions | **VERIFIED existence** (DOI + title + venue + ~5,000 cites); full text NOT read — model details MEDIUM confidence | Hunter & Sanders 1990, *J. Am. Chem. Soc.*, DOI 10.1021/ja00170a016 |
| The accepted definition of the hydrogen bond (with distance/angle criteria as evidence categories, not hard cutoffs) | **VERIFIED existence** (DOI + title + author list); numeric criteria NOT read from full text | Arunan et al., "Definition of the hydrogen bond (IUPAC Recommendations 2011)", DOI 10.1351/PAC-REC-10-01-02 |
| "Typical π-stack centroid distance ≈ 3.3–3.8 Å" (the commonly quoted range) | **UNVERIFIED** — lower bound 3.3 Å is in the Janiak body text, which I could not access (RSC 403). Upper bound 3.8 Å VERIFIED via abstract. Verify full text before shipping any number. | Janiak 2000 (same DOI) |
| Neat crystals of benzene/naphthalene/anthracene pack herringbone (edge-to-face) rather than as ideal π-stacks | **UNVERIFIED** here (textbook knowledge; CIF measurement deferred to data-prep by decision). Design implication regardless: the game uses *idealized pairwise interaction geometry*, labeled as such — not crystal-packing reproduction. | — |

### Set A — "Aromatic π-stack" family

| Molecule | PubChem CID | Formula | Status |
|----------|-------------|---------|--------|
| Benzene | 241 | C6H6 | **VERIFIED** (live lookup) |
| Naphthalene | 931 | C10H8 | **VERIFIED** |
| Anthracene | 8418 | C14H10 | **VERIFIED** |
| Phenanthrene | 995 | C14H10 | **VERIFIED** |
| Biphenyl (optional; non-planar ground state) | 7095 | C12H10 | **VERIFIED** |

- Ring counts: 1/2/3/3(±2) — within the ≤3-ring constraint ✓
- Molecule geometry: PubChem 3D SDF per CID (**pipeline VERIFIED**; per-CID 3D-record coverage to confirm at data-prep — benzene confirmed, others presumed)
- Stacking data: Janiak 2000 CSD-derived rules (see anchors table). The dataset ships *prescribed* geometry, e.g. "parallel-displaced π–π, centroid–centroid 3.4 Å, ring-normal angle ~20°" — **the 3.4 Å specific value is UNVERIFIED until data-prep pins it** (from Janiak full text, or measured from a stacked crystal's COD/CSD entry, or quoted from Hunter–Sanders full text)
- HUMAN APPROVAL REQUIRED before shipping (repo constraint).

### Set B — "Carboxylic-acid H-bond" family

| Molecule | PubChem CID | Formula | Status |
|----------|-------------|---------|--------|
| Formic acid | 284 | CH2O2 | **VERIFIED** |
| Acetic acid | 176 | C2H4O2 | **VERIFIED** |
| Benzoic acid | 243 | C7H6O2 | **VERIFIED** |

- Interaction: carboxylic-acid dimer as the chain link (two O–H···O hydrogen bonds).
- Data: IUPAC H-bond definition (DOI VERIFIED, existence); the dimer motif's existence in crystals and its O···O distance are to be **measured from a COD entry at data-prep** (COD search for C7 H6 O2 VERIFIED to return hundreds of entries; per-entry inspection pending). The commonly quoted O···O ≈ 2.6–2.7 Å is **UNVERIFIED here — do not ship until measured/cited**.
- Note: formic/acetic acids crystallize with dimers AND catemer chains in the literature — **which motif the game uses is a data-prep decision from the actual COD/CSD entry chosen**.

### Set C — "Heteroaromatic" family

| Molecule | PubChem CID | Formula | Status |
|----------|-------------|---------|--------|
| Pyridine | 1049 | C5H5N | **VERIFIED** |
| Pyrazine | 9261 | C4H4N2 | **VERIFIED** |
| Furan | 8029 | C4H4O | **VERIFIED** |
| Thiophene | 8030 | C4H4S | **VERIFIED** |
| 1,3,5-Triazine | 9262 | C3H3N3 | **VERIFIED** |
| Imidazole (bonus: N–H donor) | 795 | C3H4N2 | **VERIFIED** |

- Data: Janiak 2000 is *specifically about aromatic nitrogen-containing ligands* — the most on-point literature anchor for this set (**VERIFIED** for its qualitative rules).
- Imidazole N–H···N chains: chemically well-known directionally, but **specific distances UNVERIFIED here** — pin from COD CIF at data-prep.
- C–H···N contact distances: **UNVERIFIED** — same treatment.

### Set D — "Hydroxyl H-bond chain" family

| Molecule | PubChem CID | Formula | Status |
|----------|-------------|---------|--------|
| Phenol | 996 | C6H6O | **VERIFIED** |
| Hydroquinone | 785 | C6H6O2 | **VERIFIED** |
| Urea | 1176 | CH4N2O | **VERIFIED** |

- Data: O–H···O chain distances to be pinned from COD entries at data-prep (**UNVERIFIED here**). IUPAC definition anchor applies.
- Caveat: hydroquinone also forms π-stacked/co-crystal arrangements (quinhydrone) — **UNVERIFIED here**, treat as a data-prep discovery item, not a claim.

### Data-prep checklist derived from this research (feeds DEMO phase)

1. Pin the exact π-stack distance/angle values from Janiak full text (or a stacked crystal's database entry) → then human approval.
2. For each set: choose one specific COD/CSD entry per interaction, record entry ID + DOI, measure the distance from the CIF, ship the number with the measurement script for traceability.
3. Confirm PubChem 3D SDF availability for every chosen CID (benzene verified; rest presumed).
4. Write DATA_SOURCES.md in the bioCHEMEleon format (structure verified from `tmp/bioCHEMeleon/DATA_SOURCES.md`): source DB, ID, DOI, license, attribution line per molecule and per interaction citation.
5. Do NOT redistribute CSD (CCDC) data files; cite CSD-derived published values only. COD is CC0 (verified) — prefer COD for anything redistributed.

## Educational Scaffolding (info-box content design)

Snakeleev evidence (verified abstract): learning gains concentrate in the first 10 minutes; thematic framing (real-world "diets") drives engagement and classification learning. Implication: serpentrum's info box should deliver small, structured, per-event facts rather than paragraphs.

Proposed info-box rotation content (each ≤2 lines):

1. **Per pickup (event-driven):** "+1 Naphthalene — π-stack, parallel-displaced, 3.4 Å (Janiak 2000)" — the exact interaction the placement used. Single source of truth = interaction dataset.
2. **Idle rotation (chemistry tips):** one-liner per interaction family in the active set ("Aromatic rings attract face-to-face; in real crystals they sit slightly offset ~20°"). Sourced from the same verified anchors.
3. **Controls hints:** early-game reminders (arrow keys = steer; P = pause) — fades after first successful pickups.
4. **End-of-run summary:** snake length, molecule count, interaction breakdown (e.g., "12 π-stacks, 3 H-bond links"), then the spectra hand-off sentence.
5. **Spectra tab primer (once per session):** "Peaks = vibrations. Click a row to see which atoms move." — connects plot↔geometry, the documented student difficulty.

Sufficiency principle (repo UI constraint): every screen shows *what to do next*; chemistry depth lives in the dataset + DATA_SOURCES.md, surfaced on demand, not walls of text.

## MVP Recommendation

For MVP, prioritize (beyond spec):

1. **Demo Set A or B fully data-verified and shipped** — the demo set is the product's scientific credibility; one set done right beats three done loosely.
2. **Structured info-box content wired to the interaction dataset** — LOW cost, HIGH educational value.
3. **Snakeleev-style short-session tuning** — low default cap (~10 molecules) so a run + spectrum fits ~10 minutes; largest learning gains happen there.

Defer to post-MVP: additional sets, mode animation, upload-with-fallback, speed scaling.

## Sources

**Chemistry / data (all verified live 2026-09-06):**
- PubChem PUG REST: CID lookups + 3D SDF (`https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/241/SDF?record_type=3d` returned a valid 3D V2000 record for benzene)
- Janiak, C. *J. Chem. Soc., Dalton Trans.* 2000. DOI 10.1039/b003010o — Crossref record + OpenAlex abstract (CSD-based; parallel-displaced; ~20°; ≤3.8 Å; face-to-face rare)
- Hunter, C. A.; Sanders, J. K. M. *J. Am. Chem. Soc.* 1990. DOI 10.1021/ja00170a016 — Crossref record (~5,000 citations)
- Arunan, E. et al. "Definition of the hydrogen bond (IUPAC Recommendations 2011)". DOI 10.1351/PAC-REC-10-01-02 — Semantic Scholar record
- COD (Crystallography Open Database), crystallography.net — live, CC0, 534,911 entries; formula searches C10H8 / C14H10 / C7H6O2 all returned entries
- CCDC Access Structures (ccdc.cam.ac.uk/structures/) — free manual access, CAPTCHA-gated; systematic access = licensed CSD System (verified from page text)
- RCSB PDB CC0 policy — per bioCHEMEleon DATA_SOURCES.md precedent (local file read)

**Games / education:**
- Galizia, P. "Snakeleev: A Gamified Serious Game for Learning the Periodic Table". *J. Chem. Educ.* 2025. DOI 10.1021/acs.jchemed.5c00029 — Semantic Scholar record with full abstract (CC-BY OA; Cohen's d 1.23–2.67; >90% engagement); game at pietrogalizia.github.io/Snakeleev/
- Cooper, S. et al. "Predicting protein structures with a multiplayer online game". *Nature* 2010. DOI 10.1038/nature09304 — Crossref record (~1,000 citations); fold.it live (HTTP 200)
- Wikipedia, "Snake (video game genre)" — genre conventions (Blockade 1976; growth on eating; boundary/self collision; speed increase precedent)
- happyatoms.com live (HTTP 200) — feature details NOT verified

**Local prior art:**
- `tmp/bioCHEMeleon/DATA_SOURCES.md` — attribution format precedent (read directly)
- `tmp/bioCHEMeleon/biochemeleon/` — module layout precedent (info-box implementation not examined this pass)

**Known verification debt (for human approval / data-prep):**
- 3.3 Å lower bound of the π-stack range (Janiak body text — inaccessible, 403)
- Specific distance numbers for: prescribed π-stack game geometry, COOH dimer O···O, imidazole N–H···N, O–H···O chains, C–H···N contacts — all UNVERIFIED here; pin from COD/CIF or full-text literature at data-prep, then human approval
- Herringbone crystal packing of neat benzene/naphthalene/anthracene — UNVERIFIED here
- Per-CID PubChem 3D conformer coverage — benzene verified; others presumed

---
*Feature research for: serpentrum — educational PyMOL snake game with molecular stacking + spectra*
*Researched: 2026-09-06*
