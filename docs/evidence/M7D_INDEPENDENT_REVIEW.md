# M7D Independent Review and 1.0 Decision

- Candidate version: `1.0.0`
- Independent-review owner: Joshua Myers
- Status: independently reviewed and accepted 2026-09-15
- Technical evidence: `M7D_RELEASE_VERIFICATION.md`

## Review checklist

- [x] Confirm the candidate preserves all 144 names shipped in 0.1.1 and marks
      exactly the seven dedicated robust-meta names experimental.
- [x] Confirm the migration guide, public API reference, schema corpus, and 1.x
      stability policy describe the intended compatibility promise.
- [x] Confirm the M7B robust-meta experimental disposition remains acceptable
      and no new statistical claim or fallback was introduced in M7D.
- [x] Confirm user documentation states the method assumptions, refusal
      behavior, resource limits, and experimental exception without overstating
      scientific interpretation.
- [x] Confirm Python 3.11 and 3.12 wheel/sdist install evidence, public smoke,
      oracle, benchmark, security, license, and artifact checks are sufficient.
- [x] Confirm the release workflow builds once, attaches only the wheel, sdist,
      SBOM, and checksums, and publishes only the wheel/sdist through the
      protected trusted-publishing environment.
- [x] Confirm no blocking or unowned major finding remains.
- [x] Separately accept or reject this exact candidate as plotsalot 1.0.0.

## Decision record

| Decision | Role | Approver | Decision/date | Status |
|---|---|---|---|---|
| M7B statistical disposition | Product/statistical owner | Joshua Myers | Experimental reclassification approved, 2026-09-15 | Complete |
| M7D implementation and exact-candidate technical gate | Implementation owner | Codex | Verified, 2026-09-15 | Complete |
| Independent M7D candidate review | Independent reviewer | Joshua Myers | Reviewed and accepted, 2026-09-15 | Complete |
| Final M7 and `1.0.0` release acceptance | Product/release owner | Joshua Myers | Accepted, 2026-09-15 | Complete |

Joshua Myers's review and acceptance closes M7 and the 1.0 product gate. The
accepted technical candidate is commit `e682d9d`; this decision-record update
changes no package source, metadata, schema, workflow, or public contract. The
approval does not itself create or push a Git tag, approve the protected PyPI
deployment, or assert the post-publication filename/hash/install checks.
