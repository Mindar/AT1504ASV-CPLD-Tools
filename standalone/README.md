# Independent automation examples

Each numbered directory contains complete Python source copies and its own
instructions. Run commands from inside the chosen directory. No example imports
from its parent directory or another example; no pip packages are required.
Installed vendor applications and a suitable license are still prerequisites.

| Directory | Process | Input included? |
|---|---|---|
| `01_verilog_synthesis` | Verilog → Precision → EDIF/PIN → FIT1504 → JED; optional SVF | Yes, HDL fixture |
| `02_vhdl_synthesis` | VHDL → Precision → EDIF/PIN → FIT1504 → JED; optional SVF | Yes, HDL fixture |
| `03_cupl_compile_simulate` | CUPL compile, four-vector simulation, explicit ASV fitting | Yes, PLD and SI fixtures |
| `04_offline_svf_export` | Existing ATF1504ASV JED → offline ATMISP SVF | Supply the JED to convert |
| `05_workstation_preflight` | File/path checks and optional real licensed synthesis | Yes, both HDL fixtures |
| `06_pof_conversion` | Compatible MAX-series POF → target JEDEC | Supply a compatible POF |

The HDL/CUPL fixtures target ATF1504ASV/TQFP100 with illustrative pins 6, 8,
and 14. Review and change those for the actual PCB before programming hardware.

For tomorrow's work PC, begin with `05_workstation_preflight`, then choose
`01_verilog_synthesis` or `02_vhdl_synthesis`. Read `TOMORROW.md` in the main
project for the installation, host-bound license, and publication checks.

## Keeping independent copies consistent

The source copies are maintained by `scripts/sync_standalone_examples.py`.
They remain independent at runtime; the script is a maintenance tool only.

From the main project root:

```powershell
python scripts\sync_standalone_examples.py --check
```

After reviewing canonical source changes, `--refresh` explicitly updates the
generated copies. It never deletes unrelated files. Each example uses a `build`
directory for its generated results; these are excluded from Git publication.
