# Retired pipeline

`dsa110-FLITS` and the former parent-repository `pipeline/` submodule are fully
retired. They are historical provenance only.

All active fitting, foreground, dispersion, scattering, scintillation, and
shared plotting code is housed in this `Faber2026-analysis` repository. The
only supported environment is the local `pyproject.toml` and `uv.lock`.

Do not add a FLITS package dependency, restore the `pipeline/` submodule, or
read a sibling FLITS checkout at runtime.
