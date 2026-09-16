# plotsalot Project Memory

This is a bounded retrieval index for durable project knowledge. It is not an
activity log, task tracker, transcript, or source of truth. Verify every entry
against the linked implementation, test, issue, or decision record before acting.

Do not record secrets, personal data, client data, hidden reasoning, or other
restricted material. Update stable keys in place and remove stale entries.

## Durable constraints

| Key | Constraint | Evidence | Last verified |
|---|---|---|---|
| `no-r-runtime` | R is permitted only for development oracle generation; released Python artifacts must install and run without R, Docker, or network access. | `PROJECT_BRIEF.md`; `docs/PROJECT_PLAN.md`; `docs/evidence/M6_RELEASE_VERIFICATION.md` | 2026-09-15 |
| `polars-boundary` | Polars is the canonical tabular API; selected numeric data crosses an explicit owned NumPy boundary with no implicit pandas alignment. | `docs/adr/ADR-003-dataframe-boundary.md`; `tests/test_data_boundary.py` | 2026-09-15 |
| `atomic-failure` | Unsupported methods, invalid samples, and grouped-member failures raise without estimator fallback or partial grouped output. | `docs/CONTRACTS.md`; `docs/compatibility.md`; `tests/test_grouped.py` | 2026-09-15 |
| `bounded-stochastic-work` | Stochastic and numerical methods own or derive deterministic streams, record provenance, and reject requests beyond their declared work limits before expensive computation. | `docs/M6_STATISTICAL_METHODS.md`; `docs/M6B_STATISTICAL_METHODS.md`; `docs/M6C_STATISTICAL_METHODS.md` | 2026-09-15 |

## Accepted decisions

| Key | Decision and rationale | Evidence | Last verified |
|---|---|---|---|
| `project-identity` | The repository, distribution, and import name is `plotsalot`; it is an independent project and must not imply upstream endorsement. | `docs/adr/ADR-001-project-identity.md`; `README.md` | 2026-09-15 |
| `renderer` | Matplotlib is the owned renderer; typed statistical results remain renderer-independent and composition retains result identity. | `docs/adr/ADR-002-renderer.md`; `docs/CONTRACTS.md`; `tests/test_contracts.py` | 2026-09-15 |
| `compatibility-tiers` | Public upstream behavior is explicitly classified and Python adaptations are preferred over hidden compatibility shims or ignored parameters. | `docs/adr/ADR-004-compatibility.md`; `docs/compatibility.md` | 2026-09-15 |
| `robust-bayesian-architecture` | Robust and Bayesian modes use project-owned, approved, bounded NumPy/SciPy implementations with explicit provenance and no fallback. | `docs/adr/ADR-005-robust-method-architecture.md`; `docs/adr/ADR-006-bayesian-engine-architecture.md` | 2026-09-15 |
| `mit-license` | Joshua Myers selected the MIT distribution license and limited upstream compatibility scope to `ggstatsplot`. | `LICENSE`; `pyproject.toml`; `docs/adr/ADR-010-license-posture.md` | 2026-09-15 |
| `first-pypi-version` | The first PyPI release is `0.1.1`; it follows the existing, materially different `v0.1.0` GitHub release rather than adopting the internal `0.4` product-gate label. Its wheel and sdist were published through the protected trusted-publishing workflow. | `pyproject.toml`; `CHANGELOG.md`; `docs/PROJECT_PLAN.md`; GitHub release `v0.1.1` | 2026-09-15 |
| `security-response` | The latest published minor line receives security fixes. The repository owner targets acknowledgement within three business days and initial assessment within seven business days; these targets are not a service-level guarantee. | `SECURITY.md` | 2026-09-15 |

## Non-obvious current state

| Key | State worth retrieving later | Evidence | Last verified |
|---|---|---|---|
| `upstream-baseline` | Behavioral discovery is pinned to `ggstatsplot@7a724cd`; retained hashes and raw oracle objects define the reviewed reference boundary. | `docs/upstream/manifest.json`; `oracle/fixtures/manifest.json` | 2026-09-15 |
| `m6-release-candidate` | M0–M6 and the internal 0.4 product gate are accepted. The clean candidate passed 267 tests, 92% coverage, lint, strict typing, vulnerability/license audit, source/wheel build, oracle and benchmark verification, replay checks, and installed-wheel smoke on Python 3.11 and 3.12. M7 compatibility closure and 1.0 hardening remain. | `docs/evidence/M6_RELEASE_VERIFICATION.md`; `docs/evidence/M6_SIGNOFF.md`; `docs/MILESTONE_6.md` | 2026-09-15 |
| `release-automation` | Stable semantic tags build and verify artifacts once, create a GitHub release with the wheel, sdist, SBOM, and checksums, then publish only the wheel and sdist through the protected `pypi` environment using PyPI trusted publishing. The workflow stores no long-lived PyPI credential. | `.github/workflows/release.yml`; `tools/verify_release.py` | 2026-09-15 |
| `m7-entry` | M7 is active. Joshua Myers approved M7-D1 through M7-D3 without revision on 2026-09-15: stabilize the existing adapted surface for all 22 upstream exports, retain 29 gap clusters as post-1.0 candidates and reject 19, execute the locked robust-meta boundary plan before final disposition, and adopt the 1.x API/schema policy. Codex owns implementation and Joshua Myers owns product/statistical approval and independent review. | `docs/MILESTONE_7.md`; `docs/m7/compatibility-disposition.json`; `docs/M7_CALIBRATION_PLAN.md`; `docs/adr/ADR-007-public-api-schema-stability.md` | 2026-09-15 |
| `m7a-public-contract` | Joshua Myers accepted M7A pass 2 on 2026-09-15. All 144 root exports remain retained without removals or renames. M7B superseded the all-stable candidate by marking seven dedicated robust-meta names experimental; the other 137 remain stable candidates. M7C golden variants remain open. | `docs/PUBLIC_API_REFERENCE.md`; `docs/MIGRATING_TO_1_0.md`; `docs/m7/public-contract.json`; `docs/evidence/M7A_PASS2_VERIFICATION.md` | 2026-09-15 |
| `m7b-calibration-harness` | Joshua Myers independently reviewed the sealed M7B mapping (76,000 fits) and confirmation (40,000 fits) and approved experimental reclassification for 1.0. The mapping's one `robust_meta_ambiguous_optimum` failure blocks reaffirmation; neither run had an undercoverage flag. The runtime estimator and no-fallback behavior remain, while seven dedicated `RobustMeta*` names and the robust schema-v2 variant are outside the stable 1.x promise. | `docs/evidence/M7B_MAPPING_VERIFICATION.md`; `docs/evidence/M7B_CONFIRMATION_VERIFICATION.md`; `docs/evidence/M7B_INDEPENDENT_REVIEW.md`; `docs/m7/compatibility-disposition.json` | 2026-09-15 |

## Verified traps and failed approaches

| Key | Symptom and cause | Evidence or reproducer | Last verified |
|---|---|---|---|
| `license-mismatch` | The original proprietary template placeholder conflicted with the approved distribution posture; ADR-010 replaced it with MIT. | `LICENSE`; `docs/adr/ADR-010-license-posture.md` | 2026-09-14 |
| `release-glob` | A broad `dist/*` GitHub-release glob included the ignored `dist/.gitignore` as `default.gitignore`; release assets must use explicit wheel, sdist, SBOM, and checksum patterns. | `.github/workflows/release.yml`; GitHub release `v0.1.0` | 2026-09-15 |
