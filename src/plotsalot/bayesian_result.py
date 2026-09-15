"""Immutable M6B result contracts for approved Bayesian analyses."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import exp, isclose, isfinite, log
from typing import Any

from plotsalot.categorical_result import CategoricalSampleAudit
from plotsalot.comparison_result import RepeatedSampleAudit
from plotsalot.result import (
    IntervalResult,
    ResourceLimits,
    SampleAudit,
    ScalarIdentity,
)


def _finite(value: float, label: str) -> None:
    if not isfinite(value):
        raise ValueError(f"{label} must be finite")


@dataclass(frozen=True, slots=True)
class BayesianMethodResult:
    """Method/software identity shared by M6B result variants."""

    name: str
    version: str
    compatibility: str
    numpy_version: str
    scipy_version: str

    def __post_init__(self) -> None:
        if not all((self.name, self.version, self.numpy_version, self.scipy_version)):
            raise ValueError("Bayesian method identity must be complete")
        if self.compatibility != "adapted":
            raise ValueError("M6B methods must be classified as adapted")


@dataclass(frozen=True, slots=True)
class PriorParameter:
    """One named finite parameter in an approved prior."""

    name: str
    value: float
    units: str

    def __post_init__(self) -> None:
        if not self.name or not self.units:
            raise ValueError("prior parameter identity must be complete")
        _finite(self.value, "prior parameter")


@dataclass(frozen=True, slots=True)
class BayesianPriorResult:
    """Fully named prior family and parameters."""

    family: str
    proper: bool
    parameters: tuple[PriorParameter, ...]

    def __post_init__(self) -> None:
        if not self.family or not self.proper or not self.parameters:
            raise ValueError("M6B requires a complete proper prior")
        names = tuple(parameter.name for parameter in self.parameters)
        if len(names) != len(set(names)):
            raise ValueError("prior parameter names must be unique")


@dataclass(frozen=True, slots=True)
class BayesianPosteriorSummary:
    """Posterior median, equal-tail interval, and direction probabilities."""

    target: str
    median: float
    null_value: float
    interval: IntervalResult
    probability_above_null: float
    probability_below_null: float
    probability_at_null: float

    def __post_init__(self) -> None:
        if not self.target or self.interval.target != self.target:
            raise ValueError("posterior target and interval target must match")
        for value, label in (
            (self.median, "posterior median"),
            (self.null_value, "posterior null"),
            (self.probability_above_null, "probability above null"),
            (self.probability_below_null, "probability below null"),
            (self.probability_at_null, "probability at null"),
        ):
            _finite(value, label)
        if self.interval.method != "bayesian_equal_tail":
            raise ValueError("M6B intervals must use the equal-tail method")
        if not self.interval.low <= self.median <= self.interval.high:
            raise ValueError("posterior median must lie inside its interval")
        probabilities = (
            self.probability_above_null,
            self.probability_below_null,
            self.probability_at_null,
        )
        if any(not 0.0 <= value <= 1.0 for value in probabilities):
            raise ValueError("posterior probabilities must lie within [0, 1]")
        if not isclose(sum(probabilities), 1.0, rel_tol=0.0, abs_tol=2e-12):
            raise ValueError("posterior direction probabilities must sum to one")


@dataclass(frozen=True, slots=True)
class BayesFactorSensitivity:
    """One predeclared prior-sensitivity Bayes factor."""

    label: str
    prior_value: float
    log_bf10: float

    def __post_init__(self) -> None:
        if self.label not in {"half", "double"}:
            raise ValueError("Bayes-factor sensitivity label is unsupported")
        _finite(self.prior_value, "sensitivity prior value")
        _finite(self.log_bf10, "sensitivity log BF10")
        if self.prior_value <= 0.0:
            raise ValueError("sensitivity prior value must be positive")


def bounded_bf10_text(log_bf10: float) -> str:
    """Create the approved bounded numeric BF10 representation."""

    _finite(log_bf10, "log BF10")
    bound = log(1e6)
    if log_bf10 > bound:
        return "BF10 > 1e6"
    if log_bf10 < -bound:
        return "BF10 < 1e-6"
    return f"BF10 = {exp(log_bf10):.6g}"


@dataclass(frozen=True, slots=True)
class BayesianEvidenceResult:
    """Numeric Bayes-factor evidence with fixed orientation."""

    null_hypothesis: str
    alternative_hypothesis: str
    sampling_plan: str
    log_bf10: float
    display: str
    prior_model_odds: float
    sensitivity: tuple[BayesFactorSensitivity, ...]

    def __post_init__(self) -> None:
        if not all(
            (
                self.null_hypothesis,
                self.alternative_hypothesis,
                self.sampling_plan,
            )
        ):
            raise ValueError("Bayes-factor hypotheses and sampling plan are required")
        _finite(self.log_bf10, "log BF10")
        if self.display != bounded_bf10_text(self.log_bf10):
            raise ValueError("Bayes-factor display is inconsistent with log BF10")
        if self.prior_model_odds != 1.0:
            raise ValueError("M6B prior model odds must equal one")
        if tuple(item.label for item in self.sensitivity) != ("half", "double"):
            raise ValueError("M6B requires half/double prior sensitivity")


@dataclass(frozen=True, slots=True)
class BayesianQmcTargetDiagnostic:
    """Per-target scrambled-Sobol acceptance evidence."""

    target_identity: str
    replicate_medians: tuple[float, ...]
    replicate_probabilities_above: tuple[float, ...]
    full_interval_low: float
    full_interval_high: float
    nested_interval_low: float
    nested_interval_high: float
    median_relative_se: float
    probability_absolute_se: float
    endpoint_relative_shift: float

    def __post_init__(self) -> None:
        if not self.target_identity:
            raise ValueError("QMC target identity is required")
        if (
            len(self.replicate_medians) != 8
            or len(self.replicate_probabilities_above) != 8
        ):
            raise ValueError("QMC target requires eight replicate estimates")
        numeric = (
            *self.replicate_medians,
            *self.replicate_probabilities_above,
            self.full_interval_low,
            self.full_interval_high,
            self.nested_interval_low,
            self.nested_interval_high,
            self.median_relative_se,
            self.probability_absolute_se,
            self.endpoint_relative_shift,
        )
        if any(not isfinite(value) for value in numeric):
            raise ValueError("QMC target diagnostics must be finite")
        if any(not 0.0 <= value <= 1.0 for value in self.replicate_probabilities_above):
            raise ValueError("QMC replicate probabilities are invalid")
        width = self.full_interval_high - self.full_interval_low
        if width < 0.0:
            raise ValueError("QMC diagnostic interval is reversed")
        probability_limit = 1e-4 if width == 0.0 else 0.005 * width
        if (
            self.median_relative_se > 0.005
            or self.probability_absolute_se > probability_limit
            or self.endpoint_relative_shift > 0.01
        ):
            raise ValueError("QMC target stability threshold failed")


@dataclass(frozen=True, slots=True)
class BayesianComputationResult:
    """Bounded numerical computation and diagnostic provenance."""

    algorithm: str
    evaluations: int
    absolute_tolerance: float | None
    relative_tolerance: float | None
    estimated_error: float | None
    calculated_work: int
    maximum_work: int
    hard_maximum_work: int
    root_seed: int | None
    diagnostics: tuple[str, ...]
    qmc_dimension: int | None = None
    qmc_replicates: int | None = None
    qmc_points_per_replicate: int | None = None
    child_seeds: tuple[int, ...] = ()
    replicate_max_relative_se: float | None = None
    nested_max_relative_shift: float | None = None
    qmc_targets: tuple[BayesianQmcTargetDiagnostic, ...] = ()

    def __post_init__(self) -> None:
        if self.algorithm not in {
            "closed_form_normal_inverse_gamma",
            "adaptive_gauss_kronrod_correlation",
            "closed_form_dirichlet_multinomial",
            "scrambled_sobol_conjugate_posterior",
        }:
            raise ValueError("Bayesian computation algorithm is unsupported")
        if self.evaluations < 0 or self.calculated_work < 1:
            raise ValueError("Bayesian computation counts are invalid")
        if not (
            self.calculated_work
            <= self.maximum_work
            <= self.hard_maximum_work
            == 500_000_000
        ):
            raise ValueError("Bayesian work ceilings are inconsistent")
        tolerance_values = (
            self.absolute_tolerance,
            self.relative_tolerance,
            self.estimated_error,
        )
        if any(
            value is not None and (not isfinite(value) or value < 0.0)
            for value in tolerance_values
        ):
            raise ValueError("Bayesian tolerances/errors must be finite non-negative")
        if self.algorithm == "adaptive_gauss_kronrod_correlation":
            if (
                self.absolute_tolerance != 1e-12
                or self.relative_tolerance != 1e-10
                or self.estimated_error is None
                or self.evaluations < 1
                or self.calculated_work != self.evaluations
            ):
                raise ValueError("correlation quadrature provenance is incomplete")
        elif any(value is not None for value in tolerance_values):
            raise ValueError("non-quadrature computation must not claim tolerances")
        if self.root_seed is not None and not 0 <= self.root_seed <= 2**64 - 1:
            raise ValueError("Bayesian root seed must be unsigned 64-bit")
        if any(not diagnostic for diagnostic in self.diagnostics):
            raise ValueError("Bayesian diagnostics must not be empty")
        qmc_values = (
            self.qmc_dimension,
            self.qmc_replicates,
            self.qmc_points_per_replicate,
        )
        if self.algorithm == "scrambled_sobol_conjugate_posterior":
            if (
                any(value is None or value < 1 for value in qmc_values)
                or self.qmc_replicates != 8
                or self.qmc_points_per_replicate != 4096
                or len(self.child_seeds) != 8
                or self.root_seed is None
                or self.replicate_max_relative_se is None
                or self.nested_max_relative_shift is None
                or not self.qmc_targets
            ):
                raise ValueError("scrambled Sobol provenance is incomplete")
            assert self.qmc_dimension is not None
            assert self.qmc_replicates is not None
            assert self.qmc_points_per_replicate is not None
            if (
                self.evaluations != self.qmc_replicates * self.qmc_points_per_replicate
                or self.calculated_work != self.evaluations * self.qmc_dimension
                or len(set(self.child_seeds)) != 8
                or len({item.target_identity for item in self.qmc_targets})
                != len(self.qmc_targets)
                or not isclose(
                    self.replicate_max_relative_se,
                    max(item.median_relative_se for item in self.qmc_targets),
                    rel_tol=0.0,
                    abs_tol=1e-15,
                )
                or not isclose(
                    self.nested_max_relative_shift,
                    max(item.endpoint_relative_shift for item in self.qmc_targets),
                    rel_tol=0.0,
                    abs_tol=1e-15,
                )
            ):
                raise ValueError("scrambled Sobol work/diagnostics are inconsistent")
        elif (
            any(value is not None for value in qmc_values)
            or self.child_seeds
            or self.replicate_max_relative_se is not None
            or self.nested_max_relative_shift is not None
            or self.qmc_targets
        ):
            raise ValueError("non-QMC computation must not claim QMC provenance")


@dataclass(frozen=True, slots=True)
class BayesianOneSampleResult:
    """Schema-v3 one-sample Bayesian result."""

    schema_version: int
    analysis: str
    mode: str
    column: str
    sample: SampleAudit
    method: BayesianMethodResult
    prior: BayesianPriorResult
    location: BayesianPosteriorSummary
    effect: BayesianPosteriorSummary
    evidence: BayesianEvidenceResult
    computation: BayesianComputationResult
    limits: ResourceLimits
    warnings: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.schema_version != 3 or self.mode != "bayes":
            raise ValueError("Bayesian one-sample result requires schema v3/bayes")
        if self.analysis not in {
            "gghistostats_one_sample_bayesian",
            "ggdotplotstats_one_sample_bayesian",
        }:
            raise ValueError("Bayesian one-sample analysis identity is unsupported")
        if (
            self.method.name != "conjugate_normal_location"
            or self.prior.family != "standardized_normal_inverse_gamma"
            or self.computation.algorithm != "closed_form_normal_inverse_gamma"
        ):
            raise ValueError("Bayesian one-sample method provenance is inconsistent")
        if not self.column or self.sample.analyzed_rows < 3:
            raise ValueError("Bayesian one-sample identity/sample is invalid")
        if self.location.target != "population_mean":
            raise ValueError("Bayesian one-sample location target is unsupported")
        if self.effect.target != "population_mean_difference":
            raise ValueError("Bayesian one-sample effect target is unsupported")
        if not isclose(
            self.location.median - self.location.null_value,
            self.effect.median,
            rel_tol=1e-12,
            abs_tol=1e-12,
        ):
            raise ValueError("Bayesian one-sample location/effect are inconsistent")
        if any(not warning for warning in self.warnings):
            raise ValueError("Bayesian warnings must not be empty")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class BayesianDotEstimateResult:
    """One label-level Bayesian location and evidence record."""

    label: ScalarIdentity
    sample: SampleAudit
    posterior: BayesianPosteriorSummary
    evidence: BayesianEvidenceResult
    computation: BayesianComputationResult
    warnings: tuple[str, ...]

    def __post_init__(self) -> None:
        if isinstance(self.label, str) and not self.label:
            raise ValueError("Bayesian dot label must be non-empty")
        if isinstance(self.label, float) and not isfinite(self.label):
            raise ValueError("Bayesian numeric dot label must be finite")
        if self.sample.analyzed_rows < 3:
            raise ValueError("Bayesian dot label requires at least three rows")
        if self.computation.algorithm != "closed_form_normal_inverse_gamma":
            raise ValueError("Bayesian dot computation provenance is inconsistent")
        if self.posterior.target != "population_mean":
            raise ValueError("Bayesian dot estimate target is unsupported")
        if any(not warning for warning in self.warnings):
            raise ValueError("Bayesian dot warnings must not be empty")

    @property
    def value(self) -> float:
        return self.posterior.median

    @property
    def interval(self) -> IntervalResult:
        return self.posterior.interval


@dataclass(frozen=True, slots=True)
class BayesianDotPlotResult:
    """Schema-v3 Bayesian labeled-dot result."""

    schema_version: int
    analysis: str
    mode: str
    x: str
    label_column: str
    sample: SampleAudit
    method: BayesianMethodResult
    prior: BayesianPriorResult
    one_sample: BayesianOneSampleResult
    estimates: tuple[BayesianDotEstimateResult, ...]
    limits: ResourceLimits
    warnings: tuple[str, ...]

    def __post_init__(self) -> None:
        if (
            self.schema_version != 3
            or self.mode != "bayes"
            or self.analysis != "ggdotplotstats_one_sample_bayesian"
        ):
            raise ValueError("Bayesian dot result identity is unsupported")
        if not self.x or not self.label_column or self.x == self.label_column:
            raise ValueError("Bayesian dot columns are invalid")
        if self.sample != self.one_sample.sample or not self.estimates:
            raise ValueError("Bayesian dot overall sample/result is inconsistent")
        if (
            self.method.name != "conjugate_normal_labeled_location"
            or self.prior != self.one_sample.prior
        ):
            raise ValueError("Bayesian dot method provenance is inconsistent")
        if self.one_sample.analysis != self.analysis:
            raise ValueError("Bayesian dot one-sample identity is inconsistent")
        identities = tuple((type(item.label), item.label) for item in self.estimates)
        if len(identities) != len(set(identities)):
            raise ValueError("Bayesian dot labels must be unique")
        if tuple(item.value for item in self.estimates) != tuple(
            sorted(item.value for item in self.estimates)
        ):
            raise ValueError("Bayesian dot estimates must be sorted by median")
        if any(not warning for warning in self.warnings):
            raise ValueError("Bayesian dot warnings must not be empty")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class BayesianCorrelationResult:
    """Schema-v3 Bayesian Pearson-correlation result."""

    schema_version: int
    analysis: str
    mode: str
    x: str
    y: str
    sample: SampleAudit
    method: BayesianMethodResult
    prior: BayesianPriorResult
    posterior: BayesianPosteriorSummary
    evidence: BayesianEvidenceResult
    computation: BayesianComputationResult
    sample_correlation: float
    limits: ResourceLimits
    warnings: tuple[str, ...]

    def __post_init__(self) -> None:
        if (
            self.schema_version != 3
            or self.mode != "bayes"
            or self.analysis != "ggscatterstats_bayesian_pearson"
        ):
            raise ValueError("Bayesian correlation result identity is unsupported")
        if not self.x or not self.y or self.x == self.y:
            raise ValueError("Bayesian correlation columns are invalid")
        if self.sample.analyzed_rows < 4:
            raise ValueError("Bayesian correlation requires at least four pairs")
        _finite(self.sample_correlation, "sample correlation")
        if not -1.0 < self.sample_correlation < 1.0:
            raise ValueError("Bayesian sample correlation must be inside (-1, 1)")
        if self.posterior.target != "population_pearson_rho":
            raise ValueError("Bayesian correlation target is unsupported")
        if (
            self.method.name != "exact_sample_correlation"
            or self.prior.family != "symmetric_beta_transformed_correlation"
            or self.computation.algorithm != "adaptive_gauss_kronrod_correlation"
        ):
            raise ValueError("Bayesian correlation method provenance is inconsistent")
        if any(not warning for warning in self.warnings):
            raise ValueError("Bayesian warnings must not be empty")

    @property
    def estimate(self) -> float:
        return self.posterior.median

    @property
    def interval(self) -> IntervalResult:
        return self.posterior.interval

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class BayesianCorrelationMatrixCell:
    """One directed cell in a Bayesian correlation matrix."""

    x: str
    y: str
    n_obs: int
    posterior: BayesianPosteriorSummary | None
    evidence: BayesianEvidenceResult | None

    def __post_init__(self) -> None:
        if not self.x or not self.y or self.n_obs < 1:
            raise ValueError("Bayesian matrix cell identity is invalid")
        diagonal = self.x == self.y
        if (diagonal and (self.posterior is not None or self.evidence is not None)) or (
            not diagonal and (self.posterior is None or self.evidence is None)
        ):
            raise ValueError("Bayesian matrix diagonal/off-diagonal fields conflict")
        if (
            self.posterior is not None
            and self.posterior.target != "population_pearson_rho"
        ):
            raise ValueError("Bayesian matrix posterior target is unsupported")

    @property
    def estimate(self) -> float:
        return 1.0 if self.posterior is None else self.posterior.median

    @property
    def significant(self) -> None:
        return None


@dataclass(frozen=True, slots=True)
class BayesianCorrelationMatrixResult:
    """Schema-v3 complete pointwise Bayesian correlation matrix."""

    schema_version: int
    analysis: str
    mode: str
    columns: tuple[str, ...]
    method: BayesianMethodResult
    prior: BayesianPriorResult
    cells: tuple[BayesianCorrelationMatrixCell, ...]
    evidence_scope: str
    calculated_bayesian_work: int
    maximum_bayesian_work: int
    limits: ResourceLimits
    warnings: tuple[str, ...]

    def __post_init__(self) -> None:
        if (
            self.schema_version != 3
            or self.mode != "bayes"
            or self.analysis != "ggcorrmat_bayesian_pearson"
        ):
            raise ValueError("Bayesian matrix result identity is unsupported")
        if not 2 <= len(self.columns) <= 50 or len(set(self.columns)) != len(
            self.columns
        ):
            raise ValueError("Bayesian matrix columns are invalid")
        if len(self.cells) != len(self.columns) ** 2:
            raise ValueError("Bayesian matrix must contain every directed cell")
        expected = tuple((x, y) for x in self.columns for y in self.columns)
        if tuple((cell.x, cell.y) for cell in self.cells) != expected:
            raise ValueError("Bayesian matrix cell order is invalid")
        if self.evidence_scope != "pointwise_no_multiplicity_adjustment":
            raise ValueError("Bayesian matrix evidence scope is unsupported")
        if (
            self.method.name != "exact_sample_correlation_matrix"
            or self.prior.family != "symmetric_beta_transformed_correlation"
        ):
            raise ValueError("Bayesian matrix method provenance is inconsistent")
        if not (
            1
            <= self.calculated_bayesian_work
            <= self.maximum_bayesian_work
            <= 500_000_000
        ):
            raise ValueError("Bayesian matrix work is invalid")
        if any(not warning for warning in self.warnings):
            raise ValueError("Bayesian matrix warnings must not be empty")

    @property
    def p_adjust(self) -> str:
        return "none"

    @property
    def sig_level(self) -> float:
        return 0.05

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class BayesianComparisonLevelResult:
    """One condition mean from an approved Bayesian comparison."""

    level: ScalarIdentity
    n_obs: int
    posterior: BayesianPosteriorSummary

    def __post_init__(self) -> None:
        if self.n_obs < 3 or self.posterior.target != "population_mean":
            raise ValueError("Bayesian comparison level is invalid")

    @property
    def mean(self) -> float:
        return self.posterior.median

    @property
    def interval(self) -> IntervalResult:
        return self.posterior.interval


@dataclass(frozen=True, slots=True)
class BayesianPairwiseComparisonResult:
    """One pointwise posterior contrast and its numeric evidence."""

    left: ScalarIdentity
    right: ScalarIdentity
    posterior: BayesianPosteriorSummary
    evidence: BayesianEvidenceResult

    def __post_init__(self) -> None:
        if (type(self.left), self.left) == (type(self.right), self.right):
            raise ValueError("Bayesian contrast levels must differ")
        if self.posterior.target != "population_mean_difference":
            raise ValueError("Bayesian comparison contrast target is unsupported")


@dataclass(frozen=True, slots=True)
class BayesianComparisonResult:
    """Schema-v3 Bayesian independent or complete-block comparison."""

    schema_version: int
    analysis: str
    mode: str
    design: str
    x: str
    y: str
    subject_id: str | None
    sample: SampleAudit | RepeatedSampleAudit
    method: BayesianMethodResult
    prior: BayesianPriorResult
    levels: tuple[BayesianComparisonLevelResult, ...]
    omnibus: BayesianEvidenceResult
    pairwise: tuple[BayesianPairwiseComparisonResult, ...]
    computation: BayesianComputationResult
    credible_level: float
    pairwise_display: str
    limits: ResourceLimits
    warnings: tuple[str, ...]

    def __post_init__(self) -> None:
        expected = {
            "between": "ggbetweenstats_bayesian_homoscedastic",
            "within": "ggwithinstats_bayesian_complete_block",
        }
        if (
            self.schema_version != 3
            or self.mode != "bayes"
            or expected.get(self.design) != self.analysis
            or not self.x
            or not self.y
            or self.x == self.y
        ):
            raise ValueError("Bayesian comparison identity is unsupported")
        if (self.design == "within") != (self.subject_id is not None):
            raise ValueError("Bayesian comparison subject identity is inconsistent")
        expected_method = {
            "between": "homoscedastic_cell_means_nig",
            "within": "complete_block_helmert_compound_symmetry",
        }
        if (
            self.method.name != expected_method[self.design]
            or self.prior.family != "standardized_normal_inverse_gamma"
            or self.computation.algorithm != "scrambled_sobol_conjugate_posterior"
        ):
            raise ValueError("Bayesian comparison method provenance is inconsistent")
        if not 2 <= len(self.levels) <= 20:
            raise ValueError("Bayesian comparison requires 2-20 levels")
        identities = tuple((type(item.level), item.level) for item in self.levels)
        if len(identities) != len(set(identities)):
            raise ValueError("Bayesian comparison levels must be unique")
        if not 0.80 <= self.credible_level <= 0.99 or any(
            item.posterior.interval.level != self.credible_level for item in self.levels
        ):
            raise ValueError("Bayesian comparison credible level is inconsistent")
        if isinstance(self.sample, SampleAudit):
            if (
                self.design != "between"
                or sum(item.n_obs for item in self.levels) != self.sample.analyzed_rows
            ):
                raise ValueError("Bayesian between-group sample does not reconcile")
        elif self.design != "within" or any(
            item.n_obs != self.sample.analyzed_subjects for item in self.levels
        ):
            raise ValueError("Bayesian repeated sample does not reconcile")
        if len(self.pairwise) != len(self.levels) * (len(self.levels) - 1) // 2:
            raise ValueError("Bayesian comparison contrast family is incomplete")
        expected_pairs = tuple(
            (self.levels[left].level, self.levels[right].level)
            for left in range(len(self.levels))
            for right in range(left + 1, len(self.levels))
        )
        if tuple((item.left, item.right) for item in self.pairwise) != expected_pairs:
            raise ValueError("Bayesian comparison contrast order is inconsistent")
        if any(
            item.posterior.interval.level != self.credible_level
            for item in self.pairwise
        ):
            raise ValueError("Bayesian contrast credible level is inconsistent")
        if self.pairwise_display not in {"all", "none"}:
            raise ValueError("Bayesian pairwise display must be 'all' or 'none'")
        if any(not warning for warning in self.warnings):
            raise ValueError("Bayesian warnings must not be empty")

    @property
    def p_adjust(self) -> str:
        return "none"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class BayesianCategoricalCellResult:
    """Observed categorical cell with its posterior probability."""

    x_level: ScalarIdentity
    y_level: ScalarIdentity | None
    observed: int
    displayed_proportion: float
    joint_proportion: float
    posterior: BayesianPosteriorSummary

    def __post_init__(self) -> None:
        if type(self.observed) is not int or self.observed < 0:
            raise ValueError("Bayesian categorical count must be non-negative")
        if not all(
            isfinite(value) and 0.0 <= value <= 1.0
            for value in (self.displayed_proportion, self.joint_proportion)
        ):
            raise ValueError("Bayesian categorical proportions are invalid")
        if self.posterior.target != "cell_probability":
            raise ValueError("Bayesian categorical cell target is unsupported")


@dataclass(frozen=True, slots=True)
class BayesianCategoricalContrastResult:
    """One stable row-pair probability contrast within a category."""

    left: ScalarIdentity
    right: ScalarIdentity
    category: ScalarIdentity
    posterior: BayesianPosteriorSummary

    def __post_init__(self) -> None:
        if (type(self.left), self.left) == (type(self.right), self.right):
            raise ValueError("Bayesian categorical contrast rows must differ")
        if self.posterior.target != "cell_probability_difference":
            raise ValueError("Bayesian categorical contrast target is unsupported")


@dataclass(frozen=True, slots=True)
class BayesianCategoricalResult:
    """Schema-v3 Bayesian one-way or fixed-row categorical analysis."""

    schema_version: int
    analysis: str
    mode: str
    design: str
    x: str
    y: str | None
    counts: str | None
    sample: CategoricalSampleAudit
    x_levels: tuple[ScalarIdentity, ...]
    y_levels: tuple[ScalarIdentity, ...]
    cells: tuple[BayesianCategoricalCellResult, ...]
    contrasts: tuple[BayesianCategoricalContrastResult, ...]
    row_totals: tuple[int, ...]
    column_totals: tuple[int, ...]
    ratio: tuple[float, ...] | None
    method: BayesianMethodResult
    prior: BayesianPriorResult
    omnibus: BayesianEvidenceResult
    effect: BayesianPosteriorSummary | None
    computation: BayesianComputationResult
    credible_level: float
    pairwise_display: str
    proportion_test: bool
    limits: ResourceLimits
    warnings: tuple[str, ...]

    def __post_init__(self) -> None:
        expected = {
            "one_way": "categorical_bayesian_fixed_total",
            "independent": "categorical_bayesian_fixed_rows",
        }
        if (
            self.schema_version != 3
            or self.mode != "bayes"
            or expected.get(self.design) != self.analysis
        ):
            raise ValueError("Bayesian categorical identity is unsupported")
        if not self.x or self.y == self.x or self.counts in {self.x, self.y}:
            raise ValueError("Bayesian categorical columns are invalid")
        if self.design == "one_way" and (self.y is not None or self.y_levels):
            raise ValueError("Bayesian one-way result cannot contain y levels")
        if self.design == "independent" and (self.y is None or len(self.y_levels) < 2):
            raise ValueError("Bayesian fixed-row result requires y levels")
        expected_method = {
            "one_way": "dirichlet_multinomial_fixed_total",
            "independent": "dirichlet_multinomial_fixed_rows",
        }
        expected_algorithm = (
            "closed_form_dirichlet_multinomial"
            if self.design == "one_way"
            else "scrambled_sobol_conjugate_posterior"
        )
        if (
            self.method.name != expected_method[self.design]
            or self.prior.family != "exchangeable_dirichlet_multinomial"
            or self.computation.algorithm != expected_algorithm
        ):
            raise ValueError("Bayesian categorical method provenance is inconsistent")
        if not 2 <= len(self.x_levels) <= 20:
            raise ValueError("Bayesian categorical result requires 2-20 x levels")
        x_keys = tuple((type(level), level) for level in self.x_levels)
        y_keys = tuple((type(level), level) for level in self.y_levels)
        if len(x_keys) != len(set(x_keys)) or len(y_keys) != len(set(y_keys)):
            raise ValueError("Bayesian categorical levels must be unique")
        width = max(1, len(self.y_levels))
        if len(self.cells) != len(self.x_levels) * width:
            raise ValueError("Bayesian categorical cell family is incomplete")
        expected_cells = tuple(
            (x_level, None if self.design == "one_way" else y_level)
            for x_level in self.x_levels
            for y_level in (self.y_levels or (None,))
        )
        if tuple((cell.x_level, cell.y_level) for cell in self.cells) != expected_cells:
            raise ValueError("Bayesian categorical cell order is inconsistent")
        expected_contrasts = (
            0
            if self.design == "one_way"
            else len(self.x_levels) * (len(self.x_levels) - 1) // 2 * len(self.y_levels)
        )
        if len(self.contrasts) != expected_contrasts:
            raise ValueError("Bayesian categorical contrast family is incomplete")
        observed = tuple(cell.observed for cell in self.cells)
        computed_rows = tuple(
            sum(observed[start : start + width])
            for start in range(0, len(observed), width)
        )
        if (
            self.row_totals != computed_rows
            or sum(self.row_totals) != self.sample.weighted_total
        ):
            raise ValueError("Bayesian categorical totals do not reconcile")
        computed_columns = tuple(sum(observed[index::width]) for index in range(width))
        if self.column_totals != (() if self.design == "one_way" else computed_columns):
            raise ValueError("Bayesian categorical column totals do not reconcile")
        if self.design == "one_way":
            if (
                self.ratio is None
                or len(self.ratio) != len(self.x_levels)
                or any(value <= 0.0 or not isfinite(value) for value in self.ratio)
                or not isclose(sum(self.ratio), 1.0, rel_tol=0.0, abs_tol=1e-12)
            ):
                raise ValueError("Bayesian fixed-total ratio is invalid")
            if self.effect is not None:
                raise ValueError("Bayesian one-way result has no scalar global effect")
        elif (
            self.ratio is not None
            or self.effect is None
            or self.effect.target != "cramers_v"
        ):
            raise ValueError("Bayesian fixed-row effect/ratio is inconsistent")
        if not 0.80 <= self.credible_level <= 0.99 or any(
            cell.posterior.interval.level != self.credible_level for cell in self.cells
        ):
            raise ValueError("Bayesian categorical credible level is inconsistent")
        if self.pairwise_display not in {"all", "none"}:
            raise ValueError("Bayesian pairwise display must be 'all' or 'none'")
        if any(not warning for warning in self.warnings):
            raise ValueError("Bayesian warnings must not be empty")

    @property
    def p_adjust(self) -> str:
        return "none"

    @property
    def conf_level(self) -> float:
        return self.credible_level

    @property
    def pairwise(self) -> tuple[()]:
        return ()

    @property
    def strata(self) -> tuple[()]:
        return ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
