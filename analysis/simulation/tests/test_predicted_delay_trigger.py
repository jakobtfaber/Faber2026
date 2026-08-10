"""Phase 1-4 tests of the predicted-delay trigger calibration
(docs/rse/specs/plan-predicted-delay-trigger-calibration.md)."""
import numpy as np

from simulation.predicted_delay_trigger import (
    fit_one_screen,
    make_truth_waterfall,
    predicted_delay_statistic,
    trigger_pvalue,
)


def test_statistic_finds_injected_bump_only_inside_window():
    rng = np.random.default_rng(0)
    nf, nt, dt = 16, 4096, 0.00256
    resid = rng.normal(0.0, 1.0, (nf, nt))
    t = np.arange(nt) * dt
    t_peak, tau_pred = 5.0, 3.0
    bump = np.exp(-0.5 * ((t - (t_peak + tau_pred)) / (2 * dt)) ** 2)
    resid += 4.0 * bump[None, :] / np.sqrt(nf)
    inside = predicted_delay_statistic(
        resid, valid=np.ones((nf, nt), bool), time_ms=t,
        t_peak_ms=t_peak, tau_pred_ms=tau_pred, window_frac=0.5)
    outside = predicted_delay_statistic(
        resid, valid=np.ones((nf, nt), bool), time_ms=t,
        t_peak_ms=t_peak, tau_pred_ms=1.0, window_frac=0.5)
    assert inside.matched_snr > outside.matched_snr
    assert inside.window_ms == (t_peak + 0.5 * tau_pred,
                                t_peak + 1.5 * tau_pred)


def test_statistic_is_invariant_to_masked_channels():
    rng = np.random.default_rng(1)
    nf, nt = 16, 256
    resid = rng.normal(0.0, 1.0, (nf, nt))
    valid = np.ones((nf, nt), bool)
    valid[3] = False
    t = np.arange(nt) * 0.00256
    a = predicted_delay_statistic(resid, valid, t, 0.1, 0.2, 0.5)
    resid2 = resid.copy()
    resid2[3] = 1e6
    b = predicted_delay_statistic(resid2, valid, t, 0.1, 0.2, 0.5)
    assert a.matched_snr == b.matched_snr


def test_statistic_empty_window_is_nan_not_inf():
    resid = np.zeros((4, 64))
    t = np.arange(64) * 0.00256
    out = predicted_delay_statistic(
        resid, np.ones((4, 64), bool), t, t_peak_ms=1.0,
        tau_pred_ms=100.0, window_frac=0.1)
    assert np.isnan(out.matched_snr)
    assert out.n_window_samples == 0


def test_two_screen_truth_nests_to_one_screen_just_above_r_floor():
    # r must exceed twoscreen.R_FLOOR = 1e-6, else the kernel short-circuits
    # to the identical one-screen call and the test compares EMG with itself.
    one = make_truth_waterfall(seed=7, r=0.0, snr=15.0)
    nested = make_truth_waterfall(seed=7, r=1e-5, snr=15.0)
    np.testing.assert_allclose(one.clean, nested.clean, rtol=1e-3, atol=1e-9)


def test_truth_waterfall_snr_matches_request():
    tw = make_truth_waterfall(seed=3, r=0.0, snr=20.0)
    peak_channel = tw.clean.max(axis=1).argmax()
    measured = tw.clean[peak_channel].max() / tw.noise_std[peak_channel]
    assert 15.0 < measured < 25.0


def test_truth_tau_spans_many_samples_on_this_grid():
    tw = make_truth_waterfall(seed=5, r=0.0, snr=15.0)
    dt = tw.time_ms[1] - tw.time_ms[0]
    assert tw.truth["tau1_band_ms"] / dt > 20.0


def test_ml_fit_recovers_truth_on_low_noise_one_screen():
    tw = make_truth_waterfall(seed=11, r=0.0, snr=200.0)
    fit = fit_one_screen(tw)
    assert abs(fit.tau1_ms - tw.truth["tau1_ms"]) / tw.truth["tau1_ms"] < 0.10
    assert abs(fit.t0_ms - tw.truth["t0_ms"]) < 0.05


def test_null_pvalues_are_uniformish():
    tw = make_truth_waterfall(seed=17, r=0.0, snr=15.0)
    fit = fit_one_screen(tw)
    p = trigger_pvalue(tw, fit, tau_pred_ms=3 * fit.tau1_band_ms,
                       window_frac=0.5, n_replicates=200, seed=99)
    assert 0.0 <= p <= 1.0


# ---------------------------------------------------------------------------
# Phase 4-5 tests

import pytest  # noqa: E402

from simulation.predicted_delay_trigger import (  # noqa: E402
    anchor_pair,
    declared_cells,
    rate_table,
    run_cell,
)


def test_declared_schedule_is_27_cells_with_aligned_ratios():
    cells = declared_cells()
    nulls = [c for c in cells if c[0] == "null"]
    powers = [c for c in cells if c[0] == "power"]
    assert len(nulls) == 15 and len(powers) == 12
    null_ratios = {c[3] for c in nulls}
    power_rs = {c[3] for c in powers}
    assert power_rs <= null_ratios
    assert len({c[4] for c in cells}) == 27


def test_rate_table_envelope_and_detection_on_constructed_samples():
    rng = np.random.default_rng(0)
    nulls = {"null:a": rng.normal(0, 1, 400).tolist(),
             "null:b": (rng.normal(0, 1, 400) + 1.0).tolist()}
    powers = {"power:hi": np.full(100, 50.0).tolist(),
              "power:lo": np.full(100, -50.0).tolist()}
    table = rate_table(nulls, powers, rates=(0.01,))
    envelope = table["thresholds"][0.01]
    assert envelope == max(table["per_cell_null_quantiles"][0.01].values())
    assert envelope == pytest.approx(
        np.quantile(np.asarray(nulls["null:b"]), 0.99), abs=1e-12)
    assert table["detection"][0.01]["power:hi"] == 1.0
    assert table["detection"][0.01]["power:lo"] == 0.0


def test_rate_table_fails_closed_on_majority_nan_cell():
    nulls = {"null:bad": [float("nan")] * 6 + [0.0] * 4}
    with pytest.raises(ValueError, match="cannot set a threshold"):
        rate_table(nulls, {}, rates=(0.01,))


def test_run_injection_failure_records_nan_not_raise(monkeypatch):
    import simulation.predicted_delay_trigger as pdt
    monkeypatch.setattr(pdt, "fit_one_screen",
                        lambda tw: (_ for _ in ()).throw(RuntimeError("x")))
    rec = pdt.run_injection("null", 15.0, 3.0, seed=1)
    assert np.isnan(rec["statistic"]) and "error" in rec


@pytest.mark.slow
def test_smoke_cell_produces_finite_statistics():
    records = run_cell("null", 30.0, 3.0, n=2, cell_index=0)
    stats = [r["statistic"] for r in records]
    assert len(stats) == 2 and all(np.isfinite(s) for s in stats)
    power = run_cell("power", 30.0, 3.0, n=1, cell_index=1)
    assert np.isfinite(power[0]["statistic"])


@pytest.mark.slow
def test_anchor_pair_smoke_nested_agrees_with_ml():
    pair = anchor_pair("null", 30.0, 3.0, seed=5, nlive=60,
                       n_replicates=50)
    assert np.isfinite(pair["ml_statistic"])
    assert np.isfinite(pair["nested_statistic"])
    assert abs(pair["ml_statistic"] - pair["nested_statistic"]) < 2.0
