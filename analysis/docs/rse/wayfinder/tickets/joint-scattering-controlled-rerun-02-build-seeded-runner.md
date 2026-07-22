# Build the seeded reproducible joint-fit runner

- Type: `wayfinder:task` (AFK)
- Status: open
- Assignee: —
- Blocked by: [Audit the deprecated Zach C2D4 failure](joint-scattering-controlled-rerun-01-audit-deprecated-zach-c2d4.md)
- Map: [ApJ submission](../map-apj-submission.md)
- Plan: [Controlled joint-scattering reruns](../../specs/plan-controlled-joint-scattering-reruns-2026-07-22.md)
- Authorization: manuscript-owner request, 2026-07-22

## What to build

Make joint-scattering fit generation deterministic and provenance-complete. A
controlled run must require and record a sampler seed, exact inputs and
configuration, clean source revision, command, working directory, environment,
and output hashes. It must fail closed if any required identity is absent or
changes. Prove repeatability with a cheap controlled fit before launching the
three production runs.

## Acceptance criteria

- [ ] The sampler receives an explicit recorded seed on serial and multiprocess paths.
- [ ] A pre-run receipt verifies clean source, exact inputs, configuration, command, and environment before sampling.
- [ ] A repeated cheap fit produces identical scientific arrays, summaries, diagnostics, and rendered bytes.
- [ ] Deprecated-Zach guards are enforced or surfaced by the controlled path.
- [ ] Seed omission, dirty source, missing input, and hash mismatch fail closed in tests.

## Blocked by

- [Audit the deprecated Zach C2D4 failure](joint-scattering-controlled-rerun-01-audit-deprecated-zach-c2d4.md)
