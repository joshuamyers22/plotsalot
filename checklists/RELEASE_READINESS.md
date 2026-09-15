# Release Readiness

Complete this checklist against the exact commit that will be tagged. Record
unresolved risks and accountable approvals in the applicable release evidence;
do not infer approval from a green automated gate.

## Product and documentation

- [ ] The selected semantic version matches `pyproject.toml`, the changelog, and
      the intended public compatibility promise.
- [ ] The changelog has a dated section for the release and no completed work is
      left only under `Unreleased`.
- [ ] README installation, maturity, examples, links, and limitations describe
      the artifact being published.
- [ ] Public behavior changes update the user guide, compatibility matrix,
      method specification, result schema, and migration guidance as applicable.
- [ ] The supported-version and private vulnerability-reporting policy in
      `SECURITY.md` has accountable owner approval.
- [ ] Remaining risks have an owner and disposition; statistical-method and
      release acceptance are recorded separately from implementation review.

## Repository and identity

- [ ] The worktree is clean and the release commit is on the intended default
      branch.
- [ ] `checklists/REPOSITORY_SETUP.md` passes for local Git identity, authenticated
      GitHub account, canonical remote, project URLs, and CODEOWNERS.
- [ ] Secrets, private data, generated distributions, scratch files, and raw
      telemetry are absent from tracked files and Git history.
- [ ] `PROJECT_MEMORY.md` is current, evidence-linked, deduplicated, and contains
      no credentials, personal data, transcripts, or hidden reasoning.
- [ ] Tracked work notes are closed or current.

## Verification and artifacts

- [ ] `make check` passes from the release commit.
- [ ] `make audit` reports no unaccepted runtime vulnerability, adverse project
      status, or dependency-license violation.
- [ ] `make build` produces exactly one expected wheel and one sdist.
- [ ] `uvx twine check dist/*.whl dist/*.tar.gz` passes.
- [ ] The built wheel installs and imports in isolated minimum-supported Python
      3.11 and current-development Python 3.12 environments.
- [ ] Applicable oracle, benchmark, stochastic replay, schema, and cross-mode
      evidence is current for the changed boundary.
- [ ] Wheel and sdist contain the expected code, README, and license and no
      credentials, private data, caches, or machine-specific paths.
- [ ] CI builds release artifacts from the tagged commit and emits an SBOM and
      SHA-256 checksums; local `dist/` files are never uploaded.

## PyPI trusted publishing

- [ ] The PyPI project or pending publisher names owner `joshuamyers22`, repository
      `plotsalot`, workflow `release.yml`, and the reviewed GitHub environment.
- [ ] The GitHub environment requires the intended protection or accountable
      approval available for the repository plan.
- [ ] The `pypi` environment permits only stable `vMAJOR.MINOR.PATCH` tags and
      the repository owner explicitly approves its deployment job.
- [ ] The publish job has only `id-token: write` plus the read permissions it
      needs; no long-lived PyPI token is stored in GitHub secrets.
- [ ] The publish step selects only the wheel and sdist and runs after the complete
      release gate.
- [ ] The semantic tag exactly matches package metadata and points to the reviewed
      commit.

## Publication and recovery

- [ ] The GitHub release contains only the intended wheel, sdist, SBOM, and
      checksum manifest.
- [ ] PyPI shows the expected metadata, README, license, Python requirement,
      project URLs, wheel, and sdist.
- [ ] A fresh environment installs the exact version from PyPI and completes a
      public-API smoke test without R, Docker, or network access after install.
- [ ] The published hashes match the GitHub release checksum manifest.
- [ ] A defective release will be yanked rather than overwritten; corrections
      use a new patch version and an explicit changelog entry.
