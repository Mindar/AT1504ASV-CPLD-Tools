"""Prepare a source-only GitHub upload folder; no Git installation required.

Uses an allowlist and basic secret checks. Review the output before publishing.
The original project, installed tools, and license files are not modified.
"""

import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path


ROOT_FILES = [".gitignore", "README.md", "QUICKSTART.md", "PRINTABLE_GUIDE.md", "TOMORROW.md"]
SOURCE_EXTENSIONS = {".py", ".v", ".vhd", ".pld", ".si", ".tcl", ".do"}
SECRET_PATTERNS = {
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "GitHub token": re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})"),
    "signed vendor license": re.compile(r"(?im)^\s*(?:FEATURE|INCREMENT)\s+\S+\s+\S+\s+\S+\s+\S+"),
}


def selected_files(root):
    files = [root / name for name in ROOT_FILES]
    files.extend((root / "docs").glob("*.md"))
    for directory in ("examples", "tests", "scripts"):
        files.extend(path for path in (root / directory).iterdir()
                     if path.is_file() and path.suffix.lower() in SOURCE_EXTENSIONS)
    # Numbered examples are flat and allowlisted; never walk their build output.
    files.append(root / "standalone/README.md")
    for directory in (root / "standalone").iterdir():
        if directory.is_dir() and re.match(r"^\d\d_", directory.name):
            files.extend(path for path in directory.iterdir() if path.is_file()
                         and (path.name == "README.md" or path.suffix.lower() in SOURCE_EXTENSIONS))
    return sorted(set(files), key=lambda path: str(path.relative_to(root)))


def inspect_file(path):
    if path.is_symlink():
        raise ValueError(f"Symlink requires manual review: {path.name}")
    data = path.read_bytes()
    if b"\0" in data or len(data) > 1_000_000:
        raise ValueError(f"Unexpected binary or large source file: {path.name}")
    text = data.decode("utf-8")
    for description, pattern in SECRET_PATTERNS.items():
        if pattern.search(text):
            raise ValueError(f"Possible {description} in {path.name}; publication stopped")
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def prepare(root, destination):
    files = selected_files(root)
    manifest = {"schema": 1, "files": {}}
    # Check every file before creating/copying the publication directory.
    for path in files:
        manifest["files"][path.relative_to(root).as_posix()] = inspect_file(path)
    destination.mkdir(parents=True, exist_ok=False)
    for path in files:
        target = destination / path.relative_to(root)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
    (destination / "PUBLICATION_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Prepared {len(files)} source/documentation files in {destination}")
    print("Research data, tool binaries, installers, and license files were excluded.")
    print("Review the folder before uploading. GitHub web uploads do not apply .gitignore.")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=None, help="NEW source-only output folder")
    args = parser.parse_args()
    root = Path(__file__).absolute().parents[1]
    destination = args.output.absolute() if args.output else root / "publication/source"
    prepare(root, destination)


if __name__ == "__main__":
    main()
