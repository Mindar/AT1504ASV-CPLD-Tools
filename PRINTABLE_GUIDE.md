# ATF1504ASV development

This guide contains the settings, tool calls, and Python structure needed to recreate the workflow locally.

## 1. Target and tool setup

Target: **ATF1504ASV, 100-pin TQFP**, likely ordering code **ATF1504ASV-15AU100**. Confirm the complete device marking and PCB schematic.

| Setting | Value |
|---|---|
| CUPL device | `f1504isptqfp100` |
| Fitter technology | `ATF1504ASV` |
| Fitter package | `TQFP100` |
| Pin assignment policy | `KEEP` |
| JTAG | `ON` |
| Development security | `OFF` |

Reserve the package's JTAG pins: **TDI 4, TMS 15, TCK 62, TDO 73**. The ASV device uses a 3.3 V supply arrangement; consult its datasheet for the full power-pin and electrical requirements. Datasheet reference: **Microchip DS20006185A, ATF1504ASV/ATF1504ASVL**, particularly the 100-lead TQFP pinout tables.

| Component | Executable/location |
|---|---|
| WinCUPL compiler | `C:\Wincupl\Shared\cupl.exe` |
| CUPL device library | `C:\Wincupl\Shared\Atmel.dl` |
| ProChip fitter | `C:\ATMEL_PLS_Tools\ProChip\pldfit\fit1504.exe` |
| Precision synthesis | `C:\ATMEL_PLS_Tools\Precision\bin\precision.exe` |
| ModelSim | `C:\ATMEL_PLS_Tools\ModelSim\win32aoem\vsim.exe` |
| ATMISP | `C:\ATMISP7\ATMISP.exe` |

Relevant tested versions: WinCUPL installation 5.30.4; ProChip distribution 5.0.2; ProChip fitter **1918 (3-21-07)**; Precision **2013a.10OEM_Atmelcpld**; ModelSim ATMEL **6.2c**; ATMISP distribution **7.3.1**.

Use the ProChip fitter by its full path. WinCUPL's installation also contains an older fitter, **1.8.7.8**, whose arguments differ. The ProChip fitter accepts package and technology separately, as shown here.

## 2. Build sequence and exact commands

For a CUPL project named `design`, keep `design.pld` and its functional test vectors, `design.si`, together. Run each build in a new directory containing copies of those files.

### A. Compile and run functional simulation

```text
C:\Wincupl\Shared\cupl.exe -m1anlxs -u C:\Wincupl\Shared\Atmel.dl design.pld
```

Relevant options: `m1` quick minimization; `a` absolute output; `n` source-based output names; `l` listing; `x` expanded documentation; `s` simulation; `u` device library. Inspect `design.so` for the simulation result.

### B. Generate the device netlist

```text
C:\Wincupl\Shared\cupl.exe -m1anlxj -u C:\Wincupl\Shared\Atmel.dl design.pld
```

The `j` stage produces the `design.tt2` needed by the fitter. CUPL may invoke its automatic fitter during this operation. The next step explicitly runs the selected ProChip fitter.

Keep these two compiler calls separate. On the tested ATF1504 design, combining simulation and JEDEC generation in one call produced undefined-pin/JEDEC-vector errors. Simulation without `j`, followed by device generation without `s`, worked.

### C. Fit the target device

```text
C:\ATMEL_PLS_Tools\ProChip\pldfit\fit1504.exe -i design.tt2 -cupl -device TQFP100 -tech ATF1504ASV -preassign keep -str JTAG=ON -str security=OFF
```

Check `design.fit` for:

```text
Device_name = TQFP100
Tech_name = ATF1504ASV
Preassignment = keep
Security_mode = OFF
JTAG = ON
```

Also check the final placement of every constrained signal. `KEEP` preserves assigned pins; the fitter's default `TRY` policy can relax assignments on a later fitting attempt.

The resulting `design.jed` contains the programming data. Keep its FIT report and command logs. The tested JED's generic header said `ATF1504AS` even though the FIT report correctly recorded `ATF1504ASV`; use the complete build record to identify the variant.

## 3. A compact Python implementation

The following is a complete standard-library script. Save it as `build.py`. It incorporates the essential functionality of the previously developed `toolchain.py`: child environment setup, controlled working directory, argument handling, logging, timeouts, fresh outputs, and result checks.

`EXPECTED_PINS` below matches the small example in section 4. Update it for the actual PCB. This implementation stages one source and one vector file; add the project's include files and other dependencies when needed.

```python
import os
import shutil
import subprocess
import sys
from pathlib import Path


WINCUPL = Path(r"C:\Wincupl")
FITTERS = Path(r"C:\ATMEL_PLS_Tools\ProChip\pldfit")
LIBRARY = WINCUPL / "Shared" / "Atmel.dl"
EXPECTED_PINS = {"a": 6, "b": 8, "y": 14}


def environment():
    env = os.environ.copy()
    directories = [
        WINCUPL / "Shared",
        WINCUPL / "WinCupl",
        FITTERS,
        WINCUPL / "WinCupl" / "Fitters",
    ]
    env["PATH"] = os.pathsep.join(map(str, directories)) + os.pathsep + env.get("PATH", "")
    env["FITTERDIR"] = str(FITTERS)
    env["LIBCUPL"] = str(WINCUPL / "Shared" / "cupl.dl")
    return env


def run(command, work, log_name, timeout=120):
    command = [str(argument) for argument in command]
    log = work / log_name
    with log.open("wb") as output:
        header = f"Command: {subprocess.list2cmdline(command)}\n"
        output.write(header.encode("utf-8"))
        output.flush()
        try:
            result = subprocess.run(
                command,
                cwd=work,
                env=environment(),
                stdin=subprocess.DEVNULL,
                stdout=output,
                stderr=subprocess.STDOUT,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired:
            output.write(b"\nTIMEOUT\n")
            raise
        output.write(f"\nExit code: {result.returncode}\n".encode("ascii"))
    if result.returncode != 0:
        raise RuntimeError(f"Tool failed; see {log}")
    return log


def require_file(path):
    if not path.is_file() or path.stat().st_size == 0:
        raise RuntimeError(f"Missing or empty output: {path}")
    return path


def build(source, directory):
    source = Path(source).resolve(strict=True)
    vectors = source.with_suffix(".si").resolve(strict=True)
    work = Path(directory).resolve()
    work.mkdir(parents=True, exist_ok=False)
    shutil.copy2(source, work / source.name)
    shutil.copy2(vectors, work / vectors.name)
    stem = work / source.stem
    compiler = WINCUPL / "Shared" / "cupl.exe"

    run([compiler, "-m1anlxs", "-u", LIBRARY, source.name],
        work, "simulation.log")
    require_file(stem.with_suffix(".so"))

    run([compiler, "-m1anlxj", "-u", LIBRARY, source.name],
        work, "compile.log")
    require_file(stem.with_suffix(".tt2"))

    # Remove any preliminary JED before the explicit fitter creates its output.
    jed = stem.with_suffix(".jed")
    jed.unlink(missing_ok=True)
    fit_log = run([
        FITTERS / "fit1504.exe",
        "-i", stem.with_suffix(".tt2").name,
        "-cupl", "-device", "TQFP100", "-tech", "ATF1504ASV",
        "-preassign", "keep",
        "-str", "JTAG=ON", "-str", "security=OFF",
    ], work, "fitter.log")
    require_file(jed)

    report = require_file(stem.with_suffix(".fit")).read_text(
        encoding="cp1252", errors="replace")
    expected = [
        "Device_name = TQFP100", "Tech_name = ATF1504ASV",
        "Preassignment = keep", "Security_mode = OFF", "JTAG = ON",
    ]
    expected += [f"{name} is placed at pin {pin}"
                 for name, pin in EXPECTED_PINS.items()]
    for setting in expected:
        if setting not in report:
            raise RuntimeError(f"FIT report missing: {setting}")
    if "Design fits successfully" not in fit_log.read_text(encoding="cp1252"):
        raise RuntimeError(f"Fitter success message missing; see {fit_log}")
    return jed


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python build.py source.pld new-output-directory")
    print(build(sys.argv[1], sys.argv[2]))
```

Run from PowerShell:

```powershell
python build.py src\design.pld build\run001
```

### Why the implementation is arranged this way

- **Argument lists:** each command argument is a separate Python list element. `subprocess` handles Windows quoting. Omit `shell=True` and do not insert quote characters around path arguments.
- **Working directory:** `cwd=work` makes the matching SI file and generated outputs easy for the legacy tools to locate. Use local, reasonably short ASCII paths. Some tools have their own path-length limitations.
- **Child environment:** PATH locates helper programs; `FITTERDIR` locates fitters; `LIBCUPL` supplies a library setting used by CUPL. The explicit `-u` selects `Atmel.dl`. These changes apply to child processes only.
- **Binary log files:** stdout and stderr go directly to disk. Read vendor text using `cp1252` where needed. This also avoids output-pipe problems with launcher programs that leave GUI children running.
- **Timeouts:** a hung command raises an exception and stops the build. A launcher may leave child processes behind; inspect and terminate only processes owned by that run before retrying.
- **Fresh directory:** `exist_ok=False` prevents an old JED or report from being mistaken for a new result. The preliminary JED removal is limited to the current build's same-stem output.
- **Result checks:** the script checks exit codes, artifacts, fitter settings, and pin placement. Review the SO report during bring-up. In testing, an intentionally wrong expected simulation output caused CUPL to return 1 and the build to stop.

The report checks use strings from fitter version 1918. Recheck these strings when changing tool versions. Extend the expected-pin list to cover all production constraints, and add timing acceptance checks appropriate to the design.

Handle help/version probes separately from build commands: the tested fitter help call returned 101 despite printing its help normally. For Precision bring-up, use the documented `-shell -file` invocation; a `-help` probe on this installation launched a GUI child and timed out.

## 4. Small bring-up design

Create `src\design.pld`:

```text
Name     design;
PartNo   ATF1504ASV;
Date     11/11/2026;
Revision 1;
Designer Example;
Company  Example;
Assembly None;
Location None;
Device   f1504isptqfp100;

Pin 6  = a;
Pin 8  = b;
Pin 14 = y;
y = a & b;

PROPERTY ATMEL {preassign = keep};
PROPERTY ATMEL {JTAG = ON};
```

Create `src\design.si` with the **same header through the Device statement**, followed by:

```text
ORDER: a, b, y;
VECTORS:
0 0 L
0 1 L
1 0 L
1 1 H
```

The four expected rows in `design.so` are `00L`, `01L`, `10L`, and `11H`. The example pins are for software bring-up. Replace them and `EXPECTED_PINS` with the PCB's assignments before preparing a hardware release.

## 5. VHDL/Verilog through Precision

Once the requested Precision license is available, the flow is:

```text
VHDL/Verilog → Precision → EDIF → FIT1504 → JED
```

The installed Precision guide uses `MGLS_LICENSE_FILE` for a license file or a vendor-specified server location. To set it for the current PowerShell session:

```powershell
$env:MGLS_LICENSE_FILE = 'C:\ATMEL_PLS_Tools\Licenses\license.dat'
```

First create a project in Precision selecting the target, package, sources, top level, actual pins, and timing requirements. Save the `.psp` and use **File → Export Settings Script** to capture the exact OEM settings and library names.

Precision's documented invocation is:

```text
C:\ATMEL_PLS_Tools\Precision\bin\precision.exe -shell -file C:\pldwork\build.tcl
```

A starting Tcl script for an already configured `design.psp` is:

```tcl
if {[catch {
    open_project design.psp
    compile
    synthesize
    report_timing
    save_project
} message]} {
    puts stderr "BUILD_FAILED: $message"
    exit -force
}
puts "BUILD_COMPLETED"
exit -force
```

Run it from the project directory using the Python `run` function above:

```python
project = Path(r"C:\pldwork\project").resolve()
log = run([
    r"C:\ATMEL_PLS_Tools\Precision\bin\precision.exe",
    "-shell", "-file", project / "build.tcl",
], project, "precision.log", timeout=600)
text = log.read_text(encoding="cp1252", errors="replace")
if "BUILD_FAILED:" in text or "BUILD_COMPLETED" not in text:
    raise RuntimeError("Precision script did not complete successfully")
```

Check that the expected EDIF was newly generated. The installed manual documents `exit -force`; the explicit markers allow Python to recognize a caught script failure even if the process returns zero.

The documented fitter command adapted to the target is:

```text
C:\ATMEL_PLS_Tools\ProChip\pldfit\fit1504.exe -i design.edf -ifmt EDIF -lib C:\ATMEL_PLS_Tools\ProChip\pldfit\aprim.lib -device TQFP100 -tech ATF1504ASV -preassign keep -str JTAG=ON -str security=OFF
```

Use the same Python runner and FIT/JED checks. Verify that the project's pin constraints reached the fitter; `KEEP` acts on the assignments supplied to it.

**Validation status:** the Precision shell invocation reached the license check on the VM. Synthesis and the resulting EDIF-to-fitter integration still require validation after licensing. The CUPL flow above was tested end to end.

## 6. HDL simulation with ModelSim

The installed ProChip documentation says ModelSim requires a separate Siemens license. Confirm its availability independently of the Precision license.

For a working directory containing HDL sources, a testbench, and `simulate.do`, use:

```text
C:\ATMEL_PLS_Tools\ModelSim\win32aoem\vsim.exe -c -do "do {C:/pldwork/sim/simulate.do}"
```

A basic DO script for Verilog is:

```tcl
onerror {quit -code 1 -force}
onbreak {quit -code 1 -force}
vlib work
vlog design.v design_tb.v
vsim work.design_tb
run 100 ns
quit -code 0 -force
```

Use `vcom` for VHDL and compile packages before their users. Set a simulation duration sufficient for the testbench. Have failing checks trigger an error or `$stop`, and require a distinctive completion marker such as `TEST_PASS` in the transcript after all checks pass. Arrange testbench termination so it does not end the simulator before this exit-code handling runs.

From Python, pass the DO expression as one argument:

```python
script = Path(r"C:\pldwork\sim\simulate.do").resolve()
run([
    r"C:\ATMEL_PLS_Tools\ModelSim\win32aoem\vsim.exe",
    "-c", "-do", f"do {{{script.as_posix()}}}",
], script.parent, "modelsim.log", timeout=600)
```

The `-do` expression is parsed by Tcl as well as by the Windows process launcher. Forward slashes and braces protect an ordinary script path containing spaces; avoid braces/newlines in the path itself.

The ModelSim console entrypoint was tested to its missing-license error on the VM. Licensed simulation remains to be validated.

## 7. ATMISP: SVF export and later programming

### Offline SVF export

ATMISP can generate an SVF file without a programmer:

1. Create a chain containing one **ATF1504ASV**.
2. Select **Program/Verify** and the fitted JED.
3. Check **Write SVF file** and enter an output filename.
4. Select the required SVF revision; the tested default was **Revision D**.
5. Set the TCK-period field; **1 µs** was used for the offline test.
6. Click Run and check the generated SVF and `jtag.log`.

For an initial implementation, this can be a supervised step after the Python build. The project also successfully automated it using Python `ctypes` and native Windows messages. The key control IDs in the tested ATMISP build were:

| Control | ID |
|---|---:|
| Run | 1007 |
| Device count | 1018 |
| SVF output filename | 1019 |
| Write SVF file checkbox | 1020 |
| SVF revision | 1022 |
| TCK period | 1023 |
| Device type in Device Property dialog | 1026 |
| Operation in Device Property dialog | 1027 |
| JED filename in Device Property dialog | 1028 |

A GUI automation implementation should select windows by the launched process ID, wait for each dialog, select the device/operation, enter the JED path, and confirm the chain count. Before pressing Run, verify the offline checkbox is checked and the output path is correct. Wait for a fresh, nonempty SVF and `JTAG instructions finished successfully` in `jtag.log`. Use bounded waits and close only the process launched by that run. Native-message implementations should use pointer-sized parameters, `SendMessageTimeoutW`, and `WM_GETTEXT` for other-process edit controls. These IDs need rechecking after a tool upgrade.

The saved CHN did not retain the SVF-output checkbox or filename in the observed version. Establish those settings for every export. GUI automation requires an interactive Windows session and compatible process elevation levels.

### Executing a saved chain with a programmer

Create and review the chain in the GUI, then execute it using an **absolute path**:

```text
C:\ATMISP7\ATMISP.exe C:\pldwork\release\target.chn -1
```

`-1` is digit one and executes the operations saved in the chain. Python can use:

```python
chain = Path(r"C:\pldwork\release\target.chn").resolve(strict=True)
run([r"C:\ATMISP7\ATMISP.exe", chain, "-1"],
    chain.parent, "atmisp-console.log", timeout=300)
```

Use absolute JED references inside the chain too. Archive ATMISP's own `jtag.log` after each run; stdout may contain little information. A relative chain argument returned zero without useful execution evidence in testing. An absolute chain request reached a blocking hardware/settings dialog on the no-programmer VM, so include timeout handling even with `-1`.

ATMISP 7 supports the **ATDH1150USB** cable. A VM will need USB-device passthrough and the appropriate FTDI driver. Physical programming remains untested in this investigation. Start with a supervised hardware run, preserve JTAG access, and keep security disabled during development.

## 8. Optional input: an existing POF

If a project supplies a compatible MAX-series POF, the installed converter is `C:\POF2JED\bin\POF2JED.exe`. Its invocation for this target family is:

```text
C:\POF2JED\bin\POF2JED.exe -i design.pof -o design.jed -device 1504ASV -JTAG ON
```

Stage the POF in a fresh directory and call it through the same Python runner. Review the generated TXT report. The source POF determines the package and pin mapping; confirm it matches the 100-pin TQFP design. The converter accepted an incompatible target override during testing and still returned zero, so check density, package, voltage variant, and warnings explicitly. Preserve the default race coverage unless the design review calls for a change, and review security settings inherited from the source.

## 9. Acceptance and troubleshooting checklist

For each release, retain the source revision, exact target, tool versions, command logs, simulation reports, pin/timing reports, JED, and any SVF.

Before accepting a build:

- The output directory was new and all required inputs were staged.
- Simulation completed and its expected checks passed.
- The FIT report identifies **ATF1504ASV / TQFP100**, fixed PCB pins, JTAG ON, and intended security settings.
- Timing was checked against the actual part and design requirements.
- Any programming or SVF-export result has its own log and explicit success evidence.

When a step fails, first check its log, working directory, input/output filenames, and library paths. For Precision/ModelSim, resolve license errors before changing scripts. For ATMISP timeouts, inspect modal dialogs and hardware settings. Run one build/export per worker initially; separate directories do not isolate shared GUI configuration or license seats.

Useful installed references: ProChip `help\fitter15xx.pdf`; Precision `shared\pdfdocs\precisionsyn_ref.pdf`; ModelSim `docs\pdfdocs\modelsim_oem_ref.pdf`; ATMISP `Help\ATMISP.chm`, especially Getting Started → Launching ATMISP Using DOS Command.
