# Documentation

Plotsalot documentation is organized by reader intent. The package is pre-1.0;
public behavior is defined by source, tests, approved method specifications, and
versioned result schemas rather than by similarity to the upstream R interface.

## Start here

| Goal | Document |
|---|---|
| Install and complete a first analysis | [Getting started](GETTING_STARTED.md) |
| Select an analysis or plotting workflow | [User guide](USER_GUIDE.md) |
| Interpret outputs and understand refusal behavior | [Interpretation and limitations](INTERPRETATION_AND_LIMITATIONS.md) |
| Inspect data, analysis, result, and rendering boundaries | [Contracts](CONTRACTS.md) |
| Check implemented and deferred upstream behavior | [Compatibility](compatibility.md) |

## Statistical methods

- [M2 frequentist univariate and correlation methods](M2_STATISTICAL_METHODS.md)
- [M3 independent and repeated comparison methods](M3_STATISTICAL_METHODS.md)
- [M4 categorical methods](M4_STATISTICAL_METHODS.md)
- [M5 coefficient and frequentist meta-analysis methods](M5_STATISTICAL_METHODS.md)
- [M6 robust methods](M6_STATISTICAL_METHODS.md)
- [M6 Bayesian methods](M6B_STATISTICAL_METHODS.md)
- [M6 coefficient and meta-analysis extensions](M6C_STATISTICAL_METHODS.md)

The root [statistical analysis plan](../STATISTICAL_ANALYSIS_PLAN.md) records the
cross-milestone review boundary. Method documents specify estimands, sampling
rules, uncertainty, failure behavior, and adaptation decisions.

## Development and evidence

- [Project plan](PROJECT_PLAN.md)
- [M7 active contract](MILESTONE_7.md)
- [1.x API and schema stability policy](API_STABILITY.md)
- [M7 robust meta-analysis calibration plan](M7_CALIBRATION_PLAN.md)
- [Release procedure](RELEASING.md)
- [Milestone records](MILESTONE_0.md)
- [Architecture decisions](adr/ADR-001-project-identity.md)
- [Accepted 1.x stability decision](adr/ADR-007-public-api-schema-stability.md)
- [Verification and sign-off records](evidence/M6_RELEASE_VERIFICATION.md)
- [Pinned upstream manifest](upstream/README.md)
- [Parquet dataset contract](PARQUET_DATASETS.md)
- [Regression evidence contract](REGRESSION_EVIDENCE.md)
- [Statistical-learning point of view](STATISTICAL_LEARNING_POINT_OF_VIEW.md)
- [Agentic verification guide](AGENTIC_VERIFICATION_GUIDE.md)

Milestone and evidence documents are retained audit records. They are not the
recommended entry point for ordinary package use.
