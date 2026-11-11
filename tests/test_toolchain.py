"""Standard-library tests; these never invoke vendor tools or hardware."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "examples"))
import toolchain


class ToolchainTests(unittest.TestCase):
    def test_startup_handshake_acknowledges_before_work(self):
        with tempfile.TemporaryDirectory() as root:
            work = Path(root)
            ack = work / "ready.ack"
            code = (
                "import sys,time; from pathlib import Path; "
                "print('STARTUP_READY',flush=True); "
                "p=Path(sys.argv[1]); "
                "exec('while not p.exists(): time.sleep(0.01)'); "
                "print('BODY_PASS',flush=True)"
            )
            log = toolchain.run_tool([sys.executable, "-c", code, ack], work, "run.log", timeout=5,
                                     startup_marker="STARTUP_READY", startup_timeout=2,
                                     startup_ack=ack)
            self.assertTrue(ack.is_file())
            self.assertIn("BODY_PASS", log.read_text())

    def test_startup_timeout_does_not_acknowledge(self):
        with tempfile.TemporaryDirectory() as root:
            ack = Path(root) / "ready.ack"
            with self.assertRaises(toolchain.StartupTimeout):
                toolchain.run_tool([sys.executable, "-c", "import time; time.sleep(10)"],
                                   root, "run.log", timeout=5, startup_marker="NEVER_READY",
                                   startup_timeout=0.1, startup_ack=ack)
            self.assertFalse(ack.exists())

    def test_precision_retries_only_startup_timeout(self):
        with tempfile.TemporaryDirectory() as root:
            work = Path(root)
            script = work / "build.tcl"
            script.write_text("puts BODY")
            log = work / "success.log"
            log.write_text("PRECISION_STARTUP_READY\nBUILD_COMPLETED")
            with patch.object(toolchain, "run_tool", side_effect=[
                    toolchain.StartupTimeout("precision", 15), log]) as run:
                self.assertEqual(toolchain.run_precision(script, work), log)
            self.assertEqual(run.call_count, 2)
            bootstrap = next(work.glob("precision-bootstrap-*.tcl")).read_text()
            self.assertLess(bootstrap.index("while"), bootstrap.index("source"))

    def test_precision_does_not_retry_synthesis_timeout(self):
        with tempfile.TemporaryDirectory() as root:
            script = Path(root) / "build.tcl"
            script.write_text("puts BODY")
            with patch.object(toolchain, "run_tool", side_effect=
                              subprocess.TimeoutExpired("precision", 120)) as run:
                with self.assertRaises(subprocess.TimeoutExpired):
                    toolchain.run_precision(script, root)
            self.assertEqual(run.call_count, 1)

    @unittest.skipUnless(sys.platform == "win32", "Windows process-tree cleanup")
    def test_timeout_stops_launcher_child(self):
        import ctypes
        from ctypes import wintypes

        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        kernel.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        with tempfile.TemporaryDirectory() as root:
            pid_file = Path(root) / "child.pid"
            code = (
                "import subprocess,sys,time; from pathlib import Path; "
                "p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)']); "
                "Path(sys.argv[1]).write_text(str(p.pid)); time.sleep(30)"
            )
            with self.assertRaises(subprocess.TimeoutExpired):
                toolchain.run_tool([sys.executable, "-c", code, pid_file], root, "run.log", timeout=1)
            self.assertTrue(pid_file.is_file(), "Test launcher did not create its child")
            handle = kernel.OpenProcess(0x100001, False, int(pid_file.read_text()))
            if handle:
                try:
                    if kernel.WaitForSingleObject(handle, 0) != 0:
                        kernel.TerminateProcess(handle, 99)  # Clean up our test child.
                        self.fail("The timed-out launcher's child was still running")
                finally:
                    kernel.CloseHandle(handle)

    def test_work_directory_must_be_new(self):
        with tempfile.TemporaryDirectory() as root:
            work = toolchain.new_work_directory(Path(root) / "run")
            self.assertTrue(work.is_dir())
            with self.assertRaises(FileExistsError):
                toolchain.new_work_directory(work)

    def test_output_must_exist_and_be_nonempty(self):
        with tempfile.TemporaryDirectory() as root:
            output = Path(root) / "design.jed"
            with self.assertRaises(RuntimeError):
                toolchain.require_file(output)
            output.touch()
            with self.assertRaises(RuntimeError):
                toolchain.require_file(output)
            output.write_bytes(b"example")
            self.assertEqual(toolchain.require_file(output), output)

    def test_child_environment_does_not_change_parent(self):
        original = toolchain.os.environ.copy()
        env = toolchain.tool_environment()
        self.assertEqual(toolchain.os.environ.copy(), original)
        self.assertEqual(env["FITTERDIR"], str(toolchain.PROCHIP / "pldfit"))

    def test_runner_saves_output(self):
        with tempfile.TemporaryDirectory() as root:
            log = toolchain.run_tool([sys.executable, "-c", "print('HELLO')"], root, "run.log")
            self.assertIn("HELLO", log.read_text())
            self.assertIn("Exit code: 0", log.read_text())

    def test_runner_rejects_nonzero_exit(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(RuntimeError):
                toolchain.run_tool([sys.executable, "-c", "raise SystemExit(7)"], root, "run.log")
            self.assertIn("Exit code: 7", (Path(root) / "run.log").read_text())

    def test_runner_enforces_timeout(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(subprocess.TimeoutExpired):
                toolchain.run_tool([sys.executable, "-c", "import time; time.sleep(10)"],
                                   root, "run.log", timeout=0.1)

    def test_fitter_uses_explicit_target_and_fresh_jed(self):
        with tempfile.TemporaryDirectory() as root:
            work = Path(root)
            tt2 = work / "design.tt2"
            tt2.write_text("example")
            jed = work / "design.jed"
            jed.write_text("STALE")

            def fake_fitter(command, directory, log):
                self.assertFalse(jed.exists())
                self.assertIn("fit1504.exe", str(command[0]))
                self.assertIn("TQFP100", command)
                self.assertIn("ATF1504ASV", command)
                self.assertIn("JTAG=ON", command)
                self.assertIn("security=OFF", command)
                jed.write_text("FRESH")

            with patch.object(toolchain, "run_tool", side_effect=fake_fitter):
                self.assertEqual(toolchain.fit_tt2(tt2, 1504, "TQFP100", "ATF1504ASV"), jed)

    def test_precision_failure_marker_is_not_success(self):
        with tempfile.TemporaryDirectory() as root:
            work = Path(root)
            script = work / "build.tcl"
            script.write_text("example")
            log = work / "precision.log"
            log.write_text("BUILD_FAILED: synthesis error\nExit code: 0")
            with patch.object(toolchain, "run_tool", return_value=log):
                with self.assertRaises(RuntimeError):
                    toolchain.run_precision(script, work)


if __name__ == "__main__":
    unittest.main()
