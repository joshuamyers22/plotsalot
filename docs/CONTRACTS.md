# Shared Analysis, Data, and Rendering Contracts

These contracts are the M1 foundation extended by the approved M2 univariate
and correlation records and the approved M3 comparison, composition, and theme
records.

## Data boundary

`select_numeric_sample` is the canonical one-column boundary:

- input must be a Polars dataframe and a named numeric column;
- nulls are dropped and reconciled in `SampleAudit`;
- NaN and infinite values fail rather than being silently omitted;
- size and nonzero-variation requirements are explicit arguments;
- output is an owned, one-dimensional, read-only NumPy `float64` array.

`NumericSample` keeps that exact array with its column identity and audit. An
analysis and renderer sharing one `NumericSample` therefore cannot select subtly
different rows.

`select_numeric_pair` applies the same ownership contract to two aligned,
pairwise-complete columns. M2 association analyses require four retained pairs,
variation in both columns, and reject non-finite and numerically near-constant
inputs.

`select_comparison_sample` owns a deterministic 2–20-level independent sample.
It removes rows null in the level or numeric value, requires two observations
and positive variance per level, preserves scalar identity, and orders levels by
declared categorical order or deterministic scalar order.

`select_repeated_sample` requires explicit, distinct subject, condition, and
numeric columns. Duplicate subject-condition cells fail before null-value
removal. It then removes null identities/values and constructs one complete
subject-by-condition block; incomplete subjects are audited and excluded from
both inference and rendering. Its numeric matrix and identity arrays are owned
and read-only.

## Result boundary

`StructuredResult` is the minimum interface accepted by `StatsPlot`: a schema
version, an analysis identity, and a JSON-safe `to_dict` representation. Each
plot family owns a concrete frozen result type and a checked-in schema rather
than forcing unrelated methods into a universal bag of optional fields.

Concrete schema-v1 result families are `AnalysisResult`, `DotPlotResult`,
`CorrelationResult`, `CorrelationMatrixResult`, `ComparisonResult`,
`GroupedResult`, and `CompositionResult`. Their serialized shapes are governed
by the checked-in files under `schemas/`. M2 and M3 results retain their
configured resource ceilings in `ResourceLimits`.

`ComparisonResult` contains the exact analyzed sample audit, ordered per-level
descriptives, omnibus test, two-level estimate/interval when applicable, named
effect size, complete pairwise family, raw and adjusted probabilities, display
policy, repeated-measures correction metadata, limits, and warnings. It rejects
incomplete hypothesis families and inconsistent design, method, interval,
correction, count, or limit metadata.

## Analysis and rendering boundary

`analyze_gghistostats` performs validation and statistical computation without
creating a figure. It returns `HistogramAnalysis`, containing the structured
result and exact numeric sample.

`render_gghistostats` consumes that object and creates a new Matplotlib figure.
It formats all displayed statistics from typed result fields. Re-rendering the
same analysis can change visual options without recomputing statistics.

`gghistostats` remains the convenience operation that performs both steps.
The dot, scatter, and matrix families follow the same `analyze_*`, `render_*`,
and convenience-function split.

The between and within families follow that split as well. Their renderers
consume `ComparisonAnalysis`, use its exact owned values, and format inference
only from `ComparisonResult`. Between rendering includes semantic distribution,
raw-observation, mean-interval, and optional pairwise layers. Within rendering
uses the same layers plus subject paths from the complete analyzed block.

## Plot boundary

`StatsPlot` pairs a structured result with its Matplotlib figure, named axes,
and `PlotAnnotations`. Construction rejects empty axes or axes owned by a
different figure. The axes mapping is copied and exposed read-only, while the
Matplotlib objects themselves remain caller-customizable.

`GroupedStatsPlot` pairs an atomic `GroupedResult` with one ordered `StatsPlot`
per group. Null group rows are audited at the container boundary; any invalid
group fails the operation with its identity. `extract_stats`,
`extract_subtitle`, and `extract_caption` work for individual and grouped plot
containers. Dot labels and group identities preserve their string, integer,
finite-float, or boolean JSON scalar type; unsupported scalar types fail rather
than being silently stringified.

M3 grouped comparisons use the same atomic outer boundary. Each inner result
has its own complete hypothesis family and no p-value correction is pooled
across outer groups. Repeated subject identities are scoped within their outer
group.

## Composition and theme boundary

`combine_plots` accepts a non-empty sequence of `StatsPlot` and
`GroupedStatsPlot` containers, flattens every grouped member in stable order,
and retains each source result object by identity in `CompositionResult`.
Automatic or explicit layout is deterministic, only `guides="keep"` is
supported, and the default ceiling is twenty panels. The composed figure uses
documented raster snapshots; it neither mutates source canvases nor reruns
analysis.

`theme_ggstatsplot` returns a frozen `StatsTheme`. Applying it changes only the
supplied axis and owning figure, including the comparison mean accent color;
process-global Matplotlib `rcParams` remain unchanged.

## Compatibility policy

These contracts are public during the 0.x series and use explicit schema
versions. A backward-incompatible Python or serialized-result change requires a
changelog entry, schema-version decision, migration note, and focused contract
tests. Statistical compatibility labels remain governed by ADR-004 and do not
follow merely from satisfying these software boundaries.
