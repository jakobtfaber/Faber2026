"""Layout guards for docs/rse/specs/.

Full docs/rse/ taxonomy guards live in tests/test_rse_layout.py.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPECS = ROOT / "docs" / "rse" / "specs"


def test_specs_contains_only_markdown():
    non_md = sorted(
        p for p in SPECS.rglob("*") if p.is_file() and p.suffix != ".md"
    )
    assert non_md == [], (
        "docs/rse/specs/ must contain only .md files; found:\n"
        + "\n".join(str(p.relative_to(ROOT)) for p in non_md)
    )


def test_specs_root_has_no_loose_markdown():
    loose = sorted(SPECS.glob("*.md"))
    allowed = {SPECS / "README.md"}
    unexpected = [p for p in loose if p not in allowed]
    assert unexpected == [], (
        "loose markdown at docs/rse/specs/ root (use prefix subfolders):\n"
        + "\n".join(p.name for p in unexpected)
    )
