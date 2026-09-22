"""Guard that scatter_broaden conserves flux for any input dtype.

The 2D branch used to allocate its output with ``np.zeros_like(signal)`` on the
caller's array, because the float64 cast inside ``_validate_and_prepare_inputs``
was discarded rather than returned. An integer dynamic spectrum therefore had
every broadened sample truncated toward zero, silently breaking the unit-integral
normalisation the docstring promises.
"""

from __future__ import annotations

import numpy as np
import pytest

from radio_pipeline.scattering.broaden import scatter_broaden

# 0.1 ms sampling over 25.6 ms. The kernel is capped at 10 * tau / dt = 100
# samples, so an impulse at sample 20 puts the last non-zero output at sample
# 119 — inside the 256-sample window, and nothing is trimmed.
TIME_MS = np.arange(256) * 0.1
TAU_MS = 1.0
IMPULSE_SAMPLE = 20
IMPULSE_AMPLITUDE = 100


def _impulse(dtype: np.dtype | type) -> np.ndarray:
    """A two-channel spectrum with one bright sample per channel."""
    spectrum = np.zeros((2, TIME_MS.size), dtype=dtype)
    spectrum[:, IMPULSE_SAMPLE] = IMPULSE_AMPLITUDE
    return spectrum


@pytest.mark.parametrize("dtype", [np.int16, np.int32, np.float32, np.float64])
def test_two_dimensional_broadening_conserves_flux_for_every_input_dtype(dtype) -> None:
    spectrum = _impulse(dtype)

    broadened = scatter_broaden(spectrum, TIME_MS, TAU_MS)

    assert broadened.dtype == np.float64
    assert broadened.shape == spectrum.shape
    # Flux is conserved exactly: the kernel is normalised to unit integral and
    # the impulse sits far enough from the end of the window that the trimmed
    # convolution keeps the whole tail, so the tolerance is rounding only.
    assert broadened.sum() == pytest.approx(float(spectrum.sum()), rel=1e-9)


def test_integer_input_is_not_truncated_toward_zero() -> None:
    """The pre-fix failure: int16 in, int16 out, ~21% of the flux discarded."""
    integer_spectrum = _impulse(np.int16)

    broadened = scatter_broaden(integer_spectrum, TIME_MS, TAU_MS)

    assert not np.issubdtype(broadened.dtype, np.integer)
    # Every sample of the decaying tail rounded down to an integer, so the
    # truncated total sat far below the input's.
    assert broadened.sum() > 0.9 * float(integer_spectrum.sum())


def test_one_and_two_dimensional_paths_agree_on_the_same_row() -> None:
    """A single row broadened alone matches the same row inside a 2D spectrum."""
    integer_spectrum = _impulse(np.int16)

    two_d = scatter_broaden(integer_spectrum, TIME_MS, TAU_MS)
    one_d = scatter_broaden(integer_spectrum[0], TIME_MS, TAU_MS)

    assert one_d.dtype == two_d.dtype
    np.testing.assert_allclose(two_d[0], one_d)


def test_zero_tau_returns_a_float_copy_of_an_integer_input() -> None:
    """tau <= 0 short-circuits to a copy; that copy must not stay integer."""
    integer_spectrum = _impulse(np.int16)

    unbroadened = scatter_broaden(integer_spectrum, TIME_MS, 0.0)

    assert unbroadened.dtype == np.float64
    np.testing.assert_allclose(unbroadened, integer_spectrum.astype(np.float64))
