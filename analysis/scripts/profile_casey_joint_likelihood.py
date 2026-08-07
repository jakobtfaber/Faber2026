#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

import numpy as np
from fit_one_event_joint_burst import _request
from one_event_workflow import load_config

from radio_pipeline.fitting.joint_burst import (
    _component_kernels,
    _gain_marginal_band,
    _layout,
    _log_likelihood,
    _prior_transform,
    _values,
)


def _elapsed(callable_, repeats: int) -> list[float]:
    samples = []
    for _ in range(repeats):
        started = time.perf_counter()
        callable_()
        samples.append(time.perf_counter() - started)
    return samples


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--chime-observation", type=Path, required=True)
    parser.add_argument("--dsa-observation", type=Path, required=True)
    parser.add_argument("--geometry-constraint", type=Path, required=True)
    parser.add_argument("--max-seconds", type=float, required=True)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--reference-calls", type=int, default=849724)
    parser.add_argument("--workers", type=int, default=16)
    args = parser.parse_args()

    config = load_config(args.config)
    request = _request(
        config,
        args.chime_observation,
        args.dsa_observation,
        args.geometry_constraint,
        checkpoint_dir=Path("/tmp/casey-likelihood-profile-checkpoints"),
        timing_variant="primary",
        timing_sensitivity_roster=None,
        timing_sensitivity_roster_path=None,
        timing_sensitivity_roster_sha256=None,
    )
    report = {}
    failed = False
    for morphology in request.settings.morphologies:
        layout = _layout(request, request.associations[0], morphology)
        theta = _prior_transform(np.full(len(layout.parameters), 0.5), layout)
        values = _values(theta, layout)
        _log_likelihood(theta, request, layout, morphology)

        kernel_samples = []
        gain_samples = []
        for observation in request.observations:
            kernels = _component_kernels(
                request, observation, layout, values, morphology
            )
            kernel_samples.extend(
                _elapsed(
                    lambda observation=observation,
                    layout=layout,
                    values=values,
                    morphology=morphology: _component_kernels(
                        request, observation, layout, values, morphology
                    ),
                    args.repeats,
                )
            )
            gain_samples.extend(
                _elapsed(
                    lambda observation=observation, kernels=kernels: _gain_marginal_band(
                        observation, kernels, request.settings.gain_variance
                    ),
                    args.repeats,
                )
            )
        likelihood_samples = _elapsed(
            lambda theta=theta, layout=layout, morphology=morphology: _log_likelihood(
                theta, request, layout, morphology
            ),
            args.repeats,
        )
        median_seconds = statistics.median(likelihood_samples)
        failed |= median_seconds > args.max_seconds
        report[morphology] = {
            "median_likelihood_seconds": median_seconds,
            "median_kernel_seconds_per_band": statistics.median(kernel_samples),
            "median_gain_seconds_per_band": statistics.median(gain_samples),
            "projected_reference_wall_seconds": (
                median_seconds * args.reference_calls / args.workers
            ),
            "samples": likelihood_samples,
        }
    print(json.dumps(report, indent=2, sort_keys=True))
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
