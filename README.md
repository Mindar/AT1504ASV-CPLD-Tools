# Automating Atmel/Microchip PLD tools with Python

**Target: ATF1504ASV-15AU100 (64-macrocell CPLD, 100-pin TQFP).** Confirm the full ordering code against your actual device.

## Start here

- **[Printable implementation guide](PRINTABLE_GUIDE.md)**: self-contained tool calls, Python build implementation, and operational checks.
- **[Quickstart for ATF1504ASV](QUICKSTART.md)**: the recommended flow, essential settings, and a small Python coordinator example.
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

## What was established

| Capability | Result on this VM |
|---|---|
| Python → CUPL compilation | Working |
| Python → functional CUPL simulation | Working, including all four target-example vectors |
| Python → explicit ProChip FIT1504, ASV, TQFP100 | Working |
| Python → POF2JED compatible-file conversion | Working; target/package review remains essential |
| Python → ATMISP offline SVF generation | Working through native Windows controls |
| ATMISP `absolute-chain-path -1` | Recognized; absent-hardware/settings path can show a blocking dialog |
| Precision scripted synthesis | Entry point tested; blocked by missing OEM license |
| ModelSim console scripting | Entry point tested; blocked by missing simulator license |
| Physical programming/verification | Not tested: this VM has no programmer or target attached |

`research/` contains experimental probes, extracted installed documentation, logs, and build artifacts. Start with `examples/`, not the exploratory scripts. Extracted vendor manuals remain vendor-owned; do not redistribute the research tree indiscriminately.
