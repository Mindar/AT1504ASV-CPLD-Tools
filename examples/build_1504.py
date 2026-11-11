"""Compile, simulate, and fit the ATF1504ASV / TQFP100 AND-gate example."""

import argparse
from pathlib import Path

from toolchain import WINCUPL, compile_cupl, fit_tt2, require_file, run_tool


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("work", type=Path, help="New output directory")
    args = parser.parse_args()
    source = Path(__file__).with_name("and1504.pld")
    # A CPLD's functional simulation need not append vectors to a JEDEC file.
    # Omitting -j avoids CSIM's undefined-pin/JED-vector failure on this device.
    work = compile_cupl(source, args.work, simulate=True, jedec_vectors=False)
    require_file(work / "and1504.so")
    simulation = (work / "and1504.so").read_text(encoding="cp1252", errors="replace")
    for vector in ("0001: 00L", "0002: 01L", "0003: 10L", "0004: 11H"):
        if vector not in simulation:
            raise RuntimeError(f"Expected successful simulation vector not found: {vector}")
    # Request the device build separately, now without -s. This emits the TT2
    # that our explicit ProChip fitter consumes, regardless of auto-fit results.
    run_tool([WINCUPL / "Shared/cupl.exe", "-m1anlxj", "-u",
              WINCUPL / "Shared/Atmel.dl", source.name], work, "cupl-build.log")
    jed = fit_tt2(work / "and1504.tt2", 1504, "TQFP100", "ATF1504ASV")
    report = (work / "and1504.fit").read_text(encoding="cp1252", errors="replace")
    expected_settings = ("Tech_name = ATF1504ASV", "Device_name = TQFP100",
                         "Security_mode = OFF", "JTAG = ON",
                         "y is placed at pin 14", "b is placed at pin 8", "a is placed at pin 6")
    for setting in expected_settings:
        if setting not in report:
            raise RuntimeError(f"Expected target setting not found in FIT report: {setting}")
    print(jed)
    print("Build only: inspect FIT/SO reports and adapt PCB pins before programming.")


if __name__ == "__main__":
    main()
