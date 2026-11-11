# VERILOG synthesis and fitting

Compile the included AND-gate HDL for ATF1504ASV-15AU100, then fit it with
fixed pins a=6, b=8, y=14 and JTAG enabled. Required tools: licensed Precision
OEM and the ProChip FIT1504/library installation.

From this directory:

```powershell
python run.py build\run001
```

Inspect `build\run001\validation.json`, the `fit` directory's JED/FIT/PIN
files, and the saved Precision `.psp` project. The PIN sidecar is required;
the script creates it and checks the final placement.

For optional offline SVF export, also provision ATMISP and use an interactive
Windows desktop:

```powershell
python run.py build\run002 --svf
```

Precision's pre-script startup stall is handled by a 15-second readiness
handshake and up to three starts. Acknowledgement gates the synthesis script;
errors or timeouts after synthesis starts are not retried. No hardware is
programmed by these commands. HDL simulation is outside this example.

## Workstation preparation

Use Windows and an approved Python installation. No pip packages are required.
Provision the listed vendor tools through your normal approved process.
Use a short writable local path, and a new output directory for each run.

Default ProChip root: `C:\ATMEL_PLS_Tools`. If yours differs, set
`ATMEL_PLS_TOOLS` in the current shell before running Python. Precision needs
a license valid for the machine; set `MGLS_LICENSE_FILE` as instructed by the
license administrator. Confirm that the license is valid for the computer.

These are complete source copies. They do not import from the parent project.
Build outputs and logs stay in the selected output directory. Adapt the example
pin assignments to the PCB before preparing files for hardware programming.

