# Milestone M3: Between- and Within-Group Comparisons

- Status: Planned; statistical-method approval pending
- Contract date: 2026-09-14
- Target duration: 5–7 weeks
- Product and statistical owner: Joshua Myers
- Implementation, visualization, and independent-review owners: Unassigned

## Objective

Add classical frequentist comparisons for independent groups and repeated
measurements, including inspectable omnibus and pairwise results, reconciled
analysis/plot samples, and semantic Matplotlib figures. M3 also closes the
composition and theme utilities promised for the `0.1` product gate.

This contract fixes the product boundary, evidence requirements, and stopping
rules. It does not approve a statistical method. Each implemented mode remains
blocked until Joshua Myers approves its method record.

## Entry gate

M0, M1, and M2 are complete. The M2 typed-result, owned-data, grouped-operation,
rendering, extraction, oracle, resource, and production contracts remain in
force unless an approved M3 decision explicitly supersedes one.

Before implementation begins for an individual comparison mode, its method
record must define and receive statistical-owner approval for the estimand,
test, interval, effect size, missingness policy, assumption behavior,
multiplicity family, pairwise behavior, repeated-measure identity policy where
applicable, compatibility classification, oracle, and numerical tolerance.

## Delivery tracks and release boundary

M3 is delivered in two ordered tracks within the existing 5–7 week estimate.
The allocations below are planning bounds, not separate additions to that
estimate.

| Track | Planned allocation | Required public surfaces | Product gate |
|---|---:|---|---|
| M3A: independent groups and composition | 3–4 weeks | `ggbetweenstats`, `grouped_ggbetweenstats`, `combine_plots`, `theme_ggstatsplot` | Completes the remaining M3-owned `0.1` scope |
| M3B: repeated measurements | 2–3 weeks | `ggwithinstats`, `grouped_ggwithinstats` | Supplies the within-subject portion of `0.2` |

M3A may produce a `0.1` release candidate after all applicable gates pass. That
does not mark M3 complete. M3 is complete only after M3B also passes its gates.
Likewise, completing M3B does not by itself complete the wider `0.2` product
gate, which also includes M4 categorical families.

## Product scope

| Family | Required behavior | M3 outcome |
|---|---|---|
| Two independent groups | Approved two-sample inference, effect estimate, interval, effect size, sample audit, and semantic distribution renderer | M3A |
| Three or more independent groups | Approved omnibus inference plus explicitly scoped pairwise comparisons | M3A |
| Grouped independent comparisons | Deterministic outer-group execution with atomic failure and separately identified inner comparison levels | M3A |
| Composition | Arrange compatible plot containers without losing their typed results, axes identities, annotations, or group identities | M3A |
| Theme | Provide an owned, documented Matplotlib styling surface without mutating global plotting state | M3A |
| Two repeated conditions | Approved paired inference using an explicit subject/condition identity policy and auditable complete-pair sample | M3B |
| Three or more repeated conditions | Approved repeated-measures omnibus inference, assumption/correction metadata, and paired post-hoc comparisons | M3B |
| Grouped repeated comparisons | Deterministic outer-group execution with atomic failure and subject identities scoped safely within groups | M3B |
| Extraction | `extract_stats`, `extract_subtitle`, and `extract_caption` work for every new plot and composed/grouped container | Both |

Every statistical surface must expose at least one approved classical method.
Additional upstream modes and arguments may be deferred individually only when
the compatibility matrix records an explicit disposition. Removing an entire
surface or delivery track requires a product-owner-approved contract amendment.

## Deliverables and acceptance evidence

| Deliverable | Acceptance evidence | Track | Status |
|---|---|---|---|
| Approved method records | Reviewed specification for every supported independent or repeated-measures mode | Both | Pending |
| Independent-group data contract | Typed level identities, retained observations, per-level counts, exclusions, and stable order | M3A | Planned |
| Independent-group analysis | Approved two-level and three-or-more-level analysis paths with analytic, independent-reference, and oracle tests | M3A | Planned |
| Repeated-measures data contract | Explicit subject/condition mapping, duplicate detection, completeness audit, and stable condition order | M3B | Planned |
| Repeated-measures analysis | Approved two-condition and three-or-more-condition paths with analytic, independent-reference, and oracle tests | M3B | Planned |
| Pairwise comparison core | Typed hypotheses, estimates, raw and adjusted probabilities, interval/effect metadata, and display disposition | Both | Planned |
| Versioned result schemas | Frozen JSON-safe schemas for omnibus, pairwise, sample-audit, assumption, grouped, and composition records | Both | Planned |
| Semantic renderers | Layer and annotation tests proving that displayed statistics originate in the paired typed result | Both | Planned |
| Grouped execution | Stable order and identity, nested sample audits, declared correction scope, and atomic failure | Both | Planned |
| Composition and theme utilities | Public API tests, result-preservation tests, local-style tests, and explicit incompatibility errors | M3A | Planned |
| Compatibility disposition | Every touched upstream method and argument classified in `compatibility.md` | Both | Planned |
| Oracle and independent evidence | Frozen pinned-R fixtures plus analytic or independent Python references at predeclared tolerances | Both | Planned |
| Performance baseline | Retained analysis/render measurements across row, level, pairwise, subject, condition, and composition grids | Both | Planned |
| Public documentation | Examples, method limitations, sample rules, assumptions, errors, extraction, and reproducibility metadata | Both | Planned |
| Production repository gate | Check, audit, build, isolated-wheel smoke, oracle verification, and benchmark verification pass | Both | Planned |
| Review and sign-off | Verification loop, adversarial review, finding disposition, independent review, and Joshua Myers approval | Both | Pending |

## Statistical method approval checklist

Each supported method record must define, before implementation fixtures are
treated as acceptance evidence:

- population, sampling unit, experimental unit, estimand, null and alternative
  hypotheses, and sidedness;
- the decision rule selecting the two-level or three-or-more-level path;
- estimator/test identity, parameterization, degrees of freedom, equal-variance
  assumptions, and any Welch or other correction behavior;
- effect-size identity, bias correction, sign/orientation, interval target,
  interval method, confidence level, and one- versus two-sided behavior;
- the omnibus hypothesis and its relationship to follow-up comparisons;
- pairwise contrast direction, comparison family, adjustment method, raw and
  adjusted probability retention, alpha, and display-filter behavior;
- null, non-finite, constant, tied, minimum-sample, empty-level, extreme-value,
  and assumption-failure behavior;
- exact analyzed and plotted samples, including whether missingness is removed
  per observation, level, comparison pair, outer group, subject, or complete
  repeated-measures block;
- for repeated measures, the required subject identifier policy, uniqueness of
  subject-condition cells, condition ordering, incomplete-subject policy, and
  whether plotted paths and inferential samples may differ;
- for three-or-more repeated conditions, the approved sphericity diagnostic,
  correction rule, corrected degrees of freedom, and reported uncorrected and
  corrected values;
- any resampling algorithm, deterministic inputs, caller-owned random generator,
  replicate budget, failure behavior, and calibration evidence;
- structured result fields, rendered labels, compatibility tier, numerical
  tolerance, and independent reference.

Pairwise display filtering is presentation only. It must never erase computed
hypotheses, raw probabilities, adjusted probabilities, or family metadata from
the structured result.

## Data and result invariants

- Each plotted distribution and statistical result uses the same retained
  observations, or the result records an approved, visible reason for a
  plot-only observation to be excluded from inference.
- Per-level, per-comparison, and per-subject counts reconcile to a typed sample
  audit. Missingness and exclusion reasons are machine-readable.
- A subject-condition cell has at most one analyzed value. Duplicate cells fail
  with the subject and condition identified; values are never silently averaged
  or selected.
- Reordering input rows cannot change level order, condition order, subject
  pairing, hypothesis orientation, or correction-family membership.
- Omnibus and pairwise results retain method identity, hypotheses, degrees of
  freedom, estimates, intervals, effect sizes, raw probabilities, adjusted
  probabilities, alpha, and assumption/correction metadata where applicable.
- Multiple-testing scope is explicit. Inner comparison families and outer
  grouped families are never pooled accidentally.
- Every displayed scalar, bracket, interval, subtitle, caption, and assumption
  marker is traceable to a typed result field; renderers do not recompute
  statistics.
- A grouped operation is atomic: an invalid group identifies the group and
  fails the operation instead of returning an unlabeled partial result.
- Group, level, condition, subject, and comparison identities remain distinct in
  memory and serialized output, including null outer-group labels.
- Caller data is not mutated. Retained numeric and identity arrays are owned and
  read-only.
- Analysis modules do not import Matplotlib or mutate global plotting or random
  state.
- Public mappings are JSON-safe and contain no Polars, NumPy, SciPy,
  Statsmodels, or Matplotlib objects.
- R and the network remain development-only oracle facilities, never package
  runtime requirements.

## Composition and theme contract

- `combine_plots` accepts only documented plotsalot plot/container forms and
  rejects incompatible inputs with the item position and expected type.
- Composition preserves the source result objects and exposes deterministic
  panel identities and layout metadata for extraction and serialization.
- Composition does not rerun analysis, alter annotations, renumber statistical
  hypotheses, or silently discard grouped members.
- Rows, columns, guide/legend behavior, shared labels, titles, subtitles,
  captions, and panel tags have owned parameters with deterministic defaults.
- Invalid dimensions, contradictory layout requests, empty inputs, and requests
  above the composition ceiling fail before a partial figure is returned.
- `theme_ggstatsplot` returns or applies an owned style contract with documented
  defaults. It does not change Matplotlib `rcParams` or other process-global
  state.
- Theme and composition compatibility target semantic equivalence with the
  pinned upstream behavior; arbitrary patchwork expressions and pixel-identical
  ggplot reproduction are not required.

## Required fixture matrix

| Area | Minimum retained cases |
|---|---|
| Two independent groups | balanced and unbalanced samples; different spreads; positive, negative, and null effects; null-containing input; reordered levels; minimum valid samples; constant level; ties; non-finite values; extreme finite scale |
| Three or more independent groups | balanced and unbalanced designs; different spreads; null and clear omnibus effects; reordered levels; empty declared level; sparse or invalid level; ties; non-finite values; extreme finite scale |
| Independent pairwise | 3, 5, 10, and maximum supported levels; known raw and adjusted probabilities; tied probabilities; all/significant/non-significant/none display filters; stable contrast orientation |
| Two repeated conditions | complete pairs; partial subjects; duplicate subject-condition cells; missing identifiers; reordered rows and conditions; minimum complete pairs; constant differences; non-finite values; extreme finite scale |
| Three or more repeated conditions | complete blocks; partial blocks; reordered subjects/conditions; assumption-satisfying and correction-triggering cases; sparse condition; constant subject profiles; duplicate cells; invalid minimum sample |
| Repeated pairwise | pair-specific and complete-block missingness candidates; stable subject pairing; known adjusted probabilities; display filters; omnibus/post-hoc family separation |
| Grouped | explicit and observed outer-group order; null outer-group label; repeated subject labels across different outer groups; sparse or invalid group; reordered rows; atomic failure; nested correction metadata |
| Composition and theme | one and many plots; heterogeneous plot families; grouped containers; row/column layouts; titles, labels, tags, and legends; result preservation; invalid input; empty input; ceiling boundary; no global-style mutation |

Oracle agreement alone is insufficient. Every supported deterministic method
also needs an analytic case or independent implementation/reference. A library
used by the production analysis is not independent evidence for itself.
Stochastic methods need retained aggregate calibration evidence with declared
error bounds.

## Performance and resource requirements

- Preserve the retained M0 and M2 benchmarks. Investigate any median analysis
  time, render time, or peak-allocation regression above 20% on the same host.
- Add five independent analysis and render measurements for every retained M3
  workload; do not time oracle startup or input-frame construction as analysis.
- Retain independent-group workloads at 10K, 100K, and 1M rows and at 2, 5, 10,
  and 20 comparison levels.
- Retain repeated-measures workloads spanning 100, 1K, and 10K subjects and 2,
  5, and 10 conditions, including at least one incomplete-block case.
- Retain pairwise workloads through the declared maximum comparison family and
  composition workloads at 1, 4, 10, and the maximum supported panel count.
- Measure data selection, analysis, and rendering separately; state whether the
  input frame is inside or outside the allocation boundary.
- Before implementation, declare defaults and explicit overrides for input rows,
  levels/conditions, outer groups, pairwise hypotheses, rendered observations,
  subject paths, composed panels, and any resampling work. Every applied limit
  is serialized in the result.
- Oversized requests fail predictably or require an explicit override. There is
  no silent row, subject, hypothesis, or path sampling.
- Do not create placeholder benchmark results for an unimplemented path.

## Compatibility requirements

- Audit the pinned `ggstatsplot@7a724cd` implementations and documentation for
  all six public surfaces before declaring an argument supported.
- Classify each touched function, method, and argument as equivalent, adapted,
  experimental, or deferred in `compatibility.md`.
- Preserve familiar public names where they do not compromise Python typing,
  sample safety, or result inspectability. Record deliberate Python-specific
  differences next to tests that enforce them.
- Unsupported `type` modes, pairwise methods, prior-related arguments, arbitrary
  layer injection, and R-specific theme/composition objects fail explicitly;
  they are never accepted and ignored.
- Upstream subtitle or caption parity is evidence for label compatibility, not
  a substitute for independent statistical validation.

## Non-goals

- Robust or Bayesian comparison modes assigned to M6.
- Categorical bar/pie families assigned to M4.
- Coefficient plots or meta-analysis assigned to M5.
- Multifactor ANOVA, ANCOVA, regression adjustment, mixed-effects models,
  cluster-robust inference, or arbitrary contrast matrices.
- Automatic inference of a subject identifier unless a future approved method
  record explicitly defines and justifies it.
- General dataframe interchange or pandas support.
- Arbitrary ggplot layer injection, patchwork expression compatibility, or
  pixel-identical reproduction of an R figure.
- Support for arbitrary R expressions, dynamic function lookup, or R model
  objects.
- Final 1.0 stability for schemas or rendering style.

## Verification rubric

| Dimension | Severity | Pass threshold |
|---|---|---|
| Statistical identity | Blocking | Approved method record; analytic/independent evidence; oracle disposition; correct estimates, tests, effects, intervals, labels, and metadata |
| Sample and pairing integrity | Blocking | Plotted/tested samples reconcile; repeated subject pairing and duplicate detection pass adversarial cases |
| Multiplicity integrity | Blocking | Omnibus and pairwise families, raw/adjusted values, display filters, and nested grouped scope are explicit and tested |
| Result/render contract | Blocking | Versioned JSON-safe results; displayed values originate only from those results; analysis remains renderer-independent |
| Grouping, composition, and theme | Blocking | Stable identities, atomic grouped behavior, result-preserving composition, deterministic layout, and no global style mutation |
| Failure behavior | Blocking | Unsupported modes, invalid data, ambiguous pairing, invalid layout, and resource excess fail explicitly without partial output |
| Compatibility | Blocking | Every touched upstream surface and argument is classified; differences are documented and tested |
| Production quality | Blocking | `make check`, `make audit`, `make build`, isolated-wheel smoke, oracle verification, and benchmark verification pass |
| Coverage | Required | Project branch coverage remains at least 75%; new M3 domain branches reach at least 90% |
| Performance | Required | Retained paths stay within the 20% investigation threshold or have an approved disposition; M3 baselines are complete |
| Documentation | Required | Public examples, limitations, assumptions, sample rules, errors, result fields, and reproducibility behavior match implementation |

## Verification budget and stopping rules

- Use at most three evidence-changing verification passes per delivery track.
- A later pass must add a focused test, full package gate, independent numerical
  reference, retained oracle/benchmark evidence, or a meaningfully different
  architecture/statistical review.
- Stop implementation of a method when its estimand, variance assumption,
  missing-data policy, subject identity, sphericity behavior, correction family,
  effect-size definition, or interval semantics are ambiguous; escalate to the
  statistical owner.
- Stop a track on an unexplained oracle mismatch, sample/pairing mismatch,
  multiplicity-scope mismatch, result/render divergence, unbounded workload,
  package-gate failure, or unapproved compatibility claim.
- Record accepted, corrected, deferred, and rejected review findings with an
  owner and acceptance check. Repeating review against unchanged evidence does
  not count as another pass.

## Required closeout artifacts

- `docs/M3_STATISTICAL_METHODS.md`
- `docs/evidence/M3A_VERIFICATION_LOOP.md`
- `docs/evidence/M3A_ADVERSARIAL_REVIEW.md`
- `docs/evidence/M3A_VERIFICATION.md`
- `docs/evidence/M3A_SIGNOFF.md`
- `docs/evidence/M3B_VERIFICATION_LOOP.md`
- `docs/evidence/M3B_ADVERSARIAL_REVIEW.md`
- `docs/evidence/M3B_VERIFICATION.md`
- `docs/evidence/M3B_SIGNOFF.md`
- updated `docs/compatibility.md`, `STATISTICAL_ANALYSIS_PLAN.md`, public API
  documentation, schemas, oracle manifest, and benchmark manifest

Joshua Myers must approve each supported statistical method before its fixtures
become acceptance evidence and approve each release candidate after all findings
are dispositioned. Agent review cannot supply either approval.

## Track and milestone exit gates

M3A is complete only when both independent-group surfaces expose at least one
approved method; omnibus and pairwise sample/multiplicity contracts pass;
composition, theme, grouping, extraction, compatibility, schema, oracle,
performance, documentation, and production gates pass; all blocking findings
are closed; and Joshua Myers approves the M3A release candidate.

M3B is complete only when both repeated-measures surfaces expose at least one
approved method; subject identity, duplicate detection, missingness, pairing,
assumption/correction, omnibus, pairwise, grouping, extraction, compatibility,
schema, oracle, performance, documentation, and production gates pass; all
blocking findings are closed; and Joshua Myers approves the M3B release
candidate.

M3 is complete only when both M3A and M3B are complete, every remaining touched
method and argument has an explicit compatibility disposition, and the combined
release candidate passes the production gate from a clean source tree.
