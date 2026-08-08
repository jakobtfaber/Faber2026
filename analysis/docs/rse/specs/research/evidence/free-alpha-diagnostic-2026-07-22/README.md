# Free-alpha diagnostic evidence packet

Read-only capture from h17 on 2026-07-22. It preserves three diagnostic
families: six scintillation-gain products, seven component-leakage products,
and five tail-plus-component products. Ten component-grid products and all six
scintillation products have successful, empty-error Slurm logs. Two additional
pilot products have no recovered launch logs. It also preserves current driver,
job-script, fitter-provenance, and campaign-input bytes.

The copied evidence totals about 260 KiB. `SHA256SUMS` binds all 60 copied
artifact. `manifest.json` records the host, environment, remote paths, code
commits, and important limitations: the driver and fitter provenance were
untracked in their h17 worktree, so no repository commit proves they are the
exact runtime bytes. The campaign-input records postdate the injections by one
day. Only physical injection parameters needed to check the landed bias
arithmetic are embedded; sampler and runtime settings remain incomplete.
Observed environment versions may have drifted since the July 18 runs.

Verify from a clean checkout with Python 3.10 or newer; only the standard
library is required:

```bash
python3 docs/rse/specs/research/evidence/free-alpha-diagnostic-2026-07-22/verify_packet.py
```

The verifier checks hashes and the exact filesystem roster, input diagnostic status,
the analytic within-channel modulation suppression, posterior ordering,
bias arithmetic, agreement between scheduled products and logs, successful
return codes, empty error logs, and the reported bounds. `grid_roster.json`
records every recovered multi-component product and distinguishes the two
unlogged pilots.

Recovered bounds are exact over these rosters: the minimum component-only bias
is `-0.43040582429955254` among seven products; the minimum combined-tail-and-
component bias is `-0.8561575297363464` among five. These grids did not reproduce
the approximately `-1.6` anomaly. They do not universally exclude either
mechanism outside the recovered tested envelope.

Independent parsing found one metadata-only defect. The driver constructs an
inclusive 400--800 MHz frequency grid, so the spacing used in the effective
modulation calculation is 400 MHz divided by `nchan - 1`. The JSON field
`chan_width_mhz_target` records the nominal 400 MHz divided by `nchan` value.
The stored effective modulation values agree with the actual grid spacing, so
the injection and leakage bounds are unaffected. Do not reuse the nominal JSON
field as the exact simulated channel spacing.
