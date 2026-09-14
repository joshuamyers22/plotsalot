"""Statistical visualizations and extractable results for Python."""

from plotsalot.categorical import (
    ggbarstats,
    ggpiestats,
    render_ggbarstats,
    render_ggpiestats,
)
from plotsalot.categorical_analysis import (
    CategoricalAnalysis,
    analyze_categorical,
    analyze_ggbarstats,
    analyze_ggpiestats,
)
from plotsalot.categorical_data import CategoricalTable, select_categorical_table
from plotsalot.categorical_grouped import (
    analyze_grouped_ggbarstats,
    analyze_grouped_ggpiestats,
    grouped_ggbarstats,
    grouped_ggpiestats,
    render_grouped_ggbarstats,
    render_grouped_ggpiestats,
)
from plotsalot.categorical_result import CategoricalResult, CategoricalSampleAudit
from plotsalot.coefficient import ggcoefstats, render_ggcoefstats
from plotsalot.coefficient_analysis import CoefficientAnalysis, analyze_ggcoefstats
from plotsalot.coefficient_data import (
    CoefficientTable,
    StudyEffectTable,
    select_coefficients,
    select_study_effects,
)
from plotsalot.coefficient_result import (
    CoefficientResult,
    CoefficientTableResult,
    MetaAnalysisResult,
)
from plotsalot.coefficient_table_analysis import TableCoefficientAnalysis
from plotsalot.comparison import (
    ggbetweenstats,
    ggwithinstats,
    render_ggbetweenstats,
    render_ggwithinstats,
)
from plotsalot.comparison_analysis import (
    ComparisonAnalysis,
    analyze_ggbetweenstats,
    analyze_ggwithinstats,
)
from plotsalot.comparison_data import ComparisonSample, RepeatedSample
from plotsalot.comparison_grouped import (
    analyze_grouped_ggbetweenstats,
    analyze_grouped_ggwithinstats,
    grouped_ggbetweenstats,
    grouped_ggwithinstats,
    render_grouped_ggbetweenstats,
    render_grouped_ggwithinstats,
)
from plotsalot.comparison_result import (
    ComparisonResult,
    PairwiseComparisonResult,
    RepeatedSampleAudit,
)
from plotsalot.composition import (
    ComposedStatsPlot,
    CompositionResult,
    combine_plots,
)
from plotsalot.correlation import (
    ggcorrmat,
    ggscatterstats,
    render_ggcorrmat,
    render_ggscatterstats,
)
from plotsalot.correlation_analysis import (
    CorrelationAnalysis,
    CorrelationMatrixAnalysis,
    analyze_ggcorrmat,
    analyze_ggscatterstats,
)
from plotsalot.data import (
    NumericSample,
    PairedNumericSample,
    select_numeric_pair,
    select_numeric_sample,
)
from plotsalot.dotplot import ggdotplotstats, render_ggdotplotstats
from plotsalot.dotplot_analysis import DotPlotAnalysis, analyze_ggdotplotstats
from plotsalot.grouped import (
    GroupedAnalysis,
    analyze_grouped_ggcorrmat,
    analyze_grouped_ggdotplotstats,
    analyze_grouped_gghistostats,
    analyze_grouped_ggscatterstats,
    grouped_ggcorrmat,
    grouped_ggdotplotstats,
    grouped_gghistostats,
    grouped_ggscatterstats,
    render_grouped_ggcorrmat,
    render_grouped_ggdotplotstats,
    render_grouped_gghistostats,
    render_grouped_ggscatterstats,
)
from plotsalot.histogram import gghistostats, render_gghistostats
from plotsalot.histogram_analysis import HistogramAnalysis, analyze_gghistostats
from plotsalot.plot import (
    GroupedStatsPlot,
    PlotAnnotations,
    StatsPlot,
    extract_caption,
    extract_stats,
    extract_subtitle,
)
from plotsalot.result import (
    AnalysisResult,
    CorrelationMatrixResult,
    CorrelationResult,
    DotPlotResult,
    GroupedResult,
    ResourceLimits,
    StructuredResult,
)
from plotsalot.theme import StatsTheme, theme_ggstatsplot

__all__ = [
    "AnalysisResult",
    "CategoricalAnalysis",
    "CategoricalResult",
    "CategoricalSampleAudit",
    "CategoricalTable",
    "CoefficientAnalysis",
    "CoefficientResult",
    "CorrelationAnalysis",
    "CorrelationMatrixAnalysis",
    "CorrelationMatrixResult",
    "CorrelationResult",
    "ComparisonAnalysis",
    "ComparisonResult",
    "ComparisonSample",
    "ComposedStatsPlot",
    "CompositionResult",
    "DotPlotAnalysis",
    "DotPlotResult",
    "GroupedAnalysis",
    "GroupedResult",
    "GroupedStatsPlot",
    "HistogramAnalysis",
    "NumericSample",
    "MetaAnalysisResult",
    "PairedNumericSample",
    "PairwiseComparisonResult",
    "PlotAnnotations",
    "ResourceLimits",
    "RepeatedSample",
    "RepeatedSampleAudit",
    "StatsTheme",
    "StudyEffectTable",
    "CoefficientTable",
    "CoefficientTableResult",
    "TableCoefficientAnalysis",
    "StatsPlot",
    "StructuredResult",
    "analyze_categorical",
    "analyze_grouped_ggbarstats",
    "analyze_grouped_ggcorrmat",
    "analyze_grouped_ggbetweenstats",
    "analyze_grouped_ggdotplotstats",
    "analyze_grouped_gghistostats",
    "analyze_grouped_ggscatterstats",
    "analyze_grouped_ggwithinstats",
    "analyze_grouped_ggpiestats",
    "analyze_ggbarstats",
    "analyze_ggcoefstats",
    "analyze_ggbetweenstats",
    "analyze_ggcorrmat",
    "analyze_ggdotplotstats",
    "analyze_gghistostats",
    "analyze_ggscatterstats",
    "analyze_ggwithinstats",
    "analyze_ggpiestats",
    "combine_plots",
    "extract_caption",
    "extract_stats",
    "extract_subtitle",
    "ggbarstats",
    "ggcoefstats",
    "ggcorrmat",
    "ggbetweenstats",
    "ggdotplotstats",
    "gghistostats",
    "ggscatterstats",
    "ggwithinstats",
    "ggpiestats",
    "grouped_ggbarstats",
    "grouped_ggbetweenstats",
    "grouped_ggcorrmat",
    "grouped_ggdotplotstats",
    "grouped_gghistostats",
    "grouped_ggscatterstats",
    "grouped_ggwithinstats",
    "grouped_ggpiestats",
    "render_ggbarstats",
    "render_ggcoefstats",
    "render_ggbetweenstats",
    "render_ggcorrmat",
    "render_ggdotplotstats",
    "render_gghistostats",
    "render_ggscatterstats",
    "render_grouped_ggcorrmat",
    "render_grouped_ggbetweenstats",
    "render_grouped_ggdotplotstats",
    "render_grouped_gghistostats",
    "render_grouped_ggscatterstats",
    "render_grouped_ggwithinstats",
    "render_ggwithinstats",
    "render_ggpiestats",
    "render_grouped_ggbarstats",
    "render_grouped_ggpiestats",
    "select_categorical_table",
    "select_study_effects",
    "select_coefficients",
    "select_numeric_pair",
    "select_numeric_sample",
    "theme_ggstatsplot",
]
