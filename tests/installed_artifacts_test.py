import hashlib
from pathlib import Path
import tempfile
import unittest

from scripts.installed_artifacts import fetch, load_lock


class InstalledArtifactsTest(unittest.TestCase):
    def test_checked_in_lock_is_well_formed(self):
        artifacts = load_lock(Path("installed-artifacts.lock"))
        self.assertEqual(
            {artifact["id"] for artifact in artifacts},
            {"sagan-toolchain", "sagan-vscode", "sagan-physics", "sagan-render"},
        )

    def test_fetch_verifies_file_url_and_rejects_corruption(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "artifact.zip"
            source.write_bytes(b"verified artifact")
            checksum = hashlib.sha256(source.read_bytes()).hexdigest()
            artifact = {"id": "fixture", "url": source.as_uri(), "sha256": checksum}
            output = fetch(artifact, root / "downloads")
            self.assertEqual(output.read_bytes(), source.read_bytes())
            artifact["sha256"] = "0" * 64
            with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                fetch(artifact, root / "other-downloads")


if __name__ == "__main__":
    unittest.main()
