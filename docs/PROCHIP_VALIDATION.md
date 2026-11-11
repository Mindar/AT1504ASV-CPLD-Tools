# ProChip Designer: licensed target validation

The licensed toolchain was tested from **`G:\Standardprojekt`** for **ATF1504ASV-15AU100**, using small VHDL and Verilog AND-gate designs. **Both languages passed synthesis and fixed-pin fitting; the Verilog run also passed offline SVF export.** The example pins are inputs 6/8 and output 14; adapt them to the actual PCB before programming.

| Check | Result / evidence |
|---|---|
| ProChip IDE startup | Correct image/directory verified; `research\prochip_ide_check\windows.json` |
| Licensed VHDL synthesis and fitting | Passed; `research\prochip_validation\vhdl_full\validation.json` |
| Saved Precision project reopening | Passed; `vhdl_full\reopen_check\precision-console.log` |
| Explicit `tPD=15` fitter strategy | Passed with correct pins; `vhdl_full\fit_speed15\` |
| Licensed Verilog synthesis, fitting, and offline SVF | Passed; `research\prochip_validation\verilog_retry\validation.json` |
| Final serial rebuild using startup recovery | VHDL and Verilog passed; `research\prochip_validation\final-20261111-223151\results.json`; Verilog also exported SVF |
| Unit tests | 16 tests passed, including startup gating, retry scope, process-tree cleanup, pin checks, and IDE image arguments |
| ModelSim simulation | Not required for the requested synthesis workflow |
| Hardware programming | No programmer attached; untested |

## Reproduce the build

Use new output directories:

```powershell
Set-Location G:\Standardprojekt
python examples\build_prochip_1504.py build\prochip-vhdl --language vhdl
python examples\build_prochip_1504.py build\prochip-verilog --svf
```

The second command exports SVF using the interactive ATMISP desktop. It does not contact a programmer.

The script:

1. Creates an isolated build directory and copies the selected HDL fixture.
2. Creates a Precision project and implementation.
3. Selects manufacturer `Atmel`, family `ATF15xxASV`, part `ATF1504ASV-15AU100`, and speed `-15`.
4. Compiles and synthesizes the top-level `prochip1504` to EDIF.
5. Saves the project and synthesis reports.
6. Creates the PIN sidecar required by the fitter.
7. Runs ProChip FIT1504 with ASV/TQFP100, KEEP, JTAG ON, security OFF, and `tPD=15`.
8. Checks the final signal/JTAG pin placement, successful-fit marker, and output files.
9. Optionally exports offline SVF and checks ATMISP's own generation log.
10. Writes a `validation.json` containing outcomes and artifact hashes.

The generated Precision project is `<build-directory>\prochip1504.psp`. Use Precision's **Open Project** command to reopen it. Its project files must remain with the implementation directory and staged source.

The VHDL project was reopened successfully through `open_project`, and an additional fit confirmed acceptance of the explicit `tPD=15` strategy while preserving the requested pins.

The validated Verilog run produced an 11,871-byte JED and a 97,831-byte Rev. D SVF. Its JSON report records their SHA-256 hashes and the output FIT/EDIF artifacts.

## Important integration fix: PIN sidecar

Precision writes `pin_number` properties into the EDIF. The ProChip fitter tested here does not apply these properties on its own. Without a PIN sidecar it logged `Can not open ... .pin file`, continued, returned zero, and moved the pins.

For an EDIF named `prochip1504.edf`, place `prochip1504.pin` in the same fitter working directory:

```text
CHIP "prochip1504" ASSIGNED TO AN TQFP100
a : 6
b : 8
y : 14
```

The corrected fit preserves a=6, b=8, y=14, TDI=4, TMS=15, TCK=62, and TDO=73. The EDIF fitter may capitalize input names in its reports; the script compares names case-insensitively. It also keeps `requested-pins.txt`, since the fitter can rewrite its PIN output.

Two regression tests check the sidecar and ensure that a moved pin is rejected even when a simulated fitter returns zero.

## Starting the ProChip IDE

The installed shortcut uses:

```text
Executable: C:\ATMEL_PLS_Tools\ProChip\bin\visual.exe
Arguments:  ProChipDesPrd.im
Start in:   C:\ATMEL_PLS_Tools\ProChip\bin
```

Starting `visual.exe` alone produced `Can't open visual.IM`. Using the shortcut's image and directory successfully opened **Atmel ProChip Designer (no project)**. The following helper reproduces that launch and supplies the licensed environment:

```powershell
python examples\launch_prochip.py
```

Keep your project sources and results under `G:\Standardprojekt`; the IDE's startup directory follows its installed shortcut. The IDE's synthesis and simulation configuration already points to the installed Precision and ModelSim executables.

The GUI startup check is separate from the automated Precision/fitter tests. The automated builds invoke the suite's synthesis/fitting tools directly; an IDE-driven `.apj` compilation has not been claimed as tested.

## Shared-folder handling

Use the mapped `G:` drive for vendor paths. Python's `Path.resolve()` can expand it to `\\VBoxSvr\shared_dir`, which this Precision version mishandled when opening its transcript. The shared runner now preserves mapped paths and captures stdout in `precision-console.log`, leaving Precision's own `precision.log` available.

All new validation scripts, sources, and results are in the shared workspace. Installed applications and the local license remain in their installation directories.

## Precision startup recovery

Intermittent stalls occurred before Precision's startup banner, including during a later license/discovery check. Windows 7 compatibility mode and single-CPU affinity trials did not eliminate the problem, so neither setting is applied to the normal workflow. The underlying cause remains unresolved.

`run_precision()` now uses a two-stage startup handshake:

1. A generated bootstrap Tcl script prints `PRECISION_STARTUP_READY` and flushes stdout.
2. The bootstrap waits for a unique acknowledgement file from Python.
3. Python waits up to 15 seconds for the emitted readiness message, then creates the acknowledgement file.
4. Only then does Tcl source the requested synthesis script.
5. If readiness times out, Python terminates the owned process tree and retries, up to three startup attempts.

This acknowledgement prevents the synthesis script from starting during a startup timeout/retry race. Actual script errors and timeouts after the handshake are not retried. The example build has a 120-second overall timeout per attempt; the generic helper accepts a longer timeout for larger designs.

**Repeated check:** 12 of 12 serial startup/script checks passed with this recovery mechanism. Eleven passed on the first attempt; one encountered the startup stall and completed on its second attempt. Evidence: `research\precision_recovery\20261111-223037\results.json`.

The original long-timeout failure is retained under `research\prochip_validation\verilog_full`, and an earlier successful complete retry under `verilog_retry`. Additional compatibility/affinity experiments are under `research\precision_startup`. Keep synthesis runs serialized initially.

## Remaining limits

- ModelSim is outside the requested workflow. These checks exercise synthesis, fitting, and optional offline SVF export.
- The small fixture checks tool integration and physical pin preservation. It does not establish timing closure or correct PCB behavior for a production design.
- No programmer or target is attached, so physical programming/readback remains untested.

See `research\prochip_validation` for detailed runs and `research\prochip_ide_check\windows.json` for the IDE startup record.
