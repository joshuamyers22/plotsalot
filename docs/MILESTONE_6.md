# Milestone M6: Robust and Bayesian Methods

- Status: M6A and M6B accepted; M6C passes 1–2 passed, pass 3 next
- Contract date: 2026-09-14
- Target duration: 8–13 weeks
- Product and statistical owner: Joshua Myers
- Implementation and visualization owner: Codex
- Independent-review owner: Joshua Myers for M6A and M6B

## Objective

Add explicit robust and Bayesian analysis modes to the plot families completed
in M2–M5 while preserving plotsalot's owned-data, typed-result, semantic-render,
and reproducible-evidence contracts. M6 must make estimator, prior, interval,
Bayes-factor, randomness, convergence, and computational-budget semantics
inspectable. A plot must never be the only record of a stochastic or robust
analysis.

M6 completes the `0.4` product candidate. It does not make plotsalot a general
Bayesian modeling framework, reproduce every `statsExpressions` method, add
arbitrary model-object dispatch, or establish 1.0 API/schema stability.

This document fixes product scope, decision gates, and acceptance evidence. The
M6A R1–R3/G6 methods and ADR-005/ADR-006 boundaries were approved by Joshua
Myers on 2026-09-14. Joshua Myers approved B1–B6 without revision on
2026-09-15; he subsequently independently reviewed and accepted the completed
M6B candidate on that date. The detailed R4/B5 M6C proposal was prepared on
2026-09-15 in `M6C_STATISTICAL_METHODS.md`; Joshua Myers approved it without
revision on that date, authorizing M6C implementation and fixture construction.

## Entry gate and inherited contracts

M0 through M5 and the `0.3` product gate are complete. Their Polars boundary,
owned immutable inputs, exact missingness/pairing audits, versioned JSON-safe
results, analysis/render separation, semantic layers, extraction, grouping,
composition, resource limits, compatibility tiers, frozen R oracle, independent
references, retained benchmarks, package isolation, and accountable review
remain binding unless an approved M6 decision explicitly supersedes one.

Before each applicable implementation track begins, M6 must:

- create and approve ADR-005 for robust-method and resampling architecture;
- create and approve ADR-006 for Bayesian engine, dependency, and artifact
  architecture;
- approve the applicable R1–R4, B1–B6, and G6 decisions defined below;
- pin every new Python and development-oracle dependency in the authoritative
  lockfiles and pass license/security review;
- establish deterministic work ceilings and failure behavior for every
  stochastic or iterative path; and
- predeclare oracle, independent-reference, simulation, calibration, and
  numerical tolerances before acceptance fixtures are evaluated.

No upstream default, package availability, or implementation convenience counts
as statistical approval.

## Pinned upstream surface audited for scope

M6 is prepared against
`ggstatsplot@7a724cd0ab55668b9d0b2e84b12c711c5be68ac8`, recorded in
`upstream/manifest.json`, and the matching R 4.5.1 oracle environment. The
pinned public signatures expose `type`, `tr`, `bf.prior`, and `bf.message` on
the applicable families:

- `gghistostats` and `ggdotplotstats`: robust/Bayesian one-sample inference and
  selectable centrality;
- `ggscatterstats` and `ggcorrmat`: robust/Bayesian correlation, with matrix
  multiplicity and optional partial-correlation arguments upstream;
- `ggbetweenstats` and `ggwithinstats`: robust/Bayesian omnibus, two-level, and
  pairwise comparisons with trimming/prior controls;
- `ggbarstats` and `ggpiestats`: Bayesian categorical inference; the pinned
  inventory does not advertise a robust categorical mode; and
- `ggcoefstats`: robust and Bayesian random-effects meta-analysis, optional
  Bayes-factor captions, and broad upstream model tidying.

The pinned oracle already locks `statsExpressions==2.1.1`, `WRS2==1.1-7`, and
`BayesFactor==0.9.12-4.8`. Robust/Bayesian meta-analysis packages used by the
upstream optional paths are not currently part of plotsalot's required oracle
lock and cannot become evidence until explicitly pinned and reviewed.

The upstream surface is behavioral evidence, not an automatic Python support
promise. M6 may classify an approved Python method as adapted when its
estimator, prior, evidence measure, interval, engine, or failure policy differs.

## Delivery tracks and release boundary

| Track | Planned allocation | Required surface | Outcome |
|---|---:|---|---|
| M6A: robust continuous analysis | 3–4 weeks | robust univariate, correlation, between/within comparison, matrix, and existing grouped surfaces | Adds bounded, inspectable robust inference without weakening classical modes |
| M6B: Bayesian data analysis | 3–5 weeks | Bayesian univariate, correlation, between/within comparison, categorical, matrix, and existing grouped surfaces | Adds approved Bayesian estimation/evidence with complete prior and computation provenance |
| M6C: coefficient/meta extensions and `0.4` closeout | 2–4 weeks | robust/posterior-summary coefficient input, approved robust/Bayesian meta-analysis, shared rendering/results, cross-mode hardening | Completes the coherent M6 family and `0.4` candidate |

M6A and M6B may be developed and reviewed separately after their own method
gates. M6C depends on the shared result/dependency decisions and the accepted M5
coefficient/meta contract. No individual track alone completes M6 or `0.4`.

Removing a required family, adding nonparametric methods, or changing the
release boundary requires a product-owner-approved contract amendment.

## Product scope

| Family | Required behavior | Track |
|---|---|---|
| Robust one-sample summaries | Approved robust location, uncertainty, test, effect target, tuning metadata, and centrality rendering for histogram and labeled-dot workflows | M6A |
| Robust association | Approved robust correlation estimate, interval/test, tuning metadata, pairwise-complete sample audit, scatter rendering, and correlation-matrix family handling | M6A |
| Robust independent comparison | Approved two-level and multi-level robust inference, effect target, pairwise family, centrality summaries, and atomic grouped execution | M6A |
| Robust repeated comparison | Explicit-subject robust paired/multi-condition inference over an approved missingness population, pairwise family, centrality summaries, and atomic grouped execution | M6A |
| Bayesian one-sample summaries | Approved likelihood/prior, posterior location/effect summaries, credible interval, evidence statement, and centrality rendering | M6B |
| Bayesian association | Approved correlation model/prior, posterior/evidence result, interval, matrix family semantics, and scatter/matrix rendering | M6B |
| Bayesian independent/repeated comparison | Approved two-level and multi-level models, priors, posterior contrasts, evidence/family policy, explicit repeated identity, and centrality summaries | M6B |
| Bayesian categorical analysis | Approved one-way and independent association models; paired analysis only if its estimand and evidence/estimation asymmetry are explicitly approved | M6B |
| Robust/Bayesian coefficient summaries | Strict robust and posterior-summary table profiles and, only if separately approved, narrow exact fitted-result adapters; no arbitrary posterior/model dispatch | M6C |
| Robust meta-analysis | One approved aggregate-data robust random-effects model with complete convergence, influence, scale, weight, interval, and fallback provenance | M6C |
| Bayesian meta-analysis | One approved aggregate-data Bayesian random-effects model with explicit likelihood/prior, posterior heterogeneity, pooled/prediction targets, diagnostics, and computation provenance | M6C |
| Shared presentation | Existing plot functions select modes explicitly and render only values retained in typed results; captions distinguish frequentist, robust, and Bayesian semantics | All |
| Extraction, grouping, composition | Exact result identity, annotations, randomness/provenance, and atomic failure survive existing public containers | All |

An approved mode must cover both analysis and its existing semantic renderer.
M6 does not add a second plotting API or a generic `fit_bayesian_model`
function.

## Deliverables and acceptance evidence

| Deliverable | Acceptance evidence | Track | Initial status |
|---|---|---|---|
| Pinned-surface audit | Exact applicable signatures, backend calls, result fields, dependency versions, and deliberate adaptations recorded | All | Complete for M6A entry |
| ADR-005 robust architecture | Approved estimator/resampling/dependency/fallback policy | M6A/M6C | Accepted 2026-09-14 |
| ADR-006 Bayesian architecture | Approved engine/optional-extra/RNG/artifact/diagnostic policy | M6B/M6C | Accepted 2026-09-14; M6B engine fixed by approved B6 on 2026-09-15 |
| M6 statistical method specification | Approved R1–R4, B1–B6, and G6 decisions with estimands and failure behavior | All | R1–R3/G6 approved 2026-09-14; B1–B6 and R4/B5 M6C approved 2026-09-15 |
| Robust analysis contracts | Typed, immutable robust analyses for every M6A family with analytic/independent evidence | M6A | Technical candidate verified |
| Bayesian analysis contracts | Typed Bayesian analyses for every M6B family with prior/computation provenance and calibration evidence | M6B | Complete and accepted 2026-09-15 |
| Coefficient/meta extensions | Strict robust/posterior coefficient summaries plus approved robust/Bayesian aggregate meta-analysis | M6C | Passes 1–2 verified; provisional zero-heterogeneity calibration disposition requires M7 review |
| Result schemas | Versioned JSON-safe robust, posterior, evidence, diagnostic, warning, audit, and limit records | All | M6A/M6B verified; M6C coefficient and aggregate v2/v3 variants implemented |
| Semantic renderers | Layer/injection tests prove every displayed estimate, interval, evidence label, diagnostic, and centrality value comes from the result | All | M6A and M6B verified |
| Grouping/extraction/composition | Atomic grouped execution and exact result identity across classical/robust/Bayesian mixed dashboards | All | M6A/M6B verified; M6C has no grouped coefficient surface |
| Oracle and independent evidence | Raw pinned-R objects, normalized fields, independent calculations, simulation/calibration summaries, and hashed manifest | All | M6A/M6B verified; M6C pass-2 oracle passes and its retained boundary finding has a provisional owner disposition |
| Performance and work baselines | Phase-separated robust and Bayesian grids with time, memory, draws/evaluations, and ceilings | All | M6A/M6B verified; M6C planned |
| Compatibility disposition | Every touched `type`, tuning, prior, evidence, model, and meta argument classified and tested | All | M6A/M6B complete; M6C entry disposition approved |
| Public documentation | Supported modes, assumptions, priors, diagnostics, reproducibility, limits, errors, adaptations, and examples match implementation | All | M6A/M6B complete; M6C entry contract documented |
| Production gate | Check, audit, build, isolated-wheel/core-import and Bayesian-extra smoke, oracle, benchmark, and reproducibility verification pass | All | M6A and M6B verified |
| Review and sign-off | Verification loops, adversarial findings, independent review, Joshua Myers track acceptance, and final M6/`0.4` approval | All | M6A accepted 2026-09-14; M6B accepted 2026-09-15; M6C/final gate blocking |

## Required statistical and architecture decisions

The M6 method specification must name and obtain approval for:

- R1: one-sample robust location/effect estimands, test statistic, uncertainty,
  trimming/tuning value, small-sample rule, and centrality target;
- R2: robust association estimator, interval/test, contamination target,
  pairwise missingness, matrix multiplicity, and partial-correlation exclusion or
  inclusion;
- R3: independent and repeated robust omnibus/two-level/pairwise estimators,
  effect targets, subject population, trimming, bootstrap/resampling, family
  correction, and small/unbalanced sample behavior;
- R4: robust coefficient-summary meaning and robust meta-analysis likelihood or
  estimating model, heterogeneity target, weights/influence, convergence,
  tuning, and fallback policy;
- B1: common Bayesian reporting vocabulary, posterior estimators, credible-
  interval definition, evidence/Bayes-factor orientation, thresholds, prior
  provenance, and conditions under which no evidence label is displayed;
- B2: one-sample and association likelihoods, priors, nulls, effect targets,
  centrality summaries, and matrix family semantics;
- B3: independent and repeated comparison likelihoods, priors, subject/group
  structure, omnibus and pairwise targets, contrasts, and multiplicity or joint-
  posterior policy;
- B4: one-way, independent, and any paired categorical likelihoods, sampling
  plan, fixed margins, prior concentration, effect/association target, and
  structural/sparse-cell behavior;
- B5: coefficient posterior-summary protocol and Bayesian meta-analysis
  likelihood, effect scale, pooled/prediction/heterogeneity targets, priors,
  dependence, and small-study behavior;
- B6: inference engine, approximation/sampling algorithm, chains, warmup,
  retained draws, seed/RNG ownership, parallel streams, diagnostic thresholds,
  retry/fallback prohibition, and result/artifact retention; and
- G6: grouped family identity, correction/evidence scope, seed derivation,
  partial-failure behavior, work allocation, progress/cancellation semantics,
  and label/artist limits.

Approval for each retained method must also cover:

- population, observation unit, estimand, hypothesis/evidence direction,
  alternative, units, transformations, and meaningful null/reference value;
- input schema, level/subject/study identity, missingness, ties, duplicate rows,
  zero variation, finite-value rules, minimum effective sample, and exclusions;
- robustness definition and contamination being guarded against; “robust” may
  not be used as an unexplained label;
- interval target and level, sidedness, finite-sample correction, bootstrap
  type if any, Monte Carlo error, and behavior when bounds are undefined;
- exact prior family/parameterization, units/scaling, properness, sensitivity
  set, likelihood support, and whether defaults vary by data scale;
- Bayes-factor numerator/denominator, null width or point hypothesis, sampling
  plan, logarithm/base, direction, display threshold, and overflow handling;
- exact centrality target for each mode; renderer labels may not switch among
  trimmed mean, posterior mean, median, or MAP without retained provenance;
- numerical algorithms, tolerances, maximum evaluations/draws, diagnostic
  thresholds, warning/failure policy, and whether any fallback is allowed;
- exact optional dependency set, versions, licenses, platform support, import
  isolation, and behavior when extras are absent;
- oracle interpretation, independent references, calibration design,
  tolerances, compatibility tier, and complete typed-result fields; and
- default and hard resource ceilings for rows, variables, groups, hypotheses,
  resamples, chains, draws, evaluations, wall time, memory proxies, and artists.

No mode may silently change estimators, priors, evidence direction, interval
targets, covariance, trimming, sampling plans, or engines. A fallback requires
its own approved method identity and must be visible in the result.

## Robust analysis contract

- Robust mode is selected explicitly. Classical methods never switch to a
  robust estimator because of a diagnostic, outlier, failed assumption, or
  numerical problem.
- Each robust result names its location/association/effect estimand, estimator,
  tuning or trimming value, test and reference distribution, uncertainty
  method, effective sample, exclusions, and any resampling computation.
- Trimming or Winsorization acts only after the approved missingness boundary.
  The result records the original retained count, effective count, tail counts,
  and whether interpolation or weighting was used.
- Robust procedures do not silently delete observations identified as outliers.
  Any estimator-specific downweighting or influence value is method output, not
  a changed analysis population.
- Repeated analyses retain explicit subject keys. Any subject exclusion occurs
  before robust calculation and is shared by analysis and rendering.
- Pairwise and matrix work retains complete family membership even when only
  selected annotations are displayed. Unsupported or undefined members fail
  according to the approved atomicity rule; they are not silently omitted.
- If an approved method uses bootstrap or other resampling, its seed/RNG,
  resample count, interval construction, successful/failed replicate counts,
  work ceiling, and Monte Carlo qualification are retained.
- Nonconvergence, insufficient effective sample, degenerate trimmed scale,
  singular estimating equations, invalid bootstrap distribution, or ceiling
  exhaustion raises a typed error before a partial plot is returned unless an
  explicitly approved result state defines a non-inferential display.

## Bayesian analysis contract

- Bayesian mode is selected explicitly. It never appears as an automatic
  supplement to a classical or robust result unless the caller requests an
  independently approved combined-reporting surface.
- Every result identifies the likelihood, link/parameterization where relevant,
  complete prior and hyperprior parameters, posterior target, credible interval
  method/level, evidence method, engine/version, and computation settings.
- Bayes factors identify hypotheses, orientation, scale, and whether the stored
  value is raw, logarithmic, or transformed. Captions may not say only “BF” or
  use qualitative evidence adjectives without the approved numeric rule.
- Posterior point labels explicitly distinguish posterior mean, median, MAP, or
  another approved target. A frequentist confidence interval is never relabeled
  as a credible interval, and a posterior interval is never presented as a
  prediction interval without the required predictive target.
- If analytic or deterministic quadrature is approved, the result retains its
  algorithm, tolerances, evaluation count, and convergence checks. If sampling
  is approved, it retains chains, warmup, draws, thinning if any, RNG identity,
  seed derivation, parallelism, acceptance/sampler diagnostics, and warnings.
- At minimum, sampling-based paths must assess approved R-hat, bulk/tail ESS,
  Monte Carlo error, divergent transitions or engine-equivalent pathologies,
  and chain completeness. Threshold failures cannot be hidden by rounding or
  by returning only a plot.
- Full posterior draws are not embedded in default JSON results. Results retain
  sufficient summaries, diagnostics, settings, and an optional caller-managed
  artifact fingerprint. Plotsalot does not persist draws or caller data unless a
  separate explicit API and storage contract are approved.
- Prior predictive checks, posterior predictive checks, and prior sensitivity
  are required where specified by B1–B6. They must use development/validation
  evidence distinct from the locked final oracle cases.
- Same-seed claims are limited to the exact approved engine/platform contract.
  Cross-language or cross-platform bit identity is not promised. Statistical
  agreement uses approved Monte Carlo uncertainty and calibration bounds.

## Bayesian dependency and runtime contract

- Core installation and import must remain usable without Bayesian extras. A
  missing optional extra fails only when a Bayesian path needing it is invoked,
  with a stable actionable error.
- ADR-006 decides whether M6 uses analytic SciPy/NumPy implementations, a pinned
  PyMC/ArviZ extra, another engine, or a narrow combination. The contract may
  not be satisfied by an undeclared transitive dependency.
- Optional dependencies are locked, audited, license-checked, imported lazily,
  and exercised on every supported Python/platform combination before release.
- Importing plotsalot or a Bayesian module performs no network, compilation,
  sampling, global warning-filter, thread-count, backend, or random-state side
  effect.
- Runtime analysis performs no network access and downloads no model or data.
  R, Docker, and the upstream packages remain development-only oracle tools.
- Thread/process behavior, BLAS and sampler parallelism, oversubscription,
  cancellation, progress callbacks, and deterministic seed-stream derivation
  are explicit. Hidden unbounded parallel work is prohibited.
- Wheel/sdist smoke tests cover both a minimal core environment and every
  released Bayesian extra. Unsupported platforms fail at installation or mode
  selection, not during an opaque long-running computation.

## Data, grouping, and result contracts

- Existing classical input selection and audit objects remain the source of
  truth unless a method requires an approved stricter boundary. Robust and
  Bayesian modes may not independently select a different displayed sample.
- Analysis inputs are copied into owned, immutable numerical structures before
  computation. Caller mutation cannot change a retained result or render.
- Grouped calls preflight all group identities, samples, method options,
  computation budgets, and deterministic child seeds before analysis. One
  invalid or failed group returns no partial grouped result.
- A grouped root seed is expanded by a stable documented algorithm using typed
  scalar group identity, not iteration timing, Python hash randomization, or
  worker completion order.
- Result schemas distinguish classical, robust, and Bayesian variants without
  ambiguous optional-field bags. Common estimate/interval concepts use shared
  typed components only when their targets and semantics truly match.
- Robust results retain estimator/tuning/effective-sample/resampling metadata.
  Bayesian results retain prior/likelihood/posterior/evidence/computation and
  diagnostic metadata. Both retain method and software versions, limits,
  warnings, and sample audits.
- All scalar result fields are finite and JSON-safe. Undefined quantities use a
  typed absence reason rather than NaN, infinity, an empty string, or a
  misleading numeric placeholder.
- Constructor and schema tests reject contradictory mode, target, interval,
  prior, evidence, diagnostic, seed, family, sample, and limit records.

## Rendering and annotation contract

- Rendering consumes a completed typed analysis/result and never fits, samples,
  resamples, recalculates evidence, or changes random state.
- Every rendered estimate, interval, null/reference line, effect, centrality,
  evidence value, warning, diagnostic, and classification maps to a retained
  result field and a named semantic artist/layer.
- Subtitles/captions name the method family and interval/evidence target. Robust
  tuning and consequential Bayesian prior/diagnostic warnings remain available
  through extraction even if concise visual text is requested.
- Presentation filtering affects labels only. It cannot change samples,
  hypotheses, posterior draws, model fitting, adjustment families, pooled
  estimates, or evidence calculations.
- Failed Bayesian diagnostics may not be styled as an ordinary accepted result.
  The approved policy must either fail atomically or display a prominent typed
  qualification derived from the result.
- Existing extraction functions return the exact result object. Composition
  preserves each panel's mode, annotations, diagnostics, and result identity in
  mixed classical/robust/Bayesian dashboards.
- Labels, intervals, paths, matrix cells, posterior summaries, and composed
  panels remain bounded by explicit default and hard artist ceilings.

## Oracle, independent reference, and calibration evidence

- The R oracle retains raw pinned ggstatsplot/statsExpressions objects and
  normalized values for every supported robust/Bayesian family. Oracle fixtures
  are generated only after the corresponding method decision is approved.
- Exact upstream dependency revisions, optional packages, seeds, computation
  settings, warnings, and session identity are stored in the oracle manifest.
- Upstream agreement is never the sole evidence. Deterministic robust methods
  require analytic or independently implemented reference calculations.
- Bayesian analytic/conjugate paths require exact or high-precision references.
  Sampling paths require independently generated reference summaries plus
  simulation-based calibration, coverage, or other method-appropriate aggregate
  evidence with predeclared uncertainty bounds.
- Bayes-factor tests include reciprocal/orientation checks, null and alternative
  fixtures, prior-scale sensitivity, extreme finite values, and independent
  evidence calculations where practicable.
- Robust tests include location/scale equivariance, row/label permutations,
  clean-data limiting behavior, controlled contamination, tuning boundaries,
  small/effective sample boundaries, and independent calculations.
- Development fixtures may tune algorithms and tolerances. Locked validation
  and final fixtures are not used to select methods, priors, convergence rules,
  or thresholds.
- Oracle and evidence manifests hash inputs, raw outputs, normalized outputs,
  engine/lock identity, and aggregate calibration artifacts. Drift fails the
  default verification gate.

## Required test matrix

| Area | Required cases |
|---|---|
| Robust one-sample | symmetric/asymmetric clean samples; ties; contamination; trim/tuning boundaries; small effective sample; null/non-finite/zero-scale; location/scale equivariance |
| Robust association | positive/negative/null association; contamination in each axis; pairwise nulls; ties; near-constant variables; row/column permutation; matrix adjustment family; unsupported partial mode |
| Robust comparisons | two/many groups; balanced/unbalanced; repeated subjects; ties; contaminated group; empty trimmed tail; pairwise family; grouped identity; resampling exhaustion/failure if applicable |
| Bayesian one-sample/association | prior-only and concentrated-likelihood behavior; null/alternative cases; prior-scale sensitivity; BF orientation; credible interval target; seed replay; diagnostic pass/fail |
| Bayesian comparisons | two/many groups; balanced/unbalanced; repeated identity; contrast orientation; joint/pairwise evidence policy; sparse group; prior sensitivity; chain/evaluation failure |
| Bayesian categorical | one-way/independent and any approved paired path; zero/sparse cells; count-weighted parity; ratio keying; sampling-plan/prior changes; category permutation; structural zeros |
| Coefficient summaries | posterior table profiles; parameter/scale identity; credible-versus-confidence interval rejection; model/draw artifact mutation; unsupported adapter/fake object; transformed parameters |
| Robust meta-analysis | zero/positive/high heterogeneity; influential study; contamination; 3/5/500 studies; scale equivariance; convergence/boundary; no fallback; pooled versus prediction identity |
| Bayesian meta-analysis | small/large study counts; weak/strong heterogeneity; prior sensitivity; pooled/prediction distinction; study dependence rejection; seed replay; diagnostics; ceiling/cancellation |
| Results/renderers | JSON schema; constructor mutations; displayed-field injection; typed absence; evidence orientation; warning visibility; extraction identity; mixed composition |
| Resources/dependencies | defaults/hard overrides; preflight failure; missing extra; minimal core import; offline wheel; unsupported platform; parallel budget; no network/R runtime |

Tests must assert full-precision structured results and semantic artists, not
rounded subtitle strings or pixel snapshots alone.

## Performance and resource contract

The retained M6 benchmark must separate selection, deterministic analysis,
resampling/sampling, summarization, and rendering. It must report five warmed
measurements where meaningful, median elapsed time, incremental Python peak
allocation, and algorithmic work counters.

Required grids include:

- robust univariate/scatter workloads at 10K, 100K, and 1M rows;
- robust comparison workloads across row, group, subject, and condition limits;
- robust/Bayesian correlation matrices at 10, 25, and 50 variables within
  approved computational ceilings;
- Bayesian analytic or sampled workloads across representative sample sizes,
  chain/draw settings, group counts, and both diagnostic-pass/failure cases;
- coefficient/meta workloads through approved term/study ceilings; and
- grouped and composed mixed-mode workloads at their approved panel/group
  ceilings.

M6 must define finite defaults and hard overrides before implementation. A
budget is checked before expensive work and retained in the result. Exhaustion
raises a stable typed error; it never silently reduces draws, resamples,
hypotheses, groups, variables, studies, or labels.

Existing classical paths remain in the benchmark and may not regress by more
than 20% in median time or peak allocation without an approved investigation
and disposition. Bayesian cold-start/import costs and steady-state analysis are
reported separately. Performance never substitutes for diagnostic adequacy.

## Compatibility and failure policy

- Each touched upstream argument and method is marked equivalent, adapted,
  experimental, deferred, or rejected in `compatibility.md`.
- Python uses explicit string-literal mode values and named keyword allowlists.
  Unknown values and upstream ellipsis-style options fail immediately.
- `bf_prior`, trimming/tuning, confidence/credible level, evidence display,
  centrality selection, sampler settings, and computation limits are accepted
  only when defined by the approved method record.
- Missing optional dependencies, invalid prior support, improper posterior,
  non-identification, nonconvergence, failed diagnostics, insufficient effective
  samples, invalid evidence, and resource exhaustion have distinct stable errors.
- No robust/Bayesian failure triggers a classical result; no sampling failure
  triggers an unapproved approximation; no Bayesian failure is downgraded to a
  missing caption.
- Warnings are typed result data with stable codes and conditions. User-facing
  messages remain concise and never claim model validity or practical meaning.

## Explicit exclusions and deferrals

The following are outside M6 unless this contract is amended and the applicable
method decisions are approved:

- nonparametric rank tests and nonparametric correlation as a general product
  family;
- generic permutation, bootstrap, posterior-predictive, or simulation APIs
  beyond resampling required by a specifically approved M6 method;
- automatic method selection based on normality, outliers, diagnostics, sample
  size, Bayes factors, or convergence;
- automatic outlier removal, imputation, winsorization, transformations, or
  prior scaling not fixed by the approved method;
- arbitrary PyMC/Stan/JAX model execution, formula parsing, user model code,
  custom likelihoods/priors, or general Bayesian regression fitting;
- broad fitted-model/posterior object dispatch, R-model compatibility, and
  arbitrary third-party adapters;
- multilevel, multivariate, network, dependent-effect, publication-bias,
  selection-model, or participant-level meta-analysis;
- partial correlation, covariate-adjusted comparison, mixed-effects,
  time-series, survival, causal, predictive, or model-selection workflows;
- robust categorical methods, because the pinned upstream inventory has no such
  advertised mode;
- long-term posterior storage, databases, remote services, telemetry, hosted
  sampling, or network-dependent runtime behavior;
- arbitrary Matplotlib/ggplot layer forwarding, interactive/animated output,
  pixel identity, or 1.0 schema/style stability; and
- automatic interpretation, evidence-strength claims beyond an approved rule,
  scientific recommendations, or claims of upstream endorsement.

Deferred input values must be absent from public signatures or rejected. They
are never accepted and ignored.

## Verification rubric and acceptance criteria

| Dimension | Severity | Pass threshold |
|---|---|---|
| Statistical identity | Blocking | Every robust/Bayesian estimate, hypothesis, interval, evidence measure, prior, and diagnostic matches an approved method record |
| Sample and family integrity | Blocking | Displayed/analyzed samples, subjects, groups, categories, studies, hypotheses, and grouped families reconcile without silent loss |
| Randomness and reproducibility | Blocking | RNG ownership, seeds/streams, draws/resamples, engine settings, work counts, and reproducibility limits are retained and tested |
| Convergence and diagnostics | Blocking | Approved numerical/sampler thresholds pass; failures are typed and cannot return an ordinary successful result |
| Result/render contract | Blocking | Versioned JSON-safe results contain every displayed value/classification; rendering performs no analysis or random work |
| Dependency/runtime isolation | Blocking | Core works without extras; extras are pinned/audited/lazy/offline; imports have no I/O, compilation, global-state, or network side effects |
| Grouping/composition | Blocking | Atomic grouped results and mixed-mode composition preserve identity, provenance, warnings, diagnostics, and deterministic seed mapping |
| Failure and resource behavior | Blocking | Invalid data/options/priors/diagnostics and ceiling exhaustion fail before partial output or silent method/work reduction |
| Oracle and independence | Blocking | Pinned-R evidence plus analytic/independent or calibrated simulation evidence passes predeclared tolerances |
| Compatibility | Blocking | Every touched upstream mode/argument/backend behavior has an explicit tested disposition |
| Production quality | Blocking | `make check`, `make audit`, `make build`, minimal and extra isolated-wheel smoke, oracle, benchmark, and reproducibility gates pass |
| Coverage | Required | Project branch coverage remains at least 75%; every new M6 domain module reaches at least 90% branch coverage |
| Performance | Required | Earlier paths remain within the 20% threshold or have an approved disposition; all M6 workloads retain time/memory/work evidence |
| Documentation | Required | Public examples, priors, diagnostics, semantics, limitations, errors, extras, and compatibility claims match implementation |
| Accountable acceptance | Blocking | All findings are dispositioned; an independent reviewer records each track decision; Joshua Myers approves methods and final M6/`0.4` candidate |

## Verification budget and stopping rules

- Use at most three evidence-changing verification passes per delivery track
  after that track's statistical and architecture decisions are approved.
- A pass must add focused implementation/tests, an independent calculation,
  oracle/calibration evidence, retained performance/work evidence, a production
  gate, fault injection, dependency-isolation evidence, or a meaningfully
  different adversarial review.
- Stop before inferential implementation when any applicable R1–R4, B1–B6, G6,
  ADR-005, or ADR-006 decision is unapproved.
- Stop on ambiguous estimand, prior parameterization, evidence orientation,
  interval target, population, trimming, resampling, seed mapping, diagnostic,
  fallback, dependency, or resource semantics.
- Stop stochastic work before launch when the requested work exceeds approved
  ceilings or deterministic child-seed allocation cannot be established.
- Stop the track on unexplained oracle drift, calibration failure, diagnostic
  failure, result/render divergence, silent fallback, classical regression,
  package-isolation failure, or an unresolved blocking finding.
- Repeating review against unchanged evidence does not consume another pass or
  establish independence. Agent self-review cannot supply statistical,
  dependency-risk, or release approval.

## Required closeout artifacts

- `docs/adr/ADR-005-robust-method-architecture.md`;
- `docs/adr/ADR-006-bayesian-engine-architecture.md`;
- `docs/M6_STATISTICAL_METHODS.md`;
- `docs/M6C_STATISTICAL_METHODS.md`;
- `docs/evidence/M6A_VERIFICATION_LOOP.md`;
- `docs/evidence/M6A_ADVERSARIAL_REVIEW.md`;
- `docs/evidence/M6A_VERIFICATION.md`;
- `docs/evidence/M6A_SIGNOFF.md`;
- `docs/evidence/M6B_VERIFICATION_LOOP.md`;
- `docs/evidence/M6B_ADVERSARIAL_REVIEW.md`;
- `docs/evidence/M6B_VERIFICATION.md`;
- `docs/evidence/M6B_SIGNOFF.md`;
- `docs/evidence/M6C_METHOD_AUDIT.md`;
- `docs/evidence/M6C_VERIFICATION_LOOP.md`;
- `docs/evidence/M6C_ADVERSARIAL_REVIEW.md`;
- `docs/evidence/M6C_VERIFICATION.md`;
- `docs/evidence/M6C_SIGNOFF.md`;
- robust/Bayesian result-schema revisions and stable typed error/warning codes;
- raw and normalized pinned-R fixtures plus independent/calibration artifacts
  and the updated oracle manifest;
- retained M6 benchmark and reproducibility/work verifier;
- minimal-core and every-extra isolated-wheel smoke evidence;
- updated `docs/compatibility.md`, `docs/CONTRACTS.md`,
  `STATISTICAL_ANALYSIS_PLAN.md`, `README.md`, changelog, and project memory.

Joshua Myers must approve each retained method and architecture decision before
its acceptance fixtures become normative and approve the final M6/`0.4`
candidate after all findings are dispositioned. An implementation agent cannot
provide those approvals.

## Track and milestone exit gates

M6A is complete only when every retained robust continuous family has approved
estimands/tuning/failure rules, immutable analysis/results, semantic rendering,
grouped behavior where already public, independent/oracle evidence, resource
limits, benchmarks, documentation, production gates, independent review, and
Joshua Myers's acceptance.

M6B is complete only when every retained Bayesian data-analysis family has
approved likelihoods/priors/posterior/evidence targets, engine/RNG/diagnostic
contracts, immutable typed results, semantic rendering, atomic grouping,
independent/calibration/oracle evidence, limits, benchmarks, dependency
isolation, documentation, independent review, and Joshua Myers's acceptance.

M6C is complete only when strict robust/posterior coefficient summaries and the
approved robust/Bayesian aggregate meta-analysis paths share the M5
coefficient-result/render contract, retain complete convergence/diagnostic/work
provenance, pass cross-mode and optional-extra gates, close every blocking
finding, receive independent review, and are accepted by Joshua Myers.

M6 and `0.4` are complete only when M6A–M6C are complete, all touched upstream
behaviors and dependencies are dispositioned, the combined candidate passes the
full production/reproducibility gate from a clean source tree, and Joshua Myers
gives final M6/`0.4` approval.

## Immediate next gate

M6A passed its technical, independent-review, and product/statistical gates and
was accepted by Joshua Myers on 2026-09-14. Joshua Myers approved B1–B6,
independently reviewed the three-pass M6B candidate, and accepted M6B on
2026-09-15. Its evidence is recorded in
`M6B_STATISTICAL_METHODS.md`, `evidence/M6B_METHOD_AUDIT.md`,
`evidence/M6B_SIGNOFF.md`, and `evidence/M6B_VERIFICATION_LOOP.md`. The R4/B5
M6C proposal, entry audit, sign-off ledger, and pass-zero verification
loop are now prepared. Joshua Myers approved every R4/B5 entry decision without
revision on 2026-09-15. M6C implementation pass 1 passed its technical gate on
that date. Pass 2 implemented the robust and Bayesian aggregate meta-analysis
engines and passed its formula, oracle, fault, schema, contamination, and
Bayesian calibration checks. After retained conservative findings at `k=10`
and `k=50` with generating `tau=0`, Joshua Myers provisionally approved the
one-sided conservative rule only when `k<20` or `tau=0`; `k>=20, tau>0` retains
the two-sided rule. M7 must revisit that exception before 1.0. The next gate is
M6C pass 3 shared rendering, integration, benchmark, documentation, adversarial,
and production evidence. Candidate acceptance and final M6/`0.4` acceptance
remain open.
