# Milestone M1: Shared Contracts and Production Foundation

- Status: Complete
- Started: 2026-09-14
- Target duration: 2–3 weeks

## Objective

Turn the M0 walking skeleton into small, reusable contracts that later plot
families can share without coupling statistical analysis to Matplotlib or
duplicating dataframe validation.

## Entry gate

M1 does not waive M0. Its entry gate was satisfied by the statistical and
license approvals recorded on 2026-09-14 in M0's sign-off and ADR-010.

## Deliverables and acceptance evidence

| Deliverable | Acceptance evidence | Status |
|---|---|---|
| Versioned structured-result contract | Immutable records, deterministic JSON-safe mapping, schema-alignment tests | Complete |
| Shared numeric data boundary | Polars-only validation, owned read-only float64 data, sample reconciliation, edge-case tests | Complete |
| Analysis/render separation | Statistical computation runs without creating a figure; rendering consumes the analyzed slice | Complete |
| Validated plot container | Named axes are immutable as a mapping, belong to the figure, and annotations remain extractable | Complete |
| Public contract documentation | README examples and API exports describe analysis, rendering, and composition | Complete |
| Production repository gate | `make check`, dependency/license audit, build, and isolated wheel smoke pass | Complete |
| Milestone review | Bounded verification record and adversarial architecture review have no open blocking finding | Complete |

## Invariants

- The plotted values and analyzed values are the same owned numeric sample.
- Caller data is never mutated.
- Statistical computation has no figure creation or global plotting side effect.
- Every displayed statistic is formatted from a typed result field.
- Result payloads are versioned and contain no SciPy, Polars, NumPy, or
  Matplotlib objects.
- The public tabular boundary accepts Polars dataframes only.

## Non-goals

- Adding a second statistical plot family.
- General dataframe interchange or pandas support.
- Stabilizing every future result field before its method specification exists.
- Selecting a distribution license or approving statistical methods on behalf
  of accountable reviewers.
- Pixel-level compatibility with upstream R renderers.

## Verification rubric and stopping rules

- Blocking: sample mismatch, mutable shared numeric data, result/schema drift,
  analysis importing rendering concerns, unvalidated foreign axes, a failing
  quality/build/audit gate, or an unapproved upstream dependency.
- Maximum three evidence-changing verification passes.
- A later pass must add a focused test, full gate, isolated artifact smoke, or
  meaningfully different architecture/security review.
- Stop and escalate rather than infer a statistical or legal approval.

## Exit gate

M1 passes when every technical deliverable above has retained evidence, the M0
entry gate is closed, and no blocking review finding remains. All conditions
were satisfied on 2026-09-14.

Technical evidence is recorded in `evidence/M1_VERIFICATION.md`; entry-gate
approvals are recorded in `evidence/M0_SIGNOFF.md` and ADR-010.
