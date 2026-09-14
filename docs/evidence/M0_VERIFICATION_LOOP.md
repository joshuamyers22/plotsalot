# Agentic Verification Loop: M0 closeout

## Rubric

Blocking checks were exact upstream identity, a lockfile-driven R oracle,
representative hashed fixtures, explicit method/sample semantics, separate
analysis/render baselines with peak allocation, clean package gates, and no
license-boundary violation. Statistical and legal approvals require accountable
human reviewers.

## Iterations

| Pass | New evidence | Finding | Correction | Result |
|---:|---|---|---|---|
| 1 | Initial oracle image build | Rocker binary snapshot was too old; install warning did not fail the image | Treat warnings as errors, use source resolution, add missing native toolchain | Pinned ggstatsplot installed |
| 2 | Direct ggstatsplot extraction and first fixture run | Upstream effect size and invalid-input behavior differ from prototype | Classify adaptations; retain raw/normalized outputs and exact semantic verifier | Five fixture classes pass |
| 3 | Clean renv rebuild, benchmark, full gate, adversarial review | Evidence needed ordinary-gate integrity checks; owner sign-offs remain external | Add SHA-256 manifest, artifact unit tests, five-sample workload grid, sign-off record | No open technical blocker |

## Exit

- Technical stop reason: all executable M0 rubric items pass and an unchanged
  pass would add no new evidence.
- Governance closeout: Joshua Myers supplied the statistical and product/legal
  approvals on 2026-09-14; `M0_SIGNOFF.md` and ADR-010 record the decisions.
- Rollback: any oracle hash/parity drift, stale lock, benchmark schema failure,
  package gate failure, or unapproved upstream implementation reopens M0.
