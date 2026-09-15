# M6C Accountable Sign-off

Joshua Myers approved the M6C statistical and numerical entry decisions without
revision on 2026-09-15. This passes the entry gate only; implementation,
independent review, M6C acceptance, and combined M6/`0.4` acceptance remain open.

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
| M6C technical release-candidate gates | Implementation owner | Codex | Passes 1–2 passed; pass 3 not started, 2026-09-15 | In progress |
| Independent adversarial review | Independent reviewer | Pending | Not started | Blocking |
| M6C release acceptance | Product/statistical owner | Pending | Not started | Blocking |
| Combined M6/`0.4` acceptance | Product/statistical owner | Pending | Not started | Blocking |

The approved decisions are specified in `../M6C_STATISTICAL_METHODS.md`, with
entry evidence in `M6C_METHOD_AUDIT.md` and architecture boundaries in
`../adr/ADR-005-robust-method-architecture.md` and
`../adr/ADR-006-bayesian-engine-architecture.md`.

Approval of the first six rows authorizes M6C implementation and fixture
construction only. It does not accept the resulting candidate or close M6,
M6C, or `0.4`.
