from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest


SCRIPT = Path(__file__).parents[1] / "scripts" / "manual_bad_channel_gui.py"
SPEC = importlib.util.spec_from_file_location("manual_bad_channel_gui", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


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
        dynamic_spectrum=np.arange(36, dtype=np.float32).reshape(6, 6),
        frequency_mhz=np.array([700.0, 701.0, 702.0, 703.0, 704.0, 705.0]),
        row_valid=np.array([True, True, False, True, True, True]),
        time_ms=np.arange(6, dtype=float),
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


def make_gui(tmp_path: Path, **kwargs):
    bundle = tmp_path / "review.npz"
    source_map = tmp_path / "source.json"
    write_bundle(bundle)
    write_map(source_map)
    return MODULE.ManualBadChannelGUI(
        bundle_path=bundle,
        map_path=source_map,
        output_map_path=tmp_path / "draft.json",
        default_frequency_window=(700.0, 702.0),
        band_width_mhz=2.0,
        build=False,
        **kwargs,
    )


def test_drag_dispatch_flags_and_unflags_exact_rows(tmp_path: Path):
    gui = make_gui(tmp_path)

    gui.apply_span(700.6, 704.2, mode="flag")
    np.testing.assert_array_equal(
        gui.session.selected_rows, [False, True, False, True, True, False]
    )

    gui.apply_span(703.5, 704.2, mode="unflag")
    np.testing.assert_array_equal(
        gui.session.selected_rows, [False, True, False, True, False, False]
    )
    gui.undo()
    assert int(gui.session.selected_rows.sum()) == 3
    gui.clear()
    assert not gui.session.selected_rows.any()


def test_band_navigation_is_bounded_and_exact(tmp_path: Path):
    gui = make_gui(tmp_path)

    gui.next_band()
    assert gui.window == pytest.approx((702.0, 704.0))
    gui.next_band()
    assert gui.window == pytest.approx((703.0, 705.0))
    gui.previous_band()
    assert gui.window == pytest.approx((701.0, 703.0))


def test_save_is_draft_only_and_records_gui_hash(tmp_path: Path):
    gui = make_gui(tmp_path)
    gui.apply_span(703.5, 705.1, mode="flag")

    gui.save_draft()

    payload = json.loads(gui.output_map_path.read_text())
    assert payload["status"] == "draft"
    assert payload["review"]["reviewer"] is None
    assert payload["review"]["reviewed_at"] is None
    assert len(payload["review"]["gui_interface_sha256"]) == 64
    assert [(item["start"], item["stop"]) for item in payload["bad_row_ranges"]] == [
        (4, 6)
    ]


def test_approved_map_is_immutable(tmp_path: Path):
    bundle = tmp_path / "review.npz"
    source_map = tmp_path / "approved.json"
    write_bundle(bundle)
    write_map(source_map, status="owner_approved")

    with pytest.raises(ValueError, match="approved map is immutable"):
        MODULE.ManualBadChannelGUI(
            bundle_path=bundle,
            map_path=source_map,
            output_map_path=tmp_path / "draft.json",
            build=False,
        )


def test_headless_gui_build_has_three_drag_panels(tmp_path: Path):
    gui = make_gui(tmp_path)

    figure = gui.build()

    assert figure is gui.figure
    assert set(gui.data_axes) == {"before", "after", "spectrum"}
    assert len(gui.span_selectors) == 3
    assert gui.data_axes["spectrum"].get_ylim() == pytest.approx((700.0, 702.0))
    gui.close()
