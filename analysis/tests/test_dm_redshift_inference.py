import math

import dm_redshift_inference as dri


def test_hostless_roster_has_no_established_redshifts():
    rows = dri.load_hostless()
    assert {row.name for row in rows} == dri.HOSTLESS


def test_redshift_prior_is_positive_and_finite():
    for z in (0.01, 0.1, 0.5, 1.0, 2.5):
        assert math.isfinite(dri.redshift_prior(z))
        assert dri.redshift_prior(z) > 0.0


def test_dm_redshift_order_tracks_excess_dm():
    results = {
        row.name: dri.infer_one(row, 100.0)
        for row in dri.load_hostless()
    }
    assert results["FRB 20240122A"]["z50"] > results["FRB 20221203A"]["z50"]
    assert results["FRB 20230325C"]["z50"] > results["FRB 20221203A"]["z50"]
    for result in results.values():
        assert 0.0 < result["z16"] < result["z50"] < result["z84"] < 2.5
