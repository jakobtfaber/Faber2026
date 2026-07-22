# Faber2026 analysis/control workspace.
MANUSCRIPT_ROOT ?= ..
MANUSCRIPT_ROOT_ABS := $(abspath $(MANUSCRIPT_ROOT))
UV ?= uv

.PHONY: check-mount check-state test figures figure-review-status figure-review-next kb-index kb-refs-sync notes-serve notes wayfinder-plan wayfinder-status wayfinder-launch

check-mount:
	@test -f "$(MANUSCRIPT_ROOT_ABS)/main.tex" || \
		(echo "Faber2026 parent not found at $(MANUSCRIPT_ROOT_ABS)" >&2; exit 1)
	@test -d "$(MANUSCRIPT_ROOT_ABS)/pipeline" || \
		(echo "pipeline submodule not found at $(MANUSCRIPT_ROOT_ABS)/pipeline" >&2; exit 1)

check-state: check-mount
	FABER2026_ROOT="$(MANUSCRIPT_ROOT_ABS)" python3 scripts/sync_state.py --check --offline

test: check-state
	cd "$(MANUSCRIPT_ROOT_ABS)" && \
		FABER2026_ROOT="$(MANUSCRIPT_ROOT_ABS)" \
		PYTHONPATH="$(MANUSCRIPT_ROOT_ABS)/analysis:$(MANUSCRIPT_ROOT_ABS)/analysis/scripts" \
		$(UV) run --project pipeline --group test --frozen python -m pytest -q -ra \
		--strict-config --strict-markers analysis/tests
	FABER2026_ROOT="$(MANUSCRIPT_ROOT_ABS)" python3 scripts/figure_review.py verify
	bash tests/test_journal_append.sh

figures: check-mount
	cd "$(MANUSCRIPT_ROOT_ABS)" && \
		FABER2026_ROOT="$(MANUSCRIPT_ROOT_ABS)" \
		python3 analysis/scripts/figure_flow.py regen --manuscript --clone-ok

figure-review-next:
	python3 scripts/figure_review.py next

figure-review-status:
	python3 scripts/figure_review.py status

kb-index: check-mount
	FABER2026_ROOT="$(MANUSCRIPT_ROOT_ABS)" python3 scripts/kb index

kb-refs-sync: check-mount
	FABER2026_ROOT="$(MANUSCRIPT_ROOT_ABS)" python3 scripts/kb_refs_sync.py
	FABER2026_ROOT="$(MANUSCRIPT_ROOT_ABS)" python3 scripts/kb index --source refs

notes-serve:
	python3 scripts/running_notes.py serve

notes:
	@test -n "$(MSG)" || (echo 'Usage: make notes MSG="your running note"' >&2; exit 1)
	python3 scripts/running_notes.py submit "$(MSG)"

wayfinder-plan:
	python3 scripts/wayfinder_controller.py plan --wave "$(or $(WAVE),first)"

wayfinder-status:
	python3 scripts/wayfinder_controller.py status

wayfinder-launch:
	@test -n "$(WAVE)" || (echo 'Usage: make wayfinder-launch WAVE=first' >&2; exit 1)
	python3 scripts/wayfinder_controller.py launch --wave "$(WAVE)"
