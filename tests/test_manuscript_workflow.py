from pathlib import Path
from unittest import TestCase, main

WORKFLOW = Path(__file__).parents[1] / ".github/workflows/manuscript-provenance.yml"
MAKEFILE = Path(__file__).parents[1] / "Makefile"


class ManuscriptWorkflow(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = WORKFLOW.read_text()

    def test_prose_only_route_skips_full_provenance(self) -> None:
        self.assertIn("prose-only=$prose_only", self.text)
        self.assertIn("if: needs.changes.outputs.prose-only != 'true'", self.text)

    def test_focused_lane_checks_claims_paths_and_compiles(self) -> None:
        manuscript = self.text.split("  manuscript:", 1)[1].split(
            "  provenance:", 1
        )[0]
        self.assertIn("make check-manuscript", manuscript)
        self.assertIn("python3 -m unittest discover", manuscript)
        self.assertIn("xu-cheng/latex-action@", manuscript)

    def test_focused_claim_check_does_not_run_full_registry_validation(self) -> None:
        target = MAKEFILE.read_text().split("check-manuscript:", 1)[1].split(
            "check-provenance:", 1
        )[0]
        self.assertIn("check_claim_anchors.py", target)
        self.assertNotIn("--validate", target)

    def test_parent_watches_one_stable_analysis_verdict(self) -> None:
        pinned = self.text.split("  pinned-analysis-tests:", 1)[1].split(
            "  required:", 1
        )[0]
        self.assertIn("gh run watch", pinned)
        self.assertIn('.name == "analysis-ci"', pinned)
        self.assertNotIn("head_branch", pinned)
        self.assertNotIn("dualband-one-to-one", pinned)


if __name__ == "__main__":
    main()
