# Agent One draft vs. verified formalism — audit memo

Agent One (Wolfram) was used as a **draft generator** for the two-screen
scintillation section. Every relation was then checked against the primary
literature and, where geometric, an independent ray-trace. Summary of what
survived and what was corrected.

## Correct in the Agent One draft
- ACF definition, off-pulse normalization, and lag-0 exclusion rationale
  (noise spike). ✔
- Lorentzian ACF model `m^2 / (1 + (dnu/nu_s)^2)`; `nu_s` = HWHM. ✔
- `ACF(0+) = m^2`; point vs extended source (`m<1` = partial quenching). ✔
- `N_scint ~ eta B/nu_s`; fractional errors `~ 1/sqrt(N_scint)`. ✔
- Thin-screen scattering time `tau = theta_scat^2 d_eff/(2c)`,
  `d_eff = d(D-d)/D`; `theta_scat = sqrt(2c tau/d_eff)`;
  `s_d = lambda/(2 pi theta_scat)`. ✔
- Overall physical argument: near-screen scintillation requires the far
  image to be unresolved; detection → upper limit; marginal resolution →
  equality. ✔ (This is the real, published Masui2015 / Pradeep2025 result.)

## Corrected errors
1. **Fourier constant C1.** Draft: `C1 = 2` for a "uniform medium".
   Not adopted. The only value sourceable from retrieved primary text is
   the RANGE `C1 = 0.5–2` (Lambert & Rickett 1999, as quoted verbatim in the
   fetched Pradeep+2025 PDF), of order unity for a thin screen. Specific
   point values (e.g. 1.16 Kolmogorov thin screen, 0.74 uniform Kolmogorov
   medium) are commonly quoted but were NOT confirmable against retrieved
   primary text in this session, so they are deliberately omitted from the
   manuscript; the .tex uses C1=1 fiducial + the 0.5–2 range as a systematic.

2. **Image lever-arm (the central formula).** Draft:
   `theta_img = theta_scat,1 * (D - d1)/(d1 - d2)` — denominator is the
   screen–screen separation. **Wrong.** Independent ray-trace (point source
   → thin deflector at d1 → plane at d2) gives
   `theta_img = theta_scat,1 * (D - d1)/(D - d2)`.
   Verified at d2 = {0, 50, 200, 500} (arb. units): ray-trace matches the
   `(D - d2)` form to machine precision; the draft's `(d1 - d2)` form is
   wrong at every point and fails the d2→0 observer limit
   (should reduce to the standard `theta_h (D-d1)/D`).

3. **Distance relation.** Draft gave only a hand-assembled inequality with
   the wrong lever arm. Replaced with the redshift-consistent published
   form, Pradeep et al. (2025) Eq. 7.6:
   `D_h,FRB · D_MW  <=  (1+z) D_FRB^2 /(8 pi nu^2) · nu_s,MW/(m_MW tau_s,h)`,
   which closes to an equality at marginal resolution (RP ≈ 1,
   0 < m_MW < 1). Order-of-magnitude checked: `L_x L_g <~ 0.6 kpc^2`,
   consistent with Sammons et al. (2023) CRAFT constraints.

## Value Agent One did *not* supply (added from literature)
- Two-screen ACF **product term** and the resulting `m_tot = sqrt(3)` in the
  unresolved, fully-modulated regime (Pradeep et al. 2025). This is the
  quantitative core of the modulation-index parameterization and is what
  makes the regime observationally diagnosable.
- Resolution Power `RP = L_MW L_host/(lambda D_MW,host)` as the ordering
  parameter, and the "quenching is gradual, not knife-edge" correction to
  the older assume-scintillation-disappears treatments.

## Bottom line
Agent One reproduced standard textbook relations reliably but (a) misstated
an order-unity constant and (b) got the key non-textbook geometric factor
wrong — exactly the two places where a draft is most dangerous. It also did
not know the current (2025) two-screen ACF result. Used as a scaffold with
mandatory verification it was useful; cited unchecked it would have put a
wrong lever-arm into the manuscript.
