from foregrounds.propagation.sightline_budget import _is_placeholder_z


def test_missing_and_legacy_placeholder_redshifts_fail_closed():
    assert _is_placeholder_z(None)
    assert _is_placeholder_z(float("nan"))
    assert _is_placeholder_z(1.0)
    assert not _is_placeholder_z(0.271)
