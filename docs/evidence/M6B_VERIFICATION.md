# M6B Technical Verification

- Candidate date: 2026-09-15
- Approved authority: B1–B6 in `../M6B_STATISTICAL_METHODS.md`
- Outcome: implementation-owner technical gate passed
- Independent review: Joshua Myers, accepted 2026-09-15

## Implemented surface

- exact normal-inverse-gamma one-sample and label-level dot summaries;
- exact sample-correlation posterior/BF quadrature and complete matrices;
- homoscedastic cell-means independent comparisons;
- complete-block Helmert/compound-symmetry repeated comparisons;
- fixed-total and fixed-row Dirichlet-multinomial categorical analyses;
- all pre-existing grouped wrappers, semantic rendering, extraction, and schema;
- explicit proper priors, numeric BF10 orientation/sensitivity, credible
  intervals, computation diagnostics, stable seeds, and bounded work.

Paired Bayesian categorical analysis and Bayesian coefficient/meta-analysis are
deliberately deferred by B4/B5.

## Verification gates

| Gate | Result |
|---|---|
| Formatting, lint, and strict typing | Passed |
| Full unit/integration suite | 223 tests passed |
| Coverage | 91% total; `bayesian.py` 92%; `bayesian_result.py` 90% |
| Exact/symmetry/replay/fault tests | Passed |
| Retained M6B benchmark/work grid | Passed verifier |
| Dependency/license audit | Passed |
| Source/wheel build and isolated import smoke | Passed |

## Acceptance

Joshua Myers independently reviewed the approved equations, numerical evidence,
repeated constrained-model Bayes factors, and adversarial dispositions. He
accepted the candidate and provided accountable M6B release acceptance on
2026-09-15. M6B is complete; R4/M6C and final M6/`0.4` remain open.
