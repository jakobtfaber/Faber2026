"""Reference-parity phase-coherence DM fits for paired CHIME/DSA bursts.

The stored products are already dedispersed.  Trial coordinates are therefore
physical residual DMs around the exact value encoded in each filename.  The
coherence statistic follows DM_phase: Fourier transform along time, discard
amplitude, sum unit phasors across channels, square the modulus, and weight by
fluctuation frequency squared.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import numpy as np

from dispersion.chime_dm import K_DM

_PRODUCT_DM = re.compile(r"_I_(\d+)_(\d+)_\d+b_cntr_bpc\.npy$")


@dataclass(frozen=True)
class PhaseSurface:
    dm_grid: np.ndarray
    fluctuation_hz: np.ndarray
    coherent_power: np.ndarray
    jackknife_power: np.ndarray
    valid_channels: int


@dataclass(frozen=True)
class CurveFit:
    dm: float
    sigma_jackknife: float
    cutoff_hz: float
    cutoff_peaks: dict[float, float]
    cutoff_contrast: dict[float, float]
    score: np.ndarray
    jackknife_peaks: np.ndarray


def product_dm_from_filename(filename: str) -> float:
    """Parse the exact pre-dedispersion DM encoded in a product filename."""
    match = _PRODUCT_DM.search(filename)
    if match is None:
        raise ValueError(f"cannot parse product DM from {filename!r}")
    return float(f"{match.group(1)}.{match.group(2)}")


def normalise_channels(waterfall: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Robustly standardise channels and return the retained-channel mask."""
    wf = np.asarray(waterfall, dtype=float)
    if wf.ndim != 2:
        raise ValueError("waterfall must have shape (frequency, time)")
    finite = np.isfinite(wf).mean(axis=1)
    median = np.nanmedian(wf, axis=1)
    mad = np.nanmedian(np.abs(wf - median[:, None]), axis=1)
    sigma = 1.4826 * mad
    valid = (finite >= 0.90) & np.isfinite(sigma) & (sigma > 0)
    if valid.sum() < 16:
        raise ValueError("fewer than 16 valid frequency channels")
    out = (wf[valid] - median[valid, None]) / sigma[valid, None]
    return np.nan_to_num(out), valid


def block_average(
    waterfall: np.ndarray,
    frequencies_mhz: np.ndarray,
    frequency_factor: int,
    time_factor: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Average complete frequency/time blocks without inventing samples."""
    wf = np.asarray(waterfall, dtype=float)
    freq = np.asarray(frequencies_mhz, dtype=float)
    ff, tf = int(frequency_factor), int(time_factor)
    nf = (wf.shape[0] // ff) * ff
    nt = (wf.shape[1] // tf) * tf
    if nf == 0 or nt == 0:
        raise ValueError("resolution factor exceeds input dimensions")
    blocks = wf[:nf, :nt].reshape(nf // ff, ff, nt // tf, tf)
    reduced = np.nanmean(blocks, axis=(1, 3))
    reduced_freq = np.nanmean(freq[:nf].reshape(nf // ff, ff), axis=1)
    return reduced, reduced_freq


def crop_on_pulse(
    waterfall: np.ndarray,
    sample_time_s: float,
    *,
    window_s: float = 0.030,
) -> tuple[np.ndarray, tuple[int, int], np.ndarray]:
    """Extract a fixed-width, burst-centred window with off-pulse margin."""
    z, valid = normalise_channels(waterfall)
    profile = np.mean(np.clip(z, 0.0, None), axis=0)
    smooth = max(1, int(round(1.0e-4 / sample_time_s)))
    if smooth > 1:
        profile = np.convolve(profile, np.ones(smooth) / smooth, mode="same")
    peak = int(np.argmax(profile))
    width = min(waterfall.shape[1], max(128, int(round(window_s / sample_time_s))))
    start = max(0, min(peak - width // 2, waterfall.shape[1] - width))
    stop = start + width
    return np.asarray(waterfall[valid, start:stop], dtype=float), (start, stop), valid


def phase_surface(
    waterfall: np.ndarray,
    frequencies_mhz: np.ndarray,
    sample_time_s: float,
    residual_dm_grid: np.ndarray,
    *,
    low_hz: float = 50.0,
    high_hz: float = 5000.0,
    jackknife_groups: int = 12,
    dm_chunk: int = 4,
) -> PhaseSurface:
    """Compute the DM_phase coherent-power surface and block jackknifes."""
    wf, valid = normalise_channels(waterfall)
    freq = np.asarray(frequencies_mhz, dtype=float)[valid]
    order = np.argsort(freq)
    wf, freq = wf[order], freq[order]
    grid = np.asarray(residual_dm_grid, dtype=float)
    if grid.ndim != 1 or grid.size < 5 or np.any(np.diff(grid) <= 0):
        raise ValueError("residual_dm_grid must be strictly increasing")
    delay_per_dm = K_DM * (freq**-2 - float(freq.max()) ** -2)
    maximum_delay = float(np.max(np.abs(delay_per_dm)) * np.max(np.abs(grid)))
    pad = int(np.ceil(maximum_delay / sample_time_s)) + 8
    padded = np.pad(wf, ((0, 0), (pad, pad)))
    spectrum = np.fft.rfft(padded, axis=1)
    amplitude = np.abs(spectrum)
    phase = np.divide(
        spectrum,
        amplitude,
        out=np.zeros_like(spectrum),
        where=amplitude > np.finfo(float).tiny,
    )
    fluctuation = np.fft.rfftfreq(padded.shape[1], sample_time_s)
    use = (fluctuation >= low_hz) & (fluctuation <= high_hz)
    phase = phase[:, use]
    fluctuation = fluctuation[use]
    if fluctuation.size < 5:
        raise ValueError("fluctuation-frequency window contains fewer than five bins")

    n_group = min(max(4, int(jackknife_groups)), wf.shape[0])
    group_id = np.arange(wf.shape[0]) % n_group
    power = np.empty((grid.size, fluctuation.size), dtype=float)
    jack = np.empty((n_group, grid.size, fluctuation.size), dtype=float)
    for start in range(0, grid.size, dm_chunk):
        trial = grid[start : start + dm_chunk]
        correction = np.exp(
            2j
            * np.pi
            * trial[:, None, None]
            * delay_per_dm[None, :, None]
            * fluctuation[None, None, :]
        )
        contributions = correction * phase[None, :, :]
        coherent = contributions.sum(axis=1)
        power[start : start + trial.size] = np.abs(coherent) ** 2
        for group in range(n_group):
            removed = contributions[:, group_id == group, :].sum(axis=1)
            jack[group, start : start + trial.size] = np.abs(coherent - removed) ** 2
    return PhaseSurface(grid, fluctuation, power, jack, int(wf.shape[0]))


def _parabolic_peak(grid: np.ndarray, score: np.ndarray) -> float:
    index = int(np.nanargmax(score))
    if index == 0 or index == grid.size - 1:
        return float(grid[index])
    x = grid[index - 1 : index + 2]
    y = score[index - 1 : index + 2]
    coefficient = np.polyfit(x - x[1], y, 2)
    if coefficient[0] >= 0 or np.any(~np.isfinite(coefficient)):
        return float(x[1])
    peak = float(x[1] - coefficient[1] / (2.0 * coefficient[0]))
    return float(np.clip(peak, x[0], x[-1]))


def fit_surface(
    surface: PhaseSurface,
    *,
    cutoff_candidates_hz: tuple[float, ...] = (500.0, 1000.0, 1500.0, 2500.0, 5000.0),
    stability_dm: float = 0.10,
) -> CurveFit:
    """Select a stable cutoff and estimate peak sampling error by jackknife."""
    frequency_weight = surface.fluctuation_hz**2
    candidates = sorted(
        {
            float(min(cutoff, surface.fluctuation_hz[-1]))
            for cutoff in cutoff_candidates_hz
            if cutoff >= surface.fluctuation_hz[4]
        }
    )
    if not candidates:
        candidates = [float(surface.fluctuation_hz[-1])]
    scores: dict[float, np.ndarray] = {}
    peaks: dict[float, float] = {}
    contrast: dict[float, float] = {}
    for cutoff in candidates:
        use = surface.fluctuation_hz <= cutoff
        score = np.sum(surface.coherent_power[:, use] * frequency_weight[use], axis=1)
        scores[cutoff] = score
        peaks[cutoff] = _parabolic_peak(surface.dm_grid, score)
        baseline = float(np.nanmedian(score))
        contrast[cutoff] = float(np.nanmax(score) / baseline) if baseline > 0 else float("inf")

    stable = []
    for index, cutoff in enumerate(candidates):
        neighbours = []
        if index:
            neighbours.append(candidates[index - 1])
        if index + 1 < len(candidates):
            neighbours.append(candidates[index + 1])
        if any(abs(peaks[cutoff] - peaks[other]) <= stability_dm for other in neighbours):
            stable.append(cutoff)
    pool = stable or candidates
    selected = max(pool, key=lambda cutoff: contrast[cutoff])
    use = surface.fluctuation_hz <= selected
    score = scores[selected]
    jackknife_peaks = np.asarray(
        [
            _parabolic_peak(
                surface.dm_grid,
                np.sum(row[:, use] * frequency_weight[use], axis=1),
            )
            for row in surface.jackknife_power
        ]
    )
    mean = float(np.mean(jackknife_peaks))
    n = jackknife_peaks.size
    sigma = float(np.sqrt((n - 1.0) / n * np.sum((jackknife_peaks - mean) ** 2)))
    return CurveFit(
        dm=_parabolic_peak(surface.dm_grid, score),
        sigma_jackknife=sigma,
        cutoff_hz=selected,
        cutoff_peaks=peaks,
        cutoff_contrast=contrast,
        score=score,
        jackknife_peaks=jackknife_peaks,
    )


def gaussian_joint_fit(
    chime_dm: float,
    chime_sigma: float,
    dsa_dm: float,
    dsa_sigma: float,
) -> dict[str, float]:
    """Combine independent band fits and report their consistency."""
    sigma_c = max(float(chime_sigma), 1.0e-6)
    sigma_d = max(float(dsa_sigma), 1.0e-6)
    values = np.asarray([chime_dm, dsa_dm])
    difference = float(chime_dm - dsa_dm)
    difference_sigma = float(np.hypot(sigma_c, sigma_d))
    tension = abs(difference) / difference_sigma

    def combine(tau: float) -> tuple[float, float, float]:
        weights = 1.0 / (np.asarray([sigma_c, sigma_d]) ** 2 + tau**2)
        mean = float(np.sum(weights * values) / np.sum(weights))
        sigma_mean = float(np.sqrt(1.0 / np.sum(weights)))
        q_value = float(np.sum(weights * (values - mean) ** 2))
        return mean, sigma_mean, q_value

    tau = 0.0
    dm, sigma, q_value = combine(tau)
    if q_value > 1.0:
        low, high = 0.0, max(abs(difference), difference_sigma)
        for _ in range(80):
            middle = 0.5 * (low + high)
            if combine(middle)[2] > 1.0:
                low = middle
            else:
                high = middle
        tau = high
        dm, sigma, q_value = combine(tau)
    return {
        "dm": dm,
        "sigma": sigma,
        "between_band_sigma": float(tau),
        "chime_minus_dsa": difference,
        "difference_sigma": difference_sigma,
        "tension_sigma": float(tension),
        "joint_q": q_value,
    }
