# Shared Analysis, Data, and Rendering Contracts

These contracts are the M1 foundation extended by the approved M2 univariate,
correlation, and grouped-result records.

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

## Result boundary

`StructuredResult` is the minimum interface accepted by `StatsPlot`: a schema
version, an analysis identity, and a JSON-safe `to_dict` representation. Each
plot family owns a concrete frozen result type and a checked-in schema rather
than forcing unrelated methods into a universal bag of optional fields.

Concrete schema-v1 result families are `AnalysisResult`, `DotPlotResult`,
`CorrelationResult`, `CorrelationMatrixResult`, and `GroupedResult`. Their
serialized shapes are governed by the checked-in files under `schemas/`.
New M2 results retain their configured resource ceilings in `ResourceLimits`.

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

## Compatibility policy

These contracts are public during the 0.x series and use explicit schema
versions. A backward-incompatible Python or serialized-result change requires a
changelog entry, schema-version decision, migration note, and focused contract
tests. Statistical compatibility labels remain governed by ADR-004 and do not
follow merely from satisfying these software boundaries.
