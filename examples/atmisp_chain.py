"""Print an ATMISP batch command; execute it only with --execute.

A CHN file may erase/program/secure hardware. Review it in ATMISP first.
The process return code is diagnostic, NOT proof that programming succeeded.
"""

import argparse
import subprocess
from pathlib import Path

from toolchain import ATMISP, run_tool


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("chain", type=Path, help="Existing, reviewed ATMISP .CHN file")
    parser.add_argument("--execute", action="store_true", help="Execute ALL operations saved in the chain")
    args = parser.parse_args()
    chain = args.chain.resolve(strict=True)
    if chain.suffix.lower() != ".chn":
        parser.error("Expected a .CHN file")
    command = [ATMISP, chain, "-1"]
    print(f"Working directory: {chain.parent}")
    print(subprocess.list2cmdline(list(map(str, command))))
    if not args.execute:
        print("Preview only. Add --execute after reviewing chain operations and JEDEC paths.")
        return
    # A unique console log prevents overwriting evidence from a previous run.
    from datetime import datetime
    log_name = f"atmisp-console-{datetime.now():%Y%m%d-%H%M%S-%f}.log"
    log = run_tool(command, chain.parent, log_name, timeout=300)
    print(f"Process returned zero; inspect ATMISP's own LOG file and results. Console: {log}")


if __name__ == "__main__":
    main()
