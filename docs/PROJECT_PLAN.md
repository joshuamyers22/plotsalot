# plotsalot Project Plan

The detailed planning artifact was prepared from the production project template
on 2026-09-13. This repository executes that plan through the following gates.

| Milestone | Scope | Estimated duration |
|---|---|---:|
| M0 | Discovery, frozen R oracles, decisions, walking skeleton | 2–3 weeks |
| M1 | Shared result/data/render contracts and production repository ([detail](MILESTONE_1.md)) | 2–3 weeks |
| M2 | Frequentist univariate and correlation core ([detail](MILESTONE_2.md)) | 4–5 weeks |
| M3 | Between- and within-group comparisons and pairwise tests ([detail](MILESTONE_3.md)) | 5–7 weeks |
| M4 | Categorical bar/pie families ([detail](MILESTONE_4.md)) | 3–4 weeks |
| M5 | Coefficients and approved meta-analysis | 4–6 weeks |
| M6 | Robust and Bayesian methods | 8–13 weeks |
| M7 | Compatibility closure, hardening, documentation, 1.0 | 4–6 weeks |

M0 through M4 are complete, and the `0.2` product gate is accepted. M5 is the
next planned milestone.

Total planning estimate: 42–58 engineer-weeks, or roughly 6–8 calendar months
with two Python engineers and a part-time statistical-methods reviewer.

## Product gates

- `0.1`: frequentist univariate/correlation/between-group core, extraction,
  grouping, and composition.
- `0.2`: within-subject and categorical families.
- `0.3`: coefficient plots and approved frequentist meta-analysis.
- `0.4+`: robust/Bayesian previews as method gates pass.
- `1.0`: every upstream export is dispositioned, result schemas are
  stable, and production release evidence is approved.

## Program invariants

- R is development-oracle tooling, never a released runtime dependency.
- A plot and its analysis use reconciled samples.
- All rendered statistics originate in typed, extractable result fields.
- Statistical and visual equivalence are tested separately.
- Polars is canonical; pandas may exist only behind an approved adapter.

See `MILESTONE_0.md`, `MILESTONE_1.md`, `MILESTONE_2.md`,
`MILESTONE_3.md`, `MILESTONE_4.md`, `compatibility.md`,
`../PROJECT_BRIEF.md`, and `../STATISTICAL_ANALYSIS_PLAN.md` for active work and
acceptance evidence.
