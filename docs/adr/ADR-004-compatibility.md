# ADR-004: Behavioral compatibility tiers

- Status: Accepted
- Date: 2026-09-13
- Owners: Joshua Myers, product and M0 statistical approver

## Context and forces

R and Python differ in language semantics, renderers, distribution
parameterization, random generators, model objects, and dependency coverage.
Treating all differences as bugs or silently approximating them would both be
unsafe.

## Decision

Classify each exported upstream symbol and method as `equivalent`, `adapted`,
`experimental`, or `deferred`. Numerical equivalence requires a method-level
specification, analytic/independent reference cases, and frozen R-oracle evidence.
Visual equivalence requires semantic layers and annotations, not pixels.

## Consequences

- The compatibility matrix is a release artifact.
- Pythonic argument and object-model adaptations are permitted when documented.
- Missing capability remains visible instead of receiving the nearest available
  method under an inherited label.

## Verification

`tests/test_repository_policy.py` compares the accepted M7 machine ledger with
the pinned upstream name, revision, export count, exact 22-export inventory, and
exported Python surfaces. It also rejects duplicate exports/gap identifiers and
unknown disposition values. Joshua Myers approved the product dispositions
through M7-D1 on 2026-09-15; passing the structural test guards that accepted
boundary against drift.
