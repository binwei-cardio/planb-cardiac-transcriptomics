# -*- coding: utf-8 -*-
"""Portable project paths for Plan B scripts.

Override with PLANB_ROOT when the repository is moved. PLANB_PROJECT_ROOT is the
parent directory containing the PlanB_Repro_v1 folder.
"""
from pathlib import Path
import os

SCRIPTS_DIR = Path(__file__).resolve().parent
PLANB_ROOT = Path(os.environ.get("PLANB_ROOT", str(SCRIPTS_DIR.parent))).resolve()
PROJECT_ROOT = Path(
    os.environ.get("PLANB_PROJECT_ROOT", str(PLANB_ROOT.parent))
).resolve()
