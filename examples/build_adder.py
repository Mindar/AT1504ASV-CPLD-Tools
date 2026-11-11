"""Compile and simulate the installed SPLD adder example without hardware."""

import argparse
from pathlib import Path

from toolchain import WINCUPL, compile_cupl, require_file


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("work", type=Path, help="New, preferably short ASCII output directory")
    parser.add_argument("--simulate", action="store_true")
    args = parser.parse_args()
    work = compile_cupl(WINCUPL / "Examples" / "Atmel" / "ADDER.PLD",
                        args.work, simulate=args.simulate)
    print(require_file(work / "ADDER.jed"))


if __name__ == "__main__":
    main()
