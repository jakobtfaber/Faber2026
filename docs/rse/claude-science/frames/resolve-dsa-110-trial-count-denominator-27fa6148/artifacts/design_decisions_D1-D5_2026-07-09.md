# Design decisions D1-D5 — scattering/scintillation/energetics sections

**Recorded:** 2026-07-09 · **Referee report:** `docs/referee_report_2026-07-07.md` §"Design decisions for the incoming scattering/scintillation sections"

These are the author-selected resolutions to the five design decisions the referee
asked to be locked *before* the pending scattering/scintillation/energetics sections
are written, so the per-sightline ledger is internally consistent. Each entry notes
what is decided now and what its implementation depends on.

---

## D1 — Galactic-vs-extragalactic alpha consistency

**Referee concern.** The screen-attribution logic tests whether the Galaxy explains
the scattering using NE2025 tau predictions scaled with a fixed Kolmogorov alpha=4.4,
while the paper's thesis is that fixing alpha biases inference. The referee reads this
as an inconsistency every per-sightline verdict would inherit.

**Decision — no methodological change; make the framing explicit.**
The apparent inconsistency dissolves once the two objects being brought to a common
frequency are distinguished:

- **NE2025's Galactic tau/dnu is a *model output*.** NE2025 is a Kolmogorov-based
  electron-density model; its native frequency dependence is alpha=4.4. Scaling that
  prediction to the comparison frequency must use the model's own index. Applying our
  empirically fitted beta to a model quantity would be incoherent.
- **Our measured tau is *empirical*.** It carries whatever frequency dependence our
  fitted beta implies and scales by our alpha(beta).

Correct recipe: **each quantity scaled by its own native index, compared at NE2025's
reference frequency.** The two indices differing is not a fixed-alpha assumption
smuggled into our inference — it reflects that one is a model prediction and one is a
measurement.

**Implementation (lockable now):** add an explicit statement in Sec Obs-MW that the
alpha=4.4 used for the NE2025 comparison is inherited from NE2025's Kolmogorov
construction, not a fixed-alpha choice in our own analysis. No code change.

---

## D2 — beta=4 degeneracy with the inner-scale regime

**Referee concern.** When the diffractive scale falls below the inner scale, alpha->4
regardless of beta (Cordes et al. 2016; Cordes 2025), so beta=4 (square-law) and the
inner-scale-dominated regime are observationally degenerate. Do not report beta=4 as a
turbulence-spectrum measurement; bake a "closure regime" column into the results table
rather than retrofitting the caveat in prose.

**Decision — add a "closure regime" column to the results table.**
Each sightline carries an explicit regime label (e.g. inertial-range /
inner-scale-dominated / square-law-degenerate) alongside its beta. beta=4 cases are
flagged as regime-ambiguous, not reported as a spectral-index measurement.

**Implementation (design locked; column build gated on revalidated fits).** The regime
classification rule per sightline must be defined, and the current joint fits are not
yet in a state to populate it (see note below).

---

## D3 — sub-band validation uses a parametrization the joint fit may reject

**Referee concern.** Sec Subband fits an EMG (exponential PBF) per sub-band — the family
the joint fit argues biases alpha. As a slope cross-check this is defensible only if the
shape-mismatch bias in per-sub-band tau largely cancels in the slope, which holds only
when the mismatch is frequency-independent (not true in general).

**Decision — partition the sub-band diagnostic by best-fit PBF family; rework required.**
The per-sub-band EMG slope is only a coherent cross-check for sightlines whose *joint*
fit already prefers an exponential/thin-screen PBF. For a burst best-fit by a beta-based
PBF, imposing an EMG per sub-band is not a validation — the shape-mismatch bias is the
dominant term, not a small correction that cancels.

Locked design principle: **the sub-band diagnostic uses, per sightline, the same PBF
family the joint fit selected, and is labeled a validation diagnostic throughout — never
a turbulence constraint.** This removes the "uses the rejected parametrization" objection
at its root. For EMG-preferred sightlines, additionally make the
frequency-independence-of-mismatch cancellation argument explicit.

**Implementation (principle locked; per-burst assignment gated on revalidated fits).**
Which bursts are EMG- vs beta-preferred cannot be assigned from the current fits (see
note).

---

## D4 — scintillation double-use

**Referee concern.** The gain marginalization absorbs the scintillation pattern into the
per-channel gain, yet scintillation returns later as an observable (Sec
Results-scintillation). State, where the marginalization is introduced, that
scintillation products come from a separate analysis path; and address whether the
gain-prior width interacts with the tau posterior at low S/N (a fully free per-channel
gain can absorb scattering-induced spectral smearing in the low-tau limit).

**Decision — separate-path statement AND a quantitative gain-prior/tau sensitivity check.**
Add the separate-path statement, and run/report the low-S/N sensitivity: show how the tau
posterior moves as the gain-prior width varies, demonstrating the gain prior does not
absorb scattering in the low-tau limit.

**Implementation.** The statement is a prose add (lockable now). The sensitivity check is
a re-fit sweep over gain-prior width on the low-S/N bursts — part of the revalidation
campaign.

---

## D5 — energetics comparability

**Referee concern.** The band-restricted two-band E_iso is not comparable to literature
values over a fixed rest-frame band. Eq. eq:eiso applies a single (1+z) k-correction to a
two-band sum with different spectral indices. Provide a fixed rest-frame-band variant or
state prominently that these energies cannot be placed on standard luminosity functions,
and write out the per-band rest-frame intervals.

**Decision — provide a fixed rest-frame-band E_iso variant.**
Compute an additional E_iso over a fixed rest-frame band (per-band k-correction with each
band's own spectral index), so the sample can sit on standard FRB luminosity functions;
keep the observed-band two-band value alongside.

**Status of the prose (already in `sections/methods.tex`):**
- Per-band rest-frame intervals [0.400(1+z), 0.800(1+z)] GHz (CHIME) and
  [1.311(1+z), 1.499(1+z)] GHz (DSA) are written out. DONE.
- Non-comparability to fixed-rest-frame-band literature energies stated prominently. DONE.
- The single-(1+z) concern is resolved: it is the bandwidth (time-dilation) k-correction
  common to both bands; the differing spectral indices gamma_C, gamma_D enter only the
  in-band flux integrals, so the two-band sum is internally consistent. DONE.

**Implementation (remaining).** Derive and report the fixed rest-frame-band variant
itself — currently promised in the text but not defined. Gated on the pending energetics
inputs (spectral amplitudes, calibration path, host-redshift provenance, inclusion rule),
per the "Energy rows are deferred until..." note in methods.tex.

---

## Blocking note: the joint fits are not yet revalidation-ready

D2's regime column and D3's per-burst family assignment both depend on trustworthy
per-burst PBF-family / beta verdicts. The current `joint_gate` fits
(`pipeline/analysis/scattering-refit-2026-06/joint_json/`) are **all flagged MARGINAL**:

| burst | alpha | beta | flag |
|---|---|---|---|
| chromatica | 6.00 | 3.00 | alpha prior-railed -> unconstrained |
| freya | 6.00 | 3.00 | alpha prior-railed -> unconstrained |
| hamilton | 5.99 | 3.00 | alpha prior-railed -> unconstrained |
| isha | 4.96 | 3.35 | off Kolmogorov |
| johndoeII | 1.37 | -- | sub-Kolmogorov (closure n/a) |
| mahi | 5.53 | 3.13 | off Kolmogorov |
| oran | 1.44 | -- | sub-Kolmogorov (closure n/a) |
| phineas | 3.58 | 4.53 | chi2_D marginal |
| whitney | 1.46 | -- | sub-Kolmogorov (closure n/a) |
| wilhelm | 2.71 | 7.67 | chi2_C marginal |
| zach | 3.66 | 4.41 | no PPC |

Three sightlines are alpha-railed at the prior bound, three are sub-Kolmogorov (alpha<2,
where the alpha=2beta/(beta-2) closure does not apply), and none passes clean PPC. This
is exactly the fit re-validation ladder the referee's scope note lists as pending. The
D2/D3 columns cannot be populated from these fits; they wait on the revalidation campaign.

## Summary of what is unblocked now

- **D1:** write the Sec Obs-MW acknowledgment (no code).
- **D4:** write the separate-path statement (no code).
- **D5:** prose parts done; fixed-band variant awaits energetics inputs.
- **D2, D3:** design principles locked; table columns / per-burst assignments await
  revalidated fits.
