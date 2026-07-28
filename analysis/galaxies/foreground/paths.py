"""Canonical paths for the foreground analysis housed in Faber2026-analysis."""

from pathlib import Path


ANALYSIS_ROOT = Path(__file__).resolve().parents[2]
FOREGROUND_ROOT = ANALYSIS_ROOT / "foregrounds"
CENSUS_ROOT = FOREGROUND_ROOT / "studies" / "census"
DATA_DIR = CENSUS_ROOT / "data"
BUDGET_DATA = CENSUS_ROOT / "budget_table_data.json"
FOREGROUND_TABLE_DATA = CENSUS_ROOT / "foreground_table_data.json"
RESULTS_ROOT = FOREGROUND_ROOT / "results"
