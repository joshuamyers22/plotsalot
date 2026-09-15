# M6A Accountable Sign-off

The M6A contract cannot pass its statistical or architecture entry gate through
technical preparation alone. Joshua Myers is the recorded statistical and
product owner.

| Decision | Role | Approver | Decision/date | Status |
|---|---|---|---|---|
| ADR-005 native bounded robust architecture | Architecture/statistical reviewer | Joshua Myers | Approved, 2026-09-14 | Complete |
| ADR-006 isolated Bayesian boundary required by M6 entry | Architecture reviewer | Joshua Myers | Approved, 2026-09-14 | Complete |
| R1 robust one-sample and centrality inference | Statistical-methods reviewer | Joshua Myers | Approved, 2026-09-14 | Complete |
| R2 robust association and correlation-matrix inference | Statistical-methods reviewer | Joshua Myers | Approved, 2026-09-14 | Complete |
| R3 robust independent and repeated comparisons | Statistical-methods reviewer | Joshua Myers | Approved, 2026-09-14 | Complete |
| G6 grouping, RNG, work limits, and presentation | Statistical/product reviewer | Joshua Myers | Approved, 2026-09-14 | Complete |
| M6A technical release-candidate gates | Implementation owner | Codex | Verified, 2026-09-14 | Complete |
| Independent adversarial review | Independent reviewer | Joshua Myers | Accepted, 2026-09-14 | Complete |
| M6A release acceptance | Product/statistical owner | Joshua Myers | Accepted, 2026-09-14 | Complete |

The approved decisions are specified in `../M6_STATISTICAL_METHODS.md`,
`../adr/ADR-005-robust-method-architecture.md`, and
`../adr/ADR-006-bayesian-engine-architecture.md`. ADR-006 fixes only the future
Bayesian dependency boundary and does not add an M6A runtime dependency.

Joshua Myers approved the entry rows without revision on 2026-09-14, authorizing
R1–R3/G6 implementation exactly as written. After the technical candidate
passed `M6A_VERIFICATION.md`, Joshua Myers independently reviewed the candidate,
reported no new findings, and accepted M6A on 2026-09-14. This closes M6A only;
it does not approve R4/B1–B6 or close M6, M6C, M6B, or `0.4`.
