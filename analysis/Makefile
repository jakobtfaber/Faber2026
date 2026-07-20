# Faber2026 manuscript build. Mirrors what Overleaf does (latexmk + bibtex).
MAIN := main
UV ?= uv

.PHONY: all clean watch test-science check-state

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
# Control-state drift/contradiction/rules gate (stdlib only, no submodule env).
# --offline keeps CI hermetic; run `python3 scripts/sync_state.py --check`
# locally for the live stored<->GitHub contradiction pass.
check-state:
	python3 scripts/sync_state.py --check --offline

test-science: check-state
	$(UV) run --project pipeline --frozen python -m pytest -q -ra \
		--strict-config --strict-markers tests
	python3 scripts/figure_review.py verify
	bash tests/test_journal_append.sh

# Repo knowledge base (docs, tickets, git, code, refs). See docs/rse/knowledge-base.md.
.PHONY: kb-index kb-refs-sync
kb-index:
	python3 scripts/kb index

kb-refs-sync:
	python3 scripts/kb_refs_sync.py
	python3 scripts/kb index --source refs
