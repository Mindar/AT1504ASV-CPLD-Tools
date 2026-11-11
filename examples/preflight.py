"""Check a Windows workstation before building; no downloads or installation.

The optional synthesis check uses the installed licensed tools. Reports may
contain local paths, so keep the chosen output directory private.
"""

import argparse
import json
import os
import platform
import shutil
import sys
from pathlib import Path

from toolchain import ATMISP, PLS_TOOLS, PRECISION, PROCHIP, new_work_directory


def inspect(work, svf=False):
    checks = []

    def record(name, passed, detail):
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    record("Windows", os.name == "nt", platform.platform())
    record("Python API version", sys.version_info >= (3, 8), sys.version.split()[0])
    record("Writable output", work.is_dir(), str(work))
    text = str(work)
    record("Simple local/mapped path",
           text.isascii() and not any(character.isspace() for character in text)
           and not any(character in text for character in "{}\n\r") and not text.startswith("\\\\"),
           "Prefer a short ASCII path without spaces or UNC expansion")
    files = {
        "Precision": PRECISION,
        "FIT1504": PROCHIP / "pldfit/fit1504.exe",
        "EDIF primitive library": PROCHIP / "pldfit/aprim.lib",
        "ASV technology library": PLS_TOOLS / "Precision/pkgs/psr/techlibs/atf15asv.syn",
        "Verilog example": Path(__file__).absolute().with_name("prochip1504.v"),
        "VHDL example": Path(__file__).absolute().with_name("prochip1504.vhd"),
    }
    if svf:
        files["ATMISP"] = ATMISP
    for name, path in files.items():
        record(name, path.is_file(), str(path))
    record("Timeout cleanup", shutil.which("taskkill") is not None,
           "Windows taskkill must be permitted for the launched process tree")
    return checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("work", type=Path, help="NEW short ASCII output directory")
    parser.add_argument("--synthesize", action="store_true", help="Run a real licensed example build")
    parser.add_argument("--language", choices=["verilog", "vhdl"], default="verilog")
    parser.add_argument("--svf", action="store_true", help="Also check/export ATMISP; requires --synthesize")
    args = parser.parse_args()
    if args.svf and not args.synthesize:
        parser.error("--svf requires --synthesize")
    work = new_work_directory(args.work)
    checks = inspect(work, svf=args.svf)
    report = {"checks": checks, "synthesis": "not requested",
              "license": "not verified until a real synthesis succeeds"}
    destination = work / "preflight.json"
    for check in checks:
        print(f"{'PASS' if check['passed'] else 'FAIL'}: {check['name']} — {check['detail']}")
    try:
        if any(not check["passed"] for check in checks):
            raise RuntimeError("Prerequisites failed; resolve them before building")
        if args.synthesize:
            from build_prochip_1504 import build
            build(work / "smoke", language=args.language, svf=args.svf)
            report["synthesis"] = "passed"
            report["license"] = "checkout succeeded for this run"
        else:
            print("Static checks passed. Executable permissions and license validity remain unverified.")
    except Exception as error:
        report["error"] = f"{type(error).__name__}: {error}"
        print(report["error"], file=sys.stderr)
        raise SystemExit(1)
    finally:
        destination.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"Report: {destination}")


if __name__ == "__main__":
    main()
