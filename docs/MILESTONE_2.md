# Milestone M2: Frequentist Univariate and Correlation Core

- Status: Planned
- Contract date: 2026-09-14
- Target duration: 4–5 weeks
- Product and statistical owner: Joshua Myers
- Implementation, visualization, and independent-review owners: Unassigned

## Objective

Extend the M1 contracts into a coherent classical frequentist core for
univariate distributions and associations. M2 must produce inspectable typed
results and semantic Matplotlib figures, with explicit statistical methods and
reconciled samples, rather than merely matching upstream labels or pixels.

## Entry gate

M0 and M1 are complete. Before implementation begins for an individual method,
the statistical owner must approve its estimand, sample policy, test and
estimator, interval, multiplicity behavior, effect-size behavior, edge cases,
and compatibility classification. This milestone contract defines delivery
scope; it does not itself approve those statistical choices.

## Product scope

| Family | Public surfaces | M2 outcome |
|---|---|---|
| Histogram | `gghistostats` | Promote the walking skeleton for the explicitly approved classical frequentist modes |
| Dot plot | `ggdotplotstats` | Reuse the approved univariate analysis contract with a dot-plot renderer |
| Scatter | `ggscatterstats` | Return an approved bivariate association result with a scatter renderer and typed annotations |
| Correlation matrix | `ggcorrmat` | Return per-cell estimates, sample counts, uncertainty/test metadata, correction metadata, and a semantic matrix renderer |
| Grouped univariate | `grouped_gghistostats`, `grouped_ggdotplotstats` | Produce deterministic per-group plots and structured results |
| Grouped association | `grouped_ggscatterstats`, `grouped_ggcorrmat` | Produce deterministic per-group association outputs with explicit family-level correction scope |
| Extraction | `extract_stats`, `extract_subtitle`, `extract_caption` | Work consistently for every M2 result and grouped container |

Support is method-by-method. An upstream argument is not supported until the
compatibility matrix names its classification and the public API either
implements it or rejects it with a specific error.

Every surface row above is an M2 delivery commitment and must expose at least
one approved supported method. Additional modes and arguments may be deferred
individually. Removing an entire surface requires a product-owner-approved
contract amendment rather than a closeout-time deferral.

## Deliverables and acceptance evidence

| Deliverable | Acceptance evidence | Status |
|---|---|---|
| Approved method records | One reviewed specification per supported univariate and association mode | Planned |
| Univariate analysis core | Shared analysis used by histogram and dot renderers; analytic, independent-reference, and oracle tests | Planned |
| Association analysis core | Bivariate and matrix results with explicit sample and multiplicity semantics | Planned |
| Grouped execution contract | Stable ordering, group identity, atomic failure behavior, and per-group sample audits | Planned |
| Versioned result schemas | Frozen typed records, JSON-safe mappings, schemas, and migration notes where M1 contracts change | Planned |
| Semantic renderers | Layer/annotation tests showing that every displayed statistic comes from the paired result | Planned |
| Compatibility disposition | Supported and rejected methods/arguments recorded in `compatibility.md` | Planned |
| Oracle and independent evidence | Frozen R fixtures plus analytic or independent Python references at predeclared tolerances | Planned |
| Performance baseline | Scatter workloads at 10K/100K/1M rows and correlation matrices at 10/25/50 variables | Planned |
| Public documentation | Examples, method limitations, extraction behavior, errors, and reproducibility metadata | Planned |
| Production repository gate | Check, audit, build, isolated-wheel smoke, oracle verification, and benchmark verification pass | Planned |
| Milestone review and sign-off | Verification loop, adversarial review, finding disposition, and statistical-owner approval | Planned |

## Statistical specification checklist

Each supported method record must define, before its implementation fixtures are
evaluated:

- population, sampling unit, estimand, null and alternative hypotheses;
- estimator/test identity, parameterization, sidedness, degrees of freedom, and
  effect-size identity where applicable;
- confidence-interval target, method, level, and one- versus two-sided behavior;
- null, non-finite, constant, tied, small-sample, and extreme-value behavior;
- exact analyzed sample and whether missingness is removed per variable,
  variable pair, group, or complete row;
- correlation method and parameter mapping, including how perfect correlation
  and constant inputs behave;
- the multiple-testing family and correction method for matrices and grouped
  outputs, including whether displayed raw and adjusted values are retained;
- any resampling algorithm, deterministic inputs, caller-owned random generator,
  replicate budget, failure behavior, and calibration evidence;
- structured result fields, rendered labels, upstream compatibility tier,
  numerical tolerance, and independent reference.

Classical parametric and nonparametric modes may be proposed. Robust and
Bayesian modes remain outside M2 even if an upstream function exposes them under
the same public name.

## Invariants

- Each plot and statistical result use the same retained numeric observations.
- Every scalar, interval, matrix cell, subtitle, and caption is traceable to a
  typed result field; renderers do not recompute statistics.
- Each matrix cell records its analyzed sample count. Symmetry, diagonal, and
  missing-data behavior follow the approved method record.
- Group order and identity are deterministic and retained in serialized results.
- A grouped operation is atomic: an invalid group identifies the group and
  fails the operation instead of returning an unlabeled partial result.
- Caller data is not mutated. Retained numeric arrays are owned and read-only.
- Analysis modules do not import Matplotlib or mutate global plotting or random
  state.
- Public result mappings remain JSON-safe and contain no Polars, NumPy, SciPy,
  Statsmodels, or Matplotlib objects.
- R and the network remain development-only oracle facilities, never package
  runtime requirements.

## Required fixture matrix

| Area | Minimum retained cases |
|---|---|
| Univariate | ordinary continuous sample, skew, ties, null-containing sample, minimum valid sample, constant sample, non-finite values, and extreme finite scale |
| Bivariate | positive, negative, and near-zero association; perfect association; ties; constant input; null patterns; minimum valid sample; extreme finite scale |
| Matrix | known analytic matrix, mixed missingness, constant column, reordered columns, diagonal behavior, raw and adjusted multiplicity output |
| Grouped | explicit group order, null group label, sparse group, invalid group, reordered rows, and identical values across differently labeled groups |

Oracle agreement alone is insufficient. Every supported deterministic method
also needs an analytic case or an independent implementation/reference.
Stochastic methods need retained aggregate calibration evidence with declared
error bounds.

## Performance and resource requirements

- Preserve the retained M0 histogram benchmark and investigate any median time
  or peak-allocation regression above 20% on the same benchmark host.
- Add five independent analysis and render measurements for each new retained
  workload size.
- Measure analysis separately from rendering and state whether input-frame
  allocation is inside or outside the memory boundary.
- Set explicit limits for rows, variables, groups, rendered artists, and
  resampling work. Oversized requests must fail predictably or require an
  explicit override.
- Do not create placeholder benchmark results for an unimplemented path.

## Non-goals

- Between- or within-group hypothesis-test families assigned to M3.
- Categorical bar/pie families, coefficient plots, or meta-analysis.
- Robust or Bayesian methods.
- General dataframe interchange or pandas support.
- Pixel-identical reproduction of an R figure.
- Support for arbitrary R expressions, dynamic function lookup, R model
  objects, or every upstream argument.
- Final 1.0 stability for schemas or rendering style.

## Verification rubric

| Dimension | Severity | Pass threshold |
|---|---|---|
| Statistical identity | Blocking | Approved method record; analytic/independent evidence; oracle disposition; correct labels and metadata |
| Sample integrity | Blocking | Plotted, tested, grouped, and matrix-cell samples reconcile in focused edge-case tests |
| Result/render contract | Blocking | Versioned JSON-safe results; displayed values originate only from those results; analysis remains renderer-independent |
| Failure behavior | Blocking | Unsupported modes and invalid data fail explicitly without partial or misleading output |
| Compatibility | Blocking | Every touched upstream surface and argument is classified; differences are documented and tested |
| Production quality | Blocking | `make check`, `make audit`, `make build`, isolated-wheel smoke, oracle verification, and benchmark verification pass |
| Coverage | Required | Project branch coverage remains at least 75%; new M2 domain branches reach at least 90% |
| Performance | Required | Retained M0 path stays within the 20% investigation threshold or has an approved disposition; new baselines are complete |
| Documentation | Required | Public examples, limitations, errors, result fields, and reproducibility behavior match the implementation |

## Verification budget and stopping rules

- Use at most three evidence-changing verification passes for the milestone.
- A later pass must add a focused test, full package gate, independent numerical
  reference, retained oracle/benchmark evidence, or a meaningfully different
  architecture/statistical review.
- Stop implementation of a method when its statistical identity, missing-data
  policy, correction family, or interval semantics are ambiguous; escalate to
  the statistical owner.
- Stop the milestone on an unexplained oracle mismatch, sample mismatch,
  result/render divergence, unbounded workload, package-gate failure, or
  unapproved compatibility claim.
- Record accepted, corrected, deferred, and rejected review findings with an
  owner and an acceptance check. Repeating review against unchanged evidence
  does not count as another pass.

## Required closeout artifacts

- `docs/evidence/M2_VERIFICATION_LOOP.md`
- `docs/evidence/M2_ADVERSARIAL_REVIEW.md`
- `docs/evidence/M2_VERIFICATION.md`
- `docs/evidence/M2_SIGNOFF.md`
- updated `docs/compatibility.md`, `STATISTICAL_ANALYSIS_PLAN.md`, public API
  documentation, schemas, oracle manifest, and benchmark manifest

## Exit gate

M2 is complete only when every in-scope surface exposes at least one approved
supported method; remaining methods and arguments have explicit dispositions;
every supported method has statistical-owner approval and the required
independent/oracle evidence; grouped, extraction, schema, failure, and resource
contracts pass; all blocking findings are closed; and the complete production
gate passes from the release candidate. Agent review cannot supply the required
statistical approval.
