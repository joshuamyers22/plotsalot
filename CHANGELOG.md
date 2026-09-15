# Changelog

## Unreleased

- Created the `plotsalot` production repository and M0 planning/evidence records.
- Added the initial parametric `gghistostats` walking skeleton with structured,
  extractable results and a Matplotlib renderer.
- Added M1 shared contracts: a reusable Polars-to-NumPy numeric boundary,
  renderer-independent histogram analysis, reusable rendering, generic typed
  plot/result extraction, validated named axes, and immutable annotations.
- Added the lockfile-driven R 4.5.1 oracle for pinned ggstatsplot fixtures,
  SHA-256 integrity checks, and explicit upstream/adapted behavior records.
- Added retained 10K/100K/1M-row analysis/render timing and incremental
  peak-allocation distributions, with artifact checks in the unit gate.
- Adopted the MIT license and limited the upstream compatibility scope to
  ggstatsplot in ADR-010.
- Added the detailed M2 contract for frequentist univariate, correlation,
  grouped-result, oracle, benchmark, and production acceptance gates.
- Recorded Joshua Myers's approval of the pinned-source M2 statistical methods.
- Added labeled dot plots, Pearson scatter plots, pairwise-complete Pearson
  correlation matrices with Holm adjustment, and atomic grouped variants with
  typed JSON-safe results and semantic Matplotlib renderers.
- Added M2 resource ceilings, preserved scalar group identities, result schemas,
  analytic/independent checks, and focused contract/failure tests.
- Added pinned-R M2 oracle fixtures and the retained scatter/matrix performance
  grid with five separate analysis and render measurements per workload.
- Completed M2 after the full production gate, adversarial finding disposition,
  independent review, and Joshua Myers's final milestone approval.
- Added the detailed M3 contract, separating the M3A independent-group and
  `0.1` composition/theme gate from the M3B repeated-measures and `0.2` gate,
  with explicit method-approval, pairing, multiplicity, evidence, resource, and
  sign-off requirements.
- Added the approval-ready M3 classical method proposal and pending accountable
  sign-off records for independent-group and repeated-measures tracks.
- Recorded Joshua Myers's approval of the M3 classical comparison methods.
- Added typed independent and explicit-subject repeated comparison samples,
  Welch/paired/repeated analyses, full Holm families, Greenhouse–Geisser
  metadata, semantic renderers, and atomic grouped variants.
- Added result-preserving plot composition with shared labels and deterministic
  tags, immutable local theming, M3 result schemas, pinned-R fixtures, and the
  retained row/level/subject/condition/composition performance grid.
- Completed M3A and M3B after the full production gate, adversarial finding
  disposition, independent review, and Joshua Myers's final milestone approval.
- Added the detailed M4 contract for raw and count-weighted categorical tables,
  one-way/independent/paired designs, shared bar/pie analysis, follow-up
  families, grouped execution, resource bounds, evidence, and `0.2` acceptance.
- Added the approval-ready M4 classical categorical method proposal and pending
  accountable sign-off record for C1–C5/G5.
- Recorded Joshua Myers's approval of the M4 classical categorical methods.
- Added owned raw/count-weighted categorical tables, one-way, independent, and
  exact binary paired analyses, noncentral effect intervals, complete pairwise
  and stratum Holm families, and schema-v1 categorical results.
- Added semantic normalized bars, faceted pies, atomic grouped categorical
  variants, stable cross-group colors, extraction/composition coverage, and
  explicit categorical resource ceilings.
- Added pinned-R C1–C5 oracle fixtures, analytic and failure-path tests, M4
  compatibility documentation, and the categorical performance workload grid.
- Completed M4 after the full production gate, adversarial finding disposition,
  independent review, and Joshua Myers's final approval, closing the `0.2`
  product gate.
- Added the detailed M5 contract for strict coefficient tables, approved fitted-
  Statsmodels adapters, semantic dot-and-whisker rendering, frequentist random-
  effects meta-analysis, explicit method gates, and `0.3` acceptance.
- Added the approval-ready M5A K1–K4 coefficient-method proposal and pending
  accountable sign-off/verification records; implementation remains stopped at
  the required statistical-review gate.
- Recorded Joshua Myers's approval of the M5A coefficient methods without
  revision, authorizing implementation while MA1–MA4 remain pending for M5B.
- Added the approval-ready M5B MA1–MA4 proposal and pending accountable records
  for strict study effects, REML heterogeneity, modified Hartung–Knapp pooled
  inference, prediction intervals, and explicit no-fallback boundaries.
- Recorded Joshua Myers's approval of the M5B meta-analysis methods without
  revision, authorizing implementation while release acceptance remains pending.
- Added the M5B technical core: immutable study-effect input, deterministic
  intercept-only REML, modified Hartung–Knapp pooled inference, prediction
  intervals, Q/I-squared/tau heterogeneity, and schema-v1 coefficient results.
- Added the explicit meta-analysis `ggcoefstats` forest renderer, extraction and
  composition coverage, independent likelihood/analytic tests, resource and
  failure guards, and a retained 3/10/100/500-study performance grid.
- Added pinned-R M5B evidence: a raw ggstatsplot meta object, an independently
  solved base-R REML/modified-Hartung–Knapp reference, and pinned metafor
  normal/modified-Hartung–Knapp comparison values.
- Recorded Joshua Myers's independent review and acceptance of the M5B technical
  candidate; M5A and the combined M5/`0.3` gate remain open.
- Added M5A estimate-only, interval, full-t, and full-z coefficient tables;
  structured identity and intercept audits; and exact fitted Statsmodels OLS
  adaptation for nonrobust and HC3 covariance.
- Extended schema-v1 results and `ggcoefstats` rendering across coefficient and
  meta-analysis modes, with pinned-R/base-R OLS evidence, adversarial tests, and
  a retained 10/100/500-term plus model-adapter benchmark.
- Recorded Joshua Myers's independent M5A review, M5A acceptance, and final
  combined M5/`0.3` approval after the complete production gate, closing M5.
- Added the detailed M6 contract with separate robust, Bayesian, and
  coefficient/meta closeout tracks; explicit ADR/method-approval gates;
  stochastic reproducibility, diagnostic, optional-dependency, resource,
  oracle/calibration, performance, and `0.4` acceptance requirements.
- Prepared the M6A ADR-005/ADR-006 architecture proposals and R1–R3/G6 robust
  method proposal, accountable sign-off, entry findings, and verification loop;
  Joshua Myers approved the entry decisions without revision on 2026-09-14,
  authorizing M6A implementation while R4/B1–B6 and release acceptance remain
  separate gates.
- Implemented the M6A robust continuous-analysis candidate across histogram,
  labeled-dot, scatter, correlation-matrix, independent/repeated comparison,
  and existing grouped surfaces with fixed 20% trimming/Winsorization,
  deterministic bounded bootstrap streams, raw effects, and no fallback.
- Added immutable schema-v2 robust result variants, semantic renderers,
  mutation/fault/replay/resource tests, independent base-R formula fixtures and
  retained upstream objects, and a phase-separated M6A performance/work baseline.
- Recorded Joshua Myers's independent review and acceptance of M6A after the
  complete technical gate, closing the robust continuous-analysis track while
  leaving R4, B1–B6, M6, and `0.4` open.
- Prepared the approval-ready M6B B1–B6 proposal, pending accountable sign-off,
  and pass-zero verification record for Bayesian reporting/evidence,
  univariate/correlation/comparison/categorical models, explicit M6C deferrals,
  and a bounded NumPy/SciPy closed-form, quadrature, and RQMC engine. Bayesian
  implementation remains stopped at the required approval gate.
- Recorded Joshua Myers's B1–B6 approval and implemented the M6B technical
  candidate: schema-v3 Bayesian results, exact NIG/Dirichlet-multinomial
  inference, exact correlation quadrature, deterministic bounded scrambled
  Sobol comparison/categorical summaries, numeric BF10 sensitivity records,
  semantic scalar/matrix/grouped rendering, mutation/fault tests, JSON schema,
  and retained performance/work evidence. Independent review and release
  acceptance remain open.
- Recorded Joshua Myers's independent M6B review, acceptance of every finding
  disposition, and accountable release acceptance, closing M6B while leaving
  R4/M6C and final M6/`0.4` open.
- Prepared the approval-ready M6C R4/B5 coefficient/meta proposal, entry audit,
  pending sign-off ledger, and pass-zero verification loop. The proposal fixes
  strict caller-reported robust/posterior coefficient profiles, a fixed-
  Student-t4 robust aggregate sensitivity model, a proper-prior Bayesian
  normal-normal aggregate model with deterministic quadrature, explicit
  prediction/diagnostic boundaries, bounded work, and no new runtime dependency
  or fallback. Implementation remains stopped at the accountable approval gate.
- Recorded Joshua Myers's approval of every R4/B5 M6C entry decision without
  revision on 2026-09-15, authorizing coefficient/meta implementation and
  acceptance-fixture construction while leaving technical verification,
  independent candidate acceptance, and final M6/`0.4` approval open.
