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
| M5 | Coefficients and approved frequentist meta-analysis ([detail](MILESTONE_5.md)) | 4–6 weeks |
| M6 | Robust and Bayesian methods ([detail](MILESTONE_6.md)) | 8–13 weeks |
| M7 | Compatibility closure, hardening, documentation, 1.0 | 4–6 weeks |

M0 through M5 are complete, and the `0.3` product gate is accepted. Joshua Myers
independently reviewed and accepted both M5 tracks and approved the combined
M5/`0.3` candidate on 2026-09-14. M6 is active. Joshua Myers approved the M6A
robust architecture/method entry gate on 2026-09-14. The M6A technical candidate
passed its technical gate and was independently reviewed and accepted by Joshua
Myers on 2026-09-14. Joshua Myers approved the detailed M6B B1–B6 method
contract on 2026-09-15, independently reviewed the resulting scalar, matrix,
comparison, categorical, and grouped candidate, and accepted M6B. The next
project gate is M6C implementation pass 1 under the detailed R4/B5 coefficient/
meta method contract in `M6C_STATISTICAL_METHODS.md`, approved by Joshua Myers
on 2026-09-15. Candidate review and final M6/`0.4` acceptance remain later
gates.

Total planning estimate: 42–58 engineer-weeks, or roughly 6–8 calendar months
with two Python engineers and a part-time statistical-methods reviewer.

## Product gates

- `0.1`: frequentist univariate/correlation/between-group core, extraction,
  grouping, and composition.
- `0.2`: within-subject and categorical families.
- `0.3`: coefficient plots and approved frequentist meta-analysis.
- `0.4`: approved robust/Bayesian methods and coefficient/meta extensions.
- `1.0`: every upstream export is dispositioned, result schemas are
  stable, and production release evidence is approved.

## Program invariants

- R is development-oracle tooling, never a released runtime dependency.
- A plot and its analysis use reconciled samples.
- All rendered statistics originate in typed, extractable result fields.
- Statistical and visual equivalence are tested separately.
- Polars is canonical; pandas may exist only behind an approved adapter.

See `MILESTONE_0.md`, `MILESTONE_1.md`, `MILESTONE_2.md`,
`MILESTONE_3.md`, `MILESTONE_4.md`, `MILESTONE_5.md`, `MILESTONE_6.md`,
`compatibility.md`, `../PROJECT_BRIEF.md`, and
`../STATISTICAL_ANALYSIS_PLAN.md` for active work and acceptance evidence.
