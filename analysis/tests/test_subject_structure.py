from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUBJECTS = {
    "observations",
    "associations",
    "dispersion",
    "scattering",
    "scintillation",
    "foregrounds",
    "energetics",
    "polarization",
}
RETIRED_ROOTS = {
    "campaigns",
    "dm-joint-phase-v2",
    "provisional_propagation",
    "scintillation-summary",
    "v3_energetics",
}


def test_canonical_subjects_have_documented_interfaces():
    for subject in SUBJECTS:
        readme = ROOT / subject / "README.md"
        assert readme.is_file(), f"{subject} lacks README.md"
        text = readme.read_text()
        for section in ("data", "methods", "results", "figures", "tests", "studies"):
            assert f"`{section}/`" in text, f"{subject} omits {section}/ from its interface"


def test_ambiguous_legacy_roots_are_retired():
    present = sorted(name for name in RETIRED_ROOTS if (ROOT / name).exists())
    assert present == []
