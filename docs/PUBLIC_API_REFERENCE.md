# Public API Reference

- Status: M7A pass 2 accepted by Joshua Myers on 2026-09-15
- Machine source: [`m7/public-contract.json`](m7/public-contract.json)
- Stability policy: [`API_STABILITY.md`](API_STABILITY.md)

This reference classifies every name exported through `plotsalot.__all__`.
The 1.x candidate retains all 144 names already shipped in `0.1.1`; pass 2
found no accidental wildcard, leading-underscore, test, benchmark, or oracle
export. Exact signatures and dataclass fields are retained in the machine
manifest and checked by `make public-contract`.

Internal defining modules are review metadata, not alternate supported import
paths. The stable import form is `from plotsalot import <name>`. Human-
readable error prose, undocumented object internals, and exact rendered
pixels remain outside the compatibility promise.

## Classification summary

| Category | Count | Rationale |
|---|---:|---|
| `upstream_workflow_surface` | 56 | Approved Python surface for one of the 22 pinned upstream exports. |
| `shared_analysis_function` | 1 | Shared explicit analysis entry point used by supported renderers. |
| `selector_function` | 7 | Owned validation and data-selection boundary for public workflows. |
| `serialized_result` | 25 | Top-level typed result with a versioned JSON-safe representation. |
| `result_component` | 27 | Typed field record exposed by a supported public result contract. |
| `analysis_container` | 12 | Typed analysis/render handoff preserving exact data-result identity. |
| `selected_data` | 9 | Typed owned data boundary returned by a public selector or analysis. |
| `plot_contract` | 5 | Typed figure, annotations, or local-theme contract for rendering. |
| `result_protocol` | 1 | Minimum public structural protocol accepted by plot containers. |
| `coded_exception` | 1 | Public exception with machine-readable failure codes. |

## Classified names

### `upstream_workflow_surface`

Approved Python surface for one of the 22 pinned upstream exports.

Normative documentation: `docs/compatibility.md`, `docs/USER_GUIDE.md`, `docs/CONTRACTS.md`.

`analyze_ggbarstats`, `analyze_ggbetweenstats`, `analyze_ggcoefstats`, `analyze_ggcorrmat`, `analyze_ggdotplotstats`, `analyze_gghistostats`, `analyze_ggpiestats`, `analyze_ggscatterstats`, `analyze_ggwithinstats`, `analyze_grouped_ggbarstats`, `analyze_grouped_ggbetweenstats`, `analyze_grouped_ggcorrmat`, `analyze_grouped_ggdotplotstats`, `analyze_grouped_gghistostats`, `analyze_grouped_ggpiestats`, `analyze_grouped_ggscatterstats`, `analyze_grouped_ggwithinstats`, `combine_plots`, `extract_caption`, `extract_stats`, `extract_subtitle`, `ggbarstats`, `ggbetweenstats`, `ggcoefstats`, `ggcorrmat`, `ggdotplotstats`, `gghistostats`, `ggpiestats`, `ggscatterstats`, `ggwithinstats`, `grouped_ggbarstats`, `grouped_ggbetweenstats`, `grouped_ggcorrmat`, `grouped_ggdotplotstats`, `grouped_gghistostats`, `grouped_ggpiestats`, `grouped_ggscatterstats`, `grouped_ggwithinstats`, `render_ggbarstats`, `render_ggbetweenstats`, `render_ggcoefstats`, `render_ggcorrmat`, `render_ggdotplotstats`, `render_gghistostats`, `render_ggpiestats`, `render_ggscatterstats`, `render_ggwithinstats`, `render_grouped_ggbarstats`, `render_grouped_ggbetweenstats`, `render_grouped_ggcorrmat`, `render_grouped_ggdotplotstats`, `render_grouped_gghistostats`, `render_grouped_ggpiestats`, `render_grouped_ggscatterstats`, `render_grouped_ggwithinstats`, `theme_ggstatsplot`.

### `shared_analysis_function`

Shared explicit analysis entry point used by supported renderers.

Normative documentation: `docs/CONTRACTS.md`, `docs/M4_STATISTICAL_METHODS.md`.

`analyze_categorical`.

### `selector_function`

Owned validation and data-selection boundary for public workflows.

Normative documentation: `docs/CONTRACTS.md`.

`select_categorical_table`, `select_coefficients`, `select_numeric_pair`, `select_numeric_sample`, `select_posterior_coefficient_summaries`, `select_robust_coefficient_summaries`, `select_study_effects`.

### `serialized_result`

Top-level typed result with a versioned JSON-safe representation.

Normative documentation: `docs/CONTRACTS.md`, `schemas/`.

`AnalysisResult`, `BayesianCategoricalResult`, `BayesianComparisonResult`, `BayesianCorrelationMatrixResult`, `BayesianCorrelationResult`, `BayesianDotPlotResult`, `BayesianMetaResult`, `BayesianOneSampleResult`, `CategoricalResult`, `CoefficientResult`, `CoefficientTableResult`, `ComparisonResult`, `CompositionResult`, `CorrelationMatrixResult`, `CorrelationResult`, `DotPlotResult`, `GroupedResult`, `PosteriorCoefficientTableResult`, `RobustCoefficientTableResult`, `RobustComparisonResult`, `RobustCorrelationMatrixResult`, `RobustCorrelationResult`, `RobustDotPlotResult`, `RobustMetaResult`, `RobustOneSampleResult`.

### `result_component`

Typed field record exposed by a supported public result contract.

Normative documentation: `docs/CONTRACTS.md`, `docs/README.md`.

`BayesianEvidenceResult`, `BayesianMetaEvidenceResult`, `BayesianMetaFitResult`, `BayesianMetaPriorResult`, `BayesianMetaQuadratureResult`, `BayesianMetaStudyResult`, `BayesianPosteriorSummary`, `CategoricalSampleAudit`, `M6CMetaResourceLimits`, `M6CWorkResult`, `MetaAnalysisResult`, `MetaStudyIdentityResult`, `PairwiseComparisonResult`, `PosteriorCoefficientProvenanceResult`, `PosteriorCoefficientSummaryResult`, `PosteriorCoefficientTermResult`, `RepeatedSampleAudit`, `ResamplingResult`, `ResourceLimits`, `RobustCoefficientProvenanceResult`, `RobustCoefficientTermResult`, `RobustMetaAnalysisResult`, `RobustMetaConvergenceResult`, `RobustMetaPooledResult`, `RobustMetaStartResult`, `RobustMetaStudyResult`, `TrimmedKernelResult`.

### `analysis_container`

Typed analysis/render handoff preserving exact data-result identity.

Normative documentation: `docs/CONTRACTS.md`.

`BayesianMetaAnalysis`, `CategoricalAnalysis`, `CoefficientAnalysis`, `ComparisonAnalysis`, `CorrelationAnalysis`, `CorrelationMatrixAnalysis`, `DotPlotAnalysis`, `GroupedAnalysis`, `HistogramAnalysis`, `ReportedCoefficientAnalysis`, `RobustMetaAnalysis`, `TableCoefficientAnalysis`.

### `selected_data`

Typed owned data boundary returned by a public selector or analysis.

Normative documentation: `docs/CONTRACTS.md`.

`CategoricalTable`, `CoefficientTable`, `ComparisonSample`, `NumericSample`, `PairedNumericSample`, `PosteriorCoefficientSummaryTable`, `RepeatedSample`, `RobustCoefficientSummaryTable`, `StudyEffectTable`.

### `plot_contract`

Typed figure, annotations, or local-theme contract for rendering.

Normative documentation: `docs/CONTRACTS.md`, `docs/USER_GUIDE.md`.

`ComposedStatsPlot`, `GroupedStatsPlot`, `PlotAnnotations`, `StatsPlot`, `StatsTheme`.

### `result_protocol`

Minimum public structural protocol accepted by plot containers.

Normative documentation: `docs/CONTRACTS.md`.

`StructuredResult`.

### `coded_exception`

Public exception with machine-readable failure codes.

Normative documentation: `docs/API_STABILITY.md`, `docs/M6C_STATISTICAL_METHODS.md`.

`M6CMetaError`.

## Review and migration rule

Every listed name has `one_x_disposition="stabilize"` in the retained
manifest. That technical disposition preserves the `0.1.1` root surface
and introduces no removal or rename. It does not independently approve
the final 1.0 candidate: statistical disposition, golden serialization,
error and semantic rendering evidence, platform gates, and owner
acceptance remain required by M7.
