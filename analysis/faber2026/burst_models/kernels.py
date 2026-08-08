"""Physical timing and pulse kernels.

Times are seconds, frequencies are megahertz, and dispersion measures are
parsecs per cubic centimetre. Every density integrates to one over time.
"""

from __future__ import annotations

import math

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.special import erfcx, ndtr

REFERENCE_FREQUENCY_MHZ = 400.0
K_DM_S_MHZ2 = 4148.808


def dispersion_delay_s(
    delta_dm: ArrayLike,
    frequencies_mhz: ArrayLike,
) -> NDArray[np.floating]:
    """Cold-plasma delay relative to the fixed 400 megahertz coordinate."""

    frequencies = np.asarray(frequencies_mhz, dtype=float)
    if np.any(frequencies <= 0):
        raise ValueError("frequencies must be positive")
    return K_DM_S_MHZ2 * np.asarray(delta_dm, dtype=float) * (
        frequencies**-2 - REFERENCE_FREQUENCY_MHZ**-2
    )


def gaussian_density(
    time_s: ArrayLike,
    center_s: ArrayLike,
    sigma_s: ArrayLike,
) -> NDArray[np.floating]:
    """Area-normalized Gaussian, broadcast over supplied coordinates."""

    time = np.asarray(time_s, dtype=float)
    center = np.asarray(center_s, dtype=float)
    sigma = np.asarray(sigma_s, dtype=float)
    if np.any(sigma <= 0):
        raise ValueError("Gaussian width must be positive")
    return np.exp(-0.5 * ((time - center) / sigma) ** 2) / (
        math.sqrt(2.0 * math.pi) * sigma
    )


def exponentially_modified_gaussian(
    time_s: ArrayLike,
    center_s: ArrayLike,
    sigma_s: ArrayLike,
    tau_s: ArrayLike,
) -> NDArray[np.floating]:
    """Gaussian convolved with a causal exponential pulse-broadening function."""

    time = np.asarray(time_s, dtype=float)
    center = np.asarray(center_s, dtype=float)
    sigma = np.asarray(sigma_s, dtype=float)
    tau = np.asarray(tau_s, dtype=float)
    if np.any(sigma <= 0) or np.any(tau <= 0):
        raise ValueError("Gaussian and scattering widths must be positive")
    delta = time - center
    argument = sigma / (math.sqrt(2.0) * tau) - delta / (
        math.sqrt(2.0) * sigma
    )
    with np.errstate(over="ignore", under="ignore", invalid="ignore"):
        stable = (
            0.5
            / tau
            * np.exp(-0.5 * (delta / sigma) ** 2)
            * erfcx(argument)
        )
        asymptotic = np.exp(0.5 * (sigma / tau) ** 2 - delta / tau) / tau
    result = np.where(argument > -25.0, stable, asymptotic)
    return np.nan_to_num(result, nan=0.0, posinf=0.0, neginf=0.0)


def scattering_index(beta: float) -> float:
    """Frequency exponent implied by the thin-screen turbulence index."""

    if not 2.0 < beta <= 4.0:
        raise ValueError("beta must lie in (2, 4]")
    return 2.0 * beta / (beta - 2.0)


def power_law_pbf(
    time_s: ArrayLike,
    tau_s: float,
    beta: float,
) -> NDArray[np.floating] | float:
    """Normalized causal thin-screen pulse-broadening function.

    This is the manuscript model: exponential before the crossover and a
    continuous power-law tail afterward. The beta-equals-four endpoint is the
    pure exponential.
    """

    if tau_s <= 0:
        raise ValueError("scattering time must be positive")
    scattering_index(beta)
    time = np.asarray(time_s, dtype=float)
    value = np.zeros_like(time)
    causal = time >= 0
    scaled = time[causal] / tau_s
    if beta == 4.0:
        value[causal] = np.exp(-scaled) / tau_s
    else:
        crossover = 2.0 * math.log(2.0 / (4.0 - beta))
        core_mass = 1.0 - math.exp(-crossover)
        tail_mass = math.exp(-crossover) * crossover / (beta / 2.0 - 1.0)
        normalization = core_mass + tail_mass
        density = np.exp(-scaled)
        tail = scaled > crossover
        density[tail] = math.exp(-crossover) * (
            scaled[tail] / crossover
        ) ** (-beta / 2.0)
        value[causal] = density / (tau_s * normalization)
    if value.ndim == 0:
        return float(value)
    return value


def power_law_pbf_tail_mass_after(
    cutoff_s: float,
    tau_s: float,
    beta: float,
) -> float:
    """Exact omitted probability beyond a causal finite-support cutoff."""

    if cutoff_s < 0:
        return 1.0
    if tau_s <= 0:
        raise ValueError("scattering time must be positive")
    scattering_index(beta)
    scaled = cutoff_s / tau_s
    if beta == 4.0:
        return math.exp(-scaled)
    crossover = 2.0 * math.log(2.0 / (4.0 - beta))
    tail_total = math.exp(-crossover) * crossover / (beta / 2.0 - 1.0)
    normalization = 1.0 - math.exp(-crossover) + tail_total
    if scaled <= crossover:
        remaining = math.exp(-scaled) - math.exp(-crossover) + tail_total
    else:
        remaining = tail_total * (scaled / crossover) ** (1.0 - beta / 2.0)
    return remaining / normalization


def convolved_tail_upper_bound(
    cutoff_s: float,
    sigma_s: float,
    tau_s: float,
    beta: float,
) -> float:
    """Rigorous upper bound for a Gaussian convolved with a causal PBF.

    For every split ``a``, ``P(G + P > x)`` is at most
    ``P(G > a) + P(P > x-a)``. We return the smallest bound on a fixed dense
    split grid; every candidate is independently valid.
    """

    if cutoff_s <= 0:
        return 1.0
    if sigma_s <= 0 or tau_s <= 0:
        raise ValueError("pulse widths must be positive")
    splits = np.linspace(-8.0 * sigma_s, cutoff_s, 4097)
    gaussian_tail = ndtr(-splits / sigma_s)
    pbf_tail = np.asarray(
        [
            power_law_pbf_tail_mass_after(cutoff_s - split, tau_s, beta)
            for split in splits
        ]
    )
    return float(min(1.0, np.min(gaussian_tail + pbf_tail)))


def gaussian_power_law_density(
    time_s: ArrayLike,
    center_s: ArrayLike,
    sigma_s: ArrayLike,
    tau_s: ArrayLike,
    beta: float,
    *,
    quadrature_order: int = 128,
) -> NDArray[np.floating]:
    """Gaussian convolved with the beta-coupled causal power-law PBF."""

    if beta == 4.0:
        return exponentially_modified_gaussian(
            time_s,
            center_s,
            sigma_s,
            tau_s,
        )
    scattering_index(beta)
    time, center, sigma, tau = np.broadcast_arrays(
        np.asarray(time_s, dtype=float),
        np.asarray(center_s, dtype=float),
        np.asarray(sigma_s, dtype=float),
        np.asarray(tau_s, dtype=float),
    )
    if np.any(sigma <= 0) or np.any(tau <= 0):
        raise ValueError("Gaussian and scattering widths must be positive")
    delta = time - center
    crossover = 2.0 * math.log(2.0 / (4.0 - beta))
    core_mass_raw = 1.0 - math.exp(-crossover)
    tail_mass_raw = (
        math.exp(-crossover) * crossover / (beta / 2.0 - 1.0)
    )
    normalization = core_mass_raw + tail_mass_raw
    nodes, weights = np.polynomial.legendre.leggauss(quadrature_order)
    quantiles = 0.5 * (nodes + 1.0)
    probability_weights = 0.5 * weights

    # Integrate over each branch's probability coordinate. This remains stable
    # when the broadening time is much smaller than the intrinsic width; direct
    # time-domain quadrature misses that narrow causal kernel.
    core_lag_units = -np.log1p(-quantiles * core_mass_raw)
    core = np.sum(
        probability_weights
        * gaussian_density(
            delta[..., None] - tau[..., None] * core_lag_units,
            0.0,
            sigma[..., None],
        ),
        axis=-1,
    )
    tail_lag_units = crossover * (1.0 - quantiles) ** (
        -1.0 / (beta / 2.0 - 1.0)
    )
    tail = np.sum(
        probability_weights
        * gaussian_density(
            delta[..., None] - tau[..., None] * tail_lag_units,
            0.0,
            sigma[..., None],
        ),
        axis=-1,
    )
    return (
        core_mass_raw * core + tail_mass_raw * tail
    ) / normalization


__all__ = [
    "K_DM_S_MHZ2",
    "REFERENCE_FREQUENCY_MHZ",
    "convolved_tail_upper_bound",
    "dispersion_delay_s",
    "exponentially_modified_gaussian",
    "gaussian_density",
    "gaussian_power_law_density",
    "power_law_pbf",
    "power_law_pbf_tail_mass_after",
    "scattering_index",
]
