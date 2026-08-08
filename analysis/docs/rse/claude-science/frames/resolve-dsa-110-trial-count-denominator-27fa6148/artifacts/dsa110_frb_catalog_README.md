# DSA-110 FRB catalog

Cleaned from the DSA-110 internal master spreadsheet (`DSA110-FRBs(frb_params).csv`). One row per FRB detection, keyed on `candname`.

- **92** detections; **56** with host redshifts.
- **10** carry a CHIME/FRB event number (co-detections).
- Sorted chronologically by MJD; **8** recent candidate stubs (no measurements yet) sort to the end.

## Cleaning applied
- Fixed non-UTF-8 bytes (NBSP -> space); output is valid UTF-8.
- Dropped 34 trailing empty columns, blank padding rows, and the `[median]` summary row.
- Unified the split identifier (early rows used `NAME`, later rows `TNS name`) into `frb_name`.
- Coerced numeric columns by parsing the leading number and discarding any trailing
  non-numeric text, so a stray annotation on a numeric field becomes a clean float.
  (Note: `signal_bin` is deliberately exempt and kept verbatim as a string — markers
  like `953**` and ranges like `3818-3820` are preserved there; see Caveats.)
- Split `Position error (1sigma)` "ra, dec" into `pos_err_ra_arcsec` / `pos_err_dec_arcsec`.
- Normalized `johndoe (II)` -> `johndoeII`.

## Caveats
- Two entries share the `johndoe` nickname (candname `230814aaas` = johndoeII, and a candname-less `johndoe` at z=0.5535); retained both as they carry independent measurements. Verify whether these are the same source before science use.
- `signal_bin` is kept as string because some rows record ranges (`3818-3820`) or multiples.
- `pari` (FRB20240304C, candname `240304aaax`) had a source-spreadsheet MJD typo (`554553`, → year 3377); corrected to MJD 60373 (2024-03-04) per its candname date. Flagged in that row's `comment`.

## Detection count (referee B3 trial set)
DSA-110 detected **64 FRBs between 2022 February and 2024 February** (candnames `220204aaai` through `240229aaad`), of which 48 are localized and 10 carry a CHIME/FRB event number. This is the look-elsewhere denominator for the P_cc trials factor in the manuscript (`sections/toa.tex`): summed over these 64 bursts at per-event μ_j ~ 5×10⁻⁹, Σμ_j ≈ 3×10⁻⁷. The window count is stable under two independent methods (MJD field vs. YYMMDD candname date).

## Columns

| column | description |
|---|---|
| `frb_name` | TNS FRB designation (canonical, no space), e.g. FRB20220207C; blank if not yet assigned |
| `nickname` | DSA-110 internal source nickname |
| `candname` | Pipeline candidate name (YYMMDD + suffix); unique detection key |
| `tns_name` | TNS name as reported (with space) |
| `mjd` | Barycentric MJD of the burst |
| `snr_heimdall` | Detection S/N from Heimdall |
| `dm_heimdall` | Dispersion measure from Heimdall (pc cm^-3) |
| `dm_opt` | Optimized/structure-maximizing DM (pc cm^-3) |
| `dm_exgal` | Extragalactic DM = DM_obs - DM_MW,ISM (pc cm^-3) |
| `dm_mw_ne2001_30kpc` | Galactic DM to 30 kpc from NE2001 (pc cm^-3) |
| `redshift` | Host spectroscopic/photometric redshift; blank if unlocalized |
| `ra_beam_deg` | Detection-beam RA (deg) |
| `dec_beam_deg` | Detection-beam Dec (deg) |
| `detection_beam` | Detection beam index (ibeam) |
| `ibox` | Boxcar width index at detection |
| `opt_integration_bins` | Optimal integration width (bins of 32.768 us) |
| `signal_bin` | Signal bin index or range (kept as string; some rows list ranges/notes) |
| `fluence_jyms` | Burst fluence (Jy ms) |
| `pb_attenuation` | Primary-beam attenuation factor (3.5 deg beam) |
| `chime_event_no` | CHIME/FRB event number for co-detections; blank otherwise |
| `voltage_localization` | Voltage-based localization (sexagesimal RA Dec) |
| `pos_err_ra_arcsec` | 1-sigma RA position error (arcsec) |
| `pos_err_dec_arcsec` | 1-sigma Dec position error (arcsec) |
| `calib_voltages` | Calibration voltage notes (free text) |
| `astrometry_notes` | Astrometry notes (free text) |
| `comment` | Miscellaneous comment (free text) |
| `swift` | Swift/BAT co-trigger note if any (free text) |
