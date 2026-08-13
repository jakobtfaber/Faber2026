"""A module-level name a file never binds makes that file unimportable.

Thirty-five scripts under `scattering/studies/joint-refits/` computed their
repository root with `Path(__file__)` while importing `os` and `sys` but never
`pathlib`, so each raised `NameError: name 'Path' is not defined` before any of
its own code ran. The expression arrived in a migration that replaced a
hard-coded `dsa110-FLITS` path; the import it needed did not arrive with it.

Nothing caught it because `[tool.ruff] extend-exclude` lists `*/studies/*`, so
the linter that reports exactly this (`F821`) never reads the tree the defect
lives in. This check is deliberately independent of that setting.

Scope is module level only — a name used inside a function body is a runtime
question about that call path, not an import-time break, and the reference
trees under `scintillation/studies/reference_analysis/` carry many of those by
design.
"""

import ast
import builtins
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Not live repository code: `.archive/` holds superseded trees,
# `docs/rse/specs/s1-scripts/` holds one-off experiment records kept as they
# ran, and `.venv/` is the environment `uv run` builds inside `analysis/`.
# Matches the exclusions in test_foreground_module_paths.py.
EXCLUDED = (".archive", ".venv", "docs")

BUILTINS = frozenset(dir(builtins)) | {
    "__file__",
    "__name__",
    "__doc__",
    "__package__",
    "__spec__",
    "__loader__",
    "__builtins__",
}

SCOPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)
COMPREHENSIONS = (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)


def live_python_sources() -> list[Path]:
    return [
        path
        for path in sorted(ROOT.rglob("*.py"))
        if not any(part in EXCLUDED for part in path.relative_to(ROOT).parts)
    ]


def _bound_by(node: ast.AST) -> set[str]:
    """Names a single statement or target expression binds."""
    names: set[str] = set()
    if isinstance(node, ast.Name):
        names.add(node.id)
    elif isinstance(node, (ast.Tuple, ast.List, ast.Starred)):
        for child in ast.iter_child_nodes(node):
            names |= _bound_by(child)
    return names


def _module_level_names(tree: ast.Module) -> tuple[set[str], set[str], bool]:
    """Return (bound, loaded, has_star_import) for module-level code only.

    Function and class bodies are skipped: their names resolve at call time,
    not import time. Comprehension targets bind inside their own scope, so a
    `for p in ...` inside a generator must not count as a module-level load —
    which is precisely the shape of the expression this test was written for.
    """
    bound: set[str] = set()
    loaded: set[str] = set()
    star = False

    def walk(node: ast.AST, comprehension_locals: frozenset[str]) -> None:
        nonlocal star
        if isinstance(node, SCOPES):
            # The definition itself binds a module-level name; its body does not.
            if not isinstance(node, ast.Lambda):
                bound.add(node.name)
            for decorator in getattr(node, "decorator_list", []):
                walk(decorator, comprehension_locals)
            return

        if isinstance(node, COMPREHENSIONS):
            inner = set(comprehension_locals)
            for generator in node.generators:
                # The first iterable is evaluated in the enclosing scope; the
                # targets it binds are visible to everything after it.
                walk(generator.iter, frozenset(inner))
                inner |= _bound_by(generator.target)
                for condition in generator.ifs:
                    walk(condition, frozenset(inner))
            for child in ast.iter_child_nodes(node):
                if child not in node.generators:
                    walk(child, frozenset(inner))
            return

        if isinstance(node, ast.Import):
            for alias in node.names:
                bound.add(alias.asname or alias.name.split(".")[0])
            return
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name == "*":
                    star = True
                else:
                    bound.add(alias.asname or alias.name)
            return

        if isinstance(node, ast.Name):
            if isinstance(node.ctx, ast.Load):
                if node.id not in comprehension_locals:
                    loaded.add(node.id)
            else:
                bound.add(node.id)
            return

        if isinstance(node, ast.ExceptHandler) and node.name:
            bound.add(node.name)

        for child in ast.iter_child_nodes(node):
            walk(child, comprehension_locals)

    for statement in tree.body:
        walk(statement, frozenset())
    return bound, loaded, star


def undefined_module_level_names(path: Path) -> set[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        # A file that does not parse is a different defect; py_compile and the
        # lint lane own it.
        return set()
    bound, loaded, star = _module_level_names(tree)
    if star:
        # `from x import *` can supply anything; the check cannot be exact.
        return set()
    return loaded - bound - BUILTINS


def test_no_live_module_uses_an_unbound_name_at_module_level() -> None:
    offenders = {
        str(path.relative_to(ROOT)): sorted(undefined)
        for path in live_python_sources()
        if (undefined := undefined_module_level_names(path))
    }
    assert not offenders, (
        "these modules raise NameError on import, before any of their own code runs:\n"
        + "\n".join(f"  {path}: {', '.join(names)}" for path, names in sorted(offenders.items()))
    )


def test_the_check_catches_the_defect_it_was_written_for(tmp_path: Path) -> None:
    """Guard the checker itself: the comprehension scoping is the subtle part."""
    broken = tmp_path / "broken.py"
    broken.write_text(
        "import os\n"
        'REPO = os.environ.get("X", next(str(p) for p in Path(__file__).resolve().parents\n'
        '                                if (p / "pyproject.toml").exists()))\n'
    )
    assert undefined_module_level_names(broken) == {"Path"}

    fixed = tmp_path / "fixed.py"
    fixed.write_text(
        "import os\n"
        "from pathlib import Path\n"
        'REPO = os.environ.get("X", next(str(p) for p in Path(__file__).resolve().parents\n'
        '                                if (p / "pyproject.toml").exists()))\n'
    )
    # `p` is the comprehension target, not an unbound module-level load.
    assert undefined_module_level_names(fixed) == set()
