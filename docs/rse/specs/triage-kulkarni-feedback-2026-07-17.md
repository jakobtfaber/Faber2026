# Triage: Kulkarni-persona feedback (2026-07-17)

**Sources:** `~/scratch/kulkarni-profile/Faber2026/kulkarni-referee-2026-07-17.md`
and `kulkarni-discovery-scan-2026-07-17.md` (simulated persona review + idea
scan; private, not a real referee report).
**Companion PR:** the `ms/deflation-kulkarni-20260717` writing pass, which
implements every prose-actionable item below. Everything else is a science
lane and stays gated by `CONTEXT.md` and the plan-§V re-trust ladders.

## Referee report — prose items (implemented in the companion PR)

1. **"Factor-of-two" mislabel.** The 100–560 pc cm⁻³ cluster-column bracket is
   a factor ~5.6 end to end, not 2. Fixed in five places (abstract,
   results §dominant-systems, conclusions, appendix geometry note,
   `fig:clusters_icm` caption): the bracket is now quoted explicitly and the
   results text calls it "a factor of ~6 end to end" (560/100 = 5.6).
2. **Induced α-prior.** A prior uniform in β∈[3,4] induces a prior density on
   α ∝ (β−2)², four times higher at the β=4 endpoint than at β=3. Now stated
   in the methods priors paragraph, with the endpoint-degenerate treatment as
   the adjudication (consistent with the CONTEXT.md rule that a β=4-railing
   posterior is evidence against thin-screen closure, never a square-law
   detection).
3. **A-posteriori cluster framing.** Results §dominant-systems now states that
   the intervening-DM dominance of the FRB 20230307A crossing describes a
   single a-posteriori-identified alignment in a depth-varying census, not an
   FRB-sightline population property.
4. **f_IGM circularity prominence.** Conclusions bullet 3 now carries the
   inherited f_IGM = 0.76 normalization and its partial derivation from
   DSA-110 sightlines; methods and the host-forward-model appendix already
   stated it.
5. **Sub-band "validation" overclaim.** Subsection retitled "Sub-band
   cross-check of the frequency scaling"; the opening sentence no longer says
   "validated independently" (the referee's point: the EMG sub-band fits share
   the β=4 kernel family and are a slope diagnostic, which the text already
   conceded two paragraphs later).
6. **"Three decades in E_iso".** Already gated: appears only in commented-out
   draft prose behind the V3 clearance; no compiled text quotes it. No action.
7. **Note-u coverage honesty.** Already present (referee applauded it); the
   new a-posteriori sentence reinforces the coverage-artifact reading.

## Referee report — science items (NOT implemented; need their own lanes)

- **S1. X-ray/SZ upper-limit mass bound for J115120.4+714435** (referee §5;
  = discovery Thread 2). The PSZ2/MCXC absences are currently used only for
  cross-match; converting them (plus eROSITA/ROSAT archival limits) into a
  Y_500/L_X → M_500 bound would replace the richness-mass tower and shrink
  the factor-~5 column bracket. Cheap (one archival query) but it is a new
  quantitative manuscript input → needs a predeclared experiment record and
  owner sanction before any number enters prose. **Recommended first.**
- **S2. A-priori cluster-crossing probability** (referee §6). Expected
  crossings within R_500 of ≥10¹⁴ M_⊙ clusters across twelve sightlines
  (referee's rough estimate ~0.1). Small, self-contained calculation; the
  result would sharpen the a-posteriori framing already in prose. Needs a
  predeclared method (cluster mass function + path integral) before the
  number is quotable.
- **S3. f_IGM non-circular normalization** (referee §5). Breaking the
  circularity requires an external f_IGM not derived from DSA-110 sightlines
  (or a joint refit). Larger scope; the sensitivity is now stated in prose.
  Defer; revisit at the V5 follow-up or the next budget pass.

## Discovery scan — thread dispositions

| Thread | Verdict | Gate |
|---|---|---|
| 1. RM → intervening cluster/CGM B-field | Chase (strongest; cross-paper seam). DM_int inputs are V4/V5-cleared; RM comes from the polarization companion. | New predeclared lane; coordinate with companion-paper owners before any attribution claim. |
| 2. DM as gas calorimeter below SZ/X-ray floor | Chase; same archival query as S1. | Same record as S1. |
| 3. δDM vs τ differential (ν⁻² test) | Valid design, but the τ side consumes wave-1-revoked scattering fits. δDM alone (V6-cleared) supports the ν⁻² bound half. | τ-correlation half blocked behind V1/C1; the pure δDM bound could be chartered now. |
| 4. Steep-β cluster sightline (20230307A α=5.26) | Blocked. Built entirely on revoked fits; CONTEXT.md bars quoting β for any row pending V1 + geometry adjudication; the analyst layer itself flags component-multiplicity artifact risk. | V1 + geometry-selection campaign. |
| 5. τ–DM_host population regression | Blocked (revoked τ fits; scattering-censored selection acknowledged by the scan itself). | Post-C1; carry the censoring caveat. |
| 6. β→4 rails as demographic | Blocked and partially contradicted: under CONTEXT.md the rails are evidence against thin-screen closure and rail tallies are dropped from the manuscript; reading the rail count as a "compact screen" demographic presumes the closure the rails reject. Reframe, if at all, inside the geometry-selection campaign. | Geometry-selection campaign. |

**Struck thread** (withheld-novelty objection): already struck in the referee
file — the two-band β-closure analysis is being added; no action.
