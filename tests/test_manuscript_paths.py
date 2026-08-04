from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main

from scripts.check_manuscript_paths import validate


class ManuscriptPathChecks(TestCase):
    def root(self, manuscript: str) -> tuple[TemporaryDirectory, Path]:
        temporary = TemporaryDirectory()
        root = Path(temporary.name)
        (root / "sections").mkdir()
        (root / "analysis" / "results").mkdir(parents=True)
        (root / "main.tex").write_text(manuscript)
        return temporary, root

    def test_accepts_the_single_repository_and_tracked_analysis_path(self) -> None:
        temporary, root = self.root(
            r"\url{https://github.com/jakobtfaber/Faber2026} "
            r"\texttt{analysis/results/}"
        )
        self.addCleanup(temporary.cleanup)
        self.assertEqual(validate(root), [])

    def test_rejects_extra_repository_urls(self) -> None:
        temporary, root = self.root(
            r"\url{https://github.com/jakobtfaber/Faber2026} "
            r"\url{https://github.com/jakobtfaber/retired}"
        )
        self.addCleanup(temporary.cleanup)
        self.assertIn("manuscript GitHub URLs must be exactly", validate(root)[0])

    def test_rejects_missing_analysis_paths(self) -> None:
        temporary, root = self.root(
            r"\url{https://github.com/jakobtfaber/Faber2026} "
            r"\texttt{analysis/missing/}"
        )
        self.addCleanup(temporary.cleanup)
        self.assertEqual(
            validate(root),
            ["manuscript analysis path does not exist: analysis/missing/"],
        )

    def test_resolves_tex_escaped_analysis_paths(self) -> None:
        temporary, root = self.root(
            r"\url{https://github.com/jakobtfaber/Faber2026} "
            r"\texttt{analysis/results/file\_name.py}"
        )
        self.addCleanup(temporary.cleanup)
        (root / "analysis/results/file_name.py").touch()
        self.assertEqual(validate(root), [])


if __name__ == "__main__":
    main()
