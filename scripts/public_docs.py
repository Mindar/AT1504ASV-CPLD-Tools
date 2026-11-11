"""Technical documentation for the source publication."""


def public_texts():
    readme = r"""# ATF1504ASV Python toolchain

Python automation for **ATF1504ASV-15AU100**, a 64-macrocell CPLD in a 100-pin TQFP package.

## Start

- [Setup](SETUP.md)
- [Quickstart](QUICKSTART.md)
- [Technical guide](PRINTABLE_GUIDE.md)
- [Independent examples](standalone/README.md)
- [ProChip synthesis](docs/PROCHIP_VALIDATION.md)
- [ATMISP and SVF](docs/ATMISP.md)
- [License configuration](docs/LICENSES.md)

Requires Windows, Python, and the installed vendor tools. The Python code uses only the standard library.

```powershell
python examples\preflight.py build\check001 --synthesize
python examples\build_prochip_1504.py build\verilog001
python examples\build_prochip_1504.py build\vhdl001 --language vhdl
```

Use a new output directory for each run. The synthesis examples create EDIF, PIN, FIT, and JEDEC files for the specified part. Optional `--svf` exports an SVF through ATMISP on an interactive desktop.

The sample design uses inputs 6/8 and output 14. Replace these assignments with the PCB's pinout before programming hardware. JTAG pins are 4, 15, 62, and 73.

The repository contains source code and instructions. Vendor software and license files are provisioned separately.
"""
    setup = r"""# Setup

## Required for HDL synthesis

- Windows and Python using the standard library.
- ProChip Designer with Precision OEM, FIT1504, and the ASV library.
- A Precision license valid for the computer.
- A short, writable local work directory.

Default installation paths:

```text
C:\ATMEL_PLS_Tools\Precision\bin\precision.exe
C:\ATMEL_PLS_Tools\Precision\pkgs\psr\techlibs\atf15asv.syn
C:\ATMEL_PLS_Tools\ProChip\pldfit\fit1504.exe
C:\ATMEL_PLS_Tools\ProChip\pldfit\aprim.lib
```

Configure a different installation root and license in the current PowerShell session:

```powershell
$env:ATMEL_PLS_TOOLS = 'C:\tools\ATMEL_PLS_Tools'
$env:MGLS_LICENSE_FILE = 'C:\licenses\license.dat'
```

Use the actual paths provided by the installation/license administrator. A network license may use a supplied server location instead of a file.

```powershell
python examples\preflight.py build\check001
python examples\preflight.py build\check002 --synthesize
python -m unittest discover -s tests -q
```

Static preflight checks files and paths. A successful synthesis check verifies actual execution and license checkout. No pip packages are needed.

ATMISP is optional for offline SVF export. Set `ATMISP_HOME` if its directory differs from `C:\ATMISP7`. CUPL examples additionally need WinCUPL; `WINCUPL_HOME` defaults to `C:\Wincupl`. POF conversion uses `POF2JED_HOME`, defaulting to `C:\POF2JED`.
"""
    quickstart = r"""# Quickstart

## HDL synthesis and fitting

```powershell
python examples\build_prochip_1504.py build\run001
python examples\build_prochip_1504.py build\run002 --language vhdl
```

The scripts stage sources, run Precision, create the fitter's PIN sidecar, fit the design, and verify the target and pin assignments.

Target settings: `ATF15xxASV`, `ATF1504ASV-15AU100`, speed `-15`; fitter `TQFP100`, `ATF1504ASV`, `KEEP`, JTAG ON, security OFF, `tPD=15`.

Inspect `validation.json`, `implementation\prochip1504.edf`, and `fit\prochip1504.fit`/`.jed`. Replace the sample pins with the PCB's assignments.

## Optional offline SVF

```powershell
python examples\build_prochip_1504.py build\run003 --svf
```

Requires ATMISP and an interactive Windows desktop. The output is `svf\design.svf`; no hardware programming is performed.

## CUPL

```powershell
python examples\build_1504.py build\cupl001
```

This compiles and functionally simulates the included AND-gate design, then fits it for ASV/TQFP100.

## Independent examples

Each numbered directory under `standalone/` contains all of its Python helpers and instructions. Start with the preflight example, then select the synthesis language or conversion process needed.
"""
    technical = r"""# Toolchain implementation guide

## Build sequence

```text
HDL → Precision → EDIF + PIN → FIT1504 → JED → optional ATMISP SVF
```

Required target settings:

| Setting | Value |
|---|---|
| Precision manufacturer / family | `Atmel` / `ATF15xxASV` |
| Part / speed | `ATF1504ASV-15AU100` / `-15` |
| Fitter package / technology | `TQFP100` / `ATF1504ASV` |
| Pin policy | `KEEP` |
| Development options | JTAG ON, security OFF, `tPD=15` |

## Python process runner

`examples/toolchain.py` implements the common operations:

- Copy the current environment and add tool/library paths for child processes.
- Run argument lists with an explicit working directory.
- Capture stdout and stderr in a file and check the exit code.
- Apply timeouts and stop the owned process tree when necessary.
- Require nonempty output files and reject reused build directories.
- Start Precision through a readiness handshake with bounded startup retries.

A concrete fitter invocation is:

```python
run_tool([
    PROCHIP / "pldfit/fit1504.exe",
    "-i", "design.edf", "-ifmt", "EDIF",
    "-lib", PROCHIP / "pldfit/aprim.lib",
    "-device", "TQFP100", "-tech", "ATF1504ASV",
    "-preassign", "keep", "-str", "JTAG=ON",
    "-str", "security=OFF", "-str", "tPD=15",
], work, "fitter-console.log")
```

`run_tool` comes from `toolchain.py`; `work` is a new build directory. Pass each argument separately, leave `shell=False`, and avoid adding manual quote characters. Use a short ASCII local or mapped-drive path. Preserve mapped drive letters rather than expanding them to UNC paths.

## Precision Tcl

```tcl
new_project -name design -folder {C:/pldwork/run001}
new_impl -name implementation
setup_design -manufacturer Atmel -family ATF15xxASV -part ATF1504ASV-15AU100 -speed -15
setup_design -design design -basename design -edif
add_input_file {C:/pldwork/run001/design.v}
compile
synthesize
save_impl
save_project
exit -force
```

Invoke it with `precision.exe -shell -file synthesize.tcl`. The Python helper uses a bootstrap around this script for startup recovery. The complete build implementation is in `examples/build_prochip_1504.py`.

## PIN sidecar

Before fitting `design.edf`, create `design.pin` in the same directory:

```text
CHIP "design" ASSIGNED TO AN TQFP100
a : 6
b : 8
y : 14
```

The fitter needs this sidecar to apply assignments. EDIF `pin_number` properties alone are insufficient. Keep the input constraints and inspect the final FIT report; signal names may be capitalized. The example checks names case-insensitively.

## Acceptance checks

Require successful process completion, a fresh EDIF/JED/FIT, the correct ASV/TQFP100 target, and the complete expected pin map. Check JTAG ON and security OFF. A fit success alone does not establish production timing closure. The generic JEDEC header may say `ATF1504AS`; retain the more specific target command and FIT report with it.

## Startup handling

Precision can stall before executing Tcl. Its bootstrap emits `PRECISION_STARTUP_READY`, flushes stdout, and waits for a unique acknowledgement file. Python creates that file only after receiving the readiness message. Tcl then sources the synthesis script.

If readiness times out after 15 seconds, terminate the owned process tree and retry, up to three starts. Do not retry failures after the synthesis script begins. Keep each attempt's log and serialize builds. Compatibility mode and CPU-affinity settings are not required by this implementation.

## CUPL calls

```text
cupl.exe -m1anlxs -u C:\Wincupl\Shared\Atmel.dl design.pld
cupl.exe -m1anlxj -u C:\Wincupl\Shared\Atmel.dl design.pld
fit1504.exe -i design.tt2 -cupl -device TQFP100 -tech ATF1504ASV -preassign keep -str JTAG=ON -str security=OFF
```

Keep functional simulation (`s`) and JEDEC generation (`j`) in separate calls. Supply the matching `.si` file and inspect `.so`. The first call produces simulation results; the second supplies the TT2 for explicit fitting.

## Optional POF conversion

```text
POF2JED.exe -i design.pof -o design.jed -device 1504ASV -JTAG ON
```

Use a compatible POF with the correct density, package, and pinout. Review the conversion report: an incompatible target override can still return zero. The source POF determines package/pin mapping.
"""
    atmisp = r"""# ATMISP and SVF

## Offline export

```powershell
python examples\atmisp_svf.py C:\pldwork\design.jed build\export001
```

The exporter creates one ATF1504ASV chain, selects Program/Verify, supplies the JED, enables Write SVF file, and verifies the output path before Run. It requires an interactive Windows desktop and matching process elevation levels. Inspect the SVF and `jtag.log`.

The automation uses native Windows control IDs from ATMISP 7.3.x:

| Control | ID |
|---|---:|
| Run | 1007 |
| Device count | 1018 |
| SVF filename | 1019 |
| Write SVF file | 1020 |
| Revision / TCK period | 1022 / 1023 |
| Device / operation / JED path | 1026 / 1027 / 1028 |

Revalidate control IDs after a tool upgrade. The saved CHN does not preserve the offline-output checkbox/filename; establish them for every export. Offline generation messages describe the generated instruction stream.

## Saved chain execution

```text
C:\ATMISP7\ATMISP.exe C:\pldwork\target.chn -1
```

Use absolute CHN and JED paths. `-1` executes the operations saved in the chain. Review the device, operation, and JED first. Error dialogs can block batch execution, so keep a timeout and retain the vendor log. ATMISP 7 uses the ATDH1150USB cable.

The provided automation validates offline export. Validate physical programming on the intended hardware before relying on an unattended programming process.
"""
    licenses = r"""# Precision license configuration

Use a Precision OEM license valid for the computer and installed product version. Configure the file or license-service location supplied by the administrator:

```powershell
$env:MGLS_LICENSE_FILE = 'C:\licenses\license.dat'
```

The default local fallback is `<ATMEL_PLS_TOOLS>\Licenses\license.dat`. The Python runner inherits existing license environment settings. Confirm checkout with a real synthesis smoke test:

```powershell
python examples\preflight.py build\check001 --synthesize
```

License checkout errors require checking the licensed feature/version, host binding, expiry, and configured location. Keep license files and licensing diagnostics out of the repository.
"""
    standalone = r"""# Independent examples

Each directory contains complete local source copies and its own README. No example imports Python helpers from another directory.

| Directory | Process |
|---|---|
| `01_verilog_synthesis` | Verilog synthesis, fitting, optional SVF |
| `02_vhdl_synthesis` | VHDL synthesis, fitting, optional SVF |
| `03_cupl_compile_simulate` | CUPL compilation, functional simulation, fitting |
| `04_offline_svf_export` | Existing ATF1504ASV JED to SVF |
| `05_workstation_preflight` | Static checks and real synthesis smoke test |
| `06_pof_conversion` | Compatible POF to JEDEC |

Synthesis examples include HDL sources. CUPL includes the design and test vectors. Conversion examples take an existing design file as input. Vendor applications and licenses are installed separately.
"""
    return {
        "README.md": readme,
        "SETUP.md": setup,
        "QUICKSTART.md": quickstart,
        "PRINTABLE_GUIDE.md": technical,
        "docs/AUTOMATION.md": technical,
        "docs/ATMISP.md": atmisp,
        "docs/LICENSES.md": licenses,
        "docs/PROCHIP_VALIDATION.md": technical,
        "standalone/README.md": standalone,
    }
