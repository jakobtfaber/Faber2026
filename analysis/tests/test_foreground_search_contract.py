from __future__ import annotations

import pytest

from scripts.foreground_search_contract import (
    RecoveredRedshiftEvidence,
    classify_recovered_cluster_redshift,
)


SHA = "a" * 64


def evidence(
    redshift: float,
    kind: str,
    interval_95: tuple[float, float] | None = None,
    *,
    sigma: float | None = None,
    source_id: str = "catalog/release/source-row",
) -> RecoveredRedshiftEvidence:
    return RecoveredRedshiftEvidence(source_id, SHA, redshift, kind, interval_95, sigma)


@pytest.mark.parametrize(
    "item,z_host,expected",
    [
        (evidence(0.10, "spectroscopic"), 0.20, "foreground"),
        (evidence(0.2001, "spectroscopic"), 0.20, "host_local_ambiguous"),
        (evidence(0.30, "spectroscopic"), 0.20, "background"),
        (
            evidence(0.10, "photometric", (0.08, 0.12)),
            0.20,
            "potentially_foreground",
        ),
        (
            evidence(0.25, "photometric", (0.15, 0.30)),
            0.20,
            "redshift_ambiguous",
        ),
        (
            evidence(0.25, "photometric", sigma=0.04),
            0.20,
            "redshift_ambiguous",
        ),
        (evidence(0.10, "unknown"), 0.20, "no_usable_redshift"),
    ],
)
def test_recovered_cluster_uses_frozen_evidence_for_classification(
    item, z_host, expected
):
    result = classify_recovered_cluster_redshift([item], z_host)
    assert result.geometry_state == "resolved"
    assert result.redshift_state == expected
    assert result.search_geometry_redshift_source == f"{item.source_id}@sha256:{SHA}"


def test_conflicting_recovered_redshifts_remain_geometry_unresolved():
    result = classify_recovered_cluster_redshift(
        [
            evidence(0.10, "spectroscopic", source_id="catalog/a"),
            evidence(0.11, "spectroscopic", source_id="catalog/b"),
        ],
        z_host=0.20,
    )
    assert result.geometry_state == "cluster_search_geometry_unresolved"
    assert result.redshift_state is None
    assert result.search_geometry_redshift_source is None
