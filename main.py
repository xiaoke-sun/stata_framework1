#!/usr/bin/env python3
"""
Main entry point for the spatial data processing framework.
"""

import sys
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.cli import main

if __name__ == "__main__":
    main()