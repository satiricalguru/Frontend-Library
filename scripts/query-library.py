#!/usr/bin/env python3
"""Convenient repository entry point for the portable skill's offline search."""
import runpy
from pathlib import Path

runpy.run_path(str(Path(__file__).resolve().parent.parent / ".agents/skills/frontend-library/scripts/query.py"), run_name="__main__")
