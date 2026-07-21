# Faber2026 manuscript build. Mirrors what Overleaf does (latexmk + bibtex).
MAIN := main
UV ?= uv

.PHONY: all clean watch test-science check-state figures wayfinder-plan wayfinder-status wayfinder-launch

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

# Clone-safe embedded manuscript figures (figures/catalog.yaml).
# Needs flits conda env + pipeline uv lock. Skips fig1 / external-data nodes.
# Full manuscript set (incl. data-bound): python3 scripts/figure_flow.py regen --manuscript
# Agent runbook: figures/ax/SKILL.md
figures:
	python3 scripts/figure_flow.py regen --manuscript --clone-ok

# Repo knowledge base (docs, tickets, git, code, refs). See docs/rse/ops/knowledge-base.md.
.PHONY: kb-index kb-refs-sync
kb-index:
	python3 scripts/kb index

kb-refs-sync:
	python3 scripts/kb_refs_sync.py
	python3 scripts/kb index --source refs

# ADHD Running Notes → headless Claude Code CLI (see docs/rse/ops/running-notes/).
.PHONY: notes-serve notes
notes-serve:
	python3 scripts/running_notes.py serve

notes:
	@test -n "$(MSG)" || (echo 'Usage: make notes MSG="your running note"' >&2; exit 1)
	python3 scripts/running_notes.py submit "$(MSG)"

# Reviewed, fail-closed Wayfinder task automation. Launch requires WAVE.
wayfinder-plan:
	python3 scripts/wayfinder_controller.py plan --wave "$(or $(WAVE),first)"

wayfinder-status:
	python3 scripts/wayfinder_controller.py status

wayfinder-launch:
	@test -n "$(WAVE)" || (echo 'Usage: make wayfinder-launch WAVE=first' >&2; exit 1)
	python3 scripts/wayfinder_controller.py launch --wave "$(WAVE)"
