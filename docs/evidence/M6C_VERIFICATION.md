# M6C Technical Verification

- Candidate date: 2026-09-15
- Starting revision for pass 3: `909cad9`
- Approved authority: `../M6C_STATISTICAL_METHODS.md`
- Outcome: three-pass implementation-owner technical gate passed
- Independent review: Joshua Myers, accepted 2026-09-15

## Implemented pass-3 surface

- semantic rendering for caller-reported robust confidence summaries and
  posterior equal-tail credible summaries;
- semantic fixed-Student-t4 robust and proper-prior Bayesian normal-normal
  aggregate forest rendering;
- distinct study, pooled profile-confidence, pooled posterior-credible, and
  posterior-predictive artist roles;
- exact typed-result extraction and four-mode heterogeneous composition;
- bounded printable display identities, explicit runtime analysis validation,
  and presentation-only interval/prediction/label controls;
- retained coefficient/meta analysis, render, memory, and deterministic-work
  baselines; and
- public method, compatibility, contract, plan, and acceptance documentation.

## Verification gates

| Gate | Result |
|---|---|
| Formatting, lint, and strict typing | Passed |
| Full unit/integration suite | 267 tests passed |
| Coverage | 92% total; M6C renderer 97%; analysis/result modules 90–99% |
| Semantic injection, artist identity, extraction, composition, and adversarial tests | Passed |
| Dependency vulnerability and MIT-compatible license audit | Passed; no known vulnerabilities or adverse project statuses |
| Source distribution and wheel build | Passed |
| Offline isolated-wheel robust/Bayesian render smoke | Passed with locally cached locked runtime dependencies |
| Frozen oracle/hash verifier | Passed |
| Retained benchmark/work verifier | Passed |
| Visual inspection | Passed after reserving title/caption space and wrapping long semantic annotations |

## Retained performance evidence

`benchmarks/results/m6c-baseline.json` retains five separately measured samples
per phase. Median analysis/render times on the recording host were:

| Workload | Analysis | Render |
|---|---:|---:|
| Robust reported coefficients, 10/100/500 terms | 1.05/3.33/14.19 ms | 47.80/382.34/1,965.35 ms |
| Posterior reported coefficients, 10/100/500 terms | 1.46/4.59/19.54 ms | 48.65/385.69/1,936.44 ms |
| Robust meta-analysis, 10/100/500 studies | 48.05/59.44/84.93 ms | 52.39/381.69/1,903.97 ms |
| Bayesian meta-analysis, 3/10/100/500 studies | 5,451.12/4,482.08/6,523.63/9,055.48 ms | 28.50/54.37/382.90/1,931.79 ms |

Robust meta actual work was 452–581 of 20,000,000 reserved units. Bayesian
actual work was 67,828–123,634 of 25,000,000 reserved units. The sequential M5A
regression comparison's worst median increase was 4.6%. The historical M5B
comparison showed 16–24% slower analysis in several cells (roughly 2–116 ms)
despite no change to its estimator. A same-host, same-interpreter comparison
against an archive of starting revision `909cad9` then bounded the worst median
change at 16.0% (a 0.064 ms selection difference); every analysis/render cell
was within 3.2%. This isolates the larger historical comparison as host/baseline
drift, while retaining it as reviewer context rather than overwriting the
accepted M5B baseline.

## Acceptance state

All three authorized implementation passes are used. Joshua Myers independently
reviewed and accepted the M6C candidate on 2026-09-15. The separate combined
M6/`0.4` decision remains open. The provisional one-sided conservative rule
when `k<20` or generating `tau=0` remains mandatory M7 debt and is not converted
into permanent acceptance by the M6C decision.
