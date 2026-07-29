"""Exact installed-manuscript checks for Figure 3."""

from __future__ import annotations

from scripts import validate_foreground_census_analysis_only as validation


def test_installed_figure_is_the_staged_approved_render() -> None:
    assert validation.MANUSCRIPT_FIGURE.is_file()
    assert validation.STAGED_FIGURE.is_file()
    assert validation.sha256_file(
        validation.MANUSCRIPT_FIGURE
    ) == validation.sha256_file(validation.STAGED_FIGURE)


def test_installed_figure_matches_the_committed_census() -> None:
    result = validation.check_census_matches_figure3(
        validation.Inputs.load(),
        figure=validation.MANUSCRIPT_FIGURE,
        render=True,
    )
    assert result.passed, result.failures
    assert result.facts["installed_matches_staged_render_byte_for_byte"] is True
    assert result.facts["installed_content_matches_fresh_render"] is True
