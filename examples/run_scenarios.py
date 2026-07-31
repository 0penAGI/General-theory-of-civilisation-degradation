"""Пример: прогнать пять сценариев песочницы и вывести вердикт.

Запуск из корня репозитория (без установки):
    python examples/run_scenarios.py
или после установки пакета:
    app-sim
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from adaptive_pluralism_protocol import run_experiments

if __name__ == "__main__":
    run_experiments()
