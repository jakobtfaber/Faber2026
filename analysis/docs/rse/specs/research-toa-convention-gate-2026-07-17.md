# Research: ToA convention and model-correction gate

**Date:** 2026-07-17
**Scope:** Internal codebase and pinned dependency
**Codebase state:** Faber2026 `e4b79f80`; pinned dsa110-FLITS `5fb387e`

## Question / Scope

Which CHIME-minus-DSA arrival-time field is currently citable, and do the
manuscript, local producers, generated provenance, and pinned FLITS contract
use that field consistently? This audit covers the association and ToA prose,
the sample-table and association producers, the ToA-decomposition producer,
the reproducibility manifest, and the pinned crossmatch implementation. Figure
1 rendering and scintillation outputs are explicitly outside this lane.

## Codebase Findings

- The pinned crossmatch gates model adoption on two conditions:
  `model_fit_quality == "PASS"` and `model_figure_reviewed`; otherwise it
  preserves the peak offset in `measured_offset_ms` and marks the candidate
  model field diagnostic-only
  (`pipeline/crossmatching/toa_crossmatch.py:317-332`).
- All twelve committed rows are `diagnostic_only:MARGINAL`; all twelve input
  fits have `model_figure_reviewed=false`. In every row,
  `measured_offset_ms == peak_measured_offset_ms`, while
  `model_corrected_offset_ms` is retained separately as a diagnostic
  (`pipeline/crossmatching/toa_crossmatch_results.json:13-31`).
- The association report explicitly computes its timing summary from
  `peak_measured_offset_ms` and labels the convention `observed_peak_400MHz`
  (`pipeline/crossmatching/association.py:222-258`). The sample-table and
  association-summary producers consume `measured_offset_ms`, so at the pinned
  state they also use the peak convention
  (`scripts/make_sample_table.py:88-109`,
  `scripts/plot_association_summary.py:90-122`).
- The manuscript contradicts that fail-closed state by saying that model ToAs
  are adopted and primary (`sections/toa.tex:51-55`,
  `sections/toa.tex:72-78`, `sections/toa.tex:113-124`). Its ToA-decomposition
  figure and caption also consume and promote `model_corrected_offset_ms`
  despite the diagnostic status (`scripts/plot_toa_offset_decomposition.py:43-53`,
  `sections/toa.tex:314-323`).
- The manifest row is stale in both field name and state: it says the producer
  reads `measured_offset_ms`, calls the output an adopted model-$t_0$ figure,
  and describes a pending pin switch, although the producer now explicitly
  reads `model_corrected_offset_ms` and the current pin already implements the
  fail-closed gate (`repro_manifest.csv:39`).
- The pinned FLITS `reproduce_model_result` docstring still says that
  `measured_offset_ms` reports the intrinsic model offset, although the
  implementation only does so after the gate passes
  (`pipeline/crossmatching/toa_crossmatch.py:278-290`,
  `pipeline/crossmatching/toa_crossmatch.py:317-332`). This is documentation
  drift in FLITS, not a reason to move the parent gitlink in this lane.

## Synthesis

The current citable association convention is the observed peak after both
bands are referred to 400 MHz with the shared DSA DM. The model-corrected field
is useful as a named diagnostic, but no current row has cleared the two-part
adoption gate. The smallest consistent repair is therefore to keep the
physics/method definition of the candidate correction, state its diagnostic
status, make the manuscript-facing decomposition read the canonical
`measured_offset_ms`, and add an audit that rejects future model promotion
while any row remains unvalidated. The FLITS docstring should be corrected in
its own repository without changing this branch's submodule pointer.

The Figure 1 producer also contains model-anchor language, but Figure 1 is an
owner-rejected, separately assigned regeneration lane. This audit records that
coupling and does not edit or regenerate Figure 1.

## References / Sources

- `sections/toa.tex`
- `scripts/plot_toa_offset_decomposition.py`
- `scripts/make_sample_table.py`
- `scripts/plot_association_summary.py`
- `scripts/consistency_audit.py`
- `repro_manifest.csv`
- `pipeline/crossmatching/toa_crossmatch.py`
- `pipeline/crossmatching/toa_crossmatch_results.json`
- `pipeline/crossmatching/association.py`
- `pipeline/crossmatching/notebook_reproduction_fixture.json`
- `docs/superpowers/plans/2026-07-07-two-telescope-model-toas.md`
