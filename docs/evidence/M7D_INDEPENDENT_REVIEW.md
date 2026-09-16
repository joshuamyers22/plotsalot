# M7D Independent Review and 1.0 Decision

- Candidate version: `1.0.0`
- Independent-review owner: Joshua Myers
- Status: ready for review; no decision recorded
- Technical evidence: `M7D_RELEASE_VERIFICATION.md`

## Review checklist

- [ ] Confirm the candidate preserves all 144 names shipped in 0.1.1 and marks
      exactly the seven dedicated robust-meta names experimental.
- [ ] Confirm the migration guide, public API reference, schema corpus, and 1.x
      stability policy describe the intended compatibility promise.
- [ ] Confirm the M7B robust-meta experimental disposition remains acceptable
      and no new statistical claim or fallback was introduced in M7D.
- [ ] Confirm user documentation states the method assumptions, refusal
      behavior, resource limits, and experimental exception without overstating
      scientific interpretation.
- [ ] Confirm Python 3.11 and 3.12 wheel/sdist install evidence, public smoke,
      oracle, benchmark, security, license, and artifact checks are sufficient.
- [ ] Confirm the release workflow builds once, attaches only the wheel, sdist,
      SBOM, and checksums, and publishes only the wheel/sdist through the
      protected trusted-publishing environment.
- [ ] Confirm no blocking or unowned major finding remains.
- [ ] Separately accept or reject this exact candidate as plotsalot 1.0.0.

## Decision record

| Decision | Role | Approver | Decision/date | Status |
|---|---|---|---|---|
| M7B statistical disposition | Product/statistical owner | Joshua Myers | Experimental reclassification approved, 2026-09-15 | Complete |
| M7D implementation and exact-candidate technical gate | Implementation owner | Codex | Verified, 2026-09-15 | Complete |
| Independent M7D candidate review | Independent reviewer | Joshua Myers | Pending | Open |
| Final M7 and `1.0.0` release acceptance | Product/release owner | Joshua Myers | Pending | Open |

Approval here closes M7 and the 1.0 product gate. It does not itself create or
push a Git tag, approve the protected PyPI deployment, or assert the
post-publication filename/hash/install checks.
