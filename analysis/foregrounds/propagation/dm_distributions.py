"""Small probability-grid utilities for dispersion-measure inference.

The functions here contain no sightline data or scientific priors.  They make
normalization, marginalization, and tail checks explicit so producers can emit
complete probability grids rather than only selected quantiles.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import integrate


@dataclass(frozen=True)
class GridPosterior:
    """Normalized density on a strictly increasing one-dimensional grid."""

    grid: np.ndarray
    density: np.ndarray

    def __post_init__(self) -> None:
        grid = np.asarray(self.grid, dtype=float)
        density = np.asarray(self.density, dtype=float)
        if grid.ndim != 1 or density.shape != grid.shape or grid.size < 3:
            raise ValueError("grid and density must be matching one-dimensional arrays")
        if not np.all(np.isfinite(grid)) or not np.all(np.diff(grid) > 0.0):
            raise ValueError("grid must be finite and strictly increasing")
        if not np.all(np.isfinite(density)) or np.any(density < 0.0):
            raise ValueError("density must be finite and nonnegative")
        norm = float(np.trapezoid(density, grid))
        if not np.isfinite(norm) or norm <= 0.0:
            raise ValueError("density has no positive finite integral")
        grid = grid.copy()
        density = density / norm
        grid.setflags(write=False)
        density.setflags(write=False)
        object.__setattr__(self, "grid", grid)
        object.__setattr__(self, "density", density)

    def quantiles(self, probabilities: tuple[float, ...] = (0.16, 0.5, 0.84)) -> tuple[float, ...]:
        """Return linearly interpolated quantiles."""
        if any(not 0.0 <= probability <= 1.0 for probability in probabilities):
            raise ValueError("quantile probabilities must lie in [0, 1]")
        cdf = integrate.cumulative_trapezoid(self.density, self.grid, initial=0.0)
        cdf /= cdf[-1]
        return tuple(float(value) for value in np.interp(probabilities, cdf, self.grid))

    def probability_between(self, lower: float, upper: float) -> float:
        """Integrate probability over a closed grid interval."""
        if upper < lower:
            raise ValueError("upper bound must not be below lower bound")
        points = np.concatenate(
            (
                [lower],
                self.grid[(self.grid > lower) & (self.grid < upper)],
                [upper],
            )
        )
        values = np.interp(points, self.grid, self.density, left=0.0, right=0.0)
        return float(np.trapezoid(values, points))

    def edge_mass(self, fraction: float = 0.05) -> tuple[float, float]:
        """Probability in the lowest and highest ``fraction`` of the grid span."""
        if not 0.0 < fraction < 0.5:
            raise ValueError("edge fraction must lie in (0, 0.5)")
        span = self.grid[-1] - self.grid[0]
        return (
            self.probability_between(self.grid[0], self.grid[0] + fraction * span),
            self.probability_between(self.grid[-1] - fraction * span, self.grid[-1]),
        )

    def as_dict(self) -> dict:
        """Return a JSON-serializable complete grid."""
        q16, q50, q84 = self.quantiles()
        edge_low, edge_high = self.edge_mass()
        return {
            "grid": self.grid.tolist(),
            "density": self.density.tolist(),
            "normalization": float(np.trapezoid(self.density, self.grid)),
            "z16": q16,
            "z50": q50,
            "z84": q84,
            "edge_mass_low_5pct": edge_low,
            "edge_mass_high_5pct": edge_high,
        }


def normalize_joint(grid: np.ndarray, density: np.ndarray) -> np.ndarray:
    """Normalize ``density[state, grid]`` over state and the continuous grid."""
    grid = np.asarray(grid, dtype=float)
    density = np.asarray(density, dtype=float)
    if density.ndim != 2 or density.shape[1] != grid.size:
        raise ValueError("joint density must have shape (state, grid)")
    if np.any(~np.isfinite(density)) or np.any(density < 0.0):
        raise ValueError("joint density must be finite and nonnegative")
    norm = float(np.trapezoid(density.sum(axis=0), grid))
    if not np.isfinite(norm) or norm <= 0.0:
        raise ValueError("joint density has no positive finite integral")
    return density / norm


def marginal_from_joint(grid: np.ndarray, joint_density: np.ndarray) -> GridPosterior:
    """Marginalize a normalized or unnormalized state-by-grid density."""
    normalized = normalize_joint(grid, joint_density)
    return GridPosterior(grid=np.asarray(grid, dtype=float), density=normalized.sum(axis=0))


def state_probabilities(grid: np.ndarray, joint_density: np.ndarray) -> np.ndarray:
    """Integrate posterior probability for every discrete state."""
    normalized = normalize_joint(grid, joint_density)
    probabilities = np.trapezoid(normalized, np.asarray(grid, dtype=float), axis=1)
    return probabilities / probabilities.sum()


def coarsening_quantile_shift(posterior: GridPosterior) -> float:
    """Largest 16th/50th/84th-percentile shift after dropping alternate nodes."""
    coarse = GridPosterior(
        grid=posterior.grid[::2],
        density=posterior.density[::2],
    )
    return float(
        max(
            abs(fine - reduced)
            for fine, reduced in zip(posterior.quantiles(), coarse.quantiles(), strict=True)
        )
    )
