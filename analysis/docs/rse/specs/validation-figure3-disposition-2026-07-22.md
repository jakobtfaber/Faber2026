# Figure 3 disposition

**Status:** source replay complete; owner visual approval pending.

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

Law et al. (2024) Table 3 supplies the older host redshifts: Zach
`z=0.043040`, Whitney `z=0.477958`, and Oran `z=0.30039`. Pipeline pull
requests 220--223 replay and freeze the complete source chain and deterministic
rendering at merge `f3c8d22a9088914e0179cfecf1ee4086777dc927`. Chromatica's
NED row has the `PUN` flag, no quoted uncertainty, and an unknown photometric
method. It is therefore inconclusive and excluded from the Figure 3 system
rows.

The frozen expanded-catalog build SHA-256 is
`6d7881c243613149b436de53e69b02d575041b84918f801a9c03a6d927329aef`;
the Figure 3 input SHA-256 is
`ce0179a27fd2d4f18b7599cea9f8d56f98874d9c4c6a7a654e84395ff163acc3`.
Two live source replays produced no scientific differences and identical
payloads apart from their timestamps. The original seven pre-freeze DESI
response payloads cannot be reconstructed; this is a recorded provenance
limitation, not an active gate, because current selected rows and full
responses are now frozen and independently replayed.

The review slot deliberately has `protect_in_manuscript=false`: the manuscript
already includes older Figure 3 bytes without a receipt. Promotion must flip
this flag in the same reviewed change that installs the approved candidate and
receipt; this avoids retroactively failing unrelated checks while keeping the
new bytes unpromotable through the review command.

The superseded batch `2026-07-22-fig3-verdi-roster` and its candidate SHA-256
`dcac3181a06e42b9466b75cbaee80623fcda821afd14b38bc939fb0f152ab291`
must not receive approval. Analysis pull request 20 and its timestamp-bearing
candidate are also superseded and were closed unmerged.

The definitive candidate is in batch `2026-07-22-fig3-source-replay`. Its PDF
SHA-256 is
`45017274a7e3d60cf6918d72c3e89558c0e9d50e27427d39a216547c4999fa6c`.
The manifest binds that PDF to all seven frozen evidence artifacts and the
pipeline merge above. Two independent full renders, without
`SOURCE_DATE_EPOCH` and separated by two seconds, are byte-identical. A
two-process regression test enforces this property.

No manuscript bytes are changed. The only remaining human-only gate is
manuscript-owner visual approval of that exact PDF. After approval, agents can
perform the remaining non-human work:

1. install the exact approved bytes and approval receipt;
2. set `protect_in_manuscript=true` in the same reviewed change;
3. compile the manuscript and replay the release gates.
