#!/usr/bin/env python3
"""Honigtopf v2 — Multi-service IoT / server honeypot framework."""

from __future__ import annotations

import os
import sys


def ensure_dirs() -> None:
    os.makedirs("config/profiles", exist_ok=True)
    os.makedirs("config/templates", exist_ok=True)
    os.makedirs("logs", exist_ok=True)


def main() -> None:
    ensure_dirs()
    from src.gui import HonigtopfGUI

    app = HonigtopfGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
