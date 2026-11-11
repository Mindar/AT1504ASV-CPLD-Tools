"""Print a concise, read-only inventory without launching vendor applications."""

import json
import platform
import sys
from pathlib import Path

from toolchain import ATMISP, MODELSIM, POF2JED, PRECISION, PROCHIP, WINCUPL


def main():
    tools = {
        "CUPL compiler": WINCUPL / "Shared/cupl.exe",
        "WinCUPL GUI": WINCUPL / "WinCupl/Wincupl.exe",
        "WinSim GUI": WINCUPL / "WinSim/winsim.exe",
        "CUPL simulator": WINCUPL / "Shared/csim.exe",
        "ProChip GUI": PROCHIP / "bin/visual.exe",
        "Precision": PRECISION,
        "ModelSim": MODELSIM / "vsim.exe",
        "ATMISP": ATMISP,
        "POF2JED": POF2JED,
    }
    for family in (1502, 1504, 1508):
        tools[f"ProChip FIT{family}"] = PROCHIP / f"pldfit/fit{family}.exe"
    report = {
        "python": sys.version,
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "tools": {name: {"path": str(path), "exists": path.is_file()}
                  for name, path in tools.items()},
        "downloaded_installers": [path.name for path in (Path.home() / "Downloads").iterdir()
                                  if path.is_file() and path.suffix.lower() in (".zip", ".exe")],
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
