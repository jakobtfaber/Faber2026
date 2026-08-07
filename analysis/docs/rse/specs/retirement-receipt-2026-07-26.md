# Retirement receipt — three-repo branch shutdown (2026-07-26)

**Objective/phase:** Phase 3 (retirement) of the owner-chartered closure
campaign. Owner approved the retire list in `closure-roster-2026-07-26.md`
in-session on 2026-07-26 ("I approve the 128-branch retire list").

**Count correction.** Previous claim: 128 branches. Corrected: the roster
actually names 132 (16 parent, 110 analysis, 6 FLITS) — the prose totals
were mis-summed; the named set is unchanged. Practical consequence: none;
every deletion below is a branch named (or class-defined) in the roster.
Additionally 2 same-class branches created by the campaign itself
(`codex/pin-alignment-20260726`, `docs/closure-roster-20260726`, both
PRs merged) were retired, for 134 total deletions.

**Verification at the one-way door:** each ref's live SHA was captured by
`ls-remote` immediately before deletion (manifests below); no retire branch
was the head of an open pull request; parent/analysis/FLITS keep-lists
confirmed intact after deletion (9 / 3 / 13 branches remain, listed below).

## Deleted refs (SHA at deletion)

### Faber2026
```
5ea3fad3aa8ed9e1fc1be2530d7f7a346f864882 infra/owner-board
001fd81e4f142d9a2e605c4873661b906405ff99 ms/fig1-dm-drift-closure-20260717
c2820a3c60d6bf6846575f2f50edb4da141405d7 docs/authority-roles-proof-20260720
6e6a986b78bc46d9d3dbb23415dac5252543cdef research/foreground-redshift-verdicts
2b33c05215fbfb78782a12039fa7f1cc50322505 codex/expanded-foreground-phase-two-review
9ea975de30549ff996bc93ab6692c67a7eb74fb0 codex/expanded-foreground-map-closure
c27f6279a96d0436c2264b7a4cf34ea7e45ed740 codex/figure3-source-replay-pins
7b060fee1fb76b6c64055238588f9eb575458462 codex/nine-sightline-search-contract
46a34a79f2d39e4fefc7e55e162261494939fb30 codex/nine-sightline-search-contract-successor-20260722
724f6311841eda513466f6a6159e07fbb5afd3da codex/chime-rfi-preservation-gates-successor-20260722
cd5b67bd782608064cb1a2f6a164a52b12a43dbf codex/prototype-chime-rfi-preservation-gates
c62dab8e53ea0b498a8b06ee2b5b67a47a604662 codex/wayfinder-07-pin-host-redshift-evidence
65367b178d99920892dc9a108e44cf01a43954bc codex/host-dm-repair-v2
2063726d786e7ef60247256e6d1a7179c0635611 codex/pin-analysis-owner-queue-fix-20260724
3a58378fbcf7aae12d2c3db26cd730dbd932a97a docs/special-ref-maintenance-20260724
94052932dce402551cb124a465e3f1ff6c779ad2 research/rfi-route-validation
```
### Faber2026-analysis
```
ba4c75e2ae66348e0ebc82cc5a12af3bfd7aa1b0 codex/adjudicate-host-redshift-identifiers-19
7c45a2e8ca828dfdbbbca0034a6df0da1dc2066c codex/apj-wayfinder-closure
cef8aa795c4333036e838f476e980fe86fee2e22 codex/apj-wayfinder-finalize
ebb7e469df87316b7335e8c2b3ec2ca493772aba codex/assign-open-issues-jakobtfaber-20260723
37653b91341c7874cef9b0daaa1bce749fe466d9 codex/authoritative-pass-gates-20260722
253d7ea542a85f8c0a13ce58d6634709adbc48e0 codex/auto-resolve-expanded-crossmatch-contract
9ac847879f5dd2970bdb15c7b00bf01942b1bc54 codex/auto-review-count-audit
e2841ecee58be1c3bb20037d778342521dc935cb codex/auto-review-rfi-preservation-limits
75b9d5f62bbf8bf0526ad733add64a395ca8444d codex/auto-review-trust-ledger
2b47740521dbcb144ff9923fbd1c8a2de72c4ae0 codex/auto-set-expanded-figure3-gate
fab50f1266ee345fe75778f6f01639f5f5ae17ca codex/chime-rfi-validation-route
12af19948795c165a78ce97ee3a0d8315002571d codex/claim-coverage-drift-packet-20260724
22cabfe867fe6d1cb65104e3ad9431ef0a8f46e7 codex/close-crossmatch-contract-02
68f52cc6e69a0eed4871a75c802c2450b2d2ea47 codex/close-expanded-foreground-tickets-02-03
b57025a9d07219c0f94e4e9325f09ca5c34e699e codex/close-physics-authority-03
bfd37dc8ee9fce1b9c2f7d4dfc3756edc92efe7d codex/close-ticket09-controller
19ad2dde99a4649cfb6e3dfa70919e820bdc5025 codex/controller-queue-hardening
2b0effb97598b331fe3efb331cfdc91efbc7f0e1 codex/convergence-wave-20260722
304a177a931003d41b03fb0925b9d993c77d6373 codex/expanded-foreground-map-closure
e2d2cd58942301c65f9fc17287f4629f04996374 codex/fail-closed-rfi-route-20260722
bc57892e55c7656028b79e194607f5b367a2feb4 codex/figure3-source-replay-deterministic
418b79d911b5599ddbf235ecac7bd4519d54302d codex/figure3-source-replay-final
449b0d2d698d7ef2b21b34c482e3d89a90f0694d codex/final-author-decision
7bbc4382c80872fca4bd3a002463801ff3c14da1 codex/fix-owner-queue-resolved-redshift
6addaced9400dc8442469bb50857ef8d7271573f codex/fix-path-hint-test-20260723
faf249a5eb91597f0b56ade1f915a3264365e279 codex/foreground-control-refresh
c5486aa078868c216936d2c9658b0b51db3676cc codex/foreground-six-row-identities
c905f2d721aea72e388ab76229647d5760ea44ce codex/handoff-joint-scattering-20260723
a172521d96395de3169a840fe189e18b81c68636 codex/host-dm-repair-v2
5fbbf8db34c3e5d23a40f802531825204c167837 codex/host-dm-trust-ratification
ba258cd04d331525d494d0323be5a2911a37135a codex/integrate-trust-baseline-20260723
cd56108f04c1e5bafb8418601e2bdfbf444deec1 codex/issue-map-reconcile-20260722
0578adf3d043251c8b087faa3dcf3c77564fe99a codex/johndoeii-c2d2-controlled-rerun
2d523d6741527b6cc79b03ccba00d581807935a1 codex/joint-scattering-controlled-20260722
f73fe88d91b73659506d2345b84a28076f76245d codex/joint-scattering-owner-ci-20260722
71df983c2073c7f7a3512c736f1a5e7ece5ff82c codex/joint-scattering-repro-20260722
546c6f762a2f046cfe096f7125e4ad671ff34b1e codex/joint-scattering-runtime-20260722
f5ddde013d68c2f501859071bf0cf23abff545e7 codex/jointtf-v2-evidence-preservation
53e647e4adec4c44f3f6c8f8fd45655acf0d724f codex/kb-persistent-fastembed-cache-20260723
6c0e9b3640061ba95df54cc457898fb24824a3e2 codex/nine-sightline-cherrypick-resolution-20260725
33a61ad894c6e41b7d3f91664fe3edf2a1f5fa8d codex/nine-sightline-search-contract
cb76795b7008b8077955daafb6c7bb1718990d1c codex/oran-c1d1-controlled-rerun-20260723
bad41d81c726dc1ed2461b273723313cad5c1245 codex/owner-queue-date-independent-20260724
cd000487f7350bf59b58b6cf422fab80682b5809 codex/packet-coauthor-candidates
280a38722f48e74efb4d13497fb71f0b3c9b6644 codex/packet-rfi-preservation
16b29015e49e25280eb93dd9a155d241660eeeff codex/packet-technical-robustness
46df12fad47d5bc4078118cc5286cb14c84334f9 codex/phase0-queue-accounting
45b6430bea213af039c8965c0b64aacd4f815af3 codex/phineas-probabilistic-crossing
409524dba05cf1d0a779d47f22d854a95ec5459c codex/protected-corpus-15
5b27e3db7105f82b581153badd8043e6b601610e codex/reconcile-board-owner-markers-20260724
e444494d96e710c1b2a20e5e5196322158533e38 codex/reconcile-dm-signoff-board
695b602129fc1a491fb18b92c62eb650dcd31eb3 codex/reconcile-parent-integration-20260723
2f8d66f2f7c77a29a3b43261223d4fa8af83bcef codex/record-no-approved-figures-20260723
a2efef51f2220c0b18c0a13858dffacb80eaa8da codex/refresh-owner-queue-20260723
d74e862947ee9ba67e3c8a179d810ab4a9f733ee codex/repair-parent-pin-gates-20260723
0087378b99129db44746d4ac13002c187f6785d9 codex/repair-root-science-governance-20260724
058d293c70f2b93716997d81a6fff23968efc4e6 codex/repair-ticket14-authoritative-roster
26276d0a6ed4bdbd5de796c351093fc2d7fe9d3a codex/replay-nine-sightline-corpora
78d04ed31587341432884a014957a0558d452487 codex/repository-archive-audit-20260722
23a8ed103cc8cdaf9a83c83b63b242a0229f17f2 codex/resolve-dsa-denominator
97866e78e51d293f1bfb4c6f0befb0f6aedf4592 codex/resolve-free-alpha-reporting
5292337ffc6c0bb918a763860d70c0575530ae61 codex/resolve-trust-assessment
32b8f764bc3a503dac5464606053a78e6295a277 codex/retire-figure3-gate04-controller-20260724
bc5b7f93dcc0d92594af637d6f6509893cd66af0 codex/review-count-audit
9e026c79e2ab7bc366744efba4c6d52241ca966c codex/rfi-validation-01-owner-disposition-20260726
f0d26f89d88f49d77be2812cb3b2c98c11aed349 codex/rfi-validation-contract-20260723
4ef360d6c781383565b456cff7929610648aa756 codex/ticket20-injection-component-count
abaf5ead47e1c2d3ab66697a004dead5a6f385ca codex/ticket6-controlled-panel-admission
1b7c29ef7923ef9b547abf5fe9f31261a477de6c codex/trust-decision-packet
4d08d18c8c75e35726208bf6c0c311f22459f598 codex/unblock-wayfinder-tickets
4e6d1b3963f648401b655c1b4de4808480b00db0 codex/update-owner-queue-after-redshift-resolution
04453ca6ce6435cb65ca0d5de492c48375fc1e6d codex/verify-foreground-sources-09
361584b4cc260cdb1aa5f506042b11e970033f0a codex/visual-science-review
c81784675310fb0f809d5107aa06e768382beabc codex/visual-science-review-v2
75570ce4bdb51d7e130c5bb3ea18188882cd863f codex/wayfinder-07-freeze-host-redshift-evidence
2c2183c05c1d5bd7b0d69dcbf5be1d61bcf84a44 codex/wayfinder-07-host-redshift-provenance
c005a4d71928eff023a4503cb25d121fe1f4843d codex/wayfinder-18-law-host-redshifts
5e8d88ef7dc2e858b278933614d8e2b214d87caf codex/wayfinder-18-law-host-redshifts-v2
b1686cde4c56416c3a9aeacdb926a54a3d0c4e7a codex/wayfinder-default-recommendation-approval
2a69ade8e7db9670d805a8e4665aad632ac50e5e codex/wayfinder-frontier-reconcile-20260723
933e795abe1c4bb3e0aeb287508c3181da6c8932 codex/wayfinder-host-redshift-authority-claim
b4fa11be18a496c4f5d3d4ecefcef2e9aaf77b0d codex/wayfinder-host-redshift-authority-resolution
bc0403c5b221d97ddac0e2e6d5f8cd6acae305a5 codex/zach-c2d4-controlled-rerun-20260723
0f351717343c457111aee9090b481555091252ed codex/zach-chime-manual-map-amendment-20260726
2afbd06ec28cee80fe82cb3199f0477bcd361ad6 docs/land-trust-deltas-20260724
b977303855b7facfa28002c7cd3f919120ff3c36 docs/nine-sightline-divergence-packet
26503a06a13a5d26cf14e37b129e220465ff9323 docs/plan-scattered-work-integration-retirement
d76269e208fb0c87b4ec1a3d2e926d830ce6049e docs/raw-chime-definition-20260724
c4696e451e5fde3de7dfed9085bd2f6db7bf43a5 docs/receipt-family1-rfi-20260726
eac6d4ffe49dc4d3bf5d5edb031d2ba0a276833e docs/receipt-family2-hostdm-20260726
ebaa4105ec369af28ce25648db72488f8897cf63 docs/receipt-family3-foreground-20260726
289edd6624583250dcfea3b577508f463008d0f5 docs/receipt-family4-trust-20260726
ad965a634737cf0d8536c25fa8138102b144b36c docs/receipt-family5-scintillation-20260726
974b770b3401954b436019ce3bcb0ef93527d8be docs/receipt-family6-landing-20260726
560877c5a09a9413acb86bdbcadbfa1eb5e00006 docs/receipt-final-deletion-20260726
360c5d49bb5cf7b2b34f14bf24369ae3943f4cf2 docs/receipt-flits-wip-capture-20260726
582ad75b86d0e573bdc5d757f3295e50edda1864 docs/receipt-phase3-sidecheckouts
b744cc70d396c1cf9e727133815f1ca3f54b96e9 docs/receipt-phase4-preservation
9500bb12300e5be848a88b0f4a3f32d6ec7e2174 docs/receipt-phase5-followup-sweep-20260726
402d3b440883935f58c33efb61c192846d8dd05b docs/receipt-phase5-trackA-batch1
719f57895e2fd1f07000f1f09af083411f7319c8 docs/receipt-phase5-trackA-batch2
89e25c5021a4bafd5d108bc2416709350dffa1d6 docs/receipt-phase5-trackB-batch3
713da510f3140dd36489376cdd41f90a4b525d13 docs/repoint-retired-overleaf-paths
415e2ce644455c1bdc39f5177991c80c530bf9a6 docs/repository-map-landing
3ff3bdd26ad112c06825bb5897cac3eb1b7b7136 docs/rfi-packet-caption-fix
0f28950fd720abce1533f17c7a072994d9e3ff12 docs/rfi-preratification-packet-20260726
047ea425321f748d3c24eff17b3a80e8ce6ecf80 docs/roster-branch-landing-20260726
ef3bae792d2cd2fc8d3e5c9198038b52bb875414 docs/scattered-work-rescue-records-20260725
875765c64070b2b2b54fd93a3a9708cd68bf1f70 docs/technical-review-decision-packet-20260724
819a22be6b7768caf5ff97d47378a8e85ec2cbca ms/checkout-advisory-triage
745f321f44415acd3d30afe8d70c27dc727d500b codex/pin-alignment-20260726
b0730e767bb60ba595f797541a376a8f47dee6fe docs/closure-roster-20260726
```
### dsa110-FLITS
```
5cffcb395df443d5afcbb09517588fc685beb73f joint/tf-fit-window-resolution
c46c8e508bc152902f860a45c4baade3afdb8889 codex/figure3-deterministic-pdf
dac02d96f96788d4a96b9cb721c4e26281addd1a codex/model-grid-exact-support-20260722
45605249dc5e454b1f2d0d31d6b40d7b8419ecec codex/auto-freeze-candidate-redshifts
7d26b1f7d3747afebb0ed7064d3058d25fb33396 codex/auto-freeze-candidate-redshifts-mainpin
8f63185cc9b9f2a9810f5a4f2e275216427bd194 codex/b4-figure-review-20260720
```

## Surviving branches (post-retirement, verified)

- **Faber2026 (8 + main):** codex/final-author-block (open PR #216),
  codex/scintillation-notebook-wayfinder (provenance-load-bearing:
  registry cites 8d492fea for budget_table.tex), entire/checkpoints/v1,
  gh-pages, overleaf-2026-07-11-2125, publish/repository-provenance-map-followup
  (DECIDE), rescue/science-gates-parent-20260722.
- **Faber2026-analysis (2 + main):** codex/auto-set-expanded-independent-validation
  (CARRY: ticket-05 agent lane), publish/repository-provenance-map (DECIDE;
  its two alignment commits were landed via PR #119).
- **dsa110-FLITS (12 + main):** four pre-rewrite lineages, archive/foreground-
  source-freeze-pr231, four rescue estates, rescue/wip-crossmatch-scint-20260726
  (CARRY), codex/chromatica-cross-band-scintillation (DECIDE, scint hold),
  publish/repository-provenance-map (DECIDE).
