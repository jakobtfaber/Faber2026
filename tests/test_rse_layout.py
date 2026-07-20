"""Layout guards for docs/rse/ top-level taxonomy.

Collected by `make test-science` via `pytest tests`.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RSE = ROOT / "docs" / "rse"
SPECS = RSE / "specs"

ALLOWED_ROOT_FILES = {RSE / "README.md"}
ALLOWED_ROOT_DIRS = {
    "control",
    "protocols",
    "certificates",
    "ops",
    "wayfinder",
    "specs",
    "decks",
    "patches",
}

FORBIDDEN_TREES = {
    ROOT / "docs" / "superpowers",
    RSE / "claude-science",
}

ALLOWED_SPECS_DIRS = {
    "research",
    "plan",
    "experiment",
    "implement",
    "validation",
    "handoff",
    "decision",
    "runbook",
    "dm",
    "notes",
}

ALLOWED_DECK_STRANDS = {"dm", "scintillation", "budget", "closeouts"}


def test_rse_root_only_readme_and_role_dirs():
    loose = [p for p in RSE.iterdir() if p.is_file() and p not in ALLOWED_ROOT_FILES]
    assert loose == [], (
        "loose files at docs/rse/ root (only README.md allowed):\n"
        + "\n".join(p.name for p in sorted(loose))
    )
    dirs = {p.name for p in RSE.iterdir() if p.is_dir()}
    unexpected = sorted(dirs - ALLOWED_ROOT_DIRS)
    assert unexpected == [], (
        "unexpected dirs at docs/rse/ root:\n" + "\n".join(unexpected)
    )


def test_specs_contains_only_markdown():
    non_md = sorted(
        p for p in SPECS.rglob("*") if p.is_file() and p.suffix != ".md"
    )
    assert non_md == [], (
        "docs/rse/specs/ must contain only .md files; found:\n"
        + "\n".join(str(p.relative_to(ROOT)) for p in non_md)
    )


def test_specs_prefix_dirs_only():
    loose = sorted(SPECS.glob("*.md"))
    allowed = {SPECS / "README.md"}
    unexpected = [p for p in loose if p not in allowed]
    assert unexpected == [], (
        "loose markdown at docs/rse/specs/ root:\n"
        + "\n".join(p.name for p in unexpected)
    )
    dirs = {p.name for p in SPECS.iterdir() if p.is_dir()}
    unexpected_dirs = sorted(dirs - ALLOWED_SPECS_DIRS)
    assert unexpected_dirs == [], (
        "unexpected specs/ subdirs:\n" + "\n".join(unexpected_dirs)
    )


def test_decks_nested_under_strands():
    """Campaign dirs must sit under a strand, not directly under decks/."""
    unexpected = sorted(
        p.name
        for p in (RSE / "decks").iterdir()
        if p.is_dir() and p.name not in ALLOWED_DECK_STRANDS and p.name != ".DS_Store"
    )
    # Allow only strand folders (+ ignore junk files at decks root)
    files = [p.name for p in (RSE / "decks").iterdir() if p.is_file() and p.name != ".DS_Store"]
    assert unexpected == [], (
        "campaign dirs must nest under decks/{dm,scintillation,budget,closeouts}/:\n"
        + "\n".join(unexpected)
    )
    assert files == [], f"unexpected files at decks/ root: {files}"


def test_forbidden_docs_trees_absent():
    present = sorted(str(p.relative_to(ROOT)) for p in FORBIDDEN_TREES if p.exists())
    assert present == [], "deleted non-authority trees must stay gone:\n" + "\n".join(present)


def test_docs_root_only_rse():
    """Under docs/, only docs/rse/ is allowed (no loose referee markdown)."""
    docs = ROOT / "docs"
    if not docs.is_dir():
        return
    loose_md = sorted(p.name for p in docs.glob("*.md"))
    assert loose_md == [], (
        "loose markdown at docs/ root (fold into docs/rse/ops/):\n"
        + "\n".join(loose_md)
    )
    dirs = {p.name for p in docs.iterdir() if p.is_dir() and p.name != ".DS_Store"}
    unexpected = sorted(dirs - {"rse"})
    assert unexpected == [], (
        "unexpected dirs under docs/ (only rse/ allowed):\n" + "\n".join(unexpected)
    )