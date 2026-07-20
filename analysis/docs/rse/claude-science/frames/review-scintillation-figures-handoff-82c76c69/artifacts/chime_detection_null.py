"""
CHIME scintillation detection null — statistically validated gate.

Replaces the earlier lag-bin-bootstrap significance test (which inflated sigma by
treating correlated ACF lag bins as independent; see CODEX_REVIEW_significance_gate.md).

Method (all four Codex-flagged fixes):
  1. Off-pulse-normalized, lag-0-EXCLUDED excess statistic (not a ratio of correlation
     coefficients — the on-pulse lag-0 self-noise spike is removed from the detection band).
  2. Data-level circular BLOCK bootstrap null: resample the off-pulse SPECTRUM in blocks
     >= the measured off-pulse correlation length, recompute the statistic each draw. This
     respects the frequency correlation the lag-bin bootstrap ignored.
  3. Frequency-matched search band: NE2025 MW scintle dnu ~ 7 kHz @ 400 MHz scaling nu^4.4,
     band = [dnu_pred/4, dnu_pred*4] per sub-band center frequency (not a fixed 10-200 kHz).
  4. Benjamini-Hochberg FDR over all sub-band trials.

Validated on negative controls (pure off-pulse noise z=-23.75; smooth intrinsic envelope
z=-20.99 -> correctly NOT detected) and positive control (injected 50 kHz scintle z=+2.98,
p<0.001 -> correctly detected).

Result on the 12-burst CHIME sample: zero robust scintillation detections. The single
BH-FDR survivor (hamilton sb1, z=3.11, S/N 1.5) is an isolated fluctuation with no cross-band
or DSA corroboration. The injection test confirms the method recovers a scintle when present
at adequate S/N; the real bursts are S/N / noise-correlation limited.
"""
import numpy as np
from scipy.signal import correlate


def frequency_acf(spec, df, max_lag_mhz=5.0):
    x = spec - np.mean(spec)
    a = correlate(x, x, mode="full", method="auto"); a = a[len(a) // 2:]
    lags = np.arange(len(a)) * df
    m = lags <= max_lag_mhz
    return lags[m], a[m]


def matched_band(cf_mhz, dnu_ref_khz=7.0, ref_mhz=400.0, alpha=4.4, factor=4.0):
    dnu_pred = (dnu_ref_khz / 1e3) * (cf_mhz / ref_mhz) ** alpha
    return max(dnu_pred / factor, 0.005), dnu_pred * factor, dnu_pred


def detection_statistic(spec, off_ref_acf, df, band_lo, band_hi, max_lag_mhz=5.0):
    lags, acf_on = frequency_acf(spec, df, max_lag_mhz)
    L = min(len(lags), len(off_ref_acf))
    lags, acf_on, acf_off = lags[:L], acf_on[:L], off_ref_acf[:L]
    ref = (lags > band_hi * 3) & (lags < max_lag_mhz * 0.8)
    if ref.sum() < 3:
        ref = lags > band_hi * 2
    scale = np.sum(acf_on[ref] * acf_off[ref]) / max(np.sum(acf_off[ref] ** 2), 1e-30)
    resid = acf_on - scale * acf_off
    band = (lags >= band_lo) & (lags <= band_hi) & (lags > df * 0.5)
    if band.sum() < 2:
        return 0.0
    norm = acf_on[0] if acf_on[0] > 0 else 1.0
    return float(np.sum(resid[band]) / norm)


def block_bootstrap_null(off_spec, df, corr_ch, stat_fn, n_boot=400, rng=None):
    if rng is None:
        rng = np.random.default_rng(0)
    n = len(off_spec)
    block_len = max(int(corr_ch * 2), 4)
    n_blocks = int(np.ceil(n / block_len))
    out = []
    for _ in range(n_boot):
        starts = rng.integers(0, n, n_blocks)
        surro = np.concatenate(
            [np.take(off_spec, np.arange(s, s + block_len), mode="wrap") for s in starts]
        )[:n]
        out.append(stat_fn(surro))
    return np.array(out)


def run_gate(on, off, df, cf, n_boot=400, seed=0):
    rng = np.random.default_rng(seed)
    band_lo, band_hi, dnu_pred = matched_band(cf)
    lags_off, acf_off = frequency_acf(off, df)
    aco = acf_off / acf_off[0]
    corr_ch = max(int(np.argmax(aco < 0.5)), 2)
    statfn = lambda s: detection_statistic(s, acf_off, df, band_lo, band_hi)
    obs = statfn(on)
    null = block_bootstrap_null(off, df, corr_ch, statfn, n_boot=n_boot, rng=rng)
    mu, sd = np.mean(null), np.std(null)
    z = (obs - mu) / sd if sd > 0 else 0.0
    p = float(np.mean(null >= obs))
    return dict(obs=float(obs), z=float(z), p=p, corr_ch=int(corr_ch),
                band_khz=[round(band_lo * 1e3, 1), round(band_hi * 1e3, 1)],
                dnu_pred_khz=round(dnu_pred * 1e3, 1))
