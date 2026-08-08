#!/usr/bin/env python3
"""Propose reviewed component windows from two immutable observation products.

This diagnostic never edits an event configuration. It follows the explicit
component counts and association hypotheses in ``joint_fit.review_plan``, then
emits only a review proposal and a visual review sheet.
"""

from __future__ import annotations

import argparse
import bisect
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import matplotlib
import numpy as np
from scipy.signal import find_peaks

REPO_ROOT = str(Path(__file__).resolve().parents[1])
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from one_event_workflow import arrays_sha256, event_binding_sha256  # noqa: E402

from radio_pipeline.fitting import load_band_observation_product  # noqa: E402
from radio_pipeline.fitting.products import sha256_file  # noqa: E402

MINIMUM_PEAK_SIGNAL_TO_NOISE = 6.0
MINIMUM_OFF_PULSE_SAMPLES_PER_SIDE = 8
TAIL_BACKGROUND_THRESHOLD_SIGMA = 2.5
TAIL_BACKGROUND_FILTER_WIDTHS = 2


@dataclass(frozen=True, slots=True)
class BandProposal:
    instrument: str
    profile: np.ndarray
    peak_signal_to_noise: float
    matched_filter_width_samples: int
    core_start_sample: int
    core_stop_sample: int
    padding_samples: int
    envelope_start_sample: int
    envelope_stop_sample: int
    center_sample: float
    half_width_samples: float
    width_bounds_s: tuple[float, float]
    off_pulse_samples_left: int
    off_pulse_samples_right: int
    off_pulse_intervals_samples: tuple[tuple[int, int], ...]
    tail_background_start_sample: int
    tail_background_stop_sample: int
    tail_extension_applied: bool

    def compact(self, component_index: int) -> dict[str, object]:
        return {
            "instrument": self.instrument,
            "component_id": f"{self.instrument}_c{component_index}",
            "peak_signal_to_noise": self.peak_signal_to_noise,
            "matched_filter_width_samples": self.matched_filter_width_samples,
            "signal_core_samples": [self.core_start_sample, self.core_stop_sample],
            "padding_samples": self.padding_samples,
            "on_pulse_envelope_samples": [
                self.envelope_start_sample,
                self.envelope_stop_sample,
            ],
            "center_sample": self.center_sample,
            "half_width_samples": self.half_width_samples,
            "width_bounds_s": list(self.width_bounds_s),
            "off_pulse_samples": {
                "left": self.off_pulse_samples_left,
                "right": self.off_pulse_samples_right,
            },
            "off_pulse_intervals_samples": [
                list(interval) for interval in self.off_pulse_intervals_samples
            ],
            "tail_background_check": {
                "threshold_sigma": TAIL_BACKGROUND_THRESHOLD_SIGMA,
                "consecutive_samples": (
                    self.tail_background_stop_sample
                    - self.tail_background_start_sample
                ),
                "background_consistent_samples": [
                    self.tail_background_start_sample,
                    self.tail_background_stop_sample,
                ],
                "envelope_extended": self.tail_extension_applied,
            },
        }


def _true_intervals(mask: np.ndarray) -> tuple[tuple[int, int], ...]:
    edges = np.diff(np.pad(np.asarray(mask, dtype=np.int8), (1, 1)))
    starts = np.flatnonzero(edges == 1)
    stops = np.flatnonzero(edges == -1)
    return tuple(
        (int(start), int(stop)) for start, stop in zip(starts, stops, strict=True)
    )


def _profile_and_off_pulse(product_path: Path) -> tuple[object, np.ndarray, np.ndarray]:
    observation = load_band_observation_product(product_path)
    with np.load(product_path, allow_pickle=False) as archive:
        noise_mask = np.asarray(archive["noise_estimation_mask"], dtype=bool)
    standardized = np.full_like(observation.waterfall, np.nan, dtype=float)
    np.divide(
        observation.waterfall,
        observation.noise_std,
        out=standardized,
        where=observation.valid,
    )
    valid_count = observation.valid.sum(axis=0)
    if np.any(valid_count <= 0):
        raise ValueError(f"{observation.instrument} has time samples without valid support")
    # Median combination prevents one surviving interference row from setting
    # the component window. The square-root factor retains the scale expected
    # for a coherent broadband signal; the off-pulse samples calibrate it.
    profile = np.nanmedian(standardized, axis=0) * np.sqrt(valid_count)
    off_pulse_columns = noise_mask.sum(axis=0) >= max(
        1,
        observation.waterfall.shape[0] // 4,
    )
    if int(off_pulse_columns.sum()) < 2 * MINIMUM_OFF_PULSE_SAMPLES_PER_SIDE:
        raise ValueError(f"{observation.instrument} has inadequate off-pulse support")
    baseline = float(np.median(profile[off_pulse_columns]))
    scale = float(
        1.4826 * np.median(np.abs(profile[off_pulse_columns] - baseline))
    )
    if not np.isfinite(scale) or scale <= 0:
        raise ValueError(f"{observation.instrument} has invalid profile noise")
    return observation, (profile - baseline) / scale, off_pulse_columns


def _candidate_widths(sample_count: int) -> tuple[int, ...]:
    maximum = max(1, sample_count // 8)
    widths = {1, maximum}
    width = 2
    while width < maximum:
        widths.add(width)
        width *= 2
    return tuple(sorted(widths))


def _proposal_for_peak(
    observation,
    profile: np.ndarray,
    off_pulse_columns: np.ndarray,
    *,
    filtered: np.ndarray,
    width: int,
    peak: int,
    peak_signal_to_noise: float,
) -> BandProposal:
    threshold = max(2.5, 0.20 * peak_signal_to_noise)
    left = peak
    right = peak + 1
    while left > 0 and filtered[left - 1] >= threshold:
        left -= 1
    while right < profile.size and filtered[right] >= threshold:
        right += 1
    # A narrow or noisy threshold crossing must still contain the selected
    # matched-filter support.
    core_start = min(left, max(0, peak - width))
    core_stop = max(right, min(profile.size, peak + width + 1))
    padding = max(4, 2 * width)
    envelope_start = core_start - padding
    envelope_stop = core_stop + padding

    tail_profile = filtered / np.sqrt(width)
    tail_run_samples = TAIL_BACKGROUND_FILTER_WIDTHS * width
    tail_background_start = None
    for start in range(core_stop, profile.size - tail_run_samples + 1):
        if np.all(
            np.abs(tail_profile[start : start + tail_run_samples])
            <= TAIL_BACKGROUND_THRESHOLD_SIGMA
        ):
            tail_background_start = start
            break
    if tail_background_start is None:
        raise ValueError(
            f"{observation.instrument} post-peak tail never reaches background"
        )
    tail_background_stop = tail_background_start + tail_run_samples
    tail_extension_applied = envelope_stop < tail_background_start
    if tail_extension_applied:
        envelope_stop = tail_background_stop
    if envelope_start <= 0 or envelope_stop >= profile.size:
        raise ValueError(f"{observation.instrument} proposed envelope contacts crop edge")

    left_off_pulse = int(off_pulse_columns[:envelope_start].sum())
    right_off_pulse = int(off_pulse_columns[envelope_stop:].sum())
    if min(left_off_pulse, right_off_pulse) < MINIMUM_OFF_PULSE_SAMPLES_PER_SIDE:
        raise ValueError(f"{observation.instrument} has inadequate two-sided off-pulse support")

    center = 0.5 * (envelope_start + envelope_stop - 1)
    half_width = 0.5 * (envelope_stop - envelope_start)
    characteristic_width_s = max(width, core_stop - core_start) * observation.sample_interval_s
    width_low = max(observation.sample_interval_s, characteristic_width_s / 4.0)
    width_high = min(
        half_width * observation.sample_interval_s,
        4.0 * characteristic_width_s,
    )
    if not width_low < width_high:
        raise ValueError(f"{observation.instrument} cannot support broad width bounds")

    return BandProposal(
        instrument=observation.instrument,
        profile=profile,
        peak_signal_to_noise=peak_signal_to_noise,
        matched_filter_width_samples=width,
        core_start_sample=core_start,
        core_stop_sample=core_stop,
        padding_samples=padding,
        envelope_start_sample=envelope_start,
        envelope_stop_sample=envelope_stop,
        center_sample=center,
        half_width_samples=half_width,
        width_bounds_s=(width_low, width_high),
        off_pulse_samples_left=left_off_pulse,
        off_pulse_samples_right=right_off_pulse,
        off_pulse_intervals_samples=_true_intervals(off_pulse_columns),
        tail_background_start_sample=tail_background_start,
        tail_background_stop_sample=tail_background_stop,
        tail_extension_applied=tail_extension_applied,
    )


def _select_separated(
    candidates: list[BandProposal],
    count: int,
    instrument: str,
) -> list[BandProposal]:
    # Expand the signal core by one selected filter width. This prevents
    # multiple filter scales or noise sub-peaks within one physical component
    # from satisfying a requested multi-component plan.
    ordered = sorted(
        candidates,
        key=lambda row: row.core_stop_sample + row.matched_filter_width_samples,
    )
    stops = [
        row.core_stop_sample + row.matched_filter_width_samples for row in ordered
    ]
    previous = [
        bisect.bisect_right(
            stops,
            row.core_start_sample - row.matched_filter_width_samples,
            hi=index,
        )
        - 1
        for index, row in enumerate(ordered)
    ]
    negative = float("-inf")
    score = np.full((count + 1, len(ordered) + 1), negative, dtype=float)
    score[0, :] = 0.0
    take = np.zeros(score.shape, dtype=bool)
    for selected in range(1, count + 1):
        for end in range(1, len(ordered) + 1):
            without = score[selected, end - 1]
            row = ordered[end - 1]
            prior = score[selected - 1, previous[end - 1] + 1]
            with_row = prior + row.peak_signal_to_noise
            if with_row > without:
                score[selected, end] = with_row
                take[selected, end] = True
            else:
                score[selected, end] = without
    if not np.isfinite(score[count, len(ordered)]):
        raise ValueError(
            f"{instrument} cannot separate requested component_count={count}"
        )
    selected_rows: list[BandProposal] = []
    selected = count
    end = len(ordered)
    while selected:
        if not take[selected, end]:
            end -= 1
            continue
        row = ordered[end - 1]
        selected_rows.append(row)
        end = previous[end - 1] + 1
        selected -= 1
    return sorted(selected_rows, key=lambda row: row.center_sample)


def propose_band(
    product_path: Path,
    component_count: int,
) -> tuple[object, list[BandProposal]]:
    if isinstance(component_count, bool) or not isinstance(component_count, int):
        raise ValueError("component_count must be an integer")
    if not 1 <= component_count <= 8:
        raise ValueError("component_count must be between one and eight")
    observation, profile, off_pulse_columns = _profile_and_off_pulse(product_path)
    candidates: list[BandProposal] = []
    rejected: list[str] = []
    for width in _candidate_widths(profile.size):
        kernel = np.ones(width, dtype=float) / np.sqrt(width)
        filtered = np.convolve(profile, kernel, mode="same")
        peaks, properties = find_peaks(
            filtered,
            height=MINIMUM_PEAK_SIGNAL_TO_NOISE,
            prominence=1.0,
            distance=max(2, width // 2),
        )
        ranked = sorted(
            zip(peaks, properties["peak_heights"], strict=True),
            key=lambda row: float(row[1]),
            reverse=True,
        )[:12]
        for peak, peak_signal_to_noise in ranked:
            try:
                candidates.append(
                    _proposal_for_peak(
                        observation,
                        profile,
                        off_pulse_columns,
                        filtered=filtered,
                        width=width,
                        peak=int(peak),
                        peak_signal_to_noise=float(peak_signal_to_noise),
                    )
                )
            except ValueError as error:
                rejected.append(str(error))
                continue
    if not candidates:
        for failure_kind in (
            "contacts crop edge",
            "inadequate two-sided off-pulse support",
        ):
            specific_failure = next(
                (message for message in rejected if failure_kind in message),
                None,
            )
            if specific_failure is not None:
                raise ValueError(specific_failure)
        raise ValueError(
            f"{observation.instrument} has no separated peak above "
            f"signal-to-noise {MINIMUM_PEAK_SIGNAL_TO_NOISE:.1f}"
        )
    return observation, _select_separated(
        candidates,
        component_count,
        observation.instrument,
    )


def _expected_input_hashes(config: dict, instrument: str) -> dict[str, str]:
    hashes = config["input_sha256"]
    if instrument == "chime":
        return {
            "raw_chime_h5": hashes["raw_chime_h5"],
            "accepted_chime_reference": hashes["accepted_chime_reference"],
        }
    return {
        "raw_dsa_filterbank": hashes["raw_dsa_filterbank"],
        "accepted_dsa_reference": hashes["accepted_dsa_reference"],
    }


def _render(
    observations: dict[str, object],
    proposals: dict[str, list[BandProposal]],
    output: Path,
) -> None:
    if output.suffix.lower() != ".pdf":
        raise ValueError("proposal review sheet must use the .pdf extension")
    figure, axes = plt.subplots(2, 2, figsize=(10.0, 7.0), constrained_layout=True)
    for column, instrument in enumerate(("chime", "dsa")):
        observation = observations[instrument]
        time_ms = observation.time_s * 1.0e3
        masked = np.ma.masked_where(~observation.valid, observation.waterfall)
        finite = masked.compressed()
        limit = float(np.nanpercentile(np.abs(finite), 99.0))
        time_step_ms = observation.sample_interval_s * 1.0e3
        frequency_steps = np.diff(observation.frequency_mhz)
        if not (np.all(frequency_steps > 0) or np.all(frequency_steps < 0)):
            raise ValueError(f"{instrument} frequency centers are not ordered")
        frequency_direction = float(np.sign(frequency_steps[0]))
        axes[0, column].imshow(
            masked,
            aspect="auto",
            origin="lower",
            extent=(
                float(time_ms[0] - 0.5 * time_step_ms),
                float(time_ms[-1] + 0.5 * time_step_ms),
                float(
                    observation.frequency_mhz[0]
                    - 0.5 * frequency_direction * observation.channel_width_mhz[0]
                ),
                float(
                    observation.frequency_mhz[-1]
                    + 0.5 * frequency_direction * observation.channel_width_mhz[-1]
                ),
            ),
            cmap="RdBu_r",
            vmin=-limit,
            vmax=limit,
            interpolation="none",
        )
        axes[0, column].set_ylabel(
            f"{instrument.upper()}\nfrequency (MHz)\n"
            f"dt={observation.sample_interval_s * 1.0e6:.2f} us"
        )
        axes[0, column].set_xlabel("time from crop start (ms)")
        axes[1, column].plot(
            time_ms,
            proposals[instrument][0].profile,
            color="black",
            linewidth=0.8,
        )
        background_intervals = proposals[instrument][0].off_pulse_intervals_samples
        for interval_index, (start, stop) in enumerate(background_intervals):
            if interval_index == 0:
                label = "pre-burst background"
            elif interval_index == len(background_intervals) - 1:
                label = "post-burst background"
            else:
                label = "background"
            for axis, alpha in ((axes[0, column], 0.08), (axes[1, column], 0.12)):
                axis.axvspan(
                    (start - 0.5) * time_step_ms,
                    (stop - 0.5) * time_step_ms,
                    color="tab:green",
                    alpha=alpha,
                    label=label if axis is axes[1, column] else None,
                )
        for component_index, proposal in enumerate(proposals[instrument], start=1):
            label_suffix = f" {component_index}" if len(proposals[instrument]) > 1 else ""
            for axis, envelope_alpha, core_alpha in (
                (axes[0, column], 0.12, 0.18),
                (axes[1, column], 0.15, 0.25),
            ):
                axis.axvspan(
                    (proposal.envelope_start_sample - 0.5) * time_step_ms,
                    (proposal.envelope_stop_sample - 0.5) * time_step_ms,
                    color="tab:blue",
                    alpha=envelope_alpha,
                    label=(
                        f"padded envelope{label_suffix}"
                        if axis is axes[1, column]
                        else None
                    ),
                )
                axis.axvspan(
                    (proposal.core_start_sample - 0.5) * time_step_ms,
                    (proposal.core_stop_sample - 0.5) * time_step_ms,
                    color="tab:orange",
                    alpha=core_alpha,
                    label=(
                        f"signal core{label_suffix}"
                        if axis is axes[1, column]
                        else None
                    ),
                )
        axes[1, column].axhline(0.0, color="0.6", linewidth=0.6)
        axes[1, column].set_xlabel("time from crop start (ms)")
        axes[1, column].set_ylabel("robust profile signal-to-noise")
        axes[1, column].legend(frameon=False, fontsize=8)
    figure.savefig(output, format="pdf")
    plt.close(figure)


def _validate_review_plan(config: dict) -> dict[str, object]:
    try:
        plan = config["joint_fit"]["review_plan"]
        counts = plan["component_count"]
        associations = plan["association_hypotheses"]
    except (KeyError, TypeError) as error:
        raise ValueError("configuration lacks a complete joint_fit.review_plan") from error
    if not isinstance(plan, dict) or not isinstance(counts, dict):
        raise ValueError("joint_fit.review_plan must be an object")
    if set(counts) != {"chime", "dsa"}:
        raise ValueError("review plan must give CHIME/FRB and DSA-110 component counts")
    for instrument in ("chime", "dsa"):
        count = counts[instrument]
        if isinstance(count, bool) or not isinstance(count, int) or not 1 <= count <= 8:
            raise ValueError(f"{instrument} component_count must be an integer from one to eight")
    if not isinstance(associations, list) or not associations:
        raise ValueError("review plan requires explicit association hypotheses")
    known = {
        instrument: {
            f"{instrument}_c{index}" for index in range(1, counts[instrument] + 1)
        }
        for instrument in ("chime", "dsa")
    }
    names: set[str] = set()
    for hypothesis in associations:
        if not isinstance(hypothesis, dict):
            raise ValueError("association hypotheses must be objects")
        name = hypothesis.get("name")
        matches = hypothesis.get("matches")
        if not isinstance(name, str) or not name or name in names:
            raise ValueError("association hypothesis names must be unique and non-empty")
        names.add(name)
        if not isinstance(matches, list) or not matches:
            raise ValueError(f"association {name} requires at least one explicit match")
        chime_indices: list[int] = []
        dsa_indices: list[int] = []
        latent_ids: set[str] = set()
        for match in matches:
            if not isinstance(match, dict):
                raise ValueError(f"association {name} matches must be objects")
            chime_id = match.get("chime_component_id")
            dsa_id = match.get("dsa_component_id")
            latent_id = match.get("latent_id")
            if chime_id not in known["chime"] or dsa_id not in known["dsa"]:
                raise ValueError(f"association {name} references an unknown component")
            if not isinstance(latent_id, str) or not latent_id or latent_id in latent_ids:
                raise ValueError(f"association {name} has invalid latent component identifiers")
            latent_ids.add(latent_id)
            chime_indices.append(int(chime_id.rsplit("c", 1)[1]))
            dsa_indices.append(int(dsa_id.rsplit("c", 1)[1]))
        if len(set(chime_indices)) != len(chime_indices) or len(set(dsa_indices)) != len(
            dsa_indices
        ):
            raise ValueError(f"association {name} reuses an instrument component")
        ordered_pairs = sorted(zip(chime_indices, dsa_indices, strict=True))
        if any(
            right[1] <= left[1]
            for left, right in zip(ordered_pairs, ordered_pairs[1:], strict=False)
        ):
            raise ValueError(f"association {name} is not order-preserving")
    return plan


def run(
    *,
    config_path: Path,
    event: str,
    chime_path: Path,
    dsa_path: Path,
    output_json: Path,
    output_pdf: Path,
) -> dict[str, object]:
    if output_json.suffix.lower() != ".json":
        raise ValueError("proposal output must use the .json extension")
    config = json.loads(config_path.read_text())
    if config.get("event") != event or config.get("identity", {}).get("reviewed_event") != event:
        raise ValueError("requested event differs from configuration identity")
    if config.get("event_binding_sha256") != event_binding_sha256(config):
        raise ValueError("configuration event binding changed")
    review_plan = _validate_review_plan(config)

    observations: dict[str, object] = {}
    proposals: dict[str, list[BandProposal]] = {}
    for instrument, path in (("chime", chime_path), ("dsa", dsa_path)):
        observation, band_proposals = propose_band(
            path,
            review_plan["component_count"][instrument],
        )
        if observation.instrument != instrument:
            raise ValueError(f"{instrument} product has wrong instrument identity")
        if observation.input_sha256 != _expected_input_hashes(config, instrument):
            raise ValueError(f"{instrument} observation input identity changed")
        observations[instrument] = observation
        proposals[instrument] = band_proposals

    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    _render(observations, proposals, output_pdf)
    payload: dict[str, object] = {
        "schema_version": 1,
        "status": "proposal_pending_owner_review",
        "approved": False,
        "event": event,
        "event_binding_sha256": config["event_binding_sha256"],
        "review_plan": review_plan,
        "native_grids_preserved": True,
        "observation_contracts": {
            instrument: {
                "shape": list(observations[instrument].waterfall.shape),
                "sample_interval_s": observations[instrument].sample_interval_s,
                "frequency_grid_sha256": arrays_sha256(
                    observations[instrument].frequency_mhz,
                    observations[instrument].channel_width_mhz,
                ),
                "valid_mask_sha256": arrays_sha256(observations[instrument].valid),
            }
            for instrument in ("chime", "dsa")
        },
        "inputs": {
            "config": sha256_file(config_path),
            "chime_observation": sha256_file(chime_path),
            "dsa_observation": sha256_file(dsa_path),
        },
        "components": [
            proposal.compact(component_index)
            for instrument in ("chime", "dsa")
            for component_index, proposal in enumerate(proposals[instrument], start=1)
        ],
        "association_hypotheses": review_plan["association_hypotheses"],
        "review_sheet": {
            "path": str(output_pdf),
            "sha256": sha256_file(output_pdf),
        },
    }
    output_json.write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--event", required=True)
    parser.add_argument("--chime-observation", type=Path, required=True)
    parser.add_argument("--dsa-observation", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-pdf", type=Path, required=True)
    args = parser.parse_args()
    result = run(
        config_path=args.config,
        event=args.event,
        chime_path=args.chime_observation,
        dsa_path=args.dsa_observation,
        output_json=args.output_json,
        output_pdf=args.output_pdf,
    )
    print(json.dumps({"status": result["status"], "event": result["event"]}))


if __name__ == "__main__":
    main()
