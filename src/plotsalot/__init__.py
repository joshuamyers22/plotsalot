"""Statistical visualizations and distribution diagnostics for Python."""

from plotsalot.data import NumericSample, select_numeric_sample
from plotsalot.histogram import gghistostats, render_gghistostats
from plotsalot.histogram_analysis import HistogramAnalysis, analyze_gghistostats
from plotsalot.plot import (
    PlotAnnotations,
    StatsPlot,
    extract_caption,
    extract_stats,
    extract_subtitle,
)
from plotsalot.result import AnalysisResult, StructuredResult

__all__ = [
    "AnalysisResult",
    "HistogramAnalysis",
    "NumericSample",
    "PlotAnnotations",
    "StatsPlot",
    "StructuredResult",
    "analyze_gghistostats",
    "extract_caption",
    "extract_stats",
    "extract_subtitle",
    "gghistostats",
    "render_gghistostats",
    "select_numeric_sample",
]
