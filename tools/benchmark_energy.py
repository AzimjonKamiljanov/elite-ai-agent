import time
import sys
import os
from pathlib import Path

# Add the current directory to sys.path to import core
sys.path.append(os.getcwd())

from core.energy_tracker import EnergyTracker

def setup_data(num_records=1000):
    tracker = EnergyTracker()
    tracker._records = []
    from datetime import datetime, timedelta, timezone
    _TASHKENT_TZ = timezone(timedelta(hours=5))
    now = datetime.now(_TASHKENT_TZ)

    for i in range(num_records):
        date_str = (now - timedelta(days=i)).strftime("%Y-%m-%d")
        tracker._records.append({
            "date": date_str,
            "level": 2 if i < 5 else 4,
            "label": "Test",
            "note": "Test note"
        })
    return tracker

def benchmark():
    tracker = setup_data(10000)

    start_time = time.perf_counter()
    for _ in range(1000):
        report = tracker.format_report()
    end_time = time.perf_counter()

    print(f"Time taken for 1000 format_report calls: {end_time - start_time:.4f} seconds")

if __name__ == "__main__":
    benchmark()
