from pathlib import Path

import pytest

from foregrounds.visualization.systems_figures import (
    cluster_params,
    load_cluster_targets,
)


DATA = Path(__file__).parents[1] / "census" / "data"


def test_cluster_figure_uses_canonical_mass_and_geometry() -> None:
    targets = load_cluster_targets(str(DATA))
    first = targets[0]

    assert first[0] == "J115120.4+714435"
    assert first[1:] == pytest.approx((603.6, 0.83, 0.2, 1.48e14, 729.0))
    result = cluster_params(*first[1:])
    assert result["m500_msun"] == pytest.approx(1.48e14)
    assert result["r500_kpc"] == pytest.approx(729.0)
    assert result["dm_at_b"] == pytest.approx(224.719617368599, rel=1e-9)
