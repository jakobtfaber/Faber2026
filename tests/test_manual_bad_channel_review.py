from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest


SCRIPT = Path(__file__).parents[1] / "scripts" / "manual_bad_channel_review.py"
SPEC = importlib.util.spec_from_file_location("manual_bad_channel_review", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def bundle() -> MODULE.ReviewBundle:
    frequency = np.array([700.0, 701.0, 702.0, 703.0, 704.0, 705.0])
    dynamic = np.arange(24, dtype=np.float32).reshape(6, 4)
    return MODULE.ReviewBundle(
        dynamic_spectrum=dynamic,
        frequency_mhz=frequency,
        row_valid=np.array([True, True, False, True, True, True]),
        time_ms=np.arange(4, dtype=float),
        off_mean=np.arange(6, dtype=float),
        off_standard_deviation=np.arange(6, dtype=float) + 1,
        on_spectrum=np.arange(6, dtype=float) + 2,
        metadata={
            "schema_version": 1,
            "event": "zach",
            "instrument": "chime-frb",
            "frequency_axis_sha256": "frequency",
            "source_product_sha256": "source",
        },
    )


def draft_map() -> dict:
    return {
        "schema_version": 1,
        "status": "draft",
        "event": "zach",
        "instrument": "chime-frb",
        "source_product": {"path": "/source.npy", "sha256": "source"},
        "frequency_axis": {
            "path": "/frequency.npy",
            "sha256": "frequency",
            "row_count": 6,
        },
        "bad_row_ranges": [],
        "review": {
            "reviewer": None,
            "reviewed_at": None,
            "evidence": [],
            "notes": "",
        },
    }


def test_span_selects_exact_valid_rows_and_ranges_are_half_open():
    review = bundle()

    selected = MODULE.rows_for_frequency_span(
        review.frequency_mhz, review.row_valid, 700.6, 704.2
    )
    records = MODULE.mask_to_range_records(
        selected,
        review.frequency_mhz,
        reason="owner manual selection",
        evidence="review.npz",
    )

    np.testing.assert_array_equal(selected, [False, True, False, True, True, False])
    assert [(item["start"], item["stop"]) for item in records] == [(1, 2), (3, 5)]
    assert records[1]["frequency_min_mhz"] == 703.0
    assert records[1]["frequency_max_mhz"] == 704.0


def test_span_selection_supports_descending_frequency_axes_and_single_row_clicks():
    frequency = np.array([705.0, 704.0, 703.0, 702.0, 701.0, 700.0])
    valid = np.ones(6, dtype=bool)

    selected = MODULE.rows_for_frequency_span(frequency, valid, 701.5, 703.5)
    click = MODULE.rows_for_frequency_span(frequency, valid, 704.49, 704.49)

    np.testing.assert_array_equal(selected, [False, False, True, True, False, False])
    np.testing.assert_array_equal(click, [False, True, False, False, False, False])


def test_bundle_binding_rejects_map_drift():
    MODULE.verify_map_binding(draft_map(), bundle())
    payload = draft_map()
    payload["frequency_axis"]["sha256"] = "changed"

    with pytest.raises(ValueError, match="frequency-axis SHA-256 mismatch"):
        MODULE.verify_map_binding(payload, bundle())


def test_session_add_undo_and_clear_are_exact():
    session = MODULE.ManualFlaggingSession(draft_map(), bundle())

    session.add_span(700.6, 704.2)
    np.testing.assert_array_equal(
        session.selected_rows, [False, True, False, True, True, False]
    )
    session.undo()
    assert not session.selected_rows.any()
    session.add_span(703.5, 705.1)
    session.clear()
    assert not session.selected_rows.any()


def test_session_can_remove_only_a_selected_subspan():
    session = MODULE.ManualFlaggingSession(draft_map(), bundle())
    session.add_span(700.0, 705.0)

    session.remove_span(703.5, 705.1)

    np.testing.assert_array_equal(
        session.selected_rows, [True, True, False, True, False, False]
    )


def test_save_writes_draft_only_and_preserves_retained_values(tmp_path: Path):
    review = bundle()
    session = MODULE.ManualFlaggingSession(draft_map(), review)
    session.add_span(703.5, 705.1)
    output = tmp_path / "zach.json"

    session.save_draft(
        output,
        reason="owner manual selection",
        evidence="zach-review.npz",
    )

    payload = json.loads(output.read_text())
    assert payload["status"] == "draft"
    assert payload["review"]["reviewer"] is None
    assert payload["review"]["reviewed_at"] is None
    assert len(payload["review"]["editor_sha256"]) == 64
    assert [(item["start"], item["stop"]) for item in payload["bad_row_ranges"]] == [
        (4, 6)
    ]
    masked = MODULE.mask_preview(review.dynamic_spectrum, session.selected_rows)
    np.testing.assert_array_equal(masked[~session.selected_rows], review.dynamic_spectrum[~session.selected_rows])
    assert np.isnan(masked[session.selected_rows]).all()


def test_approved_map_cannot_be_edited_or_downgraded(tmp_path: Path):
    payload = draft_map()
    payload["status"] = "owner_approved"

    with pytest.raises(ValueError, match="approved map is immutable"):
        MODULE.ManualFlaggingSession(payload, bundle())


def test_headless_figure_smoke(tmp_path: Path):
    import matplotlib

    matplotlib.use("Agg")
    session = MODULE.ManualFlaggingSession(draft_map(), bundle())
    session.add_span(703.5, 705.1)

    figure, _ = MODULE.build_review_figure(session, 700.0, 705.0)
    output = tmp_path / "preview.png"
    figure.savefig(output)

    assert output.stat().st_size > 0
