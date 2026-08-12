"""Pin which statistics the off-pulse RFI flagger actually cuts on.

The module docstring of `auto_rfi_flag` is a trust-basis statement, so the
statistics it names have to be the ones `auto_flag` uses. These tests assert
the behaviour that docstring describes, so a later change to one without the
other fails here.
"""

import numpy as np
import pytest

from scintillation.scint_analysis import auto_rfi_flag as arf

NCHAN, NTIME = 64, 400
OFF = (0, NTIME)
SIGMA = 5.0  # the auto_flag default this file exercises


@pytest.fixture
def spectrum() -> np.ma.MaskedArray:
    """De-scalloped, baseline-subtracted off-pulse noise with planted defects."""
    rng = np.random.default_rng(0)
    power = rng.normal(0.0, 1.0, (NCHAN, NTIME))
    power[7] *= 12.0  # variable-gain RFI: a time-std outlier
    walk = np.cumsum(rng.normal(0.0, 1.0, NTIME))
    # Temporally correlated RFI, rescaled to the ordinary time-std of the noise
    # channels: a random walk left unscaled is also a large time-std outlier, so
    # the lag-1 cut would never be the statistic under test.
    power[19] = walk / walk.std()
    power[31] += 25.0  # bright channel mean, ordinary variance and no correlation
    masked = np.ma.MaskedArray(power, mask=np.zeros(power.shape, bool))
    masked.mask[52, :] = True  # already fully masked by the pipeline
    return masked


def test_time_std_and_lag_one_autocorrelation_outliers_are_flagged(spectrum) -> None:
    flagged, _ = arf.auto_flag(spectrum, OFF)
    assert flagged[7], "a time-std outlier should be flagged"
    assert flagged[19], "a temporally correlated channel should be flagged"


def test_the_correlated_channel_is_not_a_time_std_outlier(spectrum) -> None:
    # Without this, dropping tac1 from the flagger would leave the test above
    # green: channel 19 has to be invisible to the time-std cut for its flag to
    # be attributable to the lag-1 autocorrelation cut alone.
    _, sd, _ = arf.offpulse_channel_stats(spectrum, OFF)
    finite = sd[np.isfinite(sd)]
    mad = np.median(np.abs(finite - np.median(finite))) * 1.4826
    z = (sd[19] - np.median(finite)) / mad
    assert abs(z) < SIGMA


def test_a_bright_channel_mean_alone_is_not_flagged(spectrum) -> None:
    # The spectrum reaching this flagger is baseline-subtracted, so the channel
    # mean is not an RFI statistic and cutting on it would remove good
    # channels. This is the claim the module docstring makes.
    flagged, _ = arf.auto_flag(spectrum, OFF)
    assert not flagged[31]


def test_channels_already_masked_across_the_off_pulse_window_are_flagged(spectrum) -> None:
    flagged, _ = arf.auto_flag(spectrum, OFF)
    assert flagged[52]


def test_only_the_planted_defects_are_flagged(spectrum) -> None:
    flagged, info = arf.auto_flag(spectrum, OFF)
    assert sorted(np.flatnonzero(flagged).tolist()) == [7, 19, 52]
    assert info["n_flagged"] == 3
    assert info["n_chan"] == NCHAN


def test_pure_noise_flags_nothing() -> None:
    rng = np.random.default_rng(1)
    clean = np.ma.MaskedArray(rng.normal(0.0, 1.0, (NCHAN, NTIME)))
    flagged, info = arf.auto_flag(clean, OFF)
    assert info["n_flagged"] == 0
    assert not flagged.any()
