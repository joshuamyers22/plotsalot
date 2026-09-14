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

CI will eventually compare the upstream inventories with the compatibility
matrix and fail when an export or supported method lacks a disposition.
