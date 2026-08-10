# Fit-independent burst energetics

This directory separates measurement, calculation, verification, and manuscript
admission.

1. `measure_data_fluences.py` measures calibrated CHIME/FRB and DSA-110 band
   fluences directly from dynamic spectra. It consumes no fitted burst parameter.
2. `build_data_driven_energies.py` joins accepted fluence receipts to the frozen
   host-redshift sources and computes band-restricted isotropic-equivalent energy.
3. `verify_data_driven_energies.py` independently checks the output arithmetic,
   roster, hashes, and absence of fitted-parameter fields.
4. Manuscript admission remains separate: every row must pass measurement and
   provenance gates, then owner visual review.

Commands, from the analysis repository root:

```bash
python energetics/studies/burst-energies/measure_data_fluences.py \
  --chime-data-dir ~/Data/Faber2026/chimefrb/CHIME_bursts \
  --dsa-data-dir ~/Data/Faber2026/dsa110/DSA_bursts \
  --dsa-beam-cube /path/to/DSA110_beam_1.h5 \
  --output energetics/studies/burst-energies/data_fluences.candidate.csv

python energetics/studies/burst-energies/build_data_driven_energies.py \
  --fluences energetics/studies/burst-energies/data_fluences.accepted.csv \
  --output energetics/studies/burst-energies/burst_energies.data.json

python energetics/studies/burst-energies/verify_data_driven_energies.py \
  energetics/studies/burst-energies/burst_energies.data.json
```

Candidate receipts never become accepted by renaming alone. Review the dynamic
spectra and window diagnostics, validate the correlated-noise uncertainty, then
record `review_status=accepted` and `noise_status=accepted` explicitly. Accepted
rows also require a reviewed, positive `calibration_systematic_dex`; the
measurement command leaves it blank rather than inventing a missing beam-scale
uncertainty.
The builder fails closed on missing, unstable, uncalibrated, or unreviewed bands.
One accepted receipt covers all 24 event-band measurements; the builder consumes
the 16 bands with eligible redshifts and records dispositions for the other four
events. Its artifact separates statistical, window, calibration, and total
energy uncertainty.

The all-event manuscript candidate is likewise fail-closed. The current
catalog command uses `--candidate`, writes only to figure-review staging, and
marks stable, failed, and unavailable band measurements explicitly:

```bash
uv run --frozen python \
  energetics/studies/burst-energies/plot_all_event_energetics.py \
  --fluences energetics/studies/burst-energies/data_fluences.candidate.csv \
  --output figure_review/staging/energetics_all_events/figures/energetics_all_events.pdf \
  --candidate
```

Without `--candidate`, every row must have accepted window, calibration,
correlated-noise, and review status. The candidate is not manuscript-admitted.

The methods figure uses the actual central-window dynamic spectra and calibrated
fluence spectra for one stable example:

```bash
uv run python energetics/studies/burst-energies/plot_measurement_method.py \
  --dsa-beam-cube ~/Documents/DSA110_beam_1.h5
```

It writes a PDF and a hash-bound provenance receipt under `figures/`.
The figure is a candidate-method illustration, not an admitted energy result.

`burst_energies.json`, `burst_energies.tex`, and
`recompute_energies.py` are legacy fitted-amplitude cross-checks. They are not
manuscript inputs.
