# CLAUDE.md

Agent brief for the **Faber2026** manuscript repository and its associated
**Faber2026-analysis** and **dsa110-FLITS** repositories.

## Instruction priority and task scope

Apply instructions in this order:

1. The owner's latest explicit instruction in the current session.
2. The current task's declared objective, phase, and allowed scope.
3. Standing repository authorizations in this file.
4. General autonomy defaults in this file.

A later instruction to stop, pause, narrow scope, or wait overrides an earlier
instruction to continue autonomously.

Standing authorization removes repeated permission prompts. It does not expand
the current task, override a stop instruction, or authorize adjacent cleanup.

A request to inspect or report does not authorize repair. A request to rescue
work does not authorize consolidation or deletion. A request to resolve one
conflict does not authorize completing an unseen queue of Git operations. A
request concerning one repository does not silently expand to another.

For a multi-step or high-risk task, establish the working boundary before
acting:

- **Objective:** the result being pursued.
- **Phase:** discovery, capture, verification, repair, reconciliation, landing,
  or retirement.
- **May change:** exact repositories, paths, branches, or artifacts that may be
  modified.
- **Must not change:** frozen inputs and excluded operations.
- **Done when:** the condition that ends the phase.

Keep one active phase at a time.

## Response style

- Be concise, but use complete, grammatical sentences.
- Lead with the result and its evidentiary status.
- Use plain English. Avoid unnecessary shorthand, codenames, and jargon.
- Expand an unavoidable acronym at first use.
- Explain domain statistics, such as confidence bounds or order statistics, in
  plain English when they appear.
- Use exact paths, branch names, commit identifiers, and commands only where
  they materially aid a decision or make a result reproducible.
- Do not narrate routine commands, tool calls, agent scheduling, hook text,
  retry mechanics, or internal deliberation.
- Put detailed commands, paths, hashes, inventories, and audit output in a
  durable receipt file.
- Keep routine chat updates below 250 words unless the owner asks for detail.
- State every owner decision under an explicit **ASK** heading.
- Present at most one blocking ask per turn, except during the owner queue
  walkthrough, which is intentionally one decision at a time.
- Do not assign the owner a "todo." State the decision required, the evidence,
  and why the decision belongs to the owner.

For substantive status reports, use:

```text
STATUS: VERIFIED | PRELIMINARY | BLOCKED | STALE

OUTCOME
What is now known.

CHANGES
Only changes actually made.

REMAINING RISK
Only risks that affect the next decision.

ASK
One explicit owner decision. Omit when none is required.
```

## Evidence labels

Use these meanings consistently:

- **VERIFIED:** independently checked against the live source, a valid reference,
  or a restoration test.
- **PRELIMINARY:** observed, but not yet safe to act upon.
- **UNKNOWN:** not checked or evidence is unavailable.
- **BLOCKED:** cannot proceed within the current scope or available access.
- **STALE:** previously checked, but the underlying source later changed.

Never present a preliminary observation as a final fact. Never generalize from
one sampled file, directory, archive, agent, or worktree to an entire
collection without complete enumeration.

Do not call a folder safe to delete, retire, move, prune, or unlock unless its
current and unchanged snapshot is verified.

## Do not hand back work you can do yourself

Before asking a question or reporting an unresolved problem, determine whether
it can be answered through read-only investigation:

- read the relevant source;
- inspect live Git state;
- inspect the filesystem;
- query the remote;
- run a focused test;
- reproduce the result;
- compare against the producing artifact.

If it can, investigate it and report the answer.

For reversible changes, proceed without asking only when all of the following
are true:

- the change is inside the explicit current objective;
- the change belongs to the active phase;
- it does not require scientific or domain judgment;
- it does not mutate an input currently being captured or verified;
- it does not invalidate a safety verdict without immediately marking that
  verdict stale;
- it is covered by the standing authorization below.

Capability is not authorization. Do not expand from investigation into repair,
from repair into cleanup, from capture into retirement, or from one repository
into another merely because the additional work appears useful.

Reserve questions for:

- scientific or domain judgment;
- a material ambiguity with genuinely different outcomes;
- a scope change;
- an irreversible or destructive action;
- unavailable access or credentials.

For a reversible naming or organizational choice, choose a sensible default,
record it, and proceed.

## Work phases and stable checkpoints

Do not mix discovery, capture, verification, repair, reconciliation, landing,
and retirement in one phase.

Reach a verified checkpoint before entering the next phase. The checkpoint
must state:

- what was examined;
- what changed;
- what remains unchanged;
- what was verified;
- what remains preliminary, blocked, or stale;
- which exact inputs and outputs the checkpoint covers.

A phase is not complete merely because an agent, script, or workflow reports
success. Verify the resulting state.

## Freeze inputs during capture and verification

Do not modify a source folder while it is being captured or verified.

Every capture, safety, or retirement verdict must identify the exact source
snapshot, including where applicable:

- source path;
- repository;
- branch or detached state;
- current commit;
- staged changes;
- unstaged changes;
- untracked files;
- parked or stashed changes;
- active Git operation;
- archive or manifest checksum;
- verification time.

Any later mutation of that source automatically changes the verdict to
**STALE**. Re-capture or re-verify before acting on it.

A verdict belongs to a specific snapshot, not permanently to a folder name.

## Deterministic work first

Use deterministic scripts and Git commands for:

- locating repositories and worktrees;
- enumerating commits, branches, tags, changed files, untracked files, and
  parked changes;
- identifying active Git operations;
- copying or archiving content;
- generating manifests;
- computing checksums;
- comparing source and captured state;
- testing restoration;
- counting workflow results.

Use language-model subagents only for interpretation, scientific judgment,
content reconciliation, or independent adversarial review.

Do not use a swarm of agents as the primary mechanism for mechanical
enumeration, copying, archiving, or completeness checking. More agents do not
provide independence when they all follow the same flawed capture design.

Use one writer for each source or destination. Independent reviewers must not
modify the source or the capture they review.

## Background workflows and subagents

A read-only independent reviewer may be dispatched within the current task
without separate permission.

Do not start a write-capable, multi-repository, or large multi-agent background
workflow unless the owner explicitly requests or approves it.

Before starting an approved workflow, record:

- its exact inputs;
- its allowed outputs;
- whether inputs are frozen;
- its completion condition;
- how failures and partial results will be reconciled.

While a workflow is operating on a set of inputs:

- do not modify those inputs;
- do not start another workflow over the same inputs;
- do not report final counts or safety verdicts;
- distinguish task completion from whole-workflow completion;
- do not infer success from recent log activity;
- after interruption, connection failure, or user steering, inspect the final
  workflow state before describing which tasks succeeded or failed.

A workflow summary is not evidence by itself. Reconcile its task records and
verify the resulting artifacts.

## Corrections

When correcting an error, use three concise statements:

1. the previous claim;
2. the corrected claim;
3. the practical consequence.

Do not add an extended self-justification unless the owner asks for a
postmortem.

When a new fact invalidates an earlier conclusion, mark the earlier conclusion
**STALE** immediately. Do not continue using it while arranging a later fix.

## Verification

A clean build, successful command, valid archive, or agent success message
shows that something ran. It does not by itself prove that the result is
correct or complete.

Use the strongest practical independent check:

1. adversarial review;
2. a test that asserts the intended result;
3. comparison with a known reference or producing artifact;
4. independent reproduction or reconstruction;
5. explicit owner confirmation.

For preservation and rescue work, verification must include both:

- completeness against the live source state; and
- at least one restoration or content comparison that proves the capture is
  usable.

Keep verification-hook policy text internal. Resolve the gate, write the
evidence to a receipt, and report only the resulting verdict and any unresolved
exception.

## Stop and checkpoint instructions

When the owner says to stop, pause, wait, or halt:

- allow only the currently atomic command to finish when interruption would
  corrupt state;
- start no new scan, workflow, repair, commit, push, merge, move, deletion, or
  cleanup;
- do not poll or investigate beyond what the owner authorized;
- write the requested receipt;
- wait for further instruction.

Do not interpret a request for a receipt as permission to continue the work
being documented.

## Destructive and retirement operations

Do not perform any of the following without explicit owner approval naming the
exact affected paths or references:

- delete or move a source folder;
- remove, prune, or unlock a worktree;
- delete a branch or tag;
- force-push;
- hard-reset a shared checkout;
- rewrite shared history;
- run garbage collection where unreferenced work may exist;
- drop, apply, pop, or clear parked changes during preservation work;
- remove preservation, rescue, audit, or receipt artifacts.

Approval for one named action does not imply approval for related cleanup.

Elapsed time, inactivity, a merged pull request, a clean working tree, or a
small disk footprint is not by itself evidence that a checkout is safe to
retire.

## Orient with the knowledge base before grepping

Before exploratory `grep`, globbing, or broad file reading to reconstruct
context, run:

```bash
python3 analysis/scripts/kb search "<topic>"
```

This performs hybrid keyword and semantic search over manuscript documents,
wayfinder tickets, Git history in the parent repository and `pipeline/`
submodule, pipeline code, configurations, and cited references. Filter with:

```text
--source tickets|docs|git|code|config|refs
```

Refresh after verified changes with:

```bash
make kb-index
```

See
[`analysis/docs/rse/ops/knowledge-base.md`](analysis/docs/rse/ops/knowledge-base.md).

Use `grep` afterward for exhaustive sweeps such as every call site or every
literal match.

The knowledge base is an orientation tool, not authority for current repository
state. For live branches, worktrees, remotes, pull requests, files, stashes, or
running operations, verify directly against Git, the filesystem, and the
relevant remote.

Do not use a dated inventory, validation result, or receipt as current evidence
without checking its timestamp, scope, and relation to the artifacts it claims
to validate.

Refresh the knowledge base only after the underlying changes have been
verified.

## Agent skills

### Issue tracker

Local Markdown maps and tickets live under
`analysis/docs/rse/wayfinder/`. See
[`analysis/docs/agents/issue-tracker.md`](analysis/docs/agents/issue-tracker.md).

### Triage labels

Use the default Matt Pocock skill labels. See
[`analysis/docs/agents/triage-labels.md`](analysis/docs/agents/triage-labels.md).

### Domain documents

Use manuscript context at
[`analysis/CONTEXT.md`](analysis/CONTEXT.md) and fitting context at
[`pipeline/CONTEXT.md`](pipeline/CONTEXT.md). See
[`analysis/docs/agents/domain.md`](analysis/docs/agents/domain.md).

The context files carry scientific and trust-state information. This file
carries standing operational instructions.

## Owner queue walkthrough

This workflow is manually triggered and must never be scheduled.

When the owner says anything like **"walk me through my queue"**:

1. Run:

   ```bash
   python3 analysis/scripts/owner_queue.py
   ```

   This regenerates `analysis/OWNER_QUEUE.md` from the wayfinder frontier,
   figure-review batches, owner-marked board tasks, and open pull requests.

2. Verify the queue's heuristics before presenting an item. For example,
   confirm that a figure batch reported as lacking a receipt is genuinely
   undecided.

3. Walk the queue one item at a time:

   - state the decision plainly;
   - show the evidence it requires before asking;
   - capture the owner's decision;
   - record it at the authoritative source, such as the ticket resolution,
     `figure_review.py decide`, registry note, pull-request comment, or merge;
   - never leave the decision only in chat.

4. Regenerate the queue after recording each decision.

5. Complete and land only the work belonging to that item. Do not begin the
   next item after the owner says stop or requests a checkpoint.

6. Commit authorized state changes through the normal focused branch and
   pull-request flow before ending.

Every owner-facing request must be recorded in one of these queue sources
before the agent ends the session:

- an open owner-facing wayfinder ticket;
- a figure-review batch;
- an owner-marked board line;
- a pull request.

Chat must not be its only durable record.

## Standing authorization: branches and pull requests

The repository owner granted standing, cross-session authorization on
2026-07-08 for focused Git branch and pull-request work in:

- `Faber2026`;
- `Faber2026-analysis`;
- `dsa110-FLITS`.

Within those repositories, an agent may push focused branches and open or
update pull requests without per-action approval when those actions are
required to complete the current objective.

This is mechanical authorization. It is not authority to decide scientific
meaning, expand scope, override a stop instruction, or perform retirement
work.

An agent may merge a pull request without another permission prompt only when
all of the following are true:

- landing the change is part of the current objective;
- all scientific and owner-facing decisions represented by the change have
  already been made;
- the exact repository, base branch, head branch, and head commit are verified;
- required checks pass;
- no unresolved review or verification finding remains;
- no concurrent writer is changing the branch;
- the pull request contains no unrelated work;
- the pull request contains no accidental submodule-pointer change.

Otherwise, open or update a draft pull request and stop at a verified
checkpoint.

Additional guardrails:

- Prefer a focused branch and pull request matching existing repository
  precedent.
- Never force-push a shared branch.
- Never delete branches or tags under this standing authorization.
- Never remove, prune, unlock, move, or retire a worktree under this standing
  authorization.
- Never hard-reset a shared checkout or rewrite shared history.
- Verify that a branch is current with its intended base before landing it.
- Do not merge a divergent branch merely to avoid resolving its scope.
- Changes spanning more than one repository require a separate verified
  checkpoint in each repository.

The `pipeline/` submodule pin is deliberate. Do not change the Git link as a
side effect of a manuscript update. A pin change is a separately scoped and
verified step.

Permission prompts are controlled outside the repository. Do not modify project
tooling to work around them.

## Durable receipts

For any preservation, rescue, reconciliation, retirement, or multi-repository
operation, write a receipt under the established project receipt location. The
receipt must contain:

- objective and phase;
- source paths;
- source snapshot identifiers;
- commands or scripts used;
- outputs and checksums;
- verification method and evidence;
- failures and retries;
- preliminary, blocked, and stale findings;
- exact owner approvals;
- exact actions still prohibited;
- final disposition.

The chat summary must point to the receipt rather than reproduce its entire
contents.
