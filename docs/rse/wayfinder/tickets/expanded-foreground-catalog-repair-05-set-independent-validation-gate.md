# Set the independent validation and release gate

- Type: `wayfinder:task` (AFK)
- Status: open
- Assignee: Independent reviewer
- Blocked by: [Set the Figure 3 regeneration and promotion gate](expanded-foreground-catalog-repair-04-set-figure-3-gate.md)
- Map: [Expanded foreground catalog repair](../map-expanded-foreground-catalog-repair.md)
- Triage: `ready-for-agent`

## Question

What evidence demonstrates that the rebuilt catalog, classifications, physics,
and Figure 3 are correct without trusting the builder or its prose summary?

## Acceptance decision

The reviewer starts from committed source inputs and paper equations, implements
independent calculations, rechecks every selected identifier and separation,
compares counts and hashes, and records row-level differences. Validation fails
on any unexplained mismatch, query-error collapse, missing input, stale figure,
unapproved figure, or classification drift. The final report names the parent
commit and pipeline commit and may say `Verified` only when all gates pass.
