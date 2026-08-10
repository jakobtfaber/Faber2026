"""Exact installed-manuscript checks for Figure 3."""

from __future__ import annotations

from scripts import validate_foreground_census_analysis_only as validation


def test_unapproved_candidate_does_not_replace_installed_figure() -> None:
    assert validation.MANUSCRIPT_FIGURE.is_file()
    assert validation.STAGED_FIGURE.is_file()
    assert validation.sha256_file(
        validation.MANUSCRIPT_FIGURE
    ) != validation.sha256_file(validation.STAGED_FIGURE)


def test_staged_candidate_matches_the_committed_census() -> None:
    result = validation.check_census_matches_figure3(
        validation.Inputs.load(),
        figure=validation.STAGED_FIGURE,
        render=True,
    )
    assert result.passed, result.failures
    assert result.facts["candidate_matches_staged_render_byte_for_byte"] is True
    assert result.facts["candidate_content_matches_fresh_render"] is True
