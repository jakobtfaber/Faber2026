"""Geometry-constrained dual-band burst inference."""

from .joint import (
    AssociationHypothesis,
    ComponentMatch,
    GeometryConstraint,
    JointFitRequest,
    JointFitResult,
    PosteriorSummary,
    combine_joint_fit_results,
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
    "combine_joint_fit_results",
    "evaluate_log_likelihood",
    "fit_joint_event",
]
