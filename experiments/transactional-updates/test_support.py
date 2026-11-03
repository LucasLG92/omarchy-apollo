# SPDX-License-Identifier: MIT
"""Small synthetic root-owned fixtures. No phone or live package operations."""
from pathlib import Path
import os, tempfile

if os.geteuid() != 0:
    raise SystemExit("Run in a disposable Linux container as root; see README.md")
_workspace = tempfile.TemporaryDirectory(prefix='apollo-public-test-', dir='/var/lib')
TEST_BASE = Path(_workspace.name)
_bootstrap = None

def bootstrap_parent():
    global _bootstrap
    parent = Path('/var/cache/pacman')
    parent.mkdir(parents=True, exist_ok=True)
    _bootstrap = tempfile.TemporaryDirectory(prefix='apollo-public-test-', dir=parent)
    return Path(_bootstrap.name)
