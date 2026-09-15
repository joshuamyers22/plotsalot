# M6C Accountable Sign-off

Joshua Myers approved the M6C statistical and numerical entry decisions without
revision on 2026-09-15. After the three-pass technical candidate completed, he
independently reviewed and accepted M6C on the same date. He approved the
combined M6/`0.4` candidate after its technical release gate passed.

| Decision | Role | Approver | Decision/date | Status |
|---|---|---|---|---|
| R4-C robust coefficient-summary profile and reporting boundary | Product/statistical reviewer | Joshua Myers | Approved, 2026-09-15 | Complete |
| B5-C posterior coefficient-summary profile and reporting boundary | Product/statistical reviewer | Joshua Myers | Approved, 2026-09-15 | Complete |
| R4-M fixed-Student-t4 robust aggregate model and profile inference | Statistical-methods reviewer | Joshua Myers | Approved, 2026-09-15 | Complete |
| B5-M proper-prior Bayesian NNHM, evidence, prediction, and sensitivity | Statistical-methods reviewer | Joshua Myers | Approved, 2026-09-15 | Complete |
| M6C native deterministic engine, schema, work, and no-fallback boundary | Architecture/statistical reviewer | Joshua Myers | Approved, 2026-09-15 | Complete |
| M6C verification loop, oracle/license posture, and acceptance thresholds | Product/statistical reviewer | Joshua Myers | Approved, 2026-09-15 | Complete |
| Warned `k=10–19` conservative-coverage disposition | Product/statistical reviewer | Joshua Myers | Approved 2026-09-15; fresh confirmation completed and retained | Complete |
| Provisional exact-`tau=0` conservative-coverage disposition | Product/statistical reviewer | Joshua Myers | Approved for M6/0.4, 2026-09-15; mandatory M7 review | Complete |
| M6C technical release-candidate gates | Implementation owner | Codex | Three-pass technical gate complete, 2026-09-15 | Complete |
| Independent adversarial review | Independent reviewer | Joshua Myers | Accepted, 2026-09-15 | Complete |
| M6C release acceptance | Product/statistical owner | Joshua Myers | Accepted, 2026-09-15 | Complete |
| Combined M6/`0.4` technical release gate | Implementation owner | Codex | Passed, 2026-09-15 | Complete |
| Combined M6/`0.4` acceptance | Product/statistical owner | Joshua Myers | Approved, 2026-09-15 | Complete |

The approved decisions are specified in `../M6C_STATISTICAL_METHODS.md`, with
entry evidence in `M6C_METHOD_AUDIT.md` and architecture boundaries in
`../adr/ADR-005-robust-method-architecture.md` and
`../adr/ADR-006-bayesian-engine-architecture.md`.

The first six approvals authorized implementation and fixture construction.
The later independent-review and release-acceptance decisions closed M6C. The
final combined approval recorded above closes M6 and the `0.4` product gate.
