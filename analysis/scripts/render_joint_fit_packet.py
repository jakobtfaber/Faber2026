#!/usr/bin/env python3
"""Render the owner-review packet for one provisional joint fit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from radio_pipeline.fitting import load_band_observation_product
from radio_pipeline.fitting.products import sha256_file


def _frequency_edges(observation) -> tuple[np.ndarray, np.ndarray]:
    centers = np.asarray(observation.frequency_mhz, dtype=float)
    widths = np.asarray(observation.channel_width_mhz, dtype=float)
    order = np.argsort(centers)
    centers = centers[order]
    widths = widths[order]
    lower = centers - 0.5 * widths
    upper = centers + 0.5 * widths
    tolerance = max(float(np.max(widths)) * 1.0e-9, 1.0e-12)
    if np.any(np.diff(centers) <= 0):
        raise ValueError("frequency centers must be unique")
    edges = [float(lower[0])]
    row_indices = []
    for index in range(centers.size):
        if index:
            if lower[index] < upper[index - 1] - tolerance:
                raise ValueError("frequency channels overlap")
            if lower[index] > upper[index - 1] + tolerance:
                row_indices.append(-1)
                edges.append(float(lower[index]))
        row_indices.append(int(order[index]))
        edges.append(float(upper[index]))
    return np.asarray(edges), np.asarray(row_indices)


def _image(ax, values, observation, label: str) -> None:
    masked = np.ma.masked_where(~observation.valid, values)
    finite = masked.compressed()
    limit = np.nanpercentile(np.abs(finite), 99.0)
    frequency_edges, row_indices = _frequency_edges(observation)
    plotted = np.ma.masked_all(
        (row_indices.size, observation.waterfall.shape[1]),
        dtype=masked.dtype,
    )
    populated = row_indices >= 0
    plotted[populated] = masked[row_indices[populated]]
    time_edges_ms = (
        np.arange(observation.waterfall.shape[1] + 1)
        * observation.sample_interval_s
        * 1.0e3
    )
    ax.pcolormesh(
        time_edges_ms,
        frequency_edges,
        plotted,
        shading="flat",
        cmap="RdBu_r",
        vmin=-limit,
        vmax=limit,
        rasterized=True,
    )
    ax.set_ylabel(
        f"{label}\nfrequency (MHz)\n"
        f"dt={observation.sample_interval_s * 1e6:.2f} us, "
        f"df={np.median(observation.channel_width_mhz):.4f} MHz"
    )


def render(
    *,
    chime_path: Path,
    dsa_path: Path,
    chime_posterior_path: Path,
    dsa_posterior_path: Path,
    fit_result_path: Path,
    posterior_path: Path,
    model_path: Path,
    geometry_path: Path,
    oracle_path: Path,
    output: Path,
) -> None:
    if output.suffix.lower() != ".pdf":
        raise ValueError("review packet output must use the .pdf extension")
    observations = {
        item.instrument: item
        for item in (
            load_band_observation_product(chime_path),
            load_band_observation_product(dsa_path),
        )
    }
    posterior_observations = {
        item.instrument: item
        for item in (
            load_band_observation_product(chime_posterior_path),
            load_band_observation_product(dsa_posterior_path),
        )
    }
    fit = json.loads(fit_result_path.read_text())
    geometry = json.loads(geometry_path.read_text())
    oracle = json.loads(oracle_path.read_text())
    if oracle["status"] != "passed_pending_owner_visual_approval":
        raise RuntimeError("physical oracle verification has not passed")
    consumed = {
        "fit_result": fit_result_path,
        "posterior": posterior_path,
        "model_products": model_path,
        "geometry_constraint": geometry_path,
        "chime_fit_observation": chime_path,
        "dsa_fit_observation": dsa_path,
        "chime_posterior_observation": chime_posterior_path,
        "dsa_posterior_observation": dsa_posterior_path,
    }
    expected = oracle.get("consumed_inputs", {})
    for name, path in consumed.items():
        if expected.get(name) != sha256_file(path):
            raise RuntimeError(f"review packet input hash changed: {name}")
    with (
        np.load(model_path, allow_pickle=False) as models,
        np.load(posterior_path, allow_pickle=False) as posterior,
    ):
        figure, axes = plt.subplots(5, 2, figsize=(11.0, 15.0), constrained_layout=True)
        for column, instrument in enumerate(("chime", "dsa")):
            observation = observations[instrument]
            _image(
                axes[0, column],
                posterior_observations[instrument].waterfall,
                posterior_observations[instrument],
                f"{instrument.upper()} posterior-median DM",
            )
            _image(
                axes[1, column],
                observation.waterfall,
                observation,
                f"{instrument.upper()} fit-coordinate data",
            )
            _image(
                axes[2, column],
                models[f"{instrument}_model"],
                observation,
                f"{instrument.upper()} model",
            )
            _image(
                axes[3, column],
                models[f"{instrument}_residual"],
                observation,
                f"{instrument.upper()} residual",
            )
            axes[3, column].set_xlabel("time from locked crop start (ms)")

        dm_values = []
        dm_weights = []
        timing_residual_ms = []
        run_weights = np.asarray(posterior["run_weights"], dtype=float)
        for index, run_weight in enumerate(run_weights):
            names = list(posterior[f"run_{index}_parameter_names"])
            dm_index = names.index("absolute_dm_pc_cm3")
            dm_values.append(posterior[f"run_{index}_samples"][:, dm_index])
            dm_weights.append(posterior[f"run_{index}_sample_weights"] * run_weight)
            samples = posterior[f"run_{index}_samples"]
            timing_residual_ms.append(
                1.0e3
                * (
                    samples[:, names.index("timing_error_chime_s")]
                    - samples[:, names.index("timing_error_dsa_s")]
                )
            )
        axes[4, 0].hist(
            np.concatenate(dm_values),
            bins=60,
            weights=np.concatenate(dm_weights),
            histtype="step",
            color="black",
        )
        axes[4, 0].set_xlabel(r"shared absolute DM (pc cm$^{-3}$)")
        axes[4, 0].set_ylabel("posterior density")

        for values, residual in zip(dm_values, timing_residual_ms, strict=True):
            axes[4, 1].scatter(values, residual, s=2, alpha=0.15)
        axes[4, 1].axhline(0.0, color="black", linewidth=0.8)
        axes[4, 1].set_xlabel(r"shared absolute DM (pc cm$^{-3}$)")
        axes[4, 1].set_ylabel("CHIME/FRB − DSA-110 timing residual (ms)")
        diagnostic = fit["diagnostics"]
        weight_text = ", ".join(
            f"{name}={weight:.2f}" for name, weight in diagnostic["run_weights"].items()
        )
        figure.text(
            0.01,
            0.002,
            (
                f"{fit['status']}; 400 MHz; native grids; "
                f"geometry oracle {geometry['projection_disagreement_s'] * 1e9:.2f} ns; "
                f"DM edge={diagnostic['posterior_dm_at_edge']}; "
                f"model adequate={diagnostic['model_adequate']}; "
                "fully coherent CHIME/FRB and exactly-once DSA-110 "
                "posterior brackets passed; "
                f"{weight_text}. ToA is the unscattered geocentric center. "
                "Owner approval required."
            ),
            fontsize=7,
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(
        output,
        format="pdf",
        metadata={"CreationDate": None, "ModDate": None},
    )
    plt.close(figure)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--chime-observation", type=Path, required=True)
    parser.add_argument("--dsa-observation", type=Path, required=True)
    parser.add_argument("--chime-posterior-observation", type=Path, required=True)
    parser.add_argument("--dsa-posterior-observation", type=Path, required=True)
    parser.add_argument("--fit-result", type=Path, required=True)
    parser.add_argument("--posterior", type=Path, required=True)
    parser.add_argument("--model-products", type=Path, required=True)
    parser.add_argument("--geometry-constraint", type=Path, required=True)
    parser.add_argument("--oracle-verification", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    render(
        chime_path=args.chime_observation,
        dsa_path=args.dsa_observation,
        chime_posterior_path=args.chime_posterior_observation,
        dsa_posterior_path=args.dsa_posterior_observation,
        fit_result_path=args.fit_result,
        posterior_path=args.posterior,
        model_path=args.model_products,
        geometry_path=args.geometry_constraint,
        oracle_path=args.oracle_verification,
        output=args.output,
    )
    print(args.output)


if __name__ == "__main__":
    main()
