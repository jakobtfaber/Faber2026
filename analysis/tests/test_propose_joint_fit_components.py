from __future__ import annotations

import copy
import json

import numpy as np
import pytest
from one_event_workflow import event_binding_sha256
from propose_joint_fit_components import run

from radio_pipeline.fitting import DispersionState
from radio_pipeline.fitting.products import write_band_observation_product


def _config(
    tmp_path,
    *,
    chime_count=1,
    dsa_count=1,
    associations=None,
):
    if associations is None:
        associations = [
            {
                "name": "c1d1",
                "matches": [
                    {
                        "latent_id": "c1",
                        "chime_component_id": "chime_c1",
                        "dsa_component_id": "dsa_c1",
                    }
                ],
            }
        ]
    config = {
        "event": "injected",
        "identity": {"reviewed_event": "injected"},
        "input_sha256": {
            "raw_chime_h5": "1" * 64,
            "accepted_chime_reference": "2" * 64,
            "raw_dsa_filterbank": "3" * 64,
            "accepted_dsa_reference": "4" * 64,
        },
        "joint_fit": {
            "review_plan": {
                "component_count": {
                    "chime": chime_count,
                    "dsa": dsa_count,
                },
                "association_hypotheses": associations,
            }
        },
    }
    config["event_binding_sha256"] = event_binding_sha256(config)
    path = tmp_path / "config.json"
    path.write_text(json.dumps(config, indent=2) + "\n")
    return config, path


def _product(
    tmp_path,
    *,
    instrument,
    sample_count,
    sample_interval_s,
    centers,
    widths,
    amplitude=3.0,
):
    rng = np.random.default_rng(17 if instrument == "chime" else 29)
    row_count = 24 if instrument == "chime" else 16
    values = rng.normal(size=(row_count, sample_count))
    time = np.arange(sample_count)
    for center, width in zip(centers, widths, strict=True):
        pulse = amplitude * np.exp(-0.5 * np.square((time - center) / width))
        values += pulse[None, :]
    valid = np.ones(values.shape, dtype=bool)
    valid[::7, 50:58] = False
    hashes = (
        {
            "raw_chime_h5": "1" * 64,
            "accepted_chime_reference": "2" * 64,
        }
        if instrument == "chime"
        else {
            "raw_dsa_filterbank": "3" * 64,
            "accepted_dsa_reference": "4" * 64,
        }
    )
    path = tmp_path / f"{instrument}.npz"
    write_band_observation_product(
        path,
        instrument=instrument,
        waterfall=values,
        valid=valid,
        frequency_mhz=np.linspace(
            410.0 if instrument == "chime" else 1500.0,
            790.0 if instrument == "chime" else 1300.0,
            row_count,
        ),
        channel_width_mhz=0.1,
        sample_interval_s=sample_interval_s,
        time0_unix_ns=1_700_000_000_000_000_000,
        dispersion=DispersionState(0.0, 491.28, 0.0, 491.28, "injected"),
        input_sha256=hashes,
    )
    return path


def _inputs(
    tmp_path,
    *,
    chime_centers=(128,),
    dsa_centers=(170,),
    amplitude=3.0,
    chime_count=1,
    dsa_count=1,
    associations=None,
):
    config, config_path = _config(
        tmp_path,
        chime_count=chime_count,
        dsa_count=dsa_count,
        associations=associations,
    )
    chime = _product(
        tmp_path,
        instrument="chime",
        sample_count=256,
        sample_interval_s=2.56e-6,
        centers=chime_centers,
        widths=(5,) * len(chime_centers),
        amplitude=amplitude,
    )
    dsa = _product(
        tmp_path,
        instrument="dsa",
        sample_count=320,
        sample_interval_s=32.768e-6,
        centers=dsa_centers,
        widths=(3,) * len(dsa_centers),
        amplitude=amplitude,
    )
    return config, config_path, chime, dsa


def test_injected_c1d1_proposal_preserves_native_grids_and_emits_pdf(tmp_path) -> None:
    config, config_path, chime, dsa = _inputs(tmp_path)
    # One unflagged interference pixel must not displace the broadband pulse.
    with np.load(chime, allow_pickle=False) as archive:
        payload = {name: archive[name] for name in archive.files}
    payload["waterfall"][0, 80] = 1.0e6
    np.savez_compressed(chime, **payload)
    original_config = config_path.read_bytes()
    output_json = tmp_path / "component-proposal.json"
    output_pdf = tmp_path / "component-proposal.pdf"
    result = run(
        config_path=config_path,
        event="injected",
        chime_path=chime,
        dsa_path=dsa,
        output_json=output_json,
        output_pdf=output_pdf,
    )

    assert result["status"] == "proposal_pending_owner_review"
    assert result["approved"] is False
    assert result["event_binding_sha256"] == config["event_binding_sha256"]
    assert result["native_grids_preserved"] is True
    assert output_pdf.read_bytes().startswith(b"%PDF-")
    assert config_path.read_bytes() == original_config
    components = {row["instrument"]: row for row in result["components"]}
    assert abs(components["chime"]["center_sample"] - 128) < 10
    assert abs(components["dsa"]["center_sample"] - 170) < 10
    for component in components.values():
        start, stop = component["on_pulse_envelope_samples"]
        assert 0 < start < stop
        assert component["padding_samples"] >= 4
        assert component["width_bounds_s"][0] < component["width_bounds_s"][1]
        assert min(component["off_pulse_samples"].values()) >= 8


def test_proposal_fails_on_low_signal(tmp_path) -> None:
    _, config_path, chime, dsa = _inputs(tmp_path, amplitude=0.0)
    with pytest.raises(ValueError, match="signal-to-noise"):
        run(
            config_path=config_path,
            event="injected",
            chime_path=chime,
            dsa_path=dsa,
            output_json=tmp_path / "proposal.json",
            output_pdf=tmp_path / "proposal.pdf",
        )


def test_proposal_fails_when_padded_envelope_contacts_edge(tmp_path) -> None:
    _, config_path, chime, dsa = _inputs(tmp_path, chime_centers=(10,))
    with pytest.raises(ValueError, match="contacts crop edge"):
        run(
            config_path=config_path,
            event="injected",
            chime_path=chime,
            dsa_path=dsa,
            output_json=tmp_path / "proposal.json",
            output_pdf=tmp_path / "proposal.pdf",
        )


def test_multi_component_one_component_preserves_ambiguous_hypotheses(tmp_path) -> None:
    associations = [
        {
            "name": "first_chime",
            "matches": [
                {
                    "latent_id": "shared",
                    "chime_component_id": "chime_c1",
                    "dsa_component_id": "dsa_c1",
                }
            ],
        },
        {
            "name": "second_chime",
            "matches": [
                {
                    "latent_id": "shared",
                    "chime_component_id": "chime_c2",
                    "dsa_component_id": "dsa_c1",
                }
            ],
        },
    ]
    _, config_path, chime, dsa = _inputs(
        tmp_path,
        chime_centers=(90, 166),
        dsa_centers=(170,),
        chime_count=2,
        dsa_count=1,
        associations=associations,
    )
    result = run(
        config_path=config_path,
        event="injected",
        chime_path=chime,
        dsa_path=dsa,
        output_json=tmp_path / "proposal.json",
        output_pdf=tmp_path / "proposal.pdf",
    )
    components = {row["component_id"]: row for row in result["components"]}
    assert set(components) == {"chime_c1", "chime_c2", "dsa_c1"}
    assert abs(components["chime_c1"]["center_sample"] - 90) < 10
    assert abs(components["chime_c2"]["center_sample"] - 166) < 10
    assert result["association_hypotheses"] == associations
    assert result["review_plan"]["component_count"] == {"chime": 2, "dsa": 1}


def test_plan_rejects_unknown_and_non_order_preserving_components(tmp_path) -> None:
    unknown = [
        {
            "name": "unknown",
            "matches": [
                {
                    "latent_id": "x",
                    "chime_component_id": "chime_c2",
                    "dsa_component_id": "dsa_c1",
                }
            ],
        }
    ]
    _, config_path, chime, dsa = _inputs(tmp_path, associations=unknown)
    with pytest.raises(ValueError, match="unknown component"):
        run(
            config_path=config_path,
            event="injected",
            chime_path=chime,
            dsa_path=dsa,
            output_json=tmp_path / "proposal.json",
            output_pdf=tmp_path / "proposal.pdf",
        )

    reversed_order = [
        {
            "name": "reversed",
            "matches": [
                {
                    "latent_id": "x",
                    "chime_component_id": "chime_c1",
                    "dsa_component_id": "dsa_c2",
                },
                {
                    "latent_id": "y",
                    "chime_component_id": "chime_c2",
                    "dsa_component_id": "dsa_c1",
                },
            ],
        }
    ]
    config, config_path = _config(
        tmp_path,
        chime_count=2,
        dsa_count=2,
        associations=reversed_order,
    )
    config_path.write_text(json.dumps(config))
    with pytest.raises(ValueError, match="not order-preserving"):
        run(
            config_path=config_path,
            event="injected",
            chime_path=chime,
            dsa_path=dsa,
            output_json=tmp_path / "proposal.json",
            output_pdf=tmp_path / "proposal.pdf",
        )


def test_requested_component_count_must_be_separable(tmp_path) -> None:
    associations = [
        {
            "name": "first_only",
            "matches": [
                {
                    "latent_id": "x",
                    "chime_component_id": "chime_c1",
                    "dsa_component_id": "dsa_c1",
                }
            ],
        }
    ]
    _, config_path, chime, dsa = _inputs(
        tmp_path,
        chime_count=2,
        associations=associations,
    )
    with pytest.raises(ValueError, match="cannot separate requested"):
        run(
            config_path=config_path,
            event="injected",
            chime_path=chime,
            dsa_path=dsa,
            output_json=tmp_path / "proposal.json",
            output_pdf=tmp_path / "proposal.pdf",
        )


def test_proposal_fails_without_two_sided_off_pulse_support(tmp_path) -> None:
    _, config_path, chime, dsa = _inputs(tmp_path)
    with np.load(chime, allow_pickle=False) as archive:
        payload = {name: archive[name] for name in archive.files}
    noise_mask = np.zeros_like(payload["noise_estimation_mask"], dtype=bool)
    noise_mask[:, :7] = payload["pixel_valid"][:, :7]
    noise_mask[:, -7:] = payload["pixel_valid"][:, -7:]
    payload["noise_estimation_mask"] = noise_mask
    np.savez_compressed(chime, **payload)
    with pytest.raises(ValueError, match="inadequate off-pulse support"):
        run(
            config_path=config_path,
            event="injected",
            chime_path=chime,
            dsa_path=dsa,
            output_json=tmp_path / "proposal.json",
            output_pdf=tmp_path / "proposal.pdf",
        )


def test_proposal_fails_on_changed_event_or_product_identity(tmp_path) -> None:
    config, config_path, chime, dsa = _inputs(tmp_path)
    changed = copy.deepcopy(config)
    changed["identity"]["reviewed_event"] = "other"
    config_path.write_text(json.dumps(changed))
    with pytest.raises(ValueError, match="configuration identity"):
        run(
            config_path=config_path,
            event="injected",
            chime_path=chime,
            dsa_path=dsa,
            output_json=tmp_path / "proposal.json",
            output_pdf=tmp_path / "proposal.pdf",
        )

    config_path.write_text(json.dumps(config))
    with np.load(chime, allow_pickle=False) as archive:
        payload = {name: archive[name] for name in archive.files}
    payload["input_sha256_json"] = np.asarray(
        json.dumps(
            {
                "raw_chime_h5": "9" * 64,
                "accepted_chime_reference": "2" * 64,
            }
        )
    )
    np.savez_compressed(chime, **payload)
    with pytest.raises(ValueError, match="input identity changed"):
        run(
            config_path=config_path,
            event="injected",
            chime_path=chime,
            dsa_path=dsa,
            output_json=tmp_path / "proposal.json",
            output_pdf=tmp_path / "proposal.pdf",
        )
