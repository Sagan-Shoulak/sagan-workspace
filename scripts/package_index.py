"""Combine installed package catalogs from exact workspace component checkouts."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import sys
import tempfile
import tomllib

from workspace import DEFAULT_ROOT, inspect, load_contract


PACKAGE_OWNERS = {"sagan-physics", "sagan-render"}
SAFE_NAME = re.compile(r"[A-Za-z0-9._-]+\Z")


def child_path(root: Path, relative: str) -> Path:
    path = Path(relative)
    if path.is_absolute() or not path.parts or any(part in (".", "..") for part in path.parts):
        raise ValueError(f"unsafe relative path: {relative!r}")
    resolved = (root / path).resolve()
    if not resolved.is_relative_to(root):
        raise ValueError(f"path escapes catalog root: {relative!r}")
    return resolved


def read_catalog(root: Path, component: Path) -> list[str]:
    catalog = component / "libraries" / "index.tsv"
    if not catalog.is_file() or catalog.is_symlink():
        raise ValueError(f"missing regular package catalog: {catalog}")
    lines = catalog.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "sagan-package-index-v1":
        raise ValueError(f"unsupported package catalog schema: {catalog}")
    rows = []
    for number, line in enumerate(lines[1:], start=2):
        if not line or line.startswith("#"):
            continue
        fields = line.split("\t")
        if len(fields) != 5 or fields[3] != "installed":
            raise ValueError(f"invalid installed package row {catalog}:{number}")
        name, version, compiler, _, relative = fields
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", name):
            raise ValueError(f"invalid package name at {catalog}:{number}")
        if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version):
            raise ValueError(f"invalid package version at {catalog}:{number}")
        if not re.fullmatch(r"\^?[0-9]+\.[0-9]+\.[0-9]+", compiler):
            raise ValueError(f"invalid compiler requirement at {catalog}:{number}")
        manifest = child_path(catalog.parent, relative)
        if not manifest.is_relative_to(component / "libraries") or not manifest.is_file():
            raise ValueError(f"package manifest escapes component or is missing: {relative}")
        with manifest.open("rb") as stream:
            package = tomllib.load(stream).get("package")
        if not isinstance(package, dict) or package.get("name") != name or package.get("version") != version:
            raise ValueError(f"indexed package identity differs from {manifest}")
        rebased = manifest.relative_to(root).as_posix()
        rows.append("\t".join((name, version, compiler, "installed", rebased)))
    return rows


def components_from_lock(root: Path) -> dict[str, str]:
    checkout_dir, entries = load_contract(root, root / "workspace.toml", root / "workspace.lock")
    components = {}
    for entry in entries:
        target = checkout_dir / entry["checkout"]
        good, detail = inspect(target, entry)
        if not good:
            raise ValueError(f"{entry['id']}: {detail}; restore the lock before generating")
        if entry["id"] in PACKAGE_OWNERS:
            components[entry["id"]] = target.relative_to(root).as_posix()
    return components


def generate(root: Path, components: dict[str, str], output: str, force: bool) -> Path:
    if not SAFE_NAME.fullmatch(output) or output in (".", ".."):
        raise ValueError("output must be one safe filename at the catalog root")
    if not root.is_dir() or root.is_symlink():
        raise ValueError("catalog root must be an existing regular directory")
    root = root.resolve()
    destination = root / output
    if destination.is_symlink() or (destination.exists() and not destination.is_file()):
        raise ValueError(f"refusing unsafe output: {destination}")
    seen: set[tuple[str, str]] = set()
    rows = []
    for identifier, relative in sorted(components.items()):
        component = child_path(root, relative)
        if not component.is_dir():
            raise ValueError(f"missing component checkout {identifier}: {component}")
        for row in read_catalog(root, component):
            fields = row.split("\t")
            identity = (fields[0], fields[1])
            if identity in seen:
                raise ValueError(f"duplicate package {identity[0]} {identity[1]}")
            seen.add(identity)
            rows.append(row)
    content = "sagan-package-index-v1\n" + "".join(f"{row}\n" for row in sorted(rows))
    if destination.exists():
        if destination.read_text(encoding="utf-8") == content:
            return destination
        if not force:
            raise ValueError(f"existing catalog differs: {destination}; pass --force to replace it")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="\n", dir=root,
                                         prefix=f".{output}.", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(content)
        os.replace(temporary, destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--output", default=".sagan-package-index.tsv")
    parser.add_argument("--component", action="append", default=[], metavar="ID=RELATIVE_PATH")
    parser.add_argument("--from-lock", action="store_true")
    parser.add_argument("--force", action="store_true")
    arguments = parser.parse_args()
    try:
        if arguments.from_lock and arguments.component:
            raise ValueError("--from-lock and --component are mutually exclusive")
        if not arguments.from_lock and not arguments.component:
            raise ValueError("choose --from-lock or at least one --component")
        root = arguments.root.resolve()
        components = components_from_lock(root) if arguments.from_lock else {}
        if arguments.from_lock and not components:
            raise ValueError("no active physics/render package repositories in workspace.lock")
        for item in arguments.component:
            identifier, separator, relative = item.partition("=")
            if not separator or not identifier or not relative or identifier in components:
                raise ValueError(f"invalid or duplicate --component: {item!r}")
            components[identifier] = relative
        destination = generate(root, components, arguments.output, arguments.force)
        print(f"Package catalog: {destination} ({len(destination.read_text(encoding='utf-8').splitlines()) - 1} packages)")
        return 0
    except (OSError, RuntimeError, ValueError, tomllib.TOMLDecodeError) as error:
        print(f"Package catalog generation failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
