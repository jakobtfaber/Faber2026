# Handoff: Readiness-board redesign — visual pass + strand-swimlane IA restructure

---
**Date:** 2026-07-12 23:47
**Author:** AI Assistant (claude-fable-5, board lane)
**Status:** Handoff
**Branch:** `ms/dm-host-posteriors-pdfs` (shared tree, multiple concurrent agent lanes)
**Commit:** `24f5ca0` (HEAD moved during session — association-summary lane committing concurrently)

---

## Task(s)

| Task | Status | Notes |
|------|--------|-------|
| Owner orientation ("lost the thread") | ✅ Complete | Delivered in-chat from CONTEXT.md + plan-circulation-readiness.md + journal + owner-view.json |
| Board visual redesign (pass 1) | ✅ Complete + deployed | Dependency-spine SVG map, trust-ladder stepper, needs-you banner, journal dot-timeline, CVD-validated palette |
| Board IA restructure (pass 2) | ✅ Complete + deployed | Owner view re-grouped by **science strand** × lifecycle (inputs→method→measured→validated→written); recovery map/ladder/lane detail demoted to agent fold |
| owner-view.json re-keyed to strands | ✅ Complete | 7 strand components; stale "P0 unblocks census+budget" hint corrected |
| Stale trust-state fixes on board | ✅ Complete | V4/V5/V6 now shown cleared 07-07 (was: "nothing retains trust") — verified against CONTEXT.md status paragraphs |
| Commit board source to main | 📋 Planned | Deploy is live on gh-pages, but `readiness.html` + `owner-view.json` are uncommitted on the branch |

**Current Workflow Phase:** Implement (infrastructure/visibility work, not manuscript science)

## Workflow Artifacts

- [plan-circulation-readiness.md](../plan/plan-circulation-readiness.md) — master plan; source of all task IDs the board renders
- [plan-trust-reset-revalidation.md](../plan/plan-trust-reset-revalidation.md) — §V expansion (P0–P6 rungs on the board's trust ladder)
- `docs/rse/protocols/journal-protocol.md` — board upkeep protocol (rebake + deploy flow)

## Critical References

- `docs/rse/control/board/readiness.html` — the entire board (inline CSS + static sections + two baked marker regions). Read its top comment blocks: they document the baker class contract and the update duty for the static strand/map/ladder sections.
- `docs/rse/control/board/owner-view.json` — owner-strip data (needs_you / now / next / components). Components are now **strand-keyed** (Sample & association, Budget & census, Scattering, Scintillation, Energies, Synthesis, Mechanics).
- `scripts/render_journal_panel.py` — the baker. Rewrites `OWNER:BEGIN/END` and `JOURNAL:BEGIN/END` regions only; everything else in readiness.html is hand-maintained static markup.

## Recent Changes (this lane only)

- `docs/rse/control/board/readiness.html` — full rewrite ×2. Final structure: header → baked owner view (needs-you banner via `.oc-you` CSS, full-width) → **strand swimlanes** (`.strands`, 7 rows, 5-stage steppers, `.feed` chips for cross-strand dependencies) → fold "Agent detail" (recovery-pipeline SVG map, P0–P6 trust-ladder stepper, V…G lane/task lists) → fold Journal (dot timeline, uses CSS `:has()`) → fold Reference (trust state now split restored-vs-still-revoked) → footer (documents the strand structure + sync duty).
- `docs/rse/control/board/owner-view.json` — components re-keyed to strands; `next` hints updated; timestamp bumped.
- `docs/rse/protocols/journal.jsonl` — three `board`-lane entries appended (23:09, ~23:15 by other lane, 23:30 strand restructure).
- gh-pages — deployed twice via `scripts/deploy-board.sh`; live at https://jakobtfaber.github.io/Faber2026/board/.

Not this lane (concurrent, do not fold into board commits): association-cards/summary figures + `sections/*.tex` + `scripts/*association*` (staged, association-summary lane), `scripts/render_journal_panel.py` +80 lines (earlier owner-view lane, uncommitted), `pipeline` gitlink MM, `.gitignore`, scint-review outputs.

## Design decisions & rationale (owner-approved this session)

1. **Strands over recovery lanes.** The V/A/B/…/G buckets encode the 07-06 trust-reset recovery pipeline, not the paper. Owner confirmed the reorganization: main view = 7 science strands, each on an inputs→method→measured→validated→written lifecycle. Trust is the per-strand *validated* stage, not a separate bucket; input provenance stays early (V2 under scattering *inputs*).
2. **Task IDs are immutable keys.** P0/A1/B4/… from the plans are unchanged everywhere; strands only regroup presentation. Journal lanes, plan docs, and agent scheduling still speak lane IDs.
3. **Radial mind-map rejected** (owner accepted reasoning): 7 hubs + cross-feeds → spaghetti; swimlane-with-feed-chips encodes the same non-linearity legibly. Only 3 cross-feeds are drawn: scint → scattering method (prior odds), scattering → budget D2 comparison, scattering+budget → synthesis inputs.
4. **Recovery map kept, demoted.** The V…G SVG dependency map remains the graph agents schedule against — it lives in the "Agent detail" fold with the ladder and lane lists.
5. Status palette CVD-validated (dataviz six-checks script): light `--now` teal moved to `#0F7E99`; dark teal/blue pair separated to `#45C4D8`/`#8FA6EE` (deutan ΔE 11.9 → 16.8).

## Verification State / Known-Broken

- **Verified:** rebake round-trip (baker markers survive both rewrites); headless-Chrome screenshots of light, dark, and folds-open renders inspected; deploy script reported success both times.
- **Uncommitted:** `readiness.html` (M) and `owner-view.json` (untracked) on `ms/dm-host-posteriors-pdfs`. The live board does not depend on this, but the *source of truth for the next board editor does* — commit them to main (or the next board-touching PR) before another agent edits from a stale checkout.
- **Not tested:** browsers without CSS `:has()` (journal dots degrade to hairline-gray — acceptable); Pages rebuild visually confirmed only via prior deploys, not re-fetched after the second push.
- **Tests:** none run — no Python/tex code touched by this lane (`render_journal_panel.py` diff belongs to the earlier owner-view lane).

## Learnings

- **Baker contract:** `scripts/render_journal_panel.py` regenerates only the marker regions but emits fixed class names (`.own*`, `.oc-*`, `.comp`, `.cnm/.cid/.cnx`, `.journal`, `.jts/.jagent/.jlane/.jnote`, `chip c-*`, state classes `s-good/now/pend/ready`). Any redesign is free in CSS but must keep those names, or extend the baker first.
- **Full-file Write + rebake beats surgical edits** for this board: markers make the rewrite idempotent; run the baker immediately after to re-fill owner/journal regions.
- **Board staleness is systemic:** static sections don't self-update. This session found and fixed V4/V5/V6 shown unrecovered days after clearance. The footer + inline comments now name the sync duty (strands + map + ladder + lane detail + owner-view.json), but it remains manual — candidate future fix: derive strand/lane state from a small JSON the way owner-view already works.
- **gh-pages deploys are cheap and concurrent-safe** (`deploy-board.sh` uses a temp worktree; two other board deploys happened this evening, 23:09/23:15, interleaved without conflict).
- Force light-mode screenshots of the fragment-style HTML by prefixing `<html data-theme="light">` to a temp copy; headless Chrome follows system dark otherwise.

## Action Items & Next Steps

1. [ ] Commit `docs/rse/control/board/readiness.html` + `docs/rse/control/board/owner-view.json` (plus the earlier-lane `render_journal_panel.py` owner-view support, if its owner lane hasn't) to main via a focused `infra/board` branch — keep association-lane staged files out.
2. [ ] Propagate the strand vocabulary to `docs/rse/protocols/journal-protocol.md` (it describes owner-view upkeep; add one line: components are strand-keyed, strand swimlane stages must be updated with lane state).
3. [ ] Optional next iteration (owner hasn't asked): data-drive the strand stages from JSON like owner-view, so agents update one file instead of three HTML sections.
4. [ ] Ongoing owner decisions unchanged and still pending on the board: A1 trigger calibration; first trust-ladder rung (P0 recommended).

**Recommended Next Skill:** `ai-research-workflows:implementing-plans` only if item 3 is picked up; otherwise none — items 1–2 are mechanical closeout any session can do directly.

## Other Notes

- Canonical board URL: https://jakobtfaber.github.io/Faber2026/board/ (gh-pages `board/` subdir; repo-root of gh-pages hosts the CHIME scattering deck — deploy script touches only `board/`).
- The shared working tree has several **separate-active lanes** (association summary staged; scint-review outputs; pipeline gitlink MM). Inventory read-only before any commit from this tree; never sweep them into a board commit.
- Trust-state authority is CONTEXT.md (statuses dated 2026-07-07), not older board/plan copies — the plan file `plan-circulation-readiness.md` §V checkboxes still show V4/V5/V6 unchecked; the board now disagrees *correctly*. Consider updating the plan's checkboxes in the same closeout commit (verify against CONTEXT.md wording first).

---

**Handoff created by AI Assistant on 2026-07-12**
