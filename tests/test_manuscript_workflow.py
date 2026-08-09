from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from re import findall
from types import SimpleNamespace
from unittest import TestCase, main
from unittest.mock import patch

WORKFLOW = Path(__file__).parents[1] / ".github/workflows/manuscript-provenance.yml"
MAKEFILE = Path(__file__).parents[1] / "Makefile"


class ManuscriptWorkflow(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = WORKFLOW.read_text()

    def test_prose_or_analysis_pin_route_skips_full_provenance(self) -> None:
        self.assertIn("analysis/*|*.tex|bib/*.bib", self.text)
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
            "  required:", 1
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

    def test_analysis_suite_runs_in_repo_not_via_pin_watch(self) -> None:
        # The former pinned-analysis-tests job watched the standalone
        # repository's verdict for the submodule pointer. Since the monorepo
        # consolidation the analysis suite runs in this repository on the
        # same commit, so the watcher must stay retired and the in-repo
        # workflow must expose the stable required check name.
        self.assertNotIn("pinned-analysis-tests", self.text)
        self.assertNotIn("gh run watch", self.text)
        analysis_ci = (
            Path(__file__).parents[1] / ".github/workflows/analysis-ci.yml"
        ).read_text()
        self.assertIn("name: analysis-ci", analysis_ci)

    def test_ax_front_door_reaches_the_runner_in_its_project_environment(self) -> None:
        # figures/ax/agent.py shells out to figure_flow for every tool call.
        # It resolved the runner under the repository root, where the
        # monorepo consolidation no longer leaves one, and launched it with
        # sys.executable, which generally has no PyYAML. Nothing imports this
        # module in CI, so only an agent following the skill would find out.
        spec = spec_from_file_location(
            "_ax_front_door", Path(__file__).parents[1] / "figures/ax/agent.py"
        )
        ax = module_from_spec(spec)
        spec.loader.exec_module(ax)
        self.assertTrue(
            ax.FLOW.is_file(),
            f"the Ax front door resolves figure_flow to a missing path: {ax.FLOW}",
        )
        with patch.object(ax.subprocess, "run") as run:
            run.return_value = SimpleNamespace(returncode=0, stdout="", stderr="")
            ax.list_figures()
        argv = run.call_args.args[0]
        self.assertEqual(
            argv[:2],
            ["uv", "run"],
            f"figure_flow must be launched in the analysis project environment: {argv}",
        )
        self.assertIn("--project", argv)


if __name__ == "__main__":
    main()
