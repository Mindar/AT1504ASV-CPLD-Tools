# Automating this VM's Atmel/Microchip PLD tools with Python

**Target: ATF1504ASV-15AU100 (64-macrocell CPLD, 100-pin TQFP).** Confirm the full ordering code against your actual device. Investigated on this Windows VM on **11 November 2026**.

## Start here

- **[Work-PC readiness and tomorrow's runbook](TOMORROW.md)**: prerequisites, host-bound licensing, source-only publication, preflight, and go/no-go checks.
- **[Independent examples](standalone/README.md)**: six self-contained source directories for synthesis, CUPL simulation, SVF export, preflight, and POF conversion.
- **Current setup:** work is now in `G:\Standardprojekt`. Licensed Precision synthesis and target fitting are verified; see [ProChip validation](docs/PROCHIP_VALIDATION.md), including bounded recovery for an intermittent startup stall. ModelSim is optional and outside the requested synthesis workflow.
- **[Licensed ProChip workflow](docs/PROCHIP_VALIDATION.md)**: VHDL/Verilog build script, target settings, PIN sidecar, and correct IDE launch.
- **[Printable work-PC implementation guide](PRINTABLE_GUIDE.md)**: self-contained tool calls, Python build implementation, and operational checks for manual reimplementation.
- **[Quickstart for your ATF1504ASV use case](QUICKSTART.md)**: the recommended flow, essential settings, and a small Python coordinator example.
- [Detailed automation guide](docs/AUTOMATION.md): inventory, tested build flow, simulation, fitters, POF conversion, Precision/ModelSim, and automation design.
- [ATMISP programming and offline SVF export](docs/ATMISP.md): command syntax, native GUI automation, saved chain format, and hardware limitations.
- [License-arrival checklist](docs/LICENSES.md): prepare Precision now; distinguish its license from ModelSim's.
- [Evidence and references](docs/EVIDENCE.md): exact results, known failures, and local/vendor documentation.
- [Readable Python examples](examples/): standard library only; no Python packages needed for the supported examples.

## Quick start: no license or programmer needed

Run in PowerShell from this directory. Use a **new** output directory each time.

```powershell
python examples\inventory.py
python examples\build_1504.py build\first1504
python examples\atmisp_svf.py build\first1504\and1504.jed build\firstsvf
```

The first build simulates a small AND gate, generates a TT2 netlist, and fits it explicitly for `ATF1504ASV` / `TQFP100`. The second script drives ATMISP's GUI in **offline SVF mode**. It requires an interactive Windows desktop, not a USB programmer.

**Do not program these demonstration pins onto an arbitrary PCB.** Inputs 6 and 8 and output 14 are illustrative legal package pins, not a board-specific pinout. Review the FIT report, JTAG settings, supply requirements, and schematic first.

## What was established

| Capability | Result on this VM |
|---|---|
| Python → CUPL compilation | Working |
| Python → functional CUPL simulation | Working, including all four target-example vectors |
| Python → explicit ProChip FIT1504, ASV, TQFP100 | Working |
| Python → POF2JED compatible-file conversion | Working; target/package review remains essential |
| Python → ATMISP offline SVF generation | Working through native Windows controls |
| ATMISP `absolute-chain-path -1` | Recognized; absent-hardware/settings path can show a blocking dialog |
| Precision scripted synthesis | VHDL and Verilog synthesis/fitting passed; Verilog offline SVF export passed |
| ModelSim console scripting | Entry point tested; blocked by missing simulator license |
| Physical programming/verification | Not tested: this VM has no programmer or target attached |

The installed tools are predominantly **SPLD/CPLD** tools, not Libero/FlashPro. Do not apply modern Microchip FPGA Tcl commands to this suite.

`research/` contains local experimental probes, vendor-document extracts, and diagnostics. It is excluded from publication. The supported examples do not depend on it. For a GitHub web upload, use `python scripts\prepare_publication.py` and review the source-only output first; web uploads do not apply `.gitignore`.
