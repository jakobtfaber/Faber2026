"""Geometry-constrained dual-band burst inference."""

from .joint import (
    AssociationHypothesis,
    ComponentMatch,
    GeometryConstraint,
    JointFitRequest,
    JointFitResult,
    PosteriorSummary,
    evaluate_log_likelihood,
    fit_joint_event,
)

__all__ = [
    "AssociationHypothesis",
    "ComponentMatch",
    "GeometryConstraint",
    "JointFitRequest",
    "JointFitResult",
    "PosteriorSummary",
    "evaluate_log_likelihood",
    "fit_joint_event",
]
