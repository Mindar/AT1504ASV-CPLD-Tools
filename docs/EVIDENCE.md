# Evidence, limitations, and references

Investigation date: **11 November 2026**. Machine: Windows 11 x64 VM, Python 3.15.2 x64. No programmer or target connected. The task did not require installing an OpenCode extension: web search/fetch tools were available.

**Later licensed validation:** the Microchip license is installed. VHDL and Verilog synthesis and EDIF fitting for `ATF1504ASV-15AU100` passed with verified PIN-sidecar assignments; the saved Precision project reopened successfully. The Verilog flow also exported offline SVF. Correct ProChip IDE launch was checked. One startup stall and its serial retry are recorded in [ProChip validation](PROCHIP_VALIDATION.md). The matrix below preserves the earlier pre-license investigation.

## 1. Validation matrix

| Test | Observed result | Evidence |
|---|---|---|
| Installed components and Downloads | WinCUPL, ProChip/Precision/ModelSim, ATMISP, POF2JED, FTDI distribution, Python found | `examples/inventory.py`; inventory in main guide |
| ProChip FIT1502 help | Newer version 1918; exit 101 for help | `research/probes/prochip_fitter_help.txt` |
| WinCUPL FIT1502 help | Older version 1.8.7.8; exit 101 for help | `research/probes/wincupl_fitter_help.txt` |
| ModelSim version | ATMEL 6.2c / 2006.08, exit 0 | `research/probes/modelsim_version.txt` |
| CUPL without library environment | Error about LIBCUPL | `research/probes/cupl_help.txt` |
| SPLD ADDER compile/simulation | Exit 0; JED and ten-vector SO produced | `research/builds/adder/` |
| ATF1508 TIM_CNT compile/explicit fit | Exit 0; Design fits successfully | `research/builds/tim_cnt/` |
| ATF1504ASV TQFP100 functional simulation | All four AND-gate vectors correct | `research/builds/atf1504asv_final/and1504.so` |
| Target device netlist generation | TT2 contains pins 6, 8, 14 and target token | `research/builds/atf1504asv_final/and1504.tt2` |
| Exact target fit | Newer FIT1504, ASV/TQFP100, KEEP, JTAG ON, security OFF, correct pins | `research/builds/atf1504asv_final/fitter.log`, `and1504.fit`, `and1504.jed` |
| ATMISP native GUI export | Fresh nonempty Rev. D SVF and successful generation log | `research/builds/svf_final/design.svf`, `jtag.log` |
| GUI-saved single-device CHN | ATF1504ASV, IR width 10, Program/Verify value 1 | `research/atmisp_batch/generated_offline.chn` |
| Relative-path ATMISP batch attempt | Returned zero, no expected log; not accepted as success | `research/atmisp_batch/console.log` |
| Absolute-path ATMISP batch attempt | Blocking “Hardware and software settings mismatch.” | `research/atmisp_batch/diagnostics.json` |
| Compatible POF conversion | EPM7064 PLCC84 → 1504AS PLCC84, exit 0 | `research/builds/pof1504/` |
| Invalid POF target override experiment | Returned zero despite impossible 1502AS/PLCC84 pairing | `research/builds/pof/`; **not a usable target artifact** |
| Precision script entry | Failed missing `pscatmelcpldcore`, exit 11 | `research/licensed_probes/precision.log` |
| ModelSim console entry | Failed invalid license environment, exit 4 | `research/licensed_probes/modelsim.log` |
| Target simulation with combined -j/-s | Failed JEDEC-vector/undefined-pin path | `research/builds/atf1504asv/and1504.so`, `cupl.log` |
| Deliberately incorrect AND-gate expected output | CSIM returned 1; Python rejected the build | `research/builds/negative_simulation/` |

`research/validation.json` records artifact sizes and SHA-256 values after validating target, pin, simulation, and offline-export evidence. Recreate it with:

```powershell
python research\validate_results.py
```

The eight standard-library unit tests passed, Python compilation checks passed, and all local Markdown links were checked. The final target build was repeated successfully in `research/builds/checked1504/` after the final wrapper changes. A deliberately incorrect simulation vector was rejected, not silently accepted. The target JED's generic first-line `ATF1504AS` label does not reproduce the more specific ASV technology recorded in the FIT report; see the main guide's warning.

The successful target flow intentionally separates simulation, device-netlist generation, and fitting. Intermediate directories from failed experiments remain as evidence; **use the final directory**, not the earliest trial JED.

## 2. What is not claimed

- No physical programming, real-device verification, target IDCODE read, cable qualification, or board validation.
- No proof that your actual PCB uses demonstration pins 6, 8, 14.
- No timing closure for a production design or the `-15` grade based solely on a fit success.
- Licensed Precision synthesis/EDIF fitting is now validated for the supplied examples. ModelSim simulation remains license-blocked.
- Production-project pin/timing closure and an IDE-driven `.apj` build have not been validated.
- No installation or testing of Quartus, OpenOCD, an alternate JTAG cable, or an OpenCode extension.
- No proven ATMISP serial-number CLI syntax or stable public CHN file specification.
- No guarantee that a future ATMISP build keeps the same native control IDs.

## 3. Reproduce the useful tests

From the repository/documentation root in PowerShell, using new directories:

```powershell
python -m unittest discover -s tests -v
python examples\inventory.py
python examples\build_adder.py build\sanity-adder --simulate
python examples\build_1504.py build\sanity-1504
python examples\atmisp_svf.py build\sanity-1504\and1504.jed build\sanity-svf
python examples\convert_pof.py C:\POF2JED\work\myand2.pof build\sanity-pof --device 1504AS
```

The last POF example is a converter smoke test, not your TQFP100 design. The unit tests use standard-library mocks/current Python only and never invoke vendor programs or hardware.

The GUI-based export needs an interactive Windows desktop. New run names prevent stale files and vendor logs from contaminating results.

## 4. Primary local documentation

These are already installed; a web connection is not required to inspect them:

| Source | Why it matters |
|---|---|
| `C:\Users\admin\Downloads\ProChip_v5_0_2\release_notes.txt` | Distribution version 5.0.2 and changes |
| Same folder, `README.pdf` | Licensing distinction and installation layout |
| `C:\ATMEL_PLS_Tools\ProChip\help\fitter15xx.pdf` | CLI syntax, input formats, target settings, strategies, pin assignments |
| Same folder, `CPLD_Mentor_Verilog_tutorial.pdf` and `CPLD_Mentor_VHDL_tutorial.pdf` | Native HDL design flow and simulator-license requirement |
| Same folder, `Prochip4.chm` | IDE usage, device fitter integration, licensing help |
| `C:\ATMEL_PLS_Tools\Precision\shared\pdfdocs\precisionRTL_users.pdf` | Shell use and project/script workflow |
| Same directory, `precisionsyn_ref.pdf` | Tcl commands, compile/synthesize, project commands, exit semantics |
| `C:\ATMEL_PLS_Tools\Precision\shared\htmldocs\precisionRTL_users\setup_design01.html` | `precision -shell -file` documented locally |
| Same users manual, `projects18.html` | File → Export Settings Script |
| `C:\ATMEL_PLS_Tools\Precision\shared\htmldocs\precisionsyn_install\quick_install7.html` | MGLS/LM license-file search order |
| `C:\ATMEL_PLS_Tools\ModelSim\docs\pdfdocs\modelsim_oem_ref.pdf` | ModelSim command reference |
| Same directory, `modelsim_oem_user.pdf` | Console/DO simulation workflow |
| `C:\ATMEL_PLS_Tools\ModelSim\docs\cmd_help\oem_cmd_help.txt` | Installed onerror/onbreak command descriptions |
| `C:\ATMISP7\release_notes.txt` | 7.3.1, FTDI 2.12.36.20, cable restrictions and known problems |
| `C:\ATMISP7\Help\ATMISP.chm` | Exact `-1` batch command, SVF workflow, JTAG-disable warning |
| Same Help directory, `QSTutor.pdf` | Chain creation, ATDH1150USB, programming flow |
| `C:\POF2JED\README.txt` | CLI/GUI versions and supported conversion families |
| `C:\POF2JED\bin\help.htm` | Exact converter syntax, option meanings, conversion warnings |

CHM content was extracted with Windows HTML Help for inspection; for example:

```powershell
Start-Process C:\Windows\hh.exe -ArgumentList '-decompile C:\pldwork\atmisp_help C:\ATMISP7\Help\ATMISP.chm' -Wait
```

`research/atmisp_help/start.htm`, section `CMD`, contains the batch syntax; `start.htm`'s SVF section describes offline generation. `cmd.htm` explains the JTAG port-check override and external-programmer recovery requirement.

PDF text extraction used `pypdf` installed **only into the approved temporary research directory**, not into the system Python. `research/extract_manuals.py` is an investigative convenience requiring that optional dependency; the runnable examples do not depend on it.

## 5. Web references consulted

Prefer vendor documentation and installed manuals to generic download sites. One search result incorrectly described ATMISP as a microcontroller utility; it was not used as an authority for this CPLD flow.

### Microchip primary sources

1. [ATF1504ASV product page](https://www.microchip.com/en-us/product/atf1504asv).
2. [ATF1504ASV/ATF1504ASVL datasheet, DS20006185A](https://ww1.microchip.com/downloads/aemDocuments/documents/OTH/ProductDocuments/DataSheets/ATF1504ASV-ATF1504ASVL-Data-Sheet-20006185A.pdf): package identification, 100-pin TQFP signal/JTAG tables, ordering code.
3. [ATF15XX/ATF1500 fitter user guide](https://ww1.microchip.com/downloads/aemDocuments/documents/MPD/ProductDocuments/UserGuides/ATF15XX-ATF1500-CPLD-Fitter-User-Guide-DS20007127.pdf).
4. [Online fitter CLI section](https://onlinedocs.microchip.com/oxy/GUID-F1454631-FFF9-4807-A296-41526776DBA8-en-US-1/GUID-15BE71E5-4098-473C-AC42-3AA7A1C7DD98.html).
5. [CUPL PROPERTY statements](https://onlinedocs.microchip.com/oxy/GUID-F1454631-FFF9-4807-A296-41526776DBA8-en-US-1/GUID-2F055188-6902-4158-92F1-591530EF9624.html).
6. [ATMISP product/tool page](https://www.microchip.com/en-us/development-tool/atmisp): supported cable and offline SVF capability.
7. [ATF15xx In-System Programming guide](https://ww1.microchip.com/downloads/en/DeviceDoc/Atmel-8968-CPLD-ATF-ISP-User%20Guide.pdf): JTAG interface and reservation requirements.
8. [Precision licensing request page](https://www.microchip.com/prochiplicensing/), referenced by the installed README. Follow the vendor's current request process if redirected.
9. [Microchip support article about DOS launching ATMISP](https://microchip.my.site.com/s/article/Launch-and-execute-ATMISP-ATF15xx-CPLD-JTAG-ISP-software-using-DOS-command-prompt). The fetched page returned a loading/CSS error, so it **did not supply usable syntax**; installed CHM documentation did.

### Secondary examples, used for leads rather than authority

- [adrienkohlbecker/cupl.bat](https://github.com/adrienkohlbecker/cupl.bat): practical CUPL library/PATH setup and separate fit step. The supplied Python implementation is not a blind copy of its device mapping.
- [dinoboards CPLD toolchain fitter notes](https://github.com/dinoboards/cpld-toolchain/blob/main/docs/atmel-fitters.md): TT2 → vendor fitter architecture and older/newer fitter distinction.
- [Programmable logic with CPLDs](https://loriholden.com/posts/2023/programmable-logic-with-cplds/): practical WinCUPL command-line workflow.
- [Public single-device CHN example](https://github.com/levvayner/VGA_PLD/blob/main/VGA_SINGLE_PLD/atmisp/VGA_SINGLE_PLD.chn): format lead, subsequently checked against a chain saved by the installed ATMISP itself.
- [CPLD upgrade and toolchain discussion](https://www.steckschwein.de/post/2025/07/cpld-upgrade-new-toolchain/): third-party SVF-player background only; not evidence of compatibility with an untested programmer.

## 6. Keeping evidence useful

The research tree deliberately includes failed experiments. This is useful for understanding why the recommended workflow differs from a one-line internet build command. It is not a directory of production programming files.

Before publishing this folder, remove/redact local usernames, host/VM details, any future license files, and proprietary project data as appropriate. Vendor manuals and extracted content retain their original licensing/copyright terms. Never commit an actual `license.dat` or disclose host-bound licensing diagnostics in a public issue.
