# ADR-007: Public API and Schema Stability for 1.x

- Status: Accepted
- Date: 2026-09-15
- Owner: Joshua Myers
- Decision gate: M7-D3

## Context and forces

Plotsalot `0.1.1` exposes a broad typed Python surface, multiple serialized
result variants, console scripts, semantic Matplotlib containers, and statistical
contracts developed across M0–M6. Pre-1.0 implementation evidence does not by
itself define what downstream users may rely on throughout 1.x.

Python signature compatibility is insufficient for a statistical library. A
change can preserve a function name while changing its retained population,
estimand, interval, prior, correction, randomness, result units, warning, or
refusal behavior. Conversely, pixel-level rendering changes need not be breaking
when semantic axes, layers, annotations, and result identity remain stable.

## Decision

Adopt [`../API_STABILITY.md`](../API_STABILITY.md) as the normative 1.x policy,
subject to the exact public manifest, schema fixtures, error inventory, and
`0.1.1` migration review required by M7.

The policy treats documented exports, signatures, result meanings, serialized
variants, semantic plot contracts, and stable error types/codes as public. It
uses semantic versioning, immutable published schema versions, explicit
migrations, and a normal deprecation window of at least one minor release and
90 days. Statistical meaning is part of compatibility. Pixel output, exact
message prose, undocumented internals, and arbitrary artist mutation are not.

Joshua Myers approved M7-D3 without revision on 2026-09-15. This decision adopts
the policy for M7 hardening; it does not freeze the current pre-1.0 surface or
authorize a 1.0 release before the required inventories and evidence pass.

## Consequences

- M7 must generate and review a public-name/signature/CLI manifest.
- Every emitted serialized variant needs a retained golden fixture and matching
  immutable schema version.
- Message-only failure contracts must gain a stable type/code or be explicitly
  excluded from the stability promise.
- Breaking scientific corrections require an accountable exception record and
  affected-version guidance even when immediate correction is safer than
  compatibility.
- New additive statistical methods still require method approval and evidence;
  a minor-version label is not statistical authorization.

## Alternatives considered

- **Freeze only Python call signatures:** rejected because it ignores statistical
  meaning, results, schemas, warnings, limits, and plot semantics.
- **Treat every current implementation detail as stable:** rejected because it
  would freeze undocumented internals and pixel output without user value.
- **Delay all compatibility promises beyond 1.0:** rejected because it would make
  the 1.0 designation misleading for downstream users.

## Approval and verification

M7-D3 owner approval is recorded above. The implementation evidence listed in
`API_STABILITY.md`, implementation completion, and final 1.0 release acceptance
remain separate gates.
