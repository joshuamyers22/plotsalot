# ADR-003: Polars-first dataframe boundary

- Status: Accepted
- Date: 2026-09-13
- Owners: Technical lead

## Context and forces

The production template selects Polars for quantitative data boundaries and
requires pandas exceptions to be explicit. Statistical libraries primarily
consume NumPy arrays.

## Decision

Accept Polars dataframes as the canonical public tabular input. Convert selected,
validated columns to owned NumPy arrays at a named boundary. Add pandas support
only through a separate optional adapter and ADR if user demand requires it.

## Consequences

- Category order, null behavior, dtype, row identity, and allocation must be
  explicit at conversion.
- Statsmodels and SciPy objects cannot leak into tabular domain contracts.
- Initial compatibility is narrower than accepting every dataframe-like object.

## Verification

Architecture tests reject pandas imports in the core. Boundary tests cover null,
non-finite, categorical, wrong-type, and missing-column inputs.
