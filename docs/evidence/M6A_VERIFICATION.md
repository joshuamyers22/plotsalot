# M6A Verification Evidence

- Date: 2026-09-14
- Scope: approved R1–R3/G6 robust analysis, schema-v2 results, semantic
  rendering, extraction/grouping, deterministic resampling, resource bounds,
  compatibility, oracle/calibration, benchmark, and package gates
- Technical result: release-candidate gate passes
- Acceptance result: independently reviewed and accepted by Joshua Myers on
  2026-09-14

## Statistical and sample evidence

- The shared kernel retains `n`, `g=floor(0.20*n)`, `h=n-2*g`, both marginal
  Winsorization boundaries, the 20% trimmed mean, Winsorized sample variance,
  and `q=(n-1)*s_w^2/(h*(h-1))`. It rejects fewer than five observations,
  non-finite values, an unapproved trim fraction, and degenerate scale.
- R1 implements the approved analytic trimmed-location t procedure and
  two-sided estimation interval for histogram and overall/per-label dot
  centrality. It retains the raw difference and typed absence of an unapproved
  standardized robust effect.
- R2 implements marginal Winsorized Pearson association, the approved `h-2`
  Student reference df, exact-boundary handling, and paired type-7 percentile
  intervals. Same-seed calls replay exactly; different seeds change only the
  stochastic interval; typed identity streams survive variable order and
  `PYTHONHASHSEED` changes.
- R3 implements ordered two-group Yuen inference, Welch–Yuen multi-group
  inference, complete Holm/none contrast families, subject-level trimmed
  differences for two repeated conditions, and the approved Winsorized
  repeated omnibus/epsilon calculation for three or more conditions.
- Fixed-trim location/scale equivariance is tested from `1e-100` through
  `1e100`, along with controlled tail contamination, ties/degeneracy, effective
  sample boundaries, pair directions, complete-block subjects, matrix
  symmetry, grouped identity, and atomic failure.

## Oracle and calibration evidence

The pinned R 4.5.1 environment retains raw ggstatsplot robust objects for
histogram, scatter, between-group, and repeated-group fixtures. Separate base-R
code independently implements every approved deterministic kernel, R1 test and
interval, R2 point/test calculation, Yuen/Welch–Yuen family, repeated omnibus,
epsilon, and repeated contrasts. Python agrees at relative tolerance `1e-10`
and absolute tolerance `1e-12`; the slightly wider relative tolerance is
predeclared for cancellation in the repeated covariance expression.

The verifier deliberately does not demand equality to incompatible upstream
defaults. The retained upstream one-sample object uses bootstrap-t limits, the
scatter object uses ordinary `n-2` reference df and a normal interval, and the
upstream repeated effect can be non-finite. M6A's adapted outputs are accepted
against the approved formula and calibration evidence instead.

`m6a-correlation-calibration.json` is a locked 300-case coverage study at
`n=40`, 999 bootstrap resamples, generating Pearson correlations -0.5, 0, and
0.5, and 11,988,000 total resample-work units. Population Winsorized targets
for nonzero scenarios use separate two-million-draw reference populations.
Observed 95% interval coverage is 0.94, 0.99, and 0.95, within the predeclared
0.86–1.00 finite-study band. All 299,700 replicates are valid. A separate
deterministic rerun reproduced the artifact byte for byte.

- Oracle manifest SHA-256:
  `f524877da50b67c755708676b737ae3464c6bf2751014ae77776aedfa610d97d`
- Calibration SHA-256:
  `dc48472010f0f0d35ac18dc74f829433037c1bd15b7e709febe38037c92a9463`

## Result and rendering evidence

- Five immutable robust result variants use schema version 2 and are declared
  by `schemas/robust-result.schema.json`: one-sample, dot, correlation,
  correlation matrix, and comparison. Nested method, kernel, test, effect,
  resampling, level, pairwise, and correction dataclasses reject contradictory
  or non-finite states.
- Renderers consume completed analysis objects only and display the retained
  trimmed/Winsorized target, uncertainty, effective count, raw effect,
  multiplicity status, and limitation warnings. They perform no resampling or
  inferential recomputation.
- Direct and all six applicable grouped surfaces render successfully.
  Extraction preserves exact result identity; composition continues to retain
  the source result. Grouped association records the caller root seed and total
  work at the outer result, while each child records its deterministic derived
  seed and identity. Invalid child data fails the entire operation.

## Resource and performance evidence

The default and hard resampling ceilings are 100,000,000 and 500,000,000
sampled-pair work units; the batch index ceiling is 1,000,000. Resample count is
an odd integer from 999 through 9,999, and at least
`max(950, ceil(0.99*B))` replicates must be valid. Complete scatter, matrix, and
grouped work is preflighted before any draw; no fallback, resample reduction,
pair loss, or partial result is allowed.

`benchmarks/results/m6a-baseline.json` retains five warmed samples per measured
phase. Robust histogram analysis medians at 10K/100K/1M rows are 1.36/5.02/50.23
ms with 0.32/3.20/32.00 MB median incremental Python peak allocation. A
999,000-work representative R2 analysis has a 352.28 ms median. Maximum-shape
20-level between and 100-subject-by-10-condition repeated analyses have
127.48 ms and 57.95 ms medians. The resource grid explicitly records accepted
and rejected 10K/100K/1M scatter and 10/25/50-variable matrix requests under
the approved ceilings; rejected shapes are not executed or silently reduced.

- M6A benchmark SHA-256:
  `4417b3288600dbdd8fb115a04fb823ce3352fa222238d777a07e864c627563d7`

## Python production gate

- Ruff formatting/lint and strict Pyright pass.
- 199 tests pass with 92% repository branch coverage. The M6A formula/resource
  module has 96% branch coverage and the robust result-contract module 93%,
  exceeding the per-domain 90% requirement.
- OSV reports no known vulnerabilities or adverse project statuses; dependency
  license policy passes. M6A adds no runtime dependency.
- Source distribution and wheel build successfully. A fresh offline virtual
  environment installed the wheel and completed seeded robust analysis,
  rendering, and exact extraction-identity checks.
- The expanded oracle and benchmark verifiers pass. A second clean pinned-R
  container run reproduced the retained oracle manifest exactly.
- Wheel SHA-256:
  `94e31e61e186427b94b6ae14b65e711a69b402c1aaf7a20285bf04a0c2516b75`

## Independent acceptance

Joshua Myers independently reviewed the implementation and evidence, reported
no new finding, accepted all adversarial dispositions, and accepted M6A on
2026-09-14. R4, B1–B6, M6B, M6C, M6, and the `0.4` release remain outside this
decision.
