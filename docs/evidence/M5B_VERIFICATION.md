# M5B Verification Evidence

- Date: 2026-09-14
- Scope: M5B Python study boundary, approved MA1–MA4 analysis, typed result,
  semantic renderer, extraction/composition, tests, benchmark, and package gates
- Technical result: core implementation passes its Python and pinned-R gates
- Track result: independently reviewed and accepted as the M5B technical
  candidate; shared M5A integration and final M5/`0.3` acceptance remain open

## Statistical and sample evidence

- `StudyEffectTable` accepts 3–500 studies by default from exact `term`,
  `estimate`, and `standard_error` fields, retains every source row, owns
  read-only `float64` arrays, and rejects null, duplicate, non-finite,
  nonpositive, ambiguous, oversized, and unrepresentable inputs.
- Analytic equal-variance fixtures reproduce the arithmetic pooled mean,
  closed-form REML tau-squared, Hartung–Knapp variance, Q, and I-squared.
- A separately implemented golden-section optimizer over the restricted
  likelihood reproduces the production REML score-root result for unequal
  variances to seven decimal places.
- A pinned R 4.5.1 oracle retains the raw ggstatsplot result, independently
  solves the scale-normalized REML score in base R, and derives every approved
  modified-Hartung–Knapp, prediction, heterogeneity, weight, and study field.
- Pinned metafor 5.0-1 independently corroborates tau-squared and both its
  upstream normal and `adhoc` pooled-inference paths. The verifier asserts that
  the approved modified-Hartung–Knapp standard error is not mislabeled as the
  upstream default normal result.
- Zero-boundary, three-versus-five-study prediction, scale-equivariance,
  bracket-expansion, source-order, descriptive study inference, and complete
  weight/contribution reconciliation are tested.
- A deterministic 300-case development fuzz audit covered 3, 4, 5, 10, 100,
  and 500 studies across scales from `1e-100` through `1e100`; all normalized
  weights reconciled and no unexpected analysis failure occurred. This audit
  is supporting context, not a retained test artifact.

## Result and rendering evidence

- `CoefficientResult` is frozen, finite/JSON-safe, governed by
  `schemas/coefficient-result.schema.json`, and rejects contradictory method,
  interval, weight, contribution, convergence, boundary, prediction, degree-of-
  freedom, label-limit, and pooled records.
- The forest renderer uses the retained null, study points/intervals, pooled
  estimate/confidence interval, separately labeled prediction interval,
  statistical-label policy, declarations, and diagnostics. Rendering never
  calls the analysis routine.
- Extraction preserves the exact result object, and the existing composition
  path retains that identity in an M5 panel.

## Performance evidence

`benchmarks/results/m5b-baseline.json` retains five warmed measurements for
selection, complete analysis, and rendering at 3, 10, 100, and 500 studies.
Every size covers equal/unequal sampling variances crossed with zero/positive
heterogeneity. Input-frame construction is outside the measurement boundary.

At the 500-study ceiling, selection medians are 0.48–0.54 ms, complete analysis
medians are 98.0–98.9 ms, and rendering medians are 1.98–2.00 s on the retained
arm64 host. Analysis peak Python allocation is at most 380 KB and rendering is
approximately 34.6 MB across these ceiling cases.

- M5B benchmark SHA-256:
  `4757d45695f2da2ee2a35c185aa0c0156132ce9848b4a98c6edb37956d94cc22`

## Python production gate

- Ruff and strict Pyright pass.
- 163 tests pass with 92% repository branch coverage. New M5B modules cover:
  study data 100%, analysis 91%, result contracts 97%, and renderer 96%.
- OSV reports no known vulnerabilities or adverse project statuses; dependency
  license policy passes.
- Source distribution and wheel build successfully. An offline clean temporary
  environment installed the wheel plus locked cached runtime dependencies and
  passed an M5B analysis/render smoke test.
- The expanded pinned oracle and benchmark verifiers pass.
- Oracle manifest SHA-256:
  `3f38642d15097b4785ac5432e6359eaeff542add9b7f344ef18c0447b1981b5a`
- Wheel SHA-256:
  `31e52616a9455218797d9d32a502fd73a280d7fc33048c4c40967c017a5a1298`

## Open gates

- Implement M5A and prove both modes consume the shared coefficient-result and
  renderer contract.
- Run the combined M5 production gate and obtain final M5/`0.3` approval.

## Independent acceptance

Joshua Myers independently reviewed this evidence, reported no new M5B finding,
and accepted the M5B technical candidate on 2026-09-14. The acceptance does not
waive the M5A/shared-contract or final M5/`0.3` gates.
