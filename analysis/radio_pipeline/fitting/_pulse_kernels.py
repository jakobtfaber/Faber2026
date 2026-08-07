"""Private, unit-consistent pulse kernels for joint burst fitting.

All time-like inputs use seconds. Frequencies are handled by the caller so this
module contains no dispersion or observatory conventions.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from scipy.special import erfcx


def gaussian_density(
    time_s: NDArray[np.floating],
    center_s: NDArray[np.floating],
    sigma_s: NDArray[np.floating],
) -> NDArray[np.floating]:
    """Area-normalized Gaussian for one center and width per frequency row."""

    time = np.asarray(time_s, dtype=float)[None, :]
    center = np.asarray(center_s, dtype=float)[:, None]
    sigma = np.asarray(sigma_s, dtype=float)[:, None]
    return gaussian_density_points(time - center, sigma)


def gaussian_density_points(
    delta_s: NDArray[np.floating],
    sigma_s: NDArray[np.floating],
) -> NDArray[np.floating]:
    """Area-normalized Gaussian at paired offsets and widths."""

    delta = np.asarray(delta_s, dtype=float)
    sigma = np.clip(np.asarray(sigma_s, dtype=float), 1.0e-12, None)
    return np.exp(-0.5 * (delta / sigma) ** 2) / (np.sqrt(2.0 * np.pi) * sigma)


def gaussian_exponential_density(
    time_s: NDArray[np.floating],
    center_s: NDArray[np.floating],
    sigma_s: NDArray[np.floating],
    tau_s: NDArray[np.floating],
) -> NDArray[np.floating]:
    """Area-normalized Gaussian convolved with a one-sided exponential.

    The erfcx form stays finite when the Gaussian and scattering scales differ
    strongly. Beyond erfcx argument -8, the pure exponential tail omits less
    than half of erfc(8), or 5.7e-30 relative. Rows with negligible scattering
    use the Gaussian limit directly.
    """

    time = np.asarray(time_s, dtype=float)[None, :]
    center = np.asarray(center_s, dtype=float)[:, None]
    sigma = np.asarray(sigma_s, dtype=float)[:, None]
    tau = np.asarray(tau_s, dtype=float)[:, None]
    return gaussian_exponential_density_points(time - center, sigma, tau)


def gaussian_exponential_density_points(
    delta_s: NDArray[np.floating],
    sigma_s: NDArray[np.floating],
    tau_s: NDArray[np.floating],
) -> NDArray[np.floating]:
    """Gaussian-exponential density at paired offsets, widths, and tails."""

    delta = np.asarray(delta_s, dtype=float)
    sigma = np.clip(np.asarray(sigma_s, dtype=float), 1.0e-12, None)
    tau = np.clip(np.asarray(tau_s, dtype=float), 1.0e-15, None)
    gaussian_limit = (tau < 1.0e-12) | (sigma > 100.0 * tau)
    argument = sigma / (np.sqrt(2.0) * tau) - delta / (
        np.sqrt(2.0) * sigma
    )
    core = argument > -8.0
    with np.errstate(over="ignore", under="ignore", invalid="ignore"):
        asymptotic = 0.5 * (sigma / tau) ** 2 - delta / tau
        result = np.exp(asymptotic) / tau
        result[core] = (
            0.5
            / np.broadcast_to(tau, delta.shape)[core]
            * np.exp(-0.5 * (delta / sigma) ** 2)[core]
            * erfcx(argument[core])
        )
    if np.any(gaussian_limit):
        gaussian = gaussian_density_points(delta, sigma)
        limit = np.broadcast_to(gaussian_limit, result.shape)
        result[limit] = gaussian[limit]
    if not np.all(np.isfinite(result)):
        np.nan_to_num(result, copy=False, nan=0.0, posinf=0.0, neginf=0.0)
    return result
