# Local analysis code provenance

The `analysis` repository is the sole active code and dependency authority.
It does not import, install, or read a sibling `pipeline` or `dsa110-FLITS`
checkout.

Code incorporated during the retirement:

- `radio_pipeline/`, scattering, scintillation, dispersion, crossmatching, and
  simulation code: recovered from retired source commit
  `ac960872c8da2e9c6fe11da15a4ff8cbd5538aaa`.
- `foregrounds/`: canonical foreground census, propagation, and visualization package
  commit `ee781f7`.

Imports were renamed to the local `radio_pipeline` package. The active
dependency lock contains no `flits` distribution or retired Git source.
Scientific outputs remain subject to their own tests, provenance records, and
manuscript-adoption gates; source incorporation alone is not scientific
validation.
