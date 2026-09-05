"""Arithmetic oracle: block means and MAD computed by an independent scalar path."""

import importlib.util
from pathlib import Path
from statistics import median

import numpy as np
import pytest

SPEC = importlib.util.spec_from_file_location(
    "audit", Path(__file__).parents[1] / "scripts/audit_chime_alignment_inputs.py"
)
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


@pytest.mark.parametrize("width", AUDIT.WIDTHS)
def test_scalar_oracle(width):
    values = [float(i % 17) + (12 if 14500 < i < 16500 else 0) for i in range(32000)]
    result = AUDIT.block_diagnostic(np.array(values), width)
    blocks = [sum(values[i : i + width]) / width for i in range(0, len(values) - width + 1, width)]
    baseline = median(blocks)
    noise = 1.4826 * median([abs(x - baseline) for x in blocks])
    selected = [
        (x - baseline) / noise
        for i, x in enumerate(blocks)
        if 0.4 < (i * width + (width - 1) / 2) / len(values) < 0.6
    ]
    assert result["central_max_snr"] == pytest.approx(max(selected), rel=1e-12)
    edges = [
        (x - baseline) / noise
        for i, x in enumerate(blocks)
        if (i * width + (width - 1) / 2) / len(values) < 0.02
        or (i * width + (width - 1) / 2) / len(values) > 0.98
    ]
    assert result["edge_max_snr"] == pytest.approx(max(edges), rel=1e-12)
    assert result["noise_mad"] == pytest.approx(noise, rel=1e-12)
    assert result["width_us"] == pytest.approx(width * 2.56, rel=1e-12)
    assert result["discarded_tail_samples"] == 32000 % width


@pytest.mark.parametrize(
    "values,width",
    [(np.ones(100), 1), (np.arange(100.0), 0), (np.arange(100.0), 101), (np.full(100, np.nan), 1)],
)
def test_undefined_diagnostics_rejected(values, width):
    with pytest.raises(ValueError):
        AUDIT.block_diagnostic(values, width)
