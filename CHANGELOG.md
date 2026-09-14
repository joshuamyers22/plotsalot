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
