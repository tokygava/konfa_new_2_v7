#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Точка входа для CLI без установки пакета."""
import os, sys
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(THIS_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)
from depviz.cli import main

if __name__ == "__main__":
    main()
