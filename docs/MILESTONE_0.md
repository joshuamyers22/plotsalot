# Milestone M0: Discovery, Oracle, and Decisions

- Status: Complete
- Started: 2026-09-13
- Target duration: 2–3 weeks

## Objective

Turn the pinned R repository into an auditable behavioral specification and
prove one small Python plot-plus-result slice without creating an R runtime
dependency.

## Deliverables

| Deliverable | Evidence | Status |
|---|---|---|
| Production repository skeleton | Generated files, `uv.lock`, Git `main` branch | Complete |
| Frozen upstream identities | `docs/upstream/manifest.json` | Complete |
| Exported-symbol inventory | `docs/compatibility.md` | Complete for baseline |
| Project brief | `PROJECT_BRIEF.md` | Draft complete |
| Initial statistical plan | `STATISTICAL_ANALYSIS_PLAN.md` | Draft complete |
| Project identity decision | `docs/adr/ADR-001-project-identity.md` | Accepted with constraints |
| Renderer decision | `docs/adr/ADR-002-renderer.md` | Accepted for prototype |
| Dataframe boundary | `docs/adr/ADR-003-dataframe-boundary.md` | Accepted |
| Compatibility policy | `docs/adr/ADR-004-compatibility.md` | Accepted |
| License posture | `docs/adr/ADR-010-license-posture.md` | Accepted: MIT |
| `gghistostats` walking skeleton | implementation, tests, headless smoke | Complete |
| R-oracle fixture generator | reproducible R environment and hashed outputs | Complete |
| Benchmark baseline | retained analysis/render distributions | Complete |
| Statistical and legal owner sign-off | named approvals | Complete |

Current verification evidence is recorded in `evidence/M0_VERIFICATION.md`.

## M0 verification rubric

Blocking findings are: an unpinned upstream source; an undispositioned public
symbol; a statistic without an explicit sample and method; a result label not
traceable to a typed field; an ordinary runtime dependency on R or network
access; or a failing clean-checkout package gate.

The milestone passes when all blocking findings are closed, the walking skeleton
passes the full repository gate, oracle and benchmark artifacts are retained,
and accountable statistical and legal/product owners approve their decisions.

## Resource and stopping rules

- Limit M0 to three evidence-changing review passes per artifact.
- Re-run a pass only after code, fixtures, a tool result, or reviewer perspective
  changes.
- Escalate method ambiguity to the statistical owner instead of selecting the
  nearest-named Python implementation.
- Re-estimate the remaining roadmap after the walking skeleton and R-oracle
  generator are measured.

## Technical closeout

- `make oracle` rebuilds an R 4.5.1 image from an immutable Rocker digest and
  `renv.lock`, runs pinned `ggstatsplot@7a724cd0`, regenerates five fixture
  classes, and refreshes the checked-in SHA-256 manifest.
- `make verify-oracle` compares Python results to direct ggstatsplot fields and
  independent base-R calculations at `1e-12` relative/absolute tolerance. It
  also enforces the documented boundary and effect-size adaptations.
- `make benchmark` retains five independent analysis and render measurements
  for 10K, 100K, and 1M-row univariate workloads, including incremental peak
  Python allocations. Other workload families enter the benchmark grid with
  their implementation milestones; benchmarking placeholders would not create
  actionable baselines.
- The ordinary unit gate verifies both retained artifacts without requiring R,
  Docker, or network access.

## Approval closeout

Joshua Myers approved the M0 one-sample statistical specification and the MIT
distribution license on 2026-09-14. The decisions are recorded in
`evidence/M0_SIGNOFF.md` and ADR-010.
