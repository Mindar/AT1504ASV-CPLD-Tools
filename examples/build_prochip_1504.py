"""Licensed Precision → EDIF → FIT1504 → optional offline SVF.

The included AND-gate fixtures use example pins 6, 8, and 14. This is a
target-specific bring-up build; adapt the pins and checks to the actual PCB.
"""

import argparse
import hashlib
import json
import shutil
from pathlib import Path

from toolchain import PROCHIP, new_work_directory, require_file, run_precision, run_tool


def tcl_path(path):
    text = Path(path).as_posix()
    if any(character in text for character in "{}\n\r"):
        raise ValueError("Use paths without braces or newlines")
    return "{" + text + "}"


def build(directory, language="verilog", svf=False):
    work = new_work_directory(directory)
    suffix = ".v" if language == "verilog" else ".vhd"
    source = Path(__file__).absolute().with_name("prochip1504" + suffix)
    shutil.copy2(source, work / source.name)
    script = work / "synthesize.tcl"
    script.write_text(f"""if {{[catch {{
    new_project -name prochip1504 -folder {tcl_path(work)}
    new_impl -name implementation
    setup_design -manufacturer Atmel -family ATF15xxASV -part ATF1504ASV-15AU100 -speed -15
    setup_design -design prochip1504 -basename prochip1504 -edif
    add_input_file {tcl_path(work / source.name)}
    compile
    synthesize
    report_area -cell_usage -hierarchy -all_leafs
    save_impl
    save_project
    puts {{BUILD_COMPLETED}}
}} message]}} {{
    puts stderr "BUILD_FAILED: $message"
}}
exit -force
""", encoding="ascii")

    log = run_precision(script, work, timeout=120)
    transcript = log.read_text(encoding="cp1252", errors="replace")
    if "BUILD_COMPLETED" not in transcript or "# Error:" in transcript:
        raise RuntimeError(f"Precision did not complete cleanly. See {log}")
    edif = require_file(work / "implementation/prochip1504.edf")
    if "atf15asv" not in edif.read_text(encoding="cp1252").lower():
        raise RuntimeError("EDIF does not reference the expected ASV library")

    fit_work = work / "fit"
    fit_work.mkdir()
    shutil.copy2(edif, fit_work / edif.name)
    # ProChip's EDIF fitting flow reads a same-basename PIN sidecar. The
    # fitter does not apply Precision's EDIF pin_number properties by itself.
    pin_text = 'CHIP "prochip1504" ASSIGNED TO AN TQFP100\na : 6\nb : 8\ny : 14\n'
    (fit_work / "prochip1504.pin").write_text(pin_text, encoding="ascii")
    (fit_work / "requested-pins.txt").write_text(pin_text, encoding="ascii")
    fit_log = run_tool([
        PROCHIP / "pldfit/fit1504.exe", "-i", edif.name,
        "-ifmt", "EDIF", "-lib", PROCHIP / "pldfit/aprim.lib",
        "-device", "TQFP100", "-tech", "ATF1504ASV",
        "-preassign", "keep", "-str", "JTAG=ON", "-str", "security=OFF",
        "-str", "tPD=15",
    ], fit_work, "fitter-console.log")
    jed = require_file(fit_work / "prochip1504.jed")
    report = require_file(fit_work / "prochip1504.fit").read_text(encoding="cp1252")
    expected = ["Device_name = TQFP100", "Tech_name = ATF1504ASV",
                "Preassignment = keep", "Security_mode = OFF", "JTAG = ON"]
    for signal, pin in {"a": 6, "b": 8, "y": 14, "TDI": 4,
                        "TMS": 15, "TCK": 62, "TDO": 73}.items():
        expected.append(f"{signal} is placed at pin {pin}")
    for setting in expected:
        if setting.lower() not in report.lower():
            raise RuntimeError(f"Expected setting missing from FIT report: {setting}")
    if "Design fits successfully" not in fit_log.read_text(encoding="cp1252"):
        raise RuntimeError("Fitter success marker missing")

    artifacts = [edif, jed, fit_work / "prochip1504.fit"]
    if svf:
        from atmisp_svf import export_svf
        artifacts.append(export_svf(jed, work / "svf"))
    summary = {
        "target": "ATF1504ASV-15AU100", "language": language,
        "synthesis": "passed", "fitting_and_pins": "passed",
        "svf_export": "passed" if svf else "not requested",
        "hdl_simulation": "not requested; this validates synthesis, fitting, and optional SVF export",
        "hardware_programming": "not tested; no programmer attached",
        "artifacts": {str(path.relative_to(work)): {
            "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        } for path in artifacts},
    }
    (work / "validation.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"Project: {work / 'prochip1504.psp'}")
    return jed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("work", type=Path, help="New local/mapped-drive output directory")
    parser.add_argument("--language", choices=["verilog", "vhdl"], default="verilog")
    parser.add_argument("--svf", action="store_true", help="Export offline SVF on the interactive desktop")
    args = parser.parse_args()
    build(args.work, args.language, args.svf)


if __name__ == "__main__":
    main()
