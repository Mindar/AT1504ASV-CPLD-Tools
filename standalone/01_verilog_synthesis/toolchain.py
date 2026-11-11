"""Small, standard-library-only wrappers for the tools installed on this VM.

These functions build files. They do not program hardware.
"""

import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path


PLS_TOOLS = Path(os.environ.get("ATMEL_PLS_TOOLS", r"C:\ATMEL_PLS_Tools"))
WINCUPL = Path(os.environ.get("WINCUPL_HOME", r"C:\Wincupl"))
PROCHIP = PLS_TOOLS / "ProChip"
PRECISION = PLS_TOOLS / "Precision/bin/precision.exe"
MODELSIM = PLS_TOOLS / "ModelSim/win32aoem"
POF2JED = Path(os.environ.get("POF2JED_HOME", r"C:\POF2JED")) / "bin/POF2JED.exe"
ATMISP = Path(os.environ.get("ATMISP_HOME", r"C:\ATMISP7")) / "ATMISP.exe"


class StartupTimeout(subprocess.TimeoutExpired):
    """A vendor process did not reach its startup handshake."""


def startup_message_seen(log, marker):
    lines = log.read_text(encoding="cp1252", errors="replace").splitlines()
    # Match an emitted message, not marker text inside the logged command line.
    return any(line.strip() in (marker, "# Info: " + marker) for line in lines)


def wait_for_startup(process, log, marker, timeout):
    deadline = time.monotonic() + timeout
    while process.poll() is None:
        if startup_message_seen(log, marker):
            return True
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise StartupTimeout(process.args, timeout)
        try:
            process.wait(timeout=min(0.1, remaining))
        except subprocess.TimeoutExpired:
            pass
    return startup_message_seen(log, marker)


def tool_environment():
    """Change only the child process environment, not the Windows settings."""
    env = os.environ.copy()
    directories = [WINCUPL / "Shared", WINCUPL / "WinCupl",
                   PROCHIP / "pldfit", WINCUPL / "WinCupl" / "Fitters"]
    env["PATH"] = os.pathsep.join(map(str, directories)) + os.pathsep + env.get("PATH", "")
    env["FITTERDIR"] = str(PROCHIP / "pldfit")
    env["LIBCUPL"] = str(WINCUPL / "Shared" / "cupl.dl")
    # Also works from an already-running terminal that predates installation.
    license_file = PLS_TOOLS / "Licenses/license.dat"
    if license_file.is_file():
        env.setdefault("MGLS_LICENSE_FILE", str(license_file))
    return env


def run_tool(command, work, log_name, timeout=120, startup_marker=None, startup_timeout=15,
             startup_ack=None):
    """Run an argument list, save combined output, and reject nonzero exits.

    A zero exit alone does not prove success: callers also check artifacts.
    On Windows a timeout stops the launched process tree, including vendor
    launcher children. It never stops unrelated processes by executable name.
    """
    # Preserve mapped drive letters: old vendor Tcl can mishandle UNC paths.
    work = Path(os.path.abspath(work))
    command = [str(argument) for argument in command]
    log = work / log_name
    with log.open("wb") as output:
        output.write(f"Command: {subprocess.list2cmdline(command)}\n".encode("utf-8"))
        output.flush()
        process = subprocess.Popen(command, cwd=work, env=tool_environment(),
                                   stdin=subprocess.DEVNULL, stdout=output,
                                   stderr=subprocess.STDOUT)
        try:
            started = time.monotonic()
            if startup_marker:
                ready = wait_for_startup(process, log, startup_marker, min(startup_timeout, timeout))
                if ready and startup_ack is not None:
                    Path(startup_ack).touch(exist_ok=False)
            remaining = max(0, timeout - (time.monotonic() - started))
            returncode = process.wait(timeout=remaining)
        except subprocess.TimeoutExpired as error:
            phase = "STARTUP TIMEOUT" if isinstance(error, StartupTimeout) else "TIMEOUT"
            output.write(f"\n{phase} after {error.timeout} seconds\n".encode("ascii"))
            output.flush()
            if os.name == "nt":
                # Stop descendants before killing their launcher: once the
                # parent is gone, its child tree may no longer be discoverable.
                try:
                    subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                                   stdout=output, stderr=subprocess.STDOUT,
                                   timeout=15, check=False)
                except (OSError, subprocess.TimeoutExpired):
                    output.write(b"\nProcess-tree cleanup failed; inspect remaining children.\n")
            if process.poll() is None:
                process.kill()
            process.wait(timeout=5)
            raise
        output.write(f"\nExit code: {returncode}\n".encode("ascii"))
    if returncode != 0:
        raise RuntimeError(f"{Path(command[0]).name} failed ({returncode}). See {log}")
    return log


def require_file(path):
    """Reject missing or empty output instead of trusting the tool's exit code."""
    path = Path(path)
    if not path.is_file() or path.stat().st_size == 0:
        raise RuntimeError(f"Expected a nonempty output file: {path}")
    return path


def new_work_directory(path):
    """Never reuse an old output directory: stale JEDEC files are dangerous."""
    path = Path(os.path.abspath(path))
    path.mkdir(parents=True, exist_ok=False)
    return path


def compile_cupl(source, work, simulate=False, jedec_vectors=True):
    """Compile a copied PLD file in a NEW directory; optionally copy/run SI tests.

    For projects with includes, copy the full source/include tree instead.
    CPLDs may require a separate fit_tt2() step; inspect the compiler log.
    """
    source = require_file(Path(os.path.abspath(source)))
    work = new_work_directory(work)
    local_source = work / source.name
    shutil.copy2(source, local_source)
    options = "-m1anlx"
    if not simulate or jedec_vectors:
        options += "j"
    if simulate:
        shutil.copy2(source.with_suffix(".SI"), work / source.with_suffix(".SI").name)
        options += "s"
    run_tool([WINCUPL / "Shared" / "cupl.exe", options, "-u",
              WINCUPL / "Shared" / "Atmel.dl", local_source.name], work, "cupl.log")
    return work


def fit_tt2(tt2, family, package, technology):
    """Fit CUPL TT2 using the newer ProChip fitter, keeping assigned pins.

    family: 1502/1504/1508; package: e.g. PLCC44; technology: e.g. ATF1502AS.
    This overwrites same-stem compiler artifacts, so use an isolated build.
    """
    if family not in (1502, 1504, 1508):
        raise ValueError("family must be 1502, 1504, or 1508")
    tt2 = require_file(Path(os.path.abspath(tt2)))
    # CUPL may already have emitted a preliminary JED. Do not mistake it for
    # the output of this fitter run. This function owns same-stem build output.
    tt2.with_suffix(".jed").unlink(missing_ok=True)
    run_tool([PROCHIP / "pldfit" / f"fit{family}.exe", "-i", tt2.name,
              "-cupl", "-device", package, "-tech", technology,
              "-preassign", "keep", "-str", "JTAG=ON",
              "-str", "security=OFF"], tt2.parent, "fitter.log")
    return require_file(tt2.with_suffix(".jed"))


def convert_pof(source, work, device):
    """Convert a compatible POF; explicitly preserve JTAG and avoid security.

    The caller MUST check source density/package against the requested target
    and review the conversion report. The converter can accept bad overrides.
    """
    source = require_file(Path(os.path.abspath(source)))
    work = new_work_directory(work)
    shutil.copy2(source, work / source.name)
    output = source.with_suffix(".jed").name
    run_tool([POF2JED, "-i", source.name, "-o", output,
              "-device", device, "-JTAG", "ON"], work, "pof2jed.log")
    return require_file(work / output)


def run_precision(script, work, timeout=600, startup_attempts=3):
    """Run Precision with a handshake and retries only before user Tcl starts."""
    script = require_file(Path(os.path.abspath(script)))
    work = Path(os.path.abspath(work))
    if any(character in script.as_posix() for character in "{}\n\r"):
        raise ValueError("Use a script path without braces or newlines")
    marker = "PRECISION_STARTUP_READY"
    with tempfile.NamedTemporaryFile(mode="w", encoding="ascii", dir=work,
                                     prefix="precision-bootstrap-", suffix=".tcl", delete=False) as stream:
        bootstrap = Path(stream.name)
        acknowledgement = bootstrap.with_suffix(".ready")
        stream.write("fconfigure stdout -buffering line\n")
        stream.write(f"puts {{{marker}}}\nflush stdout\n")
        stream.write(f"while {{![file exists {{{acknowledgement.as_posix()}}}]}} {{after 50}}\n")
        stream.write(f"source {{{script.as_posix()}}}\n")
    for attempt in range(1, startup_attempts + 1):
        log_name = "precision-console.log" if attempt == 1 else f"precision-console-{attempt}.log"
        try:
            log = run_tool([PRECISION, "-shell", "-file", bootstrap], work, log_name,
                           timeout, startup_marker=marker, startup_timeout=15,
                           startup_ack=acknowledgement)
        except StartupTimeout:
            if attempt == startup_attempts:
                raise
            print(f"Precision did not finish startup; retrying ({attempt + 1}/{startup_attempts}).",
                  flush=True)
            continue
        text = log.read_text(encoding="cp1252", errors="replace")
        if "BUILD_FAILED:" in text:
            raise RuntimeError(f"Precision Tcl reported BUILD_FAILED. See {log}")
        if marker not in text:
            raise RuntimeError(f"Precision did not execute its startup handshake. See {log}")
        return log
    raise ValueError("startup_attempts must be at least one")


def simulate_modelsim(script, work):
    """Run a trusted ModelSim DO script in console mode; license required."""
    script = require_file(Path(os.path.abspath(script)))
    # Tcl also parses this string. Braces protect spaces, not embedded braces.
    if any(character in script.as_posix() for character in "{}\n\r"):
        raise ValueError("Use a script path without braces or newlines")
    return run_tool([MODELSIM / "vsim.exe", "-c", "-do",
                     f"do {{{script.as_posix()}}}"], work, "modelsim.log", 600)
