"""Unit tests for the Figure 1 residual-drift gate."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from audit_fig1_residual_drift import (  # noqa: E402
    ROSTER_DEFAULT,
    audit,
    product_dm,
    roster_nicks,
    zero_consistency,
)
from audit_fig1_frequency_axes import order, parse_sigproc_header  # noqa: E402


def test_product_dm_parses_archival_filename():
    assert product_dm(Path("chromatica_chime_I_272_368_cntr_bpc.npy")) == 272.368


def test_zero_consistency_is_fail_closed():
    assert zero_consistency({"n": 8, "residual_dm": 0.01, "sigma": 0.01}) == "consistent_zero"
    assert zero_consistency({"n": 8, "residual_dm": 0.03, "sigma": 0.01}) == "nonzero"
    assert zero_consistency({"n": 2, "residual_dm": None, "sigma": None}) == "unconstrained"


def test_frequency_order_is_explicit():
    assert order(1498.75, 1311.28) == "descending"
    assert order(400.0, 800.0) == "ascending"


def test_roster_is_twelve_unique_bursts():
    assert len(roster_nicks(ROSTER_DEFAULT)) == 12


def test_gate_rejects_partial_catalog(tmp_path):
    partial = tmp_path / "catalog.csv"
    partial.write_text("nick,adopted_dm\nzach,262.361665\n")
    try:
        audit(tmp_path, partial)
    except ValueError as exc:
        assert "roster" in str(exc)
    else:
        raise AssertionError("expected a partial catalog to be rejected before gating")


def test_sigproc_header_parser_reads_dsa_fields():
    import struct

    def string(value: bytes) -> bytes:
        return struct.pack("<i", len(value)) + value

    blob = (
        string(b"HEADER_START")
        + string(b"fch1") + struct.pack("<d", 1498.75)
        + string(b"foff") + struct.pack("<d", -0.03051757812)
        + string(b"nchans") + struct.pack("<i", 6144)
        + string(b"tsamp") + struct.pack("<d", 0.000032768)
        + string(b"HEADER_END")
    )
    header = parse_sigproc_header(blob)
    assert header["fch1"] == 1498.75
    assert header["nchans"] == 6144
    assert header["tsamp"] == 0.000032768
