# M4 Verification Evidence

- Date: 2026-09-14
- Scope: approved C1–C5/G5 methods, raw/count tables, bar/pie rendering,
  grouping, schemas, oracle, benchmark, and package surfaces
- Technical result: release-candidate gates pass
- Milestone result: pending independent review and Joshua Myers's final M4/0.2 acceptance

## Statistical and sample evidence

- Joshua Myers approved Pearson C1/C2/C4/C5 paths behind the strict adequacy
  gate, exact two-category paired C3, noncentral/Clopper–Pearson intervals,
  separate Holm families, raw/count semantics, and atomic G5 grouping.
- Analytic and independent tests cover table orientation, deterministic level
  order, null precedence, zeros, raw/count equivalence, ratios, expected counts,
  Pearson statistics/residuals/effects, exact binomial probability and signed
  Cohen's g, interval containment, family membership/order/adjustment, and
  contradictory result rejection.
- Bar and pie renderers consume the same analysis/result object. Geometry,
  labels, totals, legends, colors, statistical annotations, and captions derive
  from typed result fields.

## R oracle and compatibility

Pinned R 4.5.1 and ggstatsplot revision `7a724cd0` generated retained one-way,
independent, paired, raw-row, aggregate-count, bar, pie, and grouped objects.
Base R independently normalized all shared deterministic test/effect/Holm
fields at the approved tolerance. Raw-object assertions preserve the deliberate
Fisher-to-Pearson, McNemar-to-exact-binomial, Pearson's-C-to-w/V, and
unadjusted-to-separate-Holm adaptations. `make verify-oracle` passes.

- Oracle manifest SHA-256:
  `4cd571ea2e29dd03c3a4e20e854bfe3282076a00e6fd9004bed807acb9bd9833`

## Performance evidence

| Ceiling workload | Selection median | Analysis median | Bar median | Pie median |
|---|---:|---:|---:|---:|
| 1,000,000 raw rows | 17.81 ms | 66.63 ms | 23.30 ms | 34.67 ms |
| 20 levels / 190 pairwise tests | 1.77 ms | 102.65 ms | 57.06 ms | 81.61 ms |
| 20x20 / 400 cells | 7.21 ms | 127.85 ms | 344.81 ms | 655.28 ms |
| weighted total 1,000,000,000 | 1.19 ms | 1.72 ms | 13.57 ms | 14.93 ms |

Twenty grouped analyses have a 23.36 ms median; 20-facet pie rendering has a
298.24 ms median. The artifact retains five warmed samples per phase and places
input-frame allocation outside the measurement boundary. Temporary same-host
M0–M3 reruns plus focused repeats found no sustained median time or memory
regression above 20%.

- M4 benchmark SHA-256:
  `a6164d64649f10617ab9fd0e680dd44ea97fa3cb4422a1ab87817ab937e8f03b`

## Production gate

- Ruff and strict Pyright pass.
- 145 tests pass with 91% repository branch coverage; every new M4 domain
  module is between 93% and 100%.
- Vulnerability, dependency-license, oracle, benchmark, build, and isolated
  wheel smoke gates pass.
- Wheel SHA-256:
  `46dc60ba13d19aac0102ef8bdc46892113a936dc5f96a1ee58c73332ecf95bf6`

## Remaining accountable gates

The technical candidate is ready for independent review. An independent
reviewer must record a decision and Joshua Myers must separately accept the
finding dispositions and final M4/`0.2` candidate before the milestone can be
marked complete.
