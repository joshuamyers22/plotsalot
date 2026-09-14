# M0 Adversarial Technical Review

- Date: 2026-09-14
- Scope: upstream identities, one-sample walking skeleton, R oracle, retained
  fixtures, benchmark baseline, packaging boundary, and milestone claims
- Technical verdict: approve
- Formal milestone verdict: approved after accountable sign-offs
- Review ceiling: three evidence-changing passes

## Findings and dispositions

### M0-001 — stale R binary repository could not satisfy pinned upstream

- Severity: blocking.
- Evidence: Rocker defaulted to a 2025-10-30 binary snapshot whose dplyr,
  ggplot2, and statsExpressions versions were below ggstatsplot's requirements.
- Correction: use an immutable R 4.5.1 base, install all native prerequisites,
  and restore the full dependency closure from `oracle/renv.lock`.
- Acceptance: a clean lockfile-driven image built all 107 packages and verified
  ggstatsplot's exact `RemoteSha`.
- Status: closed.

### M0-002 — upstream behavior was not equivalent to the prototype contract

- Severity: blocking if mislabeled.
- Evidence: direct extraction showed Hedges' g with ncp uncertainty and upstream
  acceptance of non-finite and zero-variance fixtures. The Python specification
  uses Cohen's d without uncertainty and rejects both states.
- Correction: retain raw upstream results, normalize shared fields, explicitly
  document the adaptations, and make the verifier assert both sides.
- Acceptance: three ordinary fixtures match shared fields at `1e-12`; two
  boundary fixtures enforce the documented divergence.
- Status: closed as an explicit prototype adaptation.

### M0-003 — evidence could drift outside the ordinary quality gate

- Severity: high.
- Correction: hash inputs, outputs, generator, Dockerfile, and lockfile; validate
  both oracle and benchmark artifacts from unit tests without R or network.
- Acceptance: 54-test full suite passes and artifact mutation causes failure.
- Status: closed.

### M0-004 — required accountable approvals were unassigned

- Severity: blocking for formal closeout; outside technical authority.
- Resolution: Joshua Myers approved the M0 statistical specification,
  ADR-010's approved upstream scope, and the MIT distribution license on
  2026-09-14.
- Status: closed by accountable sign-off.

## Residual limitations

- The benchmark is a local baseline, not a cross-host performance guarantee.
- Incremental peak allocation uses tracemalloc and excludes the already-created
  input dataframe for both phases.
- Scatter and correlation workloads join the benchmark grid only when
  implementations exist; placeholder timings would not support regressions.
