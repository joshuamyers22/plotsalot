"""Compatibility exports for the M0 result and M1 plot contracts.

New internal code should import result records from :mod:`plotsalot.result` and
plot containers from :mod:`plotsalot.plot` so analytical code stays independent
of Matplotlib.
"""

from plotsalot.plot import (
    PlotAnnotations,
    StatsPlot,
    extract_caption,
    extract_stats,
    extract_subtitle,
)
from plotsalot.result import (
    AnalysisResult,
    EffectSizeResult,
    EstimateResult,
    IntervalResult,
    SampleAudit,
    StructuredResult,
    TestResult,
)

__all__ = [
    "AnalysisResult",
    "EffectSizeResult",
    "EstimateResult",
    "IntervalResult",
    "PlotAnnotations",
    "SampleAudit",
    "StatsPlot",
    "StructuredResult",
    "TestResult",
    "extract_caption",
    "extract_stats",
    "extract_subtitle",
]
