"""Offline tests for the exact-commit workspace bootstrap contract."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import workspace  # noqa: E402


def run(*arguments: str, cwd: Path) -> str:
    result = subprocess.run(
        ["git", *arguments], cwd=cwd, text=True, capture_output=True, check=True
    )
    return result.stdout.strip()


class WorkspaceTest(unittest.TestCase):
    def test_checked_in_manifest_matches_lock(self) -> None:
        root = Path(__file__).resolve().parents[1]
        checkouts, entries = workspace.load_contract(
            root, root / "workspace.toml", root / "workspace.lock"
        )
        self.assertEqual(root / "checkouts", checkouts)
        self.assertEqual(["sagan"], [entry["id"] for entry in entries])
        self.assertEqual(40, len(entries[0]["commit"]))

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="sagan-workspace-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / "source"
        self.source.mkdir()
        run("init", "-b", "dev", cwd=self.source)
        (self.source / "example.txt").write_text("first revision\n", encoding="utf-8")
        run("add", "example.txt", cwd=self.source)
        run("-c", "commit.gpgsign=false", "-c", "user.name=Sagan Test", "-c", "user.email=test@example.invalid",
            "commit", "-m", "Fixture", cwd=self.source)
        self.commit = run("rev-parse", "HEAD", cwd=self.source)
        self.manifest = self.root / "workspace.toml"
        self.lock = self.root / "workspace.lock"
        self.write_contract()

    def write_contract(self, *, state: str = "active", checkout_root: str = "checkouts",
                       commit: str | None = None, lock_url: str | None = None) -> None:
        source = self.source.as_posix()
        self.manifest.write_text(
            'schema_version = 1\n'
            f'checkout_root = "{checkout_root}"\n'
            '[[repositories]]\n'
            'id = "sagan"\n'
            f'url = "{source}"\n'
            'checkout = "sagan"\n'
            f'state = "{state}"\n',
            encoding="utf-8",
        )
        self.lock.write_text(
            'schema_version = 1\n'
            '[[repositories]]\n'
            'id = "sagan"\n'
            f'url = "{lock_url or source}"\n'
            f'commit = "{commit or self.commit}"\n',
            encoding="utf-8",
        )

    def load(self) -> tuple[Path, list[dict]]:
        return workspace.load_contract(self.root, self.manifest, self.lock)

    def test_bootstrap_exact_commit_is_idempotent(self) -> None:
        checkouts, entries = self.load()
        self.assertEqual(1, workspace.status(checkouts, entries))
        self.assertEqual(0, workspace.bootstrap(checkouts, entries))
        self.assertEqual(0, workspace.status(checkouts, entries))
        target = checkouts / "sagan"
        self.assertEqual(self.commit, run("rev-parse", "HEAD", cwd=target))
        self.assertEqual("", run("branch", "--show-current", cwd=target))
        self.assertEqual(0, workspace.bootstrap(checkouts, entries))

    def test_dirty_and_wrong_commit_are_not_overwritten(self) -> None:
        checkouts, entries = self.load()
        self.assertEqual(0, workspace.bootstrap(checkouts, entries))
        target = checkouts / "sagan"
        (target / "personal.txt").write_text("do not discard\n", encoding="utf-8")
        self.assertEqual(1, workspace.bootstrap(checkouts, entries))
        self.assertEqual("do not discard\n", (target / "personal.txt").read_text(encoding="utf-8"))
        (target / "personal.txt").unlink()

        (self.source / "example.txt").write_text("second revision\n", encoding="utf-8")
        run("add", "example.txt", cwd=self.source)
        run("-c", "commit.gpgsign=false", "-c", "user.name=Sagan Test", "-c", "user.email=test@example.invalid",
            "commit", "-m", "Second fixture", cwd=self.source)
        second = run("rev-parse", "HEAD", cwd=self.source)
        self.write_contract(commit=second)
        checkouts, entries = self.load()
        self.assertEqual(1, workspace.bootstrap(checkouts, entries))
        self.assertEqual(self.commit, run("rev-parse", "HEAD", cwd=target))

    def test_existing_checkout_must_have_matching_origin(self) -> None:
        checkouts, entries = self.load()
        self.assertEqual(0, workspace.bootstrap(checkouts, entries))
        target = checkouts / "sagan"
        run("remote", "set-url", "origin", "https://example.invalid/other.git", cwd=target)
        self.assertEqual(1, workspace.status(checkouts, entries))
        self.assertEqual(1, workspace.bootstrap(checkouts, entries))
        self.assertEqual(1, workspace.restore_lock(checkouts, entries))
        self.assertEqual(self.commit, run("rev-parse", "HEAD", cwd=target))

    def test_restore_fetches_new_lock_without_discarding_work(self) -> None:
        checkouts, entries = self.load()
        self.assertEqual(0, workspace.bootstrap(checkouts, entries))
        (self.source / "example.txt").write_text("second revision\n", encoding="utf-8")
        run("add", "example.txt", cwd=self.source)
        run("-c", "commit.gpgsign=false", "-c", "user.name=Sagan Test",
            "-c", "user.email=test@example.invalid", "commit", "-m", "Second fixture",
            cwd=self.source)
        second = run("rev-parse", "HEAD", cwd=self.source)
        self.write_contract(commit=second)
        checkouts, entries = self.load()
        target = checkouts / "sagan"
        self.assertEqual(1, workspace.status(checkouts, entries))
        self.assertEqual(0, workspace.restore_lock(checkouts, entries))
        self.assertEqual(second, run("rev-parse", "HEAD", cwd=target))
        self.assertEqual(0, workspace.restore_lock(checkouts, entries))

    def test_restore_refuses_dirty_checkout(self) -> None:
        checkouts, entries = self.load()
        self.assertEqual(0, workspace.bootstrap(checkouts, entries))
        target = checkouts / "sagan"
        (target / "my-work.txt").write_text("keep me\n", encoding="utf-8")
        self.assertEqual(1, workspace.restore_lock(checkouts, entries))
        self.assertEqual("keep me\n", (target / "my-work.txt").read_text(encoding="utf-8"))

    def test_restore_refuses_to_overwrite_ignored_file(self) -> None:
        checkouts, entries = self.load()
        self.assertEqual(0, workspace.bootstrap(checkouts, entries))
        target = checkouts / "sagan"
        (self.source / "collision.txt").write_text("tracked new version\n", encoding="utf-8")
        run("add", "collision.txt", cwd=self.source)
        run("-c", "commit.gpgsign=false", "-c", "user.name=Sagan Test",
            "-c", "user.email=test@example.invalid", "commit", "-m", "New file",
            cwd=self.source)
        second = run("rev-parse", "HEAD", cwd=self.source)
        self.write_contract(commit=second)
        checkouts, entries = self.load()
        (target / ".git" / "info" / "exclude").write_text("collision.txt\n", encoding="utf-8")
        (target / "collision.txt").write_text("precious ignored data\n", encoding="utf-8")
        self.assertEqual(1, workspace.restore_lock(checkouts, entries))
        self.assertEqual("precious ignored data\n", (target / "collision.txt").read_text(encoding="utf-8"))
        self.assertEqual(self.commit, run("rev-parse", "HEAD", cwd=target))

    def test_lock_must_match_active_manifest(self) -> None:
        self.write_contract(lock_url="https://example.invalid/other.git")
        with self.assertRaisesRegex(ValueError, "lock URL differs"):
            self.load()
        self.write_contract(commit="123")
        with self.assertRaisesRegex(ValueError, "full lowercase commit SHA"):
            self.load()

    def test_nonactive_repository_is_not_bootstrapped(self) -> None:
        for state in ("planned", "existing-outside-organization", "archived"):
            with self.subTest(state=state):
                self.write_contract(state=state)
                self.lock.write_text("schema_version = 1\nrepositories = []\n", encoding="utf-8")
                checkouts, entries = self.load()
                self.assertEqual([], entries)
                self.assertEqual(0, workspace.bootstrap(checkouts, entries))
                self.assertFalse((checkouts / "sagan").exists())

    def test_checkout_root_rejects_traversal_and_drive_paths(self) -> None:
        for path in ("../outside", "nested/path", r"C:\\outside", ".git", ""):
            with self.subTest(path=path):
                self.write_contract(checkout_root=path)
                with self.assertRaisesRegex(ValueError, "single safe directory"):
                    self.load()


if __name__ == "__main__":
    unittest.main()
