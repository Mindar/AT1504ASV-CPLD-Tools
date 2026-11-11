# Detailed Python automation guide

## 1. Scope and recommended architecture

Your intended device is in the **ATF1504 series**, specifically the **3.3 V ATF1504ASV, 100-pin TQFP**. `ATF1504ASV-15AU100` is a real ordering code matching the description. `15` is the speed grade; `A` denotes TQFP, `U` the industrial temperature range, and `100` the lead count. Do not use the AS (5 V) technology or a 44-pin/PQFP package by accident.

The practical automation architecture is:

```text
Python                         vendor tools                    artifacts
------                         ------------                    ---------
copy sources → run commands → CUPL compiler                  → TT2/PLA
                         └→ CUPL functional simulator       → SO
                             ProChip FIT1504                → JED + FIT
                             ATMISP offline GUI             → SVF + jtag.log
                             ATMISP chain execution         → hardware + log

after Precision licensing:
VHDL/Verilog → Precision Tcl → EDIF → FIT1504 → JED → ATMISP

optional alternative input:
compatible MAX-series POF → POF2JED → JED → ATMISP
```

Python is the **orchestrator**, not a replacement synthesis engine, fitter, or JTAG implementation. Use `subprocess` for command-line tools and Tcl/DO files for their embedded scripting languages. Native GUI automation is needed only where a supported CLI does not expose the required feature—for example, ATMISP's offline output checkbox.

**Recommended now:** CUPL + the explicit ProChip fitter. It already works without Precision/ModelSim licenses. **Recommended later for VHDL/Verilog:** Precision's documented shell/Tcl interface, followed by that same fitter. There is no reason to automate the entire ProChip desktop IDE with mouse coordinates.

## 2. What was downloaded and what is installed

The inventory used Downloads, actual installation files, Windows uninstall records, executable version information, vendor release notes, and CLI banners. A downloaded installer alone was not treated as proof of installation.

Downloads are under `C:\Users\admin\Downloads`:

| Download | Installed component/evidence |
|---|---|
| `awincupl.exe.zip` and extracted `awincupl.exe\awincupl.exe` | WinCUPL under `C:\Wincupl`; uninstall registration says 5.30.4 |
| `ProChip_v5_0_2.zip` and `ProChip5_setup.exe` | Suite at `C:\ATMEL_PLS_Tools`; release notes identify 5.0.2, while registration/IDE use 5.0 |
| `ATMISP_v7_3_1.zip` and `ATMISP7_setup.exe` | Standalone programmer at `C:\ATMISP7`; release notes identify 7.3.1 |
| `pof2jed.zip` and `POF2JED_Setup.exe` | Converter at `C:\POF2JED`, CLI 4.45.1 |
| Three `CDM-v2.12.36.20-WHQL-Certified` ZIP copies | FTDI driver distribution; also bundled with ATMISP |
| `python-3.15.2-amd64.exe` | `C:\Program Files\Python315\python.exe`, Python 3.15.2 x64 |

The FTDI files on disk do **not** prove a usable passed-through USB programmer exists. This VM has no programmer. The query for installed FTDI signed-device driver entries returned none at inspection time; a staged driver can still exist without a connected device.

### Executables worth using

| Component | Path | Purpose |
|---|---|---|
| CUPL | `C:\Wincupl\Shared\cupl.exe` | Compile CUPL source; launch simulation with options |
| CSIM | `C:\Wincupl\Shared\csim.exe` | CUPL simulator; using it via `cupl.exe -s` avoids guessing its standalone syntax |
| WinCUPL GUI | `C:\Wincupl\WinCupl\Wincupl.exe` | Interactive editor/configuration |
| WinSim GUI | `C:\Wincupl\WinSim\winsim.exe` | Interactive CUPL vector editing/simulation |
| Newer fitters | `C:\ATMEL_PLS_Tools\ProChip\pldfit\fit1502.exe`, `fit1504.exe`, `fit1508.exe` | Prefer explicit invocation of these |
| Older fitters/wrappers | `C:\Wincupl\WinCupl\Fitters\fit1504.exe`, `find1504.exe` | CUPL's automatic flow can invoke these |
| ProChip IDE | `C:\ATMEL_PLS_Tools\ProChip\bin\visual.exe` | Project creation and constraint configuration |
| Precision | `C:\ATMEL_PLS_Tools\Precision\bin\precision.exe` | Licensed VHDL/Verilog synthesis, Tcl shell |
| ModelSim | `C:\ATMEL_PLS_Tools\ModelSim\win32aoem\vsim.exe` | Licensed HDL simulation, console/DO scripting |
| HDL compilers/libraries | Same ModelSim directory: `vlog.exe`, `vcom.exe`, `vlib.exe`, `vmap.exe` | Verilog/VHDL compilation and simulation libraries |
| ATMISP | `C:\ATMISP7\ATMISP.exe` | Prefer this standalone installation |
| Bundled ATMISP | `C:\ATMEL_PLS_Tools\ATMISP\ATMISP.exe` | Duplicate suite copy; do not mix configuration unknowingly |
| POF2JED CLI | `C:\POF2JED\bin\POF2JED.exe` | Automatable conversion |
| POF2JED GUI | `C:\POF2JED\bin\WinPOF2JED.exe` | Unnecessary for automated conversion |

The newer ProChip fitter banner is **1918 (3-21-07)**. The WinCUPL fitter banner is **1.8.7.8 (02-05-03)**. The CLI schemas differ: newer fitters separate `-device TQFP100` from `-tech ATF1504ASV`; older tools use device tokens such as `P1504T100`. Do not mix their arguments.

Precision's executable reports **2013a.10OEM_Atmelcpld**. ModelSim's `-version` reports **ModelSim ATMEL 6.2c, 2006.08**. The suite's 2025 packaging does not make those engines modern versions.

The ATMISP executable resource reports 7.3.0.0 and its SVF banner says 7.3, even though the distribution's release notes say **7.3.1**. Those are different version-information layers, not evidence that the release notes were ignored.

### Repeat the inventory

```powershell
python examples\inventory.py
python --version
```

No scanning of personal documents is required. Relevant installation roots and Downloads were enough. No Libero/FlashPro or Quartus installation was found in the examined installation roots/registration; do not assume those products are installed merely because the vendor sells them.

## 3. Target settings: keep these distinctions explicit

| Layer | Setting for your device |
|---|---|
| Physical ordering code | Likely `ATF1504ASV-15AU100`; confirm against the part |
| CUPL device token | `f1504isptqfp100` |
| Fitter executable | ProChip `fit1504.exe` |
| Fitter technology | `-tech ATF1504ASV` |
| Fitter package | `-device TQFP100` |
| Pin assignment policy | `-preassign keep` |
| JTAG strategy | `-str JTAG=ON` |
| Development security strategy | `-str security=OFF` |
| ATMISP device name | `ATF1504ASV` |
| POF2JED target, if applicable | `-device 1504ASV`; package comes from the POF |

The generic CUPL token does not itself guarantee the final **ASV** technology. Check the explicit fitter options and FIT report. Also, a JEDEC file fitting successfully does not prove a timing requirement for a `-15` device is satisfied.

### Demonstration pins and JTAG

The included `and1504.pld` uses `a=6`, `b=8`, `y=14`. These are legal signal pins in the datasheet's **100-lead TQFP** column. They are not a proposed board pinout.

For this package, reserve JTAG pins **TDI=4, TMS=15, TCK=62, TDO=73**. Do not copy the 44-pin package's numbers or the old 100-pin PQFP column. The target-specific fitter report confirms all four JTAG reservations.

For real hardware, verify the full power-pin split, voltage limits, grounding, unused pins, clock inputs, and PCB connectivity from the datasheet and schematic. Do not use a programming-file example as an electrical design specification.

## 4. Run legacy programs safely and reproducibly from Python

The shared implementation is [`examples/toolchain.py`](../examples/toolchain.py). It deliberately uses only Python's standard library.

### Minimal subprocess pattern

```python
import subprocess
from pathlib import Path

work = Path(r"C:\pldwork\run001")  # Example path; create a new local directory.
command = [
    r"C:\ATMEL_PLS_Tools\ProChip\pldfit\fit1504.exe",
    "-i", "design.tt2",
    "-cupl",
    "-device", "TQFP100",
    "-tech", "ATF1504ASV",
    "-preassign", "keep",
    "-str", "JTAG=ON",
    "-str", "security=OFF",
]

with (work / "fitter.log").open("wb") as log:
    result = subprocess.run(
        command, cwd=work, stdout=log, stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL, timeout=120, check=False,
    )
if result.returncode != 0:
    raise RuntimeError("Fitter failed; inspect fitter.log")
```

Pass an **argument list**, without adding manual quote characters. Leave `shell=False` (the default). Python handles Windows argument quoting. This avoids shell injection and most quoting mistakes, though it cannot repair a vendor program's own broken path parser.

Use a dedicated `cwd`: many tools locate inputs, includes, libraries, and outputs relative to it. Prefer local, short ASCII paths without spaces. Some long paths worked in these tests, but ATMISP explicitly documents problems with very long names. Python's support for Unicode/long paths does not modernize a 32-bit vendor executable.

### Environment settings

The VM already had:

```text
FITTERDIR=C:\ATMEL_PLS_Tools\ProChip\pldfit
```

For child CUPL processes, the examples add relevant WinCUPL/fitter directories to PATH and set `LIBCUPL`, while also passing the device library explicitly with `-u C:\Wincupl\Shared\Atmel.dl`. Explicit `-u` avoids depending on an unspecified global environment. A naked CUPL help probe failed with “Unable to read environment variable: LIBCUPL”.

Modify `os.environ.copy()` and pass it via `env=`. Do not modify machine-wide PATH, registry settings, or installed fitters just to run a build. In particular, do not replace the WinCUPL installation's older fitters as a first step: call the newer fitter by absolute path instead.

### Logs, timeouts, and return codes

- File-based stdout/stderr logging avoids holding large reports in RAM and avoids pipe-closure hangs when a launcher leaves a GUI child running.
- Old tools commonly emit a Windows legacy code page; read their text with `encoding="cp1252", errors="replace"`. Generated Python metadata can be UTF-8.
- `subprocess.run(timeout=...)` terminates the directly launched process on timeout, **not necessarily every descendant**. The current shared runner uses `Popen.wait()` and, on Windows, attempts `taskkill /PID <owned-launcher> /T /F` before killing the parent. This addresses the Precision child left by a timed-out validation. Inspect the cleanup log if it fails; a Windows Job Object is a stronger option for a dedicated CI worker.
- Never kill every process named `precision.exe` or `ATMISP.exe`: that could terminate another project. Track the process you own.
- A help command can exit nonzero without a malfunction: the fitter returned **101** for `-help`; POF2JED's device-help mode returned **1**.
- A zero exit is not a success certificate. Check a **fresh output**, the tool's report, the intended target/package, pin assignments, and relevant success/failure markers.
- A GUI can block on a modal dialog even in a nominal batch mode. Standard output may be empty. Include a bounded timeout and preserve diagnostic information.

### Fresh directories rather than stale outputs

The examples reject an existing build directory. This protects against accepting yesterday's `.jed` after today's failed build. The explicit fitter removes only the same-stem preliminary `.jed` it is about to replace, inside that isolated build area. Do not point the helper at unrelated user output.

Copy the full source/include tree for larger projects; the small helper copies only one `.pld` and its matching `.si`. Relative include files, macro files, memory initializers, and constraint files must also be staged when your project uses them.

## 5. Tested CUPL → simulation → FIT1504 workflow

```powershell
python examples\build_1504.py build\target001
```

Files are [`and1504.pld`](../examples/and1504.pld), [`and1504.si`](../examples/and1504.si), and [`build_1504.py`](../examples/build_1504.py).

### Stage A: functional simulation without JEDEC-vector output

```text
C:\Wincupl\Shared\cupl.exe -m1anlxs -u C:\Wincupl\Shared\Atmel.dl and1504.pld
```

Relevant options:

| Option | Use here |
|---|---|
| `-m1` | Quick minimization |
| `-a` | Absolute output for simulation |
| `-n` | Use source basename for outputs |
| `-l` | Listing |
| `-x` | Expanded product-term documentation |
| `-s` | Run functional simulation using matching SI file |
| `-u` | Explicit device-library path |
| `-j` | Request JEDEC-related output; deliberately absent in this stage |

The four vectors are:

```text
ORDER: a, b, y;
VECTORS:
0 0 L
0 1 L
1 0 L
1 1 H
```

`0`/`1` drive input values; `L`/`H` specify expected output values. Read `.so`, not just a generic “Normal exit” line. This target example produced `00L`, `01L`, `10L`, `11H` with exit zero.

**Discovered trap:** combining `-j` and `-s` directly on this CPLD example failed with undefined-pin JEDEC-vector messages and “could not open and1504.jed”. Separating functional simulation from device-file generation fixed it. This is a functional truth-table test, **not post-fit timing simulation**.

### Stage B: generate the device netlist

```text
C:\Wincupl\Shared\cupl.exe -m1anlxj -u C:\Wincupl\Shared\Atmel.dl and1504.pld
```

This emits the `.tt2` that the fitter needs. The functional-simulation-only invocation did not emit that file on this installation. The compiler may attempt an automatic `find1504` step; the Python flow does not rely on its final file being correct. Stage C explicitly invokes the intended fitter.

The TT2 contains logic and metadata, including assigned pins and `PROPERTY ATMEL` statements. The example includes:

```text
Device f1504isptqfp100;
PROPERTY ATMEL {preassign = keep};
PROPERTY ATMEL {JTAG = ON};
```

### Stage C: fit the actual ASV / TQFP100 device

```text
C:\ATMEL_PLS_Tools\ProChip\pldfit\fit1504.exe -i and1504.tt2 -cupl -device TQFP100 -tech ATF1504ASV -preassign keep -str JTAG=ON -str security=OFF
```

Expected evidence in `.fit`:

```text
Device_name = TQFP100
Tech_name = ATF1504ASV
Preassignment = keep
Security_mode = OFF
JTAG = ON
y is placed at pin 14
b is placed at pin 8
a is placed at pin 6
TDI is placed at pin 4
TMS is placed at pin 15
TCK is placed at pin 62
TDO is placed at pin 73
```

`KEEP` is important for an existing PCB. The default `TRY` strategy may retry fitting while relaxing assignments. A design fitting after pins were moved is not a usable design for your board.

The result is `.jed`, the programming data. Preserve `.fit`, `.tt2`, `.so`, and the command logs with it. No device was programmed by the build script.

**Another legacy labeling trap:** the successfully fitted ASV file's first line says `JEDEC file for: ATF1504AS`, despite the FIT report explicitly recording `Tech_name = ATF1504ASV`. Do not infer the exact voltage variant from that generic JEDEC header alone. Keep the explicit target command, FIT report, package/pin evidence, and selected ATMISP device together.

### Additional smoke test for the installed tools

```powershell
python examples\build_adder.py build\adder001 --simulate
```

This copies the installed `ADDER.PLD` and `ADDER.SI` and exercises an SPLD flow. It is a software sanity test, **not an ATF1504 design**. The separate exploratory `TIM_CNT` test targets an ATF1508 and likewise is not your production device.

## 6. POF2JED: useful alternative input, not a compiler

POF2JED converts supported MAX7000/7000E/7000A/7000AE/3000A POF files to equivalent ATF15xx programming data. It does not synthesize VHDL/Verilog, accept arbitrary FPGA bitstreams, or change your PCB's pinout.

Documented command structure:

```text
POF2JED [-i] input.pof [-o output.jed] [options]
```

For your device family:

```powershell
python examples\convert_pof.py C:\path\compatible.pof build\converted001 --device 1504ASV
```

Equivalent command:

```text
C:\POF2JED\bin\POF2JED.exe -i compatible.pof -o compatible.jed -device 1504ASV -JTAG ON
```

The wrapper deliberately does not set `-secure` or disable race coverage. Review the source design's security settings too: not passing `-secure` is not proof that all input settings are safe. Read the generated TXT report.

### Critical limitations demonstrated locally

The installed `myand2.pof` identifies as `EPM7064LC84-7`. Its matching smoke-test target is `1504AS` / PLCC84. Conversion worked, but that sample is **not** a TQFP100 design for your board.

A deliberate early test with `-device 1502AS` also returned zero and generated a JEDEC file while printing the impossible pairing `1502asPLCC84`. Therefore:

1. Check compatible **density** before calling the converter.
2. Check the **package** encoded by the source POF.
3. Explicitly select the **voltage family**.
4. Check the source pin map and all conversion warnings.
5. Verify JTAG is on in the report.
6. Do not treat an output file or “Conversion is completed” as proof of electrical or target compatibility.

There is no documented package-remapping switch here. To obtain your 100-pin TQFP pinout, build an appropriate source POF, or use your CUPL/Precision → FIT1504 flow instead. Quartus would be an additional installation and is not required for the working native flow.

## 7. Precision and ModelSim automation after licensing

**Current update:** licensed VHDL and Verilog synthesis and explicit EDIF fitting have passed, followed by successful offline SVF export for Verilog. Use `examples/build_prochip_1504.py`; the earlier preparation notes below remain useful background. A required `.pin` sidecar is described below. See [ProChip validation](PROCHIP_VALIDATION.md) for evidence and limits.

Precision is now licensed and its synthesis flow is validated. ModelSim remains blocked by a missing simulator license. The [license checklist](LICENSES.md) retains the original diagnostic results and setup instructions.

### Precision: Python → shell → Tcl → EDIF

The installed 2013a manual explicitly documents:

```text
precision.exe -shell -file build.tcl
```

Use [`run_hdl.py`](../examples/run_hdl.py):

```powershell
python examples\run_hdl.py precision examples\precision_discover.tcl C:\path\isolated-project
```

The discovery script executes `setup_design -list_technology`. Do not guess internal technology, package, or speed-grade tokens from modern Precision documentation. The OEM edition's technology names must come from this installed version or a project it exports.

Recommended initial setup once licensed:

1. Create one project in ProChip/Precision for ATF1504ASV / 100-pin TQFP.
2. Add synthesizable Verilog/VHDL, top module/entity, pin constraints, and clocks.
3. Select the actual speed grade/conditions where supported.
4. Save the project and export the script/settings. This captures exact OEM tokens and library paths.
5. Run the saved project headlessly from Python; inspect EDIF and reports.
6. Fit that EDIF explicitly with ProChip FIT1504.

The installed reference documents `new_project`, `open_project`, `add_input_file`, `setup_design`, `compile`, `synthesize`, `report_timing`, and `save_project`. [`precision_build.tcl`](../examples/precision_build.tcl) demonstrates opening a configured `.psp`, compiling, and synthesizing. It is a **template**, not a licensed end-to-end test result.

The template uses `catch` and prints `BUILD_FAILED`/`BUILD_COMPLETED`. The Python wrapper rejects `BUILD_FAILED:` even after a zero exit. This version documents `exit [-force]`, not a portable numeric `exit 1` interface. Consequently also check completion, reports, and expected **fresh EDIF**, not just the process exit code. Extend the wrapper for your exact output path and failure conventions after licensing.

### EDIF → FIT1504

The installed fitter guide gives an EDIF example using `-ifmt EDIF` and `-lib aprim.lib`. Adapted for your device:

```text
fit1504.exe -i design.edf -ifmt EDIF -lib C:\ATMEL_PLS_Tools\ProChip\pldfit\aprim.lib -device TQFP100 -tech ATF1504ASV -preassign keep -str JTAG=ON -str security=OFF
```

Use the full executable path as elsewhere. This command has now been validated on Precision-produced EDIF for the target. **Supply a same-basename `.pin` sidecar before invoking it.** The tested fitter ignored the EDIF's `pin_number` properties on their own and completed with moved pins. `-preassign keep` only preserves the assignments actually supplied to the fitter.

For the three-signal example, the sidecar is:

```text
CHIP "design" ASSIGNED TO AN TQFP100
a : 6
b : 8
y : 14
```

Use the actual EDIF basename and PCB assignments. The new build script retains the requested sidecar contents and checks the final FIT mapping case-insensitively, since the EDIF fitter can capitalize signal names.

A Python invocation uses `run_tool([...], work, "edif-fit.log")`, followed by checks of the expected JED/FIT and pin mapping. The installed `edf2pla.exe` is an internal conversion utility; the fitter's documented EDIF input is preferable to inventing an extra conversion pipeline.

### ModelSim: Python → console → DO/Tcl

Documented pattern:

```text
vsim.exe -c -do "do {C:/path/simulate.do}"
```

[`simulate.do`](../examples/simulate.do) uses `vlib`, `vlog`, `vsim`, `run`, and `quit`. Its tiny HDL source/testbench are included. Copy all three files into an isolated simulation directory before running:

```powershell
python examples\run_hdl.py modelsim C:\path\sim\simulate.do C:\path\sim
```

For VHDL, use `vcom` in source dependency order. For post-fit timing simulation, use the fitter's exported simulation netlist and SDF plus appropriate Atmel libraries; the included AND-gate example is RTL simulation only.

The DO file uses `onerror`/`onbreak` to exit nonzero on command errors and `$stop`. It runs a bounded 100 ns instead of hanging on an endless clock. The supplied Verilog testbench prints `TEST_PASS` after its four checks. For production, also require that marker in the transcript—simulating without command errors does not prove your testbench reached its assertions.

A testbench that merely prints “FAIL” or ends normally can still leave ModelSim with exit zero. Make assertion failures stop/raise an error and propagate that to `quit -code 1`.

Both Python string quoting and Tcl quoting apply to `-do`. The helper uses forward slashes and braces for the script filename and rejects braces/newlines in that filename. Source only trusted Tcl/DO scripts: they can run external commands.

## 8. Project hygiene, automation, and VM operation

### Suggested project structure

```text
project/
  src/                 CUPL, VHDL, Verilog, include files
  constraints/         PCB pin assignments and timing requirements
  scripts/             Python and vendor Tcl/DO
  toolchain.json       exact selected paths/target/version, if desired
  build/run-001/       isolated logs, TT2/EDIF, FIT, SO, JED, SVF
```

Archive source revision, part, package, options, tool banners/hashes, simulation results, final pin report, and programming-file SHA-256 together. Example hashing:

```python
import hashlib
from pathlib import Path

jed = Path("build/run-001/design.jed")
digest = hashlib.sha256(jed.read_bytes()).hexdigest()
print(jed.name, digest)
```

Do not compare JEDEC hashes as the sole proof of logical determinism: headers/timestamps may change. If you later normalize artifacts, retain the original vendor output too.

### Serial versus parallel runs

Serialize this legacy suite initially. Separate build directories isolate many files, but tools may still share configuration, temporary names, registry settings, or license seats. ATMISP GUI automation particularly should run one instance per desktop/worker. Add a lock if a scheduler can launch overlapping jobs.

### Task Scheduler / CI

CLI builds can generally run without an interactive editor. Verify license visibility under the scheduler's service account. ATMISP's GUI-based SVF export needs an **interactive logged-on Windows desktop**, matching elevation/integrity level, and functioning window-message automation. Do not expect it to work unchanged as a Windows service in Session 0.

For a VM with real hardware later, pass through the **USB device**, not just a virtual serial port. ATMISP 7 uses the ATDH1150USB cable's FTDI interface; arbitrary FTDI boards and arbitrary COM ports are not drop-in equivalents. USB passthrough, driver installation, and device recognition are separate tests from this software-only work.

64-bit Python can launch 32-bit executables without a matching Python bitness. It cannot load a 32-bit vendor DLL directly into its own process with `ctypes`. Do not try to automate programming by loading the bundled 32-bit `ftd2xx.dll` into Python 3.15 x64; that would also leave the programming algorithm unimplemented.

### Useful troubleshooting order

1. Verify executable and library paths with `inventory.py`.
2. Verify a fresh output directory and the intended `cwd`.
3. Read the first real error in the log, not just the last generic failure.
4. Confirm the compiler produced the input file for the next stage.
5. Check fitter version/schema and ASV/TQFP100 target.
6. For CSIM errors, separate `-s` functional simulation from `-j` output as demonstrated.
7. For Precision/ModelSim, resolve licensing before changing valid script syntax.
8. For an ATMISP timeout, inspect modal dialogs and its own `jtag.log`.
9. For hardware later, check USB passthrough, device chain/order, correct device type, power, and JTAG enablement.

The [evidence page](EVIDENCE.md) distinguishes tested behavior from manual-backed preparation.
