"""Run documented HDL script entrypoints after installing the required license."""

import argparse
from pathlib import Path

from toolchain import run_precision, simulate_modelsim


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tool", choices=["precision", "modelsim"])
    parser.add_argument("script", type=Path)
    parser.add_argument("work", type=Path, help="Existing isolated working/project directory")
    args = parser.parse_args()
    function = run_precision if args.tool == "precision" else simulate_modelsim
    print(function(args.script, args.work))
    print("Process completed. Check tool reports and expected fresh outputs too.")


if __name__ == "__main__":
    main()
