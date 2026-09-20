## Python dependency logic

In this folder, the `.in` files, in conjunction with the `../pyproject.toml` file (in the root of the repo) are used to generate the pinned requirements as `.txt` files.

To alter the pinned dependency, you can edit/alter the `.in` and `pyproject.toml` files, and then run the following command:

```bash
./scripts/uv-pip-compile.sh
```
:::warning
The pinned dependencies are based on the `current` version of python supported in Superset.
Output of `./scripts/uv-pip-compile.sh` may vary slightly based on the python version you are using to run the command.
Check the `pyproject.toml` file for the current version of python supported.
:::

This will generate the pinned requirements in the `.txt` files, which will be used in our CI/CD pipelines and in the Docker images.

We recommend to everyone in the community to use the pinned requirements in their local development environments, to ensure consistency across different environments, though we don't force requirements as part of our python package semantics to allow flexibility for users to install different versions of the dependencies if they wish.

Note that `development.txt` is a superset of what's in `base.txt`, and all version numbers for shared library should fully match at all times. `translations.txt` is meant as a supplemental file to be used in conjunction with the other requirements files, and is not meant to be used standalone.

## Fork-local dependency validation

This fork runs `.github/workflows/dependency-remediation-check.yml` on pull requests that touch `pyproject.toml`, `requirements/**`, or the dependency scripts. It is a deliberately small, fast signal for automated dependency-remediation PRs, and validates two things:

1. **Lock freshness** — it re-runs `./scripts/uv-pip-compile.sh` and fails if the regenerated `requirements/*.txt` differ from what the PR committed (comment-only and whitespace-only diffs are ignored, mirroring the upstream `check-python-deps` workflow).
2. **Declared-constraint consistency** — `scripts/check_pinned_extras.py` fails if a pin in `base.txt` or `development.txt` violates a specifier declared in `pyproject.toml`, including `[project.optional-dependencies]` extras. Extras are not inputs to the compile, so a package pulled in transitively (e.g. `xlrd` via `pandas`) can be pinned outside the range an extra declares while the recompile check stays green.

Limitations: nothing is installed, imported, or tested, so runtime breakage from a version bump is not detected; frontend, Docker, and helm dependencies are out of scope; there is no vulnerability scanning; and the constraint check is static (it skips requirements with environment markers and does not perform a full multi-extra resolution).

Run both checks locally with:

```bash
python scripts/check_pinned_extras.py
./scripts/uv-pip-compile.sh && git diff --exit-code requirements
```
