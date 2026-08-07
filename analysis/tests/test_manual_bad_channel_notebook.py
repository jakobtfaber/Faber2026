"""Hardened tests for notebook click-drag bad-channel editing.

Correctness criteria
--------------------
1. Analytic channel membership — for an ascending frequency axis, a closed
   interval [lo, hi] selects exactly the valid rows whose channel centres lie
   inside the interval. Invalid rows (row_valid=False) are never selected.
   Reference: ``manual_bad_channel_review.rows_for_frequency_span``.

2. Drag callback equivalence — ``_on_span_select`` (the SpanSelector path) must
   produce the same selected-row mask as ``apply_span(..., mode="flag")`` for
   the same bounds (same reference as criterion 1).

3. Invariant: view mode mutates only the visible window, never ``selected_rows``.

4. Invariant: drags narrower than half the minimum channel spacing are no-ops
   (guards against accidental single-pixel clicks becoming flags).

5. Round-trip — ``save_draft`` writes half-open row ranges whose frequency
   labels match the bundle axis; reloading via ``range_records_to_mask`` recovers
   the exact boolean mask. Frequency label tolerance is the backend's
   ``atol=1e-9`` (machine-epsilon scale for MHz floats near 1e2–1e3).

Existing tests below also cover draft-only save metadata and empty start state.
Those are schema/policy checks, not numerical baselines.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import matplotlib
import numpy as np
import pytest

matplotlib.use("Agg")


NOTEBOOK_SCRIPT = Path(__file__).parents[1] / "scripts" / "manual_bad_channel_notebook.py"
REVIEW_SCRIPT = Path(__file__).parents[1] / "scripts" / "manual_bad_channel_review.py"

NOTEBOOK_SPEC = importlib.util.spec_from_file_location(
    "manual_bad_channel_notebook", NOTEBOOK_SCRIPT
)
NOTEBOOK = importlib.util.module_from_spec(NOTEBOOK_SPEC)
assert NOTEBOOK_SPEC.loader is not None
NOTEBOOK_SPEC.loader.exec_module(NOTEBOOK)

REVIEW_SPEC = importlib.util.spec_from_file_location(
    "manual_bad_channel_review", REVIEW_SCRIPT
)
REVIEW = importlib.util.module_from_spec(REVIEW_SPEC)
assert REVIEW_SPEC.loader is not None
REVIEW_SPEC.loader.exec_module(REVIEW)

# Analytic fixture: 1 MHz channel centres, one invalid hole at 702 MHz.
FREQUENCY_MHZ = np.array([700.0, 701.0, 702.0, 703.0, 704.0, 705.0])
ROW_VALID = np.array([True, True, False, True, True, True])
# Closed interval [700.6, 704.2] ∩ valid centres → {701, 703, 704}.
ANALYTIC_SPAN = (700.6, 704.2)
ANALYTIC_MASK = np.array([False, True, False, True, True, False])


def write_bundle(path: Path) -> None:
    metadata = {
        "schema_version": 1,
        "event": "zach",
        "instrument": "chime-frb",
        "frequency_axis_sha256": "frequency",
        "source_product_sha256": "source",
    }
    np.savez_compressed(
        path,
        dynamic_spectrum=np.arange(24, dtype=np.float32).reshape(6, 4),
        frequency_mhz=FREQUENCY_MHZ,
        row_valid=ROW_VALID,
        time_ms=np.arange(4, dtype=float),
        off_mean=np.arange(6, dtype=float),
        off_standard_deviation=np.arange(6, dtype=float) + 1,
        on_spectrum=np.arange(6, dtype=float) + 2,
        metadata_json=json.dumps(metadata),
    )


def write_map(path: Path, *, status: str = "draft") -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "status": status,
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
        )
    )


def make_review(tmp_path: Path, **kwargs):
    tmp_path.mkdir(parents=True, exist_ok=True)
    bundle = tmp_path / "review.npz"
    source_map = tmp_path / "source.json"
    write_bundle(bundle)
    write_map(source_map)
    defaults = {
        "bundle_path": bundle,
        "map_path": source_map,
        "output_map_path": tmp_path / "draft.json",
        "default_frequency_window": (700.0, 705.0),
    }
    defaults.update(kwargs)
    return NOTEBOOK.ManualBadChannelNotebook(**defaults)


def test_reference_span_matches_analytic_membership():
    """Criterion 1: backend reference equals hand-derived membership."""
    selected = REVIEW.rows_for_frequency_span(
        FREQUENCY_MHZ, ROW_VALID, *ANALYTIC_SPAN
    )
    np.testing.assert_array_equal(selected, ANALYTIC_MASK)
    assert not selected[~ROW_VALID].any()


def test_notebook_flag_matches_reference_span(tmp_path: Path):
    """Criterion 1 via notebook API."""
    review = make_review(tmp_path)
    review.apply_span(*ANALYTIC_SPAN, mode="flag")
    np.testing.assert_array_equal(review.session.selected_rows, ANALYTIC_MASK)
    assert "3 rows selected" in review.status.value


def test_drag_callback_matches_direct_flag(tmp_path: Path):
    """Criterion 2: SpanSelector callback ≡ apply_span(flag)."""
    via_callback = make_review(tmp_path)
    via_callback.mode.value = "flag"
    via_callback._on_span_select(*ANALYTIC_SPAN)

    via_api = make_review(tmp_path / "api")
    via_api.apply_span(*ANALYTIC_SPAN, mode="flag")

    np.testing.assert_array_equal(
        via_callback.session.selected_rows, via_api.session.selected_rows
    )
    np.testing.assert_array_equal(via_callback.session.selected_rows, ANALYTIC_MASK)


def test_view_mode_does_not_change_selection(tmp_path: Path):
    """Criterion 3."""
    review = make_review(tmp_path)
    review.apply_span(*ANALYTIC_SPAN, mode="flag")
    before = review.session.selected_rows.copy()

    review.mode.value = "view"
    review._on_span_select(701.0, 703.0)

    np.testing.assert_array_equal(review.session.selected_rows, before)
    assert review.window == (701.0, 703.0)


def test_sub_channel_drag_is_ignored(tmp_path: Path):
    """Criterion 4: |Δν| < half channel spacing → no state change."""
    review = make_review(tmp_path)
    assert review._min_span_mhz == pytest.approx(0.5)
    review.mode.value = "flag"
    review._on_span_select(701.0, 701.0 + 0.49)

    assert not review.session.selected_rows.any()
    assert review.pending_span == (700.0, 705.0)


def test_draft_round_trip_recovers_exact_mask(tmp_path: Path):
    """Criterion 5: save → range_records_to_mask is identity on the mask."""
    review = make_review(tmp_path)
    review.apply_span(*ANALYTIC_SPAN, mode="flag")
    review.save_draft()

    payload = json.loads(review.output_map_path.read_text())
    recovered = REVIEW.range_records_to_mask(
        payload["bad_row_ranges"], FREQUENCY_MHZ
    )
    np.testing.assert_array_equal(recovered, ANALYTIC_MASK)
    assert payload["status"] == "draft"
    assert payload["review"]["reviewer"] is None
    assert payload["review"]["reviewed_at"] is None
    assert len(payload["review"]["notebook_interface_sha256"]) == 64
    assert [(item["start"], item["stop"]) for item in payload["bad_row_ranges"]] == [
        (1, 2),
        (3, 5),
    ]


def test_notebook_starts_with_no_automatic_selection(tmp_path: Path):
    review = make_review(tmp_path)
    assert not review.session.selected_rows.any()
    assert "0 rows selected" in review.status.value


def test_unflag_and_undo_follow_session_semantics(tmp_path: Path):
    review = make_review(tmp_path)
    review.apply_span(*ANALYTIC_SPAN, mode="flag")
    review.apply_span(703.5, 704.2, mode="unflag")
    np.testing.assert_array_equal(
        review.session.selected_rows, [False, True, False, True, False, False]
    )
    review.undo()
    np.testing.assert_array_equal(review.session.selected_rows, ANALYTIC_MASK)


def test_widget_layout_keeps_canvas_out_of_output(tmp_path: Path):
    """Structural invariant: canvas_box is a sibling of Output, not a child.

    Nesting ipympl inside widgets.Output swallows mouse events in Cursor/VS Code.
    """
    review = make_review(tmp_path)
    children = review.widget().children
    assert review.canvas_box in children
    assert review.figure_output in children
    assert children.index(review.canvas_box) < children.index(review.figure_output)
    assert review.canvas_box not in getattr(review.figure_output, "children", ())


def test_attach_selectors_are_vertical_on_all_panels(tmp_path: Path):
    """Drag geometry: frequency is the vertical axis on every panel."""
    import matplotlib.pyplot as plt

    review = make_review(tmp_path)
    figure, panels = REVIEW.build_review_figure(review.session, *review.window)
    try:
        review._attach_selectors(panels)
        assert len(review._span_selectors) == 3
        assert all(selector.direction == "vertical" for selector in review._span_selectors)
    finally:
        plt.close(figure)


def test_render_clears_figure_panes(tmp_path: Path, monkeypatch):
    review = make_review(tmp_path)
    scoped_calls = []
    monkeypatch.setattr(
        review.figure_output,
        "clear_output",
        lambda *, wait: scoped_calls.append(wait),
    )
    review.render()

    assert scoped_calls == [True]
    assert review.canvas_box.children == ()
