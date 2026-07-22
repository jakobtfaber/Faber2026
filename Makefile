# Faber2026 manuscript build and pinned analysis delegation.
MAIN := main
UV ?= uv
FABER2026_ROOT := $(CURDIR)

.PHONY: all clean watch check-state test-science figures kb-index kb-refs-sync notes-serve notes wayfinder-plan wayfinder-status wayfinder-launch

all: $(MAIN).pdf

$(MAIN).pdf: $(MAIN).tex auth.tex sections/*.tex bib/refs.bib
	latexmk -pdf -interaction=nonstopmode -halt-on-error $(MAIN).tex

watch:
	latexmk -pdf -pvc -interaction=nonstopmode $(MAIN).tex

clean:
	latexmk -C
	rm -f $(MAIN).bbl

check-state:
	FABER2026_ROOT="$(FABER2026_ROOT)" \
		python3 analysis/scripts/sync_state.py --check --offline

test-science: check-state
	FABER2026_ROOT="$(FABER2026_ROOT)" \
		PYTHONPATH="$(FABER2026_ROOT)/analysis:$(FABER2026_ROOT)/analysis/scripts" \
		$(UV) run --project pipeline --group test --frozen python -m pytest -q -ra \
		--strict-config --strict-markers analysis/tests
	FABER2026_ROOT="$(FABER2026_ROOT)" \
		python3 analysis/scripts/figure_review.py verify
	bash analysis/tests/test_journal_append.sh

figures:
	FABER2026_ROOT="$(FABER2026_ROOT)" \
		python3 analysis/scripts/figure_flow.py regen --manuscript --clone-ok

kb-index:
	$(MAKE) -C analysis kb-index MANUSCRIPT_ROOT="$(FABER2026_ROOT)"

kb-refs-sync:
	$(MAKE) -C analysis kb-refs-sync MANUSCRIPT_ROOT="$(FABER2026_ROOT)"

notes-serve:
	$(MAKE) -C analysis notes-serve MANUSCRIPT_ROOT="$(FABER2026_ROOT)"

notes:
	$(MAKE) -C analysis notes MANUSCRIPT_ROOT="$(FABER2026_ROOT)" MSG="$(MSG)"

wayfinder-plan:
	$(MAKE) -C analysis wayfinder-plan MANUSCRIPT_ROOT="$(FABER2026_ROOT)" WAVE="$(WAVE)"

wayfinder-status:
	$(MAKE) -C analysis wayfinder-status MANUSCRIPT_ROOT="$(FABER2026_ROOT)"

wayfinder-launch:
	$(MAKE) -C analysis wayfinder-launch MANUSCRIPT_ROOT="$(FABER2026_ROOT)" WAVE="$(WAVE)"
