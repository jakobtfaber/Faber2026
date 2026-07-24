from copy import deepcopy

from scripts.profile_component_calibration import validate_campaign


def valid_payload():
    return {
        "schema": "faber2026-profile-component-calibration/v1",
        "domain": "time_frequency_profile",
        "status": "scientific_gate_pending",
        "manuscript_count_setting_enabled": False,
        "provenance": {
            "pipeline_git_sha": "a" * 40,
            "config_sha256": "b" * 64,
            "input_manifest_sha256": "c" * 64,
            "command": "python -m scattering.profile_count_calibration campaign.yaml",
            "seed_rule": "seed0 + cell_index * 10000 + injection_index",
        },
        "comparison_contract": {
            "same_likelihood": True,
            "same_time_frequency_support": True,
            "ordered_arrivals": True,
            "gain_prior_arms": ["gain_s2_1", "gain_s2_10", "gain_s2_100"],
        },
        "cells": [{
            "instrument": "CHIME/FRB",
            "true_count": 2,
            "snr": 20,
            "separation_bins": 4,
            "width_bins": 2,
            "n_injections": 20,
            "selected_count_histogram": {"1": 2, "2": 17, "3": 1},
            "overcount_rate": 0.05,
            "undercount_rate": 0.10,
            "exact_recovery_rate": 0.85,
            "all_gain_prior_arms_agree": True,
            "mode_matched": True,
        }],
        "scientific_gate": {
            "owner_ratified": False,
            "maximum_overcount_rate": None,
            "maximum_undercount_rate": None,
            "supported_domain": None,
        },
    }


def test_complete_unratified_campaign_packet_is_admissible():
    assert validate_campaign(valid_payload()) == []


def test_acf_screen_count_packet_is_rejected():
    payload = valid_payload()
    payload["domain"] = "frequency_acf"
    assert any("ACF screen counts are inadmissible" in error for error in validate_campaign(payload))


def test_count_setting_cannot_be_enabled_before_ratification():
    payload = valid_payload()
    payload["manuscript_count_setting_enabled"] = True
    assert any("must be false" in error for error in validate_campaign(payload))


def test_incomplete_or_mode_mismatched_cell_fails_closed():
    payload = valid_payload()
    payload["cells"][0]["mode_matched"] = False
    payload["cells"][0]["selected_count_histogram"]["2"] = 16
    errors = validate_campaign(payload)
    assert any("not mode matched" in error for error in errors)
    assert any("histogram total" in error for error in errors)


def test_scientific_thresholds_cannot_be_invented_by_campaign():
    payload = deepcopy(valid_payload())
    payload["scientific_gate"]["maximum_overcount_rate"] = 0.05
    assert any("must remain null" in error for error in validate_campaign(payload))
