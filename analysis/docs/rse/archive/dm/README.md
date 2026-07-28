# Archived dispersion-measure work (historical — superseded)

Everything in this directory is **historical**. No manuscript DM traces to
these documents. The current authority for all twelve burst DMs is the
phase-coherence campaign in `analysis/dm-joint-phase-v2/`
(`manuscript_dm_catalog.csv`), adopted per
[`docs/rse/specs/verified-dm-adoption-2026-07-13.md`](../../specs/verified-dm-adoption-2026-07-13.md)
(CHIME phase-coherence DM is the measurement; DSA is the independent
cross-check).

Contents and why each is archived:

- `plan-dm-measurement-methods.md`, `research-dm-measurement-methods.md` —
  the multi-method battery campaign (vendored DM_phase / DM-power packages,
  in-tree variants, arrival regression, injection matrix). Its purpose was
  served: it proved the earlier in-tree DM-power null on DSA was an
  implementation artifact. Phases 2–3 were never completed; the phase-suite
  path superseded it. Keep as validation evidence only.
- `plan-dm-phase-suite-end-to-end.md` — the phase-suite campaign charter.
  Version 1 of the suite was retracted (baseline-DM and fit-gate
  implementation flaw); version 2 (`dm-joint-phase-v2`) is the adopted
  implementation and lives outside this archive.
- `v6-association-dm-report-2026-07-07.md` — the V6 re-validation of the
  inherited DSA catalog DMs (`bursts.yaml`, ±0.1 placeholder errors). Those
  catalog values are superseded as `DM_obs`.
- `battery-memos/` (formerly `docs/rse/specs/dm/`) — per-run memos from the
  battery era, including the 2026-07-07 DM provenance audit.
- `deck-dm-campaign-2026-07/` (formerly `docs/rse/decks/dm/dm-campaign-2026-07/`)
  — battery-era contact sheets and diagnostic figures.

Diagnostic-only survivors (not archived, but not adopted numbers): the
CHIME+DSA inverse-variance and random-effects combinations in the adopted
catalog, retained as sensitivity tests.
