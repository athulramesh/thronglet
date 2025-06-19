#!/usr/bin/env python3
import sys
from src.cli.interface import ThrongletCLI


def main():
    cli = ThrongletCLI()
    cli.run(sys.argv[1:])


if __name__ == "__main__":
    main()
