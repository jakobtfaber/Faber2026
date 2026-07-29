import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from inventory_absolute_dm_inputs_h17 import (  # noqa: E402
    _row_matches,
    _support_masks,
    load_path_manifest,
)


def test_support_masks_partition_rows() -> None:
    reference = np.asarray(
        [
            [np.nan, np.nan, np.nan],
            [2.0, 2.0, 2.0],
            [1.0, 2.0, 3.0],
        ]
    )

    support = _support_masks(reference)

    assert support["all_nan"].tolist() == [True, False, False]
    assert support["finite_flat"].tolist() == [False, True, False]
    assert support["live"].tolist() == [False, False, True]


def test_row_matches_recovers_exact_crop() -> None:
    rng = np.random.default_rng(7)
    raw = rng.normal(size=(3, 128)).astype(np.float32)
    reference = raw[:, 31:79].copy()

    matches = _row_matches(raw, reference, np.arange(3))

    assert [row["best_start_sample"] for row in matches] == [31, 31, 31]
    assert all(row["correlation"] > 0.999999 for row in matches)
    assert all(row["exact_float32_fraction"] == 1.0 for row in matches)


def test_path_manifest_requires_all_roles(tmp_path: Path) -> None:
    manifest = tmp_path / "paths.tsv"
    manifest.write_text("casey\traw_chime_h5\t/data/casey.h5\n")

    with pytest.raises(ValueError, match="missing roles"):
        load_path_manifest(manifest)
