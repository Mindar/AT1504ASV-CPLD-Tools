"""Create/check independent source-only examples from the supported scripts.

Each directory gets actual source copies, with no parent imports or symlinks.
Use --check to detect drift. --refresh explicitly updates generated copies.
"""

import argparse
from pathlib import Path


COMMON_NOTES = """
## Workstation preparation

Use Windows and an approved Python installation. No pip packages are required.
Provision the listed vendor tools through your normal approved process.
Use a short writable local path, and a new output directory for each run.

Default ProChip root: `C:\\ATMEL_PLS_Tools`. If yours differs, set
`ATMEL_PLS_TOOLS` in the current shell before running Python. Precision needs
a license valid for the machine; set `MGLS_LICENSE_FILE` as instructed by the
license administrator. The personal VM's license is host-bound.

These are complete source copies. They do not import from the parent project.
Build outputs and logs stay in the selected output directory. Adapt the example
pin assignments to the PCB before preparing files for hardware programming.
"""


def synthesis_readme(language):
    return f"""# {language.upper()} synthesis and fitting

Compile the included AND-gate HDL for ATF1504ASV-15AU100, then fit it with
fixed pins a=6, b=8, y=14 and JTAG enabled. Required tools: licensed Precision
OEM and the ProChip FIT1504/library installation.

From this directory:

```powershell
python run.py build\\run001
```

Inspect `build\\run001\\validation.json`, the `fit` directory's JED/FIT/PIN
files, and the saved Precision `.psp` project. The PIN sidecar is required;
the script creates it and checks the final placement.

For optional offline SVF export, also provision ATMISP and use an interactive
Windows desktop:

```powershell
python run.py build\\run002 --svf
```

Precision's pre-script startup stall is handled by a 15-second readiness
handshake and up to three starts. Acknowledgement gates the synthesis script;
errors or timeouts after synthesis starts are not retried. No hardware is
programmed by these commands. HDL simulation is outside this example.
{COMMON_NOTES}
"""


def synthesis_entry(language):
    return f'''"""Run this directory's self-contained {language.upper()} target example."""

import argparse
from pathlib import Path

from build_prochip_1504 import build


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("work", type=Path, help="New output directory")
    parser.add_argument("--svf", action="store_true", help="Export offline SVF through ATMISP")
    args = parser.parse_args()
    build(args.work, language="{language}", svf=args.svf)


if __name__ == "__main__":
    main()
'''


def definitions():
    synthesis_files = ["toolchain.py", "build_prochip_1504.py", "prochip1504.v",
                       "prochip1504.vhd", "atmisp_svf.py"]
    return {
        "01_verilog_synthesis": {
            "files": synthesis_files,
            "text": {"README.md": synthesis_readme("verilog"), "run.py": synthesis_entry("verilog")},
        },
        "02_vhdl_synthesis": {
            "files": synthesis_files,
            "text": {"README.md": synthesis_readme("vhdl"), "run.py": synthesis_entry("vhdl")},
        },
        "03_cupl_compile_simulate": {
            "files": ["toolchain.py", "build_1504.py", "and1504.pld", "and1504.si"],
            "text": {"README.md": """# CUPL compilation, functional simulation, and fitting

Required tools: WinCUPL and the ProChip FIT1504/library installation.
This directory includes the PLD design and all four AND-gate test vectors.

```powershell
python build_1504.py build\\run001
```

The command separately runs functional simulation, device-netlist generation,
and ASV/TQFP100 fitting. Check `and1504.so`, `and1504.fit`, and `and1504.jed`.
Expected vectors: 00L, 01L, 10L, 11H. Expected pins: a=6, b=8, y=14.
Simulation and JEDEC generation use separate CUPL calls to avoid the observed
combined -s/-j failure. Set WINCUPL_HOME if WinCUPL is not at C:\\Wincupl.
""" + COMMON_NOTES},
        },
        "04_offline_svf_export": {
            "files": ["toolchain.py", "atmisp_svf.py"],
            "text": {"README.md": """# Offline ATF1504ASV JEDEC-to-SVF export

Required tool: ATMISP 7.3.x. Requires an existing matching ATF1504ASV JEDEC
input and an interactive Windows desktop. All automation code is included;
there is no dependency on another example directory or an attached programmer.

```powershell
python atmisp_svf.py C:\\pldwork\\design.jed build\\export001
```

The script creates a single-device ATF1504ASV Program/Verify chain, selects
and verifies Write SVF file, sets the output path, and checks ATMISP's own
generation log. Inspect `design.svf` and `jtag.log` in the new output directory.
The erasing/programming/verifying log messages describe the offline stream.

Default ATMISP path: C:\\ATMISP7\\ATMISP.exe. Set ATMISP_HOME to its containing
directory if different. Native control IDs are specific to the tested version;
after an upgrade, inspect/revalidate them before using the GUI automation.
""" + COMMON_NOTES},
        },
        "05_workstation_preflight": {
            "files": synthesis_files + ["preflight.py"],
            "text": {"README.md": """# Workstation preflight and real synthesis smoke test

This directory contains every source file needed for its optional build.
Static checks require Python. Real synthesis requires licensed Precision OEM,
the ProChip fitter, and the ASV library.

```powershell
python preflight.py build\\check001
python preflight.py build\\check002 --synthesize
python preflight.py build\\check003 --synthesize --language vhdl
```

Static success verifies paths/files, not license checkout or execution policy.
Require a successful --synthesize run on the actual work PC under its normal
account before considering that machine ready. Inspect `preflight.json` and
`smoke\\validation.json`. Do not publish these workstation diagnostics.

Optional --svf also needs ATMISP and an interactive desktop. ModelSim and
WinCUPL are not dependencies of this HDL smoke test.
""" + COMMON_NOTES},
        },
        "06_pof_conversion": {
            "files": ["toolchain.py", "convert_pof.py"],
            "text": {"README.md": """# Convert a compatible POF to ATF15xx JEDEC

Required tool: POF2JED. Supply your own compatible MAX-series POF; no vendor
binary/design file is bundled. All Python code is included in this directory.

```powershell
python convert_pof.py C:\\pldwork\\design.pof build\\conversion001 --device 1504ASV
```

Review the generated TXT report and JED. The source POF supplies the package
and pin mapping: for the intended board it must match TQFP100 and the PCB pins.
The converter accepted an incompatible target override in testing and still
returned zero. Check density, package, voltage family, JTAG, and security.

Default converter path: C:\\POF2JED\\bin\\POF2JED.exe. Set POF2JED_HOME if needed.
The native Precision/CUPL build flows do not need this conversion step.
""" + COMMON_NOTES},
        },
    }


def synchronize(root, check=False, refresh=False):
    count = 0
    for name, definition in definitions().items():
        contents = {filename: (root / "examples" / filename).read_bytes()
                    for filename in definition["files"]}
        contents.update({filename: text.encode("utf-8") for filename, text in definition["text"].items()})
        directory = root / "standalone" / name
        for filename, data in contents.items():
            target = directory / filename
            same = target.is_file() and target.read_bytes() == data
            if check:
                if not same:
                    raise RuntimeError(f"Missing or outdated independent source: {target}")
            elif not same:
                if target.exists() and not refresh:
                    raise RuntimeError(f"Refusing to overwrite {target}; review changes and use --refresh")
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
            count += 1
    print(f"{'Checked' if check else 'Prepared'} {count} self-contained example files.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    synchronize(Path(__file__).absolute().parents[1], args.check, args.refresh)


if __name__ == "__main__":
    main()
