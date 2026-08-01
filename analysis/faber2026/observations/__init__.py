"""Immutable observations consumed by maintained scientific models."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

import numpy as np
from astropy.time import Time
from numpy.typing import NDArray

_DM_TOLERANCE = 1e-9


@dataclass(frozen=True, slots=True)
class DispersionState:
    """Physical dispersion represented by a derived intensity product."""

    voltage_dm: float
    coherent_delta_dm: float
    residual_delta_dm: float
    product_dm: float
    time_origin_correction_s: float

    def validate(self) -> None:
        represented = self.voltage_dm + self.coherent_delta_dm + self.residual_delta_dm
        if not np.isclose(represented, self.product_dm, rtol=0.0, atol=_DM_TOLERANCE):
            raise ValueError(
                "exactly-once dispersion requires voltage DM + coherent correction "
                "+ residual correction = product DM"
            )
        if not np.isfinite(self.time_origin_correction_s):
            raise ValueError("dispersion time-origin correction must be finite")


@dataclass(frozen=True, slots=True)
class BandObservation:
    """One instrument's measurements on its own time-frequency grid."""

    instrument: str
    intensity: NDArray[np.floating]
    valid_pixels: NDArray[np.bool_]
    frequencies_mhz: NDArray[np.floating]
    channel_widths_mhz: NDArray[np.floating]
    times_s: NDArray[np.floating]
    sample_interval_s: float
    time_origin_utc: str
    time_origin_unix_ns: int
    frequency_frame: str
    dispersion: DispersionState
    noise_std: NDArray[np.floating]
    gain_prior_std: float
    input_hashes: Mapping[str, str]

    def validate(self) -> None:
        intensity = np.asarray(self.intensity)
        valid = np.asarray(self.valid_pixels)
        frequencies = np.asarray(self.frequencies_mhz)
        widths = np.asarray(self.channel_widths_mhz)
        times = np.asarray(self.times_s)
        noise = np.asarray(self.noise_std)
        if self.instrument not in {"chimefrb", "dsa110"}:
            raise ValueError(f"unsupported instrument: {self.instrument}")
        if intensity.ndim != 2 or valid.shape != intensity.shape:
            raise ValueError("intensity and valid-pixel mask must share a frequency-time grid")
        if frequencies.shape != (intensity.shape[0],):
            raise ValueError("one authoritative frequency center is required per row")
        if widths.shape != frequencies.shape or np.any(widths <= 0):
            raise ValueError("one positive channel width is required per row")
        if times.shape != (intensity.shape[1],) or np.any(np.diff(times) <= 0):
            raise ValueError("time coordinates must be strictly increasing")
        if not np.isclose(
            np.diff(times).mean(), self.sample_interval_s, rtol=1e-10, atol=1e-15
        ):
            raise ValueError("sample interval disagrees with time coordinates")
        if noise.shape != frequencies.shape or np.any(noise <= 0):
            raise ValueError("one positive noise estimate is required per row")
        if self.gain_prior_std <= 0:
            raise ValueError("gain prior width must be positive")
        if not np.any(valid):
            raise ValueError("observation has no valid pixels")
        if np.any(~np.isfinite(intensity[valid])):
            raise ValueError("valid intensity pixels must be finite")
        if np.any(~np.isfinite(frequencies)) or np.any(frequencies <= 0):
            raise ValueError("frequency centers must be finite and positive")
        if (
            not self.time_origin_utc
            or not isinstance(self.time_origin_unix_ns, int)
            or not self.frequency_frame
            or not self.input_hashes
        ):
            raise ValueError("time, frequency, and input identities are required")
        parsed_origin_ns = np.longdouble(
            Time(self.time_origin_utc, scale="utc").to_value("unix", "long")
        ) * np.longdouble(1e9)
        if abs(parsed_origin_ns - self.time_origin_unix_ns) > 0.5:
            raise ValueError("UTC string and integer-nanosecond origin disagree")
        self.dispersion.validate()


__all__ = ["BandObservation", "DispersionState"]
