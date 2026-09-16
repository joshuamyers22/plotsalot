# M7D 1.0 Release-Candidate Verification

- Candidate date: 2026-09-15
- Candidate version: `1.0.0`
- Technical outcome: passed
- Accountable final 1.0 acceptance: approved by Joshua Myers, 2026-09-15

## Candidate boundary

This pass closes the implementation-owned M7D work. It changes package metadata
from `0.1.1` to `1.0.0`, moves the completed M7 work into the dated changelog,
and aligns the user, migration, compatibility, stability, release, and project
documents with the proposed stable contract. All 144 root exports remain
available: 137 are stable and the seven dedicated robust-meta names remain
experimental under the accepted M7B disposition.

The release build now clears stale distributions before building. The retained
artifact verifier requires exactly one version-matched universal wheel and one
source distribution, validates archive paths and integrity, compares wheel
metadata and all four console scripts with the project contract, requires the
runtime modules, README, typing marker, and MIT license, rejects development
content from the wheel, and scans both archives for generated residue, sensitive
filenames, and machine-specific paths.

## Technical gate results

| Gate | Result |
|---|---|
| Formatting and lint | Passed |
| Strict Pyright | Passed with zero errors or warnings |
| Full unit/integration suite | 294 tests passed |
| Coverage | 92% total; passed the 75% repository threshold |
| Documentation and retained public-contract drift checks | Passed |
| Runtime vulnerability and dependency-license audit | Passed |
| Frozen oracle verification | Passed |
| Retained benchmark verification | Passed |
| Source distribution and universal wheel build | Passed with stale-artifact clearing |
| Wheel/sdist integrity, content, metadata, license, path, and residue inspection | Passed |
| Release tag/metadata check for `v1.0.0` | Passed |
| Python 3.11 wheel install and public smoke | Passed offline |
| Python 3.12 wheel install and public smoke | Passed offline |
| Python 3.11 sdist build/install and public smoke | Passed offline |
| Python 3.12 sdist build/install and public smoke | Passed offline |

Each installed-artifact smoke imports from `site-packages`, verifies version,
Python/license metadata, all 144 root exports, and all four console entry points,
then renders and JSON-serializes classical, robust, Bayesian, grouped, and
composed public results without R, Docker, repository data, or network access.
CI now repeats the wheel smoke on Python 3.11 and 3.12, and the stable-tag
release workflow repeats it before SBOM generation or publication.

## Exact artifact identity

The final local candidate build produced exactly
`plotsalot-1.0.0-py3-none-any.whl` and `plotsalot-1.0.0.tar.gz`; the artifact
verifier printed a SHA-256 identity for each. Generated GitHub-release SBOM and
checksum assets remain owned by the tagged release workflow so publication
reuses its single retained build.

Artifact hashes are build identities, not source identities. A tracked source
distribution necessarily changes when this evidence record changes, so local
pre-commit hashes are deliberately not asserted as final release hashes. The
protected workflow generates the authoritative checksum manifest from the exact
accepted tag and publishes those same retained files. The GitHub release and
PyPI hashes must be compared after publication under `RELEASING.md`.

## Release-readiness reconciliation

- Product/documentation, version, changelog, migration, compatibility, security,
  reproducibility, and recovery guidance describe the 1.0 candidate.
- The normal quality, audit, artifact, oracle, benchmark, schema, replay, and
  cross-mode evidence is current.
- The release workflow uses stable semantic tags, pinned actions, least-privilege
  permissions, explicit artifact patterns, an SBOM and checksum manifest, and
  PyPI trusted publishing with no long-lived package token.
- The live GitHub `pypi` environment requires review by `joshuamyers22` and
  permits only the custom stable-tag pattern `v[0-9]*.[0-9]*.[0-9]*`.
  Repository and `pypi` environment Actions secret inventories are both empty;
  the publish job receives only `id-token: write`.
- Tag identity, GitHub release assets, PyPI metadata/hashes, and clean-index
  installation are delivery/post-publication checks and cannot pass before the
  accepted candidate is tagged and published.

## Acceptance boundary

Joshua Myers independently reviewed and accepted the exact `e682d9d` technical
candidate on 2026-09-15, closing M7 and the 1.0 product gate. The sign-off-only
documentation commit changes no package source, metadata, schema, workflow, or
public contract. Tagging and publication were separately authorized delivery
actions; the subsequently pushed annotated `v1.0.0` tag triggered the protected
GitHub release and PyPI deployment workflow.

## Publication closeout

Publication completed on 2026-09-15 America/Indiana/Indianapolis (2026-09-16
UTC):

- annotated tag `v1.0.0` points to sign-off commit `bad099b`, whose only change
  from the accepted `e682d9d` technical candidate is the owner decision record;
- release workflow `35043264726` passed its build, GitHub release, and protected
  PyPI trusted-publishing jobs;
- the GitHub release contains exactly the wheel, sdist, CycloneDX SBOM, and
  SHA-256 manifest;
- PyPI contains exactly `plotsalot-1.0.0-py3-none-any.whl` with SHA-256
  `df6b78a9dff0be407690783b48732cc86782eb1fda4ce4e40b291014c5cdca43`
  and `plotsalot-1.0.0.tar.gz` with SHA-256
  `18638be65e7635e2527a7ed66af11be1846006d778c1c3c259f23a2429fb1502`;
- both PyPI hashes match the GitHub checksum manifest, and neither file is
  yanked;
- PyPI reports version `1.0.0`, Python `>=3.11`, MIT license metadata, and the
  intended project URLs; and
- a no-cache Python 3.12 installation resolved `plotsalot==1.0.0` from PyPI and
  passed the installed public smoke from `site-packages` with all 144 exports.

The release and post-publication recovery gates are complete.
