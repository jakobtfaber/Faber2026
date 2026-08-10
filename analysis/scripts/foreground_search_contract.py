#!/usr/bin/env python3
"""Executable reference rules for recovered cluster-redshift classification."""

from __future__ import annotations

from dataclasses import dataclass
import math
import re
from typing import Sequence


SPEED_OF_LIGHT_KM_S = 299_792.458
SHA256_RE = re.compile(r"[0-9a-f]{64}")


@dataclass(frozen=True)
class RecoveredRedshiftEvidence:
    source_id: str
    row_sha256: str
    redshift: float
    kind: str
    interval_95: tuple[float, float] | None = None
    sigma: float | None = None
    secure_spectrum: bool | None = None


@dataclass(frozen=True)
class RecoveredClusterClassification:
    geometry_state: str
    redshift_state: str | None
    search_geometry_redshift_source: str | None


def _unresolved() -> RecoveredClusterClassification:
    return RecoveredClusterClassification(
        "cluster_search_geometry_unresolved", None, None
    )


def classify_recovered_cluster_redshift(
    evidence: Sequence[RecoveredRedshiftEvidence],
    z_host: float,
) -> RecoveredClusterClassification:
    """Classify one cluster recovered by separately sourced redshift evidence.

    Multiple records, conflicting values, or incomplete provenance fail closed
    before classification. The contract admits one adopted frozen record; it
    never uses source order to choose among candidates.
    """

    if not math.isfinite(z_host) or z_host <= 0:
        raise ValueError("z_host must be finite and positive")
    if len(evidence) != 1:
        return _unresolved()
    if any(
        not item.source_id.strip()
        or SHA256_RE.fullmatch(item.row_sha256) is None
        or not math.isfinite(item.redshift)
        or item.redshift <= 0
        for item in evidence
    ):
        return _unresolved()
    item = evidence[0]
    source = f"{item.source_id}@sha256:{item.row_sha256}"
    kind = item.kind.lower()
    if kind == "spectroscopic":
        if item.secure_spectrum is not True:
            state = "no_usable_redshift"
        else:
            velocity_offset = (
                SPEED_OF_LIGHT_KM_S * abs(item.redshift - z_host) / (1.0 + z_host)
            )
            if velocity_offset <= 500.0:
                state = "host_local_ambiguous"
            elif item.redshift < z_host:
                state = "foreground"
            else:
                state = "background"
    elif kind == "photometric":
        interval = item.interval_95
        if interval is None and item.sigma is not None:
            if math.isfinite(item.sigma) and item.sigma > 0:
                interval = (
                    item.redshift - 1.96 * item.sigma,
                    item.redshift + 1.96 * item.sigma,
                )
        if interval is None or not all(math.isfinite(value) for value in interval):
            state = "no_usable_redshift"
        else:
            lower, upper = interval
            if lower > upper:
                state = "no_usable_redshift"
            elif upper > 0 and lower < z_host:
                state = (
                    "potentially_foreground"
                    if 0 < item.redshift < z_host
                    else "redshift_ambiguous"
                )
            elif item.redshift >= z_host:
                state = "background"
            else:
                state = "no_usable_redshift"
    else:
        state = "no_usable_redshift"
    return RecoveredClusterClassification("resolved", state, source)
