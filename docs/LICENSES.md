# When the requested licenses arrive

**Update:** the supplied license is installed. Licensed VHDL and Verilog synthesis, EDIF fitting, pin preservation, and reopening the saved project have passed. The Verilog flow also exported offline SVF. See [ProChip validation](PROCHIP_VALIDATION.md), including the recorded startup stall/retry. The missing-license results below record the original investigation. ModelSim remains separately license-blocked.

The user has already requested licenses from Microchip and expects them in 1–2 workdays. No license was downloaded, generated, patched, or bypassed during this investigation.

## 1. Establish what the license actually covers

The installed ProChip 5.0.2 README states:

- **Precision OEM synthesis:** requires a Microchip-provided license.
- **ModelSim simulation:** Microchip no longer provides ModelSim licenses; contact Siemens for an appropriate license.

Therefore a Precision license should not be assumed to unlock the bundled ModelSim ATMEL 6.2c. Ask which product/features, version, expiration, and host binding the supplied file covers.

The installed `C:\ATMEL_PLS_Tools\Licenses` directory contained no files during inspection.

### Current observed failures

Precision, using its documented shell/Tcl entrypoint:

```text
# Error: [13503]: Unable to locate a valid Precision Atmel CPLD RTL OEM license
# Error: [13507]: Missing license atomic: pscatmelcpldcore
# Error: [580]: Failed product configuration check.
Exit code: 11
```

ModelSim console startup:

```text
Unable to checkout a license.
** Fatal: Invalid license environment. Application closing.
Exit code: 4
```

Those are license failures, not evidence that `-shell -file` or `-c -do` are invalid syntax. Their embedded scripts could not yet be exercised beyond startup.

## 2. Install the file without changing unrelated machine settings

1. Keep the supplied license and its accompanying instructions securely.
2. Confirm it is issued for this VM/host ID and the **OEM Atmel CPLD Precision** product/version.
3. Place it at the vendor-recommended location, for example:

```text
C:\ATMEL_PLS_Tools\Licenses\license.dat
```

4. Point only the current PowerShell/Python child environment at it initially:

```powershell
$env:MGLS_LICENSE_FILE = 'C:\ATMEL_PLS_Tools\Licenses\license.dat'
```

The installed Precision installation manual documents `MGLS_LICENSE_FILE` before `LM_LICENSE_FILE` in its search order. A stale registry/environment setting can mask another location. Do not indiscriminately overwrite all existing license settings or start a license server unless the supplied instructions call for one.

For a network license, the value may be a vendor-specified `port@server` instead of a file path. Use the exact server/port given by the license administrator; do not invent values or open arbitrary firewall ports.

Python equivalent:

```python
import os
import subprocess

env = os.environ.copy()
env['MGLS_LICENSE_FILE'] = r'C:\ATMEL_PLS_Tools\Licenses\license.dat'
subprocess.run(
    [r'C:\ATMEL_PLS_Tools\Precision\bin\precision.exe',
     '-shell', '-file', r'C:\pldwork\discover.tcl'],
    cwd=r'C:\pldwork', env=env, timeout=120, check=True,
)
```

The example library inherits these environment variables automatically. If separately configuring ModelSim, use the settings specified for its own license; its startup error explicitly mentions `LM_LICENSE_FILE` as an example.

## 3. Test the correct entrypoints first

Create an isolated working directory and run:

```powershell
python examples\run_hdl.py precision examples\precision_discover.tcl C:\pldwork\licensecheck
```

Expected progress: instead of the license error, `setup_design -list_technology` should produce the technologies available to this OEM edition. Save that output.

Do not use `precision.exe -help` as the primary license/CLI probe. On this installation it spawned a GUI child rather than behaving as a short console help command. The initial probe timed out, and its inherited output-pipe handles delayed cleanup until the owned GUI child was terminated.

If a valid ModelSim license is also provided, start with:

```powershell
& 'C:\ATMEL_PLS_Tools\ModelSim\win32aoem\vsim.exe' -c -do 'quit -code 0 -force'
```

Then run the included `logic.v`, `logic_tb.v`, and `simulate.do` in a copied, isolated directory. Require both a successful exit and the `TEST_PASS` transcript marker.

## 4. Export a known-good Precision project

This is the shortest path to reliable OEM-specific device tokens:

1. Launch ProChip/Precision normally once.
2. Select ATF1504ASV, 100-pin TQFP, and the appropriate speed/operating conditions.
3. Add your sources and top-level design.
4. Configure actual PCB pin constraints and required clocks/timing.
5. Save the `.psp` project.
6. Use **File → Export Settings Script**, as documented by the installed Precision manual.
7. Save the exported Tcl alongside your source/build scripts.
8. Run it using `precision.exe -shell -file ...` and record the generated EDIF/report locations.

The template `examples/precision_build.tcl` opens `design.psp`, runs compile/synthesize/report/save, and emits markers. The Python wrapper rejects `BUILD_FAILED:` even if the process returned zero. Still check `BUILD_COMPLETED`, the reports, and a newly generated EDIF; a marker alone is not sufficient for sign-off.

Where possible, have the exported settings script create a fresh project/implementation per build. Avoid parallel workers rewriting the same saved `.psp` and results directory.

## 5. Complete the EDIF/fitter integration

After synthesis works:

1. Confirm the output is the expected EDIF and references the correct Atmel primitive library.
2. Run the documented FIT1504 EDIF input flow described in [AUTOMATION.md](AUTOMATION.md).
3. Confirm pin constraints survived into the FIT report.
4. Require `Tech_name = ATF1504ASV`, `Device_name = TQFP100`, JTAG ON, and intended security settings.
5. Review timing reports against the actual `-15` part and clock requirements.
6. Run functional simulation and, if required, post-fit timing simulation.
7. Export SVF using the already-working ATMISP Python flow.

Only after this succeeds can the Precision → EDIF → FIT1504 path be labeled end-to-end validated on this VM. Today it is documented preparation, not a claimed completed synthesis test.

## 6. Diagnostics if it still fails

The installation includes `LMUTIL.EXE`/`LMTOOLS.EXE` in Precision's `bin` directory. The installed manuals and vendor instructions should determine which diagnostics apply. Typical read-only diagnostics include `lmutil lmhostid` and `lmutil lmdiag -c <license-location>`, but avoid publishing their complete output: it may reveal host IDs, server names, and licensing details.

Check:

- Correct host/MAC binding for the VM and matching licensed feature/version.
- Guest clock/date and license expiry. The VM date during testing was November 2026; do not “fix” an expired license by falsifying time.
- License-file permissions under the exact user/service account doing the build.
- Environment-variable precedence, registry settings, and stale server addresses.
- Whether a node-locked file or a floating-server setup was supplied.
- Availability of a seat and server connectivity for floating licenses.

Do not regenerate VM MAC addresses, clone a node-locked license to another host, remove signatures, or bypass checks. If the VM host identity changes, request a supported rehost from the vendor.

## 7. Ready-now versus ready-later checklist

- [x] Tool discovery and version inventory.
- [x] Python 3.15 standard-library wrappers.
- [x] Target-specific CUPL functional simulation.
- [x] Target-specific explicit ASV/TQFP100 fitting.
- [x] Automated offline ATMISP SVF export.
- [x] Documented Precision and ModelSim script entrypoints tested to license checks.
- [x] Install the actual Precision license.
- [x] Verify exact OEM target/settings Tcl and save/reopen a project.
- [x] Validate VHDL/Verilog synthesis, EDIF export, and pin-constraint transfer for the examples.
- [x] Add and test bounded recovery for the intermittent pre-script startup stall.
- [ ] Validate the production design's timing requirements.
- [ ] Optional: obtain/verify separate simulator entitlement if simulation is wanted later.
- [ ] Validate actual programming once supported USB hardware is available.
