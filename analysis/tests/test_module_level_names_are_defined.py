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


class _ModuleLevelScan:
    """Names bound and loaded by module-level code, one node kind per method.

    Function and class bodies are skipped: their names resolve at call time,
    not import time. Comprehension targets bind inside their own scope, so a
    `for p in ...` inside a generator must not count as a module-level load —
    which is precisely the shape of the expression this test was written for.

    `scoped` carries the comprehension-local names visible at each node, and
    is empty everywhere outside a comprehension.
    """

    def __init__(self) -> None:
        self.bound: set[str] = set()
        self.loaded: set[str] = set()
        self.star = False

    def walk(self, node: ast.AST, scoped: frozenset[str]) -> None:
        if isinstance(node, SCOPES):
            self._definition(node, scoped)
        elif isinstance(node, COMPREHENSIONS):
            self._comprehension(node, scoped)
        elif isinstance(node, ast.Import):
            self._import(node)
        elif isinstance(node, ast.ImportFrom):
            self._import_from(node)
        elif isinstance(node, ast.Name):
            self._name(node, scoped)
        else:
            self._descend(node, scoped)

    def _definition(self, node: ast.AST, scoped: frozenset[str]) -> None:
        # The definition itself binds a module-level name; its body does not.
        if not isinstance(node, ast.Lambda):
            self.bound.add(node.name)
        for decorator in getattr(node, "decorator_list", []):
            self.walk(decorator, scoped)

    def _comprehension(self, node: ast.AST, scoped: frozenset[str]) -> None:
        self._element(node, self._generator_scope(node, scoped))

    def _generator_scope(self, node: ast.AST, scoped: frozenset[str]) -> frozenset[str]:
        """Walk the `for ... in ... if ...` clauses; return the names they bind.

        The first iterable is evaluated in the enclosing scope; the targets it
        binds are visible to every clause after it.
        """
        inner = set(scoped)
        for generator in node.generators:
            self.walk(generator.iter, frozenset(inner))
            inner |= _bound_by(generator.target)
            for condition in generator.ifs:
                self.walk(condition, frozenset(inner))
        return frozenset(inner)

    def _element(self, node: ast.AST, scoped: frozenset[str]) -> None:
        """Walk the element expression, which sees every generator target."""
        for child in ast.iter_child_nodes(node):
            if child not in node.generators:
                self.walk(child, scoped)

    def _import(self, node: ast.Import) -> None:
        # `import a.b` binds `a`, not `a.b`.
        for alias in node.names:
            self.bound.add(alias.asname or alias.name.split(".")[0])

    def _import_from(self, node: ast.ImportFrom) -> None:
        for alias in node.names:
            if alias.name == "*":
                self.star = True
            else:
                self.bound.add(alias.asname or alias.name)

    def _name(self, node: ast.Name, scoped: frozenset[str]) -> None:
        if not isinstance(node.ctx, ast.Load):
            self.bound.add(node.id)
        elif node.id not in scoped:
            self.loaded.add(node.id)

    def _descend(self, node: ast.AST, scoped: frozenset[str]) -> None:
        if isinstance(node, ast.ExceptHandler) and node.name:
            self.bound.add(node.name)
        for child in ast.iter_child_nodes(node):
            self.walk(child, scoped)


def _module_level_names(tree: ast.Module) -> tuple[set[str], set[str], bool]:
    """Return (bound, loaded, has_star_import) for module-level code only."""
    scan = _ModuleLevelScan()
    for statement in tree.body:
        scan.walk(statement, frozenset())
    return scan.bound, scan.loaded, scan.star


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
