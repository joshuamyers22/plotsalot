# M6C Pass 2 Verification

- Date: 2026-09-15
- Scope: R4-M/B5-M aggregate robust and Bayesian engines and result variants
- Starting revision: `921ea52`
- Gate: passed with provisional statistical-owner boundary disposition

## Implemented slice

Pass 2 adds deterministic fixed-Student-t4 aggregate maximum likelihood with
three REML/median/fixed-effect starts, raw score/KKT convergence, ambiguity
checks, profile-likelihood confidence intervals and tests, and retained study
residual/latent/effective precision records. It also adds the proper-prior
normal-normal Bayesian hierarchy with analytic conditional-normal integration,
adaptive transformed Gauss-Kronrod quadrature, BF10, posterior population mean,
tau/tau-squared, true-effect prediction, and all four mandatory prior
sensitivities.

Both paths enforce the approved study floors, interval vocabulary, warnings,
typed absence reasons, deterministic work preflight/accounting, and strict
schema-v2/v3 immutable results. Robust and Bayesian rendering remains an
intentional pass-3 failure before figure construction.

## Formula and oracle evidence

- The robust hand fixture independently evaluates the Student-t4 log density,
  score/KKT equations, latent precisions, and nested golden-section profile
  endpoints. The Python estimate is `0.2751322305316832`, with boundary
  `tau_squared=0`, 95% profile interval `[0.1181625593, 0.4575575162]`, and
  likelihood-ratio p-value `0.0025363746`.
- A separately written base-R `dt`/`optimize` oracle returns estimate
  `0.275132230614478`, the same boundary, interval
  `[0.1181625593, 0.4575575162]`, statistic `9.1141667524`, and p-value
  `0.0025363746` within the predeclared oracle tolerance.
- Independent dense numerical integration reproduces the primary Bayesian
  `log_bf10=-0.7914751790`; BF01 is its exact reciprocal on the log scale.
- The development-only oracle now pins `bayesmeta==3.5`,
  `forestplot==3.2.0`, and `checkmate==2.3.4`. With identical proper priors and
  tightened integration/mixture settings, it reproduces primary and all four
  sensitivity BF, mu, tau, and true-effect predictive summaries within the
  predeclared `5e-6` approximation tolerance. GPL oracle code and packages
  remain outside the MIT runtime and distribution.
- Oracle regeneration and `tools/verify_oracle.py` pass with updated hashes.

## Automated and fault evidence

The focused pass-2 tests cover scale/translation and permutation invariance,
boundary and positive heterogeneity, contamination downweighting, prior
sensitivity identity, 3-study and label/work floors, 500-study resource paths,
JSON-safe schema discriminators, constructor mutations, and atomic injected
profile-root, work, optimizer-peak, quadrature, and tolerance failures. The new
analysis module reaches the required 90% branch coverage and the result module
reaches 99% on the focused suite.

## Held-out calibration finding

`m6c-pass2-calibration.json` retains the unmodified first held-out run: 2,000
cases in each of four robust cells plus 2,000 Bayesian prior-predictive cases.
Seeds, cells, and thresholds were fixed before execution. No cell was pooled,
removed, or rerun under a new threshold.

- Robust 99% Wilson intervals contain the nominal 0.95 coverage in the `k=20`,
  `k=50`, and `k=500` cells.
- The `k=10, mu=0, tau=0` cell covers `1935/2000=0.9675`; its 99% Wilson
  interval `[0.9556412, 0.9762672]` excludes 0.95 on the conservative side.
  This fails the approved symmetric calibration rule.
- Robust median absolute error is lower than M5 REML under locked 10% gross
  contamination in every cell.
- Bayesian SBC passes: `D_mu=0.0137292` and `D_tau=0.0115506`, both below the
  predeclared 99% DKW bound `0.0363948`.

The failed robust cell is reproducible and the implementation matches the
independent R profile oracle. It is therefore retained as a statistical
contract finding: asymptotic chi-squared profile inference is conservative at
the approved minimum study count on this boundary cell. The implementation
owner cannot weaken the criterion, change seeds, or add a finite-sample method.
A product/statistical-owner disposition is required before pass 2 can pass.

## Approved disposition and locked confirmation

Joshua Myers approved a narrow statistical disposition on 2026-09-15: retain
the method and visible 10–19-study warning; for that warned band, require the
99% Wilson upper bound to reach 0.95 and permit conservative overcoverage. The
two-sided interval-must-contain rule remains unchanged for `k>=20`.

Seeds `2026091514` through `2026091516` were used only for a 20-case harness
smoke and are excluded from acceptance evidence. Streams `2026091517` through
`2026091519` were then retired after the public M5 comparator encountered its
reporting-level REML root-tolerance failure before producing confirmation
statistics. The confirmation comparator now independently solves the same M5
REML score at machine precision. Before the 2,000-case confirmation, the
following untouched PCG64DXSM seeds were locked:

- clean robust coverage: `2026091520`;
- robust contamination: `2026091521`; and
- Bayesian prior-predictive SBC: `2026091522`.

Confirmation again uses 2,000 cases per cell. The first evidence artifact and
its failure status remain unchanged.

The confirmation passes every contamination and Bayesian SBC check. Its
`k=50, mu=0.3, tau=0` cell covers `1929/2000=0.9645`; the 99% Wilson interval
`[0.9522137, 0.9737146]` excludes 0.95 conservatively and therefore fails the
unchanged `k>=20` rule recorded for that run. The confirmation artifact remains
an immutable held-out finding.

## Provisional boundary disposition

Joshua Myers provisionally approved a second narrow disposition on 2026-09-15:
the one-sided conservative acceptance rule applies when `k<20` or the declared
generating heterogeneity is exactly `tau=0`. Cells with `k>=20, tau>0` retain
the two-sided interval-must-contain rule. This post-confirmation owner decision
does not change or relabel either evidence artifact, alter runtime inference, or
claim predeclared validation. M7 must explicitly reaffirm, replace, or remove
the `tau=0` extension before 1.0.

An isolated 200-case-per-cell comparison using pinned ggstatsplot 1.1.1 and
statsExpressions 2.1.1 with metaplus 1.0-8 produced conservative point coverage
from 0.960 through 0.985 in normal-null and matched fixed-Student-t4-null cells
at `k=10,50`, with zero fit failures. Every 99% Wilson interval contained 0.95.
This does not formally reproduce the M6C finding and cannot establish the same
mechanism because upstream uses a different normal-mixture model.

## Gate disposition

The pass-2 implementation and technical evidence are complete. Joshua Myers's
provisional boundary disposition closes the calibration blocker and authorizes
entry to pass 3 while retaining the finding for mandatory M7 review. This
record does not constitute independent review, M6C acceptance, or M6/`0.4`
acceptance.
