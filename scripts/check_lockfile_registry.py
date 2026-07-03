#!/usr/bin/env python3
"""Fail if an npm lockfile resolves dependencies from a non-public registry.

The frontend ``package-lock.json`` must resolve every dependency from a public
npm registry. If a lockfile is regenerated inside a private/corporate network,
npm rewrites every ``resolved`` URL to that internal mirror (for example an
Artifactory proxy). Such a lockfile is unusable from a clean checkout: ``npm ci``
hangs or fails because the internal host is unreachable, and the frontend build
never runs. This guard catches that class of regression before it is committed.

It scans the lockfile for ``resolved`` URLs and asserts every host is on the
allowlist of known-public npm registries. Any other host fails the check.

Usage:
    python scripts/check_lockfile_registry.py
    python scripts/check_lockfile_registry.py path/to/package-lock.json ...

Exit codes:
    0  all resolved hosts are public (or no resolved URLs present)
    1  one or more resolved URLs point at a non-public host
    2  usage / IO / parse error
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.parse import urlparse

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Default lockfiles to check when no paths are given on the command line.
DEFAULT_LOCKFILES = (PROJECT_ROOT / "frontend" / "package-lock.json",)

# Hosts allowed to appear in a committed lockfile. Keep this list minimal and
# explicit: only well-known public npm registries belong here.
ALLOWED_HOSTS = frozenset(
    {
        "registry.npmjs.org",
        "registry.yarnpkg.com",
    }
)


def _iter_resolved_urls(node: object):
    """Yield every ``resolved`` URL found anywhere in the parsed lockfile."""
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "resolved" and isinstance(value, str):
                yield value
            else:
                yield from _iter_resolved_urls(value)
    elif isinstance(node, list):
        for item in node:
            yield from _iter_resolved_urls(item)


def check_lockfile(path: Path) -> list[str]:
    """Return a sorted list of offending (non-public) hosts found in ``path``.

    An empty list means the lockfile is clean.
    """
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"error: lockfile not found: {path}") from None
    except (OSError, json.JSONDecodeError) as exc:  # pragma: no cover - IO/parse
        raise SystemExit(f"error: could not read/parse {path}: {exc}") from exc

    offenders: set[str] = set()
    total = 0
    for url in _iter_resolved_urls(data):
        # Skip non-http resolutions (e.g. local "file:" or "link:" entries).
        if not url.startswith(("http://", "https://")):
            continue
        total += 1
        host = (urlparse(url).hostname or "").lower()
        if host not in ALLOWED_HOSTS:
            offenders.add(host or "<no-host>")

    rel = path.relative_to(PROJECT_ROOT) if path.is_relative_to(PROJECT_ROOT) else path
    if offenders:
        print(f"FAIL  {rel}: {len(offenders)} non-public registry host(s) across {total} resolved URLs")
        for host in sorted(offenders):
            print(f"        - {host}")
    else:
        print(f"OK    {rel}: {total} resolved URL(s), all public")
    return sorted(offenders)


def main(argv: list[str]) -> int:
    paths = [Path(a).resolve() for a in argv] or list(DEFAULT_LOCKFILES)
    any_offenders = False
    for path in paths:
        if check_lockfile(path):
            any_offenders = True

    if any_offenders:
        print(
            "\nA lockfile resolves dependencies from a non-public registry. "
            "Regenerate it against the public npm registry:\n"
            "  cd frontend && rm package-lock.json && "
            "npm install --registry=https://registry.npmjs.org/",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
