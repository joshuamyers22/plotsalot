# Shared Analysis, Data, and Rendering Contracts

These contracts are the M1 foundation for later plot families. They are narrow
on purpose: a new method extends them only after its statistical specification
defines the additional behavior.

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

## Result boundary

`StructuredResult` is the minimum interface accepted by `StatsPlot`: a schema
version, an analysis identity, and a JSON-safe `to_dict` representation. Each
plot family owns a concrete frozen result type and a checked-in schema rather
than forcing unrelated methods into a universal bag of optional fields.

The current `AnalysisResult` is the concrete schema-v1 result for the
parametric one-sample `gghistostats` slice. Its serialized shape is governed by
`schemas/analysis-result.schema.json`.

## Analysis and rendering boundary

`analyze_gghistostats` performs validation and statistical computation without
creating a figure. It returns `HistogramAnalysis`, containing the structured
result and exact numeric sample.

`render_gghistostats` consumes that object and creates a new Matplotlib figure.
It formats all displayed statistics from typed result fields. Re-rendering the
same analysis can change visual options without recomputing statistics.

`gghistostats` remains the convenience operation that performs both steps.

## Plot boundary

`StatsPlot` pairs a structured result with its Matplotlib figure, named axes,
and `PlotAnnotations`. Construction rejects empty axes or axes owned by a
different figure. The axes mapping is copied and exposed read-only, while the
Matplotlib objects themselves remain caller-customizable.

`extract_stats`, `extract_subtitle`, and `extract_caption` operate on any
`StatsPlot` whose result implements `StructuredResult`.

## Compatibility policy

These contracts are public during the 0.x series and use explicit schema
versions. A backward-incompatible Python or serialized-result change requires a
changelog entry, schema-version decision, migration note, and focused contract
tests. Statistical compatibility labels remain governed by ADR-004 and do not
follow merely from satisfying these software boundaries.
