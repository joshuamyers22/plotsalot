# Releasing plotsalot

Releases are built by GitHub Actions from a stable semantic-version tag. The
workflow builds once, attaches the wheel, source distribution, SBOM, and
checksums to a GitHub release, and then publishes that same wheel and source
distribution to PyPI through OpenID Connect (OIDC). No long-lived PyPI token is
used by the workflow.

## One-time trusted-publisher setup

The GitHub `pypi` environment is restricted to stable version tags and requires
repository-owner approval. Because the PyPI project does not yet exist, sign in
to [PyPI account publishing](https://pypi.org/manage/account/publishing/) and add
a pending GitHub Actions publisher with exactly these values:

| Field | Value |
|---|---|
| PyPI project name | `plotsalot` |
| GitHub owner | `joshuamyers22` |
| GitHub repository | `plotsalot` |
| Workflow filename | `release.yml` |
| Environment name | `pypi` |

The pending publisher creates the PyPI project on its first successful upload.
It does not reserve the project name beforehand. Do not add a PyPI API token to
GitHub Actions secrets. A previously created token is unnecessary for this
workflow and can be revoked after trusted publishing is confirmed, unless it is
needed for a separate, documented purpose.

## Prepare a release

1. Select the semantic version. Update it with `uv version VERSION`, and confirm
   that `pyproject.toml`, `uv.lock`, and the changelog agree.
2. Move completed changelog entries out of `Unreleased` and add the release
   date.
3. Complete [`checklists/RELEASE_READINESS.md`](../checklists/RELEASE_READINESS.md)
   against the exact commit to be tagged.
4. Run the release gates:

   ```sh
   make check
   make audit
   make build
   uvx twine check dist/*.whl dist/*.tar.gz
   uv run python tools/verify_release.py --tag vVERSION
   ```

5. Merge the reviewed change to `main`, confirm CI succeeds, and verify that the
   local worktree is clean and `main` points to the intended release commit.

## Publish

Create and push an annotated tag that exactly matches the package version:

```sh
git tag -a vVERSION -m "plotsalot VERSION"
git push origin vVERSION
```

The `Release` workflow verifies the tag, runs the complete release gate, builds
the artifacts and SBOM, creates the GitHub release, and then waits for approval
on the `pypi` environment. Review the tagged commit and GitHub release artifacts
before approving that deployment. Approval causes `uv publish` to request a
short-lived OIDC credential and upload only the wheel and source distribution.

## Verify and recover

After publication, compare PyPI's filenames and hashes with the GitHub release
and install the exact version from PyPI in a clean environment:

```sh
uv run --isolated --no-project --with "plotsalot==VERSION" python -c \
  'from importlib.metadata import version; import plotsalot; print(version("plotsalot"))'
```

PyPI files and versions are immutable. If a release is defective, yank it and
publish a corrected patch version; do not attempt to overwrite it. If an upload
is interrupted, rerun the failed publish job so it reuses the retained build
artifact rather than creating a different artifact locally.
