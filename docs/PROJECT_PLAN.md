# plotsalot Project Plan

The detailed planning artifact was prepared from the production project template
on 2026-09-13. This repository executes that plan through the following gates.

| Milestone | Scope | Estimated duration |
|---|---|---:|
| M0 | Discovery, frozen R oracles, decisions, walking skeleton | 2–3 weeks |
| M1 | Shared result/data/render contracts and production repository | 2–3 weeks |
| M2 | Frequentist univariate and correlation core | 4–5 weeks |
| M2B | Q–Q/P–P points, lines, detrending, initial bands | 4–6 weeks |
| M3 | Between- and within-group comparisons and pairwise tests | 5–7 weeks |
| M4 | Categorical bar/pie families | 3–4 weeks |
| M5 | Coefficients and approved meta-analysis | 4–6 weeks |
| M6 | Robust, Bayesian, and advanced diagnostic bands | 8–13 weeks |
| M7 | Compatibility closure, hardening, documentation, 1.0 | 4–6 weeks |

Total planning estimate: 46–64 engineer-weeks, or roughly 6–9 calendar months
with two Python engineers and a part-time statistical-methods reviewer.

## Product gates

- `0.1`: frequentist univariate/correlation/between-group core, Q–Q/P–P points
  and lines, approved initial bands, extraction, grouping, and composition.
- `0.2`: within-subject and categorical families.
- `0.3`: coefficient plots and approved frequentist meta-analysis.
- `0.4+`: robust/Bayesian previews and advanced diagnostic bands as method gates
  pass.
- `1.0`: every combined upstream export is dispositioned, result schemas are
  stable, and production release evidence is approved.

## Program invariants

- R is development-oracle tooling, never a released runtime dependency.
- A plot and its analysis use reconciled samples.
- All rendered statistics originate in typed, extractable result fields.
- Statistical and visual equivalence are tested separately.
- Polars is canonical; pandas may exist only behind an approved adapter.
- No `qqplotr` source is copied or translated before ADR-010 is approved.

See `MILESTONE_0.md`, `compatibility.md`, `../PROJECT_BRIEF.md`, and
`../STATISTICAL_ANALYSIS_PLAN.md` for the active work and acceptance evidence.
