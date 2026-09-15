# M6B Adversarial Review

- Candidate date: 2026-09-15
- Review scope: approved B1–B6 implementation and evidence
- Candidate self-review: complete
- Independent reviewer: Joshua Myers
- Independent decision: accepted, 2026-09-15

The implementation owner performed the following fault-oriented review to make
the technical candidate reviewable. Joshua Myers independently reviewed the
candidate, accepted every disposition, and reported no new blocking finding.

| ID | Adversarial concern | Evidence | Disposition |
|---|---|---|---|
| M6B-A-001 | A Bayesian label could hide different likelihoods, priors, nulls, or BF orientation | Schema-v3 results retain method, complete prior, sampling plan, H0/H1 text, finite `log_bf10`, bounded numeric display, and half/double sensitivity | Resolved in candidate; every family is explicitly `adapted` |
| M6B-A-002 | Quadrature could silently lose posterior mass near a boundary or remote mode | Exact correlation sign reversal, mode-aware tail integration, warning/error gates on normalization and every tail, conservative zero-call work preflight, finite error/tolerance records, perfect-correlation failure, and injected-fault tests | Resolved in candidate |
| M6B-A-003 | Random draws could change with ordering, hashing, ambiguous identity encoding, or hidden retries | Eight fixed 4,096-point scrambled Sobol replicates use SHA-256 child seeds over length-prefixed typed scopes; delimiter-collision/type tests pass; root/children/work/target diagnostics are retained; there is no retry path | Resolved in candidate |
| M6B-A-004 | Comparison evidence could test a different null than its posterior contrasts | Independent H0 uses the common-mean submodel; repeated inference uses orthonormal Helmert contrasts; pairwise repeated BF uses exact marginal Student-t Savage–Dickey density ratios | Resolved in candidate; independent constrained-model verification remains an explicit reviewer check |
| M6B-A-005 | Sparse categorical tables could trigger asymptotic fallback or erase declared cells | Proper Dirichlet models support zero observed cells; empty row margins, invalid weights, structural-zero specifications, and paired requests fail; all row-pair/category posterior contrasts are retained | Resolved in candidate |
| M6B-A-006 | A result mutation could make rendering disagree with inference | Constructor mutation tests cover method/prior/algorithm cross-provenance, posterior/evidence/computation, reconciled QMC work and diagnostic maxima, matrix pairing, comparison families, categorical cells/contrasts, and warnings; renderers consume results only | Resolved in candidate |
| M6B-A-007 | Grouped execution could reuse streams, exceed aggregate work, or return a partial result | RQMC child seeds include typed outer-group identity; total grouped RQMC work is preflighted before point generation and retained with the root seed; grouped construction is atomic and group failures are re-raised with identity | Resolved in candidate |

## Independent review decision

Joshua Myers independently reviewed and accepted the M6B candidate and every
recorded disposition on 2026-09-15. No finding remains open for M6B.
