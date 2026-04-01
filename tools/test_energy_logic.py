import sys
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.append(os.getcwd())

import core.energy_tracker
from core.energy_tracker import EnergyTracker

def test_logic():
    # Mocking _TASHKENT_TZ and current time for deterministic tests
    _TASHKENT_TZ = timezone(timedelta(hours=5))
    fixed_now = datetime(2025, 5, 20, 12, 0, 0, tzinfo=_TASHKENT_TZ)

    # We need to mock datetime.now within core.energy_tracker if we want full control
    # But let's just mock the helper functions
    core.energy_tracker._today_str = lambda: "2025-05-20"
    # detect_burnout_risk uses datetime.now(_TASHKENT_TZ) directly.
    # We might need to mock that too.

    class MockDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed_now

    core.energy_tracker.datetime = MockDatetime

    tracker = EnergyTracker()
    # Past 3 days (19, 18, 17) have level 2
    tracker._records = [
        {"date": "2025-05-19", "level": 2},
        {"date": "2025-05-18", "level": 2},
        {"date": "2025-05-17", "level": 2},
        {"date": "2025-05-20", "level": 4, "label": "Yaxshi 😊", "note": "All good"}
    ]

    report = tracker.format_report()
    print("--- REPORT START ---")
    print(report)
    print("--- REPORT END ---")

    assert "Burnout xavfi aniqlandi!" in report
    assert "Burnout xavfi: bir necha kun dam oling!" in report
    assert "Bugun: 4/5" in report
    print("Logic test passed!")

if __name__ == "__main__":
    test_logic()
