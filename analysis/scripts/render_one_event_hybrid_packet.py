#!/usr/bin/env python3
"""Render one event's anchored-hybrid absolute-DM validation packet."""

from __future__ import annotations

import argparse
import json
import warnings
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch

from absolute_dm_voltage import sha256
from one_event_workflow import load_config

ROOT = Path(__file__).resolve().parents[1]
AUTHORITY_PATHS = (
    ROOT / "docs/rse/wayfinder/tickets/rfi-validation-01-define-acceptance-contract.md",
    ROOT / "docs/rse/control/BOARD.md",
    ROOT / "scripts/plot_codetection_data_grid.py",
    ROOT / "scripts/plot_codetection_triptych.py",
    ROOT / "scripts/plot_codetection_gallery.py",
)
TIMING_SLOPE_MS_PER_PC_CM3 = -24.157736787133153


def _load_product(path: str | Path) -> dict[str, np.ndarray]:
    with np.load(path) as product:
        return {key: product[key] for key in product.files}


def _resolve_product(result_path: Path, recorded_path: str) -> Path:
    path = Path(recorded_path)
    if path.is_file():
        return path
    local = result_path.parent / path.name
    if local.is_file():
        return local
    raise FileNotFoundError(f"cannot resolve product {recorded_path}")


def _normalised_rows(waterfall: np.ndarray) -> np.ndarray:
    values = np.asarray(waterfall, dtype=float)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        median = np.nanmedian(values, axis=1)
        mad = np.nanmedian(np.abs(values - median[:, None]), axis=1)
    sigma = 1.4826 * mad
    valid = np.isfinite(sigma) & (sigma > 0)
    output = np.full(values.shape, np.nan, dtype=float)
    output[valid] = (values[valid] - median[valid, None]) / sigma[valid, None]
    return output


def _block_mean(values: np.ndarray, maximum_rows: int, maximum_columns: int) -> np.ndarray:
    row_factor = max(1, int(np.ceil(values.shape[0] / maximum_rows)))
    column_factor = max(1, int(np.ceil(values.shape[1] / maximum_columns)))
    row_stop = values.shape[0] // row_factor * row_factor
    column_stop = values.shape[1] // column_factor * column_factor
    reshaped = values[:row_stop, :column_stop].reshape(
        row_stop // row_factor,
        row_factor,
        column_stop // column_factor,
        column_factor,
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        return np.nanmean(reshaped, axis=(1, 3))


def _show_spectrum(
    axis: plt.Axes,
    product: dict[str, np.ndarray],
    *,
    label: str,
) -> None:
    waterfall = np.asarray(product["waterfall"], dtype=float)
    frequency = np.asarray(product["frequency_mhz"], dtype=float)
    order = np.argsort(frequency)
    display = _block_mean(_normalised_rows(waterfall[order]), 512, 1000)
    sample_time_s = float(product["sample_time_s"])
    duration_ms = waterfall.shape[1] * sample_time_s * 1000.0
    axis.imshow(
        display,
        aspect="auto",
        origin="lower",
        interpolation="none",
        cmap="viridis",
        vmin=-1.0,
        vmax=7.0,
        extent=(
            -duration_ms / 2.0,
            duration_ms / 2.0,
            frequency.min(),
            frequency.max(),
        ),
        rasterized=True,
    )
    axis.text(
        0.02,
        0.96,
        label,
        transform=axis.transAxes,
        ha="left",
        va="top",
        fontsize=9,
        color="white",
        bbox={"facecolor": "black", "alpha": 0.55, "pad": 2, "edgecolor": "none"},
    )
    axis.set_xlabel("Time in fixed crop (ms)")


def _profile(product: dict[str, np.ndarray]) -> tuple[np.ndarray, np.ndarray]:
    waterfall = np.asarray(product["waterfall"], dtype=float)
    profile = np.nanmean(np.clip(_normalised_rows(waterfall), 0.0, None), axis=0)
    sample_time_s = float(product["sample_time_s"])
    time_ms = (
        np.arange(profile.size, dtype=float) - (profile.size - 1) / 2.0
    ) * sample_time_s * 1000.0
    scale = float(np.nanmax(profile))
    return time_ms, profile / scale


def _plot_profiles(
    axis: plt.Axes,
    products: dict[str, dict[str, np.ndarray]],
    labels: dict[str, str],
) -> None:
    for key, label in labels.items():
        time_ms, profile = _profile(products[key])
        axis.plot(time_ms, profile, label=label, linewidth=1.2)
    axis.set_xlabel("Time in fixed crop (ms)")
    axis.set_ylabel("Scaled positive profile")
    axis.set_ylim(-0.03, 1.08)
    axis.legend(frameon=False, fontsize=8)


def _plot_dsa_input_audit(axis: plt.Axes, audit: dict) -> None:
    matches = audit["row_match"]["matches"]
    row = np.asarray([item["row"] for item in matches], dtype=float)
    start = np.asarray(
        [item["best_start_sample"] for item in matches],
        dtype=float,
    )
    correlation = np.asarray(
        [item["correlation"] for item in matches],
        dtype=float,
    )
    crop_start = float(audit["row_match"]["median_start_sample"])
    axis.scatter(row, start - crop_start, s=10, color="#2563eb")
    axis.axhline(0.0, color="#111827", linewidth=0.8)
    axis.set_xlabel("DSA-110 frequency-row index")
    axis.set_ylabel("Best-start residual (samples)")
    axis.set_ylim(-0.55, 0.55)
    second = axis.twinx()
    second.scatter(row, correlation, s=8, color="#d97706", alpha=0.65)
    second.set_ylabel("Raw/reference correlation")
    second.set_ylim(0.0, 1.03)
    residual_dm = audit["dedispersion_state_fit"][
        "inferred_reference_minus_raw_dm_pc_cm3"
    ]
    direct = audit["frequency_order"]["direct_median_correlation"]
    reversed_order = audit["frequency_order"]["reversed_median_correlation"]
    selected_count = int(audit["row_match"]["selected_count"])
    start_sample = int(round(crop_start))
    axis.text(
        0.02,
        0.97,
        (
            f"{selected_count}/{selected_count} starts = {start_sample}\n"
            f"residual DM = {residual_dm:.2e}\n"
            f"direct/reversed = {direct:.3f}/{reversed_order:.3f}"
        ),
        transform=axis.transAxes,
        va="top",
        fontsize=8,
        bbox={
            "facecolor": "white",
            "alpha": 0.85,
            "pad": 2,
            "edgecolor": "none",
        },
    )
    axis.set_title("DSA-110 input-state oracle", fontsize=10)


def _display_only_invalid_count(product: dict[str, np.ndarray]) -> int:
    waterfall = np.asarray(product["waterfall"], dtype=float)
    accepted = np.asarray(product["accepted_live"], dtype=bool)
    finite_fraction = np.isfinite(waterfall).mean(axis=1)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        standard_deviation = np.nanstd(waterfall, axis=1)
    display_valid = (
        (finite_fraction >= 0.90)
        & np.isfinite(standard_deviation)
        & (standard_deviation > 0)
    )
    return int(np.sum(accepted & ~display_valid))


def _plot_support(
    axis: plt.Axes,
    chime: dict,
    *,
    display_only_invalid_count: int,
) -> None:
    missing = np.asarray(chime["support"]["h5_missing_ids"], dtype=int)
    present_dead = np.asarray(
        chime["support"]["h5_present_accepted_dead_ids"],
        dtype=int,
    )
    full_grid_rows = int(chime["support"]["full_grid_rows"])
    category = np.full(full_grid_rows, 2, dtype=int)
    category[present_dead] = 1
    category[missing] = 0
    axis.imshow(
        category[None, :],
        aspect="auto",
        interpolation="none",
        cmap=ListedColormap(["#6b7280", "#d97706", "#0f766e"]),
        vmin=-0.5,
        vmax=2.5,
        extent=(0, full_grid_rows, 0, 1),
    )
    axis.set_yticks([])
    axis.set_xlim(0, full_grid_rows)
    axis.set_xlabel("CHIME/FRB full-grid channel ID")
    axis.text(
        0.5,
        1.42,
        (
            f"{missing.size} source-missing  |  "
            f"{present_dead.size} accepted upstream-dead  |  "
            f"{chime['support']['accepted_live_count']} accepted live  |  "
            f"extra rows: {len(chime['support']['proposed_extra_bad_rows'])}  |  "
            f"fit-crop display-only invalid fine rows: {display_only_invalid_count}"
        ),
        transform=axis.transAxes,
        ha="center",
        va="bottom",
        fontsize=10,
    )
    axis.legend(
        handles=[
            Patch(facecolor="#6b7280", label="source-missing"),
            Patch(facecolor="#d97706", label="accepted upstream-dead"),
            Patch(facecolor="#0f766e", label="accepted live"),
        ],
        loc="lower center",
        bbox_to_anchor=(0.5, 1.02),
        ncol=3,
        frameon=False,
        fontsize=8,
    )


def _plot_hybrid_and_oracle(axis: plt.Axes, chime: dict) -> None:
    fine = chime["grid"]["fine"]
    fit = chime["grid"]["fit"]
    dm = np.asarray(
        [row["target_total_dm_pc_cm3"] for row in fine],
        dtype=float,
    )
    score = np.asarray(fit["selected_score"], dtype=float)
    axis.plot(
        dm,
        score / np.max(score),
        color="#2563eb",
        linewidth=1.5,
        label="anchored hybrid grid",
    )
    oracle = chime["full_coherent_oracle"]
    oracle_dm = np.asarray(oracle["dm_pc_cm3"], dtype=float)
    axis.scatter(
        oracle_dm,
        oracle["hybrid_normalised_score"],
        marker="o",
        color="#7c3aed",
        label="hybrid at oracle DMs",
        zorder=4,
    )
    axis.scatter(
        oracle_dm,
        oracle["fully_coherent_normalised_score"],
        marker="x",
        color="#dc2626",
        label="fully coherent H5 oracle",
        zorder=5,
    )
    axis.axvline(
        fit["dm_pc_cm3"],
        color="#111827",
        label=f"fit {fit['dm_pc_cm3']:.6f}",
    )
    axis.axvline(
        chime["geometry_dm_pc_cm3"],
        color="#059669",
        linestyle="--",
        label=f"geometry {chime['geometry_dm_pc_cm3']:.6f}",
    )
    axis.set_xlabel("Absolute total dispersion measure (pc cm$^{-3}$)")
    axis.set_ylabel("Normalized phase-coherence objective")
    axis.ticklabel_format(axis="x", style="plain", useOffset=False)
    axis.set_ylim(0.0, 1.08)
    axis.legend(frameon=False, fontsize=8, ncol=2)


def _plot_timing_residual(axis: plt.Axes, chime: dict) -> None:
    fit_dm = float(chime["grid"]["fit"]["dm_pc_cm3"])
    geometry_dm = float(chime["geometry_dm_pc_cm3"])
    fine_dm = np.asarray(
        [row["target_total_dm_pc_cm3"] for row in chime["grid"]["fine"]]
    )
    lower = min(float(np.min(fine_dm)), geometry_dm) - 0.005
    upper = max(float(np.max(fine_dm)), geometry_dm) + 0.005
    dm = np.linspace(lower, upper, 200)
    residual_ms = TIMING_SLOPE_MS_PER_PC_CM3 * (dm - geometry_dm)
    fit_residual_ms = TIMING_SLOPE_MS_PER_PC_CM3 * (fit_dm - geometry_dm)
    axis.plot(dm, residual_ms, color="#334155")
    axis.axhline(0.0, color="#111827", linewidth=0.8)
    axis.axvline(geometry_dm, color="#059669", linestyle="--")
    axis.scatter([fit_dm], [fit_residual_ms], color="#dc2626", zorder=3)
    axis.set_xlabel("Absolute total dispersion measure (pc cm$^{-3}$)")
    axis.set_ylabel("Timing-minus-geometry residual (ms)")
    axis.ticklabel_format(axis="x", style="plain", useOffset=False)
    axis.set_title("Geometry zero crossing", fontsize=10)
    axis.text(
        0.03,
        0.96,
        f"fit residual = {fit_residual_ms:+.4f} ms",
        transform=axis.transAxes,
        va="top",
        fontsize=9,
    )


def _plot_status(
    axis: plt.Axes,
    chime: dict,
    dsa: dict,
    provenance: dict,
) -> None:
    method = chime["hybrid_method"]
    smearing = method["smearing_bound"]
    injected = method["injected_absolute_dm_recovery"]
    oracle = chime["full_coherent_oracle"]
    control_hash = provenance.get(
        "event_binding_sha256",
        provenance.get("control_manifest_sha256", "unrecorded"),
    )
    container = provenance.get(
        "chime_container_image",
        provenance.get("container_image_id", "unrecorded"),
    )
    text = "\n".join(
        [
            "STATUS: one-event diagnostic; independent review pending",
            (
                f"CHIME anchor {method['anchor_dm_pc_cm3']:.6f}; "
                f"coherent anchor count {method['coherent_anchor_count']}; "
                f"oracle-only coherent count {method['oracle_only_fully_coherent_count']}"
            ),
            (
                "Identity: input 0 + coherent anchor + "
                "(trial - anchor) once = absolute trial"
            ),
            (
                f"U={method['upchannel_factor']}; "
                f"dt={method['upchannel_sample_time_s'] * 1e6:.2f} us; "
                f"400 MHz reference"
            ),
            (
                f"Residual coarse-channel smear "
                f"{smearing['maximum_smearing_s'] * 1e6:.2f} us = "
                f"{smearing['fraction_of_upchannel_sample']:.3f} sample; "
                f"gate {'PASS' if smearing['passed'] else 'FAIL'}"
            ),
            (
                f"Injected DM {injected['injected_absolute_dm_pc_cm3']:.6f} -> "
                f"{injected['recovered_absolute_dm_pc_cm3']:.6f}; "
                f"gate {'PASS' if injected['passed'] else 'FAIL'}"
            ),
            (
                f"Full-coherent curve max difference "
                f"{oracle['maximum_normalised_score_absolute_difference']:.3f}; "
                f"peak shift {oracle['absolute_peak_difference_pc_cm3']:.6f}; "
                f"gate {'PASS' if oracle['passed'] else 'FAIL'}"
            ),
            (
                f"DSA input {dsa['input_state']['raw_total_dm_pc_cm3']:.6f}; "
                "residual = target - input once; no edge clamp"
            ),
            (
                f"Event binding {control_hash[:12]}...; "
                f"container {container[:36]}..."
            ),
        ]
    )
    axis.axis("off")
    axis.text(
        0.0,
        1.0,
        text,
        va="top",
        ha="left",
        fontsize=9,
        family="monospace",
        linespacing=1.5,
    )


def render(
    *,
    config_path: Path,
    chime_result_path: Path,
    dsa_result_path: Path,
    dsa_audit_path: Path,
    run_provenance_path: Path,
    accepted_chime_reference: Path,
    accepted_dsa_reference: Path,
    output_svg: Path,
    output_png: Path,
    receipt_path: Path,
) -> dict:
    config = load_config(config_path)
    event = config["event"]
    chime = json.loads(chime_result_path.read_text())
    dsa = json.loads(dsa_result_path.read_text())
    dsa_audit = json.loads(dsa_audit_path.read_text())
    provenance = json.loads(run_provenance_path.read_text())
    expected_status = config["result_status"]
    if chime["status"] != expected_status or dsa["status"] != expected_status:
        raise RuntimeError("packet requires matching current hybrid results")
    if chime["burst"] != event or dsa["burst"] != event:
        raise ValueError("packet result events do not match configuration")
    binding = config["event_binding_sha256"]
    for label, value in (
        ("CHIME result", chime),
        ("DSA result", dsa),
        ("DSA audit", dsa_audit),
        ("run provenance", provenance),
    ):
        if value.get("event_binding_sha256") != binding:
            raise ValueError(f"{label} binding does not match configuration")
    if dsa_audit.get("event") != event:
        raise ValueError("packet DSA audit event does not match configuration")
    if sha256(accepted_chime_reference) != config["input_sha256"][
        "accepted_chime_reference"
    ]:
        raise RuntimeError("packet CHIME reference hash does not match configuration")
    if sha256(accepted_dsa_reference) != config["input_sha256"][
        "accepted_dsa_reference"
    ]:
        raise RuntimeError("packet DSA reference hash does not match configuration")
    if chime["support"]["proposed_extra_bad_rows"]:
        raise RuntimeError("packet cannot include an extra CHIME mask")
    if dsa["support"]["proposed_extra_bad_rows"]:
        raise RuntimeError("packet cannot include an extra DSA mask")
    if not chime["full_coherent_oracle"]["passed"]:
        raise RuntimeError("full-coherent oracle did not pass")
    if not chime["hybrid_method"]["smearing_bound"]["passed"]:
        raise RuntimeError("residual-smearing gate did not pass")

    chime_products = {
        key: _load_product(_resolve_product(chime_result_path, value["path"]))
        for key, value in chime["products"].items()
    }
    dsa_products = {
        key: _load_product(_resolve_product(dsa_result_path, value["path"]))
        for key, value in dsa["products"].items()
    }
    chime_display_invalid = _display_only_invalid_count(
        chime_products["hybrid_fit_dm"]
    )

    figure = plt.figure(figsize=(19, 15), constrained_layout=True)
    grid = figure.add_gridspec(
        4,
        4,
        height_ratios=(0.22, 1.45, 1.05, 0.95),
    )
    support_axis = figure.add_subplot(grid[0, :])
    _plot_support(
        support_axis,
        chime,
        display_only_invalid_count=chime_display_invalid,
    )

    spectra = [
        (
            chime_products["anchor_before_residual"],
            "CHIME/FRB coherent anchor before residual",
        ),
        (chime_products["hybrid_fit_dm"], "CHIME/FRB hybrid fit"),
        (dsa_products["anchor_dm"], "DSA-110 at CHIME anchor"),
        (dsa_products["hybrid_fit_dm"], "DSA-110 at CHIME hybrid fit"),
    ]
    for column, (product, label) in enumerate(spectra):
        axis = figure.add_subplot(grid[1, column])
        _show_spectrum(axis, product, label=label)
        if column in (0, 2):
            axis.set_ylabel("Frequency (MHz)")

    score_axis = figure.add_subplot(grid[2, :2])
    _plot_hybrid_and_oracle(score_axis, chime)
    timing_axis = figure.add_subplot(grid[2, 2])
    _plot_timing_residual(timing_axis, chime)
    audit_axis = figure.add_subplot(grid[2, 3])
    _plot_dsa_input_audit(audit_axis, dsa_audit)

    chime_profile_axis = figure.add_subplot(grid[3, 0])
    _plot_profiles(
        chime_profile_axis,
        chime_products,
        {
            "anchor_before_residual": "anchor",
            "hybrid_fit_dm": "hybrid fit",
            "geometry_dm": "geometry",
        },
    )
    chime_profile_axis.set_title("CHIME/FRB profiles", fontsize=10)
    dsa_profile_axis = figure.add_subplot(grid[3, 1])
    _plot_profiles(
        dsa_profile_axis,
        dsa_products,
        {
            "input_dm": (
                f"input {config['dsa']['accepted_reference_dm_pc_cm3']}"
            ),
            "anchor_dm": "CHIME anchor",
            "hybrid_fit_dm": "hybrid fit",
            "geometry_dm": "geometry",
        },
    )
    dsa_profile_axis.set_title("DSA-110 profiles", fontsize=10)
    status_axis = figure.add_subplot(grid[3, 2:])
    _plot_status(status_axis, chime, dsa, provenance)

    figure.suptitle(
        f"{event.capitalize()} anchored-hybrid absolute-dispersion-measure validation\n"
        "One event; no manuscript value adopted",
        fontsize=14,
    )
    output_svg.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_svg)
    figure.savefig(output_png, dpi=170)
    plt.close(figure)

    receipt = {
        "schema_version": 1,
        "status": expected_status,
        "burst": event,
        "event_binding_sha256": binding,
        "scope": "one event only",
        "accepted_chime_route": {
            "description": (
                "current Figure 1 archival-product route supplies accepted "
                "support only; no archival array is shifted in the hybrid fit"
            ),
            "sources": [
                {"path": str(path.relative_to(ROOT)), "sha256": sha256(path)}
                for path in AUTHORITY_PATHS
            ],
        },
        "inputs": {
            "workflow_config": {
                "path": str(config_path),
                "sha256": sha256(config_path),
                "event_binding_sha256": config["event_binding_sha256"],
            },
            "chime_result": {
                "path": str(chime_result_path),
                "sha256": sha256(chime_result_path),
            },
            "dsa_result": {
                "path": str(dsa_result_path),
                "sha256": sha256(dsa_result_path),
            },
            "dsa_input_state_audit": {
                "path": str(dsa_audit_path),
                "sha256": sha256(dsa_audit_path),
            },
            "run_provenance": {
                "path": str(run_provenance_path),
                "sha256": sha256(run_provenance_path),
            },
            "accepted_chime_reference": {
                "path": str(accepted_chime_reference),
                "sha256": sha256(accepted_chime_reference),
            },
            "accepted_dsa_reference": {
                "path": str(accepted_dsa_reference),
                "sha256": sha256(accepted_dsa_reference),
            },
        },
        "checks": {
            "chime_source_missing_count": chime["support"]["h5_missing_count"],
            "chime_present_accepted_dead_count": chime["support"][
                "h5_present_accepted_dead_count"
            ],
            "chime_accepted_live_count": chime["support"]["accepted_live_count"],
            "chime_proposed_extra_bad_rows": chime["support"][
                "proposed_extra_bad_rows"
            ],
            "chime_fit_crop_display_only_invalid_fine_rows": (
                chime_display_invalid
            ),
            "coherent_anchor_count": chime["hybrid_method"][
                "coherent_anchor_count"
            ],
            "full_coherent_oracle_passed": chime["full_coherent_oracle"][
                "passed"
            ],
            "full_coherent_oracle_peak_difference_pc_cm3": chime[
                "full_coherent_oracle"
            ]["absolute_peak_difference_pc_cm3"],
            "full_coherent_normalised_curve_max_abs_difference": chime[
                "full_coherent_oracle"
            ]["maximum_normalised_score_absolute_difference"],
            "full_coherent_center_score_ratio": chime[
                "full_coherent_oracle"
            ]["center_score_ratio_hybrid_over_fully_coherent"],
            "smearing_bound_passed": chime["hybrid_method"]["smearing_bound"][
                "passed"
            ],
            "smearing_fraction_of_upchannel_sample": chime["hybrid_method"][
                "smearing_bound"
            ]["fraction_of_upchannel_sample"],
            "smearing_fraction_of_reference_pulse_fwhm": chime[
                "hybrid_method"
            ]["smearing_bound"]["fraction_of_reference_pulse_fwhm"],
            "injected_recovery_passed": chime["hybrid_method"][
                "injected_absolute_dm_recovery"
            ]["passed"],
            "injected_recovery_absolute_error_pc_cm3": chime["hybrid_method"][
                "injected_absolute_dm_recovery"
            ]["absolute_error_pc_cm3"],
            "dsa_input_total_dm_pc_cm3": dsa["input_state"][
                "raw_total_dm_pc_cm3"
            ],
            "dsa_direct_frequency_order_median_correlation": dsa["input_state"][
                "direct_frequency_order_median_correlation"
            ],
            "dsa_reversed_frequency_order_median_correlation": dsa["input_state"][
                "reversed_frequency_order_median_correlation"
            ],
            "reference_frequency_mhz": dsa["dedispersion"][
                "reference_frequency_mhz"
            ],
            "hybrid_fit_dm_pc_cm3": chime["grid"]["fit"]["dm_pc_cm3"],
            "geometry_dm_pc_cm3": chime["geometry_dm_pc_cm3"],
        },
        "outputs": {
            "svg": {"path": str(output_svg), "sha256": sha256(output_svg)},
            "png": {"path": str(output_png), "sha256": sha256(output_png)},
        },
    }
    receipt_path.write_text(json.dumps(receipt, indent=2, allow_nan=False) + "\n")
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--chime-result", type=Path, required=True)
    parser.add_argument("--dsa-result", type=Path, required=True)
    parser.add_argument("--dsa-audit", type=Path, required=True)
    parser.add_argument("--run-provenance", type=Path, required=True)
    parser.add_argument("--accepted-chime-reference", type=Path, required=True)
    parser.add_argument("--accepted-dsa-reference", type=Path, required=True)
    parser.add_argument("--output-svg", type=Path, required=True)
    parser.add_argument("--output-png", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    render(
        config_path=args.config,
        chime_result_path=args.chime_result,
        dsa_result_path=args.dsa_result,
        dsa_audit_path=args.dsa_audit,
        run_provenance_path=args.run_provenance,
        accepted_chime_reference=args.accepted_chime_reference,
        accepted_dsa_reference=args.accepted_dsa_reference,
        output_svg=args.output_svg,
        output_png=args.output_png,
        receipt_path=args.receipt,
    )
    print(f"wrote one-event hybrid packet: {args.output_svg}", flush=True)


if __name__ == "__main__":
    main()
