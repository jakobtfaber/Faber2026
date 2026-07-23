# Build the seeded reproducible joint-fit runner

- Type: `wayfinder:task` (AFK)
- Status: resolved (2026-07-22)
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

- [x] The sampler receives an explicit recorded seed on serial and multiprocess paths.
- [x] A pre-run receipt verifies clean source, exact inputs, configuration, command, and environment before sampling.
- [x] A repeated cheap fit produces identical scientific arrays, summaries, diagnostics, and rendered bytes.
- [x] Deprecated-Zach guards are enforced or surfaced by the controlled path.
- [x] Seed omission, dirty source, missing input, and hash mismatch fail closed in tests.

## Blocked by

- [Audit the deprecated Zach C2D4 failure](joint-scattering-controlled-rerun-01-audit-deprecated-zach-c2d4.md)

## Resolution — 2026-07-22

The controlled runner landed in
[dsa110-FLITS PR 224](https://github.com/jakobtfaber/dsa110-FLITS/pull/224),
then received the h17 executable-identity correction in
[PR 226](https://github.com/jakobtfaber/dsa110-FLITS/pull/226). The final
controlled source revision is `08649392d9c9f1bfd21752c63f1a7330cd39fbe7`. It freezes
the seed, clean source, exact input and configuration hashes, processing and
numerical environments, command, working directory, resolved likelihood and
priors, processed arrays, sampler history, and the complete output packet.
Real serial and multiprocessing repeatability tests pass. The full repository
suite passed with 839 tests and no failures; two independent reviews found no
remaining defect. The automated GitHub Claude review failed before examining
the code and produced no comments; this was an external reviewer failure, not
a scientific or test pass. Production fits remain separate open tickets.

The first h17 invocation at revision `67b73a85` exposed a fail-closed
virtual-environment replay defect: resolving the uv Python symlink selected the
base interpreter, which could not import NumPy. Jobs 196–198 stopped before
preflight or sampling and created no scientific output. Hash-bound failure
receipts remain under
`/home/ubuntu/flits-controlled/joint-scattering-2026-07-22/`. PR 226 preserves
the invoked virtual-environment path, separately records the resolved base
path, prefixes, complete interpreter flags/options, and rejects flags the
frozen command cannot replay. The original h17 failure loop and 841 repository
tests pass on the corrected revision.
