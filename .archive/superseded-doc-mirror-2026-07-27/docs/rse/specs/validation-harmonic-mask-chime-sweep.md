# Validation: harmonic-mask default-on sweep of the remaining CHIME configs

> Validated against action item 2 of
> `handoff-2026-07-05-23-24-flits-130-harmonic-mask-merge.md` (no `plan-*.md`
> exists for this lane; the handoff's action item is the specification) at
> Faber2026 commit `61b8710`, pipeline pin `028fa7c`, on 2026-07-05.

## Scope

FLITS PR #130 enabled `analysis.fitting.harmonic_mask
{enable: true, spacing_mhz: 0.390625, halfwidth_mhz: 0.05}` in all four CHIME
burst configs and (commit `634920b`) wired the block through the
config-driven CLI. Only `freya_chime_hi` had been A/B-validated. This
validation reruns the remaining three configs — `casey_chime`,
`casey_chime_hi`, `freya_chime` — masked (config as committed) and control
(single-key `enable: false` flip), and regression-checks `freya_chime_hi`
at the new pin.

## Implementation status

| Item | Status |
|---|---|
| Mask block present in all three configs at pin `028fa7c` | ✅ verified (`configs/bursts/{casey_chime,casey_chime_hi,freya_chime}.yaml`) |
| Config-CLI wiring present in pinned code | ✅ verified (`freya_scintillation.py:929–942` reads `harmonic_mask`, threads spacing/halfwidth when `enable` truthy) |
| Masked reruns of the three configs | ✅ done this session (6 runs, all exit 0, `success=true`) |
| `freya_chime_hi` regression at pin `028fa7c` | ✅ exact reproduction |

## Results (fresh runs, this session)

All runs: pinned submodule code (`scint_analysis.__file__` confirmed inside
`pipeline/`), conda `flits`, `FLITS_ROOT=<Faber2026>/pipeline`, `--no-figures`.
Controls differ from committed configs by exactly one line
(`harmonic_mask.enable: true → false`; diff-verified per config).

| Config | mask OFF (control) | mask ON (default) | Δ | struct. x-check (mask-indep.) |
|---|---|---|---|---|
| casey_chime | 28.05 ± 32.47 kHz | 23.32 ± 36.54 kHz | −4.73 kHz (−16.8%) | 64.6 kHz |
| casey_chime_hi | 60.07 ± 38.94 kHz | 64.81 ± 38.50 kHz | +4.74 kHz (+7.9%) | 249.8 kHz |
| freya_chime | 54.13 ± 10.32 kHz | 59.07 ± 8.29 kHz | +4.95 kHz (+9.1%) | 91.6 kHz |
| freya_chime_hi (regression) | 35.19 ± 4.42 (prior session) | **42.21 ± 2.76 — exact match to recorded arm-B1/config-A/B value** | +7.02 kHz | — |

Modulation indices for the record: casey_chime m_acf 4.95→5.52 (off→on),
casey_chime_hi 5.60→5.51 (fitted m = −5.30, unphysical), freya_chime
2.65→2.68. Structure-function cross-checks are identical on/off, as expected
(the mask acts only on the ACF fit-lag selection).

## Verification detail

- **Mask engagement evidence:** the pinned code emits no log line when the
  mask applies (checked `analysis.py` / `freya_scintillation.py` — silent
  path), so engagement is proven by the A/B deltas themselves: on/off runs
  from configs differing by exactly one key produce different fitted Δν in
  every pair, and `freya_chime_hi` reproduces the arm-B1 masking oracle to
  the last decimal.
- **Exit status:** all 7 runs exit 0, `acf.success = true`, `message: ok`.
- **Fit-window scan:** not configured in these three configs
  (`fit_lag_scan_mhz` absent → `fit_window_scan: null`); the recorded numbers
  are single-window (`fit_lagrange_mhz` as committed).

## Interpretation (validation, not adoption)

1. **No delta exceeds ~0.5σ of its own fit error.** The mask shifts all three
   configs by ≈ ±5 kHz, far inside the ±8–39 kHz statistical errors. Enabling
   the mask by default changes no scientific conclusion for these bursts.
2. **None of these numbers is manuscript-citable, mask or no mask:**
   - Both casey fits are non-detections at face value (Δν consistent with
     zero at ≲1.7σ; m_acf ≈ 5; casey_chime_hi fitted m negative).
   - The casey npz pair predates the 2026-07-04 h17 de-dispersion fix — the
     2026-07-03 lane closeout records that casey (with isha, mahi, phineas)
     **still carries the upchannelization defect**; regeneration has not been
     requested.
   - The freya CHIME tens-of-kHz scale is retracted as instrumental
     (`experiment-freya-chime-dnu-science-readiness.md`).
   These are config-default tracking numbers, recorded so a future rerun is
   not mistaken for a regression.

## Manual / decision items (unchanged from handoff)

- **Canonical-adoption decision (handoff item 1)** remains with the owner:
  which CHIME Δν number (masked vs unmasked) any doc or tex quotes, and why.
  The experiment doc's arm-B1 section now carries the factual note that the
  mask is config-default (updated this session).
- Optional: regenerate the DSA γ(ν) summary figure via
  `plot_subband_gamma_summary` (handoff item 3) — not touched here.

## Reproducibility

- **Command** (per config, from a FLITS checkout root):
  `cd scintillation && FLITS_ROOT=<checkout> conda run -n flits python -m
  scint_analysis.freya_scintillation configs/bursts/<cfg>.yaml --out <dir>
  --no-figures` (import name must be `scint_analysis.*` — numba cache).
- **Environment:** conda `flits`; pinned submodule at `028fa7c` (run from
  inside `pipeline/scintillation` so cwd shadows the editable install —
  verified via `scint_analysis.__file__`).
- **Data:** `~/Data/Faber2026/dsa110/scintillation-data/{casey_chime,
  casey_chime_hi,freya_chime,freya_chime_hi}.npz`, reached through the
  gitignored symlink `pipeline/scintillation/data` (created this session;
  matches the canonical-clone convention).
- **Preserved outputs:** result JSONs for all 7 runs at
  `~/Data/Faber2026/dsa110/scintillation-data/exp-hm-config-sweep-2026-07-05/`.
  Control configs (`*_hmoff.yaml`) were session-temporary and deleted after
  the sweep.

## Recommendations

- **Critical:** none — the implementation validates.
- **Important:** before any casey CHIME number is used anywhere, regenerate
  the casey npz pair from a de-dispersion-fixed h17 product (defect lane,
  regeneration not yet requested).
- **Nice to have:** a one-line INFO log in `measure_scintillation_bandwidth`
  when the harmonic mask engages (silent-path engagement had to be proven by
  A/B here).
- **Follow-up:** handoff items 1 (adoption decision — owner) and 3 (γ(ν)
  figure export) remain open.

## References

- [handoff-2026-07-05-23-24-flits-130-harmonic-mask-merge.md](handoff-2026-07-05-23-24-flits-130-harmonic-mask-merge.md)
- [experiment-freya-chime-instrumental-origin.md](experiment-freya-chime-instrumental-origin.md)
- [experiment-freya-chime-dnu-science-readiness.md](experiment-freya-chime-dnu-science-readiness.md)
- [handoff-2026-07-03-18-22-freya-scint-lane-closeout.md](handoff-2026-07-03-18-22-freya-scint-lane-closeout.md)
