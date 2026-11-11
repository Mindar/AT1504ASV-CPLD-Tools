# Convert a compatible POF to ATF15xx JEDEC

Required tool: POF2JED. Supply your own compatible MAX-series POF; no vendor
binary/design file is bundled. All Python code is included in this directory.

```powershell
python convert_pof.py C:\pldwork\design.pof build\conversion001 --device 1504ASV
```

Review the generated TXT report and JED. The source POF supplies the package
and pin mapping: for the intended board it must match TQFP100 and the PCB pins.
The converter accepted an incompatible target override in testing and still
returned zero. Check density, package, voltage family, JTAG, and security.

Default converter path: C:\POF2JED\bin\POF2JED.exe. Set POF2JED_HOME if needed.
The native Precision/CUPL build flows do not need this conversion step.

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
