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
| `m2-contract` | M2 completed its 4–5 week frequentist univariate/correlation contract covering histogram, dot, scatter, matrix, grouped, and extraction surfaces. | `docs/MILESTONE_2.md` | 2026-09-14 |
| `m2-method-approval` | Joshua Myers approved U2/G1/C1/C2/G2 in the M2 classical method specification without revision. | `docs/M2_STATISTICAL_METHODS.md`; `docs/evidence/M2_SIGNOFF.md` | 2026-09-14 |
| `m2-implementation` | M2 is complete. The approved univariate, Pearson, matrix, and atomic grouped surfaces have typed results, semantic renderers, serialized resource limits, focused tests, pinned-R oracle fixtures, retained benchmarks, production gates, and Joshua Myers's final approval. | `docs/MILESTONE_2.md`; `docs/evidence/M2_VERIFICATION.md`; `docs/evidence/M2_SIGNOFF.md` | 2026-09-14 |
| `m2-performance-baseline` | Five-sample phase-separated baselines cover scatter at 10K/100K/1M rows and 10K-row matrices at 10/25/50 variables; the input frame is outside the measurement boundary. | `benchmarks/results/m2-baseline.json`; `tools/verify_benchmark.py` | 2026-09-14 |
| `m3-contract` | M3's 5–7 week contract split M3A independent groups plus `0.1` composition/theme closure from M3B repeated measurements for `0.2`; both tracks are now complete. | `docs/MILESTONE_3.md`; `docs/PROJECT_PLAN.md` | 2026-09-14 |
| `m3-method-approval` | Joshua Myers approved B1–B3/G3 and W1–W3/G4 without revision: Welch independent tests, Holm pairwise families, explicit-subject complete-block repeated methods, and always-reported Greenhouse–Geisser correction. | `docs/M3_STATISTICAL_METHODS.md`; `docs/evidence/M3A_SIGNOFF.md`; `docs/evidence/M3B_SIGNOFF.md` | 2026-09-14 |
| `m3-implementation` | M3 is complete. The approved independent and explicit-subject repeated methods, atomic grouped variants, typed schemas, semantic renderers, local theme, result-preserving composition, pinned-R evidence, and retained benchmarks passed the production gate, independent review, and Joshua Myers's final approval. | `docs/MILESTONE_3.md`; `docs/evidence/M3A_VERIFICATION.md`; `docs/evidence/M3B_VERIFICATION.md` | 2026-09-14 |
| `m3-compatibility-adaptations` | Independent post-hoc inference is Welch-plus-Holm rather than upstream Games–Howell; repeated inference requires explicit subjects and one complete block; corrected GG inference is always primary; repeated partial omega uses the approved F conversion. | `docs/compatibility.md`; `docs/M3_STATISTICAL_METHODS.md`; `tools/verify_oracle.py` | 2026-09-14 |
| `m4-contract` | M4 was a 3–4 week categorical milestone covering raw and aggregate counts, one-way/independent/paired classical designs, a shared result for bar and pie renderers, pairwise/stratum families, grouped variants, and the final `0.2` gate. M4 and `0.2` are complete. | `docs/MILESTONE_4.md`; `docs/PROJECT_PLAN.md` | 2026-09-14 |
| `m4-method-approval` | Joshua Myers approved strict raw/count-weighted tables, asymptotic Pearson C1/C2/C4/C5 paths behind an explicit adequacy gate, exact-binomial two-category paired C3, noncentral effect intervals, separate Holm families, and atomic G5 grouping without revision. | `docs/M4_STATISTICAL_METHODS.md`; `docs/evidence/M4_SIGNOFF.md` | 2026-09-14 |
| `m4-implementation` | M4 is complete. Its categorical tables, shared inference, bar/pie renderers, grouped variants, schemas, tests, pinned-R fixtures, and benchmarks passed production verification, independent review, and Joshua Myers's final approval, closing `0.2`. | `docs/MILESTONE_4.md`; `docs/evidence/M4_VERIFICATION.md`; `docs/evidence/M4_SIGNOFF.md` | 2026-09-14 |
| `m5-contract` | M5 is a 4–6 week, two-track milestone for strict Polars coefficient tables, a narrow fitted-Statsmodels adapter, semantic `ggcoefstats` rendering, and one approved frequentist random-effects meta-analysis. K1–K4/MA1–MA4 approval is required before inferential implementation; accepted M5 closes `0.3`. | `docs/MILESTONE_5.md`; `docs/PROJECT_PLAN.md` | 2026-09-14 |

## Verified traps and failed approaches

| Key | Symptom and cause | Evidence or reproducer | Last verified |
|---|---|---|---|
| `license-mismatch` | The original proprietary placeholder conflicted with the approved distribution posture; ADR-010 replaced it with MIT. | `LICENSE`; `docs/adr/ADR-010-license-posture.md` | 2026-09-14 |
