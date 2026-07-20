# Runbook: give agents a separate identity, and make review a real gate

**Status:** proposed; steps 1–4 require the repository owner (they create accounts
and change org/repo settings, which an agent session cannot and should not do).
**Written:** 2026-07-09, after PR #46 merged unreviewed with a false claim.

## The problem, stated precisely

On 2026-07-09 PR #46 was opened at 09:36:14, a comment reading
"⚠️ Hold this until the emitter's data file is fixed" was posted at 09:40:19, and
the PR was merged at 09:46:27 with **zero reviews**. It carried a hazard warning
that was already false, which had to be reversed by PR #51.

Nobody can say who merged it. Every `gh` call an agent makes authenticates as
`jakobtfaber`, and every commit an agent makes is authored
`Jakob Faber <jfaber@caltech.edu>` from the repo's git config. The owner's
actions and the agent's actions are **byte-identical in the audit log**. That is
the defect this runbook closes; the merge itself is only its most visible symptom.

Note that this is not fixed by asking the agent to behave. `CLAUDE.md` grants a
standing authorization to "push branches and open/merge pull requests," and an
agent that believes it is following policy will merge its own work. Policy text
is not a gate. A gate is a gate.

## Current state (measured 2026-07-09)

| Fact | Value |
|---|---|
| `main` branch protection | **none** (`GET .../branches/main/protection` → 404) |
| Authenticated accounts | `jakobtfaber` (active; `repo`, `workflow`, `read:org`, `gist`, `delete_repo`) |
| | `jakobtfaber-2` (inactive; `repo`, `admin:org`, `delete_repo` — **no `workflow`**) |
| Commit author for agent commits | `Jakob Faber <jfaber@caltech.edu>` — same as owner |
| CI | none on `main` yet; `table-parity` proposed in PR #59 |

## Design

Two independent properties, each worth having on its own:

1. **Attribution.** Agent actions must be distinguishable from yours in
   `git log`, in the PR timeline, and in the merge event.
2. **A merge gate that the agent cannot satisfy alone.** GitHub refuses to let a
   pull request's author approve their own pull request. Once the agent is a
   *different principal* from you, "require 1 approving review" becomes a hard
   constraint on the agent rather than a formality — it structurally cannot
   merge without you.

Property 2 depends on property 1. Doing protection first, while both principals
are `jakobtfaber`, buys nothing: you would approve your own agent's PRs as
yourself.

### Choosing the agent principal

**Option A — GitHub App (recommended).** A bot identity (`your-app[bot]`) with a
fine-grained installation token. Commits and merges are attributed to the app.
No seat cost, no password/2FA to manage, scopes are per-repository and
per-permission, and the token is short-lived. Slightly more setup.

**Option B — machine user.** Reuse `jakobtfaber-2`, or make a dedicated
`jakobtfaber-agent`. Simpler: it is just another `gh auth login`. Costs nothing
on public repos. Downsides: it is a full account (2FA, recovery codes), GitHub's
ToS treats machine accounts as a limited exception, and `jakobtfaber-2` currently
holds `admin:org` — far more authority than an agent should ever carry.

If you take Option B, **do not reuse `jakobtfaber-2` as-is.** Its `admin:org`
scope means an agent holding that token can administer the organization. Mint a
fresh token restricted to `public_repo` (or `repo` for private) plus `workflow`
only if the agent must edit `.github/workflows/`.

## Steps (owner)

### 1. Create the agent principal

Option A:

```bash
# github.com/settings/apps/new
#   Repository permissions: Contents: Read & write
#                           Pull requests: Read & write
#                           Actions: Read          (to read check results)
#                           Metadata: Read         (implied)
#   Do NOT grant: Administration, Members, or any org-level write.
# Install it on jakobtfaber/Faber2026 only.
```

Then, in agent sessions, authenticate with an installation token rather than
your `gho_…` user token.

Option B:

```bash
gh auth login --hostname github.com   # as the agent account
gh api user --jq .login               # confirm it is NOT jakobtfaber
```

### 2. Separate the *git* identity too

The API token governs PR/merge attribution. It does **not** govern commit
authorship — that comes from git config. Set it per-clone in whatever checkout
agents work from:

```bash
git -C <agent-checkout> config user.name  "Faber2026 Agent"
git -C <agent-checkout> config user.email "<agent-account-id>+<agent-login>@users.noreply.github.com"
```

Verify the split is real before trusting it:

```bash
git -C <agent-checkout> log -1 --format='%an <%ae>'   # must NOT be jakobtfaber
```

Keep the existing `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`
trailer regardless — it records *which model*, which the account cannot.

### 3. Land CI first

Merge PR #59 (`ci/table-parity-gate`). Branch protection can only require a
status check that GitHub has already observed on this repo; requiring a context
that has never reported leaves PRs permanently pending.

The context name to require is the **job id**, `parity` — not the workflow name
`table-parity`.

### 4. Protect `main`

```bash
gh api -X PUT repos/jakobtfaber/Faber2026/branches/main/protection \
  --input - <<'JSON'
{
  "required_status_checks": { "strict": true, "contexts": ["parity"] },
  "required_pull_request_reviews": {
    "required_approving_review_count": 1,
    "dismiss_stale_reviews": true
  },
  "enforce_admins": true,
  "restrictions": null
}
JSON
```

`enforce_admins: true` is the load-bearing field. Without it you (and any token
with admin) bypass every rule above, and the gate is decorative. With it, *you
also* cannot push straight to `main` — that is the intended cost. Turn it off
temporarily if you ever need an emergency direct push, and turn it back on.

`strict: true` additionally requires branches to be up to date with `main`
before merging, which is what would have forced #46 to rebase onto #48 and see
the drift already fixed.

## Verification

Run all four. Each must behave as stated, or the gate is not real.

```bash
# 1. Protection is on and admins are not exempt.
gh api repos/jakobtfaber/Faber2026/branches/main/protection \
  --jq '{checks: .required_status_checks.contexts,
         reviews: .required_pull_request_reviews.required_approving_review_count,
         enforce_admins: .enforce_admins.enabled}'
# expect: {"checks":["parity"],"reviews":1,"enforce_admins":true}

# 2. A direct push to main is refused, even for you.
git push origin main            # expect: rejected by branch protection

# 3. The agent cannot approve its own PR.
#    As the agent account, on a PR the agent authored:
gh pr review <n> --approve      # expect: 422, "Can not approve your own pull request"

# 4. Attribution is distinguishable.
gh api repos/jakobtfaber/Faber2026/issues/<n>/timeline \
  --jq '.[] | select(.event=="merged") | .actor.login'
# expect: the agent login on agent merges, jakobtfaber on yours — never ambiguous
```

Check 3 is the one that matters. If it returns success rather than 422, the agent
is still you, and steps 1–2 did not take.

## What this does not fix

- **It does not make the agent's review judgement good.** It makes a *human*
  approval mandatory. If you approve without reading, you have moved the failure,
  not removed it.
- **It does not cover the submodule.** `dsa110-FLITS` is a separate repository
  (`dsa110/dsa110-FLITS`) with its own permissions. An agent that can push there
  can still change what `pipeline` points at, independent of everything above.
- **It does not stop a bad pin.** The `table-parity` check catches a
  `(super-repo, pin)` pair whose numbers disagree. It cannot catch a pin that is
  self-consistent but wrong — e.g. `c69d043`, the divergent squash that PR #53
  had to back out of.

## Rollback

Every step is reversible and none touch repository content.

```bash
gh api -X DELETE repos/jakobtfaber/Faber2026/branches/main/protection
git -C <agent-checkout> config --unset user.name
git -C <agent-checkout> config --unset user.email
gh auth logout --hostname github.com --user <agent-login>
```

## Related

- PR #59 — the `table-parity` CI gate this runbook's step 3 depends on.
- PR #58 — why `--check` alone was never a sufficient gate.
- `REPRODUCE.md`, hazard 1 — the cross-repository trap that made the drift
  invisible in the first place.
