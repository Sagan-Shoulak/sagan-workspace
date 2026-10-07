#!/usr/bin/env python3
"""Validate and download the exact installed-artifact compatibility set."""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import tempfile
import tomllib
from urllib.parse import urlparse
from urllib.request import urlopen


REQUIRED = {"id", "version", "platform", "source_commit", "url", "sha256"}


def load_lock(path: Path) -> list[dict[str, str]]:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ValueError("installed artifact lock must use schema_version = 1")
    artifacts = data.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise ValueError("installed artifact lock must contain artifacts")
    seen: set[str] = set()
    for artifact in artifacts:
        missing = REQUIRED - artifact.keys()
        if missing:
            raise ValueError(f"artifact is missing fields: {', '.join(sorted(missing))}")
        artifact_id = artifact["id"]
        if artifact_id in seen:
            raise ValueError(f"duplicate artifact id: {artifact_id}")
        seen.add(artifact_id)
        if len(artifact["source_commit"]) != 40:
            raise ValueError(f"{artifact_id}: source_commit must be a full SHA")
        digest_value = artifact["sha256"]
        if len(digest_value) != 64 or any(
            character not in "0123456789abcdef" for character in digest_value
        ):
            raise ValueError(f"{artifact_id}: sha256 must be lowercase hexadecimal")
        if urlparse(artifact["url"]).scheme not in {"https", "file"}:
            raise ValueError(f"{artifact_id}: unsupported artifact URL")
    return artifacts


def digest(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def fetch(artifact: dict[str, str], destination: Path) -> Path:
    filename = Path(urlparse(artifact["url"]).path).name
    output = destination / filename
    destination.mkdir(parents=True, exist_ok=True)
    if output.exists() and digest(output) == artifact["sha256"]:
        return output
    with urlopen(artifact["url"]) as response, tempfile.NamedTemporaryFile(
        dir=destination, delete=False
    ) as temporary:
        temporary_path = Path(temporary.name)
        while chunk := response.read(1024 * 1024):
            temporary.write(chunk)
    try:
        actual = digest(temporary_path)
        if actual != artifact["sha256"]:
            raise ValueError(
                f"{artifact['id']}: checksum mismatch: expected {artifact['sha256']}, got {actual}"
            )
        os.replace(temporary_path, output)
    finally:
        temporary_path.unlink(missing_ok=True)
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lock", type=Path, default=Path("installed-artifacts.lock"))
    parser.add_argument("--download-dir", type=Path)
    arguments = parser.parse_args()
    artifacts = load_lock(arguments.lock)
    for artifact in artifacts:
        if arguments.download_dir is None:
            print(f"{artifact['id']}: {artifact['version']} {artifact['sha256']}")
        else:
            path = fetch(artifact, arguments.download_dir)
            print(f"{artifact['id']}: verified {path} {artifact['sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
