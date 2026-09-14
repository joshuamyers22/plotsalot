"""Statistical visualizations and distribution diagnostics for Python."""

from plotsalot.core import AnalysisResult, StatsPlot
from plotsalot.histogram import (
    extract_caption,
    extract_stats,
    extract_subtitle,
    gghistostats,
)

__all__ = [
    "AnalysisResult",
    "StatsPlot",
    "extract_caption",
    "extract_stats",
    "extract_subtitle",
    "gghistostats",
]
