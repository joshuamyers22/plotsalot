# M6A Adversarial Review

- Candidate date: 2026-09-14
- Review scope: approved R1–R3/G6 implementation and evidence
- Candidate self-review: complete
- Independent reviewer: Joshua Myers
- Independent decision: accepted, 2026-09-14

The implementation owner performed the following fault-oriented review to make
the technical candidate reviewable. This is not independent acceptance.

| ID | Adversarial concern | Evidence | Disposition |
|---|---|---|---|
| M6A-A-001 | Copying upstream robust labels could hide incompatible estimands, df, or intervals | Raw pinned objects are retained beside independent base-R calculations; verifier asserts approved R1/R2/R3 values and `h-2` R2 df | Resolved in candidate; compatibility is explicitly `adapted` |
| M6A-A-002 | Matrix/group ordering or Python hashing could change stochastic results | Canonical typed SHA-256/SeedSequence identities, reordered-matrix tests, same-seed replay, and two `PYTHONHASHSEED` processes produce stable child streams | Resolved in candidate |
| M6A-A-003 | Bootstrap failure could be hidden by redraw, imputation, or a smaller unreported sample | Requested/valid/failed counts reconcile in immutable results; a fault fixture fails below `max(950,ceil(0.99*B))`; no redraw path exists | Resolved in candidate |
| M6A-A-004 | Large matrix/group requests could draw before aggregate work is known or return partial results | Scatter/matrix/group totals are preflighted against default/hard ceilings; resource grid records boundary acceptance/rejection; invalid child fault test returns no grouped result | Resolved in candidate |
| M6A-A-005 | Mutation could make displayed inference disagree with its kernel, family, or correction | Constructor-fault tests mutate counts, q, targets, statistics, df, effects, resampling counts, mirrored cells, pairs, adjustments, and repeated correction fields; invalid states raise | Resolved in candidate |
| M6A-A-006 | A robust failure could silently downgrade to a classical analysis | Mode dispatch is explicit; small/degenerate/invalid/bootstrap/resource failures raise; warnings/results identify robust methods; no fallback branch exists | Resolved in candidate |
| M6A-A-007 | The percentile interval could replay but still have unacceptable finite-sample behavior | Locked 300-case calibration covers negative/null/positive association with 0.94/0.99/0.95 observed coverage inside the predeclared 0.86–1.00 band | Resolved and accepted |

## Independent review decision

Joshua Myers independently reviewed the implementation and evidence, reported
no new finding, accepted every recorded disposition, and accepted the M6A
technical candidate on 2026-09-14.
