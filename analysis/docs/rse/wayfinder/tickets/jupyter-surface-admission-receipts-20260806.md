# Jupyter surface admission receipts — 2026-08-06

Evidence for promotion conditions 3 and 4 of
[the admission ticket](jupyter-surface-admission-2026-08-05.md). Both runs were
performed on the author's machine on 2026-08-06.

## Condition 3 — local kernel smoke test

- Machine: `jakob` (macOS 27.0, Apple Silicon)
- Command: `make test-notebook` (which runs `uv lock --check` then
  `uv run --group test --group notebook --locked python -m pytest
  tests/test_jupyter_surface.py -q`)
- Result: `2 passed in 7.90s`; exit status 0
- Interpreter: the checkout `.venv`, Python 3.12.13 (uv-managed
  cpython-3.12.13-macos-aarch64)
- ipykernel: 7.3.0
- Lock state: `uv lock --check` passed (lock unchanged)

## Condition 4 — real workbench session on the checkout interpreter

- Editor: Cursor, workspace `~/Data/Faber2026/workbench/`
- Kernel-picker entry selected: `.venv (3.12.13.final.0) (Python 3.12.13)`
  (owner-confirmed label)
- Notebook: `~/Data/Faber2026/workbench/jupyter-admission-pilot/pilot.ipynb`
- Kernel process observed:
  `.../Faber2026-analysis/.venv/bin/python -m ipykernel_launcher`
- Cell output, executed 2026-08-06:

  ```text
  machine: jakob
  interpreter: /Users/jakobfaber/Developer/repos/github.com/jakobtfaber/Faber2026-analysis/.venv/bin/python
  python: 3.12.13
  ipykernel: 7.3.0
  1 + 1 = 2
  ```

## Incident recorded during the pilot

The first pilot attempt executed on `/opt/anaconda3/bin/python` (Python
3.13.9): a stale user-level kernelspec named "Faber2026 (Python 3)" pointed at
the anaconda base interpreter. This is exactly the stale-kernelspec hazard the
surface definition forbids. The kernelspec (and a retired `flits` one) were
quarantined to `~/Data/Faber2026/_trash/stale-kernelspecs-20260806/` with
provenance, and the workbench editor settings now pin the checkout `.venv` as
the default interpreter and exclude anaconda, conda, homebrew, system, and
shared-venv environments from kernel discovery. The successful run above was
performed after that repair, through the picker path an author would use.
