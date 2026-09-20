#!/usr/bin/env python
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Check pinned requirements against the specifiers declared in pyproject.toml.

``scripts/uv-pip-compile.sh`` resolves ``pyproject.toml`` core dependencies plus
the ``requirements/*.in`` files, so optional-dependency extras never take part
in the resolution. A package that reaches ``requirements/*.txt`` only as a
transitive dependency can therefore be pinned to a version that contradicts the
range an extra declares for it, and the recompile check stays green.

This script compares every pinned version in the requirements lock files with
every specifier declared in ``pyproject.toml`` (core dependencies and all
extras) and exits non-zero on a conflict. Requirements carrying an environment
marker are skipped, as their applicability depends on the install environment.
"""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path
from typing import Any

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
from packaging.version import InvalidVersion, Version

ROOT = Path(__file__).resolve().parent.parent
LOCK_FILES = ("requirements/base.txt", "requirements/development.txt")


def declared_requirements(
    pyproject: dict[str, Any],
) -> list[tuple[str, Requirement]]:
    project = pyproject["project"]
    sources: list[tuple[str, list[str]]] = [
        ("project.dependencies", project.get("dependencies", []))
    ]
    sources += [
        (f"project.optional-dependencies.{extra}", deps)
        for extra, deps in project.get("optional-dependencies", {}).items()
    ]
    return [
        (source, Requirement(dep))
        for source, deps in sources
        for dep in deps
        if not Requirement(dep).marker
    ]


def pinned_versions(lock_file: Path) -> dict[str, Version]:
    pins: dict[str, Version] = {}
    for line in lock_file.read_text().splitlines():
        if not line or line[0].isspace() or line.startswith("#") or "==" not in line:
            continue
        name, _, version = line.partition("==")
        version = version.split(";")[0].split("#")[0].strip()
        try:
            pins[canonicalize_name(name.strip())] = Version(version)
        except InvalidVersion:
            continue
    return pins


def main() -> int:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        declared = declared_requirements(tomllib.load(handle))

    conflicts: list[str] = []
    for relative_path in LOCK_FILES:
        pins = pinned_versions(ROOT / relative_path)
        for source, requirement in declared:
            pinned = pins.get(canonicalize_name(requirement.name))
            if pinned is None or pinned in requirement.specifier:
                continue
            conflicts.append(
                f"{relative_path}: {requirement.name}=={pinned} violates "
                f"'{requirement}' declared in {source}"
            )

    if conflicts:
        print("Pinned dependencies conflict with pyproject.toml declarations:")
        for conflict in conflicts:
            print(f"  - {conflict}")
        print(
            "\nDeclare the package explicitly in requirements/base.in (or adjust the "
            "pyproject.toml specifier) and re-run ./scripts/uv-pip-compile.sh."
        )
        return 1

    print(f"Pins in {', '.join(LOCK_FILES)} satisfy all pyproject.toml specifiers.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
