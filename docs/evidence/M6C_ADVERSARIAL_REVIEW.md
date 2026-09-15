# M6C Adversarial Review

- Candidate date: 2026-09-15
- Review scope: approved R4/B5 three-pass implementation and evidence
- Candidate self-review: complete
- Independent reviewer: Joshua Myers
- Independent decision: accepted, 2026-09-15

The implementation owner performed the following fault-oriented review to make
the technical candidate reviewable. Joshua Myers independently reviewed the
candidate, accepted every disposition, and reported no new blocking finding.

| ID | Adversarial concern | Evidence | Disposition |
|---|---|---|---|
| M6C-A-001 | A generic renderer could silently treat confidence and credible intervals as interchangeable | Mode-specific subtitles, labels, and artist roles name confidence, profile-likelihood confidence, equal-tail credible, and posterior-predictive credible intervals; injection tests read the retained fields | Resolved in candidate |
| M6C-A-002 | Rendering could recompute a statistic or fabricate a test from reported summaries | Robust coefficient labels contain only the reported estimate/interval; posterior labels contain median/interval and the complete retained directional-probability partition; no p value or BF is reconstructed | Resolved in candidate |
| M6C-A-003 | Pooled and predictive Bayesian intervals could become visually indistinguishable | Separate legend roles and artists are asserted; `show_prediction=False` suppresses only the predictive layer and leaves the result unchanged | Resolved in candidate |
| M6C-A-004 | Robust meta reporting could imply unavailable classical heterogeneity or prediction quantities | The caption emits the retained Q/I-squared and prediction absence reasons verbatim; the pooled artist is explicitly profile-likelihood | Resolved in candidate |
| M6C-A-005 | Caller-controlled identities could inject controls, create unreadable labels, or break serialization | M6C display identities are printable Unicode strings of 1–200 characters; controls and overlong values fail, while valid Unicode is retained exactly | Resolved in candidate; the bound is deliberately M6C-only |
| M6C-A-006 | Duck-typed or unrelated runtime objects could reach a renderer branch | `render_ggcoefstats` accepts only the five approved analysis classes and rejects an adversarial object before figure construction | Resolved in candidate |
| M6C-A-007 | Extraction or mixed composition could copy, weaken, or replace results | Public-wrapper and four-mode composition tests assert exact object identity and finite JSON serialization for classical/robust/Bayesian panels | Resolved in candidate |
| M6C-A-008 | Rendering and high-study meta-analysis could consume unbounded time or memory | Retained five-sample analysis/render grids cover 10/100/500 coefficients and robust studies plus 3/10/100/500 Bayesian studies; actual deterministic work remains below retained reservations | Resolved in candidate |
| M6C-A-009 | GPL reference code could enter the MIT runtime or artifacts | Dependency/license audit passes; the implementation remains independently derived NumPy/SciPy code and retained external evidence contains no copied source | Resolved in candidate |
| M6C-A-010 | The provisional exact-zero-heterogeneity coverage allowance could be mistaken for permanent acceptance | The unchanged failed and confirmation artifacts remain labeled, every status document routes the issue to mandatory M7 review, and no renderer changes the statistical result | Open governance debt for M7; non-blocking only under Joshua Myers's provisional M6/0.4 disposition |

## Independent review decision

Joshua Myers independently reviewed the semantic vocabulary and artist
identity, the reported-summary no-reconstruction boundary, robust and Bayesian
meta annotations, adversarial identities, package/license evidence, and the
retained M5/M6C timing comparison. He accepted the candidate on 2026-09-15.
The provisional zero-heterogeneity disposition remains mandatory M7 debt.
