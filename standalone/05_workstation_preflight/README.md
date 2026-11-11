# Workstation preflight and real synthesis smoke test

This directory contains every source file needed for its optional build.
Static checks require Python. Real synthesis requires licensed Precision OEM,
the ProChip fitter, and the ASV library.

```powershell
python preflight.py build\check001
python preflight.py build\check002 --synthesize
python preflight.py build\check003 --synthesize --language vhdl
```

Static success verifies paths/files, not license checkout or execution policy.
Run --synthesize under the account that will perform builds. Inspect
`preflight.json` and `smoke\validation.json`.

Optional --svf also needs ATMISP and an interactive desktop. ModelSim and
WinCUPL are not dependencies of this HDL smoke test.

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
