# Combined M6 and 0.4 Release Verification

- Candidate date: 2026-09-15
- Candidate revision: `15cb0cf44cace7b33b1ec6128ecf3e68c4b156a4`
- Candidate tree: `1279bb1f1fd7ddf43ebaa7edce6e424a87274bfd`
- Starting worktree: clean
- Technical outcome: combined release gate passed
- Accountable M6/`0.4` acceptance: approved by Joshua Myers, 2026-09-15

## Accepted inputs

- M6A robust continuous-analysis candidate: independently reviewed and accepted
  by Joshua Myers on 2026-09-14.
- M6B Bayesian data-analysis candidate: independently reviewed and accepted by
  Joshua Myers on 2026-09-15.
- M6C coefficient/meta candidate: independently reviewed and accepted by Joshua
  Myers on 2026-09-15.
- ADR-005, ADR-006, R1–R4, B1–B6, and G6 have accountable approvals.

The provisional one-sided conservative coverage allowance for M6C when `k<20`
or generating `tau=0` is carried forward unchanged. It is non-blocking for this
candidate under its recorded owner disposition and remains mandatory M7 debt.

## Combined gate results

| Gate | Result |
|---|---|
| Clean committed source boundary | Passed at revision `15cb0cf`; no source changes preceded gate execution |
| Formatting and lint | Passed |
| Strict Pyright | Passed with zero errors or warnings |
| Full unit/integration suite | 267 tests passed |
| Coverage | 92% total; required new M6 domain modules remain at 90% or higher |
| Vulnerability audit | Passed; OSV reported no known vulnerabilities or adverse project statuses |
| Dependency license policy | Passed; runtime remains compatible with the MIT project license |
| Source distribution and wheel build | Passed with pinned Hatchling 1.32.0 |
| Frozen oracle verification | Passed |
| Retained benchmark/work verification | Passed across M6A, M6B, and M6C grids |
| Seed/RQMC replay and identity-focused checks | Five focused cross-track tests passed |
| Isolated installed-wheel smoke, Python 3.12 | Passed offline for robust one-sample, Bayesian one-sample, robust coefficients, Bayesian meta-analysis, extraction, JSON, and four-panel composition |
| Minimum-version installed-wheel smoke, Python 3.11.16 | Passed the same M6A/M6B/M6C analysis, rendering, extraction, schema, JSON, and composition checks |
| Wheel content/license inspection | Passed; runtime modules and MIT license are present; development oracle/reference source is absent |

The initial sandboxed build could not resolve the pinned build backend because
network access was disabled. The authorized network-enabled rerun downloaded
only the declared build requirement and completed. Python 3.12 runtime
installation of the built wheel and all locked dependencies then succeeded
offline from the local cache. The cache lacked a Python 3.11 Statsmodels wheel,
so the authorized minimum-version setup downloaded the constrained runtime
wheels before the Python 3.11.16 smoke completed successfully.

## Cross-track reconciliation

- Classical schema-v1 behavior remains covered by regression fixtures; robust
  outputs use schema version 2 and Bayesian outputs use schema version 3.
- Renderers consume typed retained results and perform no statistical or random
  work. Extraction and mixed composition preserve exact result object identity.
- Robust seeds, Bayesian typed child seeds, RQMC work, meta quadrature work, and
  aggregate grouped ceilings are retained and preflighted without retry or
  fallback.
- Every touched upstream mode and argument has an explicit supported, adapted,
  rejected, or deferred disposition in `../compatibility.md`.
- M6 adds no R, Docker, GPL implementation source, sampler, or network runtime
  dependency.
- No blocking M6A, M6B, or M6C finding remains. The M6C zero-heterogeneity
  allowance is explicitly deferred for reconsideration in M7 rather than
  silently closed.

## Artifact identity

- Source distribution SHA-256:
  `d70303c081533148c9b9e84354d06756554d8926472de0e7b77429f0be699980`
- Wheel SHA-256:
  `6ef24d5556e3df09ec93d55e63e2b12b24595e90e46ecd37e735e14453645860`
- Oracle manifest SHA-256:
  `e89d40bd21c7235e3c09cefa41da6853bd1c8e2a5a435d155c8652575c4c9b39`
- Lockfile SHA-256:
  `7e90e0ae44f19d31464be9316980aae7efb6528191a10b0627138d358f24324b`
- M6A/M6B/M6C benchmark SHA-256 values:
  `4417b3288600dbdd8fb115a04fb823ce3352fa222238d777a07e864c627563d7`,
  `297d134154463576c1d06c9d1878ba6638774564759324c9702066cf1b7e66b1`,
  and `cad36c0eda171c5c917ec591f440896c40e62a3334209e7b4bcc9039466447ba`.
- M6A calibration SHA-256:
  `dc48472010f0f0d35ac18dc74f829433037c1bd15b7e709febe38037c92a9463`.
- M6C first/confirmation calibration SHA-256 values:
  `9b7df31d6913e45370b9163f5ea96eb8c6ee18d7e92923de83e357bf6a4b5d2e`
  and `ae6b4d90cc175a09ad66ae4a4fa2957029a3b7e688b10a46e787188a84e8b75d`.

## Acceptance boundary

This record established the implementation-owner combined technical release
candidate. Joshua Myers subsequently approved the final M6/`0.4` candidate on
2026-09-15, closing the milestone and product gate. That decision did not by
itself create a Git tag or GitHub release, change package metadata, or publish
an artifact.
