# Research: Zach dedispersion reference frequencies

**Date:** 2026-07-22  
**Scope:** Internal producer-code trace  
**Codebase state:** Faber2026 `e1f75ea1`; pinned CHIME container
`sha256:f510909d892d0d5224c982c590cbe80967a49a59b79c396ab72bb710105c4c41`;
DSA beamformer `1346d53bef9224dce07e024c5f7afc06a335beac`  
**Related document:** [Zach raw-products ticket](../wayfinder/tickets/zach-analysis-01-establish-raw-products-time-axes.md)

## Question / Scope

Which frequency anchors the dedispersion delay for Zach's CHIME/FRB and DSA-110
products? Defaults count only when the invoked producer path uses them.

## Codebase findings

### CHIME/FRB

In pinned `baseband-analysis` 1.9.0,
`/opt/pysetup/baseband_analysis/core/dedispersion.py:8-43,103-115` sets
`coherent_dedisp(..., f_ref=400)` and uses it only when whole-channel
`time_shift=True`. The same file at lines 150-215 sets an omitted incoherent
reference to `min(f)`. Zach's native retained coarse-grid minimum is
400.390625 MHz.

The approved worker invokes coherent dedispersion with configurable time shift
([`upchannelize_chime.py`](../../../pipeline/analysis/scattering-refit-2026-06/baseband_recovery/upchannelize_chime.py):305-340).
The validated command used `--no-time-shift`; the worker then upchannelized the
coherently de-smeared voltages without a separate incoherent step
([validation](validation-zach-chime-preprocessing-baseline.md):153-164).
Therefore that product has no 400 MHz whole-channel shift applied. Later padded
arrival-time alignment must use the per-channel `time0` metadata and state its
chosen reference explicitly.

### DSA-110

PARSEC loads `dm_opt` before `dm_heim` from its candidate table
(`h24:dsa110-pol/dsapol/parsec.py:158-185`); its Zach row records 262.3 and
263.0 pc cm⁻³ respectively. It passes `DM0` to the offline-beamformer wrapper
(`parsec.py:1151-1207`; `polbeamform.py:49-78`). The wrapper passes that value as
`toolkit -m` for every subband
(`offline_beamforming/run_beamformer_visibs_bfweightsupdate_sb.bash:34-54`).

The exact `dsa110-bbproc/toolkit.cu:734,762-768` code states that it adds delay
to 1530 MHz and computes
`4.15 * DM * (f^-2 - 1.53^-2) / 0.065536`. The deployed binary contains the same
diagnostic string. Its SHA-256 is
`7c7268eb19878e09174f5c8997fe2d8b153cd5e14f009b663d56a93017f21e12`;
the source SHA-256 is
`6bbe433317be7e30d7fd5ec8c0be013707438be4e2d904b7754fabff7582159e`.

The Level-3 calibration path reads the already-dedispersed Stokes files and
writes calibrated arrays with their inherited header
(`h24:dsa110-pol/dsapol/polcal.py:680-710`;
`h24:dsa110-pol/dsapol/dsapol.py:495-564`). It does not choose a new reference
frequency. Zach's Level-3 filterbank is therefore dedispersed to 262.3 pc cm⁻³
at 1530 MHz.

## Synthesis

- DSA-110: confirmed reference frequency, 1530 MHz.
- CHIME coherent whole-channel shift: function default, 400 MHz.
- CHIME incoherent shift: lowest supplied frequency; 400.390625 MHz on Zach's
  native coarse grid, and factor/grid dependent after upchannelization.
- Approved Zach CHIME preprocessing: no coherent whole-channel time shift and
  no separate incoherent shift. Its later arrival-time alignment remains
  explicit downstream work.

## References / Sources

- CHIME pinned source:
  `/opt/pysetup/baseband_analysis/core/dedispersion.py:8-43,103-115,150-215`,
  SHA-256 `0e0d8713b2f3ac2b0e4082db9f878ae8e5c22d2bf9d1052928cc503e1765ca97`
- Local worker:
  [`pipeline/analysis/scattering-refit-2026-06/baseband_recovery/upchannelize_chime.py`](../../../pipeline/analysis/scattering-refit-2026-06/baseband_recovery/upchannelize_chime.py)
- DSA deployed source: `h24:/home/ubuntu/proj/dsa110-shell/dsa110-bbproc/toolkit.cu:734,762-768`
- DSA Level-3 workflow:
  `h24:/home/ubuntu/msherman_nsfrb/DSA110-DSAPOL-PROJECT/dsa110-pol/`
