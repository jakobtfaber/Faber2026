from pathlib import Path
from re import match
from unittest import TestCase, main

WORKFLOWS = Path(__file__).parents[1] / ".github/workflows"


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip())


def _fields(entries: list[str]) -> dict[str, str]:
    """Map `key: value` entries, ignoring comments and anything unkeyed."""
    fields = {}
    for entry in entries:
        entry = entry.strip()
        if entry.startswith("#") or ":" not in entry:
            continue
        key, value = entry.split(":", 1)
        fields[key.strip()] = value.split(" #", 1)[0].strip()
    return fields


def _key_path(lines: list[str], index: int) -> list[str]:
    """Return the mapping keys enclosing `lines[index]`, outermost first.

    Ancestors are found by indentation: the nearest preceding line indented
    less than the line in hand is its parent. A sequence entry (`- uses: x`)
    counts at the indentation of its dash, so keys inside a step resolve
    through it rather than past it.
    """
    path: list[str] = []
    limit = None
    for line in reversed(lines[: index + 1]):
        if not line.strip() or line.strip().startswith("#"):
            continue
        if limit is not None and _indent(line) >= limit:
            continue
        key = match(r"\s*(?:-\s+)?([\w.-]+):", line)
        if key is None:
            continue
        path.append(key.group(1))
        limit = _indent(line)
        if limit == 0:
            break
    return path[::-1]


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
        # Only a job's own `environment:` declares one. An `environment` key
        # elsewhere — a step input under `with:`, an entry under `env:` — is
        # an unrelated name that happens to collide.
        path = _key_path(lines, index)
        if len(path) != 3 or path[0] != "jobs":
            continue
        indent, inline = header.group(1), header.group(2).strip()
        if inline.startswith("{"):
            # `environment: {name: tend, deployment: false}` — flow mapping.
            fields = _fields(inline.strip("{} ").split(","))
        elif inline:
            # `environment: tend` — the scalar form always files a deployment.
            found.append((inline.split(" #", 1)[0].strip(), True))
            continue
        else:
            block = []
            for following in lines[index + 1 :]:
                if following.strip() and not following.startswith(indent + " "):
                    break
                block.append(following)
            fields = _fields(block)
        # `false`, `False`, and `FALSE` are one boolean under the YAML core
        # schema, so all three suppress the record. Any other spelling is not
        # that boolean and leaves the job reported.
        gated = fields.get("deployment") in ("false", "False", "FALSE")
        found.append((fields.get("name", ""), not gated))
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

    def test_the_parser_distinguishes_the_declaration_forms(self) -> None:
        scalar = "jobs:\n  a:\n    environment: tend  # gate only\n    steps: []\n"
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
        flow = "jobs:\n  a:\n    environment: {name: tend, deployment: false}\n"
        self.assertEqual([("tend", False)], environment_declarations(flow))
        flow_without_the_flag = "jobs:\n  a:\n    environment: {name: tend}\n"
        self.assertEqual(
            [("tend", True)], environment_declarations(flow_without_the_flag)
        )

    def test_every_yaml_spelling_of_the_false_flag_counts_as_gated(self) -> None:
        # The YAML core schema resolves `false`, `False`, and `FALSE` to the
        # same boolean, so a workflow using any of them is correctly gated and
        # must not be reported.
        for spelling in ("false", "False", "FALSE"):
            gated = (
                f"jobs:\n  a:\n    environment:\n      name: tend\n"
                f"      deployment: {spelling}\n    steps: []\n"
            )
            self.assertEqual([("tend", False)], environment_declarations(gated))
            flow = f"jobs:\n  a:\n    environment: {{name: tend, deployment: {spelling}}}\n"
            self.assertEqual([("tend", False)], environment_declarations(flow))
        # Not the boolean: a quoted string, and `true`. Both still report.
        for spelling in ("'false'", "true"):
            ungated = (
                f"jobs:\n  a:\n    environment:\n      name: tend\n"
                f"      deployment: {spelling}\n    steps: []\n"
            )
            self.assertEqual([("tend", True)], environment_declarations(ungated))

    def test_an_environment_key_outside_a_job_is_not_a_declaration(self) -> None:
        step_input = (
            "jobs:\n  a:\n    steps:\n      - uses: some/deploy@v4\n"
            "        with:\n          environment: production\n"
        )
        self.assertEqual([], environment_declarations(step_input))
        job_env = (
            "jobs:\n  a:\n    env:\n      environment: production\n    steps: []\n"
        )
        self.assertEqual([], environment_declarations(job_env))

    def test_a_commented_flag_does_not_pass_for_the_real_one(self) -> None:
        commented = (
            "jobs:\n  a:\n    environment:\n      name: tend\n"
            "      # deployment: false is what this should say\n    steps: []\n"
        )
        self.assertEqual([("tend", True)], environment_declarations(commented))


if __name__ == "__main__":
    main()
