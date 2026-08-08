# Repository-owned Jupyter surface

This document is the repository-owned definition that the wayfinder ticket
[Choose operational ownership for paused services](../wayfinder/tickets/authority-10-choose-operational-ownership.md)
requires before any Jupyter surface may exist. That ticket, owner-ratified
2026-07-20, records that the former ad hoc Jupyter runtime is unclassified
rather than retired, that the repository owns no Jupyter environment, lock,
kernel, notebook, output policy, port, or restart command, and that agents must
not reconstruct one from shell history. The sections below name each element the
ticket enumerates, in its order, and close with the admission smoke test.

**This surface is kernel-only.** It defines a locked Python kernel that an
editor — Cursor or Visual Studio Code — attaches to. It does not define, admit,
or start a JupyterLab or Jupyter Notebook server, and it exposes no browser
port. Section 6 states what a future server surface would have to specify.

Unless a section says otherwise, every command runs from the analysis checkout
root — the directory the manuscript repository mounts at `analysis/`. Paths of
the form `analysis/…` name the same files as the manuscript checkout sees them.

## 1. Environment and lock

The surface runs in a `uv`-managed environment belonging to the checkout it
serves: `analysis/.venv` in the canonical checkout, and one environment **per
active analysis worktree** — the worktree's own `uv`-managed `.venv`, the same
environment every command and the admission smoke test in this document
resolve to. There is no alternate per-worktree notebook environment (one would
pass admission against `.venv` while the editor ran something else), and no
shared, machine-global notebook
environment, because a shared one outlives the checkout that created it and then
runs analysis code against the wrong tree.

The environment is never activated by hand and never mixed with a Conda
environment, an inherited `VIRTUAL_ENV`, or a system interpreter.

- Lock: `analysis/uv.lock` is authoritative. Resolved versions come from the
  lock, not from `pyproject.toml` ranges, and every command uses `--frozen` so
  `uv` fails rather than silently re-resolving.
- Python: pinned by `analysis/.python-version` to 3.12.13, inside the project's
  `requires-python = ">=3.12"`.
- Dependency group: `notebook`, declared in `analysis/pyproject.toml` under
  `[dependency-groups]`. Its direct members are `ipykernel` (the kernel an
  editor launches), `jupyter-client` (the kernel protocol client, imported
  directly by the admission smoke test, so it is declared rather than left
  transitive), and `jupytext` (plain-text notebook round-trip). The group is
  added by its own reviewed change; this document names it and depends on it,
  and the lock — not this document — fixes the versions.

Every invocation therefore has the form:

```bash
uv run --group notebook --frozen <command>
```

The group deliberately contains no Jupyter server. The lock covers the kernel,
which is where the computation happens; the notebook interface is the editor,
which never executes analysis code and therefore cannot change a numerical
result.

## 2. Kernel specification

**No permanent user-level kernelspec is registered.** Do not run `ipykernel
install --user`. A `--user` kernelspec embeds the absolute interpreter path of
whichever checkout registered it and then persists under
`~/Library/Jupyter/kernels/` (`~/.local/share/jupyter/kernels/` on Linux). When
that worktree is removed the kernelspec does not disappear — it silently points
at a missing or, worse, a re-created and different interpreter, and later
sessions run against the wrong environment without any error.

The kernel is specified by interpreter path instead:

- The session selects the checkout's own `.venv` interpreter **directly** in the
  editor (in Cursor and Visual Studio Code: the Python interpreter / kernel
  picker, "Select Another Kernel" → "Python Environments", then the `.venv`
  belonging to the checkout the notebook is being run for).
- Record the exact interpreter path (the output of the command below) in the
  session's own notes in its workbench directory, so a reader can tell
  afterwards which environment produced a cell's output.
- If a task-local kernelspec is ever genuinely needed — for example a tool that
  can only address a kernel by name — it is generated inside that session's
  workbench directory and pointed at with `JUPYTER_PATH`, never installed under
  the user Jupyter data directory.

Confirm which interpreter the locked environment resolves to before starting
work, and compare it with the one the editor has selected:

```bash
uv run --group notebook --frozen python -c 'import sys; print(sys.executable)'
```

The printed path must be the `.venv/bin/python` inside the checkout you are
working in — never a system, Homebrew, or Anaconda Python, and never another
worktree's `.venv`.

## 3. Notebooks

The surface serves notebooks under `~/Data/Faber2026/workbench/<slug>/` only,
where `<slug>` is a short lane name for the piece of work in hand. No notebook
under the repository checkout is part of this surface: the checkout holds
maintained, reviewed code, and a notebook in it would be an unreviewed producer
sitting inside the reviewed tree. The notebooks already tracked in the
repository are grandfathered — listed in `config/grandfathered-notebooks.txt`
and frozen there by `tests/test_notebook_policy.py` — and are explicitly
excluded from this surface: this document does not admit running them, and no
new tracked notebook may be added. Legacy workflows that instruct running a
grandfathered notebook through a Jupyter server — for example the manual
bad-channel review in `rfi/manual-bad-channels/README.md` — are therefore
currently without an admitted environment; each must either migrate to this
editor-kernel path or receive its own server-surface admission before its next
use.

Pair each notebook with a `py:percent` plain-text sibling so a reviewer can read
a diff rather than a JSON blob:

```bash
uv run --group notebook --frozen jupytext --set-formats ipynb,py:percent \
  ~/Data/Faber2026/workbench/<slug>/<notebook>.ipynb
```

For what this surface is for — exploratory, session-scoped analysis that has
not yet earned a place in maintained code — see
[`live-analysis.md`](live-analysis.md).

## 4. Data mounts

`~/Data/Faber2026/` is the data root. It is machine-local, outside Git, and
described by its own `README.md`:

| Tree               | Role in this surface                                    |
| ------------------ | ------------------------------------------------------- |
| `dsa110/`          | DSA-110 burst products — read-only input                |
| `chimefrb/`        | CHIME/FRB burst products — read-only input              |
| `results-library/` | Recorded result bytes — read-only input                 |
| `workbench/`       | Mutable session area — the only place a notebook writes |

From the notebook's point of view the three input trees are read-only: a
notebook opens files there and never writes, moves, renames, or deletes
anything in them. A notebook writes only inside its own
`workbench/<slug>/`. The materialized results library is described in
[results library pointers](../../analysis/results-library.md).

Do not create cross-instrument aliases or compatibility symlinks between
`dsa110/` and `chimefrb/`; if a path is wrong, fix the referencing code.

## 5. Generated-output policy

- Notebook outputs are never committed. Neither the `.ipynb`, its execution
  outputs, `.ipynb_checkpoints/`, nor any figure, table, or array written into
  the workbench enters the repository from this surface.
- Nothing produced in the workbench is authoritative. It is a lab-notebook page:
  evidence that someone looked, not a result of record. Its bytes are unbacked
  and may be discarded.
- A product becomes authoritative only by promotion: the computation moves into
  maintained code in this repository, is reviewed, and the product gains a row
  in [`docs/rse/control/results-registry.toml`](../control/results-registry.toml)
  with its producer, inputs, artifact, and trust state. A number that reached
  the manuscript through a notebook and not through that path has no provenance.

## 6. Bind address and port

**There is no persistent Jupyter server and no externally exposed browser
port.** Nothing in this surface listens on 8888, 8899, or any other browser
port, and no such port is reserved for it.

The kernel and its client communicate over loopback ZeroMQ sockets on ports the
kernel assigns at launch. They are ephemeral, differ on every start, and are
recorded in a per-kernel connection file under the Jupyter runtime directory
(`jupyter --runtime-dir`; `~/Library/Jupyter/runtime` on this machine). The
connection file also carries the kernel's HMAC key, so it is a secret: do not
copy it, commit it, or pass it between machines.

Admitting a JupyterLab or Notebook server would be a **new** surface requiring
its own admission under authority-10. That admission would have to specify, at
minimum: bind address `127.0.0.1`; one fixed port, stated explicitly; token or
password authentication left enabled, never disabled; and remote access by SSH
tunnel only. Never bind `0.0.0.0`, and never set
`ServerApp.allow_remote_access`.

Nothing here authorizes public exposure. Authority-10's public-edge finding
stands: public exposure requires explicit outward authorization and its own live
hostname, authentication, and access-denial checks, none of which this document
grants.

## 7. Start and stop commands

The kernel has no server to start. It starts when the editor attaches to the
selected interpreter — opening a notebook or running a cell in Cursor or Visual
Studio Code — and stops when that editor's kernel is shut down or restarted
("Restart Kernel", "Interrupt Kernel", closing the notebook). Programmatic use
starts and stops it explicitly through `jupyter_client.KernelManager`
(`km.start_kernel()` / `km.shutdown_kernel()`), which is what the admission
smoke test does.

Because nothing supervises these kernels, check for strays before and after a
session. List them, with the bracket around the first character so `pgrep -f`
does not match the shell that is running the search:

```bash
pgrep -fl '[i]pykernel_launcher'
```

No output and exit status 1 means no kernel is running. To inspect one before
deciding anything, resolve its full command line and start time:

```bash
ps -p <pid> -o pid,lstart,command
```

Stop a stray kernel by its own editor session where one exists. Only when no
session owns it, and after confirming from `ps` that it is an
`ipykernel_launcher` belonging to this project, terminate it:

```bash
kill <pid>          # then re-run the pgrep above; it must print nothing
```

Do not `kill -9` a kernel as a first step, and never terminate a process you
have not identified. Stale connection files may remain in the runtime directory
after an unclean exit; they are inert and are cleaned up by Jupyter, not by
hand. In-memory kernel state is not part of this surface and is not preserved
across a restart — save anything you need to the workbench first.

## 8. Owner

`jakobtfaber`.

The owner alone ratifies this surface, admits any future server surface, and
authorizes anything outward-facing. **Only after the owner has ratified this
surface** may an agent, within the constraints stated here, start and stop
kernels for bounded work without a further prompt; until ratification the
repository owns no runnable Jupyter surface and this document grants no
kernel-start permission. A stopped
kernel is paused, not abandoned, and stopping one authorizes no cleanup,
deletion, or retirement.

## 9. Recovery procedure

**The kernel dies or will not start.** Re-run the admission smoke test
(section 10): if it passes, the fault is in the notebook, so restart the kernel
from the editor and re-run the cells. If it fails at import, the environment and
the lock disagree — see below. If it fails to start at all, check that the
editor's selected interpreter still exists on disk.

**A kernelspec points at a deleted worktree's interpreter.** This is the failure
that the no-user-level-kernelspec rule in section 2 exists to prevent, and stale
entries registered before this document may still be present. Detect it by
listing the registered specifications and checking each recorded interpreter:

```bash
uv run --group notebook --frozen jupyter kernelspec list
```

(The locked invocation matters: a bare `jupyter` may not exist on a clean
machine, or may belong to an unrelated install outside the locked
environment.)

For any entry that looks like this project's, read its `kernel.json` and test
the first element of `argv`; a path that no longer exists — or that points into
a worktree under `~/Developer/scratch/worktrees/` that has been removed — is
stale. Do not repair it by re-registering. Select the checkout's interpreter
directly instead, per section 2. Removing someone else's kernelspec is a
destructive change to shared machine state and needs the owner's approval.

**Two checkouts disagree.** If results differ between worktrees, compare the
interpreter each session recorded in its workbench notes against
`uv run --group notebook --frozen python -c 'import sys; print(sys.executable)'`
in that checkout. A notebook attached to another worktree's `.venv` is the usual
cause.

**The lock and the environment disagree** (an import fails, or `uv` reports the
environment is out of date). Rebuild the environment from the lock:

```bash
env -u VIRTUAL_ENV -u UV_PROJECT_ENVIRONMENT uv sync --frozen --group notebook
```

Clearing an inherited `VIRTUAL_ENV` matters: `uv` will otherwise select the
wrong interpreter. `UV_PROJECT_ENVIRONMENT` must be cleared for the same
reason — when exported (the dualband make targets export it, for example) it
redirects the sync to an alternate environment while the editor keeps using
the checkout `.venv`. Never repair a failure with `uv add` or `uv lock` inside a
session — that edits the lock as a side effect. If the surface genuinely needs a
new dependency, change `pyproject.toml` and `uv.lock` in their own reviewed
pull request.

In every case, recover by re-running the commands in this document. Do not
reconstruct any part of the surface from shell history, from a previous ad hoc
server, or from an unclassified kernel found on the machine.

## 10. Admission smoke test

Admission requires a local kernel smoke test. Run it from the analysis checkout
root, naming both dependency groups explicitly rather than relying on any
default group behaviour:

```bash
uv lock --check
uv run --group test --group notebook --locked \
  python -m pytest tests/test_jupyter_surface.py -q
```

(`make test-notebook` runs exactly this. The admission gate uses `uv lock
--check` plus `--locked` — not plain `--frozen` — so a `pyproject.toml` edit
whose lock was never regenerated fails admission instead of silently testing
the old locked environment.)

The test module `tests/test_jupyter_surface.py` (added by its own reviewed
change, alongside the `notebook` dependency group) performs a real kernel
round-trip through `jupyter_client.KernelManager` — it starts a kernel, executes
`1 + 1`, asserts the reply is `2`, and shuts the kernel down — plus a `jupytext`
`py:percent` round-trip that converts a notebook to plain text and back and
compares the result. The kernel it starts is the locked interpreter of the
checkout the command runs in, which is exactly what the editor is told to
select, so a pass is evidence about the environment a session will actually use.

A pass is `pytest` exiting `0` with every test in that module passing and none
skipped. A skip is not a pass: it means the kernel or `jupytext` was
unavailable, which is exactly the condition the test exists to detect. Record
the command, its output, the resolved interpreter path, and the `uv.lock` state
in the admission receipt that authority-10 requires.

## Status

**Ratified 2026-08-07** (owner decision recorded in
[the admission ticket](../wayfinder/tickets/jupyter-surface-admission-2026-08-05.md),
receipts in
[the admission receipts](../wayfinder/tickets/jupyter-surface-admission-receipts-20260806.md)).
The kernel-only surface is admitted: agents may start and stop a kernel for
bounded local work under this document's own start, stop, and recovery
instructions. Admission covers exactly this definition — a JupyterLab or
notebook server, or any outward exposure, remains a separate and later
admission per authority-10's outward-authorization requirement.
