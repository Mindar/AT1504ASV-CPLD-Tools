# CUPL compilation, functional simulation, and fitting

Required tools: WinCUPL and the ProChip FIT1504/library installation.
This directory includes the PLD design and all four AND-gate test vectors.

```powershell
python build_1504.py build\run001
```

The command separately runs functional simulation, device-netlist generation,
and ASV/TQFP100 fitting. Check `and1504.so`, `and1504.fit`, and `and1504.jed`.
Expected vectors: 00L, 01L, 10L, 11H. Expected pins: a=6, b=8, y=14.
Simulation and JEDEC generation use separate CUPL calls to avoid the observed
combined -s/-j failure. Set WINCUPL_HOME if WinCUPL is not at C:\Wincupl.

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
