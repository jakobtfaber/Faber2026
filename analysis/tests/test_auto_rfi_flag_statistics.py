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


@pytest.fixture
def spectrum() -> np.ma.MaskedArray:
    """De-scalloped, baseline-subtracted off-pulse noise with planted defects."""
    rng = np.random.default_rng(0)
    power = rng.normal(0.0, 1.0, (NCHAN, NTIME))
    power[7] *= 12.0  # variable-gain RFI: a time-std outlier
    power[19] = np.cumsum(rng.normal(0.0, 1.0, NTIME)) * 0.3  # temporally correlated RFI
    power[31] += 25.0  # bright channel mean, ordinary variance and no correlation
    masked = np.ma.MaskedArray(power, mask=np.zeros(power.shape, bool))
    masked.mask[52, :] = True  # already fully masked by the pipeline
    return masked


def test_time_std_and_lag_one_autocorrelation_outliers_are_flagged(spectrum) -> None:
    flagged, _ = arf.auto_flag(spectrum, OFF)
    assert flagged[7], "a time-std outlier should be flagged"
    assert flagged[19], "a temporally correlated channel should be flagged"


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


def test_pure_noise_flags_nothing(spectrum) -> None:
    rng = np.random.default_rng(1)
    clean = np.ma.MaskedArray(rng.normal(0.0, 1.0, (NCHAN, NTIME)))
    flagged, info = arf.auto_flag(clean, OFF)
    assert info["n_flagged"] == 0
    assert not flagged.any()
