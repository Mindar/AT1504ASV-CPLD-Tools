# Quickstart: automate your ATF1504ASV workflow with Python

## The short version

Your target is the **ATF1504ASV, 100-pin TQFP**, likely ordering code **ATF1504ASV-15AU100**. Confirm the full marking before using real hardware.

Python does not implement the synthesis or programming algorithm. It **runs the installed tools, checks their results, and organizes the output**.

For this VM, the useful flow is:

```text
Design source + testbench + PCB pin assignments
                    │
         Python runs compilation/simulation
                    │
         Python runs the ATF1504 fitter
                    │
             JEDEC programming file
                    │
       Python drives ATMISP in offline mode
                    │
              SVF programming file
```

This entire software-only flow works using **CUPL**. The installed Precision license also enables the validated **VHDL/Verilog → EDIF → fitter** flow; the same ATMISP export stage applies.

## 1. What matters for your particular part

| Setting | Use |
|---|---|
| Device technology | `ATF1504ASV` — the 3.3 V variant, not `ATF1504AS` |
| Package | `TQFP100`, not TQFP44 or 100-pin PQFP |
| CUPL device token | `f1504isptqfp100` |
| Fitter | `C:\ATMEL_PLS_Tools\ProChip\pldfit\fit1504.exe` |
| Pin assignment policy | `-preassign keep` |
| JTAG | `-str JTAG=ON` |
| Development security | `-str security=OFF` |

**Keep the actual PCB pin assignments fixed.** A successful fit is useless if the fitter moved your signals to different pins. Reserve JTAG pins **4, 15, 62, and 73** for this package.

The demonstration uses inputs **6 and 8** and output **14**. Those are legal package pins, **not your board's pinout**. Do not program that example onto an arbitrary PCB.

Also, “fits successfully” does not establish timing closure for the `-15` speed grade.

## 2. Try the working example now

Open PowerShell in this folder:

```powershell
python examples\inventory.py
python examples\build_1504.py build\first1504
python examples\atmisp_svf.py build\first1504\and1504.jed build\firstsvf
```

**Use new directory names on subsequent runs.** The scripts intentionally refuse to reuse an existing output directory.

No Python packages, Precision license, or programmer are needed for these commands. The ATMISP export needs an **interactive Windows desktop** because it automates the GUI.

### What those commands do

1. **Inventory:** confirm the installed executables exist.
2. **Build:** simulate an AND gate's four input combinations, compile its device netlist, then fit explicitly for **ATF1504ASV / TQFP100**.
3. **Check:** reject failed commands, missing outputs, incorrect simulation results, and unexpected target/pin settings.
4. **Export:** launch ATMISP, create a single-device chain, explicitly select **Write SVF file**, and generate the SVF without hardware.

The important outputs are:

| File | Meaning |
|---|---|
| `and1504.so` | Functional simulation results |
| `and1504.tt2` | Compiler netlist consumed by the fitter |
| `and1504.fit` | Target settings, pin placement, and fitting report |
| `and1504.jed` | JEDEC programming data |
| `design.svf` | JTAG programming instruction stream exported by ATMISP |
| Command logs / `jtag.log` | Diagnostics and export outcome |

**Neither command programs a physical device.** An offline ATMISP log may say “erasing/programming/verifying”; here those messages describe generating the instruction stream.

## 3. Roughly what your automation script would look like

Think of the top-level script as a small coordinator:

```text
Create a fresh run directory
    ↓
Stage sources, testbench, and constraints
    ↓
Compile and simulate — stop if tests fail
    ↓
Fit for ATF1504ASV / TQFP100 — stop if target or pins are wrong
    ↓
Optionally export SVF through ATMISP
    ↓
Archive source revision, reports, logs, JED, and SVF
```

Here is a runnable example that coordinates the **existing demonstration scripts**. Save it as `automate.py` beside this guide:

```python
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def run_script(script, *arguments):
    subprocess.run(
        [sys.executable, str(script), *map(str, arguments)],
        check=True,
    )


def main():
    root = Path(__file__).resolve().parent
    examples = root / "examples"
    run_name = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    output = root / "build" / run_name

    # Simulate, compile, fit, and check the target-specific example.
    run_script(examples / "build_1504.py", output / "device")
    jed = output / "device" / "and1504.jed"

    # Export an SVF without a programmer. Requires an interactive desktop.
    run_script(examples / "atmisp_svf.py", jed, output / "svf")

    print(f"Build and offline export completed: {output}")
    print("No hardware was programmed.")


if __name__ == "__main__":
    main()
```

The lower-level scripts already implement command logging, timeouts, fresh output directories, and result checks. The coordinator uses `check=True` so it stops when a child script fails.

**For your real project:** replace the demonstration build stage with your sources and testbench, and update the expected pin assignments. `build_1504.py` deliberately checks the AND-gate example's particular vectors and pins; it is a template to adapt, not a generic project builder.

## 4. If your design will be VHDL or Verilog

**Update:** the Precision license is installed. The licensed VHDL synthesis and fitting flow has passed, including fixed-pin checks. The working entrypoint is:

```powershell
python examples\build_prochip_1504.py build\licensed1504 --language vhdl
```

See [ProChip validation](docs/PROCHIP_VALIDATION.md) for the PIN sidecar requirement, saved project, and IDE launch configuration. The original setup checklist follows.

For your actual VHDL/Verilog project:

1. Install/configure the supplied **Precision OEM** license.
2. Create one known-good project selecting your target, sources, top level, PCB pins, and timing requirements.
3. Export its settings using **File → Export Settings Script**. This captures the correct device/library names for this old OEM version.
4. Have Python run Precision using:

   ```text
   precision.exe -shell -file build.tcl
   ```

5. Feed the resulting **EDIF** into the ProChip FIT1504 flow.
6. Check the FIT report and export JED/SVF as above.

The working target-specific script is `examples/build_prochip_1504.py`. Both VHDL and Verilog synthesis/fitting have passed, and Verilog also passed offline SVF export. Its shared runner handles intermittent pre-script startup stalls with a bounded handshake/retry. The project also retains `precision_discover.tcl`, `precision_build.tcl`, and `run_hdl.py` for custom scripts.

ModelSim is optional and outside the requested synthesis workflow. Its examples remain available for separately licensed simulation if needed later.

See [the license-arrival checklist](docs/LICENSES.md) for exact next steps.

## 5. When you eventually attach a programmer

Keep programming a **separate, explicit action**, rather than doing it after every build.

For the supported ATDH1150USB cable, a reviewed ATMISP chain can be executed using:

```text
C:\ATMISP7\ATMISP.exe C:\absolute\path\target.chn -1
```

The supplied wrapper previews by default:

```powershell
python examples\atmisp_chain.py C:\absolute\path\target.chn
# Only after reviewing the chain and hardware:
python examples\atmisp_chain.py C:\absolute\path\target.chn --execute
```

Important distinctions:

- `-1` means **execute the saved chain**; it is not a dry run.
- A saved chain did **not** retain the offline SVF checkbox in our tests. Do not use `-1` as an assumed JED→SVF conversion command.
- The batch command was recognized, but this no-programmer VM reached a blocking hardware/settings error. Physical programming remains untested.
- A real VM setup needs USB-device passthrough and the correct driver, not merely a virtual COM port.

## 6. The pitfalls worth remembering

1. **Use the newer ProChip fitter explicitly.** WinCUPL also contains older fitters with different arguments.
2. **Keep simulation separate from JEDEC generation.** The working CPLD example uses separate `-s` and `-j` stages to avoid a legacy simulation failure.
3. **Do not trust exit code zero alone.** Check fresh artifacts, simulation results, target/package, fixed pins, and logs.
4. **Keep the FIT report with the JED.** The JED's generic header can say `ATF1504AS` even when the FIT report correctly records `ATF1504ASV`.
5. **You do not need POF2JED for the native flow.** It is only relevant if you already have a compatible MAX-series POF. It is not a VHDL/Verilog compiler or a package-remapping tool.
6. **Do not confuse offline export with hardware validation.** SVF generation works; physical programming and production timing have not been tested.

For details: [full automation guide](docs/AUTOMATION.md), [ATMISP guide](docs/ATMISP.md), and [test evidence](docs/EVIDENCE.md).
