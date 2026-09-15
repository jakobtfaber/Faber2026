---
title: "Independent review: scattering mathematical foundations audit"
kind: review
comments: none
---

# Verdict: approve, with four cleanups

Reviewer: Claude Opus 5, session `b959b802`, read-only. Reviewed state: working
tree on branch `method-reassessment-2026-09-11`, HEAD `353d1df4`, audit
directory untracked.

Reviewed files, all under
`analysis/docs/analysis/scattering-mathematical-foundations/`:
`index.md` (100 lines), `physics-sources.md` (197), `statistics-and-sampling.md`
(252), `checks.py` (91), `check-results.json`.

Every substantive mathematical claim I could test against the code or derive by
hand holds. No claim in any of the three documents is wrong. The findings below
are precision and durability issues, not corrections.

Repository unchanged by this review: no production edit, no fit, no commit, no
push, no touch to the earlier reassessment pull request. The only execution was
the audit's own documented reproduction command.

## Findings, priority order

### A. The guard's stated rationale is false for the system actually solved

`analysis/scattering/scat_analysis/burstfit_joint.py:214-265` justifies the
eigenvalue cull with "M_f singular -> the full-N solve explodes |g|". The solve
is not against `M`. It is against `A = M + (σ²/s²)I`, which is positive definite
for every finite `s²` no matter how singular `M` is. The gain estimate therefore
cannot diverge, and the premise for discarding a direction does not exist.

`statistics-and-sampling.md:129-131` already says the covariance stays positive
definite. It stops short of naming the docstring's reasoning as the thing that
is wrong. Saying it directly strengthens the counterexample from "the
approximation differs" to "the approximation is defended by an argument that
does not apply." That is a sharper result and costs one sentence.

### B. `normalized_piecewise_kernel_area` does not exercise the criticized path

`checks.py:55-57` builds `s_c`, the continuous area `N_β`, and integrates the
piecewise kernel to infinity, confirming area 1 to 1e-7. The normalization that
`statistics-and-sampling.md` §1 and `physics-sources.md` §5 actually criticize
is the *finite discrete grid* normalization inside
`gaussian_powerlaw_convolution`, which sums over a truncated lag grid. The check
confirms the continuous analytic form. It says nothing about the truncated sum.

No document names this key in prose, so a reader meeting it in
`check-results.json` may take it as covering the criticism. One line in
statistics §1 disclaiming that would close the gap.

### C. Two citation ranges are slightly off

| Document text | Actual |
| --- | --- |
| `_gain_marginal_multi_band_impl`, lines 214-356 | function spans 214-392 |
| `_JointPriorTransformOrdered`, lines 633-684 | class starts 630, `__call__` ends 686 |

Both point at the right code. The ranges just do not bracket it.

### D. `checks.py` is weaker than a re-runnable gate needs

Two issues. Every assertion is a bare `assert`, so `python -O` strips all of
them and the script exits 0 having verified nothing. And the rank-fallback
assertion at `checks.py:47` uses a magic threshold, `abs(exact-approximate) > 4000`, with no stated origin; the observed gap is 4994.89, so the number reads
as a round-down of the answer rather than a derived bound.

Both are cheap to fix: raise `AssertionError` explicitly (or use `if ... raise`),
and either derive the threshold or assert against the recorded value with a
tolerance. The repository's own verification standard asks for a re-runnable
check, and a stripped assertion is not one.

## Scope notes, no action requested here

**E. The old reassessment docstring is now incomplete.**
`analysis/docs/rse/specs/research/method-reassessment-2026-09-11/injection_recovery.py:112-127`
still describes the 1.2337 divisor as something that "defines the original
synthetic arrays, not a mean-delay normalization or a verified physical medium."
The physics note now identifies it as π²/8, the mean-conversion factor of the
complete Williamson response. The docstring is not wrong about what the code
does. It is stale about what the number is. Editing it is outside this task's
stated constraints, so this is a flag only.

**F. Primary-source page attributions are UNKNOWN to me.**
I did not re-fetch Lambert & Rickett 2000, Cordes & Lazio 2001, Williamson 1972,
or the Cordes et al. 2026 draft. Every equation number and page in
`physics-sources.md` rests on the physics researcher's own verification. What I
can report: every consequence derivable from those citations that I checked is
internally consistent, including the β=4 logarithmic divergence matching the
stated `ln[1+4/(q_o b)²]` form. The note's explicit list of uninspected sources
(Ostashov & Shishov, Lambert & Rickett 1999, Lee & Jokipii 1975, Williamson
1975) is appropriately marked.

## What I verified

### Reproduction

```
MPLCONFIGDIR=/tmp/faber2026-mpl analysis/.venv/bin/python \
  analysis/docs/analysis/scattering-mathematical-foundations/checks.py
```

All 13 keys reproduce `check-results.json` value for value, including
`williamson_mean: 1.2337005501361702` and both rank-fallback log-likelihoods.

Note for a later session: the project `uv run --frozen` path fails under this
sandbox on a cache permission error, and the system Python lacks `emcee`.
Invoking `analysis/.venv/bin/python` directly with `MPLCONFIGDIR` set is what
works.

### Statistics claims

| Claim | Where | Result |
| --- | --- | --- |
| Proper Gaussian marginal equals full-rank implementation | statistics §3 | VERIFIED, error 0.0 |
| Rank-one fallback drops an informative weak mode | statistics §3 | VERIFIED, -20.7586 vs -5015.6534 |
| Large-`s²` penalty is `−(N/2)log s²`, code docstring says `+` | statistics §4, index table | VERIFIED, step -4.60517 matches `−(2/2)log 100` |
| Flat prior drops `−T/2·log(2πσ²)` | statistics §4 | VERIFIED at `burstfit.py:817-856` |
| Log-uniform transform `exp[log a + u log(b/a)]` | statistics §5 | VERIFIED, `_JointPriorTransform` |
| `tau_1ghz` and `zeta_*` log-flagged, `beta` uniform | statistics §5 | VERIFIED, `_joint_prior_spec_gain_multi` |
| Ordered arrival-time prior, min-spacing shrinks width | statistics §5 | VERIFIED by hand, `N!/W^N`, `W−(N−1)δ` |
| `build_priors` supplies the bounds | statistics §5 | VERIFIED, imported at `:66`, used at `:455`, `:456`, `:481`, `:482`, `:532`, `:533`, `:560` |
| β≥3.98 branch carries prior mass 0.02 | statistics §5 | VERIFIED, default β prior is U[3,4] |
| dynesty static sampler, `rwalk`, `nlive=600`, `dlogz=0.5` | statistics §6 | VERIFIED, `fit_joint_scattering` |
| `dynesty==3.1.0` fixed | statistics §6 | VERIFIED, `pyproject.toml:13,42` and `uv.lock` |

### Physics claims, the four named targets

**Square law gives an exponential, and α=4 does not identify β=4.**
`∫d²ϑ B = Γ(0) = 1` and `p(t) = (π/A)B(√(t/A))` reproduce the stated result. For
the counterexample I re-derived the inner-scale-dominated limit independently: at
β=11/3 with `r_diff ≪ ℓ_i`, the structure function is locally quadratic, giving
`r_diff ∝ λ⁻¹`, `ϑ_d ∝ λ²` and `τ ∝ λ⁴`. An exponential response together with
α=4 is therefore consistent with Kolmogorov turbulence and a large inner scale.
The non-uniqueness claim stands.

**The 2<β<4 domain.** The small-`q` integrand behaves as `q^{3−β}`, which
converges only for β<4, while the large-`q` integrand behaves as `q^{1−β}` and
converges only for β>2. The stated domain is exactly that intersection. I
re-derived `α = 2β/(β−2)` as well, and β=11/3 gives 4.4.
Code agrees: `alpha_from_beta` returns `4.0` at `beta >= 3.98` and
`2β/(β−2)` below, and `default_joint_beta_bounds()` evaluates to `(3.0, 4.0)`.
The unsaturated left-limit α is 4.020202…, numerically 4.02122 at β=3.979, as
`physics-sources.md:143` states.

**β=3 exact solution.** `Γ(b) = exp[−b/(2r_diff)]` leads to
`p(t) = [2t_*]⁻¹(1+t/t_*)^{−3/2}` with `t_* = A/(4k²r_diff²)`. Normalization
checks. The 1/e time is `(e^{2/3}−1)t_*`. The Hankel identity in `checks.py:76`
is also correct algebraically: both sides equal `0.25/(0.25+δ)^{1.5}`, and it
reproduces numerically to 3.9e-14.

**Williamson coefficients and the π²/8 mean.** Derived independently from
`sech(πx/2) = (4/π)Σ_{n odd}(−1)^{(n−1)/2} n/(n²+x²)`. The transform is
`sech[(π/2)√s]`, area 1, mean π²/8. The implemented heavy-tail kernel `h` is
twice a Lévy one-half density with `a = (π/2)√τ_w`, hence area 2 and divergent
mean. Expanding `sech(y) = 2Σ_k(−1)^k e^{−(2k+1)y}` shows `h` is exactly the n=1
term of the full series. The full-sightline Eq. (21) transform
`π√(τs)/sinh[π√(τs)]` expands as `1 − y²/6`, giving mean π²τ/6. All of this
matches `physics-sources.md` §6.

I also cross-checked the script's own two-series switch at t = 0.3, 0.6, 1.0,
1.5, 2.0. The two branches agree to 1.1e-16 where they overlap.

### Judgment on the audit's framing

The scope discipline is right. `index.md:59-63` correctly labels the
counterexample as a bounded mathematical failure of equivalence rather than a
measured failure rate, and `index.md:6-9` does not overstate. At
`index.md:65-74` the audit corrects its own earlier memo honestly: arbitrary for
the truncated expression alone, identifiable once the full model is named, and
the earlier draft left standing as history. Nothing in the three
documents claims real-burst impact, and nothing claims scientific validation.

## Disposition

Approve. Findings A through D are revise-level cleanups to the audit documents
and `checks.py`, none of which change a conclusion. E and F are recorded for
whoever owns those lanes. The audit is a sound basis for the "do not start
another fitting campaign" position it takes.


## Final correction record

The four requested cleanups are applied: regularized-system rationale made explicit; continuous normalization check distinguished from discrete sampling; source ranges corrected; bare assertions replaced by runtime checks, with rank-error target derived analytically. Checks run in normal and optimized Python; a forced failed check verifies that optimization cannot suppress failure. Production code remains unchanged.
