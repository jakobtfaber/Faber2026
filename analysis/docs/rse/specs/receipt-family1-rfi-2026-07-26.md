# Receipt: family 1 — CHIME RFI preservation/validation (2026-07-26)

**Objective/phase:** third family of the branch-landing roster
(`roster-branch-landing-2026-07-26.md`), owner-chartered ("Proceed with
family 1").

## Landed

**Analysis PR #74 merged** (`b2d8b3b` on main): the remaining CHIME RFI
acceptance-contract proposal — binding removal / false-removal /
retention / time-split / held-out-scope / review-panel rules, the owner
decision packet
(`docs/rse/specs/notes/owner-decision-packet-rfi-acceptance-contract-2026-07-23.md`),
and the route-test repair. The PR was 60 commits behind main with one
conflict in `tests/test_wayfinder_certified_data_route.py` — both sides
had added a guard at the same loop (main's contract carve-out; the PR's
general closed/resolved-prerequisite skip). Resolved by keeping both
guards; head re-verified unchanged (`63d413aa`) before the merge commit
was pushed; route test 17/17 green on the branch and re-run green on
merged main. **The contract itself remains owner-pending** — the ticket
stays "Status: open — owner ratification" and the merge stages the
decision packet without deciding it.

## Superseded (verified, not landed)

| Branch | Evidence |
|---|---|
| parent `codex/prototype-chime-rfi-preservation-gates` (12) | declared the stale predecessor in PR #201's own description ("focused successor of the stale … lane, rebased onto current main") |
| parent `codex/chime-rfi-preservation-gates-successor-20260722` (6) | PR #201 closed: "Superseded. Valid real-event RFI evidence has been ported into Faber2026-analysis PR #33; synthetic-cleaner authority was excluded. Branch preserved." |
| analysis `codex/auto-review-rfi-preservation-limits` (1) | PR #34 closed: "Superseded by the owner-approved real-event Zach manual bad-channel-map route … diagnostic history only; it must not satisfy RFI validation" |

**Port-chain verification:** PR #33 itself closed unmerged ("valid lanes
were integrated through focused later pull requests"), so the port claim
was checked against main directly — analysis `origin/main` carries the
real-Zach RFI review plan/implement/validate docs, the checksummed
verify evidence (`docs/rse/verify/rfi-real-event-review-20260721/` with
`SHA256SUMS`), the owner-approved manual bad-channel map
(`rfi/manual-bad-channels/chime-frb/zach.json`), and rfi-validation
tickets 01–05. The evidence chain terminates on main; the synthetic
cleaner is excluded everywhere, consistently.

## Family status

Family 1 closed. Open owner item (queue-recorded in the ticket): ratify
the RFI acceptance contract. No branches deleted.
