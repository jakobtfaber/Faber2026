from pathlib import Path
from re import findall
from unittest import TestCase, main

WORKFLOW = Path(__file__).parents[1] / ".github/workflows/manuscript-provenance.yml"
MAKEFILE = Path(__file__).parents[1] / "Makefile"


class ManuscriptWorkflow(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = WORKFLOW.read_text()

    def test_prose_or_analysis_pin_route_skips_full_provenance(self) -> None:
        self.assertIn("analysis|*.tex|bib/*.bib", self.text)
        self.assertIn("focused-only=$focused_only", self.text)
        self.assertIn("if: needs.changes.outputs.focused-only != 'true'", self.text)

    def test_draft_pull_requests_defer_ci_until_ready(self) -> None:
        self.assertIn("ready_for_review", self.text)
        self.assertGreaterEqual(self.text.count("draft == false"), 3)

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

    def test_provenance_lane_runs_the_whole_manuscript_test_suite(self) -> None:
        provenance = self.text.split("  provenance:", 1)[1].split(
            "  pinned-analysis-tests:", 1
        )[0]
        self.assertIn(
            "uv run --project analysis --group test --frozen pytest tests",
            provenance,
        )

    def test_every_excluded_test_still_exists(self) -> None:
        root = Path(__file__).parents[1]
        excluded = findall(
            r"--(?:ignore|deselect)=(tests/\S+?\.py)(?:::(\S+))?\s", self.text
        )
        self.assertTrue(excluded, "expected the suite step to name its exclusions")
        for module, test in excluded:
            path = root / module
            self.assertTrue(
                path.is_file(),
                f"{module} is excluded from the suite but no longer exists",
            )
            if test:
                self.assertIn(
                    f"def {test}(",
                    path.read_text(),
                    f"{module}::{test} is excluded but no longer exists",
                )

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
