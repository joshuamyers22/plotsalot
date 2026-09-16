# 1.x API and Schema Stability Policy

- Status: accepted by M7-D3 on 2026-09-15
- Applies from: the first accepted 1.0 release
- Owner: Joshua Myers

## Purpose

This policy defines what downstream users may rely on during the 1.x series and
what remains implementation detail. It does not retroactively declare every
pre-1.0 behavior stable. M7 must inventory the exact 1.0 candidate and publish
any migration required from `0.1.1` before the first 1.0 release is accepted.

## Versioning rules

Plotsalot follows semantic versioning for the Python distribution:

- A patch release fixes defects, documentation, packaging, numerical stability,
  or security issues without intentionally changing a supported public contract.
- A minor release may add public names, keyword-only parameters with compatible
  defaults, result variants, schema versions, plot layers, or supported methods.
  Existing supported calls and serialized variants continue to work.
- A major release may remove or incompatibly change a supported public contract
  after the deprecation process, except when immediate removal is required to
  address an actively exploitable security or scientific-correctness defect.

Changing an estimator, estimand, prior, interval, correction family,
missingness population, RNG identity, fallback policy, or evidence direction is
never treated as a patch solely because the Python signature is unchanged.

## Stable public surface

After 1.0, the following are stable when documented and included in the M7 API
manifest:

- importable names exported through `plotsalot.__all__`;
- installed console-script names, documented arguments, exit-status meanings,
  and machine-readable output contracts;
- public function and method parameter names, kinds, defaults, accepted literal
  selectors, return types, and documented exceptions or stable error codes;
- documented public dataclasses, protocols, enum/literal values, properties, and
  result/container field meanings;
- the semantic meaning of statistical outputs, audit fields, provenance,
  warnings, limits, and refusal behavior;
- documented `StatsPlot` axes keys, semantic layer identities, extraction
  behavior, grouped identity, and composition result identity; and
- serialized `to_dict()` variants and their matching versioned JSON schemas.

Names imported only from internal modules, leading-underscore names, test
helpers, oracle/benchmark tools, and undocumented object internals are not
public merely because Python permits access to them.

## Experimental public surface

An explicitly experimental feature may remain importable in 1.0 without
receiving the stable statistical and serialized-result promise above. Its call
selector, dedicated types, schema branch, rationale, and owner approval must be
listed in the machine-readable M7 compatibility ledger and generated public
manifest. Experimental status is not permission for silent fallback, uncoded
failure, unbounded work, or misleading documentation.

The sole 1.0 exception is fixed-Student-t4 robust aggregate meta-analysis,
selected by `meta_analytic_effect=True, type="robust"`. The containing
`ggcoefstats`, `analyze_ggcoefstats`, and `render_ggcoefstats` names remain stable
for supported non-experimental modes. The seven dedicated `RobustMeta*` public
types and the schema-v2 robust-meta result variant remain available but are not
promised compatible across 1.x minor releases. A change or removal must still
be documented with recovery or reanalysis guidance, but does not require the
normal stable-surface deprecation window.

## Serialized-result rules

Stable serialized results use an explicit schema discriminator. M7 must retain
a golden example for every supported variant and validate it against the
matching schema. Experimental variants are retained and tested separately but
do not acquire stable-variant status merely by sharing a schema file.

- A published schema file is immutable. Correcting it requires a new schema
  version rather than silently changing the meaning accepted by an old version.
- Removing or renaming a field, changing its type or units, tightening a value
  domain, changing nullability, or changing a discriminator requires a new
  schema version and migration guidance.
- Adding a field also requires a new schema version when the prior schema uses
  `additionalProperties: false` or an exhaustive consumer could otherwise
  reject the result.
- Existing schema files and golden fixtures remain in the repository for the
  supported migration window even after the library emits a newer version.
- A result may not claim an older schema version while emitting the semantics of
  a newer estimator, interval, prior, or audit population.

Plotsalot currently guarantees JSON-safe output, not a universal deserializer.
If a public deserializer is added, its accepted historical versions and failure
behavior require a separate compatibility contract.

## Statistical compatibility

For a supported mode, compatibility includes more than numeric proximity. The
following remain stable within 1.x unless a major release or approved emergency
correction says otherwise:

- observation unit, retained population, exclusions, missingness, pairing, and
  identity rules;
- estimator and effect target, null/reference value, sidedness, correction
  family, interval target and level, and reference distribution;
- prior and likelihood parameterization, Bayes-factor orientation, sensitivity
  set, computation engine, and diagnostic/failure thresholds;
- randomness ownership, deterministic stream derivation, work accounting, and
  retry/fallback prohibition; and
- result-field units, scale, warning meaning, and renderer annotation mapping.

A scientifically incorrect contract may be corrected before a major release,
but the release must identify the defect, affected versions, migration or
reanalysis need, and why retaining compatibility would be unsafe.

## Rendering compatibility

Stable rendering is semantic rather than pixel-identical. Documented axes keys,
layer roles, result-to-annotation mappings, extraction, and composition identity
are stable. Exact artist coordinates, padding, font metrics, colors, anti-
aliasing, backend output, and image pixels may change in compatible releases
unless explicitly frozen by a narrower visual contract.

Plotsalot does not promise compatibility with arbitrary mutation of undocumented
Matplotlib artists or global `rcParams` state.

## Errors, warnings, and resource limits

Documented exception classes and machine-readable error/warning codes are
stable. Exact human-readable message prose is not stable. M7 must identify any
public failure that currently relies only on message matching and either assign
a stable type/code or explicitly leave it outside the 1.0 compatibility promise.

Default resource limits may become more conservative in a minor release when
needed to prevent denial of service or unbounded work, provided the change is
documented and an explicit safe override remains where appropriate. Hard limits,
atomic failure, and the prohibition on silent input/work reduction remain part
of the public contract.

## Python, platforms, and dependencies

- Raising the minimum Python version or removing a supported operating system
  occurs only in a minor or major release with advance notice and migration
  guidance; never in a patch release except for an urgent security constraint.
- Compatible dependency-bound changes may occur in patch releases. A dependency
  change that alters public object types, numerical semantics, installation
  extras, or platform coverage requires minor-version treatment and evidence.
- R, Docker, network access, and oracle repositories remain excluded from
  released runtime requirements throughout 1.x.

## Deprecation and removal

Normal removal requires all of the following:

1. a documented replacement or explicit explanation that no replacement is
   safe;
2. a runtime deprecation warning at the public call boundary when feasible;
3. changelog and migration-guide entries with affected names and behavior;
4. at least one minor release and 90 days between first deprecation and removal,
   whichever is longer; and
5. a major release for the removal itself.

Security, privacy, legal, or scientific-correctness emergencies may bypass that
window. The exception requires an accountable decision record, affected-version
notice, recovery guidance, and a patch/minor release chosen according to the
smallest safe response.

## M7 implementation evidence

Before the first 1.0 release is accepted, M7 must produce:

- a generated public-name/signature manifest reviewed against documentation
  (all 144 root names classified; 137 stable and seven experimental after M7B);
- a console-script and exit-contract inventory (included in that manifest);
- golden serialized examples for every emitted result variant;
- schema validation and mutation tests for field, type, discriminator, and
  unknown-property failures;
- semantic plot/axes/extraction/composition contract tests;
- an error/refusal inventory that separates stable types/codes from prose;
- a `0.1.1` to 1.0 migration document, including an explicit “no change” entry
  for every reviewed boundary that remains compatible (M7A baseline added;
  final-candidate update still required); and
- the M7-D3 owner approval recorded in the milestone and ADR.
