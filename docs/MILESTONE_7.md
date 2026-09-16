# Milestone M7: Compatibility Closure and 1.0 Hardening

- Status: active; M7-D1 through M7-D3 and M7A accepted 2026-09-15
- Contract date: 2026-09-15
- Target duration: 4–6 weeks after entry approval
- Product and statistical owner: Joshua Myers
- Implementation owner: Codex
- Independent-review owner: Joshua Myers

## Objective

Convert the accepted M0–M6 implementation and the published `0.1.1` package
into an explicitly stable 1.0 contract. M7 closes compatibility decisions,
resolves the provisional M6C robust-meta calibration boundary, freezes public
API and serialized-result guarantees, hardens the supported workflows, and
produces reviewable 1.0 release evidence.

M7 is not a mandate to reproduce every `ggstatsplot` argument or R model class.
The approved 1.0 product boundary stabilizes the 22 already dispositioned
upstream exports and their implemented Python surfaces. Deferred capabilities
remain visible as approved post-1.0 candidates or explicit non-goals unless the
product/statistical owner approves a later scope change.

## Entry state and inherited contracts

M0 through M6 and the internal `0.4` product gate are complete. Version `0.1.1`
is published on PyPI through the protected trusted-publishing workflow. The
following contracts remain binding unless an approved M7 decision supersedes
them:

- Polars is the public tabular boundary and selected numeric data crosses an
  explicit owned NumPy boundary.
- Analysis and rendering remain separate; every rendered statistic originates
  in a typed result field.
- Invalid data, unsupported modes, numerical failure, and grouped-member
  failure do not trigger estimator fallback or partial grouped output.
- R, Docker, network access, and oracle repositories remain development-only.
- Statistical equivalence and semantic visual equivalence are verified
  separately; pixel identity is not a goal.
- Stochastic and iterative work remains deterministic, provenance-bearing, and
  bounded before expensive execution.

The pinned compatibility baseline remains
`ggstatsplot@7a724cd0ab55668b9d0b2e84b12c711c5be68ac8`. Updating that revision is a
separate scope decision because upstream drift cannot silently redefine 1.0.

## Approved entry decisions

Joshua Myers approved all three entry decisions without revision on 2026-09-15:

| ID | Decision | Approved disposition | Approval state |
|---|---|---|---|
| M7-D1 | Exact 1.0 compatibility scope | Stabilize the existing adapted surface for all 22 upstream exports; add no new statistical family solely for 1.0 | Approved 2026-09-15 |
| M7-D2 | M6C robust-meta calibration experiment and decision options | Run the locked boundary experiment in `M7_CALIBRATION_PLAN.md`, then reaffirm, replace, or reclassify the method from retained evidence | Approved 2026-09-15 |
| M7-D3 | Public API, schema, deprecation, and migration promise | Adopt `API_STABILITY.md` as the 1.x compatibility contract | Approved 2026-09-15 |

Approval authorizes the planned work and acceptance fixtures. It does not
accept an implementation, a calibration result, a release candidate, or 1.0.

## Delivery tracks

| Track | Planned allocation | Required outcome |
|---|---:|---|
| M7A: scope and compatibility closure | 1 week | Every export and deferred capability has an owner-approved 1.0 disposition; inventory drift fails CI |
| M7B: M6C calibration resolution | 1–2 weeks | Predeclared boundary experiment is retained unchanged and the robust-meta method is reaffirmed, corrected, or reclassified |
| M7C: API/schema hardening | 1–2 weeks | Public names, signatures, result variants, schemas, errors, semantic plot keys, and migration rules meet the approved stability contract |
| M7D: documentation and 1.0 closeout | 1 week | User docs, compatibility statements, clean artifacts, reproducibility evidence, independent review, and owner acceptance support a 1.0 decision |

M7A is the entry gate. M7B and M7C may proceed independently after their
applicable decisions are approved. M7D begins only after M7A–M7C have no open
blocking finding.

## Approved 1.0 compatibility boundary

The source of truth for the approved boundary is
[`m7/compatibility-disposition.json`](m7/compatibility-disposition.json). It
must contain exactly the 22 exports in the pinned upstream inventory, exactly
one disposition for each export, unique gap identifiers, and only declared
disposition values.

The boundary follows these rules:

- Existing supported classical, robust, Bayesian, grouped, extraction,
  composition, and theme behavior is in the 1.0 stabilization boundary.
- A feature is not required for 1.0 merely because an older milestone called it
  deferred. The ledger must say whether it is a post-1.0 candidate or rejected
  by the product architecture.
- Previously implemented M6 robust or Bayesian behavior supersedes stale M2–M5
  statements that called those modes deferred.
- Arbitrary ggplot layers, pixel identity, inferred repeated-subject identity,
  partial grouped success, hidden fallback, broad model dispatch, and dynamic R
  object behavior remain rejected unless an ADR changes the governing boundary.
- Reopening a post-1.0 capability requires its own method specification,
  evidence plan, resource limits, compatibility classification, and approval.

## API and schema hardening boundary

The approved stability rules are specified in [`API_STABILITY.md`](API_STABILITY.md).
M7C must inventory and test at least:

- every name in `plotsalot.__all__` and every installed console script;
- public function signatures, keyword-only defaults, accepted selectors, and
  documented exception classes or stable error codes;
- all typed public result/container records and their `to_dict()` output;
- every schema discriminator and retained schema version in `schemas/`;
- semantic axes/layer keys used for supported customization and composition;
- minimum Python, platform, and dependency compatibility declarations; and
- deprecation and migration behavior for any proposed change.

Exact exception prose, artist coordinates, colors, fonts, and pixel output are
not stable unless a narrower public contract explicitly says otherwise.

## M6C calibration boundary

The retained finding is conservative 95% profile-likelihood interval coverage
at the exact zero-heterogeneity boundary for both small and larger study counts.
The current provisional acceptance rule applies one-sided conservative handling
when `k<20` or generating `tau=0`, but generating heterogeneity is not observable
at runtime. M7 must therefore characterize the neighborhood around zero and
make an operationally meaningful decision.

The experiment in [`M7_CALIBRATION_PLAN.md`](M7_CALIBRATION_PLAN.md) freezes the
scenario grid, seeds, case counts, estimands, intervals, failure accounting,
acceptance summaries, compute ceiling, and decision options before new evidence
is generated. No failed cell may be removed, pooled, silently rerun, or relabeled
under a new threshold.

## Deliverables and acceptance evidence

| Deliverable | Required evidence | Initial state |
|---|---|---|
| M7 contract and decision ledger | Owner-approved M7-D1 through M7-D3 | Accepted 2026-09-15 |
| Machine-readable compatibility closure | Exact 22-export inventory test and unique disposition coverage | M7A pass 2 accepted 2026-09-15 |
| Robust-meta boundary resolution | Locked experiment artifact, independent calculation/review, and owner disposition | Mapping and confirmation retained; reaffirmation blocked, owner disposition pending |
| Public API manifest | Generated/retained names and signatures compared in CI with reviewed exceptions | All 144 names classified for stabilization; M7A pass 2 accepted 2026-09-15 |
| Schema stability fixtures | Golden serialized variants, schema validation, version/migration tests, and mutation rejection | Not started |
| Error and refusal contract | Typed error/code inventory plus invalid, degenerate, ceiling, and atomic-group fault tests | Not started |
| Platform/package gate | Python 3.11 and 3.12 isolated wheel/sdist install, import, public smoke, and metadata inspection | Existing 0.1.1 evidence; repeat for 1.0 candidate |
| Oracle and benchmark gate | Applicable pinned-oracle, replay, calibration, schema, and retained performance checks | Existing baseline; repeat after changed boundaries |
| Documentation closure | Getting started, user guide, compatibility, limitations, migration, security, and release docs agree | Partial |
| Independent review and acceptance | Finding ledger closed; product/statistical and release acceptance recorded separately | Not started |

## Verification loop and stop rules

[`evidence/M7_VERIFICATION_LOOP.md`](evidence/M7_VERIFICATION_LOOP.md) defines
the review rubric, iteration ceiling, escalation triggers, and evidence-changing
passes. At minimum:

1. inventory and contract verification;
2. statistical/numerical and adversarial boundary verification;
3. clean source/build/install and documentation verification; and
4. independent review of the exact candidate.

A repeated review against unchanged evidence is not another pass. Work stops on
any unapproved statistical-method change, compatibility-scope expansion,
unresolved calibration blocker, silent schema break, dependency/license blocker,
or inability to reproduce the exact release candidate.

## Explicit non-goals

- line-by-line R translation, tidy evaluation, or arbitrary `ggplot2` layers;
- pixel-identical rendering or global Matplotlib state mutation;
- inferred subject identity or partial grouped success;
- support for every R model class, arbitrary fitted objects, or dynamic tidiers;
- a generic Bayesian framework, posterior-draw ingestion, or hidden MCMC;
- automatic statistical interpretation, model selection, fallback, or outlier
  deletion; and
- a Shiny-equivalent application, service, database, or remote telemetry.

## Exit gate

M7 and 1.0 are complete only when M7-D1 through M7-D3 are approved; the M6C
finding has an evidence-backed final disposition; all in-scope public exports,
signatures, result variants, schemas, semantic plot contracts, and errors are
documented and tested; the full clean-tree production/reproducibility gate
passes; every blocking review finding is closed; and Joshua Myers separately
approves the statistical disposition and the final 1.0 release candidate.
