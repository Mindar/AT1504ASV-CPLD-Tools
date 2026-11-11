# ATMISP: Python automation, batch programming, and offline SVF

## 1. What is available and what was tested

The installed tool is **ATMISP**, the ATF15xx CPLD JTAG programmer—not Atmel Studio, AVR ISP, or Microchip FlashPro. Use:

```text
C:\ATMISP7\ATMISP.exe
```

The distribution is 7.3.1; its executable/SVF banners still identify as 7.3. ATMISP 7 supports **ATDH1150USB**. The older LPT/parallel-cable instructions in historical documents refer to ATMISP 6 and are not instructions for this installation.

This VM has **no programmer or target device**. Nevertheless, the following were tested:

- Launching ATMISP and enumerating its actual Windows controls.
- Creating a single-device **ATF1504ASV** chain through its native dialogs.
- Selecting **Program/Verify** and a freshly fitted target JEDEC file.
- Generating an SVF **offline**, without a cable, from Python.
- Saving and inspecting a chain emitted by this ATMISP version.
- Trying the documented batch interface and capturing its absent-hardware/settings failure behavior.

No physical erase, program, readback, margin test, timing validation, or on-board functional test was possible. The offline log's “erasing/programming/verifying” lines describe the generated **instruction stream**, not operations on a connected part.

## 2. Two automation interfaces, for different purposes

| Goal | Interface | Important limitation |
|---|---|---|
| Execute a reviewed programming chain | `ATMISP.exe absolute-file.chn -1` | Needs actual supported hardware; can still block on an error dialog |
| Turn JED into SVF without hardware | GUI: Write SVF file → Run | No documented standalone SVF-export CLI switch was found |

Do not invent `--program`, `--device`, `--jed`, `--svf`, or `--quiet` flags from other programming utilities. In particular, `-1` is **digit one**, not lowercase `l`, and it is **not** a dry-run flag.

## 3. Documented batch syntax

The installed help, `ATMISP.chm`, Getting Started → “Launching ATMISP Using DOS Command”, states:

```text
atmisp.exe [filename.chn] [-1]
```

With `-1`, ATMISP loads and executes the chain in the background without launching its normal GUI and creates a log containing success, failure, and warning messages.

For your application, use **absolute paths**, including absolute JEDEC references in the chain:

```text
C:\ATMISP7\ATMISP.exe C:\pldwork\release001\target.chn -1
```

### Python: preview before execution

```powershell
python examples\atmisp_chain.py C:\pldwork\release001\target.chn
```

This prints the working directory and exact command but does not run it. To execute a reviewed chain:

```powershell
python examples\atmisp_chain.py C:\pldwork\release001\target.chn --execute
```

The command executes **all operations already saved in the chain**. It does not add a “program” operation or change the target on your behalf. Review it interactively before a real hardware run. The wrapper uses a timestamped console log, but ATMISP's own `jtag.log` has a fixed name, so copy/archive it after every run and serialize executions.

### Observed batch caveats on this VM

1. A relative argument `test.chn -1` returned **zero**, produced no useful output, and did not create the expected vendor log. Do not interpret this as successful execution.
2. Supplying an **absolute chain path** caused ATMISP to process the request and display **“Hardware and software settings mismatch.”** in this no-cable environment. It blocked until a timeout/diagnostic cleanup.
3. A chain with absolute JEDEC references gave the same settings-mismatch path. This establishes recognition of the documented request and a runtime dependency failure; it does **not** prove a complete real-hardware transaction.
4. Empty stdout is normal for GUI-oriented programs. The example preserves console output, but the primary result is ATMISP's own log and, later, the actual device outcome.

Treat `-1` as a documented batch facility, **not a guarantee that all failure paths are noninteractive**. On a production worker, inspect/handle only known errors; do not blindly auto-click “OK” until the process exits. That can hide bad targets, bad chains, or security warnings.

The installed release notes also mention selecting a USB cable by serial number from a command prompt, but the exact argument syntax was not established from the accessible installed help. No serial-number switch is invented here. Obtain version-specific syntax from Microchip or validate it with multiple real cables before adding it to a production wrapper.

## 4. Saved chain file: use a GUI-generated template

This version saved the following single-device chain after selecting **ATF1504ASV / Program/Verify**:

```text
1 4 1 0

ATF1504ASV
10
1
C:\Users\admin\AppData\Local\Temp\opencode\isp\and1504.jed
```

Observed fields:

- `ATF1504ASV` is the selected device name.
- `10` matches the displayed instruction-register width.
- `1` is the operation value saved for **Program/Verify** in this observed template.
- The final line is the associated JEDEC path.

The first line contains chain/settings values; do not generalize the meaning of every number from one sample. The installed help does not specify a stable formal CHN schema. Multiple-device chains, UNKNOWN/BYPASS entries, other instructions, calibration, and port settings should initially be created in the GUI and saved as separate reviewed templates.

**Do not generate a chain from a random internet sample and assume the numeric operation is safe.** A public sample helped explore the format, but the template above was reproduced by the installed program itself.

### Simple Python template update

Keep a known-good, GUI-generated `.chn` in your project and replace exactly one known JEDEC path:

```python
from pathlib import Path

template = Path("templates/program_verify_1504asv.chn")
destination = Path("release001/target.chn")
old_path = r"C:\pldwork\template\design.jed"
new_path = str(Path("release001/design.jed").resolve(strict=True))

text = template.read_text(encoding="cp1252")
if text.count(old_path) != 1:
    raise ValueError("Expected exactly one known JEDEC path in the template")
destination.parent.mkdir(parents=True, exist_ok=True)
with destination.open("w", encoding="cp1252", newline="\r\n") as stream:
    stream.write(text.replace(old_path, new_path))
```

This does not guess instruction numbers or reserialize an undocumented grammar. Check that the template's target and operation are still correct. Keep paths short and representable by this legacy program's code page.

## 5. Offline SVF generation: fully automated from Python

An SVF file describes JTAG operations and data. It is not interchangeable with a JEDEC fusemap. It lets a compatible JTAG/SVF player execute the programming sequence later. A generated SVF is also an excellent software-only test artifact for this VM.

The installed help documents:

1. Create/load the chain.
2. Select **Write SVF file**.
3. Choose an output filename.
4. Select revision C/D (D is preferred for ATE).
5. Optionally use state resets as appropriate for the target chain.
6. Click Run.

### Important discovery: CHN does not retain offline-output settings

Saving the chain after selecting offline output produced the same basic CHN content. The SVF filename and checkbox state were **not serialized** in the observed file. Therefore:

> Running a saved chain with `-1` must not be assumed to generate SVF instead of contacting hardware.

Use a separate GUI-controlled export path. The automated exporter explicitly selects and verifies offline mode before pressing Run.

### Run the working exporter

```powershell
python examples\atmisp_svf.py build\target001\and1504.jed build\svf001
```

[`atmisp_svf.py`](../examples/atmisp_svf.py) is a standalone, standard-library-only Windows automation example. It:

1. Creates a new work directory and copies the JED to `design.jed`.
2. Launches a **new process it owns**.
3. Finds that process's main window, not another user's ATMISP instance.
4. Creates a chain containing one ATF1504ASV.
5. Selects Program/Verify and the copied JED.
6. Confirms the chain contains one device.
7. Selects **Write SVF file** and verifies its checked state.
8. Sets an explicit SVF output path and a 1 µs TCK-period field.
9. Refuses Run if offline mode/path were not established.
10. Presses Run and waits for ATMISP's own fresh successful-generation log.
11. Checks that the SVF exists and is nonempty.
12. Terminates only the GUI instance it launched.

All input/output files remain in the work directory. The script does not execute the SVF on hardware, and it does not need Precision/ModelSim licenses.

The 1 µs field is a reproducible export setting, not a claim that every board/cable combination supports any particular reliable programming rate. Confirm timing on the real system later. The program retains the GUI's SVF revision default; this installed version produced **Rev. D**. Check the generated header if revision matters to your player.

### Actual offline result

The generated header starts:

```text
// SVF file written by ATMISP version 7.3
// SVF Rev. D
TRST ABSENT;
ENDIR IDLE;
ENDDR IDLE;
HDR 0;
HIR 0;
TDR 0;
TIR 0;
```

Its `jtag.log` contains:

```text
log: erasing device #1.
log: programming device #1.
log: verifying device #1: ... OK ...
log: JTAG instructions finished successfully.
```

Again: these are offline export messages. They do **not** demonstrate that a real part was erased or verified.

### Why the native Windows code is longer than a subprocess wrapper

ATMISP exposes ordinary Win32 dialogs/controls. Python's `ctypes` can call `user32` directly, avoiding an additional GUI automation package and Python-3.15 package compatibility questions.

The script uses control messages rather than screen coordinates:

| Control | ID in this installed version |
|---|---:|
| Run | 1007 |
| Number of devices (read-only display) | 1018 |
| SVF filename edit | 1019 |
| Write SVF file checkbox | 1020 |
| SVF revision combo | 1022 |
| TCK period edit | 1023 |
| Use state reset checkbox | 1024 |
| Device-name combo in Device Property | 1026 |
| JTAG-operation combo | 1027 |
| JEDEC-path edit | 1028 |
| Instruction-width edit | 1032 |

These IDs were inspected and exercised locally. They are **not a vendor-supported API**; after an upgrade, inspect controls and rerun an offline smoke test before trusting them. Do not confuse the number-of-devices field with the SVF filename—the exploratory scripts initially did, triggering an integer-validation dialog rather than an export.

The message wrappers use pointer-sized values for 64-bit Python and finite `SendMessageTimeoutW` calls. Text is read with `WM_GETTEXT`, since `GetWindowText` cannot retrieve arbitrary other-process edit-control contents. System-defined messages used here are marshalled by Windows across bitness; custom control structures would require more care.

The code also handles the race where a dialog disappears between window enumeration and reading its caption. Polling is bounded and concerns GUI readiness, not arbitrary long sleeps between clicks.

### Desktop and security requirements

- An interactive Windows desktop is required; no RDP mouse coordinates are used, but windows/messages must work.
- Run Python and ATMISP at compatible integrity levels. Windows may block messages from an unelevated process to an elevated one.
- Use one export at a time per automation worker.
- Do not allow someone to interact with the owned ATMISP instance while the script is running.
- The script's checks reduce accidental hardware execution; still review it before adapting it to a machine with a real cable.
- Do not use untrusted JED, Tcl, chain, or installer files. These legacy tools were not designed as a sandbox.

An alternative is `pywinauto` with its Win32 backend, using the same discovered control IDs. That may be convenient for a larger automation project, but it was not needed or installed for the working examples. Avoid mouse-coordinate automation unless no native control route is available.

## 6. Using the SVF later

Some third-party JTAG stacks can play SVF, but **JED→SVF success is not proof of player/cable compatibility**. A future Python wrapper around a chosen player can use the same argument-list/log/timeout approach.

For example, OpenOCD often exposes an `svf` command inside its configuration language, but OpenOCD is **not installed or tested here**. Cable configuration, scan-chain TAP definitions, voltage adaptation, expected IDCODE, state-reset semantics, delays, and TDO comparisons must be validated for the actual hardware. Do not disable TDO checking merely to obtain a success exit code.

Do not bypass ATMISP by toggling arbitrary FTDI pins from Python without an independently validated JTAG/programming implementation. The FTDI DLL is a transport API, not the ATF1504 programming algorithm.

## 7. Real-programmer bring-up checklist

When a programmer is available:

1. Confirm the exact target part/package and the 3.3 V power design.
2. Pass the **ATDH1150USB device** through to the VM and install the correct FTDI driver for that guest.
3. Confirm ATMISP sees the supported cable; use its Scan USB Cable option after attaching it if needed.
4. Confirm chain order/count and identify the target as ATF1504ASV.
5. Review a JED generated for your actual PCB pin map, with JTAG ON and development security OFF.
6. Save a reviewed Program/Verify chain through the GUI.
7. Perform a supervised GUI operation first, then the absolute-path `-1` command.
8. Require the expected successful vendor-log result, not just Python's process code.
9. Independently exercise the board's logic and timing.
10. Establish recovery procedures before ever enabling security or disabling JTAG.

The installed help warns that disabling JTAG makes the device inaccessible through ISP; recovery requires an external programmer. Also, `Program/Verify` may erase/rewrite the part—treat it as destructive to existing device contents.

The release notes describe restrictions for mixed BE/RE and other-family chains. Your single ATF1504ASV target avoids that specific case, but any future multi-device chain still requires explicit ordering and BYPASS configuration.
