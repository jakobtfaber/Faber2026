"""Coupled dispersion-measure--redshift inference.

Candidate redshifts are marginalized directly with their possible foreground
dispersion columns.  No point redshift is inserted and no iterative
foreground-selection loop is used.
"""

from __future__ import annotations

import itertools
import math
from collections.abc import Callable
from dataclasses import dataclass
from functools import cached_property

import numpy as np
from numpy.polynomial.legendre import leggauss
from scipy import stats

from foregrounds.propagation.dm_distributions import (
    GridPosterior,
    marginal_from_joint,
    normalize_joint,
    state_probabilities,
)

DMAtRedshift = Callable[[float], float | None]


@dataclass(frozen=True)
class CandidateForegroundDistribution:
    """Candidate halo-DM mixture conditional on lying before the source."""

    identifier: str
    redshift_nodes: tuple[float, ...]
    conditional_weights: tuple[float, ...]
    dm_medians: tuple[float | None, ...]
    dm_sigma_ln: float

    def __post_init__(self) -> None:
        size = len(self.redshift_nodes)
        if size == 0 or len(self.conditional_weights) != size or len(self.dm_medians) != size:
            raise ValueError("candidate quadrature arrays must be non-empty and equal length")
        if any(weight < 0.0 or not math.isfinite(weight) for weight in self.conditional_weights):
            raise ValueError("candidate quadrature weights must be finite and nonnegative")
        if not math.isclose(sum(self.conditional_weights), 1.0, abs_tol=1e-12):
            raise ValueError("candidate conditional weights must sum to one")
        if any(
            median is not None and (median < 0.0 or not math.isfinite(median))
            for median in self.dm_medians
        ):
            raise ValueError("candidate DM medians must be finite and nonnegative")


@dataclass(frozen=True)
class CandidateMixture:
    """One candidate's photo-z and redshift-dependent halo-DM model."""

    identifier: str
    z_mean: float
    z_sigma: float
    dm_sigma_ln: float
    dm_at_redshift: DMAtRedshift
    angular_separation_arcsec: float | None = None
    geometry_source: str | None = None
    catastrophic_failure_modeled: bool = False

    def __post_init__(self) -> None:
        if not self.identifier:
            raise ValueError("candidate identifier is required")
        if self.z_mean <= 0.0 or self.z_sigma <= 0.0:
            raise ValueError("candidate redshift mean and sigma must be positive")
        if self.dm_sigma_ln <= 0.0:
            raise ValueError("candidate DM logarithmic width must be positive")
        if not callable(self.dm_at_redshift):
            raise ValueError("candidate redshift-dependent DM model is required")
        if self.angular_separation_arcsec is not None and self.angular_separation_arcsec <= 0.0:
            raise ValueError("candidate angular separation must be positive")
        if self.catastrophic_failure_modeled:
            raise ValueError("catastrophic photo-z failures require a separately approved model")

    def foreground_probability(self, source_z: np.ndarray) -> np.ndarray:
        """P(z_candidate < z_source) for a Gaussian truncated at z>0."""
        source_z = np.asarray(source_z, dtype=float)
        lower_cdf = stats.norm.cdf(0.0, loc=self.z_mean, scale=self.z_sigma)
        cdf = stats.norm.cdf(source_z, loc=self.z_mean, scale=self.z_sigma)
        return np.clip((cdf - lower_cdf) / (1.0 - lower_cdf), 0.0, 1.0)

    @cached_property
    def dm_at_photo_z_mean(self) -> float | None:
        value = self.dm_at_redshift(self.z_mean)
        return None if value is None else float(value)

    def foreground_distribution(
        self,
        source_z: float,
        *,
        quadrature_order: int,
    ) -> CandidateForegroundDistribution:
        """Integrate halo DM over photo-z conditional on candidate z < source z."""
        if source_z <= 0.0:
            raise ValueError("source redshift must be positive")
        if quadrature_order < 4:
            raise ValueError("candidate quadrature order must be at least four")
        base_nodes, base_weights = leggauss(quadrature_order)
        lower_cdf = stats.norm.cdf(0.0, loc=self.z_mean, scale=self.z_sigma)
        upper_cdf = stats.norm.cdf(source_z, loc=self.z_mean, scale=self.z_sigma)
        if upper_cdf <= lower_cdf:
            raise ValueError(f"{self.identifier}: photo-z quadrature has no foreground mass")
        probability_nodes = 0.5 * (upper_cdf - lower_cdf) * base_nodes + 0.5 * (
            upper_cdf + lower_cdf
        )
        nodes = stats.norm.ppf(
            probability_nodes,
            loc=self.z_mean,
            scale=self.z_sigma,
        )
        conditional_weights = 0.5 * base_weights
        medians = []
        for node in nodes:
            value = self.dm_at_redshift(float(node))
            medians.append(None if value is None else float(value))
        return CandidateForegroundDistribution(
            identifier=self.identifier,
            redshift_nodes=tuple(float(value) for value in nodes),
            conditional_weights=tuple(float(value) for value in conditional_weights),
            dm_medians=tuple(medians),
            dm_sigma_ln=self.dm_sigma_ln,
        )

    def as_dict(self) -> dict:
        return {
            "identifier": self.identifier,
            "z_mean": self.z_mean,
            "z_sigma": self.z_sigma,
            "dm_at_photo_z_mean": self.dm_at_photo_z_mean,
            "dm_sigma_ln": self.dm_sigma_ln,
            "dm_redshift_marginalization": "conditional photo-z quadrature",
            "angular_separation_arcsec": self.angular_separation_arcsec,
            "geometry_source": self.geometry_source,
            "photo_z_catastrophic_failures": "unmodeled",
        }


@dataclass(frozen=True)
class CoupledResult:
    """Full continuous-redshift and discrete-candidate-state posterior."""

    posterior: GridPosterior
    state_labels: tuple[str, ...]
    joint_density: np.ndarray
    state_probability: np.ndarray
    candidate_foreground_probability: dict[str, float]

    def as_dict(self) -> dict:
        return {
            **self.posterior.as_dict(),
            "state_labels": list(self.state_labels),
            "joint_density": self.joint_density.tolist(),
            "state_probability": self.state_probability.tolist(),
            "candidate_foreground_probability": self.candidate_foreground_probability,
        }


Likelihood = Callable[[float, tuple[CandidateForegroundDistribution, ...]], float]
Prior = Callable[[float], float]


def infer_coupled(
    z_grid: np.ndarray,
    *,
    candidates: tuple[CandidateMixture, ...],
    likelihood: Likelihood,
    redshift_prior: Prior,
    candidate_quadrature_order: int = 12,
) -> CoupledResult:
    """Evaluate the exact finite candidate-state mixture on ``z_grid``.

    At each source redshift, each candidate's state probability is obtained by
    integrating its redshift distribution below or above the source.  The
    dispersion likelihood is then evaluated for that state.  Summing the
    normalized joint grid marginalizes candidate identity and foreground status
    without replacing either redshift distribution by a point.
    """
    grid = np.asarray(z_grid, dtype=float)
    if grid.ndim != 1 or grid.size < 3 or np.any(np.diff(grid) <= 0.0):
        raise ValueError("z_grid must be a strictly increasing one-dimensional grid")
    if len(candidates) > 12:
        raise ValueError("candidate-state enumeration is limited to 12 candidates")
    identifiers = [candidate.identifier for candidate in candidates]
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("candidate identifiers must be unique")

    states = tuple(itertools.product((False, True), repeat=len(candidates)))
    state_labels = tuple(
        "none"
        if not candidates
        else ",".join(
            f"{candidate.identifier}={'foreground' if active else 'background'}"
            for candidate, active in zip(candidates, state, strict=True)
        )
        for state in states
    )
    q = np.array([candidate.foreground_probability(grid) for candidate in candidates])
    joint = np.zeros((len(states), grid.size), dtype=float)
    for state_index, state in enumerate(states):
        for z_index, z in enumerate(grid):
            weight = 1.0
            for candidate_index, is_foreground in enumerate(state):
                probability = q[candidate_index, z_index]
                weight *= probability if is_foreground else 1.0 - probability
            if weight:
                active = tuple(
                    candidate.foreground_distribution(
                        float(z),
                        quadrature_order=candidate_quadrature_order,
                    )
                    for candidate, is_foreground in zip(candidates, state, strict=True)
                    if is_foreground
                )
                joint[state_index, z_index] = (
                    weight * redshift_prior(float(z)) * likelihood(float(z), active)
                )

    joint = normalize_joint(grid, joint)
    posterior = marginal_from_joint(grid, joint)
    state_probability = state_probabilities(grid, joint)
    candidate_probability = {
        candidate.identifier: float(
            sum(
                probability
                for state, probability in zip(states, state_probability, strict=True)
                if state[index]
            )
        )
        for index, candidate in enumerate(candidates)
    }
    return CoupledResult(
        posterior=posterior,
        state_labels=state_labels,
        joint_density=joint,
        state_probability=state_probability,
        candidate_foreground_probability=candidate_probability,
    )


def assert_tail_control(result: CoupledResult, maximum_edge_mass: float = 0.02) -> None:
    """Fail if either outer five-percent grid region carries too much mass."""
    low, high = result.posterior.edge_mass()
    if not math.isfinite(low + high) or max(low, high) > maximum_edge_mass:
        raise ValueError(
            f"redshift grid has uncontrolled edge mass: low={low:.4g}, high={high:.4g}"
        )
