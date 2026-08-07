from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from one_event_workflow import event_binding_sha256, sha256_file  # noqa: E402

SCRIPT = ROOT / "scripts/render_one_event_hybrid_packet.py"
SPEC = importlib.util.spec_from_file_location("render_casey_packet", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

STATUS = "one_event_hybrid_pending_independent_review"


def _product(path: Path, *, chime: bool, dm: float) -> None:
    rng = np.random.default_rng(round(dm * 1000))
    waterfall = rng.normal(size=(8, 128))
    waterfall[:, 60:64] += 4.0
    payload = {
        "waterfall": waterfall.astype(np.float32),
        "frequency_mhz": np.linspace(410.0, 790.0, 8),
        "accepted_live": np.ones(8, dtype=bool),
        "sample_time_s": np.asarray(8.192e-5 if chime else 3.2768e-5),
        "target_total_dm_pc_cm3": np.asarray(dm),
    }
    if chime:
        payload["fine_frequency_id"] = np.arange(8, dtype=np.int64)
    np.savez_compressed(path, **payload)


def test_hybrid_packet_renderer_accepts_current_schema(tmp_path: Path) -> None:
    chime_paths = {}
    for key, dm in {
        "anchor_before_residual": 491.28,
        "hybrid_fit_dm": 491.276,
        "geometry_dm": 491.2792,
    }.items():
        path = tmp_path / f"chime_{key}.npz"
        _product(path, chime=True, dm=dm)
        chime_paths[key] = {"path": str(path)}
    dsa_paths = {}
    for key, dm in {
        "input_dm": 491.211,
        "anchor_dm": 491.28,
        "hybrid_fit_dm": 491.276,
        "geometry_dm": 491.2792,
    }.items():
        path = tmp_path / f"dsa_{key}.npz"
        _product(path, chime=False, dm=dm)
        dsa_paths[key] = {"path": str(path)}

    fine_dm = [491.274, 491.276, 491.278]
    fine = [{"target_total_dm_pc_cm3": dm} for dm in fine_dm]
    chime = {
        "status": STATUS,
        "burst": "casey",
        "support": {
            "full_grid_rows": 1024,
            "h5_missing_count": 253,
            "h5_missing_ids": list(range(253)),
            "h5_present_accepted_dead_count": 51,
            "h5_present_accepted_dead_ids": list(range(253, 304)),
            "accepted_live_count": 720,
            "proposed_extra_bad_rows": [],
        },
        "hybrid_method": {
            "anchor_dm_pc_cm3": 491.28,
            "coherent_anchor_count": 1,
            "oracle_only_fully_coherent_count": 3,
            "upchannel_factor": 16,
            "upchannel_sample_time_s": 8.192e-5,
                "smearing_bound": {
                    "maximum_smearing_s": 5.0e-6,
                    "fraction_of_upchannel_sample": 0.061,
                    "fraction_of_reference_pulse_fwhm": 0.028,
                    "passed": True,
                },
                "injected_absolute_dm_recovery": {
                    "injected_absolute_dm_pc_cm3": 491.316,
                    "recovered_absolute_dm_pc_cm3": 491.3158,
                    "absolute_error_pc_cm3": 0.0002,
                    "passed": True,
                },
        },
        "grid": {
            "fine": fine,
            "fit": {
                "dm_pc_cm3": 491.276,
                "selected_score": [0.8, 1.0, 0.85],
            },
        },
        "geometry_dm_pc_cm3": 491.2792,
        "full_coherent_oracle": {
            "dm_pc_cm3": [491.266, 491.276, 491.286],
            "hybrid_normalised_score": [0.8, 1.0, 0.82],
            "fully_coherent_normalised_score": [0.81, 1.0, 0.83],
            "maximum_normalised_score_absolute_difference": 0.01,
            "absolute_peak_difference_pc_cm3": 0.0002,
            "center_score_ratio_hybrid_over_fully_coherent": 1.002,
            "passed": True,
        },
        "products": chime_paths,
    }
    dsa = {
        "status": STATUS,
        "burst": "casey",
        "support": {"proposed_extra_bad_rows": []},
        "input_state": {
            "raw_total_dm_pc_cm3": 491.211,
            "direct_frequency_order_median_correlation": 0.906,
            "reversed_frequency_order_median_correlation": 0.081,
        },
        "dedispersion": {"reference_frequency_mhz": 400.0},
        "products": dsa_paths,
    }
    audit = {
        "event": "casey",
        "row_match": {
            "selected_count": 4,
            "median_start_sample": 13998.0,
            "matches": [
                {
                    "row": row,
                    "best_start_sample": 13998,
                    "correlation": 0.90 + row * 0.005,
                }
                for row in range(4)
            ],
        },
        "dedispersion_state_fit": {
            "inferred_reference_minus_raw_dm_pc_cm3": 1.2e-13
        },
        "frequency_order": {
            "direct_median_correlation": 0.906,
            "reversed_median_correlation": 0.081,
        },
    }
    chime_result = tmp_path / "chime_result.json"
    dsa_result = tmp_path / "dsa_result.json"
    audit_path = tmp_path / "dsa_audit.json"
    provenance_path = tmp_path / "run_provenance.json"
    chime_result.write_text(json.dumps(chime))
    dsa_result.write_text(json.dumps(dsa))
    audit_path.write_text(json.dumps(audit))
    provenance_path.write_text(
        json.dumps(
            {
                "control_manifest_sha256": "a" * 64,
                "container_image_id": "sha256:" + "b" * 64,
            }
        )
    )
    accepted_chime = tmp_path / "casey_accepted_chime.npy"
    accepted_dsa = tmp_path / "casey_accepted_dsa.npy"
    np.save(accepted_chime, np.zeros((1, 1)))
    np.save(accepted_dsa, np.zeros((1, 1)))
    config = json.loads(
        (
            ROOT
            / "analysis-configs/absolute-dm/casey.json"
        ).read_text()
    )
    config["paths"]["accepted_chime_reference"] = str(accepted_chime)
    config["paths"]["accepted_dsa_reference"] = str(accepted_dsa)
    config["identity"]["input_basenames"]["accepted_chime_reference"] = (
        accepted_chime.name
    )
    config["identity"]["input_basenames"]["accepted_dsa_reference"] = (
        accepted_dsa.name
    )
    config["input_sha256"]["accepted_chime_reference"] = sha256_file(
        accepted_chime
    )
    config["input_sha256"]["accepted_dsa_reference"] = sha256_file(accepted_dsa)
    config["event_binding_sha256"] = event_binding_sha256(config)
    binding = config["event_binding_sha256"]
    chime["event_binding_sha256"] = binding
    dsa["event_binding_sha256"] = binding
    audit["event_binding_sha256"] = binding
    chime_result.write_text(json.dumps(chime))
    dsa_result.write_text(json.dumps(dsa))
    audit_path.write_text(json.dumps(audit))
    provenance = json.loads(provenance_path.read_text())
    provenance["event_binding_sha256"] = binding
    provenance_path.write_text(json.dumps(provenance))
    config_path = tmp_path / "casey_packet_config.json"
    config_path.write_text(json.dumps(config))
    output_svg = tmp_path / "packet.svg"
    output_png = tmp_path / "packet.png"
    receipt_path = tmp_path / "receipt.json"

    receipt = MODULE.render(
        config_path=config_path,
        chime_result_path=chime_result,
        dsa_result_path=dsa_result,
        dsa_audit_path=audit_path,
        run_provenance_path=provenance_path,
        accepted_chime_reference=accepted_chime,
        accepted_dsa_reference=accepted_dsa,
        output_svg=output_svg,
        output_png=output_png,
        receipt_path=receipt_path,
    )

    assert output_svg.stat().st_size > 1000
    assert output_png.stat().st_size > 1000
    assert receipt["checks"]["coherent_anchor_count"] == 1
    assert receipt["checks"]["full_coherent_oracle_passed"] is True
