"""Repository-wide test execution contracts."""

from __future__ import annotations

from pathlib import Path

import pytest

MANUSCRIPT_INTEGRATION_FILES = {
    Path(line).name
    for line in (
        Path(__file__).with_name("manuscript_integration_files.txt").read_text().splitlines()
    )
    if line
}


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--run-external-data",
        action="store_true",
        default=False,
        help="run tests that require external scientific data",
    )
    parser.addoption(
        "--standalone-analysis",
        action="store_true",
        default=False,
        help="exclude tests whose public interface is the mounted manuscript",
    )


def pytest_ignore_collect(collection_path, config: pytest.Config) -> bool | None:
    if (
        config.getoption("--standalone-analysis")
        and collection_path.name in MANUSCRIPT_INTEGRATION_FILES
    ):
        return True
    return None


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    if config.getoption("--run-external-data"):
        return
    skip = pytest.mark.skip(reason="requires --run-external-data")
    for item in items:
        if "external_data" in item.keywords:
            item.add_marker(skip)
