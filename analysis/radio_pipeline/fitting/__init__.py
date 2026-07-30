"""Reusable Faber2026 fitting modules."""

from . import VALIDATION_THRESHOLDS
from .diagnostics import ResidualDiagnostics, analyze_residuals
from .joint_burst import (
    AssociationHypothesis,
    BandObservation,
    ComponentMatch,
    ComponentWindow,
    DispersionState,
    FitSettings,
    GeometryConstraint,
    JointFitRequest,
    JointFitResult,
    fit_joint_event,
)
from .products import (
    load_band_observation_product,
    write_band_observation_product,
)
from .resolution import (
    FitResolution,
    materialize_fit_resolution,
    resolve_fit_resolution,
)

__all__ = [
    "AssociationHypothesis",
    "BandObservation",
    "ComponentMatch",
    "ComponentWindow",
    "DispersionState",
    "FitSettings",
    "FitResolution",
    "GeometryConstraint",
    "JointFitRequest",
    "JointFitResult",
    "ResidualDiagnostics",
    "VALIDATION_THRESHOLDS",
    "analyze_residuals",
    "fit_joint_event",
    "load_band_observation_product",
    "materialize_fit_resolution",
    "resolve_fit_resolution",
    "write_band_observation_product",
]
