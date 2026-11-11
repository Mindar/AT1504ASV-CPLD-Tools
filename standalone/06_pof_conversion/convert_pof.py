"""Convert a compatible MAX-series POF to ATF15xx JEDEC, without hardware."""

import argparse
from pathlib import Path

from toolchain import convert_pof


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("work", type=Path, help="New output directory")
    parser.add_argument("--device", required=True, choices=[
        "1502AS", "1504AS", "1508AS", "1502ASV", "1504ASV", "1508ASV"])
    args = parser.parse_args()
    print(convert_pof(args.source, args.work, args.device))


if __name__ == "__main__":
    main()
