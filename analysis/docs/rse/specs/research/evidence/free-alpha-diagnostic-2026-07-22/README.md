# Free-alpha diagnostic evidence packet

Read-only capture from h17 on 2026-07-22. It preserves the six July 18
scintillation-gain-leakage products, their successful and empty-error Slurm
logs, the current driver and job-script bytes, the h17 fitter provenance, and
the two currently tracked campaign-input records.

The copied evidence totals less than 100 KiB. `SHA256SUMS` binds every copied
artifact. `manifest.json` records the host, environment, remote paths, code
commits, and important limitations: the driver and fitter provenance were
untracked in their h17 worktree, so no repository commit proves they are the
exact bytes used by the runs. The campaign-input records now available on
h17 postdate the injections by one day; the exact numerical inputs used at run
time remain embedded in each product and log. Environment versions were
observed during capture and may have drifted since the July 18 runs.

Verify from a clean checkout with Python 3.9 or newer; only the standard
library is required:

```bash
python3 docs/rse/specs/research/evidence/free-alpha-diagnostic-2026-07-22/verify_packet.py
```

The verifier checks hashes, the six-product roster, input diagnostic status,
the analytic within-channel modulation suppression, posterior ordering,
bias arithmetic, agreement between product and log, successful return codes,
empty error logs, and the reported bounds.

Independent parsing found one metadata-only defect. The driver constructs an
inclusive 400--800 MHz frequency grid, so the spacing used in the effective
modulation calculation is 400 MHz divided by `nchan - 1`. The JSON field
`chan_width_mhz_target` records the nominal 400 MHz divided by `nchan` value.
The stored effective modulation values agree with the actual grid spacing, so
the injection and leakage bounds are unaffected. Do not reuse the nominal JSON
field as the exact simulated channel spacing.
