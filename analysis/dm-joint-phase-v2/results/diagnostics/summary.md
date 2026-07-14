# Joint CHIME/DSA DM-phase diagnostic results

These combinations are retained as sensitivity tests. The manuscript-adopted
DMs are the CHIME/FRB measurements in
`../../manuscript_dm_catalog.csv`; see
`docs/rse/specs/verified-dm-adoption-2026-07-13.md` for the decision record.

Each band was fitted independently at the finest native or near-native resolution that was stable across the resolution grid. The quoted band uncertainty is the maximum of the channel-block jackknife, resolution dependence, fluctuation-frequency-cutoff dependence, and a 0.005 pc cm^-3 numerical floor. The joint estimate is inverse-variance weighted when the bands are consistent and uses a fitted random-effects term when their difference exceeds the stated band errors.

| Event | CHIME DM | DSA DM | Joint DM | CHIME-DSA | Status |
|---|---:|---:|---:|---:|---|
| casey | 491.2078 +/- 0.0052 | 491.1975 +/- 0.0396 | 491.2077 +/- 0.0051 | +0.0103 | PASS |
| chromatica | 272.6387 +/- 0.0119 | 272.5614 +/- 0.0862 | 272.6372 +/- 0.0118 | +0.0773 | PASS |
| freya | 912.4076 +/- 0.0157 | 912.4911 +/- 0.0223 | 912.4478 +/- 0.0417 | -0.0835 | PASS_SYSTEMATIC |
| hamilton | 518.7970 +/- 0.0050 | 518.7977 +/- 0.0630 | 518.7970 +/- 0.0050 | -0.0007 | PASS |
| isha | 411.4357 +/- 0.0050 | 411.5527 +/- 0.0724 | 411.4719 +/- 0.0541 | -0.1170 | PASS_SYSTEMATIC |
| johndoeII | 696.5180 +/- 0.0050 | 696.4655 +/- 0.0685 | 696.5177 +/- 0.0050 | +0.0525 | PASS |
| mahi | 960.1316 +/- 0.0050 | 960.0858 +/- 0.0697 | 960.1314 +/- 0.0050 | +0.0458 | PASS |
| oran | 397.0155 +/- 0.0050 | 396.9410 +/- 0.0825 | 397.0153 +/- 0.0050 | +0.0745 | PASS |
| phineas | 610.2891 +/- 0.0050 | 610.2325 +/- 0.0071 | 610.2610 +/- 0.0283 | +0.0565 | PASS_SYSTEMATIC |
| whitney | 462.1888 +/- 0.0050 | 462.1928 +/- 0.0293 | 462.1889 +/- 0.0049 | -0.0040 | PASS |
| wilhelm | 602.3778 +/- 0.0060 | 602.3792 +/- 0.0128 | 602.3781 +/- 0.0055 | -0.0014 | PASS |
| zach | 262.3617 +/- 0.0104 | 262.3164 +/- 0.0293 | 262.3473 +/- 0.0211 | +0.0453 | PASS_SYSTEMATIC |

`PASS_SYSTEMATIC` means both band maxima passed the fit-quality gates, while the shared uncertainty was widened by the measured between-band scatter. It is not a failed or unconstrained fit.

See `all_events_contact_sheet.jpg`, the event-level PNGs, `../fits.json`, and `../validation/injection_recovery.json` for the full evidence.
