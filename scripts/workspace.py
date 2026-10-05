"""Bootstrap and inspect exact-commit Sagan workspace checkouts."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import subprocess
import sys
import tomllib


DEFAULT_ROOT = Path(__file__).resolve().parent.parent
COMMIT = re.compile(r"[0-9a-f]{40}\Z")
SLUG = re.compile(r"[a-z0-9][a-z0-9-]*\Z")


def git(*args: str, cwd: Path | None = None) -> str:
    result = subprocess.run(
        ["git", *args], cwd=cwd, text=True, capture_output=True, check=False
    )
    if result.returncode:
        detail = (result.stderr or result.stdout).strip()
        raise RuntimeError(f"git {' '.join(args)} failed: {detail}")
    return result.stdout.strip()


def load_toml(path: Path) -> dict:
    with path.open("rb") as stream:
        return tomllib.load(stream)


def load_contract(root: Path, manifest_path: Path, lock_path: Path) -> tuple[Path, list[dict]]:
    manifest = load_toml(manifest_path)
    lock = load_toml(lock_path)
    if manifest.get("schema_version") != 1 or lock.get("schema_version") != 1:
        raise ValueError("workspace manifest and lock must use schema_version = 1")

    checkout_root = manifest.get("checkout_root")
    if not isinstance(checkout_root, str):
        raise ValueError("checkout_root must be a relative directory")
    if not SLUG.fullmatch(checkout_root):
        raise ValueError("checkout_root must be a single safe directory name")
    checkout_dir = root / checkout_root
    if checkout_dir.is_symlink():
        raise ValueError("checkout_root must not be a symlink")

    manifest_entries = manifest.get("repositories")
    lock_entries = lock.get("repositories")
    if not isinstance(manifest_entries, list) or not isinstance(lock_entries, list):
        raise ValueError("both files must contain repositories arrays")
    active: dict[str, dict] = {}
    all_ids: set[str] = set()
    all_paths: set[str] = set()
    for entry in manifest_entries:
        if not isinstance(entry, dict):
            raise ValueError("repository entries must be tables")
        identifier = entry.get("id")
        checkout = entry.get("checkout")
        if not isinstance(identifier, str) or not SLUG.fullmatch(identifier):
            raise ValueError(f"invalid repository id: {identifier!r}")
        if not isinstance(checkout, str) or not SLUG.fullmatch(checkout):
            raise ValueError(f"invalid checkout directory for {identifier}")
        if not isinstance(entry.get("url"), str) or not entry["url"].strip():
            raise ValueError(f"repository URL is required for {identifier}")
        if identifier in all_ids or checkout in all_paths:
            raise ValueError("repository IDs and checkout directories must be unique")
        all_ids.add(identifier)
        all_paths.add(checkout)
        if entry.get("state") == "active":
            active[identifier] = entry
        elif entry.get("state") not in ("planned", "existing-outside-organization", "archived"):
            raise ValueError(f"unsupported state for {identifier}: {entry.get('state')!r}")

    locked: dict[str, dict] = {}
    for entry in lock_entries:
        if not isinstance(entry, dict):
            raise ValueError("lock entries must be tables")
        identifier = entry.get("id")
        if identifier in locked:
            raise ValueError(f"duplicate lock entry: {identifier}")
        if identifier not in active:
            raise ValueError(f"lock contains a non-active repository: {identifier}")
        if entry.get("url") != active[identifier].get("url"):
            raise ValueError(f"lock URL differs from manifest for {identifier}")
        if not isinstance(entry.get("commit"), str) or not COMMIT.fullmatch(entry["commit"]):
            raise ValueError(f"lock requires a full lowercase commit SHA for {identifier}")
        locked[identifier] = entry
    if set(locked) != set(active):
        missing = sorted(set(active) - set(locked))
        raise ValueError(f"active repositories missing from lock: {', '.join(missing)}")
    return checkout_dir, [
        {**active[identifier], "commit": locked[identifier]["commit"]}
        for identifier in sorted(active)
    ]


def inspect(target: Path, entry: dict) -> tuple[bool, str]:
    if not target.exists():
        return False, "missing"
    if target.is_symlink() or not target.is_dir():
        return False, "unsafe or non-directory checkout"
    try:
        inside = git("-C", str(target), "rev-parse", "--show-toplevel")
        if Path(inside).resolve() != target.resolve():
            return False, "directory is inside another Git checkout"
        origin = git("-C", str(target), "remote", "get-url", "origin")
        if origin != entry["url"]:
            return False, "origin URL differs from the workspace manifest"
        head = git("-C", str(target), "rev-parse", "HEAD")
        dirty = bool(git("-C", str(target), "status", "--porcelain"))
    except RuntimeError as error:
        return False, str(error)
    if dirty:
        return False, f"dirty at {head[:12]}"
    if head != entry["commit"]:
        return False, f"HEAD {head[:12]} differs from lock {entry['commit'][:12]}"
    return True, f"clean at locked commit {head[:12]}"


def bootstrap(checkout_dir: Path, entries: list[dict]) -> int:
    checkout_dir.mkdir(parents=True, exist_ok=True)
    for entry in entries:
        target = checkout_dir / entry["checkout"]
        if target.exists() or target.is_symlink():
            good, message = inspect(target, entry)
            print(f"{entry['id']}: {message}")
            if not good:
                return 1
            continue
        print(f"{entry['id']}: cloning {entry['url']} at {entry['commit'][:12]}", flush=True)
        try:
            git("clone", "--no-checkout", entry["url"], str(target))
            git("-C", str(target), "checkout", "--detach", entry["commit"])
        except RuntimeError as error:
            raise RuntimeError(
                f"{error}. Preserve the partial checkout at {target} for inspection; "
                "do not overwrite it automatically."
            ) from error
        good, message = inspect(target, entry)
        print(f"{entry['id']}: {message}")
        if not good:
            return 1
    return 0


def status(checkout_dir: Path, entries: list[dict]) -> int:
    result = 0
    for entry in entries:
        good, message = inspect(checkout_dir / entry["checkout"], entry)
        print(f"{entry['id']}: {message}")
        if not good:
            result = 1
    return result


def restore_lock(checkout_dir: Path, entries: list[dict]) -> int:
    for entry in entries:
        target = checkout_dir / entry["checkout"]
        if not target.exists() and not target.is_symlink():
            if bootstrap(checkout_dir, [entry]):
                return 1
            continue
        if target.is_symlink() or not target.is_dir():
            print(f"{entry['id']}: unsafe or non-directory checkout")
            return 1
        try:
            inside = git("-C", str(target), "rev-parse", "--show-toplevel")
            if Path(inside).resolve() != target.resolve():
                print(f"{entry['id']}: directory is inside another Git checkout")
                return 1
            origin = git("-C", str(target), "remote", "get-url", "origin")
            if origin != entry["url"]:
                print(f"{entry['id']}: origin URL differs from the workspace manifest")
                return 1
            if git("-C", str(target), "status", "--porcelain", "--untracked-files=all"):
                print(f"{entry['id']}: dirty checkout; preserve your work before restoring")
                return 1
            head = git("-C", str(target), "rev-parse", "HEAD")
            if head == entry["commit"]:
                print(f"{entry['id']}: already at locked commit {head[:12]}")
                continue
            try:
                git("-C", str(target), "cat-file", "-e", f"{entry['commit']}^{{commit}}")
            except RuntimeError:
                print(f"{entry['id']}: fetching locked commit {entry['commit'][:12]}", flush=True)
                git("-C", str(target), "fetch", "--no-tags", "origin", entry["commit"])
            git("-C", str(target), "checkout", "--detach", "--no-overwrite-ignore", entry["commit"])
        except RuntimeError as error:
            print(f"{entry['id']}: {error}", file=sys.stderr)
            return 1
        good, message = inspect(target, entry)
        print(f"{entry['id']}: {message}")
        if not good:
            return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("bootstrap", "status", "restore-lock"))
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--lock", type=Path)
    arguments = parser.parse_args()
    root = arguments.root.resolve()
    manifest_path = arguments.manifest or root / "workspace.toml"
    lock_path = arguments.lock or root / "workspace.lock"
    try:
        checkout_dir, entries = load_contract(root, manifest_path, lock_path)
        if arguments.command == "bootstrap":
            return bootstrap(checkout_dir, entries)
        if arguments.command == "restore-lock":
            return restore_lock(checkout_dir, entries)
        return status(checkout_dir, entries)
    except (OSError, RuntimeError, ValueError, tomllib.TOMLDecodeError) as error:
        print(f"Workspace {arguments.command} failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
