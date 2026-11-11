"""Run this directory's self-contained VERILOG target example."""

import argparse
from pathlib import Path

from build_prochip_1504 import build


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("work", type=Path, help="New output directory")
    parser.add_argument("--svf", action="store_true", help="Export offline SVF through ATMISP")
    args = parser.parse_args()
    build(args.work, language="verilog", svf=args.svf)


if __name__ == "__main__":
    main()
