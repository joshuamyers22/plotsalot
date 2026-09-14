# Milestone M4: Categorical Bar and Pie Families

- Status: Release candidate ready; independent review and final acceptance pending
- Contract date: 2026-09-14
- Target duration: 3–4 weeks
- Product and statistical owner: Joshua Myers
- Implementation and visualization owner: Codex
- Independent-review owner: Unassigned

## Objective

Add inspectable classical categorical analyses and two semantic renderers over
one shared result: `ggbarstats` for normalized stacked bars and `ggpiestats` for
faceted pies. Support raw observations and aggregate frequency tables, one-way
goodness-of-fit, two-way independent association, paired categorical designs,
follow-up families where applicable, and atomic grouped execution.

M4 completes the categorical portion of the `0.2` product gate. Together with
the within-subject work completed in M3, an accepted M4 release candidate closes
`0.2`; it does not imply 1.0 API or schema stability.

This contract fixes scope and acceptance evidence. Joshua Myers approved the
separate M4 statistical method record on 2026-09-14.

## Entry gate and inherited contracts

M0 through M3 are complete. Their Polars boundary, owned immutable analysis
sample, typed result, semantic renderer, extraction, atomic grouping, resource,
compatibility, oracle, benchmark, package-isolation, and accountable-review
contracts remain in force unless an approved M4 decision explicitly supersedes
one.

Before implementation begins, the M4 method specification must resolve the
goodness-of-fit, independent-table, paired-table, pairwise, proportion-test,
sparse-cell, expected-count, effect-size, interval, count-weight, and
multiplicity decisions below. Upstream behavior is evidence, not automatic
approval.

## Pinned upstream surface audited for scope

The scope was prepared against
`ggstatsplot@7a724cd0ab55668b9d0b2e84b12c711c5be68ac8` and its pinned
statsExpressions backend. The four public surfaces are:

- `ggbarstats(data, x, y=None, counts=None, type="parametric", paired=False,
  ...)`;
- `ggpiestats(data, x, y=None, counts=None, type="parametric", paired=False,
  ...)`;
- `grouped_ggbarstats(data, ..., grouping.var, ...)`;
- `grouped_ggpiestats(data, ..., grouping.var, ...)`.

The pinned API also exposes result subtitles, count/percentage labels,
one-sample proportion labels for two-way plots, expected ratios, alternatives,
confidence levels, Holm adjustment, titles/captions/legends, palettes, and
arbitrary ggplot components. These are inputs to compatibility disposition;
they are not all automatically supported in Python.

## Delivery tracks and release boundary

| Track | Planned allocation | Required public surfaces | Outcome |
|---|---:|---|---|
| M4A: categorical core and bars | 2 weeks | shared categorical data/analysis/result contracts, `ggbarstats`, `grouped_ggbarstats` | Locks statistical and sample semantics in the recommended categorical renderer |
| M4B: pies and `0.2` closeout | 1–2 weeks | `ggpiestats`, `grouped_ggpiestats`, cross-renderer parity, final evidence | Adds the alternate renderer and completes the `0.2` candidate |

M4A may be reviewed separately but does not complete M4 or `0.2`. M4 is
complete only when both renderers and grouped variants consume the same approved
categorical result contract and the combined release candidate passes every
gate below.

## Product scope

| Family | Required behavior | Track |
|---|---|---|
| Raw categorical observations | One row per observed unit with required `x`, optional `y`, stable category identity/order, and auditable null removal | M4A |
| Aggregate frequency input | Optional named `counts` column with validated integer weights, exact weighted totals, and no physical row expansion | M4A |
| One-way categorical design | With `y=None`, compare observed `x` frequencies with an approved default or caller-supplied expected ratio and retain the full observed/expected table | M4A |
| Independent two-way design | With `y` supplied and `paired=False`, analyze the complete `x` by `y` table with an approved omnibus association test, effect, interval, and cell diagnostics | M4A |
| Paired two-way design | With `paired=True`, analyze row-aligned or count-weighted paired outcomes under an approved square-table method; reject ambiguous/nonconforming designs | M4A |
| Follow-up comparisons | For eligible independent tables, retain a deterministic, complete pairwise family over `x` levels with raw/adjusted probabilities and explicit family scope | M4A |
| Stratum proportion tests | When enabled for eligible two-way designs, retain the approved per-`y` proportion hypotheses and corrections separately from omnibus and pairwise families | M4A |
| Bar renderer | One-way normalized stacked bar or two-way normalized bars with count/percentage labels, totals, statistical annotations, stable colors, and accessible axes | M4A |
| Pie renderer | One-way pie or deterministic per-`y` facets using the identical analysis result, count/percentage labels, totals, statistical annotations, and stable colors | M4B |
| Grouped categorical plots | Stable outer-group execution, nested audits, separately scoped test families, and atomic failure for bar and pie variants | Both |
| Extraction and composition | Existing extraction functions and `combine_plots` accept all four new containers without losing result or group identity | Both |

Every public surface must expose at least one approved classical method.
`ggbarstats` and `ggpiestats` must not develop separate statistical
implementations. Removing a surface or one of the three design families above
requires a product-owner-approved contract amendment; individual optional
arguments may be deferred only with an explicit compatibility disposition.

## Deliverables and acceptance evidence

| Deliverable | Acceptance evidence | Track | Status |
|---|---|---|---|
| Approved method specification | Reviewed C1–C5/G5 records covering all retained designs and follow-up families | Both | Complete |
| Categorical data boundary | Raw/count-weighted selection, level order, null and zero handling, immutable table, and reconciling audit tests | M4A | Implemented; gate pending |
| Shared categorical analysis | One-way, independent, paired, pairwise, and proportion-test paths use one typed analysis contract | M4A | Implemented; gate pending |
| Versioned results and schemas | JSON-safe table, cell, test, effect, interval, family, audit, warning, and limit records | M4A | Implemented; gate pending |
| Semantic bar renderer | Layer and injection tests prove every count, percentage, total, interval, and statistical label comes from the typed result | M4A | Implemented; gate pending |
| Semantic pie renderer | Cross-renderer result identity plus wedge/facet/label/zero-category tests | M4B | Implemented; gate pending |
| Atomic grouped variants | Stable identities/order, nested audits, independent inner correction scopes, and identified all-or-nothing failure | Both | Implemented; gate pending |
| Extraction and composition | Individual/grouped extraction and heterogeneous composition retain categorical results by identity | Both | Implemented; gate pending |
| Compatibility disposition | Every touched upstream method and argument classified in `compatibility.md` | Both | Complete |
| Oracle and independent evidence | Frozen pinned-R objects plus analytic or independently implemented references | Both | Complete |
| Performance baseline | Five-sample selection/analysis/bar-render/pie-render/grouped grids through declared ceilings | Both | Complete |
| Public documentation | Examples, table orientation, expected ratios, paired/count inputs, sparse behavior, labels, errors, limits, and adaptations | Both | Complete |
| Production repository gate | Check, audit, build, isolated-wheel smoke, oracle verification, and benchmark verification pass | Both | Complete |
| Review and sign-off | Verification loop, adversarial review, finding disposition, independent review, and Joshua Myers approval | Both | Pending |

## Required statistical decision records

The M4 method specification must name and obtain approval for these records:

- C1: one-way goodness-of-fit test, expected-ratio semantics, effect size, and
  interval;
- C2: independent two-way omnibus association test, expected-count/sparse-table
  policy, effect size, and interval;
- C3: paired categorical test, admissible table shape, experimental unit,
  effect size, and interval;
- C4: independent-table pairwise family, contrast orientation, test identity,
  correction, interval/effect metadata, and display policy;
- C5: within-stratum proportion-test family, null ratios, correction scope,
  interval method, and display policy;
- G5: grouped categorical missingness, identity, sample, and correction scope.

For every record, approval must cover:

- population, sampling unit, experimental unit, estimand, null and alternative
  hypotheses, sidedness, and decision rule selecting the design;
- test statistic, reference distribution or exact algorithm, degrees of
  freedom, continuity correction, conditioning/margin assumptions, and whether
  any method switch is automatic or forbidden;
- effect-size identity, bias correction, orientation, mathematical range,
  interval target/method/level, and behavior at boundary values;
- one-way expected ratios: key/position alignment, normalization, tolerance,
  zero expected probability, omitted declared level, and default null model;
- independent-table expected counts, zero cells, empty margins, sparse-table
  threshold, exact/asymptotic failure behavior, and large-count conditioning;
- paired-table category alignment, square-table requirement, treatment of
  concordant/discordant cells, count weights, minimum information, and
  multi-category behavior;
- pairwise and proportion-test hypothesis membership, ordering, raw and
  adjusted values, alpha, adjustment method, display filtering, and separation
  between omnibus, pairwise, stratum, and outer-group families;
- missing category/count behavior, unobserved declared levels, structural versus
  sampling zeros, minimum categories, one-level strata, and degenerate tables;
- full typed-result fields, rendered terminology, compatibility tier,
  numerical tolerance, independent reference, and pinned-oracle interpretation.

No expected-count warning may silently change the test. If an exact or
simulation-based path is proposed, its state space, deterministic inputs,
caller-owned random generator, replicate/work ceiling, error bound, and failure
behavior require separate approval.

## Categorical data contract

- Inputs are Polars dataframes and explicit column names. `x` is required; `y`,
  `counts`, and outer `group` columns must be distinct when supplied.
- Category and group identities retain supported JSON scalar types. Declared
  Enum order is honored; ordinary Polars Categorical/string values use a
  deterministic scalar order because physical category codes are encounter-
  ordered. Row permutations cannot change table axes or hypothesis orientation.
- With no `counts` column, each retained row contributes exactly one unit. With
  `counts`, values must be finite, nonnegative integers representable exactly by
  the chosen internal count dtype. Null, negative, fractional, or overflowing
  counts follow the approved failure/audit policy.
- Count-weighted input is aggregated directly into table cells. It is never
  expanded into repeated rows. Equivalent raw and aggregated inputs must yield
  identical analyzed counts and inferential results.
- Null removal occurs once at the shared boundary and records missing `x`, `y`,
  `counts`, and outer-group identities separately where distinguishable. Both
  physical input rows and weighted analyzed units reconcile.
- The owned table covers the deterministic cross-product of retained/declared
  levels and represents sampling zeros explicitly. Structural-zero models are
  outside M4; callers cannot mark a cell structurally impossible.
- Empty analyzed totals, invalid margins, unsupported identities, excessive
  categories/cells, and ambiguous paired tables fail before analysis or
  rendering returns a partial object.
- The caller dataframe is never mutated. Owned category identities, cell counts,
  totals, expected values, and analysis arrays are immutable.

## Analysis and result contract

- A renderer-independent `CategoricalAnalysis` contains the exact owned table
  and a frozen schema-v1 categorical result.
- The result retains design (`one_way`, `independent`, or `paired`), column
  identities, ordered `x`/`y` levels, every observed cell, row/column/grand
  totals, denominators and proportions, expected counts where applicable, and a
  physical-row/weighted-unit audit.
- It also retains the approved omnibus test, effect estimate/interval,
  assumptions or expected-count diagnostics, complete pairwise and stratum
  families, raw/adjusted probabilities, alpha, display policy, correction
  scopes, resource limits, compatibility warnings, and method identity.
- Counts and totals serialize as integers; probabilities, effects, intervals,
  expected values, and residual diagnostics serialize as finite numbers or an
  explicitly schema-permitted absence. NaN and infinity never appear in public
  JSON.
- All cell, margin, sample, pairwise, and stratum counts reconcile. Constructing
  an incomplete or contradictory typed result fails.
- Analysis modules do not import Matplotlib, inspect global plotting state, or
  resolve arbitrary functions/palettes dynamically.
- `analyze_ggbarstats` and `analyze_ggpiestats` are aliases or thin entry points
  to the same categorical analysis behavior. Re-rendering an analysis never
  recomputes a test.

## Rendering contract

- `render_ggbarstats` and `render_ggpiestats` accept the shared categorical
  analysis and produce new owned Matplotlib figures.
- A one-way bar plot contains one normalized bar segmented by `x`; a two-way
  bar plot contains one normalized bar per `y`, segmented by `x`. A one-way pie
  contains one pie; a two-way pie contains one deterministic facet per `y`.
- Bar heights, wedge angles, cell labels, sample totals, legend entries, colors,
  titles, subtitles, captions, p-value annotations, and any interval/error layer
  originate only in typed result fields.
- Supported label modes are explicitly allowlisted and distinguish counts from
  percentages. Rounding is presentation-only; full precision and integer counts
  remain extractable.
- Zero-count categories remain represented in the result and legend. Renderers
  do not fabricate visible area, divide by zero, or label a zero-area wedge as
  nonzero. Empty margins fail according to the approved method record.
- Both renderers use one deterministic level-to-color mapping. A palette request
  with insufficient colors fails before a partial figure is returned.
- Labels must remain associated with the correct cell under input-row, category,
  and facet reordering. Collision handling is deterministic and bounded; no
  random jitter or hidden label dropping is permitted.
- `results_subtitle=False`, label filtering, and proportion-test display options
  change presentation only. They never delete computed result records.
- Visual compatibility means table, layer, label, facet, and annotation parity;
  pixel-identical ggplot output is not required.

## Grouped, extraction, and composition contract

- Grouped functions split on one explicit outer group using the established
  first-observed order and scalar-identity policy, then apply the identical
  categorical boundary and method independently within each group.
- Null outer-group rows are audited at the container boundary. An invalid inner
  group names its identity and fails the operation atomically.
- Inner omnibus, pairwise, and stratum corrections remain within that result.
  No correction is pooled across outer groups unless a later approved method
  explicitly says otherwise.
- Category support differences between outer groups are retained explicitly.
  A grouped renderer must use a documented common color/legend domain so the
  same category never changes meaning between panels.
- `extract_stats`, `extract_subtitle`, and `extract_caption` work for individual
  and grouped categorical containers. `combine_plots` flattens grouped members
  and preserves each categorical result by object identity.

## Required fixture matrix

| Area | Minimum retained cases |
|---|---|
| One-way goodness-of-fit | uniform/null fit; clear departure; 2, 5, 10, and 20 levels; custom unequal ratio; reordered ratio/category input; one zero observed category; nulls; minimum information; all-zero and one-level failures |
| Independent tables | analytic 2x2 and RxC cases; balanced and unbalanced margins; null/clear association; zero sampling cells; empty margin; expected counts below policy threshold; ties; reordered axes; extreme but valid total |
| Paired tables | 2x2 concordant/discordant cases; null/clear asymmetry; square multi-category case if supported; mismatched categories; nonsquare table; no discordant information; reordered rows/levels; null pairs |
| Aggregate counts | raw-versus-aggregated equivalence; duplicate cells; zero counts; null/negative/fractional/overflow counts; compact input with large weighted total |
| Pairwise family | 3, 5, 10, and 20 `x` levels; complete family size; known raw/adjusted values; tied p-values; significant/non-significant/all/none display; stable contrast order |
| Stratum proportions | enabled/disabled behavior; known null ratios; one-level stratum; raw/adjusted values; separation from pairwise and omnibus families |
| Bar renderer | one- and two-way layout; count/percentage/both/none labels; totals; zero segment; stable color/legend; result injection; insufficient palette; bounded annotations |
| Pie renderer | one and many facets; count/percentage/both/none labels; zero wedge; stable color/legend; result injection; collision boundary; excessive facets |
| Grouped | first-observed group order; null group row; different category support; repeated labels; invalid/sparse group; atomic failure; nested correction metadata; common colors |
| Extraction/composition | all individual/grouped containers; mixed M2/M3/M4 dashboard; result identity; JSON serialization; headless SVG output |

Oracle agreement alone is insufficient. Every deterministic test, effect, and
interval needs an analytic case or implementation/reference independent of the
production calculation. If an exact or stochastic method is retained, its
calibration and reproducibility evidence must be predeclared.

## Resource and performance requirements

Unless an approved method record adopts a stricter limit, the public defaults
are:

- maximum physical input rows: 1,000,000;
- maximum `x` levels: 20;
- maximum `y` levels/facets: 20;
- maximum contingency cells: 400;
- maximum pairwise hypotheses in one family: 190;
- maximum rendered cell labels: 400;
- maximum outer groups: 20;
- maximum weighted analyzed total: 1,000,000,000.

Each applicable ceiling has an explicit positive override and is serialized in
the result. Overrides may not bypass numeric representability or package-wide
safety bounds. Oversized inputs fail predictably; there is no silent category,
cell, row, group, label, or hypothesis sampling.

The retained M4 benchmark must:

- preserve M0, M2, and M3 baselines and investigate any same-host median time or
  peak-allocation regression above 20%;
- record five warmed measurements per phase with input-frame construction
  outside the measured boundary;
- measure categorical selection, inference, bar rendering, and pie rendering
  separately;
- retain raw-row workloads at 10K, 100K, and 1M rows with a 5x5 table;
- retain level/cell workloads at 2, 5, 10, and 20 levels per dimension through
  the 400-cell boundary;
- retain pairwise workloads through 20 `x` levels/190 hypotheses;
- retain equivalent raw and count-weighted workloads, including a compact large
  weighted table;
- retain grouped workloads at 1, 5, and 20 groups and pie facets at 1, 5, 10,
  and 20;
- report elapsed-time and incremental Python allocation distributions without
  timing Docker, R, oracle startup, or fixture construction.

## Compatibility requirements

- Audit the pinned implementations, documentation, raw result objects, and
  grouped wrappers for all four public surfaces before declaring an argument
  supported.
- Classify each touched method and argument as equivalent, adapted,
  experimental, or deferred in `compatibility.md`.
- Preserve `ggbarstats`, `ggpiestats`, and grouped names. Use snake_case,
  explicit column names, typed label/palette choices, and Python-specific
  subject/count contracts where safety requires adaptation.
- The first release is classical. Bayesian categorical analysis remains in M6.
  Any nonparametric/exact mode not explicitly approved for sparse-table safety
  is deferred and rejected rather than accepted and ignored.
- Arbitrary ggplot components, R theme objects, dynamic palette lookup, output
  modes returning undocumented dataframes, and ellipsis forwarding are
  deferred. Equivalent typed Python capabilities may be proposed separately.
- Differences in table construction, declared empty levels, counts expansion,
  continuity correction, pairwise tests, proportion tests, effect intervals,
  labels, legends, and grouped category domains must be named next to enforcing
  tests.

## Non-goals

- Bayesian categorical methods, assigned to M6.
- General robust/resampling or Monte Carlo inference without a separate approved
  method record.
- Three-way or higher contingency tables, log-linear models, multinomial or
  ordinal regression, survey weights, clustered/longitudinal categorical
  models, hierarchical tables, or arbitrary contrasts.
- Structural-zero modeling, missing-category imputation, automatic category
  collapsing, or automatic sparse-method switching.
- Mosaic, alluvial, Sankey, interactive, animated, or general-purpose plotting.
- General dataframe interchange or pandas support.
- Arbitrary R expressions, function lookup, ggplot layers, or palette package
  resolution.
- Pixel-identical R output or final 1.0 schema/style stability.

## Verification rubric and acceptance criteria

| Dimension | Severity | Pass threshold |
|---|---|---|
| Statistical identity | Blocking | Approved C1–C5/G5 records; analytic/independent evidence; oracle disposition; correct hypotheses, tests, effects, intervals, and labels |
| Table/sample integrity | Blocking | Physical rows, weighted units, cells, margins, levels, nulls, zeros, and plotted totals reconcile for raw and aggregate inputs |
| Sparse/paired safety | Blocking | Expected-count and zero-cell policy is explicit; paired design and table admissibility are unambiguous; no silent method switch |
| Multiplicity integrity | Blocking | Omnibus, pairwise, stratum, and outer-group families are complete, separate, ordered, retained, and adjusted exactly as approved |
| Cross-renderer contract | Blocking | Bar and pie consume the same typed analysis/result; all displayed values originate in it; neither renderer recomputes inference |
| Grouping/extraction/composition | Blocking | Stable identities/colors, atomic grouped failure, nested audits/scopes, complete extraction, and composition identity preservation |
| Failure and resource behavior | Blocking | Invalid categories/counts/ratios/tables/palettes and ceiling excess fail explicitly without partial output or silent sampling |
| Compatibility | Blocking | Every touched upstream surface, method, and argument has a tested disposition; no unsupported keyword is ignored |
| Oracle and independence | Blocking | Pinned-R fixtures verify shared behavior; every supported deterministic method also has an independent reference at predeclared tolerance |
| Production quality | Blocking | `make check`, `make audit`, `make build`, isolated-wheel smoke, oracle verification, and benchmark verification pass |
| Coverage | Required | Project branch coverage remains at least 75%; every new M4 domain module reaches at least 90% branch coverage |
| Performance | Required | Earlier retained paths remain within the 20% investigation threshold or have an approved disposition; the complete M4 grid is retained |
| Documentation | Required | Public examples, design orientation, ratios, counts, sparse/paired behavior, labels, limits, errors, and adaptations match implementation |
| Accountable acceptance | Blocking | All findings are dispositioned; an independent reviewer records a decision; Joshua Myers approves the supported methods and final M4/`0.2` candidate |

## Verification budget and stopping rules

- Use at most three evidence-changing verification passes after the method-entry
  audit. A pass must add focused implementation/tests, independent/oracle or
  retained benchmark evidence, a full production gate, or a meaningfully
  different adversarial review.
- Stop before inferential implementation when any C1–C5/G5 choice lacks Joshua
  Myers's approval.
- Stop a method on ambiguous experimental units, ratio alignment, count
  semantics, paired-table shape, expected-count/sparse behavior, test switching,
  effect target, interval, or correction family.
- Stop the milestone on an unexplained oracle mismatch, raw/aggregate mismatch,
  table/result/render divergence, cross-renderer inconsistency, unbounded
  workload, package-gate failure, or unapproved compatibility claim.
- Record each accepted, corrected, deferred, or rejected finding with severity,
  owner, disposition, and acceptance check. Repeating review against unchanged
  evidence does not consume another pass or establish independence.

## Required closeout artifacts

- `docs/M4_STATISTICAL_METHODS.md`;
- `docs/evidence/M4_VERIFICATION_LOOP.md`;
- `docs/evidence/M4_ADVERSARIAL_REVIEW.md`;
- `docs/evidence/M4_VERIFICATION.md`;
- `docs/evidence/M4_SIGNOFF.md`;
- categorical result schema and any grouped/resource schema revisions;
- raw and normalized pinned-R categorical fixtures plus updated oracle manifest;
- retained M4 benchmark plus updated benchmark verifier;
- updated `docs/compatibility.md`, `docs/CONTRACTS.md`,
  `STATISTICAL_ANALYSIS_PLAN.md`, `README.md`, changelog, and project memory.

Joshua Myers must approve every retained statistical method before its fixtures
become acceptance evidence and approve the final release candidate after all
findings are dispositioned. Agent review cannot provide either approval.

## Exit gate

M4 is complete only when all four public surfaces expose the approved one-way,
independent, and paired classical designs; raw and aggregate counts reconcile;
eligible pairwise and stratum families pass; bar and pie share one typed result;
grouped, extraction, composition, compatibility, schema, oracle, benchmark,
coverage, documentation, audit, build, and isolated-wheel gates pass; every
blocking finding is closed; an independent review is recorded; and Joshua Myers
approves the M4 release candidate. At that point, and only while M3 remains
complete, the `0.2` product gate is complete.
