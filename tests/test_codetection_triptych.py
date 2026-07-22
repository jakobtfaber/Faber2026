"""Tests for the codetection data|model|residual fit-audit figures."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "pipeline"))

import plot_codetection_triptych as triptych  # noqa: E402
from flits.batch.codetection_plots import BandSpectrum  # noqa: E402

from plot_codetection_triptych import (  # noqa: E402
    BANDS,
    PAD_FLOOR_MS,
    chime_width_display_window,
    crop_spectrum,
    load_manifest,
)


def _fake_band(label: str, t0: float, t1: float, dt: float = 0.033) -> BandSpectrum:
    t = np.arange(t0, t1 + dt, dt)
    n_f, n_t = 8, t.size
    data = np.zeros((n_f, n_t))
    # bright on-pulse block in the middle third
    i0, i1 = n_t // 3, 2 * n_t // 3
    data[:, i0:i1] = 5.0
    data += 0.01  # keep finite
    return BandSpectrum(
        freq_mhz=np.linspace(400, 800, n_f)
        if "CHIME" in label
        else np.linspace(1300, 1500, n_f),
        time_ms=t,
        data=data,
        model=data * 0.9,
        sigma=np.ones(n_f),
        label=label,
        channel_valid=np.ones(n_f, bool),
    )


def test_manifest_has_twelve_and_chromatica_null():
    rows = load_manifest(ROOT / "scripts" / "jointmodel_triptych_manifest.yaml")
    assert len(rows) == 12
    chrom = next(r for r in rows if r["nick"] == "chromatica")
    assert chrom["npz"] is None
    assert sum(1 for r in rows if r["npz"]) == 3


def test_chromatica_archival_chime_uses_x13_time_binning():
    """The sole archival data-only page keeps the documented ~33 us grid."""
    assert BANDS["chime"]["t_factor"] == 13
    assert BANDS["chime"]["dt_ms"] * BANDS["chime"]["t_factor"] == pytest.approx(
        0.03328
    )


def test_chime_width_pad_formula():
    # CHIME on-pulse ~10 ms wide inside [-20, 20]; DSA narrower but aligned.
    chime = _fake_band("CHIME/FRB", -20.0, 20.0)
    dsa = _fake_band("DSA-110", -20.0, 20.0)
    # Force known on-pulse by writing a narrow CHIME pulse of width ~10 ms
    t = chime.time_ms
    data = np.zeros_like(chime.data)
    mask = (t >= -5.0) & (t <= 5.0)
    data[:, mask] = 10.0
    chime = BandSpectrum(
        freq_mhz=chime.freq_mhz,
        time_ms=t,
        data=data,
        model=chime.model,
        sigma=chime.sigma,
        label=chime.label,
        channel_valid=chime.channel_valid,
    )
    dsa_data = np.zeros_like(dsa.data)
    dsa_mask = (dsa.time_ms >= -2.0) & (dsa.time_ms <= 2.0)
    dsa_data[:, dsa_mask] = 10.0
    dsa = BandSpectrum(
        freq_mhz=dsa.freq_mhz,
        time_ms=dsa.time_ms,
        data=dsa_data,
        model=dsa.model,
        sigma=dsa.sigma,
        label=dsa.label,
        channel_valid=dsa.channel_valid,
    )
    t0, t1 = chime_width_display_window([chime, dsa])
    # Union ~[-5,5], W_C~10 → pad ~W_C → window roughly [-15, 15]
    assert t0 == pytest.approx(-15.0, abs=2.5)
    assert t1 == pytest.approx(15.0, abs=2.5)
    assert (t1 - t0) == pytest.approx(30.0, abs=4.0)


def test_pad_floor_for_narrow_chime():
    t = np.arange(-10, 10, 0.033)
    data = np.zeros((4, t.size))
    data[:, (t >= -0.2) & (t <= 0.2)] = 8.0
    chime = BandSpectrum(
        freq_mhz=np.linspace(400, 800, 4),
        time_ms=t,
        data=data,
        model=data,
        sigma=np.ones(4),
        label="CHIME/FRB",
        channel_valid=np.ones(4, bool),
    )
    dsa = BandSpectrum(
        freq_mhz=np.linspace(1300, 1500, 4),
        time_ms=t,
        data=data,
        model=data,
        sigma=np.ones(4),
        label="DSA-110",
        channel_valid=np.ones(4, bool),
    )
    t0, t1 = chime_width_display_window([chime, dsa])
    # Narrow CHIME → pad floor 1.5 ms dominates over W_C
    assert (t1 - t0) / 2 == pytest.approx(PAD_FLOOR_MS + 0.2, abs=0.8)
    assert t0 < -1.0 and t1 > 1.0


def test_crop_spectrum_keeps_alignment():
    b = _fake_band("CHIME/FRB", -30, 30)
    c = crop_spectrum(b, -5.0, 5.0)
    assert c.time_ms[0] >= -5.1
    assert c.time_ms[-1] <= 5.1
    assert c.data.shape[1] == c.time_ms.size == c.model.shape[1]


def test_toa_offset_is_rereferenced_to_target_dm():
    legacy = triptych.toa_offset_ms("oran")
    target = 397.015535
    old_dm = 396.882
    expected_delta = (
        1e3 * triptych.K_DM_S_MHZ2 * (target - old_dm) * (400.0**-2 - 1530.0**-2)
    )
    got = triptych.toa_offset_at_dm_ms("oran", target)
    assert got == pytest.approx(legacy - expected_delta)
    assert abs(got - legacy) > 3.0


def test_render_disables_model_overlay(monkeypatch, tmp_path):
    """Contract: the producer call must disable model overlays on data."""
    calls = []

    class FakeFigure:
        def suptitle(self, *args, **kwargs):
            pass

        def savefig(self, *args, **kwargs):
            pass

    artifact = tmp_path / "fit.npz"
    summary = tmp_path / "fit.json"
    artifact.write_bytes(b"npz")
    summary.write_bytes(b"json")
    monkeypatch.setattr(triptych, "bands_from_npz", lambda *args, **kwargs: [])
    monkeypatch.setattr(
        triptych,
        "plot_codetection",
        lambda bands, **kwargs: calls.append(kwargs) or FakeFigure(),
    )
    monkeypatch.setattr(triptych.plt, "close", lambda fig: None)

    triptych.render_row(
        {
            "nick": "zach",
            "tns": "FRB 20220207C",
            "npz": str(artifact),
            "npz_sha256": hashlib.sha256(b"npz").hexdigest(),
            "fit_json": str(summary),
            "fit_json_sha256": hashlib.sha256(b"json").hexdigest(),
        },
        root=tmp_path,
        data_root=tmp_path,
        out_dir=tmp_path,
        dpi=72,
    )
    assert calls[0]["show_model_on_data"] is False


def test_render_metadata_uses_source_date_epoch(monkeypatch):
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1784505600")
    pdf = triptych.render_metadata(".pdf")
    svg = triptych.render_metadata(".svg")
    assert pdf["CreationDate"] == pdf["ModDate"]
    assert pdf["CreationDate"].tzinfo is not None
    assert svg == {"Date": "2026-07-20T00:00:00+00:00"}
    assert triptych.matplotlib.rcParams["svg.hashsalt"] == (
        "Faber2026-codetection-triptych-v2"
    )


def test_candidate_hash_mismatch_fails_closed(tmp_path):
    artifact = tmp_path / "artifact.npz"
    artifact.write_bytes(b"changed")
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        triptych.require_sha256(artifact, "0" * 64, label="candidate")


def test_bands_from_npz_anchors_on_fitted_toa(monkeypatch, tmp_path):
    """DSA dominant-component t0 -> t=0; CHIME fitted arrival -> measured offset."""
    import json as _json

    n_t = 400
    dt = 0.065536
    t = np.arange(n_t) * dt
    burst_idx = 200

    def _cube():
        data = np.zeros((6, n_t))
        data[:, burst_idx : burst_idx + 8] = 20.0
        model = np.zeros_like(data)
        model[:, burst_idx] = 1.0
        return data, model

    dataC, modelC = _cube()
    dataD, modelD = _cube()
    npz = tmp_path / "syn_jointmodel_X.npz"
    np.savez(
        npz,
        timeC=t,
        dataC=dataC,
        modelC=modelC,
        noiseC=np.ones(6),
        validC=np.ones(6, bool),
        freqC=np.linspace(0.4, 0.8, 6),
        timeD=t,
        dataD=dataD,
        modelD=modelD,
        noiseD=np.ones(6),
        validD=np.ones(6, bool),
        freqD=np.linspace(1.31, 1.5, 6),
    )
    t_burst = float(t[burst_idx])
    (tmp_path / "syn_joint_fit_X.json").write_text(
        _json.dumps(
            {
                "percentiles": {
                    "t0_C1": {"median": t_burst - 0.3},
                    "t0_C2": {"median": t_burst - 6.0},  # weak early component: ignored
                    "t0_D1": {"median": t_burst - 0.1},
                }
            }
        )
    )
    offset = 2.0
    monkeypatch.setattr(triptych, "toa_offset_ms", lambda nick, toa_json=None: offset)

    bands = triptych.bands_from_npz(npz, "syn")
    chime = next(b for b in bands if "CHIME" in b.label)
    dsa = next(b for b in bands if "DSA" in b.label)
    # Fitted arrivals: DSA at 0, CHIME at offset -> burst peaks land at
    # +0.1 (DSA) and offset + 0.3 (CHIME).
    prof_d = np.nansum(dsa.data, axis=0)
    prof_c = np.nansum(chime.data, axis=0)
    peak_d = float(dsa.time_ms[int(np.argmax(prof_d))])
    peak_c = float(chime.time_ms[int(np.argmax(prof_c))])
    assert peak_d == pytest.approx(0.1, abs=dt)
    assert peak_c == pytest.approx(offset + 0.3, abs=dt)


def test_manifest_yaml_parses_flags():
    rows = load_manifest(ROOT / "scripts" / "jointmodel_triptych_manifest.yaml")
    flagged = {r["nick"] for r in rows if r.get("flag") and r["nick"] != "chromatica"}
    assert flagged == {
        row["nick"]
        for row in load_manifest(ROOT / "scripts/jointmodel_triptych_manifest.yaml")
        if row["nick"] != "chromatica"
    }


def test_only_current_jointtf_candidates_have_model_artifacts():
    rows = {
        row["nick"]: row
        for row in load_manifest(ROOT / "scripts/jointmodel_triptych_manifest.yaml")
    }
    expected = {
        "oran": ("C1D1", 171),
        "johndoeii": ("C1D2", 175),
        "zach": ("C2D3", 178),
    }
    assert {nick for nick, row in rows.items() if row["npz"]} == set(expected)
    for nick, (components, job) in expected.items():
        row = rows[nick]
        assert row["status"] == "candidate-v2-owner-pending"
        assert row["components"] == components
        assert row["fit_job"] == job
        assert row["gain_s2"] == 100
        assert row["fit_generation_reproducible"] is False
        assert row["npz"].startswith("results-library:")
        assert row["fit_json"].startswith("results-library:")
        assert len(row["npz_sha256"]) == 64
        assert len(row["fit_json_sha256"]) == 64
    for nick, row in rows.items():
        if nick not in expected:
            assert row["status"] == "withheld-no-current-candidate"
            assert row["npz"] is None


def test_candidate_fit_artifacts_match_declared_counts_and_gain_prior():
    for row in load_manifest(ROOT / "scripts/jointmodel_triptych_manifest.yaml"):
        if not row["npz"]:
            continue
        fit_path = triptych.resolve_artifact_path(row["fit_json"])
        triptych.require_sha256(
            fit_path, row["fit_json_sha256"], label=f"{row['nick']} fit summary"
        )
        fit = json.loads(fit_path.read_text())
        assert row["status"] == "candidate-v2-owner-pending"
        assert fit["fixed_parameters"] == {}
        assert fit["gain_s2"] == pytest.approx(row["gain_s2"])
        assert f"C{fit['components_C']}D{fit['components_D']}" == row["components"]
