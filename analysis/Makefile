# Faber2026 manuscript build. Mirrors what Overleaf does (latexmk + bibtex).
MAIN := main
UV ?= uv

.PHONY: all clean watch test-science

all: $(MAIN).pdf

$(MAIN).pdf: $(MAIN).tex auth.tex sections/*.tex bib/refs.bib
	latexmk -pdf -interaction=nonstopmode -halt-on-error $(MAIN).tex

watch:
	latexmk -pdf -pvc -interaction=nonstopmode $(MAIN).tex

clean:
	latexmk -C
	rm -f $(MAIN).bbl

# Root manuscript/provenance tests use the pinned FLITS environment so the
# parent repo and CI exercise the same (super-repo commit, submodule pin) pair.
test-science:
	$(UV) run --project pipeline --frozen python -m pytest -q -ra \
		--strict-config --strict-markers tests
	bash tests/test_journal_append.sh
