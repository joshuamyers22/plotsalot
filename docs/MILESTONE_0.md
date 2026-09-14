# Milestone M0: Discovery, Oracle, and Decisions

- Status: In progress
- Started: 2026-09-13
- Target duration: 2–3 weeks

## Objective

Turn the two R repositories into an auditable behavioral specification and
prove one small Python plot-plus-result slice without creating an R runtime
dependency or crossing the unresolved `qqplotr` GPL-3 boundary.

## Deliverables

| Deliverable | Evidence | Status |
|---|---|---|
| Production repository skeleton | Generated files, `uv.lock`, Git `main` branch | Complete |
| Frozen upstream identities | `docs/upstream/manifest.json` | Complete |
| Combined exported-symbol inventory | `docs/compatibility.md` | Complete for baseline |
| Project brief | `PROJECT_BRIEF.md` | Draft complete |
| Initial statistical plan | `STATISTICAL_ANALYSIS_PLAN.md` | Draft complete |
| Project identity decision | `docs/adr/ADR-001-project-identity.md` | Accepted with constraints |
| Renderer decision | `docs/adr/ADR-002-renderer.md` | Accepted for prototype |
| Dataframe boundary | `docs/adr/ADR-003-dataframe-boundary.md` | Accepted |
| Compatibility policy | `docs/adr/ADR-004-compatibility.md` | Accepted |
| License posture | `docs/adr/ADR-010-license-posture.md` | Proposed; blocking `qqplotr` code |
| `gghistostats` walking skeleton | implementation, tests, headless smoke | Complete |
| R-oracle fixture generator | reproducible R environment and hashed outputs | Not started |
| Benchmark baseline | retained analysis/render distributions | Not started |
| Statistical and legal owner sign-off | named approvals | Blocked on assignments |

Current verification evidence is recorded in `evidence/M0_VERIFICATION.md`.

## M0 verification rubric

Blocking findings are: an unpinned upstream source; an undispositioned public
symbol; copied/translated GPL source without an approved posture; a statistic
without an explicit sample and method; a result label not traceable to a typed
field; an ordinary runtime dependency on R or network access; or a failing
clean-checkout package gate.

The milestone passes when all blocking findings are closed, the walking skeleton
passes the full repository gate, oracle and benchmark artifacts are retained,
and accountable statistical and legal/product owners approve their decisions.

## Resource and stopping rules

- Limit M0 to three evidence-changing review passes per artifact.
- Re-run a pass only after code, fixtures, a tool result, or reviewer perspective
  changes.
- Stop implementation of `qqplotr` behavior at the public specification boundary
  until ADR-010 is approved.
- Escalate method ambiguity to the statistical owner instead of selecting the
  nearest-named Python implementation.
- Re-estimate the remaining roadmap after the walking skeleton, Q–Q feasibility
  spike, and R-oracle generator are measured.

## Next tasks

1. Finish and verify the `gghistostats` walking skeleton.
2. Create a containerized R oracle generator for the pinned `ggstatsplot` commit.
3. Add representative normal, null-containing, non-finite, degenerate, and
   small-sample fixtures.
4. Measure analysis and rendering separately for the declared benchmark sizes.
5. Assign statistical, visualization, product, and license reviewers.
