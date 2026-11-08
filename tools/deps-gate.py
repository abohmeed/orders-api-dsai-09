#!/usr/bin/env python3
"""Read-only PyPI dependency gate for DSAI-09.

Queries the PyPI JSON API for each project dependency. Fails if a package
does not exist (404) or if its first release is younger than 30 days.
Never downloads wheels or installs packages.
"""
from __future__ import annotations

import json
import sys
import tomllib
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

PYPI = "https://pypi.org/pypi/{name}/json"
MIN_AGE_DAYS = 30
UA = "dsai-deps-gate/0.1 (+read-only; course lab)"


def project_deps(pyproject: Path) -> list[str]:
    data = tomllib.loads(pyproject.read_text())
    raw = data.get("project", {}).get("dependencies", [])
    names: list[str] = []
    for entry in raw:
        # Strip extras/markers/version: "foo[x]>=1.0; python_version>='3'" -> foo
        name = entry.split(";")[0].strip()
        for sep in ("[", "=", ">", "<", "!", "~", " "):
            if sep in name:
                name = name.split(sep, 1)[0]
        names.append(name.strip())
    return names


def first_release_utc(info: dict) -> datetime | None:
    releases = info.get("releases") or {}
    earliest: datetime | None = None
    for files in releases.values():
        for f in files:
            uploaded = f.get("upload_time_iso_8601") or f.get("upload_time")
            if not uploaded:
                continue
            # PyPI uses Z or +00:00
            ts = uploaded.replace("Z", "+00:00")
            try:
                dt = datetime.fromisoformat(ts)
            except ValueError:
                continue
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            if earliest is None or dt < earliest:
                earliest = dt
    return earliest


def check_package(name: str) -> int:
    url = PYPI.format(name=name)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            payload = json.load(resp)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"FAIL  {name}: not found on PyPI (HTTP 404)")
            return 1
        print(f"FAIL  {name}: PyPI error HTTP {e.code}")
        return 1
    except urllib.error.URLError as e:
        print(f"FAIL  {name}: network error ({e.reason})")
        return 1

    first = first_release_utc(payload)
    if first is None:
        print(f"FAIL  {name}: no release timestamps on PyPI")
        return 1
    age = (datetime.now(timezone.utc) - first).days
    if age < MIN_AGE_DAYS:
        print(f"FAIL  {name}: first release {first.date()} ({age}d old, need >={MIN_AGE_DAYS}d)")
        return 1
    print(f"PASS  {name}: first release {first.date()} ({age}d old)")
    return 0


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    pyproject = root / "pyproject.toml"
    if not pyproject.is_file():
        print(f"FAIL  missing {pyproject}")
        return 1
    deps = project_deps(pyproject)
    if not deps:
        print("FAIL  no project.dependencies in pyproject.toml")
        return 1
    rc = 0
    for name in deps:
        rc |= check_package(name)
    return rc


if __name__ == "__main__":
    sys.exit(main())
