import json
import importlib.util
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_review_module():
    path = ROOT / "scripts/figure_review.py"
    spec = importlib.util.spec_from_file_location("figure_review_tool", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_figure_approval_gate() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/figure_review.py", "verify"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_review_slots_are_unique_and_cover_requested_families() -> None:
    config = json.loads((ROOT / "figure_review/slots.json").read_text())
    families = {group["family"] for group in config["groups"]}
    assert families == {
        "gallery",
        "association",
        "scintillation-summary",
        "scintillation-acf",
        "chime-scintillation-acf",
        "joint-model",
        "codetection-triptych",
        "scintillation-qualification",
    }


def test_new_batch_can_select_one_stable_candidate() -> None:
    module = load_review_module()
    parsed = module.parser().parse_args(
        [
            "new-batch",
            "example",
            "--title",
            "example",
            "--pipeline-revision",
            "deadbeef",
            "--only",
            "fig6-scint-summary",
            "--only-family",
            "chime-scintillation-acf",
        ]
    )
    assert parsed.candidate == ["fig6-scint-summary"]
    assert parsed.only_family == ["chime-scintillation-acf"]


def test_gate_rejects_unapproved_protected_inclusion() -> None:
    module = load_review_module()
    target = "figures/codetection_data_grid.pdf"
    errors = module.approval_errors(
        rf"\includegraphics{{{target}}}",
        {target: "fig1-gallery"},
        {},
    )
    assert errors == [
        "protected figure is included without approval: fig1-gallery "
        "(figures/codetection_data_grid.pdf)"
    ]


def test_approval_receipts_are_hash_pinned() -> None:
    receipts = ROOT / "figure_review/approval_receipts"
    if not receipts.exists():
        return
    for path in receipts.glob("*.json"):
        receipt = json.loads(path.read_text())
        assert receipt["decision"]["status"] == "approved"
        assert receipt["decision"]["reviewer_role"] == "manuscript_owner"
        assert receipt["candidate_sha256"] == receipt["promoted_sha256"]
