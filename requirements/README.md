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

## Fork-local remediation validation

This fork runs `.github/workflows/remediation-validation.yml` as an independent, inexpensive signal for automated remediation pull requests. A `detect` job runs the repository's existing change-detector (`scripts/change_detector.py`) and publishes a flag per change category; each category job is gated on its flag, so a PR only pays for the categories it touches.

The `python-deps` category (`pyproject.toml`, `requirements/**`, `scripts/uv-pip-compile.sh`) re-runs `./scripts/uv-pip-compile.sh` and fails if the regenerated `requirements/*.txt` differ from what the PR committed — comment-only and whitespace-only diffs are ignored, mirroring the upstream `check-python-deps` workflow. Reproduce locally with:

```bash
./scripts/uv-pip-compile.sh && git diff --exit-code requirements
```

Limitations: nothing from the resolved set is installed, imported, or tested, so runtime breakage from a version bump is not detected; only state that `uv-pip-compile.sh` regenerates is validated, which excludes constraints that never take part in that resolution (notably `[project.optional-dependencies]` extras, which are not compile inputs, so a transitive pin can contradict an extra while the check stays green); there is no vulnerability or license scanning; frontend, Docker, and helm dependencies are out of scope.

To cover another remediation category (for example frontend lock files or Python code quality), add a pattern group to `scripts/change_detector.py`, expose it as an output in `.github/actions/change-detector/action.yml`, and add a job to the workflow gated on that output.
