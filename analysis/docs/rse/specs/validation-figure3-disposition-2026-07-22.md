# Figure 3 disposition

**Status:** calculation-complete; scientific promotion blocked.

Pull request 174 is superseded. Its pipeline pin predates current `main`, and
its Figure 3 candidate used the stale host roster: Wilhelm had `z=0.510` while
johndoeII had no redshift. Those bytes must not receive owner approval.

The exact owner-adopted Verdi draft source is now identified. The 2026-07-17
Overleaf export archive has SHA-256
`88cab4b89d13dffb9cdaae49edb24455a66dfd99f4c7ca23bebcc86676043621`;
its inner `verdi2025.tex` has SHA-256
`ea094a20d5cac53d79fde24e696c5c4aca967d82067e3dc7f23c8a6cdb640e90`.
Table `tab:burst_props` reports `20221203A` as `--` and `20230814B*` as
`0.5535`. No value is inferred.

Pipeline pull request 219 freezes the nine relevant source rows, repairs the
roster, and rebuilds the expanded catalog and Figure 3 input. The rebuilt
catalog SHA-256 is
`ad2e3689c4fb85102792450b2b14148be833b4a1e2c557bd5feb56d2448244f3`;
the rebuilt Figure 3 input SHA-256 is
`562fb2dffcf5dedc15e235e13af9cd3cc8d40ee229709d0813ac22c7e6781395`.

The review slot deliberately has `protect_in_manuscript=false`: the manuscript
already includes older Figure 3 bytes without a receipt. Promotion must flip
this flag in the same reviewed change that installs the approved candidate and
receipt; this avoids retroactively failing unrelated checks while keeping the
new bytes unpromotable through the review command.

The new candidate is routed through the immutable figure-review batch. It is
not installed in the manuscript. Promotion remains blocked on:

1. pipeline pull request 219 merged and downstream replay pinned to its merge;
2. independent source-level validation for the older Zach, Whitney, and Oran
   redshifts and the foreground-object redshift chains;
3. manuscript-owner visual approval of the exact candidate PDF;
4. approved-byte promotion, manuscript compilation, and release-gate replay.
