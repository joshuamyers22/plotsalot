# plotsalot Project Memory

This is a bounded retrieval index for durable project knowledge. It is not an
activity log, task tracker, transcript, or source of truth. Verify every entry
against the linked implementation, test, issue, or decision record before acting.

Do not record secrets, personal data, client data, hidden reasoning, or other
restricted material. Update stable keys in place and remove stale entries.

## Durable constraints

| Key | Constraint | Evidence | Last verified |
|---|---|---|---|
| `no-r-runtime` | R is permitted only in development oracle generation; released Python artifacts must not require R or network access. | `PROJECT_BRIEF.md`; `docs/PROJECT_PLAN.md` | 2026-09-13 |
| `polars-boundary` | Polars is the canonical tabular API and selected data crosses an explicit owned NumPy boundary. | `docs/adr/ADR-003-dataframe-boundary.md`; `tests/test_gghistostats.py` | 2026-09-13 |
| `qqplotr-license-gate` | No `qqplotr` or `qqconf` source may be copied or translated while ADR-010 is proposed. | `docs/adr/ADR-010-license-posture.md`; `docs/upstream/README.md` | 2026-09-13 |

## Accepted decisions

| Key | Decision and rationale | Evidence | Last verified |
|---|---|---|---|
| `project-identity` | The development repository, distribution, and import name is `plotsalot`; it must not imply upstream endorsement. | `docs/adr/ADR-001-project-identity.md` | 2026-09-13 |
| `initial-renderer` | Matplotlib is the owned M0/0.1 renderer; statistical results remain renderer-independent. | `docs/adr/ADR-002-renderer.md` | 2026-09-13 |
| `compatibility-tiers` | Every upstream export and method is labeled equivalent, adapted, experimental, or deferred. | `docs/adr/ADR-004-compatibility.md`; `docs/compatibility.md` | 2026-09-13 |

## Non-obvious current state

| Key | State worth retrieving later | Evidence | Last verified |
|---|---|---|---|
| `m0-active` | M0 is in progress. The repository and parametric `gghistostats` walking skeleton pass; R-oracle, benchmarks, reviews, and the license decision remain open. | `docs/MILESTONE_0.md`; `docs/evidence/M0_VERIFICATION.md` | 2026-09-13 |
| `upstream-baselines` | Behavioral discovery is pinned to `ggstatsplot@7a724cd` and `qqplotr@eeaa2e2`; key API-file hashes are retained. | `docs/upstream/manifest.json` | 2026-09-13 |

## Verified traps and failed approaches

| Key | Symptom and cause | Evidence or reproducer | Last verified |
|---|---|---|---|
| `license-mismatch` | The template's proprietary placeholder and the MIT/GPL-3 upstream combination cannot be treated as a publishable license decision. | `LICENSE`; `docs/adr/ADR-010-license-posture.md` | 2026-09-13 |

## Open threads

| Key | Unresolved question or next evidence | Owner | Review by |
|---|---|---|---|
| `license-decision` | Obtain qualified review and accept ADR-010 before Q–Q/P–P implementation or publication. | UNASSIGNED | End of M0 |
| `oracle-and-benchmarks` | Build the locked R oracle and retain performance/peak-memory baselines. | UNASSIGNED | End of M0 |
| `statistical-approval` | Assign an independent statistical-methods reviewer and approve the M0 spec. | UNASSIGNED | End of M0 |
