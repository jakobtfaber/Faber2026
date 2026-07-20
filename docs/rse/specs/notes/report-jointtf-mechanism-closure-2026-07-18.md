# Report: Joint-TF model-selection verdict + mechanism elimination (evening closure)

---
**Date:** 2026-07-18 (evening)
**Author:** AI Assistant (team-lead session; compute agent: teammate "joint-tf-fits")
**Status:** Report — supersedes the interpretation-pending items of
`handoff-2026-07-18-14-51-jointtf-plpbf-campaign.md` (that handoff remains the
mid-day snapshot; this report carries the completed verdicts).
**Live deck:** https://jakobtfaber.github.io/Faber2026/decks/jointtf-day2/ (slide 6 = the full model-selection + mechanism story)

---

## 1. Three-way model selection — COMPLETE, both bursts

| model | casey β / lnZ / Δ | wilhelm β / lnZ / Δ |
|---|---|---|
| production (exp PBF, α=4 tie) | 3.990 / −33574.6 / — | 3.990 / −16496.2 / — |
| free-α wedge (still EMG; diagnostic) | 3.666 / −28038.0 / **+5537** | 3.965 / −15765.2 / **+731** |
| PL-PBF (α tied physical, s_i free) | 3.9999 / −33571.3 / **+3.3** | 3.9994 / −16499.5 / **−3.3** |

**Verdict: PL-PBF collapses to production on both bursts** (s_i upper-rail /
unconstrained: casey log10 s_i = 1.70 [−0.17, +3.20], wilhelm 1.40 [−0.24, +3.13];
τ byte-identical to production; ΔlnZ at sampler-noise level). The exponential
per-frequency pulse shape is adequate; a heavy-tailed screen is rejected by direct
Bayes-factor test on both railed bursts. **PL-PBF does NOT become the campaign
default; the production EMG family and its β>3.98 / α=4 limits stand, hardened
against PBF-shape systematics.** Recorded in FLITS-side
`PLPBF_FITTER_PROVENANCE.md` (Results 2026-07-18).

## 2. Mechanism elimination for the wedges — COMPLETE

The free-α wedges (+5537 casey, +731 wilhelm; both still-EMG diagnostic fits) are
**chromatic-scaling anomalies**: τ(ν) deviates from ν⁻⁴ for a cause that is, by
quantitative exclusion, none of:

| mechanism | test | max α-bias reached | needed (casey) | status |
|---|---|---|---|---|
| gross single-component tail | harsh-tail injections (s_i→1000) | −0.21 (W/τ=0.3); −0.01 casey-matched | −1.6 | excluded |
| unfit close secondary (leakage) | leakage grid (amp×offset) | −0.43 (amp 0.2, dt 0.1 ms); sign flips + at dt≥0.3 | −1.6 | excluded |
| tail + secondary combined | both-at-once grid | −0.86 plateau (and casey has no heavy tail per §1) | −1.6 | excluded |
| frequency-coherent peak dipole | dipole-mask (exact √w exclusion + 10× down-weight; free-vs-tied on shared masked data) | wedge survives: casey +3540/+3795 of +5537, wilhelm +634/+586 of +731; α stays 2.27/2.75 | — | **excluded (DISTRIBUTED verdict, both)** |
| scintillation-gain leakage | 6-run bound at 2L Δν_d, m=1 maximal, real channelization; static controls | bias −0.003; all runs recover α≈4 | −1.6 | excluded |

**Sole surviving hypothesis: two-screen chromaticity** (two scattering screens
with different τ(ν) mixing across the CHIME/DSA lever arm). This is a hypothesis
**by elimination** — no forward two-screen model has been fit. Decision framing:
`decision-two-screen-charter-2026-07-18.md`.

Secondary finding (flagged separately on the deck): the two β-ceiling rails have
different origins — **casey's rail is peak-associated** (masked-tied β = 3.44,
CI ±0.01, tightly excludes 3.99; diagnostic of what pins the rail — production
limits stand on unmasked data), **wilhelm's rail is intrinsic** (survives peak
excision unchanged). The dipole magnitudes track the wedge magnitudes across
opposite instruments (casey C ±32σ ↔ +5537; wilhelm D ±26σ ↔ +731; N=2).

## 3. Count-audit state (tasks #10–#12)

- **zach**: C2D4 at 131 µs collapsed (ΔlnZ −2.3, params identical → 4th
  component found nothing; owner ground truth 1+3 stands). Root cause of the
  earlier window bug (peak-anchored window truncating the +2.06/+2.52/+3.01 ms
  cluster members) fixed with a DSA-only envelope window (5.90 ms, all four
  members in-window, CHIME byte-unchanged); fine pair C2D3/C2D4 at native
  32.8 µs running (jobs 133/134); mode-check protocol (healthy β≈3.98 vs
  trapped β≈3.16) gates any evidence read.
- **whitney**: count confirmed C2D2; the β=3 "floor rail" is
  **gain-systematic-dominated** (flat 3.025 / s2=100 3.429 / s2=10 3.988 at the
  same count; τ swings 27×; +5540 for s2=100 over s2=10 among proper priors).
  In `COMPONENT_COUNT_LADDER_AUDIT.md` as the task-#12 classification.
- **phineas**: neighbor tests favor C4 (+75) and D4 (+27); C4D4 peak test
  re-running (job 120, restarted in the scheduler fix).
- **johndoeII**: C3 "win" (+47) rejected as τ-runaway (0.114→2.25); held at
  C2D2 pending visual vet.
- **hamilton**: same-corner-as-whitney probe running (gain sweep s2=100/s2=10 +
  first-ever neighbor counts C5D1/C4D2; its C4D1 was hand-assigned).
- Standing guardrails added this cycle: window-contains-all-candidate-components
  (after the zach truncation catch); snapshot-before-overwrite; mode-check
  before count Bayes factors; component vetting before figure publication.

## 4. Infrastructure fixed this cycle

- **fit_pool.sbatch had no `--mem` directive** → submissions claimed the whole
  95 GB node ledger, serializing the queue against 38 idle CPUs. Fixed durably
  (`--mem-per-cpu=1G`, teammate-applied) after a requeue+ledger surgery landed
  a 15-job parallel wave.
- Dipole-mask primitive: per-time-bin exclusion/down-weight via √w scaling of
  data+kernel columns in the gain-marginal sufficient statistics (w=0 exact
  exclusion; noise-inflation same knob). Driver-only, validated.
- Scint-leakage injection driver: generator2d decorrelating-scint physics
  generalized to τ(ν)=τ·ν⁻⁴, joint free-α refit; static controls recover α≈4.

## 5. In flight at report time

zach fine pair (133/134), hamilton probes (127–129, 132), phineas C4D4 (120).
Verdicts land via journal + teammate monitors; TOA table / triptychs / flags
(task #6) remain blocked on these + owner ratifications.

## 6. Owner decisions queued

1. Ratify keeping the production EMG family (PL-PBF rejected on evidence) — §1.
2. Two-screen: charter forward model vs interpret-only — see decision brief.
3. Ratify the count-audit remediation (neighbor tests + guardrails) as method.
4. zach TOA exception if D4 wins only at fine binning.
5. 2L scintillation table ratification (separate lane; used here only as
   diagnostic-grade bound inputs).
