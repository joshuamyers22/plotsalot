# M3A Adversarial Review

- Date prepared: 2026-09-14
- Review target: M3A release candidate
- Preparation: implementation self-review
- Independent reviewer: Joshua Myers
- Status: Approved

## Findings found and corrected or dispositioned

| ID | Finding | Severity | Disposition | Acceptance evidence |
|---|---|---|---|---|
| M3A-AR-001 | Upstream pairwise output uses Games–Howell while the approved method uses Welch contrasts | Blocking | Retain Welch-plus-Holm, label the surface adapted, preserve the raw upstream object, and compare independently normalized values | `docs/compatibility.md`; `tools/verify_oracle.py`; between oracle and analytic tests |
| M3A-AR-002 | A composition rasterizer could leave a source figure attached to a replacement canvas | Blocking | Restore the exact original canvas in a `finally` block and test canvas identity | composition identity/canvas test |
| M3A-AR-003 | The first composition surface omitted contract-required shared labels and panel tags | Required | Add validated `x_label`, `y_label`, and deterministic `panel_tags`; retain them in schema-v1 output | composition public, error, and schema tests |
| M3A-AR-004 | `StatsTheme.accent_color` was validated but the mean layer used a literal color | Required | Route the selected theme accent into the semantic mean-interval layer | custom accent and global-style-isolation test |
| M3A-AR-005 | Composition could retain more panels than its own recorded ceiling in a manually constructed result | Required | Validate panel count against `maximum_panels` in the frozen result | composition contract tests |

## Independent review checklist

The reviewer should verify Welch formula/orientation, full Holm-family retention,
sample reconciliation, deterministic level order, result-only annotation
rendering, grouped atomicity and correction scope, raster composition semantics,
theme isolation, resource ceilings, compatibility wording, oracle adaptation,
and package isolation.

## Independent reviewer decision

Joshua Myers reviewed the M3A release candidate, accepted every finding
disposition above, and approved M3A on 2026-09-14. No additional findings were
recorded.
