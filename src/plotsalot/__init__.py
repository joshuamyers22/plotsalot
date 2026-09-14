"""Statistical visualizations and extractable results for Python."""

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

__all__ = [
    "AnalysisResult",
    "CorrelationAnalysis",
    "CorrelationMatrixAnalysis",
    "CorrelationMatrixResult",
    "CorrelationResult",
    "DotPlotAnalysis",
    "DotPlotResult",
    "GroupedAnalysis",
    "GroupedResult",
    "GroupedStatsPlot",
    "HistogramAnalysis",
    "NumericSample",
    "PairedNumericSample",
    "PlotAnnotations",
    "ResourceLimits",
    "StatsPlot",
    "StructuredResult",
    "analyze_grouped_ggcorrmat",
    "analyze_grouped_ggdotplotstats",
    "analyze_grouped_gghistostats",
    "analyze_grouped_ggscatterstats",
    "analyze_ggcorrmat",
    "analyze_ggdotplotstats",
    "analyze_gghistostats",
    "analyze_ggscatterstats",
    "extract_caption",
    "extract_stats",
    "extract_subtitle",
    "ggcorrmat",
    "ggdotplotstats",
    "gghistostats",
    "ggscatterstats",
    "grouped_ggcorrmat",
    "grouped_ggdotplotstats",
    "grouped_gghistostats",
    "grouped_ggscatterstats",
    "render_ggcorrmat",
    "render_ggdotplotstats",
    "render_gghistostats",
    "render_ggscatterstats",
    "render_grouped_ggcorrmat",
    "render_grouped_ggdotplotstats",
    "render_grouped_gghistostats",
    "render_grouped_ggscatterstats",
    "select_numeric_pair",
    "select_numeric_sample",
]
