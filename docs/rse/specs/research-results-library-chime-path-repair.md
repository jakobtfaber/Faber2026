# Research: Results-library and CHIME-path repair

**Date:** 2026-07-20
**Scope:** Internal codebase and live local custody surfaces
**Code state:** parent `74b7dd6d`; pipeline `c6111390`
**Related Documents:** [accepted repair decision](../wayfinder/tickets/authority-13-choose-link-and-chime-path-repair.md)

## Question / Scope

Can the accepted results-library and full-resolution CHIME/FRB path repair be
executed exactly as listed, without touching excluded bytes, historical
receipts, scientific trust, or unlisted current consumers?

## Codebase Findings

### Results-library mechanics

- The catalog has 18 entries and constrains trust and link modes
  (`scripts/results_library_catalog.yaml:1-214`). The external inventory still
  has 19 entries and names the noncanonical JointTF worktree as its code root.
- The builder has no exact-entry selection or receipt interface; it loops over
  the whole catalog (`scripts/build_results_library_inventory.py:312-381`) and
  exposes only broad link/force controls
  (`scripts/build_results_library_inventory.py:457-498`).
- `link_dest()` maps a sole source to the slot root
  (`scripts/build_results_library_inventory.py:212-224`). That is wrong for
  `analysis/dm-joint-phase-v2/results/diagnostics`: verified bytes live at the
  nested `dispersion/dm-joint-phase-v2/diagnostics` destination. Running the
  current materializer for this entry would create the wrong repository link.
- The materializer supports entry-level `--only`
  (`scripts/materialize_results_library.py:123-150`) and rejects both-real
  conflicts (`scripts/materialize_results_library.py:112-113,157-159`), but it
  inherits the destination bug.
- Live inspection found eight broken library links into the absent
  `Faber2026-results-library-b` worktree, two absent catalog destinations with
  live sources, and three absent repository links with verified real library
  bytes. The two both-real cases remain excluded. No scoped path had an open
  file.
- The three repository-side source trees match their pre-relocation Git blobs:
  11/11 `fit_summaries`, 11/11 `ppc`, and 17/17 `diagnostics` files.

### Full-resolution roots

- The live authorities are separate and complete: 12 CHIME/FRB cubes under
  `~/Data/Faber2026/chimefrb/CHIME_bursts` and 12 DSA-110 cubes under
  `~/Data/Faber2026/dsa110/DSA_bursts`.
- Parent producers still route both bands through one DSA-root argument in the
  gallery (`scripts/plot_codetection_gallery.py:163-177,251-298,410-416`),
  triptych (`scripts/plot_codetection_triptych.py:284-384,410-425`), data grid
  (`scripts/plot_codetection_data_grid.py:104-130,271-310,346-375`), L0
  certificate builder (`scripts/build_l0_certificates.py:36-38,92-150`), and
  Figure 1 audits (`scripts/audit_fig1_frequency_axes.py:103-140,223-243`;
  `scripts/audit_fig1_residual_drift.py:63-71,138-194`).
- `scripts/audit_fig1_axes.py:61-69,298-317` is an unlisted direct gallery
  caller. Changing the listed gallery API without changing it breaks the
  current audit.
- Pipeline producers share the same defect in
  `pipeline/dispersion/dm_power_analysis.py:320-378,785-805` and
  `pipeline/flits/batch/codetection_data.py:66-91,296-312`.
  The battery configuration is also consumed by four unlisted current files:
  `pipeline/dispersion/dm_phase_analysis.py:113-173,524-547`,
  `pipeline/dispersion/dm_campaign/run_battery.py:43-54`,
  `pipeline/dispersion/dm_campaign/adaptive_arrival.py:49-56`, and
  `pipeline/dispersion/dm_campaign/run_adaptive_arrival.py:50-63,240-247`.
  Updating only the listed configuration breaks those consumers.
- The listed joint-DM runner is inside a recorded exact historical source
  snapshot (`analysis/dm-joint-phase-v2/code/README.md:36-42`) whose provenance
  pins its hash (`analysis/dm-joint-phase-v2/results/run_provenance.json:39-45`).
  Editing it would invalidate that historical claim. Its recorded inputs
  already name the correct split roots
  (`analysis/dm-joint-phase-v2/results/run_provenance.json:46-66`).

### Input identifiers

- The twelve July 18 remediation records contain MD5 hashes but no producing
  Git identity or SHA-256 manifest. Three Freya package manifests contain
  SHA-256 hashes but no producing Git identity or separate provenance receipt.
- Under the accepted fail-closed rule, none currently qualifies for a stable
  input row. They must remain explicit exceptions; no identity should be
  fabricated in this repair.

## Synthesis

The link repair is technically bounded after exact nested destinations,
selection, receipts, tests, and rollback preimages are added. It must not run
through the current materializer first.

The full-resolution root repair cannot be implemented within the accepted
exact file list. Five direct consumers were omitted, and the listed joint-DM
runner is a frozen historical snapshot. Safe implementation requires an owner
scope decision: add the five current consumers and replace the historical-file
edit with a current wrapper, or narrow the batch and leave the mixed-root
interface unresolved.

## References / Sources

- [Accepted repair decision](../wayfinder/tickets/authority-13-choose-link-and-chime-path-repair.md)
- `scripts/results_library_catalog.yaml`
- `scripts/build_results_library_inventory.py`
- `scripts/materialize_results_library.py`
- Parent and pipeline producer files cited above
- Live `~/Data/Faber2026/results-library` and split full-resolution roots
