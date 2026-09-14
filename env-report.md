# Environment Report

## Agent and repository path

- Primary agent path: `/root`.
- Repository path: `/workspace/pfa_week01`.
- Current Git branch: `work`.
- Operating system: Ubuntu 24.04.4 LTS.
- Shell: Bash 5.2.

## Installed tools checked

| Tool | Result |
| --- | --- |
| Python 3 | Available: Python 3.14.4 at `/root/.pyenv/shims/python3` |
| Git | Available: Git 2.43.0 |
| Node.js | Available: Node.js v24.15.0 with npm/npx 11.4.2 |
| Python quality tools | Available: pytest, ruff, black, mypy, and pyright |
| Build and language tools | Available: make, GCC/G++, Clang, Java, Go, Rust, Ruby, PHP, Bun, and GitHub CLI |
| Maya / mayapy | Not installed or not on `PATH` |
| Blender | Not installed or not on `PATH` |
| ffmpeg / asciinema / OBS-style command-line recorders | Not found on `PATH` |

## What broke and how it was fixed

No required part of this first Python tool broke during environment inspection. Maya, Blender, and command-line screen-recording programs are unavailable, so the tool was deliberately written as a standard-library Python program that scans ordinary project files and does not depend on 3D software; use an available desktop screen recorder to capture the required demonstration.

## How the tool was checked

The tool is designed to run with `python3 yourtool.py`, which scans the current folder, and it can scan a chosen folder with `python3 yourtool.py /path/to/project`. The optional `--output report.txt` argument saves the same report to a text file.
