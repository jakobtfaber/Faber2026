"""Analytic Fourier modes and independent noise anchors protect pulse-lag tests."""

import importlib.util
from pathlib import Path

import h5py
import numpy as np
import pytest

SPEC = importlib.util.spec_from_file_location(
    "lineage", Path(__file__).parents[1] / "scripts/verify_chime_voltage_lineage.py"
)
LINEAGE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(LINEAGE)


@pytest.mark.parametrize("mode", [-13, 11])
def test_fourier_mode_phase(mode):
    count, dt, center, dm = 128, 2.56e-6, 600.0, 400.0
    samples = np.arange(count)
    wave = np.exp(2j * np.pi * mode * samples / count)
    frequency = mode / (count * dt * 1e6)
    angle = 2 * np.pi * 1e6 / 2.41e-4 * dm * frequency**2 / ((frequency + center) * center**2)
    expected = wave * complex(np.cos(angle), np.sin(angle))
    np.testing.assert_allclose(
        LINEAGE.dechirp(wave, dm, center, dt), expected, rtol=1e-10, atol=1e-10
    )
    np.testing.assert_allclose(LINEAGE.dechirp(wave, 0.0, center, dt), wave, rtol=1e-12, atol=1e-12)


def pair():
    rng = np.random.default_rng(20260904)
    raw = rng.normal(size=60000)
    raw += 500 * np.exp(-0.5 * ((np.arange(raw.size) - 26000) / 3) ** 2)
    return raw, raw[10000:42000].copy()


def test_noise_alignment_ignores_pulse_and_bad_early_edge():
    raw, native = pair()
    native[:3000] = np.random.default_rng(22).normal(size=3000)
    native[LINEAGE.PULSE] = 0
    result = LINEAGE.match_noise(raw, native * 7 + 3)
    assert result["origin_sample"] == 10000
    assert result["holdout_correlation"] == pytest.approx(1.0, abs=1e-12)


def test_independent_holdout_rejects_false_alignment():
    raw, native = pair()
    native[LINEAGE.HOLD] = np.random.default_rng(5).normal(size=4096)
    assert LINEAGE.match_noise(raw, native) is None


@pytest.mark.parametrize("delay", [-8, 0, 8])
def test_physical_pulse_shift_survives_noise_alignment(delay):
    raw, native = pair()
    reference = native.copy()
    x = np.arange(native.size)
    native += 500 * (
        np.exp(-0.5 * ((x - 16000 - delay) / 3) ** 2) - np.exp(-0.5 * ((x - 16000) / 3) ** 2)
    )
    assert LINEAGE.match_noise(raw, native)["origin_sample"] == 10000
    assert LINEAGE.pulse_lag(native, reference)["lag_native_bins"] == delay


@pytest.mark.parametrize("delay", [-16, -8, 8, 16, None])
def test_shared_noise_cannot_hide_changed_broad_weak_pulse(delay):
    noise = np.random.default_rng(14).normal(size=32000)
    x = np.arange(32000)
    reference = noise + 4 * np.exp(-0.5 * ((x - 16000) / 256) ** 2)
    native = noise.copy()
    if delay is not None:
        native += 4 * np.exp(-0.5 * ((x - 16000 - delay) / 256) ** 2)
    assert (
        LINEAGE.waveform_error(native[LINEAGE.PULSE], reference[LINEAGE.PULSE])
        > LINEAGE.IDENTITY_TOLERANCE
    )
    assert LINEAGE.waveform_error(reference[LINEAGE.PULSE], reference[LINEAGE.PULSE]) == 0


@pytest.mark.parametrize("defect", [None, "nonfinite-native-support", "constant-training-window"])
def test_event_reports_required_unusable_channel(tmp_path, monkeypatch, defect):
    native_path = tmp_path / "casey_chime_I_0_0_32000b_cntr_bpc.npy"
    raw_path = tmp_path / "singlebeam.h5"
    cube = np.full((1024, 32000), np.nan, dtype=np.float32)
    cube[:17] = np.random.default_rng(48).normal(size=32000)
    if defect == "nonfinite-native-support":
        cube[16, 100] = np.nan
    elif defect == "constant-training-window":
        cube[16, LINEAGE.TRAIN] = 0
    with h5py.File(raw_path, "w") as h5:
        frequencies = np.zeros(17, dtype=[("id", "i4"), ("centre", "f8")])
        frequencies["id"] = np.arange(17)
        frequencies["centre"] = np.where(np.arange(17) < 8, 500, 700)
        h5.create_dataset("index_map/freq", data=frequencies)
        h5.create_dataset("time0", data=np.zeros(17, dtype=[("fpga_count", "i8")]))
        h5.attrs["delta_time"] = 2.56e-6
    monkeypatch.setattr(
        Path, "glob", lambda self, pattern: iter([raw_path if pattern == "*.h5" else native_path])
    )
    monkeypatch.setattr(LINEAGE.np, "load", lambda *args, **kwargs: cube)
    monkeypatch.setattr(LINEAGE, "sha256", lambda path: "fixture")

    def reconstruct(h5, row, native, dm):
        return (
            {
                "origin_sample": 0,
                "frequency_mhz": float(frequencies[row]["centre"]),
                "holdout_waveform_error": 0,
                "pulse_waveform_error": 0,
            },
            native,
            native.copy(),
        )

    monkeypatch.setattr(LINEAGE, "reconstruct_row", reconstruct)
    result = LINEAGE.event("casey")
    assert result["native_live_channels"] == 17
    assert result["native_channels_missing_from_h5"] == []
    if defect:
        assert result["verdict"] == "inconclusive-alignment-or-support"
        assert len(result["matched_channels"]) == 16
        assert result["rejected_channels"] == [{"channel_id": 16, "reason": defect}]
    else:
        assert result["verdict"] == "heldout-waveform-identity-pass"
        assert len(result["matched_channels"]) == 17
        assert result["rejected_channels"] == []
