# Predicted-delay trigger calibration report

Source revision: `7a4b6a00ff7e6efdbddcac980816099f9b84b01b`; seed0 20260731.

The trigger remains **unavailable for model selection** until the
owner accepts an operating point from this table (ticket 04a).

## Conservative false-escalation envelopes (max over null cells)

| rate | statistic threshold |
|---|---|
| 0.005 | 4.699 |
| 0.01 | 4.649 |
| 0.05 | 3.935 |

## Detection rate per power cell at each envelope

| cell | 0.005 | 0.01 | 0.05 |
|---|---|---|---|
| power:snr-15:r-0.1 | 0.000 | 0.000 | 0.000 |
| power:snr-15:r-0.3 | 0.000 | 0.000 | 0.000 |
| power:snr-15:r-1 | 0.215 | 0.235 | 0.585 |
| power:snr-15:r-3 | 0.625 | 0.650 | 0.990 |
| power:snr-30:r-0.1 | 0.000 | 0.000 | 0.000 |
| power:snr-30:r-0.3 | 0.000 | 0.000 | 0.000 |
| power:snr-30:r-1 | 0.975 | 0.975 | 1.000 |
| power:snr-30:r-3 | 1.000 | 1.000 | 1.000 |
| power:snr-8:r-0.1 | 0.000 | 0.000 | 0.000 |
| power:snr-8:r-0.3 | 0.000 | 0.000 | 0.000 |
| power:snr-8:r-1 | 0.000 | 0.000 | 0.095 |
| power:snr-8:r-3 | 0.045 | 0.070 | 0.530 |

## Nested-sampling anchor (surrogate fidelity)

30 paired injections; mean |Delta p| = 0.0003; ML surrogate USABLE.
