# M3A Verification Loop

## Objective and authority

- Requirement: `docs/MILESTONE_3.md`
- Scope: independent comparisons, grouped execution, composition, and theme
- Risk class: high-risk statistical reporting
- Product/statistical owner: Joshua Myers
- Implementation owner: Codex
- Independent reviewer: Joshua Myers
- Starting revision: `cc0470d`

## Iterations

| # | Implemented slice | New evidence/context | Finding and disposition | Gate state |
|---:|---|---|---|---|
| 0 | Method-entry audit | Pinned ggstatsplot/statsExpressions behavior and independent formulas | B1–B3/G3 required accountable approval; Joshua Myers approved them without revision on 2026-09-14 | Entry gate complete |
| 1 | Owned sample, typed results, Welch analysis, semantic renderer, and atomic grouped surface | Analytic cases, independent Welch/Holm calculation, row permutation, level identity, failure, injection, and schema tests | Upstream uses Games–Howell post-hoc tests; retained the approved Welch-plus-Holm method as an explicit adaptation | Focused gates pass |
| 2 | Pinned-R oracle and retained row/level/pairwise/composition benchmark | Raw upstream objects, base-R normalized results, five-sample phase distributions through 1M rows, 20 levels, 190 contrasts, and 20 panels | Composition snapshots initially risked replacing source canvases; restoration and identity tests close the finding | Oracle and benchmark gates pass |
| 3 | Contract, production, and accountable closeout | Shared labels, deterministic panel tags, local theme accent, full check/audit/build, isolated-wheel smoke, and Joshua Myers's independent review | Required shared labels/tags and applied accent styling were missing; implemented, serialized, tested, and accepted with every other finding disposition | All technical and accountable M3A gates pass |

## Exit state

- Status: Complete
- Technical and accountable closeout: 2026-09-14
- Remaining uncertainty: no known technical blocker inside the approved M3A
  scope
