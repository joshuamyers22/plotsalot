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

## Accepted decisions

| Key | Decision and rationale | Evidence | Last verified |
|---|---|---|---|
| `project-identity` | The development repository, distribution, and import name is `plotsalot`; it must not imply upstream endorsement. | `docs/adr/ADR-001-project-identity.md` | 2026-09-13 |
| `initial-renderer` | Matplotlib is the owned M0/0.1 renderer; statistical results remain renderer-independent. | `docs/adr/ADR-002-renderer.md` | 2026-09-13 |
| `compatibility-tiers` | Every upstream export and method is labeled equivalent, adapted, experimental, or deferred. | `docs/adr/ADR-004-compatibility.md`; `docs/compatibility.md` | 2026-09-13 |
| `mit-license` | Joshua Myers selected the MIT distribution license and limited the upstream compatibility scope to ggstatsplot. | `LICENSE`; `pyproject.toml`; `docs/adr/ADR-010-license-posture.md` | 2026-09-14 |
| `m0-statistical-approval` | Joshua Myers approved the M0 one-sample specification and documented ggstatsplot adaptations. Future method families require separate approval. | `STATISTICAL_ANALYSIS_PLAN.md`; `docs/evidence/M0_SIGNOFF.md` | 2026-09-14 |

## Non-obvious current state

| Key | State worth retrieving later | Evidence | Last verified |
|---|---|---|---|
| `m0-m1-gates` | M0 and M1 are complete: technical evidence passes and Joshua Myers supplied the statistical, MIT-license, and upstream-scope approvals. | `docs/MILESTONE_0.md`; `docs/MILESTONE_1.md`; `docs/evidence/M0_SIGNOFF.md` | 2026-09-14 |
| `upstream-baseline` | Behavioral discovery is pinned to `ggstatsplot@7a724cd`; key API-file hashes are retained. | `docs/upstream/manifest.json` | 2026-09-14 |
| `shared-contracts` | Result/data/analysis modules are independent of Matplotlib; a retained histogram analysis owns an immutable numeric sample and feeds a validated, caller-customizable plot container. | `docs/CONTRACTS.md`; `tests/test_contracts.py`; `tests/test_data_boundary.py` | 2026-09-14 |
| `m0-oracle-adaptations` | The pinned ggstatsplot oracle accepts non-finite/degenerate fixtures and reports Hedges' g; plotsalot deliberately rejects those samples and reports Cohen's d. Shared t-test fields match at 1e-12 tolerance. | `oracle/fixtures/manifest.json`; `tools/verify_oracle.py`; `STATISTICAL_ANALYSIS_PLAN.md` | 2026-09-14 |
| `m0-performance-baseline` | Five-sample analysis/render timing and incremental Python allocation peaks are retained for 10K, 100K, and 1M rows on the M0 arm64 host. | `benchmarks/results/m0-baseline.json`; `tools/verify_benchmark.py` | 2026-09-14 |
| `m2-contract` | M2 is in progress as a 4–5 week frequentist univariate/correlation milestone covering histogram, dot, scatter, matrix, grouped, and extraction surfaces. | `docs/MILESTONE_2.md` | 2026-09-14 |
| `m2-method-approval` | Joshua Myers approved U2/G1/C1/C2/G2 in the M2 classical method specification without revision. | `docs/M2_STATISTICAL_METHODS.md`; `docs/evidence/M2_SIGNOFF.md` | 2026-09-14 |
| `m2-implementation` | M2 is complete. The approved univariate, Pearson, matrix, and atomic grouped surfaces have typed results, semantic renderers, serialized resource limits, focused tests, pinned-R oracle fixtures, retained benchmarks, production gates, and Joshua Myers's final approval. | `docs/MILESTONE_2.md`; `docs/evidence/M2_VERIFICATION.md`; `docs/evidence/M2_SIGNOFF.md` | 2026-09-14 |
| `m2-performance-baseline` | Five-sample phase-separated baselines cover scatter at 10K/100K/1M rows and 10K-row matrices at 10/25/50 variables; the input frame is outside the measurement boundary. | `benchmarks/results/m2-baseline.json`; `tools/verify_benchmark.py` | 2026-09-14 |

## Verified traps and failed approaches

| Key | Symptom and cause | Evidence or reproducer | Last verified |
|---|---|---|---|
| `license-mismatch` | The original proprietary placeholder conflicted with the approved distribution posture; ADR-010 replaced it with MIT. | `LICENSE`; `docs/adr/ADR-010-license-posture.md` | 2026-09-14 |
