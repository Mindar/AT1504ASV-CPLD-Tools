"""Prepare a source-only GitHub upload folder; no Git installation required.

Uses an allowlist and basic secret checks. Review the output before publishing.
The original project, installed tools, and license files are not modified.
"""

import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).absolute().parent))
from public_docs import public_texts

ROOT_FILES = [".gitignore", "README.md", "QUICKSTART.md", "PRINTABLE_GUIDE.md"]
SOURCE_EXTENSIONS = {".py", ".v", ".vhd", ".pld", ".si", ".tcl", ".do"}
SECRET_PATTERNS = {
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "GitHub token": re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})"),
    "signed vendor license": re.compile(r"(?im)^\s*(?:FEATURE|INCREMENT)\s+\S+\s+\S+\s+\S+\s+\S+"),
}


def selected_files(root):
    files = [root / name for name in ROOT_FILES]
    files.extend(root / "docs" / name for name in
                 ("AUTOMATION.md", "ATMISP.md", "LICENSES.md", "PROCHIP_VALIDATION.md")
                 if (root / "docs" / name).is_file())
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
    return inspect_data(path.read_bytes(), path.name)


def inspect_data(data, name):
    if b"\0" in data or len(data) > 1_000_000:
        raise ValueError(f"Unexpected binary or large source file: {name}")
    text = data.decode("utf-8")
    for description, pattern in SECRET_PATTERNS.items():
        if pattern.search(text):
            raise ValueError(f"Possible {description} in {name}; publication stopped")
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def prepare(root, destination, refresh=False):
    files = selected_files(root)
    contents = {}
    for path in files:
        if path.is_symlink():
            raise ValueError(f"Symlink requires review: {path.name}")
        contents[path.relative_to(root).as_posix()] = path.read_bytes()
    contents.update({name: text.encode("utf-8") for name, text in public_texts().items()})
    manifest = {"schema": 1, "files": {}}
    # Check every file before creating/copying the publication directory.
    for name, data in contents.items():
        manifest["files"][name] = inspect_data(data, name)
    if destination.exists():
        if not refresh:
            raise FileExistsError(f"Use --refresh to update the generated publication: {destination}")
        previous = json.loads((destination / "PUBLICATION_MANIFEST.json").read_text(encoding="utf-8"))
        known = set(previous["files"]) | {"PUBLICATION_MANIFEST.json"}
        for path in destination.rglob("*"):
            if path.is_file() and path.relative_to(destination).as_posix() not in known:
                raise ValueError(f"Unrecognized publication file; nothing overwritten: {path}")
        for name, metadata in previous["files"].items():
            path = destination / name
            if hashlib.sha256(path.read_bytes()).hexdigest() != metadata["sha256"]:
                raise ValueError(f"Publication file was edited; nothing overwritten: {path}")
        for name in set(previous["files"]) - set(contents):
            (destination / name).unlink()
    else:
        destination.mkdir(parents=True, exist_ok=False)
    for name, data in contents.items():
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    (destination / "PUBLICATION_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Prepared {len(contents)} source/documentation files in {destination}")
    print("Research data, tool binaries, installers, and license files were excluded.")
    print("Review the folder before uploading. GitHub web uploads do not apply .gitignore.")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=None, help="NEW source-only output folder")
    parser.add_argument("--refresh", action="store_true", help="Replace unchanged generated publication files")
    args = parser.parse_args()
    root = Path(__file__).absolute().parents[1]
    destination = args.output.absolute() if args.output else root / "publication/source"
    prepare(root, destination, args.refresh)


if __name__ == "__main__":
    main()
