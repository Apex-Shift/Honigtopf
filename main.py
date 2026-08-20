#!/usr/bin/env python3
"""Honigtopf v3 — Multi-service honeypot with advanced dashboard."""

from __future__ import annotations

import os


def main() -> None:
    os.makedirs("config/profiles", exist_ok=True)
    os.makedirs("config/templates", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    os.makedirs("reports", exist_ok=True)

    from src.gui import HonigtopfGUI

    app = HonigtopfGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
