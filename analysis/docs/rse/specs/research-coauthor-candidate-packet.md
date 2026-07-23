# Coauthor source-list review

**Review date:** 2026-07-22

**Ticket:** [Prune and typeset the co-author list](../wayfinder/tickets/11-prune-coauthor-list.md)

**State:** ready for the consolidated owner review; no personnel decision made

## Result

The rule recorded in the ticket does not produce a candidate coauthor list.
The two named papers have **no shared individual author**, even under the
less-specific comparison of normalized family names. No person was added,
removed, ranked, or contacted.

This is a source-rule failure, not evidence that the manuscript should have no
coauthors. Authorship should follow verified contributions to this manuscript,
not membership in either earlier paper.

## Frozen source evidence

| Source | Published identifier | Ordered individuals | Author metadata |
|---|---|---:|---|
| Law et al., *Deep Synoptic Array Science: First FRB and Host Galaxy Catalog* | [doi:10.3847/1538-4357/ad3736](https://doi.org/10.3847/1538-4357/ad3736); [arXiv:2307.03344v2](https://arxiv.org/abs/2307.03344) | 22 | 13 ORCIDs; no affiliations in Crossref |
| CHIME/FRB Collaboration, *The CHIME Fast Radio Burst Project: System Overview* | [doi:10.3847/1538-4357/aad188](https://doi.org/10.3847/1538-4357/aad188); [arXiv:1803.11235v1](https://arxiv.org/abs/1803.11235) | 51, plus the collaboration entity | 4 ORCIDs; no affiliations in Crossref |

Crossref DOI metadata was fetched 2026-07-22 06:44 PDT. Response SHA-256:
`e75125127608345733f7d6966b84fe40b568f7fdcd20721128fb6b66bb1cfbba`
for Law et al. and
`d291069e9db0621b71dd070f10735a98e24b0bf9f5728dadb9949035412f5a0a`
for CHIME/FRB. The ordered names and counts agree with the author blocks in
the cited arXiv versions. The published Law metadata expands the final name to
Nitika Yadlapalli Yurk; the arXiv version says Nitika Yadlapalli.

### Ordered Law et al. list

Casey J. Law; Kritti Sharma; Vikram Ravi; Ge Chen; Morgan Catha; Liam Connor;
Jakob T. Faber; Gregg Hallinan; Charlie Harnach; Greg Hellbourg; Rick Hobbs;
David Hodge; Mark Hodges; James W. Lamb; Paul Rasmussen; Myles B. Sherman;
Jun Shi; Dana Simard; Reynier Squillace; Sander Weinreb; David P. Woody;
Nitika Yadlapalli Yurk.

The arXiv author block maps these authors to three 2024 affiliations: Caltech
Cahill, Owens Valley Radio Observatory, and Steward Observatory. Those are
historical source affiliations, not verified current affiliations.

### Ordered CHIME/FRB list

M. Amiri; K. Bandura; P. Berger; M. Bhardwaj; M. M. Boyce; P. J. Boyle;
C. Brar; M. Burhanpurkar; P. Chawla; J. Chowdhury; J.-F. Cliche;
M. D. Cranmer; D. Cubranic; M. Deng; N. Denman; M. Dobbs; M. Fandino;
E. Fonseca; B. M. Gaensler; U. Giri; A. J. Gilbert; D. C. Good; S. Guliani;
M. Halpern; G. Hinshaw; C. Höfer; A. Josephy; V. M. Kaspi; T. L. Landecker;
D. Lang; H. Liao; K. W. Masui; J. Mena-Parra; A. Naidu; L. B. Newburgh;
C. Ng; C. Patel; U.-L. Pen; T. Pinsonneault-Marotte; Z. Pleunis;
M. Rafiei Ravandi; S. M. Ransom; A. Renard; P. Scholz; K. Sigurdson;
S. R. Siegel; K. M. Smith; I. H. Stairs; S. P. Tendulkar; K. Vanderlinde;
D. V. Wiebe.

The arXiv author block maps these authors to fifteen 2018 affiliations. Those
are historical source affiliations, not verified current affiliations.

## Deterministic comparison

1. Exclude the collaboration label because it is not an individual.
2. Unicode-normalize names, remove punctuation, and lowercase them.
3. Compare normalized family names. This deliberately admits more possible
   matches than full-name comparison.
4. Result: zero shared family names; therefore zero possible shared people.

Initials, diacritics, and the Yadlapalli/Yurk publication-name change cannot
alter that result. No fuzzy identity match was attempted.

## Identity gaps

- The source metadata cannot establish current affiliations for any future
  candidate.
- ORCID coverage is incomplete and no ORCID is supplied for Jakob T. Faber in
  the Law DOI metadata.
- The manuscript currently contains `0000-0000-0000-0000` for Jakob. That is a
  placeholder, not a valid identifier. It must be replaced with an
  owner-verified ORCID or omitted.
- Preferred publication names, current affiliations, ORCIDs, and contribution
  roles must be confirmed only after the owner selects the roster.

## Consolidated owner choices

| Choice | Recommended default | Unlocks |
|---|---|---|
| Authorship source rule | Replace the empty paper-list intersection with an owner-confirmed roster of people who contributed to this manuscript. Keep the two papers as provenance references only. | A real candidate roster |
| Roster | Owner selects from the contribution roster; do not automatically import either paper's authors. | Identity verification and circulation |
| Order | Jakob first; remaining authors by contribution, alphabetically only where contributions are equal. | Stable `auth.tex` order |
| Identity fields | Each selected author confirms publication name and current affiliations. Include an ORCID only when verified; omit placeholders. | Typeset author block |
| Contribution statement | Collect CRediT-style roles from selected authors and include a statement if the journal submission uses one. | Contribution text |
| Circulation | Circulate immediately after roster confirmation; recommended date 2026-07-23, leaving eight calendar days before the 2026-07-31 target. | Coauthor reading window |

No edit to manuscript `auth.tex` is authorized until these choices are made.
