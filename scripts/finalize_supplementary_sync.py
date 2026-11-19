# -*- coding: utf-8 -*-
"""Backward-compatible entry point for the current provenance finalizer."""
from finalize_provenance_zero import main

if __name__ == "__main__":
    raise SystemExit(main())
