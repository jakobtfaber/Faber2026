"""Contract tests for the Figure 3 review-candidate input."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

from foregrounds.census.build_sightline_halo_grid_input import build_frame
from foregrounds.visualization.sightline_halo_grid import _load


@__import__("pytest").mark.skipif(not __import__("pathlib").Path("foregrounds/census/data/frozen_census/bursts.csv").exists(), reason="Faber2026 manuscript fixtures moved to the analysis repository")
def test_figure_input_has_full_host_roster_and_only_confirmed_systems() -> None:
    frame = build_frame()
    hosts = frame[frame.row_kind == "host"]
    systems = frame[frame.row_kind == "system"]
    assert len(hosts) == 12
    assert hosts.nickname.is_unique
    assert set(hosts.redshift_class) == {"established", "inferred_dm_z"}
    assert set(systems.evidence_class) == {
        "confirmed_system",
        "probabilistic_candidate",
    }
    assert set(
        systems.loc[
            systems.evidence_class == "confirmed_system", "final_verdict"
        ]
    ) == {"confirmed"}
    assert not systems[["nickname", "object_id"]].duplicated().any()


def test_hostless_panels_bind_full_posterior_and_limitations() -> None:
    frame = build_frame()
    hosts = frame[
        (frame.row_kind == "host") & (frame.redshift_class == "inferred_dm_z")
    ]
    assert set(hosts.nickname) == {"freya", "mahi", "wilhelm"}
    assert (hosts.frb_z_lower < hosts.frb_z).all()
    assert (hosts.frb_z < hosts.frb_z_upper).all()
    assert hosts.frb_posterior_sha256.str.fullmatch(r"[0-9a-f]{64}").all()
    assert hosts.frb_redshift_basis.str.contains("coupled").all()
    assert hosts.coverage_limitations.astype(bool).all()
    assert hosts.query_limitations.astype(bool).all()
    assert not hosts.empty_sightline_claim.astype(bool).any()


def test_probabilistic_candidates_are_never_promoted_to_confirmed() -> None:
    frame = build_frame()
    candidates = frame[
        (frame.row_kind == "system")
        & (frame.evidence_class == "probabilistic_candidate")
    ]
    assert set(zip(candidates.nickname, candidates.object_id, strict=True)) == {
        ("freya", "197030881733398302"),
        ("freya", "197040882212782495"),
        ("wilhelm", "194453151328186646"),
    }
    assert not candidates.candidate_science_admitted.astype(bool).any()
    assert not candidates.budget_eligible.astype(bool).any()
    freya = candidates[candidates.nickname == "freya"]
    assert freya.candidate_foreground_probability.between(0.0, 1.0).all()


def test_plot_loader_keeps_all_twelve_panels_and_separate_evidence(tmp_path: Path) -> None:
    path = tmp_path / "grid.csv"
    build_frame().to_csv(path, index=False)
    foregrounds, roster = _load(str(path))
    assert len(roster) == 12
    assert set(meta["redshift_class"] for meta in roster.values()) == {
        "established",
        "inferred_dm_z",
    }
    assert set(foregrounds.evidence_class) == {
        "confirmed_system",
        "probabilistic_candidate",
    }
    assert not any(
        row["frb_name"] == "FRB 20240122A"
        for _, row in foregrounds.iterrows()
    )


@__import__("pytest").mark.skipif(not __import__("pathlib").Path("foregrounds/census/data/frozen_census/bursts.csv").exists(), reason="Faber2026 manuscript fixtures moved to the analysis repository")
def test_geometry_uses_corrected_galaxy_or_sourced_cluster_quantities() -> None:
    frame = build_frame()
    drawn = frame[(frame.row_kind == "system") & (frame.geometry_status == "pass")]
    halos = drawn[drawn.system_type == "halo"]
    clusters = drawn[drawn.system_type == "cluster"]
    assert (halos.radius_definition == "R200c").all()
    assert (clusters.radius_definition == "R500c_catalog").all()
    assert np.isfinite(halos.radius_kpc).all() and (halos.radius_kpc > 0).all()
    assert np.isfinite(halos.mass_msun).all() and (halos.mass_msun > 0).all()
    assert np.isfinite(clusters.radius_kpc).all() and (clusters.radius_kpc > 0).all()
    assert np.isfinite(clusters.mass_msun).all() and (clusters.mass_msun > 0).all()


@__import__("pytest").mark.skipif(not __import__("pathlib").Path("foregrounds/census/data/frozen_census/bursts.csv").exists(), reason="Faber2026 manuscript fixtures moved to the analysis repository")
def test_budget_flag_is_overlay_not_admission_rule() -> None:
    frame = build_frame()
    drawn = frame[(frame.row_kind == "system") & (frame.geometry_status == "pass")]
    assert (~drawn.budget_eligible.astype(bool)).any()
    assert drawn.budget_eligible.astype(bool).any()


def test_pdf_is_byte_identical_across_processes_without_timestamp_env(tmp_path: Path) -> None:
    halo_csv = tmp_path / "grid.csv"
    build_frame().to_csv(halo_csv, index=False)
    script = Path(__file__).parents[1] / "visualization" / "sightline_halo_grid.py"
    env = os.environ.copy()
    env.pop("SOURCE_DATE_EPOCH", None)
    outputs = []
    for name in ("first", "second"):
        out_dir = tmp_path / name
        subprocess.run(
            [
                sys.executable,
                str(script),
                "--halo-csv",
                str(halo_csv),
                "--out-dir",
                str(out_dir),
            ],
            check=True,
            capture_output=True,
            env=env,
            text=True,
        )
        outputs.append((out_dir / "sightline_halo_grid.pdf").read_bytes())
        time.sleep(1.1)

    assert outputs[0] == outputs[1]


def test_generator_refuses_manuscript_output_directory(tmp_path: Path) -> None:
    halo_csv = tmp_path / "grid.csv"
    build_frame().to_csv(halo_csv, index=False)
    script = Path(__file__).parents[1] / "visualization" / "sightline_halo_grid.py"
    manuscript_dir = Path(__file__).parents[3] / "figures"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--halo-csv",
            str(halo_csv),
            "--out-dir",
            str(manuscript_dir),
        ],
        capture_output=True,
        env=os.environ.copy(),
        text=True,
    )
    assert result.returncode != 0
    assert "promotion targets" in result.stderr


def test_review_candidate_refuses_output_outside_declared_staging(tmp_path: Path) -> None:
    script = Path(__file__).parents[1] / "visualization" / "sightline_halo_grid.py"
    canonical = Path(__file__).parents[1] / "census" / "data" / "sightline_halo_grid.csv"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--halo-csv",
            str(canonical),
            "--out-dir",
            str(tmp_path),
            "--review-candidate",
        ],
        capture_output=True,
        env=os.environ.copy(),
        text=True,
    )
    assert result.returncode != 0
    assert "declared staging directory" in result.stderr


def test_review_candidate_refuses_noncanonical_input(tmp_path: Path) -> None:
    altered = tmp_path / "altered.csv"
    build_frame().to_csv(altered, index=False)
    script = Path(__file__).parents[1] / "visualization" / "sightline_halo_grid.py"
    staging = (
        Path(__file__).parents[2]
        / "figure_review"
        / "artifacts"
        / "staging"
        / "fig3_halo_grid"
        / "figures"
    )
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--halo-csv",
            str(altered),
            "--out-dir",
            str(staging),
            "--review-candidate",
        ],
        capture_output=True,
        env=os.environ.copy(),
        text=True,
    )
    assert result.returncode != 0
    assert "canonical Figure 3 input" in result.stderr
