import sys
from pathlib import Path

import tomllib

sys.path.insert(0, str(Path(__file__).parents[1]))

from scripts.fetch_provenance_commits import required_commits

REGISTRY = Path(__file__).parents[1] / "analysis/docs/rse/control/results-registry.toml"


def test_required_commits_extracts_only_local_provenance_objects() -> None:
    commits = required_commits(tomllib.loads(REGISTRY.read_text()))
    assert set(commits) == {"analysis", "manuscript"}
    assert all(len(commit) == 40 for values in commits.values() for commit in values)
    assert len(commits["analysis"]) == 8
    assert len(commits["manuscript"]) == 4
