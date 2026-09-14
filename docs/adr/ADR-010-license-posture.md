# ADR-010: Combined upstream license posture

- Status: Proposed; blocks `qqplotr` source implementation
- Date: 2026-09-13
- Owners: Product and release/legal owners unassigned

## Context and forces

`ggstatsplot` is MIT licensed. `qqplotr` declares GPL-3. A direct translation or
other derivative use of GPL-covered implementation code can create distribution
obligations for the combined work. The generated repository currently uses the
production template's proprietary license. Public repository visibility does not
itself grant reuse rights or resolve the combined-work licensing question.

## Options considered

1. License the combined derivative under GPL-3-compatible terms and comply with
   all corresponding-source and notice obligations.
2. Implement Q–Q/P–P behavior independently from public APIs and published
   statistical methods, with separated provenance and qualified review.
3. Keep `qqplotr` capability in a separately distributed GPL component.
4. Defer `qqplotr` capability.

## Proposed decision

Do not copy or translate `qqplotr` or `qqconf` source while this ADR is proposed.
Continue only with API inventory, published-method research, independent test
design, and `ggstatsplot`-side work. Obtain qualified legal review before
selecting an option or publishing a package containing `qqplotr`-derived work.

## Consequences

- Q–Q/P–P implementation is temporarily blocked.
- Repository license metadata remains proprietary and must not be treated as the
  final combined-work release decision.
- Provenance records must distinguish behavioral specifications, published
  methods, independently written code, and any copied material.

## Verification

No source module, test fixture, or documentation excerpt derived from GPL source
may be added before this ADR becomes accepted. Release readiness remains blocked
until the repository license and notices match the approved option.
