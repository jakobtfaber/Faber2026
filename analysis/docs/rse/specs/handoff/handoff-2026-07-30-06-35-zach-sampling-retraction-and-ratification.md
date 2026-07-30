# Zach sampling correction and run handoff

## Authoritative decision

On 2026-07-30 the manuscript owner visually compared the 32.768- and
65.536-microsecond DSA-110 profiles, said they looked almost identical, accepted
65.536 microseconds, and requested the component-count experiment. The owner did
not select native sampling. Figure 1 and Figure 3 remain unapproved.

Commits `fbeb68e..a539c23` incorrectly replaced that conditional ruling with a
categorical native-resolution decision. The focused repair restores the direct
owner statement. The profile diagnostic remains useful but does not supersede
it:

- a threshold-only peak finder reports six native versus four averaged local
  maxima;
- requiring two noise standard deviations of prominence gives four in both;
- the two extra native maxima are low-prominence shoulders;
- the diagnostic uses a one-dimensional profile, not the 24-channel joint-fit
  likelihood, and cannot determine the physical or fitted component count.

## Controlled run

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

## Required next actions

1. Verify the corrected owner attribution, schedule, queue, and run-isolation
   tests independently.
2. Merge the focused analysis repair and deliberately update the parent pin.
3. Deploy the pinned analysis commit to a clean h17 clone.
4. Start the 27-rung 65.536-microsecond experiment under a new root.
5. Accept no component count until all fits, residual diagnostics, and
   multi-seed evidence comparisons complete.

Hostless dispersion-measure redshift inference, probabilistic sightline
searches, Figure 1, and Figure 3 are separate downstream work packages.
