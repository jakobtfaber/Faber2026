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
python campaigns/burst_energies/measure_data_fluences.py \
  --chime-data-dir ~/Data/Faber2026/chimefrb/CHIME_bursts \
  --dsa-data-dir ~/Data/Faber2026/dsa110/DSA_bursts \
  --dsa-beam-cube /path/to/DSA110_beam_1.h5 \
  --output campaigns/burst_energies/data_fluences.candidate.csv

python campaigns/burst_energies/build_data_driven_energies.py \
  --fluences campaigns/burst_energies/data_fluences.accepted.csv \
  --output campaigns/burst_energies/burst_energies.data.json

python campaigns/burst_energies/verify_data_driven_energies.py \
  campaigns/burst_energies/burst_energies.data.json
```

Candidate receipts never become accepted by renaming alone. Review the dynamic
spectra and window diagnostics, validate the correlated-noise uncertainty, then
record `review_status=accepted` and `noise_status=accepted` explicitly.
The builder fails closed on missing, unstable, uncalibrated, or unreviewed bands.

`burst_energies.json`, `burst_energies.tex`, and
`recompute_energies.py` are legacy fitted-amplitude cross-checks. They are not
manuscript inputs.
