# ADR-002: Matplotlib-native initial renderer

- Status: Accepted for M0 and 0.1; review before 1.0
- Date: 2026-09-13
- Owners: Technical lead; visualization owner unassigned

## Context and forces

The package needs owned figure/axes lifecycle, headless rendering, plot
composition, semantic artist tests, and post-construction customization. Exact
`ggplot2` grammar compatibility is a non-goal.

## Decision

Use Matplotlib as the initial rendering boundary. Build renderer-neutral plot
and band specifications where doing so creates a meaningful statistical or
testing boundary. Do not expose Seaborn or Plotnine objects as domain contracts.

## Consequences

- Users receive familiar Matplotlib figures and axes.
- Visual parity is semantic rather than pixel-identical with R.
- Higher-level plotting libraries may be used internally only after an adapter
  proves stable artist ownership and data semantics.

## Verification

The M0 histogram must render headlessly, permit caller modification, preserve
its structured result, and pass semantic artist assertions.
