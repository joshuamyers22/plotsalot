# M4 Adversarial Review

- Date prepared: 2026-09-14
- Review target: M4 categorical release candidate
- Preparation: implementation self-review
- Independent reviewer: Joshua Myers
- Status: Approved

## Findings found and corrected or dispositioned

| ID | Finding | Severity | Disposition | Acceptance evidence |
|---|---|---|---|---|
| M4-AR-001 | Separate bar and pie inference could drift in sample, table, or method | Blocking | Both renderers accept one `CategoricalAnalysis`; analysis aliases share one implementation | cross-renderer object-identity and injection tests |
| M4-AR-002 | Expanding aggregate counts could violate memory ceilings and change physical-row audits | Blocking | Validate integer counts and aggregate directly into an owned `int64` table; track physical and weighted totals separately | raw/aggregate equivalence, billion-count benchmark, audit tests |
| M4-AR-003 | Sparse cells could silently select a different test | Blocking | Apply the approved expected-count gate independently to every Pearson omnibus/follow-up and fail atomically | 2x2, general sparse, empty-margin, and grouped failure tests |
| M4-AR-004 | A paired table with mismatched support, no discordance, or an empty plotted margin is ambiguous or unrenderable | Blocking | Require the same two ordered levels, positive margins, at least one discordance, no C4/C5, and explicit `proportion_test=False` | paired analytic and failure tests |
| M4-AR-005 | Pairwise/stratum results initially omitted their exact subtables and direct confidence metadata | Blocking | Retain observed subtable/shape on every follow-up and `conf_level` on the result; reject incomplete or contradictory records | result/schema contract tests |
| M4-AR-006 | Adjustment could be accidentally pooled across omnibus, pairwise, strata, or outer groups | Blocking | Keep complete C4 and C5 families separate and record no correction across outer groups | independent R references, family ordering and grouped-scope tests |
| M4-AR-007 | Disjoint grouped categories could exhaust the common palette after partial rendering | Blocking | Validate the combined typed `x` domain during grouped analysis and resolve colors before creating the first group figure | grouped common-color/domain and atomic-failure behavior |
| M4-AR-008 | A complete 190-comparison annotation family could be clipped or silently shortened | Required | Retain every comparison, wrap annotation text deterministically, and grow the owned figure under a fixed bound | all/none display tests and 20-level benchmark |
| M4-AR-009 | Upstream method names could be mistaken for approved parity | Blocking | Classify Fisher pairwise, McNemar paired, Pearson's C, and unadjusted stratum behavior as adaptations; assert raw objects retain the differences | compatibility matrix and oracle verifier |

## Independent review checklist

The reviewer should verify table orientation, declared Enum and deterministic
Categorical/scalar level ordering, null precedence, zero cells, raw/count equivalence, expected-count
rules, ratio key alignment, C1–C5 statistics/effects/intervals, paired
orientation, complete Holm families and scopes, renderer/result traceability,
grouped atomicity/colors, schemas, compatibility wording, oracle adaptations,
resource ceilings, benchmark distributions, and isolated package behavior.

## Independent reviewer decision

Joshua Myers reviewed the release candidate, checklist, and dispositions above
and approved the independent adversarial review without revision on 2026-09-14.
