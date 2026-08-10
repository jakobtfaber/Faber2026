from pathlib import Path
from re import match
from unittest import TestCase, main

WORKFLOWS = Path(__file__).parents[1] / ".github/workflows"


def environment_declarations(text: str) -> list[tuple[str, bool]]:
    """Return one (environment name, files a deployment record) pair per job.

    Parsed by hand rather than with PyYAML: the manuscript suite runs under
    the bare interpreter, which has no third-party packages available.
    """
    lines = text.splitlines()
    found: list[tuple[str, bool]] = []
    for index, line in enumerate(lines):
        header = match(r"(\s*)environment:(.*)$", line)
        if header is None:
            continue
        indent, inline = header.group(1), header.group(2).strip()
        if inline:
            # `environment: tend` — the scalar form always files a deployment.
            found.append((inline, True))
            continue
        block = []
        for following in lines[index + 1 :]:
            if following.strip() and not following.startswith(indent + " "):
                break
            block.append(following.strip())
        name = next(
            (entry.split(":", 1)[1].strip() for entry in block
             if entry.startswith("name:")),
            "",
        )
        found.append((name, "deployment: false" not in block))
    return found


class WorkflowEnvironments(TestCase):
    def test_no_job_files_a_deployment_record_for_a_credential_gate(self) -> None:
        # The `tend` environment exists to gate a credential and to restrict
        # the ref a run may carry, not to record a release. Without
        # `deployment: false` GitHub files a deployment for every run and
        # posts it on the pull request, and `tend check` reports the job.
        offenders = [
            f"{path.name}: environment '{name}'"
            for path in sorted(WORKFLOWS.glob("*.y*ml"))
            for name, deploys in environment_declarations(path.read_text())
            if deploys
        ]
        self.assertEqual([], offenders)

    def test_the_parser_sees_the_environments_that_are_declared(self) -> None:
        # Guards the assertion above against silently matching nothing if the
        # workflow layout changes.
        declared = {
            name
            for path in WORKFLOWS.glob("*.y*ml")
            for name, _ in environment_declarations(path.read_text())
        }
        self.assertIn("tend", declared)

    def test_the_parser_distinguishes_the_two_declaration_forms(self) -> None:
        scalar = "jobs:\n  a:\n    environment: tend\n    steps: []\n"
        self.assertEqual([("tend", True)], environment_declarations(scalar))
        gated = (
            "jobs:\n  a:\n    environment:\n      name: tend\n"
            "      deployment: false\n    steps: []\n"
        )
        self.assertEqual([("tend", False)], environment_declarations(gated))
        block_without_the_flag = (
            "jobs:\n  a:\n    environment:\n      name: tend\n    steps: []\n"
        )
        self.assertEqual(
            [("tend", True)], environment_declarations(block_without_the_flag)
        )


if __name__ == "__main__":
    main()
