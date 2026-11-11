"""Launch ProChip Designer using the installed shortcut's image and directory."""

import subprocess

from toolchain import PROCHIP, tool_environment


def main():
    directory = PROCHIP / "bin"
    subprocess.Popen([str(directory / "visual.exe"), "ProChipDesPrd.im"],
                     cwd=directory, env=tool_environment())
    print("ProChip launched.")


if __name__ == "__main__":
    main()
