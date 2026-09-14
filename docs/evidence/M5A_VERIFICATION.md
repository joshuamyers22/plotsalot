# M5A Verification Evidence

- Date: 2026-09-14
- Scope: strict coefficient tables, fitted Statsmodels OLS adaptation, typed
  results, shared semantic rendering, extraction/composition, oracle, benchmark,
  and package gates
- Technical result: implementation passes its Python and pinned-R gates
- Track result: independently reviewed and accepted; final M5/`0.3` candidate
  accepted

## Data and adapter evidence

- `CoefficientTable` owns immutable finite `float64` arrays and resolves exactly
  one table-wide `estimate_only`, `interval`, `full_t`, or `full_z` profile.
- Structured `response`, `component`, and `group` identities allow repeated base
  terms without concatenation; complete structured keys must remain unique.
- Participating nulls, non-finite values, partial profiles, invalid intervals,
  nonpositive standard errors/df, invalid p-values, ambiguous intercepts, and
  resource excess fail atomically. Nonparticipating columns are ignored.
- The fitted adapter accepts only the exact Statsmodels
  `RegressionResultsWrapper` over exact `OLS`, with nonrobust or HC3 covariance,
  full rank, positive residual df, reconciled constant metadata, finite aligned
  arrays, and exactly representable observation count. It snapshots public
  results without refitting or retaining the fitted object.

## Result and rendering evidence

- The coefficient and meta-analysis variants share schema version 1, the public
  `analyze_ggcoefstats`/`render_ggcoefstats`/`ggcoefstats` surface, semantic
  reference/point/interval layers, extraction, composition, and resource policy.
- The coefficient result retains source/display identities and positions,
  excluded intercepts, reported versus model-derived provenance, confidence and
  significance policy, model summary, scale declarations, and every displayed
  inference field.
- Estimate-only and interval-only profiles cannot display statistical labels.
  `only_significant` filters text only and uses strict `p_value < alpha`.
- Injection and constructor-mutation tests reject contradictory identity,
  profile, provenance, interval, statistic, model, audit, and limit records.

## Oracle evidence

- Raw pinned-ggstatsplot objects are retained for an ordinary coefficient table
  and fitted R `lm` object.
- Base R independently supplies fitted OLS estimates, standard errors, t
  statistics, residual df, p-values, confidence intervals, observation count,
  model df, and rank. Python agrees at `1e-10` relative and `1e-12` absolute
  tolerance.
- Oracle manifest SHA-256:
  `21b0d6daef8a2dbec4477d797dad14d986def2192b59f70c71b1792ecb97e7b0`

## Performance evidence

`benchmarks/results/m5a-baseline.json` retains five warmed samples for selection,
complete analysis, and rendering at 10, 100, and 500 full-z table terms, plus a
separate fitted HC3 OLS adapter workload. Frame construction and model fitting
are outside measured phases.

At 500 terms, retained medians are 2.27 ms for selection, 453 ms for analysis,
and 1.91 s for rendering. The fitted-model adapter median is 3.91 ms with a
118 KB median incremental Python allocation peak.

- M5A benchmark SHA-256:
  `f0d3f49f152a5cb28bb959be59b089f0376f7b964f39e8cf56f883981badd920`

## Python production gate

- Ruff and strict Pyright pass.
- 175 tests pass with 92% repository branch coverage. M5 domain modules cover
  renderer 95%, meta-analysis 90%, shared data 91%, result contracts 95%, and
  coefficient-table/model analysis 94%.
- The expanded pinned oracle and benchmark verifiers pass.
- The pinned Docker/R oracle regenerates and verifies end to end.
- `uv audit --locked --no-dev` reports no known vulnerabilities or adverse
  project statuses, and the dependency-license policy passes.
- The source distribution and wheel build successfully. A fresh offline virtual
  environment installed the wheel and rendered both M5A and M5B through the
  installed package while preserving exact extraction identity.
- Wheel SHA-256:
  `51dd12092b6f8347021a241cb51b8feb7ba1c6c88f5c084a19052cd1a4dcb2f7`

## Independent and final acceptance

Joshua Myers independently reviewed the M5A evidence, reported no new finding,
accepted M5A, and accepted the final combined M5/`0.3` candidate on 2026-09-14.
