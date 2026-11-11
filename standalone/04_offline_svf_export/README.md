# Offline ATF1504ASV JEDEC-to-SVF export

Required tool: ATMISP 7.3.x. Requires an existing matching ATF1504ASV JEDEC
input and an interactive Windows desktop. All automation code is included;
there is no dependency on another example directory or an attached programmer.

```powershell
python atmisp_svf.py C:\pldwork\design.jed build\export001
```

The script creates a single-device ATF1504ASV Program/Verify chain, selects
and verifies Write SVF file, sets the output path, and checks ATMISP's own
generation log. Inspect `design.svf` and `jtag.log` in the new output directory.
The erasing/programming/verifying log messages describe the offline stream.

Default ATMISP path: C:\ATMISP7\ATMISP.exe. Set ATMISP_HOME to its containing
directory if different. Native control IDs are specific to the tested version;
after an upgrade, inspect/revalidate them before using the GUI automation.

## Workstation preparation

Use Windows and an approved Python installation. No pip packages are required.
Provision the listed vendor tools through your normal approved process.
Use a short writable local path, and a new output directory for each run.

Default ProChip root: `C:\ATMEL_PLS_Tools`. If yours differs, set
`ATMEL_PLS_TOOLS` in the current shell before running Python. Precision needs
a license valid for the machine; set `MGLS_LICENSE_FILE` as instructed by the
license administrator. The personal VM's license is host-bound.

These are complete source copies. They do not import from the parent project.
Build outputs and logs stay in the selected output directory. Adapt the example
pin assignments to the PCB before preparing files for hardware programming.
