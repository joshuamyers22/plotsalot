# ADR-010: Distribution license and upstream posture

- Status: Accepted
- Date: 2026-09-14
- Owner and product/legal approver: Joshua Myers
- Decision: License plotsalot under MIT and limit upstream compatibility scope to
  ggstatsplot

## Context and forces

Plotsalot needs a clear distribution license and provenance policy. Its retained
behavioral baseline, ggstatsplot, is MIT licensed. The project must preserve
applicable notices, remain independently branded, and avoid implying upstream
endorsement.

## Decision

Plotsalot is an independent MIT-licensed implementation. The compatibility
program targets ggstatsplot's public statistical-visualization workflows. Any
new upstream target requires an explicit scope decision, license review, pinned
identity, compatibility inventory, and statistical-method review before code or
fixtures are added.

## Consequences

- Repository and distribution metadata use the MIT license.
- Applicable upstream notices and method citations are preserved.
- Upstream repositories are behavioral references and are not vendored.
- The released package has no R or network runtime dependency.
- The project remains independent and must not imply upstream endorsement.

## Verification

- `LICENSE` contains the MIT license and package metadata declares `MIT`.
- Dependency license policy remains enforced by `make audit`.
- `docs/upstream/manifest.json` lists only approved upstream targets.
- The compatibility matrix contains only exports within approved product scope.

## Approval

Joshua Myers approved the MIT distribution license and removal of the former
secondary upstream target on 2026-09-14 through explicit project-owner
direction.
