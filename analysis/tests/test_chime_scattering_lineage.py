import numpy as np

from scripts.check_chime_scattering_lineage import profile_metrics, run


def _profile(center: int) -> np.ndarray:
    x = np.arange(1000, dtype=float)
    rng = np.random.default_rng(20260904)
    return rng.normal(0.0, 1.0, x.size) + 20.0 * np.exp(
        -0.5 * ((x - center) / 8.0) ** 2
    )


def test_centered_profile_passes_pre_registered_invariants() -> None:
    metrics = profile_metrics(_profile(500))

    assert metrics["verdict"] == "pass"
    assert metrics["edge_hot_count"] == 0
    assert 400 < metrics["centroid_bin"] < 600


def test_wrapped_edge_signal_fails() -> None:
    profile = _profile(500)
    profile[:8] += 30.0

    metrics = profile_metrics(profile)

    assert metrics["verdict"] == "fail"
    assert metrics["edge_hot_count"] > 0


def test_off_center_signal_fails() -> None:
    metrics = profile_metrics(_profile(300))

    assert metrics["verdict"] == "fail"
    assert metrics["edge_hot_count"] == 0
    assert metrics["centroid_bin"] < 400


def test_no_detected_burst_is_inconclusive_without_false_centering_claim() -> None:
    metrics = profile_metrics(np.zeros(1000))

    assert metrics["verdict"] == "fail"
    assert metrics["reasons"] == ["no-burst-above-5sigma"]


def _write_cubes(roots, count: int = 12) -> None:
    cube = np.tile(_profile(500), (4, 1)).astype(np.float32)
    for root in roots:
        root.mkdir()
        for index in range(count):
            filename = f"test{index}_chime_I_1_0000_32000b_cntr_bpc.npy"
            np.save(root / filename, cube)


def test_run_binds_identical_copies_by_filename_hash_and_root(tmp_path) -> None:
    roots = (tmp_path / "first", tmp_path / "second")
    _write_cubes(roots)

    result = run(roots)

    assert result["summary"]["cube_count"] == 24
    assert result["summary"]["pair_count"] == 12
    assert result["summary"]["malformed_pair_count"] == 0
    assert result["summary"]["topology_error_count"] == 0
    assert result["summary"]["all_24_pass"] is True


def test_duplicate_root_cannot_false_pass(tmp_path) -> None:
    root = tmp_path / "only"
    _write_cubes((root,))

    result = run((root, root))

    assert result["summary"]["all_24_pass"] is False
    assert "roots-not-distinct" in result["topology_errors"]
    assert result["summary"]["malformed_pair_count"] == 12


def test_three_roots_with_24_files_cannot_false_pass(tmp_path) -> None:
    roots = (tmp_path / "first", tmp_path / "second", tmp_path / "third")
    _write_cubes(roots, count=8)

    result = run(roots)

    assert result["summary"]["cube_count"] == 24
    assert result["summary"]["all_24_pass"] is False
    assert "expected-exactly-two-roots" in result["topology_errors"]
    assert "expected-exactly-twelve-filenames" in result["topology_errors"]


def test_missing_copy_is_malformed(tmp_path) -> None:
    roots = (tmp_path / "first", tmp_path / "second")
    _write_cubes((roots[0],))
    _write_cubes((roots[1],), count=11)

    result = run(roots)

    assert result["summary"]["all_24_pass"] is False
    assert result["summary"]["malformed_pair_count"] == 1


def test_hash_mismatch_is_malformed(tmp_path) -> None:
    roots = (tmp_path / "first", tmp_path / "second")
    _write_cubes(roots)
    mismatch = roots[1] / "test0_chime_I_1_0000_32000b_cntr_bpc.npy"
    cube = np.load(mismatch)
    cube[0, 0] += 1
    np.save(mismatch, cube)

    result = run(roots)

    assert result["summary"]["all_24_pass"] is False
    assert result["summary"]["malformed_pair_count"] == 1
    assert result["pairs"][0]["hashes_match"] is False
