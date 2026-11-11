"""Check the source publication boundary and independent example imports."""

import ast
import contextlib
import importlib.util
import io
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).absolute().parents[1]
SPEC = importlib.util.spec_from_file_location("publication", ROOT / "scripts/prepare_publication.py")
publication = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(publication)


class PublicationTests(unittest.TestCase):
    def test_allowlist_excludes_license_binaries_and_research(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "input"
            root.mkdir()
            for name in publication.ROOT_FILES:
                (root / name).write_text("example", encoding="utf-8")
            for directory in ("docs", "examples", "tests", "scripts", "research", "standalone"):
                (root / directory).mkdir()
            (root / "standalone/README.md").write_text("examples")
            (root / "examples/example.py").write_text("print('hello')")
            (root / "examples/tool.exe").write_bytes(b"binary")
            (root / "license.dat").write_text("private")
            (root / "research/private.txt").write_text("private")
            destination = Path(temporary) / "output"
            with contextlib.redirect_stdout(io.StringIO()):
                manifest = publication.prepare(root, destination)
            names = set(manifest["files"])
            self.assertIn("examples/example.py", names)
            self.assertNotIn("examples/tool.exe", names)
            self.assertFalse((destination / "license.dat").exists())
            self.assertFalse((destination / "research").exists())

    def test_suspicious_token_stops_publication(self):
        with tempfile.TemporaryDirectory() as temporary:
            file = Path(temporary) / "example.py"
            file.write_text("token = '" + "ghp_" + "A" * 30 + "'")
            with self.assertRaisesRegex(ValueError, "GitHub token"):
                publication.inspect_file(file)

    def test_independent_examples_use_only_local_or_standard_imports(self):
        standard = {"argparse", "ctypes", "hashlib", "json", "os", "pathlib", "platform",
                    "shutil", "subprocess", "sys", "tempfile", "time"}
        directories = [path for path in (ROOT / "standalone").iterdir()
                       if path.is_dir() and path.name[:2].isdigit()]
        self.assertEqual(len(directories), 6)
        for directory in directories:
            files = list(directory.glob("*.py"))
            local = {file.stem for file in files}
            for file in files:
                tree = ast.parse(file.read_text(encoding="utf-8"))
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        imports = [alias.name.split(".")[0] for alias in node.names]
                    elif isinstance(node, ast.ImportFrom):
                        self.assertEqual(node.level, 0, str(file))
                        imports = [node.module.split(".")[0]]
                    else:
                        continue
                    for name in imports:
                        self.assertIn(name, standard | local, f"{file}: external import {name}")


if __name__ == "__main__":
    unittest.main()
