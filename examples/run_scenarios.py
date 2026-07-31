"""Example: run the five sandbox scenarios and print the verdict.

Run from the repository root (without installation):
    python examples/run_scenarios.py
or after installing the package:
    app-sim
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from adaptive_pluralism_protocol import run_experiments

if __name__ == "__main__":
    run_experiments()
