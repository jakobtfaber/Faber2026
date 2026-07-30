# Superseded — see the handoff one directory up

This file was created by pull request 213 to replace
`docs/rse/specs/handoff-2026-07-30-06-35-zach-sampling-retraction-and-ratification.md`,
which that pull request deleted. Its "Authoritative decision" section stated
that the manuscript owner visually compared the two sampling rates, said they
looked almost identical, and accepted 65.536 microseconds.

**The owner states that no such conversation occurred and that they never
accepted 65.536 microseconds.** The ratified decision is native 32.768
microseconds. This file is kept, emptied of its incorrect claim, so the trail
stays intact rather than disappearing; the original text is in `69c8f56`.

Its instruction to start a 27-rung 65.536-microsecond experiment must not be
followed. See
[the restored handoff](../handoff-2026-07-30-06-35-zach-sampling-retraction-and-ratification.md)
and [the incident record](../../wayfinder/tickets/unsupported-zach-sampling-decision.md).

## Controlled run — retained, and still accurate


`/home/ubuntu/Faber2026-runs/zach-count-20260730-r3` used source
`32eac309f13598979cf0715ab02036de3f8ad18f`, 65.536-microsecond DSA-110
sampling, nine isolated C2D3 rungs, and hash-bound inputs. Each freeze pass
correctly emitted its resolved fit identity and exited through the expected
identity-mismatch traceback. Real controlled sampling then began.

The orchestrator misclassified those expected tracebacks as real-run failures
and stopped process group `162656` on 2026-07-30. No fit completed. The root is
preserved as quarantine evidence and must not be promoted or resumed. Restart
the same frozen 27-rung experiment under a new root after the focused repair is
merged and pinned.


This run used the fabricated 65.536-microsecond sampling choice, so it could not
have produced a usable result even had it completed. It remains quarantine
evidence: do not promote or resume it.
