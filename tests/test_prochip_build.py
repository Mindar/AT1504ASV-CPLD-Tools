"""Test licensed-flow orchestration with fake vendor output and no license use."""

import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import sys
sys.path.insert(0, str(Path(__file__).absolute().parents[1] / "examples"))
import build_prochip_1504 as flow
import launch_prochip


class ProChipBuildTests(unittest.TestCase):
    def test_ide_launch_supplies_image_and_installation_directory(self):
        with patch.object(launch_prochip.subprocess, "Popen") as start, \
                contextlib.redirect_stdout(io.StringIO()):
            launch_prochip.main()
        command = start.call_args.args[0]
        self.assertEqual(command[1], "ProChipDesPrd.im")
        self.assertEqual(start.call_args.kwargs["cwd"], launch_prochip.PROCHIP / "bin")

    def exercise(self, work, bad_pin=False):
        def fake_synthesis(script, directory, timeout=600):
            text = script.read_text()
            self.assertIn("ATF1504ASV-15AU100", text)
            self.assertIn("-family ATF15xxASV", text)
            output = directory / "implementation"
            output.mkdir()
            (output / "prochip1504.edf").write_text("atf15asv")
            log = directory / "precision-console.log"
            log.write_text("BUILD_COMPLETED")
            return log

        def fake_fitter(command, directory, log_name):
            pins = (directory / "prochip1504.pin").read_text()
            self.assertIn("a : 6", pins)
            self.assertIn("b : 8", pins)
            self.assertIn("y : 14", pins)
            self.assertIn("EDIF", command)
            self.assertIn("ATF1504ASV", command)
            report = ["Device_name = TQFP100", "Tech_name = ATF1504ASV",
                      "Preassignment = keep", "Security_mode = OFF", "JTAG = ON"]
            for name, pin in {"A": 6, "B": 8, "y": 92 if bad_pin else 14,
                              "TDI": 4, "TMS": 15, "TCK": 62, "TDO": 73}.items():
                report.append(f"{name} is placed at pin {pin} (MC 1)")
            (directory / "prochip1504.fit").write_text("\n".join(report))
            (directory / "prochip1504.jed").write_text("example")
            log = directory / log_name
            log.write_text("Design fits successfully")
            return log

        with patch.object(flow, "run_precision", side_effect=fake_synthesis), \
                patch.object(flow, "run_tool", side_effect=fake_fitter), \
                contextlib.redirect_stdout(io.StringIO()):
            return flow.build(work)

    def test_sidecar_and_case_insensitive_pin_checks(self):
        with tempfile.TemporaryDirectory() as root:
            jed = self.exercise(Path(root) / "build")
            self.assertTrue(jed.is_file())
            self.assertTrue((jed.parent.parent / "validation.json").is_file())

    def test_pin_movement_is_rejected_after_zero_exit(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaisesRegex(RuntimeError, "y is placed at pin 14"):
                self.exercise(Path(root) / "build", bad_pin=True)


if __name__ == "__main__":
    unittest.main()
