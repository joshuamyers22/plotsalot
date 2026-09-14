# Milestone M5: Coefficients and Frequentist Meta-analysis

- Status: M5A and M5B methods approved; implementation pending
- Contract date: 2026-09-14
- Target duration: 4–6 weeks
- Product and statistical owner: Joshua Myers
- Implementation and visualization owner: Codex
- Independent-review owner: Unassigned

## Objective

Add an inspectable `ggcoefstats` workflow for coefficient and study-effect
dot-and-whisker plots. Support a strict Polars coefficient-table protocol, a
narrow allowlist of fitted Statsmodels results, and one approved classical
random-effects meta-analysis over independent study estimates. Every displayed
estimate, interval, test label, model summary, heterogeneity measure, and pooled
effect must originate in a versioned typed result.

M5 completes the `0.3` product gate. It expands model-result interoperability;
it does not turn plotsalot into a model-fitting framework, promise universal
Statsmodels support, or establish 1.0 schema or visual stability.

This contract fixes scope and acceptance evidence. It does not approve a
coefficient interpretation, covariance estimator, meta-analytic estimator, or
small-sample correction. Those decisions require a separate M5 statistical
method record approved by Joshua Myers before inferential implementation.

## Entry gate and inherited contracts

M0 through M4 and the `0.2` product gate are complete. Their Polars boundary,
owned immutable analysis input, typed result, semantic renderer, extraction,
composition, resource, compatibility, oracle, benchmark, package-isolation,
and accountable-review contracts remain in force unless an approved M5
decision explicitly supersedes one.

Before implementation of each track begins, M5 must resolve that track's
applicable decisions: coefficient identity and scale, reported-inference
validation, model-adapter provenance, null/reference values, meta-analytic
estimand, sampling model, between-study variance estimation, pooled inference,
heterogeneity, prediction, small-study behavior, resource limits, and
compatibility dispositions described below.

## Pinned upstream surface audited for scope

M5 covers the sole remaining planned ggstatsplot plot export:

- `ggcoefstats(x, statistic=NULL, conf.int=TRUE, conf.level=0.95,
  exclude.intercept=FALSE, effectsize.type="omega",
  meta.analytic.effect=FALSE, meta.type="parametric", sort="none",
  only.significant=FALSE, stats.labels=TRUE, ...)`.

The scope was prepared against
`ggstatsplot@7a724cd0ab55668b9d0b2e84b12c711c5be68ac8`. The pinned
`R/ggcoefstats.R` source inspected for this contract has SHA-256
`8d920502e98d25f482f727c54d0dbe1917ffa4db5fad7364677f1d142ffb90c0`.
That implementation accepts a wide range of R model objects or tidy data,
optionally extracts AIC/BIC, and offers parametric, robust, and Bayesian
meta-analysis. M5 treats those behaviors as compatibility evidence, not an
automatic Python support promise.

No grouped `ggcoefstats` export exists in the pinned public inventory. M5 does
not invent one.

## Delivery tracks and release boundary

| Track | Planned allocation | Required public surface | Outcome |
|---|---:|---|---|
| M5A: coefficient contract and renderer | 2–3 weeks | coefficient table/model adapters, shared analysis/result, `ggcoefstats` coefficient mode | Establishes safe coefficient ingestion and semantic dot-and-whisker rendering |
| M5B: frequentist meta-analysis and `0.3` closeout | 2–3 weeks | study-effect input, approved random-effects analysis, pooled/heterogeneity result and rendering | Adds the approved classical meta-analysis mode and completes the `0.3` candidate |

M5A may be reviewed separately but does not complete M5 or `0.3`. M5 is
complete only when both modes consume the same coefficient-result contract and
the combined release candidate passes every applicable gate below.

## Product scope

| Family | Required behavior | Track |
|---|---|---|
| Tidy coefficient input | Accept a Polars dataframe with explicit unique term identity, finite estimates, optional complete inference fields, stable order, and an auditable exclusion record | M5A |
| Fitted-model input | Adapt only approved fitted Statsmodels result classes; snapshot public coefficient and model metadata without refitting or retaining the mutable model object | M5A |
| Display-only coefficients | Plot validated terms and estimates when inferential fields are absent, while explicitly recording that intervals/tests are unavailable | M5A |
| Reported coefficient inference | Retain supplied or adapter-derived standard errors, intervals, statistic identity/value, degrees of freedom where applicable, p-values, confidence level, and covariance provenance | M5A |
| Term selection and order | Support explicit intercept exclusion and stable source/ascending/descending estimate order without losing source identity or exclusion audit | M5A |
| Statistical labels | Support all/significant/none label display from retained result fields; filtering labels never filters estimates or changes analysis | M5A |
| Model summary | Retain allowlisted model class, family/link where applicable, covariance type, observation count, and available AIC/BIC without treating fit indices as universal quality judgments | M5A |
| Study-effect input | Require explicit study identity, comparable additive effect scale, finite estimate, positive standard error, and declared independence/estimand semantics | M5B |
| Random-effects meta-analysis | Fit one approved frequentist random-effects model and retain study weights, pooled estimate/test/interval, between-study variance, and heterogeneity diagnostics | M5B |
| Meta-analysis prediction | Retain an approved prediction interval or an explicit reason it is unavailable; never present a confidence interval as a prediction interval | M5B |
| Semantic renderer | Draw horizontal points, intervals, a typed null/reference line, optional statistical labels, and a separately identified pooled meta-analytic layer | Both |
| Extraction and composition | Existing extraction functions and `combine_plots` accept the new container without losing coefficient, model, or meta-analysis result identity | Both |

Both tracks must use one public `ggcoefstats` name with explicit allowlisted
arguments and one `analyze_ggcoefstats`/`render_ggcoefstats` split. At least one
approved classical coefficient path and one approved frequentist random-effects
path are required. Removing either track requires a product-owner-approved
contract amendment.

## Deliverables and acceptance evidence

| Deliverable | Acceptance evidence | Track | Status |
|---|---|---|---|
| Pinned-surface audit | Exact upstream signature, data/model behavior, plot layers, meta modes, and deliberate Python adaptations recorded | Both | Complete |
| Approved method specification | Reviewed K1–K4 and MA1–MA4 records covering every retained inferential path | Both | Complete |
| Coefficient data boundary | Typed table protocol, composite identity, stable order, complete-field profiles, immutable arrays, exclusions, and failure tests | M5A | Planned |
| Statsmodels adapters | Exact class allowlist, public-field extraction, covariance/test provenance, no refit, and adversarial fake-object rejection | M5A | Planned |
| Shared coefficient analysis | Display-only and inferential inputs produce one renderer-independent analysis/result contract | M5A | Planned |
| Frequentist meta-analysis | Approved random-effects estimate, weights, interval/test, prediction, and heterogeneity with independent evidence | M5B | Planned |
| Versioned result schema | JSON-safe coefficient, inference, model-summary, meta-analysis, audit, provenance, warning, and resource records | Both | Planned |
| Semantic renderer | Layer and injection tests prove every displayed quantity comes from the typed result | Both | Planned |
| Extraction and composition | Individual extraction and heterogeneous M2–M5 composition preserve result identity | Both | Planned |
| Compatibility disposition | Every touched upstream model/method/argument classified in `compatibility.md` | Both | Planned |
| Oracle and independent evidence | Frozen pinned-R objects plus analytic or independently implemented references at approved tolerances | Both | Planned |
| Performance baseline | Five-sample adapter/selection/analysis/render grids through declared term and study ceilings | Both | Planned |
| Public documentation | Coefficient protocol, supported models, scale/null semantics, meta assumptions, labels, errors, limits, and adaptations | Both | Planned |
| Production repository gate | Check, audit, build, isolated-wheel smoke, oracle verification, and benchmark verification pass | Both | Planned |
| Review and sign-off | Verification loop, adversarial review, finding disposition, independent review, and Joshua Myers approval | Both | Planned |

## Required statistical decision records

The M5 method specification must name and obtain approval for:

- K1: coefficient estimand, term identity, estimate scale, null/reference value,
  confidence target, and display-only versus inferential input profiles;
- K2: reported-inference validation, supported `t`/`z` or other statistic
  identities, degrees of freedom, p-value/interval consistency, sidedness, and
  whether any missing inferential quantity may be derived;
- K3: exact Statsmodels class allowlist, parameter-name mapping, covariance
  provenance, fitted-sample metadata, model family/link handling, and failure on
  unsupported or ambiguous objects;
- K4: intercept identity, source and sorted order, label-significance rule,
  model-summary fields, and separation between presentation filtering and
  retained results;
- MA1: study population, sampling unit, effect estimand/scale/direction,
  sampling-variance input, independence assumption, and admissible study count;
- MA2: random-effects sampling model, study weights, between-study variance
  estimator and bounds, convergence criteria, and zero-heterogeneity behavior;
- MA3: pooled hypothesis, test/reference distribution, confidence interval,
  prediction interval, confidence level, sidedness, and small-sample correction;
- MA4: Cochran-Q or other heterogeneity statistic, degrees of freedom, I-squared
  definition and bounds, tau/tau-squared reporting, influence diagnostics if
  retained, and behavior for small, dominant, or numerically extreme studies.

Approval for each applicable record must also cover:

- exact input fields, units, valid ranges, missingness, duplicate identities,
  stable ordering, and whether reported intervals must contain their estimates;
- whether inference supplied by callers is trusted, cross-validated for internal
  coherence, or recomputed, and which fields are authoritative on disagreement;
- confidence-level propagation and rejection of mixed or unknown levels;
- transformed parameters, standardized coefficients, categorical contrasts,
  offsets, constrained/fixed parameters, aliased terms, rank deficiency, and
  non-estimable coefficients;
- covariance types, finite-sample degrees of freedom, one- versus two-sided
  values, and whether model adapters may call `conf_int` on the fitted result;
- meta-analysis variance versus standard-error input, effect-scale comparability,
  within-study dependence, zero/negative variances, and duplicated studies;
- tau-squared optimization domain, start values, tolerances, iteration/work
  ceilings, nonconvergence behavior, and whether fallback estimators are
  forbidden or allowed;
- the exact distinction among a study interval, pooled mean-effect interval,
  and prediction interval, including boundary and undefined cases;
- resource limits, numerical tolerances, oracle interpretation, independent
  references, compatibility tier, rendered terminology, and complete typed
  result fields.

No adapter may silently relabel a statistic, replace a covariance estimator,
exponentiate a parameter, infer independence, or switch a meta-analysis method.
Any fallback or transformed-scale path needs its own approved record.

## Coefficient input and adapter contract

- The canonical table input is a Polars dataframe. `term` and `estimate` are
  required; terms are nonempty strings and estimates are finite numeric values.
  Unlike upstream, missing term names are not auto-generated.
- A term identity is either a unique `term` or an approved structured composite
  of explicit columns such as `response`, `component`, and `group`. Duplicate
  final identities fail. Columns are never concatenated heuristically to hide
  collisions.
- Physical source order is retained as provenance. `sort="none"` preserves it;
  ascending and descending sorts are stable and use source position as the tie
  breaker. Row permutations may change source order but never term identity or
  estimate/inference association.
- Null or non-finite estimates fail rather than being silently removed. Optional
  inference fields follow approved all-or-none profiles. A lone interval bound,
  invalid confidence level, negative standard error, p-value outside `[0, 1]`,
  non-finite statistic, or incompatible degrees of freedom fails explicitly.
- Table inputs do not receive inferred p-values, intervals, or standard errors
  merely because enough columns appear to approximate them. Any approved
  derivation records its method and inputs in the result.
- Intercept exclusion uses explicit table metadata or adapter-supplied parameter
  identity. It does not use a broad substring or regular-expression guess.
  Excluded rows remain counted and identified in the audit.
- The first Statsmodels release must support at least one exact, approved,
  single-response linear-model result class with one-dimensional named
  parameters. Additional linear, generalized-linear, discrete, survival,
  mixed, Bayesian, or third-party results are unsupported until separately
  allowlisted and tested.
- An adapter consumes an already fitted result. It never refits, changes
  covariance type, rebuilds a design matrix, mutates the result, imports caller
  data, or relies on class-name duck typing alone.
- The adapter snapshots parameter names, estimates, uncertainty, test identity,
  p-values, confidence level, residual degrees of freedom where applicable,
  observation count, covariance type, model class, Statsmodels version, and
  allowlisted model-summary values. Shape or label mismatch fails.
- The owned coefficient input is immutable and independent of subsequent caller
  dataframe or model-result mutation. Arbitrary model objects, callables,
  formulas, design matrices, and residual arrays are not serialized.

## Meta-analysis contract

- Meta-analysis is explicit; ordinary coefficients are never pooled merely
  because standard errors are present. The caller must declare a common
  estimand, additive effect scale, direction, units, and null/reference value.
- Each retained row represents one independent study estimate with a unique
  study identity, finite effect estimate, and finite strictly positive standard
  error. M5 does not derive effect sizes or sampling variances from raw outcomes.
- Clustered, multilevel, multivariate, network, dependent-effect, and
  participant-level meta-analysis are outside M5. If studies are not reasonably
  independent on the declared scale, the operation must not proceed.
- The approved model must retain every study estimate, sampling variance,
  random-effects weight, normalized weight, and contribution needed to
  reproduce the pooled result. Counts reconcile exactly with exclusions.
- The result separately identifies the pooled mean-effect estimate and interval,
  its test, tau-squared/tau, heterogeneity statistic/degrees of freedom/p-value,
  I-squared, prediction interval or absence reason, estimator identity,
  convergence record, and any boundary warning.
- A zero tau-squared estimate is a boundary result, not an automatic request to
  substitute an unrecorded fixed-effect analysis. Nonconvergence or an
  inadmissible variance fails atomically unless a separately approved fallback
  rule applies.
- Confidence and prediction intervals must state their target and method.
  Undefined quantities serialize as schema-permitted absence with an explicit
  reason; NaN and infinity never appear in public JSON or annotations.
- A pooled marker is a distinct summary layer, not a synthetic study row. Its
  identity, interval, and label derive only from the meta-analysis result.

## Analysis and result contract

- `CoefficientAnalysis` owns an immutable coefficient table and a frozen
  schema-v1 `CoefficientResult`. Analysis modules do not import Matplotlib or
  inspect global plotting state.
- The result records source kind (`table` or an exact adapter identity), source
  and displayed order, complete term identities, estimates, optional inference,
  exclusions, intercept metadata, scale/null semantics, display policy,
  confidence level, model provenance/summary, optional meta-analysis, resource
  limits, compatibility warnings, and software/method identities.
- Display-only input is a first-class result state. It must not contain fake
  uncertainty, tests, p-values, significance, or model-fit claims.
- Inferential records are internally complete for their approved profile.
  Construction rejects contradictory interval, statistic, p-value, confidence,
  covariance, model, study-weight, pooled, or heterogeneity fields.
- All public numbers serialize as finite JSON numbers or explicitly permitted
  absence. Scalar identities use the existing JSON-safe identity rules.
- `analyze_ggcoefstats` performs selection/adaptation and approved computation
  once. `render_ggcoefstats` and repeated rendering never recompute coefficient
  or meta-analytic inference.

## Rendering contract

- The renderer creates a new owned Matplotlib figure with one horizontal term
  axis. Display order is deterministic from the result and reads top to bottom.
- Every retained term has one point. A whisker appears only when a complete
  interval exists. Point position, interval endpoints, term label, statistical
  label, significance state, and any color classification come from the result.
- The reference line uses the typed null value and scale label. M5 does not
  silently change zero to one, exponentiate estimates, or reinterpret a link
  scale for presentation.
- `only_significant=True` changes statistical-label visibility only. It never
  removes points, changes meta-analysis membership, or discards result rows.
- Missing inference yields a documented estimate-only plot without blank or
  fabricated test labels. Statistical labels are unavailable unless their
  approved complete input profile is present.
- The pooled meta-analytic point and its confidence/prediction intervals are
  visibly distinct from study estimates and are semantically identified in the
  axes mapping and result.
- Label collision handling is deterministic and bounded. No random jitter,
  hidden term dropping, or unbounded figure growth is allowed.
- Titles, subtitles, captions, axes labels, colors, point/whisker geometry, and
  visibility controls use explicit typed Python arguments. Arbitrary ggplot
  components, dynamic palette lookup, and unvalidated Matplotlib keyword bags
  are not accepted.

## Extraction and composition contract

- `ggcoefstats` returns the established `StatsPlot` container.
- `extract_stats`, `extract_subtitle`, and `extract_caption` retain coefficient,
  model, and meta-analysis fields without reparsing rendered text.
- `combine_plots` accepts coefficient plots alongside M2–M4 containers and
  preserves the exact `CoefficientResult` object by identity.
- Composition does not refit a model, rerun a meta-analysis, or change term
  order, reference values, confidence levels, or label filtering.

## Required fixture matrix

| Area | Minimum retained cases |
|---|---|
| Display-only tables | one and many terms; 10, 100, and ceiling terms; positive/negative/zero estimates; source/ascending/descending order; stable ties; long/unicode labels; reordered rows |
| Reported inference | t and z profiles if approved; intervals and p-values at boundaries; mixed signs; significant/nonsignificant labels; confidence-level mismatch; incomplete fields; estimate outside interval; non-finite values |
| Identity and exclusions | unique and duplicate terms; structured repeated term names; explicit intercept present/absent/excluded; null term/estimate; empty result after exclusion; exact exclusion audit |
| Statsmodels adapter | approved result class; nonrobust and approved robust covariance; named parameters; confidence levels; intercept metadata; AIC/BIC present/absent; unsupported class; subclass/fake object; shape/name mismatch; caller mutation after analysis |
| Meta-analysis | analytic equal-variance case; unequal variances; null and clear pooled effects; zero and positive heterogeneity; 3, 10, 100, and ceiling studies; dominant study; reordered studies; very small/large valid standard errors; minimum-study and convergence boundaries |
| Meta validation | duplicate study; zero/negative/null/non-finite standard error; non-finite estimate; undeclared or mixed effect scale; unsupported dependence; inconsistent supplied intervals; invalid confidence/null value |
| Renderer | estimate-only and full-inference plots; zero and nonzero reference; interval/no-interval; all/significant/none labels; deterministic order; pooled marker; prediction interval; injection; collision and ceiling behavior; headless SVG |
| Extraction/composition | coefficient and meta containers; mixed M2/M3/M4/M5 dashboard; result identity; JSON schema validation; subtitle/caption extraction |

Oracle agreement alone is insufficient. Every supported deterministic adapter,
coefficient calculation, meta-analysis estimate, interval, test, weight, and
heterogeneity quantity needs an analytic case or implementation/reference
independent of the production calculation. A dependency used in production is
not independent evidence for itself.

## Resource and performance requirements

Unless an approved method record adopts a stricter limit, public defaults are:

- maximum coefficient-table rows or fitted-model parameters: 500;
- maximum meta-analysis studies: 500;
- maximum rendered coefficient/study points: 500;
- maximum rendered statistical labels: 200;
- maximum structured identity columns: 8;
- maximum serialized model-summary fields: 32;
- maximum composed panels remains the package-wide limit of 20.

Each applicable ceiling has an explicit positive override and is serialized in
the result. Overrides cannot bypass numeric representability or package-wide
safety bounds. Oversized inputs fail before analysis or figure creation; there
is no silent term, study, label, interval, or diagnostic sampling.

The retained M5 benchmark must:

- preserve M0, M2, M3, and M4 baselines and investigate any same-host median
  time or peak-allocation regression above 20%;
- record five warmed measurements per phase with fixture/model construction
  outside the measured boundary;
- measure table validation, model adaptation, coefficient analysis,
  meta-analysis, and rendering separately;
- retain coefficient-table workloads at 10, 100, and 500 terms with estimate-
  only, full-inference, label-off, and label-on profiles;
- retain an approved Statsmodels model grid at 10, 100, and 500 parameters when
  safe fixture construction is available;
- retain meta-analysis workloads at 3, 10, 100, and 500 studies with equal and
  unequal sampling variances and zero/positive heterogeneity cases;
- include composition workloads mixing coefficient/meta plots with retained
  earlier families;
- exclude R, Docker, oracle startup, input-frame construction, and model fitting
  from the measured M5 analysis boundary.

## Compatibility requirements

- Audit the pinned implementation, documentation, raw result objects, and
  representative model/tidy/meta paths before declaring an argument supported.
- Preserve `ggcoefstats`, but use snake_case, Polars tables, strict identities,
  typed presentation options, and exact Statsmodels adapter classes.
- Classify each touched input kind, method, and argument as equivalent, adapted,
  experimental, or deferred in `compatibility.md`.
- Treat upstream auto-generated terms, heuristic duplicate-term concatenation,
  silent missing-estimate removal, broad model tidying, and optional package
  installation as behaviors requiring explicit adaptation or deferral.
- Upstream `meta.type="parametric"` is a compatibility reference. Parity may be
  claimed only if the approved estimator, weights, interval/test, heterogeneity,
  and boundary behavior match; otherwise the Python path is labeled adapted.
- Robust and Bayesian coefficient/meta-analysis modes are assigned to M6.
  `bf_message`, Bayesian captions, and robust meta-analysis fail explicitly in
  M5 rather than being accepted and ignored.
- R model objects, easystats/parameters dispatch, ANOVA effect-size tables,
  arbitrary model classes, ellipsis forwarding, R themes, dynamic palette
  lookup, and arbitrary ggplot layers are deferred.
- AIC/BIC are retained only when supplied by an approved adapter and correctly
  named. They are not recomputed from tidy tables or described as universally
  comparable across models.

## Non-goals

- Fitting, selecting, diagnosing, validating, or approving regression models.
- Universal Statsmodels, scikit-learn, PyMC, lifelines, or third-party model
  support; R model objects or formula/tidy-evaluation compatibility.
- Robust or Bayesian coefficients or meta-analysis, Bayes factors, posterior
  intervals, or automatic dependency installation.
- ANOVA effect-size conversion, omnibus F/chi-squared tables, marginal effects,
  standardized coefficients, exponentiated odds/hazard/risk ratios, or automatic
  response/link-scale transformation without a later approved method record.
- Deriving study effect sizes from raw group summaries, correlations, binary
  events, survival data, or individual-participant data.
- Fixed-effect-only, multivariate, multilevel, network, dose-response,
  diagnostic-test, cumulative, or living meta-analysis; meta-regression or
  moderators; publication-bias tests; trim-and-fill; funnel plots or dedicated
  forest-report features beyond the contracted study/pool dot-and-whisker layer.
- Grouped coefficient plotting, interactive/animated plots, arbitrary label
  placement, or general-purpose model-report generation.
- General dataframe interchange or pandas input.
- Pixel-identical R output or final 1.0 API/schema/style stability.

## Verification rubric and acceptance criteria

| Dimension | Severity | Pass threshold |
|---|---|---|
| Statistical identity | Blocking | Approved K1–K4/MA1–MA4 records; correct estimands, scales, nulls, tests, intervals, weights, pooled effects, prediction, and heterogeneity |
| Input integrity | Blocking | Term/study identities, ordering, inference profiles, exclusions, intercepts, estimates, standard errors, and counts reconcile without silent row loss |
| Adapter provenance | Blocking | Exact supported classes only; no refit or covariance change; parameter names/shapes, model metadata, confidence level, and software identity are retained |
| Meta-analysis integrity | Blocking | Independent comparable effects only; approved estimator/convergence/boundaries; all weights and diagnostics reproduce; no silent fallback or method switch |
| Result/render contract | Blocking | Versioned JSON-safe result; every displayed number and classification originates in it; rendering never recomputes inference |
| Presentation semantics | Blocking | Ordering, intercept and significance controls, reference line, missing-inference behavior, pooled layer, and label bounds are explicit and tested |
| Extraction/composition | Blocking | Exact result identity and annotations survive extraction and heterogeneous composition |
| Failure and resource behavior | Blocking | Invalid tables/models/meta inputs/options and ceiling excess fail atomically without partial output or silent sampling |
| Compatibility | Blocking | Every touched upstream behavior and argument has a tested disposition; unsupported keywords and classes are rejected |
| Oracle and independence | Blocking | Pinned-R fixtures verify shared behavior; every deterministic method also has independent evidence at predeclared tolerance |
| Production quality | Blocking | `make check`, `make audit`, `make build`, isolated-wheel smoke, oracle verification, and benchmark verification pass |
| Coverage | Required | Project branch coverage remains at least 75%; every new M5 domain module reaches at least 90% branch coverage |
| Performance | Required | Earlier paths remain within the 20% investigation threshold or have an approved disposition; the complete M5 grid is retained |
| Documentation | Required | Public examples, supported inputs/models, scale/null semantics, meta assumptions, labels, errors, limits, and adaptations match implementation |
| Accountable acceptance | Blocking | All findings are dispositioned; an independent reviewer records a decision; Joshua Myers approves the methods and final M5/`0.3` candidate |

## Verification budget and stopping rules

- Use at most three evidence-changing verification passes per delivery track
  after method approval.
- A pass must add focused implementation/tests, analytic/independent or oracle
  evidence, a retained benchmark, a full production gate, or a meaningfully
  different adversarial review.
- Stop before inferential implementation when any decision applicable to that
  track—K1–K4 for M5A or MA1–MA4 for M5B—lacks Joshua Myers's approval.
- Stop a model adapter on ambiguous class identity, parameter names, coefficient
  scale, covariance/test provenance, degrees of freedom, fitted sample, or
  confidence semantics.
- Stop meta-analysis on ambiguous study independence, effect comparability,
  sampling variance, tau estimator, convergence, small-sample behavior, pooled
  interval/test, prediction interval, heterogeneity, or fallback behavior.
- Stop the milestone on unexplained oracle drift, table/adapter mismatch,
  result/render divergence, unbounded work, package-gate failure, or unapproved
  compatibility claims.
- Record every accepted, corrected, deferred, or rejected finding with severity,
  owner, disposition, and acceptance check. Repeating review against unchanged
  evidence does not consume another pass or establish independence.

## Required closeout artifacts

- `docs/M5_STATISTICAL_METHODS.md`;
- `docs/evidence/M5A_VERIFICATION_LOOP.md`;
- `docs/evidence/M5A_ADVERSARIAL_REVIEW.md`;
- `docs/evidence/M5A_VERIFICATION.md`;
- `docs/evidence/M5A_SIGNOFF.md`;
- `docs/evidence/M5B_VERIFICATION_LOOP.md`;
- `docs/evidence/M5B_ADVERSARIAL_REVIEW.md`;
- `docs/evidence/M5B_VERIFICATION.md`;
- `docs/evidence/M5B_SIGNOFF.md`;
- coefficient/meta-analysis result schema and resource-schema revisions;
- raw and normalized pinned-R coefficient/model/meta fixtures plus updated
  oracle manifest;
- retained M5 benchmark plus updated benchmark verifier;
- updated `docs/compatibility.md`, `docs/CONTRACTS.md`,
  `STATISTICAL_ANALYSIS_PLAN.md`, `README.md`, changelog, and project memory.

Joshua Myers must approve every retained coefficient and meta-analytic method
before its fixtures become acceptance evidence and approve the final release
candidate after all findings are dispositioned. Agent review cannot provide
either approval.

## Track and milestone exit gates

M5A is complete only when strict table input and at least one approved
Statsmodels adapter produce the same coefficient result contract; estimate-only
and inferential profiles, order/exclusion/label behavior, rendering, extraction,
composition, schema, compatibility, oracle, independent-reference, performance,
documentation, and production gates pass; every blocking finding is closed;
and Joshua Myers accepts the M5A candidate.

M5B is complete only when an approved frequentist random-effects model retains
reproducible study weights, pooled inference, prediction behavior,
heterogeneity, convergence, scale/independence metadata, and boundary handling;
the same shared renderer/result and all evidence gates pass; every blocking
finding is closed; and Joshua Myers accepts the M5B candidate.

M5 and `0.3` are complete only when both tracks are complete, every touched
upstream behavior has an explicit compatibility disposition, the combined
candidate passes the production gate from a clean source tree, an independent
review is recorded, and Joshua Myers gives final M5/`0.3` approval.
