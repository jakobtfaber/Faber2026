"""Raw-layer axis conventions + dispersion-measure sign (wayfinder ticket 17).

Always-on: corrected dispersion-measure bin-shift sign (no local data).
Local-data: checksum + frequency-order asserts against
docs/rse/certificates/l0-certificates.json when ~/Data/Faber2026/dsa110 is present.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from l0_conventions import (  # noqa: E402
    apply_binshifts,
    dm_binshift_samples,
    freq_order_from_axis,
    md5_prefix,
    sha256_file,
)

DATA = Path.home() / "Data/Faber2026/dsa110"
CERTS = ROOT / "docs/rse/certificates/l0-certificates.json"
REGISTRY = ROOT / "docs/rse/control/results-registry.toml"

EXPECTED_ORDER = {
    "chime_full": "descending",
    "dsa": "descending",
    "chime_upchan": "ascending",
}


def test_dm_binshift_positive_delta_moves_high_freq_later():
    """Handoff single-channel sign: positive dispersion-measure offset moves a high-frequency pulse later versus 400 MHz."""
    dt = 2.56e-6 * 2 * 16  # casey-like upchan DT
    f_hi = 780.0
    shift = float(dm_binshift_samples(np.array([f_hi]), delta_dm=1.0, dt_s=dt)[0])
    assert shift > 0
    # Approximate handoff check: +1 pc/cm³ at 780 MHz moves ~233 bins on casey DT.
    assert 200 < shift < 280

    n_t = 4000
    pulse_bin = 1000
    data = np.zeros((2, n_t))
    data[0, pulse_bin] = 1.0  # low-ish
    data[1, pulse_bin] = 1.0  # high
    freqs = np.array([450.0, 780.0])
    shifts = dm_binshift_samples(freqs, delta_dm=1.0, dt_s=dt)
    moved = apply_binshifts(data, shifts)
    peak_lo = int(np.argmax(moved[0]))
    peak_hi = int(np.argmax(moved[1]))
    assert peak_hi > peak_lo


def test_freq_order_from_axis_helpers():
    assert freq_order_from_axis(np.linspace(400, 800, 16)) == "ascending"
    assert freq_order_from_axis(np.linspace(800, 400, 16)) == "descending"
    assert freq_order_from_axis(np.array([1.0, 3.0, 2.0])) == "mixed"


def test_registry_has_thirty_six_derived_intensity_rows():
    text = REGISTRY.read_text()
    assert "Derived intensity-product inventory" in text
    assert "NOT treat as" in text or "not raw" in text.lower()
    n = text.count('kind = "input_certificate"')
    assert n == 36


def test_certificate_json_schema_and_orders():
    assert CERTS.is_file(), "run scripts/build_l0_certificates.py first"
    rows = json.loads(CERTS.read_text())
    assert len(rows) == 36
    nicks = {r["nick"] for r in rows}
    assert len(nicks) == 12
    for r in rows:
        assert r["freq_order"] == EXPECTED_ORDER[r["product"]], r
        assert r["md5_ok"] is True
        assert len(r["sha256"]) == 64
        assert len(r["deck_md5"]) == 8


@pytest.mark.skipif(not DATA.is_dir(), reason="local Faber2026 data tree absent")
def test_local_bytes_match_certificates():
    rows = json.loads(CERTS.read_text())
    for r in rows:
        path = Path(r["local_path"].replace("~", str(Path.home())))
        assert path.is_file(), path
        assert md5_prefix(path) == r["deck_md5"]
        assert sha256_file(path) == r["sha256"]
        if r["product"] == "chime_upchan":
            freq_path = Path(r["freq_path"].replace("~", str(Path.home())))
            freq = np.load(freq_path)
            assert freq_order_from_axis(freq) == "ascending"
            assert sha256_file(freq_path) == r["freq_sha256"]


@pytest.mark.skipif(not DATA.is_dir(), reason="local Faber2026 data tree absent")
def test_local_chime_cellular_band_still_descending():
    """Spot-check: casey full-resolution cellular-band method still returns descending."""
    sys.path.insert(0, str(ROOT / "scripts"))
    from audit_fig1_axes import audit_chime_ordering

    rows = json.loads(CERTS.read_text())
    casey = next(r for r in rows if r["nick"] == "casey" and r["product"] == "chime_full")
    path = Path(casey["local_path"].replace("~", str(Path.home())))
    verdict = audit_chime_ordering(path, n_rows=casey["shape"][0])["verdict"]
    assert verdict == "descending"
