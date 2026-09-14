# ADR-001: Project identity

- Status: Accepted
- Date: 2026-09-13
- Owners: User/product owner

## Context and forces

The project needs a Python package and repository name. It derives product ideas
from two upstream R packages but has no recorded upstream endorsement.

## Decision

Use `plotsalot` as the repository, distribution, and import name during
development. Describe it as an independent planned Python implementation. Do
not use upstream logos or “official port” language without written approval.

## Consequences

- The name is distinct from both upstream packages.
- API compatibility is documented function by function rather than implied by
  the distribution name.
- Publication remains gated on a naming/trademark and license review.

## Verification

README, package metadata, documentation, and release checks must consistently
use `plotsalot` and must not claim endorsement.
