# Faber2026 analysis/control workspace.
MANUSCRIPT_ROOT ?= ..
MANUSCRIPT_ROOT_ABS := $(abspath $(MANUSCRIPT_ROOT))
UV ?= uv

.PHONY: check-mount check-state test test-manuscript test-slow test-replay test-external lint ci figures kb-index kb-refs-sync notes-serve notes wayfinder-plan wayfinder-status wayfinder-launch

check-mount:
	@test -f "$(MANUSCRIPT_ROOT_ABS)/main.tex" || \
		(echo "Faber2026 parent not found at $(MANUSCRIPT_ROOT_ABS)" >&2; exit 1)

check-state: check-mount
	FABER2026_ROOT="$(MANUSCRIPT_ROOT_ABS)" python3 scripts/sync_state.py --check --offline
	FABER2026_ROOT="$(MANUSCRIPT_ROOT_ABS)" python3 scripts/render_results_registry.py --validate --manuscript-root "$(MANUSCRIPT_ROOT_ABS)"
	FABER2026_ROOT="$(MANUSCRIPT_ROOT_ABS)" python3 scripts/render_results_registry.py --check

test:
	PYTHONPATH="$(CURDIR):$(CURDIR)/scripts" \
		$(UV) run --group test --frozen python -m pytest -q \
		--standalone-analysis \
		-m "not slow and not network and not external_data and not historical_replay and not integration"
	bash tests/test_journal_append.sh

test-manuscript: check-mount
	cd "$(MANUSCRIPT_ROOT_ABS)" && \
		FABER2026_ROOT="$(MANUSCRIPT_ROOT_ABS)" \
		PYTHONPATH="$(CURDIR):$(CURDIR)/scripts" \
		xargs $(UV) run --project "$(CURDIR)" --group test --frozen \
		python -m pytest -q \
		-m "not external_data and not network and not slow and not historical_replay" \
		< "$(CURDIR)/tests/manuscript_integration_files.txt"

test-slow:
	PYTHONPATH="$(CURDIR):$(CURDIR)/scripts" \
		$(UV) run --group test --frozen python -m pytest -q \
		--standalone-analysis -m "slow and not network and not external_data" \
		|| test $$? -eq 5

test-replay:
	PYTHONPATH="$(CURDIR):$(CURDIR)/scripts" \
		$(UV) run --group test --frozen python -m pytest -q \
		--standalone-analysis -m "historical_replay and not integration"

test-external:
	PYTHONPATH="$(CURDIR):$(CURDIR)/scripts" \
		$(UV) run --group test --frozen python -m pytest -q \
		--standalone-analysis --run-external-data -m "external_data"

lint:
	$(UV) run --group test --frozen python scripts/lint_changed.py

ci: lint test

figures: check-mount
	cd "$(MANUSCRIPT_ROOT_ABS)" && \
		FABER2026_ROOT="$(MANUSCRIPT_ROOT_ABS)" \
		python3 analysis/scripts/figure_flow.py regen --manuscript --clone-ok

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
