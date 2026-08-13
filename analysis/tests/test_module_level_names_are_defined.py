"""A module-level name a file never binds makes that file unimportable.

Thirty-five scripts under `scattering/studies/joint-refits/` computed their
repository root with `Path(__file__)` while importing `os` and `sys` but never
`pathlib`, so each raised `NameError: name 'Path' is not defined` before any of
its own code ran. The expression arrived in a migration that replaced a
hard-coded `dsa110-FLITS` path; the import it needed did not arrive with it.

Nothing caught it because `[tool.ruff] extend-exclude` lists `*/studies/*`, so
the linter that reports exactly this (`F821`) never reads the tree the defect
lives in. This check is deliberately independent of that setting.

Scope is import time only — a name used inside a function body is a runtime
question about that call path, not an import-time break, and the reference
trees under `scintillation/studies/reference_analysis/` carry many of those by
design. A class body is import-time code and is covered; see
`_ModuleLevelScan` for what that costs and for the one gap left open.
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

# Nodes that bind a name through a plain string attribute rather than an
# `ast.Name`, so walking their children would never see the binding.
CAPTURES = {
    ast.ExceptHandler: "name",
    ast.MatchAs: "name",
    ast.MatchStar: "name",
    ast.MatchMapping: "rest",
}

# PEP 695 type parameters bind the same way — through a string attribute — but
# only inside the definition they head, so they are scoped rather than bound.
TYPE_PARAMETERS = (ast.TypeVar, ast.ParamSpec, ast.TypeVarTuple)

# Node type -> handler name on `_ModuleLevelScan`. Every handler takes
# `(node, scoped)` so `walk` can call any of them without a branch; a handler
# that has no use for `scoped` still accepts it.
HANDLERS = {
    **dict.fromkeys(SCOPES, "_definition"),
    **dict.fromkeys(COMPREHENSIONS, "_comprehension"),
    ast.Import: "_import",
    ast.ImportFrom: "_import_from",
    ast.TypeAlias: "_type_alias",
    ast.AnnAssign: "_annotated_assignment",
    ast.Name: "_name",
}


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

    Function bodies are skipped: their names resolve at call time, not import
    time. A class body is not skipped — it runs on import like any other
    module-level statement, so `class Config: root = Path(".")` is an
    import-time `NameError` — but it binds into the class rather than the
    module, so its bindings are held in a nested scan and only its unresolved
    loads reach the enclosing scope.

    Comprehension targets bind inside their own scope, so a `for p in ...`
    inside a generator must not count as a module-level load — which is
    precisely the shape of the expression this test was written for.

    `scoped` carries the comprehension-local names visible at each node, and
    is empty everywhere outside a comprehension.

    Known gap: annotations, both in a signature and on a variable. `def f(x:
    Missing)` and `x: Missing = 1` are import-time `NameError`s on Python 3.12
    and 3.13 but not on 3.14, where PEP 649 defers evaluation, and not on any
    version under `from __future__ import annotations`, which live modules
    under `analysis/` already carry. `requires-python = ">=3.12"` admits all
    of those, so reporting an annotation would name modules that import
    cleanly. A false positive gets a tree-wide check deleted rather than
    fixed, so annotations are skipped and this gap is the deliberate cost.

    PEP 695 type parameters are handled rather than skipped: `class
    Registry[T](list[T])` binds `T` for the bases that follow it, and both a
    parameter's bound and a `type` alias value are lazily evaluated.
    """

    def __init__(self) -> None:
        self.bound: set[str] = set()
        self.loaded: set[str] = set()
        self.star = False

    def walk(self, node: ast.AST, scoped: frozenset[str]) -> None:
        """Dispatch one node to its handler, `_descend` for anything unlisted.

        A table rather than an `isinstance` chain: every entry is a concrete
        `ast` node class, none of which is subclassed, so exact-type lookup
        decides the same cases a chain would while keeping this method one
        branch wide as handlers are added.
        """
        handler = getattr(self, HANDLERS.get(type(node), "_descend"))
        handler(node, scoped)

    def _definition(self, node: ast.AST, scoped: frozenset[str]) -> None:
        # The definition itself binds a name in the enclosing scope. A function
        # body waits for a call; a class body runs now, so it is walked below.
        if not isinstance(node, ast.Lambda):
            self.bound.add(node.name)
        inner = scoped | self._type_parameters(node)
        for expression in self._evaluated_at_definition(node):
            self.walk(expression, inner)
        if isinstance(node, ast.ClassDef):
            self._class_body(node, inner)

    @staticmethod
    def _type_parameters(node: ast.AST) -> frozenset[str]:
        """Names PEP 695 type parameters bind inside the definition they head.

        `class Registry[T](list[T])` resolves `T` from the parameter list, not
        from the module, so `T` has to be visible while the bases are walked.
        Nothing inside `type_params` is itself walked: a parameter's bound and
        default are lazily evaluated, so they are not import-time loads.
        """
        return frozenset(
            parameter.name
            for parameter in getattr(node, "type_params", [])
            if isinstance(parameter, TYPE_PARAMETERS)
        )

    def _type_alias(self, node: ast.TypeAlias, scoped: frozenset[str]) -> None:
        """`type Alias[T] = list[T]` binds the alias; the value is lazy.

        PEP 695 defers the value until the alias is resolved, so a name used
        there is never an import-time load.
        """
        self.bound.add(node.name.id)

    def _annotated_assignment(self, node: ast.AnnAssign, scoped: frozenset[str]) -> None:
        """Walk the target and value; the annotation is the documented gap.

        `x: Missing = 1` imports cleanly under `from __future__ import
        annotations`, which live modules under `analysis/` already carry, and
        from Python 3.14 without it. Reading the annotation as an import-time
        load would report modules that import fine — the same interpreter split
        that keeps signature annotations out of `_evaluated_at_definition`.

        The target is skipped only for a bare name with no value. `x: int`
        records an annotation, binding nothing and evaluating nothing, but
        `obj.attr: int` and `d["k"]: int` still evaluate `obj` and `d` at
        import — so guarding on `node.value` alone would drop a real load.
        """
        if isinstance(node.target, ast.Name) and node.value is None:
            return
        self.walk(node.target, scoped)
        if node.value is not None:
            self.walk(node.value, scoped)

    def _class_body(self, node: ast.ClassDef, scoped: frozenset[str]) -> None:
        """Walk a class body: its loads are the enclosing scope's, its binds are not.

        `class Config: root = Path(".")` raises `NameError` on import, so the
        loads belong here. `class Config: Path = 1` binds a class attribute and
        must not mask a missing module-level `Path`, so the nested scan keeps
        the bindings and only unresolved loads escape.
        """
        inner = _ModuleLevelScan()
        for statement in node.body:
            inner.walk(statement, scoped)
        self.loaded |= inner.loaded - inner.bound
        self.star = self.star or inner.star

    @staticmethod
    def _evaluated_at_definition(node: ast.AST) -> list[ast.AST]:
        """Decorators, bases, class keywords and defaults all run at import time.

        `class Chunk(Enum)` and `def load(root=Path("."))` raise `NameError` on
        import just as surely as a bare `Path(__file__)` does, so they belong to
        the enclosing scope's loads even though a function body they head does
        not.
        """
        args = getattr(node, "args", None)
        defaults = [*args.defaults, *filter(None, args.kw_defaults)] if args else []
        return [
            *getattr(node, "decorator_list", []),
            *getattr(node, "bases", []),
            *(keyword.value for keyword in getattr(node, "keywords", [])),
            *defaults,
        ]

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

    def _import(self, node: ast.Import, scoped: frozenset[str]) -> None:
        # `import a.b` binds `a`, not `a.b`.
        for alias in node.names:
            self.bound.add(alias.asname or alias.name.split(".")[0])

    def _import_from(self, node: ast.ImportFrom, scoped: frozenset[str]) -> None:
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
        capture = CAPTURES.get(type(node))
        if capture and getattr(node, capture):
            self.bound.add(getattr(node, capture))
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


def test_a_definition_header_is_import_time_code(tmp_path: Path) -> None:
    """A class base or a default value runs on import; only the body waits."""
    header = tmp_path / "header.py"
    header.write_text(
        'class Chunk(Enum):\n    pass\ndef load(root=Path(".")):\n    return Missing(root)\n'
    )
    # `Missing` is inside the body, so it is a call-time question, not this one.
    assert undefined_module_level_names(header) == {"Enum", "Path"}


def test_a_class_body_is_import_time_code(tmp_path: Path) -> None:
    """A class body runs on import, so an unbound name in one is a real break."""
    body = tmp_path / "body.py"
    body.write_text('class Config:\n    root = Path(".")\n')
    assert undefined_module_level_names(body) == {"Path"}


def test_a_class_attribute_does_not_bind_at_module_level(tmp_path: Path) -> None:
    """Class-local bindings must not mask a genuinely missing module-level name."""
    masked = tmp_path / "masked.py"
    masked.write_text('class Config:\n    Path = 1\n\nROOT = Path(".")\n')
    # The class attribute is `Config.Path`; the module-level call still breaks.
    assert undefined_module_level_names(masked) == {"Path"}

    method = tmp_path / "method.py"
    method.write_text('class Config:\n    def resolve(self):\n        return Missing(".")\n')
    # A method body is still call-time, even inside an import-time class body.
    assert undefined_module_level_names(method) == set()


def test_an_annotation_is_never_an_import_time_load(tmp_path: Path) -> None:
    """A module that imports cleanly must never be reported.

    Under `from __future__ import annotations` both of these are strings at
    import; on Python 3.14 they are strings without the future import too.
    """
    annotated = tmp_path / "annotated.py"
    annotated.write_text(
        "from __future__ import annotations\n"
        "\n"
        "x: Missing = 1\n"
        "\n"
        "class C:\n"
        "    y: AlsoMissing = 2\n"
        "\n"
        "def f(z: StillMissing) -> AlsoStillMissing:\n"
        "    return z\n"
    )
    assert undefined_module_level_names(annotated) == set()

    # The value beside an annotation is ordinary import-time code, so the gap
    # is the annotation alone rather than the whole statement.
    valued = tmp_path / "valued.py"
    valued.write_text('from __future__ import annotations\n\nx: int = Path(".")\n')
    assert undefined_module_level_names(valued) == {"Path"}


def test_a_non_name_annotation_target_is_evaluated_at_import(tmp_path: Path) -> None:
    """`obj.attr: int` evaluates `obj` even with no value; `x: int` does not."""
    attribute = tmp_path / "attribute.py"
    attribute.write_text("MissingThing.attr: int\n")
    assert undefined_module_level_names(attribute) == {"MissingThing"}

    subscript = tmp_path / "subscript.py"
    subscript.write_text('MissingMap["k"]: int\n')
    assert undefined_module_level_names(subscript) == {"MissingMap"}

    # A bare name is the one target that evaluates nothing, and annotating it
    # binds nothing either, so a later load of it is still reported.
    bare = tmp_path / "bare.py"
    bare.write_text("x: int\nY = x\n")
    assert undefined_module_level_names(bare) == {"x"}


def test_a_type_parameter_binds_inside_the_definition_it_heads(tmp_path: Path) -> None:
    """PEP 695 generics import cleanly, so none of these names is unbound."""
    generic = tmp_path / "generic.py"
    generic.write_text("class Registry[T](list[T]):\n    pass\n")
    assert undefined_module_level_names(generic) == set()

    alias = tmp_path / "alias.py"
    alias.write_text("type Pair[T] = tuple[T, T]\nVALUE: Pair = None\n")
    assert undefined_module_level_names(alias) == set()

    # The parameter is scoped to its own definition and must not leak out.
    leaked = tmp_path / "leaked.py"
    leaked.write_text("class Registry[T](list[T]):\n    pass\n\nSTRAY = T\n")
    assert undefined_module_level_names(leaked) == {"T"}


def test_a_match_capture_binds_its_name(tmp_path: Path) -> None:
    """`case [prog, *rest]` binds through a string attribute, not an `ast.Name`."""
    captured = tmp_path / "captured.py"
    captured.write_text(
        "import sys\nmatch sys.argv:\n    case [prog, *rest]:\n        print(prog, rest)\n"
    )
    assert undefined_module_level_names(captured) == set()
