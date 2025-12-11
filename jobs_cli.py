#!/usr/bin/env python3
"""
Entry point script for the jobapp CLI.

This script exists so that your `jobapp` symlink can point to a stable,
minimal wrapper, while the actual logic lives in the `jobapp` package.
"""

from jobapp.cli import main

if __name__ == "__main__":
    main()
