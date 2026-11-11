# Work-PC runbook: prerequisites, first build, and recovery

## Decide whether tomorrow is ready today

For HDL synthesis, the work computer needs all of the following **already provisioned through an approved route**:

| Requirement | Evidence to obtain today |
|---|---|
| Windows and permission to run the vendor tools | Confirm with the actual standard-user account |
| Python, if using the Python automation | `python --version` and `python -c "import subprocess,ctypes,tempfile"` |
| Installed ProChip/Precision and fitter libraries | Confirm the files below exist and can be executed |
| A Precision OEM license valid for the work PC | Successful checkout/synthesis on that machine, or confirmation from its license administrator |
| A writable local work directory | Create a small file there with the standard account |
| Permission to execute locally written Python/Tcl | Confirm application-control policy permits the workflow |
| Access to the reference material | Open the GitHub page on the work PC; also print this guide and the needed source files |

**If the vendor tools are absent and you cannot install them, the source repository cannot provide synthesis. Arrange IT installation or access to an approved, already-provisioned company build machine now.** If Python alone is unavailable, the installed vendor commands can still be used manually; Python automation will need an approved interpreter.

**The personal VM's license has a specific host binding.** Do not assume it will activate on the work PC. Ask Microchip/the license administrator for a license issued for that machine or an appropriate company license service. The installed `Precision\bin\LMUTIL.EXE lmhostid` command can provide the work PC's host information if your administrator requests it. Send license/host details only through the approved channel, never through this repository.

A successful build on the personal VM cannot establish work-PC permissions, license validity, or application-control behavior. The best confidence comes from running the small target example on the work PC **before tomorrow's session**, under the account you will actually use.

## Keep tomorrow's first objective small

First produce a JED from the included three-signal HDL example. Then adapt the real design. Keep SVF generation and hardware programming out of the first checkpoint.

Required installed files for the HDL flow, assuming the tested defaults:

```text
C:\ATMEL_PLS_Tools\Precision\bin\precision.exe
C:\ATMEL_PLS_Tools\Precision\pkgs\psr\techlibs\atf15asv.syn
C:\ATMEL_PLS_Tools\ProChip\pldfit\fit1504.exe
C:\ATMEL_PLS_Tools\ProChip\pldfit\aprim.lib
```

WinCUPL, POF2JED, a programmer, and ModelSim are not dependencies of this HDL synthesis/fitting checkpoint. ATMISP is needed only if you later want SVF export.

Use the installed tool versions wherever possible: Precision `2013a.10OEM_Atmelcpld` and ProChip fitter `1918`. Other versions require their own smoke test. Testing here used Python 3.15.2; the code uses Python 3.8+ APIs, but older interpreter versions have not been exercised here. Use the work PC's approved interpreter and run the tests with it.

## Files to reference or retype

For the tested HDL build, the minimum set is:

```text
examples/toolchain.py
examples/build_prochip_1504.py
examples/prochip1504.v       # Verilog, or prochip1504.vhd for VHDL
```

Also bring these as printed/reference material:

```text
examples/preflight.py
PRINTABLE_GUIDE.md
docs/PROCHIP_VALIDATION.md
TOMORROW.md
```

The tests directory provides regression checks for the orchestration and error handling. `research/` contains local experiments and is excluded from publication; tomorrow's supported commands do not depend on it. No `pip install`, Git client, downloaded Python package, or IDE extension is required.

Preserve filenames, indentation, ASCII quote characters, and UTF-8 encoding when retyping. Ensure Windows has not appended `.txt` to `.py`, `.tcl`, `.v`, `.vhd`, or `.pin` files.

## Work-PC setup: user-session settings only

Choose a short, writable local directory. For example:

```powershell
$work = Join-Path $env:LOCALAPPDATA 'pldwork'
New-Item -ItemType Directory -Force $work
Set-Location $work
```

Keep sources and build outputs outside the installation directory. Avoid a UNC path, OneDrive/network synchronization, long names, spaces, and non-ASCII characters for the first test. If the approved user directory contains problematic characters, ask IT for a suitable writable location.

If the installation uses a different root, set it **before starting Python**:

```powershell
$env:ATMEL_PLS_TOOLS = 'C:\actual\approved\installation'
```

This root must contain `Precision` and `ProChip`. The script defaults to `C:\ATMEL_PLS_Tools`. It also accepts `ATMISP_HOME`, `WINCUPL_HOME`, and `POF2JED_HOME` for the optional tools.

Configure the work-PC-valid license according to its administrator's instructions. A file-based example is:

```powershell
$env:MGLS_LICENSE_FILE = 'C:\approved\licenses\license.dat'
```

Use the supplied server location instead if it is a network license. These assignments affect the current session and its children. The scripts do not need to write machine-wide environment settings or the installation directory. Do not change host IDs or license contents to make this VM's file match another machine.

## Checkpoint 1: static preflight

From your locally recreated project folder:

```powershell
python examples\preflight.py "$work\check001"
```

Use a new directory on each attempt. This checks file availability and path suitability. It cannot prove the license or executable permissions work.

## Checkpoint 2: real synthesis and fitting

```powershell
python examples\preflight.py "$work\check002" --synthesize
```

For VHDL:

```powershell
python examples\preflight.py "$work\check003" --synthesize --language vhdl
```

Require these outputs:

```text
check002\preflight.json                         synthesis: passed
check002\smoke\validation.json                 synthesis/fitting: passed
check002\smoke\implementation\prochip1504.edf
check002\smoke\fit\prochip1504.pin
check002\smoke\fit\prochip1504.fit
check002\smoke\fit\prochip1504.jed
```

The FIT report must confirm `ATF1504ASV`, `TQFP100`, `KEEP`, JTAG ON, security OFF, and the requested pins. The example uses a=6, b=8, y=14. The JTAG pins are 4, 15, 62, and 73.

**The example pinout is not your PCB pinout.** Update both HDL attributes and the PIN-sidecar generation/checks when adapting the production design.

## Five details worth checking against the reference

1. **Exact target:** Precision family `ATF15xxASV`, part `ATF1504ASV-15AU100`, speed `-15`; fitter technology `ATF1504ASV`, package `TQFP100`, strategy `tPD=15`.
2. **PIN sidecar:** the EDIF fitter needs the same-basename `.pin` file. EDIF `pin_number` properties alone were ignored in testing. Preserve `KEEP` and check the final assignments.
3. **Startup recovery:** preserve the bootstrap/acknowledgement mechanism in `run_precision()`. It retries a pre-script startup stall only. It does not restart a failed synthesis script.
4. **Fresh output:** each attempt gets a new directory. Read its actual logs and outputs; do not accept an older JED.
5. **Paths and subprocess arguments:** keep the mapped/local path rather than expanding it to UNC; pass an argument list with `shell=False`; capture stdout/stderr and use bounded waits.

## Manual vendor-command checkpoint

If automation reimplementation is delayed, use the concrete Tcl and fitter commands in section 5 of `PRINTABLE_GUIDE.md`. The saved Tcl needs a configured project, or use the `new_project`/`new_impl` sequence generated by `build_prochip_1504.py`.

The key calls are:

```text
precision.exe -shell -file synthesize.tcl
fit1504.exe -i prochip1504.edf -ifmt EDIF -lib <installed-aprim.lib> -device TQFP100 -tech ATF1504ASV -preassign keep -str JTAG=ON -str security=OFF -str tPD=15
```

Use the full installed executable/library paths. Supply the PIN sidecar first. The same host-valid license is required. Precision can stall during startup; keep the handshake/watchdog in the automated path, and retain the PID when supervising a manual launch so only that process tree is stopped if necessary.

## If something fails: stop at the right boundary

| Symptom | Action |
|---|---|
| Python or installed executable missing | Ask IT/provisioning; retyping code cannot supply it |
| Access denied or application-control block | Ask IT to permit the approved workflow; do not disable endpoint controls |
| License checkout/host mismatch | Contact the license administrator; do not keep editing Tcl |
| No startup-ready message | Let bounded startup recovery finish; retain all attempt logs |
| `BUILD_FAILED` or compiler errors after readiness | Fix that source/script error; do not retry the whole script blindly |
| Missing PIN file or moved signals | Correct sidecar basename/content and KEEP; check the FIT report |
| Different synthesis/library version | Validate the exact target and small example before the real design |
| GitHub unavailable | Use the printed source/runbook and approved local tools |

Keep work-PC diagnostics inside the approved company workspace. They may include user paths, machine names, license-server information, or design details. Do not upload them to a public issue without review.

## Before publishing tonight

Run `python scripts\prepare_publication.py` on the personal machine and review the resulting `publication\source` folder. It includes an explicit source/documentation allowlist and hashes; it excludes research data, license files, installers, and vendor binaries.

**GitHub's web upload does not apply `.gitignore`. Upload the reviewed source-only folder, not the entire VM working directory.** Check company/IP rules before publishing. Keep real company HDL, PCB constraints, and license files out of the public repository.

After your final successful test, publish that exact revision and give it a stable tag/bookmark such as `workpc-reference-v1`. Open the page from the work PC if possible, and print the source files now. Avoid relying on a last-minute download, Git installation, private-repository sign-in, or network exception tomorrow.
