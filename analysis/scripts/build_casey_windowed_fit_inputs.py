#!/usr/bin/env python3
"""Materialize the owner-ratified windowed Casey fit inputs (2026-08-04).

Owner ruling: delivered fit inputs are redefined to compact windows
CHIME [155:235], DSA [1299:1325] (decision record:
~/Data/Faber2026/review/casey-joint-fit-inputs/window-decision-ratified-20260804.json,
amended in-session to the envelope-preserving slices). This script slices the
approved full-window products, rebuilds the timing-sensitivity roster, and
emits a new authorized config whose resolution block binds the windowed
products. The config declares `windowed_inputs` (source run, windows, and the
SHA-256 of every prematerialized product) and binds the owner's ratified
window-decision artifact in `review_decision.window_amendment`; the workflow
verifies the prematerialized products at joint_fit and refuses to rerun the
product-building stages from this config. All hashes are computed with
one_event_workflow's own functions. Original products, configs, and
checkpoints are not touched.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from copy import deepcopy
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from one_event_workflow import (  # noqa: E402
    _payload_sha256,
    arrays_sha256,
    event_binding_sha256,
    load_config,
    sample_time_axis_ns,
    validate_timing_sensitivity_roster,
)

from radio_pipeline.fitting.products import sha256_file  # noqa: E402

EVIDENCE = Path("/data/Faber2026/evidence/dm-toa-geometry-20260801")
OLD_ROOT = EVIDENCE / "casey-one-event-workflow"
NEW_ROOT = EVIDENCE / "casey-one-event-workflow-windowed"
OLD_CONFIG = EVIDENCE / "casey-control/casey-authorized.json"
NEW_CONFIG = EVIDENCE / "casey-control/casey-authorized-windowed.json"
# Owner window ratification (2026-08-04). The artifact is copied into the
# windowed output root and bound by hash in the review decision's
# window_amendment block; the build refuses to run without it.
WINDOW_DECISION = Path(
    os.environ.get(
        "CASEY_WINDOW_DECISION",
        "~/Data/Faber2026/review/casey-joint-fit-inputs/"
        "window-decision-ratified-20260804.json",
    )
).expanduser()
WORKFLOW_RUNNER = Path(__file__).resolve().parent / "run_one_event_absolute_dm_workflow.py"

WINDOWS = {"chime": (155, 235), "dsa": (1299, 1325)}
DT_NS = {"chime": 81920, "dsa": 32768}


def slice_product(src: Path, dst: Path, instrument: str) -> dict:
    start, stop = WINDOWS[instrument]
    with np.load(src, allow_pickle=False) as archive:
        data = {key: np.array(archive[key], copy=True) for key in archive.files}
    ntime = data["waterfall"].shape[1]
    assert 0 <= start < stop <= ntime, (src, start, stop, ntime)
    out = {}
    for key, value in data.items():
        if key == "time0_unix_ns":
            out[key] = np.asarray(
                int(value) + start * DT_NS[instrument], dtype=value.dtype
            )
        elif value.ndim == 2 and value.shape[1] == ntime:
            out[key] = np.ascontiguousarray(value[:, start:stop])
        else:
            out[key] = value
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_suffix(".tmp.npz")
    np.savez_compressed(tmp, **out)
    tmp.replace(dst)
    return out


def main() -> None:
    if NEW_ROOT.exists() and any(NEW_ROOT.iterdir()):
        raise SystemExit(f"refusing to overwrite non-empty {NEW_ROOT}")
    if not WINDOW_DECISION.is_file():
        raise SystemExit(
            f"owner window-decision artifact not found: {WINDOW_DECISION} "
            "(set CASEY_WINDOW_DECISION to its location)"
        )
    config = json.loads(OLD_CONFIG.read_text())

    sliced = {}
    for rel, instrument in (
        ("products/fit/chime-fit-observation.npz", "chime"),
        ("products/fit/dsa-fit-observation.npz", "dsa"),
        ("products/timing-sensitivity/dsa-anchor-sensitivity.npz", "dsa"),
        ("products/timing-sensitivity/dsa-reference-invariance.npz", "dsa"),
    ):
        sliced[rel] = slice_product(OLD_ROOT / rel, NEW_ROOT / rel, instrument)
    for rel in (
        "products/dsa/dsa_anchor_dm.npz",
        "timing-sensitivity-proposal.pdf",
        "component-proposal.json",
        "resolution-lock-proposal.json",
    ):
        src = OLD_ROOT / rel
        if src.exists():
            dst = NEW_ROOT / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

    # --- config: paths, dsa crop bookkeeping, components, resolution -------
    config["paths"]["output_root"] = str(NEW_ROOT)
    config["identity"]["output_root_basename"] = NEW_ROOT.name
    dsa_start, dsa_stop = WINDOWS["dsa"]
    chime_start, chime_stop = WINDOWS["chime"]
    config["dsa"]["raw_crop_start_sample"] = (
        int(config["dsa"]["raw_crop_start_sample"]) + dsa_start
    )
    config["dsa"]["crop_samples"] = dsa_stop - dsa_start

    shift = {"chime": chime_start, "dsa": dsa_start}
    for row in config["joint_fit"]["components"]:
        row["center_sample"] = float(row["center_sample"]) - shift[row["instrument"]]

    resolution = config["joint_fit"]["resolution"]
    for instrument, rel in (
        ("chime", "products/fit/chime-fit-observation.npz"),
        ("dsa", "products/fit/dsa-fit-observation.npz"),
    ):
        product = sliced[rel]
        path = NEW_ROOT / rel
        resolution[f"{instrument}_shape"] = list(map(int, product["waterfall"].shape))
        resolution[f"{instrument}_time0_unix_ns"] = int(product["time0_unix_ns"])
        resolution[f"{instrument}_fit_observation_sha256"] = sha256_file(path)
        resolution[f"{instrument}_frequency_grid_sha256"] = arrays_sha256(
            product["frequency_mhz"], product["channel_width_mhz"]
        )
        resolution[f"{instrument}_valid_mask_sha256"] = arrays_sha256(
            product["pixel_valid"]
        )
        resolution[f"{instrument}_off_pulse_mask_sha256"] = arrays_sha256(
            product["noise_estimation_mask"]
        )
        resolution[f"{instrument}_waterfall_sha256"] = arrays_sha256(
            product["waterfall"]
        )
        resolution[f"{instrument}_noise_std_sha256"] = arrays_sha256(
            product["noise_std"]
        )
        resolution[f"{instrument}_time_axis_sha256"] = arrays_sha256(
            sample_time_axis_ns(
                time0_unix_ns=int(product["time0_unix_ns"]),
                sample_interval_s=float(product["sample_interval_s"]),
                sample_count=int(product["waterfall"].shape[1]),
            )
        )

    # --- roster --------------------------------------------------------------
    roster = json.loads((OLD_ROOT / "timing-sensitivity-roster.json").read_text())
    dsa_shift_ns = dsa_start * DT_NS["dsa"]
    roster["source_observation"]["path"] = str(
        NEW_ROOT / "products/fit/dsa-fit-observation.npz"
    )
    roster["source_observation"]["sha256"] = resolution["dsa_fit_observation_sha256"]
    roster["authoritative_frequency_source"]["path"] = str(
        NEW_ROOT / "products/dsa/dsa_anchor_dm.npz"
    )
    roster["primary_anchor"]["time0_unix_ns"] += dsa_shift_ns
    alternative = roster["alternative_anchor"]
    alternative["time0_unix_ns"] += dsa_shift_ns
    alternative["product"] = str(
        NEW_ROOT / "products/timing-sensitivity/dsa-anchor-sensitivity.npz"
    )
    alternative["sha256"] = sha256_file(Path(alternative["product"]))
    invariance = roster["reference_frequency_invariance"]
    invariance["time0_unix_ns"] += dsa_shift_ns
    invariance["product"] = str(
        NEW_ROOT / "products/timing-sensitivity/dsa-reference-invariance.npz"
    )
    invariance["sha256"] = sha256_file(Path(invariance["product"]))
    roster["review_pdf"]["path"] = str(NEW_ROOT / "timing-sensitivity-proposal.pdf")
    # The workflow's output-set validation checks the roster against the hash
    # of the runner that will execute the windowed refit; stamp the current one.
    roster["materializer_sha256"] = sha256_file(WORKFLOW_RUNNER)
    roster_path = NEW_ROOT / "timing-sensitivity-roster.json"
    roster_path.write_text(json.dumps(roster, indent=2) + "\n")

    # --- review decision + authorization + binding ---------------------------
    joint_fit = config["joint_fit"]
    review = joint_fit["review_decision"]
    review["components_sha256"] = _payload_sha256(joint_fit["components"])
    review["approved_resolution_sha256"] = _payload_sha256(joint_fit["resolution"])
    review["timing_sensitivity_roster_sha256"] = sha256_file(roster_path)
    review["note"] += (
        " Amended 2026-08-04: owner ratified compact delivered windows CHIME"
        " [155:235], DSA [1299:1325] (envelope-preserving); see"
        " window-decision-ratified-20260804.json."
    )
    # Bind the owner's window amendment by hash. The reviewed full-window
    # proposals stay bound via component/resolution_proposal_sha256; the
    # amendment records exactly which reviewed proposals the windows amend.
    amendment_dst = NEW_ROOT / WINDOW_DECISION.name
    shutil.copy2(WINDOW_DECISION, amendment_dst)
    review["window_amendment"] = {
        "path": str(amendment_dst),
        "sha256": sha256_file(amendment_dst),
        "chime_window_samples": list(WINDOWS["chime"]),
        "dsa_window_samples": list(WINDOWS["dsa"]),
        "base_component_proposal_sha256": review["component_proposal_sha256"],
        "base_resolution_proposal_sha256": review["resolution_proposal_sha256"],
    }

    # Declare the prematerialized windowed products. The workflow verifies
    # these hashes at joint_fit instead of rebuilding, and refuses to run the
    # product-building stages from this configuration.
    prematerialized: dict[str, str] = {}
    for rel in sorted(
        {
            *sliced.keys(),
            "products/dsa/dsa_anchor_dm.npz",
            "timing-sensitivity-proposal.pdf",
            "component-proposal.json",
            "resolution-lock-proposal.json",
        }
    ):
        product = NEW_ROOT / rel
        if product.is_file():
            prematerialized[rel] = sha256_file(product)
    prematerialized["timing-sensitivity-roster.json"] = sha256_file(roster_path)
    config["windowed_inputs"] = {
        "source_config_sha256": sha256_file(OLD_CONFIG),
        "source_output_root": str(OLD_ROOT),
        "chime_window_samples": list(WINDOWS["chime"]),
        "dsa_window_samples": list(WINDOWS["dsa"]),
        "prematerialized": prematerialized,
    }
    authorization = joint_fit["authorization"]
    authorization["note"] += (
        " Windowed inputs rebuilt under the owner's 2026-08-04 window ratification."
    )
    reviewed_source = deepcopy(config)
    reviewed_source["joint_fit"].pop("authorization")
    reviewed_source["joint_fit"]["status"] = "reviewed_execution_disabled"
    reviewed_source["joint_fit"]["execution_authorized"] = False
    reviewed_source["workflow"]["execution_authorized"] = False
    reviewed_source["result_status"] = (
        "geometry_constrained_joint_fit_reviewed_execution_disabled"
    )
    reviewed_source.pop("event_binding_sha256", None)
    authorization["source_reviewed_event_binding_sha256"] = event_binding_sha256(
        reviewed_source
    )
    config["event_binding_sha256"] = event_binding_sha256(config)

    geometry = json.loads((OLD_ROOT / "geometry-constraint.json").read_text())
    geometry["event_binding_sha256"] = config["event_binding_sha256"]
    (NEW_ROOT / "geometry-constraint.json").write_text(
        json.dumps(geometry, indent=2) + "\n"
    )

    NEW_CONFIG.write_text(json.dumps(config, indent=2) + "\n")

    # --- verification: the checking code itself must accept everything -------
    validated = load_config(NEW_CONFIG, require_execution_authorized=True)
    validate_timing_sensitivity_roster(validated, roster)
    report = {
        "new_config": str(NEW_CONFIG),
        "new_root": str(NEW_ROOT),
        "event_binding_sha256": config["event_binding_sha256"],
        "chime_shape": resolution["chime_shape"],
        "dsa_shape": resolution["dsa_shape"],
        "chime_time0_unix_ns": resolution["chime_time0_unix_ns"],
        "dsa_time0_unix_ns": resolution["dsa_time0_unix_ns"],
        "chime_fit_observation_sha256": resolution["chime_fit_observation_sha256"],
        "dsa_fit_observation_sha256": resolution["dsa_fit_observation_sha256"],
        "roster_sha256": review["timing_sensitivity_roster_sha256"],
        "components": joint_fit["components"],
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
