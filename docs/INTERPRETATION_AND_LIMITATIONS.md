# Interpretation and limitations

Plotsalot makes statistical calculations and their provenance inspectable. It
does not decide whether a method is scientifically appropriate for a dataset or
whether a result is important.

## What a successful result means

A successful result means that the input passed the implemented validation and
resource gates and that the named method produced a valid typed result under its
recorded contract. It does not by itself establish:

- representative sampling;
- correct study design or independence;
- causal identification;
- practical or clinical importance;
- adequate power or calibration outside retained evidence; or
- suitability for an automated, financial, medical, or policy decision.

Interpret estimates, intervals, tests, Bayes factors, and plots in the context of
the method specification and the data-generating process.

## Samples and missing data

The displayed and tested population is owned by each analysis contract. Numeric
workflows reject non-finite or degenerate samples at their explicit boundary.
Correlation matrices use documented pair construction. Repeated comparisons
require an explicit subject identifier and analyze complete blocks; they do not
infer pairing from row order.

Grouped workflows are atomic. An invalid member invalidates the request rather
than producing a partial collection that could conceal selection.

## Multiplicity and intervals

Holm adjustment is the classical default for supported pairwise and matrix
families. Display filtering changes annotations, not the retained hypothesis
family. Unless a method specification says otherwise, displayed intervals are
pointwise rather than simultaneous.

Do not infer a correction scope from which labels happen to be visible. Inspect
the structured result and its correction metadata.

## Robust methods

The robust continuous modes use fixed 20% trimming or Winsorization. Marginally
Winsorized correlation is not a high-breakdown defense against arbitrary
bivariate leverage. Robust comparison effects are raw location differences, not
automatically standardized effects.

Bootstrap association intervals use owned deterministic streams and bounded
work. Invalid effective samples, degenerate scale, inadequate valid resamples,
or an exceeded work ceiling raise without estimator fallback.

## Bayesian methods

Bayesian modes use the proper priors and computational paths stated in the M6
specifications. Numeric BF10 values are oriented toward H1 over H0; qualitative
evidence labels are deliberately not supplied. Sensitivity records do not prove
that the selected prior family is appropriate.

The M6C robust meta-analysis calibration evidence retained conservative
zero-heterogeneity boundary findings. The accepted disposition is provisional
and must be revisited during M7 before 1.0. See the
[M6C method specification](M6C_STATISTICAL_METHODS.md) and retained evidence for
the exact boundary.

## Coefficients and meta-analysis

Caller-reported coefficient summaries retain unverified provenance; plotsalot
does not reconstruct a missing fit, test, or posterior from an interval. The
narrow fitted-model adapter does not imply support for arbitrary Statsmodels or
third-party model objects.

Aggregate meta-analysis requires independent summaries on one declared
comparable scale. It does not validate study quality, exchangeability, publication
bias, or the substantive comparability of estimands.

## Upstream compatibility

Plotsalot is an adapted Python implementation, not a drop-in or pixel-identical
port of `ggstatsplot`. Important differences include explicit Polars boundaries,
typed result schemas, Matplotlib rendering, stricter failures, explicit subjects
for repeated designs, and project-owned method choices.

Use the [compatibility matrix](compatibility.md) before migrating an analysis.
Unsupported upstream parameters or modes are deferred or rejected; they are not
silently approximated.

## Pre-1.0 stability

Result schemas are versioned, but the public Python API is not yet covered by a
1.0 compatibility promise. Review the [changelog](../CHANGELOG.md), pin an exact
package version for consequential work, and retain serialized method and
provenance metadata with downstream artifacts.
