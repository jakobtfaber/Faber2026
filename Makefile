# Faber2026 manuscript build and pinned analysis delegation.
MAIN := main
UV ?= uv
FABER2026_ROOT := $(CURDIR)

.PHONY: all clean watch check-state test-science figures figure-review-status figure-review-next kb-index kb-refs-sync notes-serve notes wayfinder-plan wayfinder-status wayfinder-launch

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
	$(MAKE) -C analysis test MANUSCRIPT_ROOT="$(FABER2026_ROOT)"

figures:
	FABER2026_ROOT="$(FABER2026_ROOT)" \
		python3 analysis/scripts/figure_flow.py regen --manuscript --clone-ok

figure-review-status:
	$(MAKE) -C analysis figure-review-status MANUSCRIPT_ROOT="$(FABER2026_ROOT)"

figure-review-next:
	$(MAKE) -C analysis figure-review-next MANUSCRIPT_ROOT="$(FABER2026_ROOT)"

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
