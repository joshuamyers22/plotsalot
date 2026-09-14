# ADR-001: Project identity

- Status: Accepted
- Date: 2026-09-13
- Owners: User/product owner

## Context and forces

The project needs a Python package and repository name. It derives product ideas
from an upstream R package but has no recorded upstream endorsement.

## Decision

Use `plotsalot` as the repository, distribution, and import name during
development. Describe it as an independent planned Python implementation. Do
not use upstream logos or “official port” language without written approval.

## Consequences

- The name is distinct from the upstream package.
- API compatibility is documented function by function rather than implied by
  the distribution name.
- Publication must retain independent-project language; the distribution
  license was resolved as MIT by ADR-010.

## Verification

README, package metadata, documentation, and release checks must consistently
use `plotsalot` and must not claim endorsement.
