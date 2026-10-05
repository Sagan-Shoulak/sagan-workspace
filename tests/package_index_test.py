"""Offline tests for combining independently owned Sagan packages."""

from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import package_index  # noqa: E402


class PackageIndexTest(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="sagan-package-index-test-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def component(self, checkout: str, name: str, *, index_path: str | None = None) -> None:
        libraries = self.root / checkout / "libraries"
        manifest = libraries / name / "sagan.toml"
        manifest.parent.mkdir(parents=True)
        manifest.write_text(
            f'[package]\nname = "{name}"\nversion = "1.2.3"\nsource = "src"\n',
            encoding="utf-8",
        )
        relative = index_path or f"{name}/sagan.toml"
        (libraries / "index.tsv").write_text(
            f"sagan-package-index-v1\n{name}\t1.2.3\t^4.0.0\tinstalled\t{relative}\n",
            encoding="utf-8",
        )

    def test_combines_relative_manifest_paths(self) -> None:
        self.component("physics", "sagan-physics")
        self.component("render", "sagan-render")
        output = package_index.generate(
            self.root, {"physics": "physics", "render": "render"}, "index.tsv", False
        )
        self.assertEqual(
            "sagan-package-index-v1\n"
            "sagan-physics\t1.2.3\t^4.0.0\tinstalled\tphysics/libraries/sagan-physics/sagan.toml\n"
            "sagan-render\t1.2.3\t^4.0.0\tinstalled\trender/libraries/sagan-render/sagan.toml\n",
            output.read_text(encoding="utf-8"),
        )
        self.assertEqual(output, package_index.generate(
            self.root, {"physics": "physics", "render": "render"}, "index.tsv", False
        ))

    def test_normalizes_root_before_containment_checks(self) -> None:
        self.component("physics", "sagan-physics")
        (self.root / "alias").mkdir()
        noncanonical_root = self.root / "alias" / ".."
        output = package_index.generate(
            noncanonical_root, {"physics": "physics"}, "index.tsv", False
        )
        self.assertEqual(self.root.resolve() / "index.tsv", output)

    def test_rejects_component_outside_root(self) -> None:
        self.component("physics", "sagan-physics")
        with self.assertRaisesRegex(ValueError, "unsafe relative path"):
            package_index.generate(self.root, {"physics": "../physics"}, "index.tsv", False)
        self.assertFalse((self.root / "index.tsv").exists())

    def test_rejects_manifest_traversal(self) -> None:
        self.component("physics", "sagan-physics", index_path="../../escape/sagan.toml")
        with self.assertRaisesRegex(ValueError, "unsafe relative path"):
            package_index.generate(self.root, {"physics": "physics"}, "index.tsv", False)
        self.assertFalse((self.root / "index.tsv").exists())

    def test_refuses_different_existing_output_without_force(self) -> None:
        self.component("physics", "sagan-physics")
        output = self.root / "index.tsv"
        output.write_text("owner data\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "existing catalog differs"):
            package_index.generate(self.root, {"physics": "physics"}, "index.tsv", False)
        self.assertEqual("owner data\n", output.read_text(encoding="utf-8"))
        package_index.generate(self.root, {"physics": "physics"}, "index.tsv", True)
        self.assertTrue(output.read_text(encoding="utf-8").startswith("sagan-package-index-v1\n"))

    def test_rejects_duplicate_identity(self) -> None:
        self.component("first", "sagan-physics")
        self.component("second", "sagan-physics")
        with self.assertRaisesRegex(ValueError, "duplicate package"):
            package_index.generate(
                self.root, {"first": "first", "second": "second"}, "index.tsv", False
            )


if __name__ == "__main__":
    unittest.main()
