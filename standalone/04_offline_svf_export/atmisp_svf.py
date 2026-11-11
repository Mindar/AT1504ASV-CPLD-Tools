"""Export ATF1504ASV JEDEC to SVF using ATMISP 7.3's native Windows GUI.

No third-party Python packages or attached programmer are required.
Control IDs are specific to the installed ATMISP version; see the guide.
The Run button is pressed ONLY after confirming offline SVF mode is checked.
"""

import argparse
import ctypes
import shutil
import subprocess
import time
from ctypes import wintypes
from pathlib import Path

from toolchain import ATMISP, new_work_directory, require_file


user32 = ctypes.WinDLL("user32", use_last_error=True)
CALLBACK = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
user32.EnumWindows.argtypes = [CALLBACK, wintypes.LPARAM]
user32.EnumChildWindows.argtypes = [wintypes.HWND, CALLBACK, wintypes.LPARAM]
user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
user32.GetDlgCtrlID.argtypes = [wintypes.HWND]
user32.IsWindow.argtypes = [wintypes.HWND]
user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.SendMessageTimeoutW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM,
                                     wintypes.LPARAM, wintypes.UINT, wintypes.UINT,
                                     ctypes.POINTER(ctypes.c_size_t)]
user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]


def send(handle, message, first=0, second=0):
    """Bound each native control message so a hung GUI cannot block forever."""
    result = ctypes.c_size_t()
    if not user32.SendMessageTimeoutW(handle, message, first, second, 2, 2000,
                                     ctypes.byref(result)):
        raise TimeoutError("ATMISP did not respond to a Windows control message")
    return result.value


def window_text(handle):
    buffer = ctypes.create_unicode_buffer(2048)
    try:
        send(handle, 0x000D, len(buffer), ctypes.addressof(buffer))  # WM_GETTEXT
    except TimeoutError:
        if not user32.IsWindow(handle):  # Dialog disappeared during enumeration.
            return ""
        raise
    return buffer.value


def set_text(handle, value):
    buffer = ctypes.create_unicode_buffer(value)
    send(handle, 0x000C, 0, ctypes.addressof(buffer))  # WM_SETTEXT


def children(parent):
    controls = {}

    @CALLBACK
    def visit(handle, _):
        controls[user32.GetDlgCtrlID(handle)] = handle
        return True

    user32.EnumChildWindows(parent, visit, 0)
    return controls


def windows(pid):
    result = []

    @CALLBACK
    def visit(handle, _):
        owner = wintypes.DWORD()
        user32.GetWindowThreadProcessId(handle, ctypes.byref(owner))
        if owner.value == pid:
            result.append(handle)
        return True

    user32.EnumWindows(visit, 0)
    return result


def wait_for(get_result, description, timeout=15):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        result = get_result()
        if result:
            return result
        time.sleep(0.1)
    raise TimeoutError(f"Timed out waiting for {description}; inspect ATMISP dialogs")


def click(handle):
    user32.PostMessageW(handle, 0x00F5, 0, 0)  # BM_CLICK, asynchronous for modal dialogs


def choose(dialog, control_id, value):
    handle = children(dialog)[control_id]
    buffer = ctypes.create_unicode_buffer(value)
    index = send(handle, 0x0158, -1, ctypes.addressof(buffer))  # CB_FINDSTRINGEXACT
    if index == ctypes.c_size_t(-1).value:
        raise RuntimeError(f"ATMISP does not offer {value!r}")
    send(handle, 0x014E, index, 0)  # CB_SETCURSEL
    send(dialog, 0x0111, control_id | (1 << 16), handle)  # CBN_SELCHANGE
    if window_text(handle) != value:
        raise RuntimeError(f"Could not select {value!r}")


def export_svf(jed, directory):
    work = new_work_directory(directory)
    shutil.copy2(Path(jed).resolve(strict=True), work / "design.jed")
    process = subprocess.Popen([str(ATMISP)], cwd=work)
    try:
        def find_main():
            return next((handle for handle in windows(process.pid)
                         if 1007 in children(handle)), None)

        def dialog_named(name):
            return next((handle for handle in windows(process.pid)
                         if window_text(handle) == name), None)

        main = wait_for(find_main, "ATMISP main window")
        user32.PostMessageW(main, 0x0111, 0xE100, 0)  # File > New

        def count_dialog():
            for handle in windows(process.pid):
                controls = children(handle)
                # The new-chain dialog has an OK button and one Edit control.
                if 1 in controls and 1026 not in controls and handle != main:
                    edits = []
                    for child in controls.values():
                        classname = ctypes.create_unicode_buffer(256)
                        user32.GetClassNameW(child, classname, len(classname))
                        if classname.value == "Edit":
                            edits.append(child)
                    if len(edits) == 1:
                        return handle, edits[0]
            return None

        dialog, edit = wait_for(count_dialog, "new-chain device count")
        set_text(edit, "1")
        click(children(dialog)[1])
        dialog = wait_for(lambda: dialog_named("Device Property"), "Device Property")
        choose(dialog, 1026, "ATF1504ASV")
        choose(dialog, 1027, "Program/Verify")
        set_text(children(dialog)[1028], str(work / "design.jed"))
        click(children(dialog)[1])
        wait_for(lambda: not dialog_named("Device Property"), "device dialog to close")

        controls = children(main)
        if window_text(controls[1018]) != "1":
            raise RuntimeError("Expected exactly one device in the chain")
        if window_text(controls[1020]) != "Write SVF file":
            raise RuntimeError("Unexpected ATMISP control layout")
        if send(controls[1020], 0x00F0) != 1:  # BM_GETCHECK
            send(controls[1020], 0x00F5)  # BM_CLICK updates the dialog too
        output = work / "design.svf"
        set_text(controls[1019], str(output))
        set_text(controls[1023], "1")  # TCK period, microseconds
        if send(controls[1020], 0x00F0) != 1 or window_text(controls[1019]) != str(output):
            raise RuntimeError("Offline SVF mode was not established; refusing Run")
        click(controls[1007])

        def completed():
            log = work / "jtag.log"
            return log.is_file() and "JTAG instructions finished successfully" in log.read_text(
                encoding="cp1252", errors="replace")

        wait_for(completed, "successful SVF export", timeout=60)
        return require_file(output)
    finally:
        # This script owns this GUI process. It has no unsaved user project.
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=5)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("jed", type=Path)
    parser.add_argument("work", type=Path, help="NEW local ASCII output directory")
    args = parser.parse_args()
    print(export_svf(args.jed, args.work))


if __name__ == "__main__":
    main()
