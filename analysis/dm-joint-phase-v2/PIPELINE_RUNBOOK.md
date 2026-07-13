# Custom joint DM-phase campaign

This workflow replaces the adaptive-arrival status gate for the manuscript DM
measurements. It keeps the published `DM_phase` coherence statistic, but makes
the search grid, cutoff study, resolution study, uncertainty budget, joint
model, diagnostics, and provenance explicit and testable in this repository.

## End-to-end run

Run from the repository root in the project Python environment:

```bash
python -m scripts.run_joint_dm_phase
python -m scripts.validate_joint_dm_phase
python -m scripts.render_joint_dm_diagnostics
python -m scripts.write_joint_dm_provenance
pytest -q tests/test_dm_joint_phase.py tests/test_dmphase_recovery.py
```

The runner parses the exact pre-dedispersion DM from every product filename; it
does not use the rounded DM column in `data-manifest.csv`. For each CHIME and
DSA product it:

1. robustly normalises and masks channels;
2. crops a 30 ms burst-centred window;
3. searches a +/-1 pc cm^-3 coarse grid at 0.01 pc cm^-3;
4. repeats the fit at native, frequency-averaged, time-averaged, and jointly
   averaged resolutions;
5. selects the finest member of the stable resolution cluster;
6. searches a 0.002 pc cm^-3 fine grid and automatically expands any grid with
   a boundary maximum;
7. repeats the phase-coherence integral at 500, 1000, 1500, 2500, and 5000 Hz;
8. estimates channel sensitivity with 12 leave-one-block-out jackknifes; and
9. quotes the largest of cutoff, resolution, jackknife, and numerical-floor
   uncertainty terms.

All 24 final real-data fits selected native frequency and time resolution. No
averaging was required to obtain a stable maximum.

## Joint fit

CHIME and DSA are first fitted independently. Consistent measurements are
combined by inverse variance. When their scatter is larger than their stated
errors, a non-negative between-band term is fitted until the two-point
random-effects statistic has Q=1. This prevents one formally narrow band fit
from hiding a real morphology-dependent band offset.

`PASS_SYSTEMATIC` means that both independent fits passed the same peak and
resolution gates, but the joint uncertainty includes this between-band term.
It does not mean that either band was unconstrained.

## Evidence and provenance

- `results/dm_joint_phase_v2/fits.json`: complete curves, cutoffs,
  jackknifes, resolutions, and joint fits.
- `results/dm_joint_phase_v2/diagnostics/summary.md`: manuscript-facing table.
- `results/dm_joint_phase_v2/diagnostics/all_events_contact_sheet.jpg`: visual
  audit of all events.
- `results/dm_joint_phase_v2/diagnostics/*_joint_dm_diagnostic.png`: full
  per-event evidence.
- `results/dm_joint_phase_v2/validation/injection_recovery.json`: held-out
  CHIME/DSA single- and double-component injection matrix.
- `results/dm_joint_phase_v2/run_provenance.json`: SHA-256 fingerprints for
  all 24 raw products, the result file, and the implementation scripts.

The diagnostics must be regenerated and visually reviewed after any algorithm,
data-product, grid, or uncertainty change.
