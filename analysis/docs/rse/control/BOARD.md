# Manuscript board — CHIME/FRB–DSA-110 co-detections (canonical task list)

**Canonical as of 2026-07-18** (owner decision). Supersedes
`specs/plan/plan-circulation-readiness.md` and the `program-state.toml` lane views,
which are frozen as history (banners in place; the CI `check-state` gate still
reads the frozen toml — retiring that machinery is a separate mechanical
change). Decisions are made on the wayfinder map
([`wayfinder/map-apj-submission.md`](wayfinder/map-apj-submission.md)) — this
board carries execution, organized by manuscript structure. Wayfinder ticket
references appear as `[wf-NN]`.

**Naming:** descriptive-first; legacy letter+number codes appear once in
parentheses for traceability into the frozen docs.

**Trust:** until the trust-ledger overhaul resolves
([wf-13](wayfinder/tickets/13-overhaul-trust-assessment.md)), the
`CONTEXT.md` trust-reset block governs what is citable. Tasks marked
**⛔ trust** consume currently-revoked products and are sequenced behind the
overhaul (or the re-validation it prescribes).

**Legend:** `[ ]` open · `[x]` done · `⛔ trust` gated on trust
overhaul/re-validation · `⏳ campaign` gated on a cross-cutting campaign ·
`✋ owner` needs an owner decision (usually a wayfinder ticket).

---

## Cross-cutting campaigns

Feed multiple sections; section tasks reference them, never duplicate them.

### Trust & contracts
- [ ] ✋ Trust-ledger overhaul — lane-by-lane re-audit of the revocation
  waves; sets the citability bar everywhere
  ([wf-13](wayfinder/tickets/13-overhaul-trust-assessment.md))
- [ ] ✋ Fit re-validation contract ratification (legacy V1) — bar for any
  re-fit to be citable ([wf-03](wayfinder/tickets/03-ratify-fit-retrust-contract.md))
- [ ] CHIME scattering-input lineage check (legacy V2) — do the dynamic
  spectra feeding the scattering fits share the gen-1 de-chirp defect?

### Both-band scintillation campaign

**⛔ INPUT REMEDIATION FIRST (owner adjudication 2026-07-18,
[findings](specs/notes/owner-data-review-findings-2026-07-18.md)):**

- [ ] RFI excision pass: all CHIME upchannelized products + DSA
  central-channel RFI; per-burst masks documented
- [ ] One authoritative DM per burst across all products (reconcile upchan
  TARGETS vs full-res vs adopted catalog; marker-dependence rule governs);
  rebuild aligned upchan npz set at adopted DMs, fresh checksums/provenance
- [ ] Re-run the windowed-refit campaign on remediated inputs (same
  predeclared gates); rerun closure/finalization + validation.json + figures
- [ ] Fresh 36-panel input review + both-band ACF review for owner

- [ ] ✋ Ratify the qualifying CHIME-band method — **blocked on remediation**
  ([wf-02](wayfinder/tickets/02-ratify-chime-scintillation-method.md))
- [ ] Burst configs for the four unconfigured sightlines
  (whitney/phineas/mahi/isha) (legacy B1)
- [ ] CHIME regeneration for the six never-generated co-detections
  (zach, oran, wilhelm, johndoeii, hamilton, chromatica) (legacy B2)
- [ ] mahi 700–725 MHz RFI inspection before that sub-band is used (legacy B3*)
- [ ] ACF / decorrelation-bandwidth measurements across the sample, both
  bands, under the ratified contract (incl. re-running the revoked DSA-band
  fits) (legacy B4)
- [ ] Two-screen analysis rebuilt on joint CHIME+DSA products (legacy B5)
- [ ] Provenance housekeeping: scint data-provenance refresh, commit the
  h17-side tooling (legacy B6)

### Scattering re-fit campaign
- [ ] ✋ Scintillation-to-scattering coupling design closure (legacy A1)
  ([wf-04](wayfinder/tickets/04-close-scint-scattering-coupling-design.md))
- [ ] ✋ Profile-component-count statistic: blocker or deferred (legacy A5)
  ([wf-05](wayfinder/tickets/05-profile-component-statistic-blocker-decision.md))
- [ ] Extended-medium (uniform-LOS) PBF kernel, β-coupled, per band (legacy A2)
- [ ] Per-sightline geometry model selection, thin vs extended,
  scint-informed (legacy A3)
- [ ] From-scratch re-fit of all twelve co-detections under the ratified
  contract with geometry adjudication (legacy C1) — **12/12 production
  mass-refit landscape landed 2026-07-18** (jointtf lane, h17): 4 interior /
  3 ceiling-adjacent / 3 ceiling-rail / new floor-rail class
  (hamilton, whitney); PL-PBF collapsed to production EMG; free-α win =
  mismatch signature. Remaining: leakage-injection verdict, count adoption
  ([wf-15](wayfinder/tickets/15-count-audit-remediation-standing-method.md)),
  free-α reporting
  ([wf-14](wayfinder/tickets/14-free-alpha-diagnostic-reporting.md)),
  validation + ratification before manuscript use
- [ ] Per-band systematics pass on flagged sightlines (legacy C2)
- [ ] Pipeline pin bump + table/figure regeneration from the campaign (legacy C3)

### Energies re-validation
- [ ] Energies pipeline under the ratified contract; resolve the spectral-index
  pile-up at ≈−5 and the table selection-rule contradiction; fold in the
  energy-definitions/calibration checklist (units, unmasked-bandwidth
  integration, SEFD/beam prior budget) (legacy V3 + review S20)

### Figures
- [ ] Figure 1 twelve-burst gallery — **at owner-decide gate** (2026-07-18):
  observed-peak candidate merged + promotable
  (`2026-07-17-fig1-observed-peak-audit`); dmcorr variant refuted
  (marker-dependence); owner runs the two `figure_review.py decide` commands
  (handoff-2026-07-18-14-44), then any session runs the promotion PR
- [ ] Wishlist figures: (re)insert per `specs/notes/figure-wishlist.md` as their
  gates clear; strip draft `\fbox` placeholders before circulation

### Verification & rigor

Protocol: [`verification-protocol.md`](../protocols/verification-protocol.md)
(adopted 2026-07-18; plain names 2026-07-20). Data chain first; then checks by
claim class — a section task is not done until its inherited checks are green.
Approved tooling: WolframScript + MATLAB (hpcc), SymPy, astropy.units,
Undermind, Perplexity, ADS, Retraction Watch/Crossref, Semantic Scholar,
hypothesis, SBC. (Excluded by owner: scite.ai, Elicit, Consensus.)

- [ ] **Calculation Check** — prose/table numbers ↔ registry; **blocking**;
  `\draftnum{}` empty at circulation freeze
- [ ] **Equation Check** — dual CAS + `astropy.units` on budget/delay arithmetic
- [ ] **Model/Fit Check** — SBC harness for dynesty; at each campaign closeout
- [ ] **Reference Check** — ADS + Retraction Watch + Semantic Scholar on
  `refs.bib`; prior-art sweep per headline claim → evidence ledger
- [ ] **No-Context Review** — ≥2 independent cold reads per round; convergence
  = no new valid P0/P1 (pre-circulation + pre-submission)

### Board hygiene
- [ ] Descriptive-names glossary for the frozen letter+number docs
  ([wf-12](wayfinder/tickets/12-retire-letter-number-stage-names.md), scope
  reduced: this board already reads descriptively)

---

## §0 — Results provenance & organization (pre-manuscript)

**DATA CHAIN (owner, 2026-07-19; names 2026-07-20):** work proceeds bottom-up
per [`verification-protocol.md`](../protocols/verification-protocol.md) —
**Raw Data** → **Input Data Products** (per-burst **data cards**, hash-bound
owner approval) → **Measurements and Fits** → **Analyses and Interpretations**
→ **In-Manuscript Claims**. **Raw Data** (CHIME) = the twelve singlebeam
voltage `.h5` files on h17 only
([`specs/notes/definition-raw-chime-data-2026-07-19.md`](../specs/notes/definition-raw-chime-data-2026-07-19.md));
intensity / upchannelized `.npy` products are Input Data Products, not Raw
Data. The route is wayfinder tickets **17 → 18 → 19 → 20 → 21 → 22 → 02**
(certify raw voltages → DM redo → TOA redo → upchan rebuild → scattering
re-anchor → scint campaign → ratification); master resume
`specs/handoff/handoff-2026-07-19-stratified-restart.md`. Scint-remediation
tasks previously under the campaigns lane are absorbed by tickets 18/20/22.
No later link opens before its upstream certificates exist. Ticket 17 is
**open** under the corrected Raw Data definition.

Owner directive 2026-07-18: before section work, establish one reliable view
of what results exist, where they originated (scripts, pipeline pin, external
survey/catalog queries), and what is trusted — the repo + auxiliary worktrees
are currently too dispersed to know what is current. Canonical artifact:
[`results-registry.toml`](../notes/results-registry.toml) (skeleton landed) →
generated `RESULTS.md` view. **This inventory is phase 1 of the trust-ledger
overhaul** ([wf-13](wayfinder/tickets/13-overhaul-trust-assessment.md)):
populate first, adjudicate row-by-row on top.

- [ ] Registry generator: `results-registry.toml` → `RESULTS.md`
  (sync_state pattern); wire into `check-state`
- [ ] Dispersion sweep: inventory artifacts across the repo, pipeline
  submodule, worktrees, `~/Data`, and h17; mark current vs superseded;
  quarantine stale products (PR #131 precedent)
- [ ] Populate the registry: every manuscript-facing number/table/figure/
  verdict, with producing script, pipeline pin, external-source provenance
  (survey/DR/DOI/query date), and trust seeded from the `CONTEXT.md` ledger
- [ ] Re-point the tier-2 prose-number parity gate at the registry (single
  source of truth for the CI check)

## Abstract

- [ ] ⏳ Fill the cluster-column slot with the intracluster-DM uncertainty
  once frozen (referee M16; submission-time)
- [ ] ⛔ Rewrite the closing multiplicity-bias claim — rides on revoked fits;
  post re-fit campaign / trust overhaul
- [ ] Final headline pass (association + budget sentences are on re-verified
  numbers; re-verify after §4 refills)

## §1 Introduction

- [ ] Opening-prose consistency guard: keep claims aligned with what the
  filled scattering/scint/energy slots actually state (carry-forward)
- [ ] Structural referee-mode pass (can run now)

## §2 Observations and Sample

- 2.1 Dynamic spectra & reduction
  - [ ] Jackknife/masking specification: block width, contiguity, ordering
    vs masking, mask-threshold stability (review S7 — 3–4 sentences)
- 2.2 Dispersion-measure measurements *(provenance re-validated 2026-07-07,
  shared DSA-DM convention)*
  - [ ] ✋ Coverage-calibrated DM uncertainties: end-to-end injections into
    real off-pulse waterfalls + coverage fraction — in or deferred?
    (review S8; disposition via [wf-10](wayfinder/tickets/10-disposition-technical-review-robustness-items.md))
- 2.3 Scattering fits
  - [ ] ⏳ Rewrite on the re-fit campaign's verified inputs/methods
- 2.4 Milky Way foreground
  - [ ] NE2025 publication-status check at submission (referee MW4)
  - [ ] ✋ Per-sightline disk-model comparison table (NE2025 vs
    NE2001/YMW16) — justifies the 30% disk prior (review S15b; via wf-10)
- 2.5 Foreground-galaxy search *(census re-validated + remediated 2026-07-15)*
  - [ ] ✋ Census-aperture wording: frozen census as-built vs live-replay
    description ([wf-08](wayfinder/tickets/08-correct-census-aperture-description.md))
  - [ ] ✋ Completeness / missing-halo systematic: limiting magnitude →
    P(missed group-scale halo) per corridor (review S11; via wf-10)

## §3 Methods

- 3.1 TOA crossmatching *(association arithmetic re-validated 2026-07-07)*
  - [ ] TOA estimator + time-standards paragraph (peak vs matched-filter vs
    model t₀; UTC/TDB; barycentring; reproduce the geometric-delay range)
    (review S3)
  - [ ] Deterministic trial-set rule + operational association windows as
    supplementary material (review S1)
  - [ ] ✋ Exact DSA-110 trigger denominator — needs trigger-DB query
    ([wf-09](wayfinder/tickets/09-obtain-dsa-trigger-denominator.md))
- 3.2 Dispersion-measure decomposition
  - [ ] ✋ Fiducial priors sign-off + host-DM right-skew headline acceptance
    ([wf-07](wayfinder/tickets/07-sign-off-budget-priors-and-host-dm-headline.md))
- 3.2b Intervening foreground galaxies & clusters
  - [ ] ✋ Phineas halo-mass prescription conflict (census flags vs budget
    chain; DM_int 241 vs ≈218)
    ([wf-06](wayfinder/tickets/06-adjudicate-phineas-halo-mass-prescriptions.md))
  - [ ] ✋ Probabilistic b/R_vir mixture for borderline halos (review S12;
    the machinery half of the phineas adjudication)
- 3.3 Scattering attribution (joint two-band fit; sub-band cross-check;
  gain-marginalized likelihood; multiple temporal components)
  - [ ] ⛔ Purge rail-class vocabulary and α=4-limit quoting; restructure
    around geometry selection (post re-fit campaign)
  - [x] Presentation contracts locked 2026-07-10: closure-regime column,
    sub-band-diagnostic-only, separate ACF path + gain prior, band-restricted
    energies disclaimer (legacy D2–D5)
- 3.4 Band-restricted burst energies
  - [ ] ⏳ Refill from the energies re-validation campaign

## §4 Results

- 4.1 Association of the co-detections *(re-validated 2026-07-07)*
  - [ ] Robustness paragraph: positive-residual mean (+2.4 ms, ≈2.4σ) with
    verdict-stability statement; declination-conditioned rate sensitivity
    sentence; repeater/clustering statement (review S4/S5/S6)
- 4.2 Per-sightline DM budget *(re-validated 2026-07-07; phantom-DM_int bug
  fixed 2026-07-15, FLITS #183)*
  - [ ] ✋ Cluster-aperture sensitivity: recompute at 1.5·R_500 / R_200 with
    envelope (review S13; via wf-10)
  - [ ] ✋ Intervening-scattering column: document the DM→τ mapping or drop
    until the scattering framework lands (review S14; triage recommends drop)
- 4.3 Scintillation & screen attribution
  - [ ] ⏳ Rebuild on the both-band campaign + two-screen rebuild
  - [ ] ✋ Modulation-index gate (m ≤ 1.5) vs two-screen √3 bound: reframe or
    raise + re-run guard matrix, report verdict changes (review S16; via wf-10)
  - [ ] ✋ Pulsar positive control through the CHIME upchannelization chain:
    needed, or does the injection battery suffice? (review S17; via wf-10)
- 4.4 Turbulence spectrum & burst multiplicity
  - [ ] ⛔⏳ Refill from the re-fit campaign under geometry adjudication;
    β-table rework (geometry-adjudicated quoting; descriptive
    exponential-consistency statements where no index is quotable)
- 4.5 Band-restricted burst energies
  - [ ] ⛔⏳ Refill from the energies re-validation (roster + disclaimers per
    the locked presentation contract)

## §5 Discussion

- [ ] ⛔⏳ Screen-attribution subsection on the re-derived
  measured-vs-predicted overlay (both sides currently revoked)
- [ ] ⛔⏳ Event-by-event interpretation ledger refresh post campaigns
  (incl. the FRB 20230913A intervening attribution, currently revoked)
- [ ] Fixed-α vs β-posterior choice in screen attribution (referee D1 full
  resolution; TODO in tex)
- [ ] Population limits / next-pass subsections: consistency with what
  actually ships

## §6 Conclusions

- [ ] ⛔⏳ Rewrite items tied to revoked claims (census/budget items,
  scattering items, the multiplicity item) after campaigns + trust overhaul

## Appendices

- A. Association cards — [ ] verify against the re-validated association
  artifacts
- B. Intracluster DMs — [x] cluster geometry offset carried as documented
  ±3% systematic (2026-07-15) · [ ] inherits the cluster-aperture
  sensitivity outcome (S13)
- C. Host-DM forward model — [ ] regenerate iff priors move
  ([wf-07](wayfinder/tickets/07-sign-off-budget-priors-and-host-dm-headline.md))
- D. Scintillation ACF diagnostics + two-screen formalism — [ ] ⏳ refresh
  from the ratified method; keep consistent with the modulation-gate
  resolution (S16)
- E. Joint-model morphology audits — [ ] ⛔⏳ refill from the re-fit
  campaign; sightline-halo-grid caption states panel count/omissions
  (referee M15)
- Parked EMG appendix — [ ] ✋ effective-index sensitivity variant vehicle:
  revive or leave parked (review S19; via wf-10)

## Front & back matter

- [ ] ✋ Co-author list: draft from Law2024 + CHIME/FRB overlap, owner
  prunes, typeset `auth.tex`
  ([wf-11](wayfinder/tickets/11-prune-coauthor-list.md))
- [ ] Zenodo archival release + DOI mint; point `\software{}` pipeline entry
  at it (referee B5/M11; submission-time)
- [ ] Data-availability section final check
- [x] Keywords include Radio bursts (1339) (referee M12)

---

## Done ledger (major, pre-board)

Association + DM provenance re-validated (2026-07-07) · census re-validated
(2026-07-07) + remediated to 28 physical systems with adjudicated masses
(2026-07-15) · DM-budget re-validated (2026-07-07); phantom-DM_int fallback
bug fixed, six sightlines corrected (FLITS #183) · chance-coincidence units
and cross-ref fixes landed · referee blocking items B1–B4 resolved; design
locks accepted (2026-07-10) · Figure 1 contract locked (2026-07-14) ·
CHIME-band qualification history: three routes documented-fail, successor
method in hand pending ratification ([wf-02](wayfinder/tickets/02-ratify-chime-scintillation-method.md)).
