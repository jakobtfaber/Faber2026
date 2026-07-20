# Validation: closeout read-only verification — red pin, drift guard, and the open PRs

> Validated on **2026-07-09** against the two picked-up handoffs
> (`handoff-2026-07-09-11-13-pr42-43-merged-and-concurrent-closeout.md` and
> `handoff-2026-07-09-04-14-mahi-tns-mislabel-and-red-pin.md`) and the FLITS
> drift-guard test `test_joint_summary_reproducible`.
> Evidence source of truth: **GitHub API + git `archive` of the exact commits**,
> not local checkout (coarse git-protection mode is active; local FLITS is parked
> on `agent/sightline-halo-grid-figure @ f9e1c246`, local Faber2026 on
> `ms/appendix-c-sync-pr40`, both stale and another lane's).
> Faber2026 `main` tip at validation: `8146b11` (PR #65). `pipeline` gitlink: `6c87890`.

## Verdict

**The closeout is correct so far, but NOT finished — do not bump the pin yet.**
The deferred read-only pass is done and every claim in the two handoffs that I
could check reproduced. The one blocking item — the red `pipeline` pin — has its
fix (**dsa110-FLITS #147**) verified green and byte-exact, but #147 is **still
open/unmerged**, so `origin/main`'s gitlink still points at the red commit.

## What I verified with fresh, self-produced evidence

### 1. The red pin is real (confirmed, deterministic)
Extracted commit `6c87890`'s tree via `git archive`, ran the committed
`gen_joint_summary.py` against its own committed `joint_json/*.json`, and diffed
against its committed `results/joint_fit_summary.md`:

- **regenerated ≠ committed → drift guard FAILS.** Reproduces
  `test_joint_summary_reproducible::test_summary_matches_generator_output`
  (1 failed / 557 passed) exactly.
- Generator is pure stdlib (`glob`, `json`, `pathlib`) — **no RNG, no timestamp**;
  the failure is deterministic, not flaky. Matches the PR #65 handoff.
- The entire diff is the **johndoeII** row: committed summary says "3 of 11
  trusted / johndoeII ✅ trusted"; the generator's `TRUST` dict at that very
  commit already says `johndoeII: "superseded"`. The summary simply lagged the
  generator + JSONs since `826ba36`.
- CI on `6c87890`: `Python 3.12` = **failure** (confirmed via API). Note there
  are two workflows on this sha — `review`/`Claude Review` = success, `Tests`/
  `Python 3.12` = failure. Reading only the first-sorted run is what produced the
  earlier false "green" claim; always filter by workflow name.

### 2. PR #147 fixes it, and its summary is a verified function of the inputs
Extracted #147 head `38f8f9a`, same procedure:

- **regenerated == committed, byte-identical → drift guard PASSES.**
- CI on `38f8f9a`: **`Tests` workflow = success**, `Python 3.12` = success
  (both confirmed via API). Reproduces my local result.
- The diff vs the pin is exactly and only the johndoeII demotion
  (✅ trusted → ↺ superseded; trusted count 3→2 = phineas, wilhelm). The
  demotion is **asserted by the committed JSONs + generator TRUST dict**, not
  hand-edited into the markdown — the summary is 100% `render()` output.
- Spot-checked numeric cells against source JSONs — all exact:
  johndoeII α=1.37 τ=0.8521 lnZ=-15805; phineas 3.58/0.3220/-23163;
  wilhelm 2.71/0.2607/-17951; mahi 5.53/0.0945/-15431; oran 1.44/0.4972/-15776.
- #147 touches **one file only** (`results/joint_fit_summary.md`, +6/-... one
  net change block). No code, no data, no pin.

### 3. The rest of the closeout landed and is internally consistent
- PRs **#42, #43, #46–#58, #60–#62, #65** all merged; `main` history from
  `8cef432` → `8146b11` is linear and each merge commit matches its PR.
- `pipeline` gitlink on `main` = `6c87890` (the re-pin off the divergent squash
  `c69d043`, via #53/#56; REPRODUCE.md corrected via #55). Confirmed via API.
- Faber2026 `main` manuscript side is unaffected by the red pin (PR #65's claim):
  the pin failure is a FLITS-internal results-drift test; the manuscript cites
  johndoeII only as figure panels + a `% TODO(disc-johndoeii)` at
  discussion.tex:75.

### 4. The three open Faber2026 PRs (another agent's lane — left untouched)
- **#59** `ci/table-parity-gate` — its `parity` check = **success**. MERGEABLE.
- **#63** `docs/agent-identity-runbook` — docs-only, checks green. (Runbook step 3
  depends on #59 landing first.)
- **#64** `docs/handoff-open-items` — the open-items handoff, checks green.
- Per both handoffs these belong to the concurrent closeout session; I did not
  touch, merge, or comment on them.

## Open items / what still needs a human (unchanged from PR #65 handoff)

1. **Merge dsa110-FLITS #147** — now verified green and byte-exact; safe to merge.
   Its `Claude Review` was still in progress at validation (non-blocking).
2. **Merge dsa110-FLITS #146** (docstring: mahi is `FRB 20240122A`, not
   `FRB 20240119A`) — was red **only by inheritance** from #147; re-run its
   `Python 3.12` after #147 lands and it should go green.
3. **Do NOT bump the `pipeline` gitlink as a side effect.** Per `CLAUDE.md` that
   is its own reviewed step. Both FLITS PRs land on the pin's *branch*;
   `origin/main` keeps `6c87890` until someone deliberately bumps it. Before
   bumping, run `git merge-base --is-ancestor 6c87890 <new>`.
4. **@decision — nickname↔TNS ownership** (`pipeline/CLAUDE.md:53` →
   gitignored `chimedsa_burst_specs.csv` with the wrong TNS for mahi;
   `configs/bursts.yaml` has no TNS names). Design call, owner's.
5. **@decision — mahi TNS registration.** `FRB 20240122A` is the pipeline's
   date-derived name; TNS could not be reached (control 404s too), so `tns_name`
   left blank. Confirm on TNS or state "unregistered" in the README.
6. **@decision — a manuscript sentence on the four co-detection near-misses**
   (gertrude, pingu, FRB20220912A2/repeater, benjy) excluded on data
   availability, not astrophysics. Candidate home: `sections/toa.tex`.
7. **Owner-only:** #59/#63/#64 disposition, branch protection, the
   `repro_manifest.csv` `run_command` rows from a fresh clone, iTerm Diff-pane.

## Method note (reproducibility of THIS validation)
- Commits fetched read-only; trees extracted with
  `git archive <sha> analysis/scattering-refit-2026-06 results/joint_fit_summary.md | tar -x`
  into `/tmp` (no `.git` writes, worktree add is blocked by protection mode).
- `python3 analysis/scattering-refit-2026-06/gen_joint_summary.py` in each tree,
  then `diff` vs a pre-run copy of that tree's committed summary.
- No writes to either repo, the shared checkout, or `~/Data`. Read-only pass.

## References
- Handoff (provenance): `handoff-2026-07-09-11-13-pr42-43-merged-and-concurrent-closeout.md`
- Handoff (red pin): `handoff-2026-07-09-04-14-mahi-tns-mislabel-and-red-pin.md`
- Open-items authority: `handoff-2026-07-09-03-50-open-items-ci-gate-and-agent-identity.md` (PR #64)
- Fix under validation: dsa110-FLITS #147 `fix/regen-joint-summary` @ `38f8f9a`
- Generator: `analysis/scattering-refit-2026-06/gen_joint_summary.py`
- Drift-guard test: `tests/.../test_joint_summary_reproducible.py`
