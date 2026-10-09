"""
JARVIS Smart Calendar System.
Haftalik eventlar, takrorlanuvchi jadvallar, conflict detection.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

_CALENDAR_FILE = Path("data/calendar.json")
_DEFAULT_EVENT_DURATION = 100  # Default duration in HHMM units (1 hour)


class CalendarEvent:
    """Kalendar event modeli."""

    def __init__(
        self,
        title: str,
        day: str,
        time: str,
        end_time: str = "",
        recurring: bool = False,
        event_type: str = "general",
        event_id: str = "",
    ) -> None:
        self.id = event_id or self._gen_id()
        self.title = title
        self.day = day  # monday, tuesday, ...
        self.time = time  # HH:MM
        self.end_time = end_time  # HH:MM
        self.recurring = recurring  # Har hafta takrorlanadi
        self.event_type = event_type  # "class", "meeting", "task", "general"

    @staticmethod
    def _gen_id() -> str:
        from uuid import uuid4
        return str(uuid4())[:8]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "day": self.day,
            "time": self.time,
            "end_time": self.end_time,
            "recurring": self.recurring,
            "event_type": self.event_type,
        }

    @classmethod
    def from_dict(cls, data: dict) -> CalendarEvent:
        return cls(
            title=data["title"],
            day=data["day"],
            time=data["time"],
            end_time=data.get("end_time", ""),
            recurring=data.get("recurring", False),
            event_type=data.get("event_type", "general"),
            event_id=data.get("id", ""),
        )


class CalendarSystem:
    """Aqlli kalendar tizimi."""

    def __init__(self) -> None:
        self._events: list[CalendarEvent] = []
        self._load()

    def _load(self) -> None:
        """Eventlarni yuklash."""
        os.makedirs("data", exist_ok=True)
        if _CALENDAR_FILE.exists():
            try:
                data = json.loads(_CALENDAR_FILE.read_text(encoding="utf-8"))
                self._events = [CalendarEvent.from_dict(e) for e in data]
            except (json.JSONDecodeError, KeyError):
                self._events = []

    def _save(self) -> None:
        """Eventlarni saqlash."""
        os.makedirs("data", exist_ok=True)
        data = [e.to_dict() for e in self._events]
        _CALENDAR_FILE.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def add_event(
        self,
        title: str,
        day: str,
        time: str,
        end_time: str = "",
        recurring: bool = False,
        event_type: str = "general",
    ) -> CalendarEvent:
        """
        Event qo'shish.
        Agar conflict bo'lsa — ogohlantirish qaytarish.
        Agar duplicate bo'lsa — qo'shmaslik.
        """
        # Duplicate check
        for e in self._events:
            if e.title.lower() == title.lower() and e.day == day and e.time == time:
                raise ValueError(f"Bu event allaqachon mavjud: {title} ({day} {time})")

        # Conflict check (return value available for callers)
        self.check_conflicts(day, time, end_time)

        event = CalendarEvent(title, day, time, end_time, recurring, event_type)
        self._events.append(event)
        self._save()
        return event

    def check_conflicts(
        self, day: str, start_time: str, end_time: str = ""
    ) -> list[CalendarEvent]:
        """Vaqt to'qnashuvini tekshirish."""
        conflicts = []
        for e in self._events:
            if e.day != day:
                continue
            # Vaqt overlap tekshirish
            if self._times_overlap(
                start_time, end_time or start_time, e.time, e.end_time or e.time
            ):
                conflicts.append(e)
        return conflicts

    @staticmethod
    def _times_overlap(s1: str, e1: str, s2: str, e2: str) -> bool:
        """Ikki vaqt oralig'i overlap qiladimi?"""
        try:
            start1 = int(s1.replace(":", ""))
            end1 = int(e1.replace(":", "")) if e1 else start1 + _DEFAULT_EVENT_DURATION
            start2 = int(s2.replace(":", ""))
            end2 = int(e2.replace(":", "")) if e2 else start2 + _DEFAULT_EVENT_DURATION
            return start1 < end2 and start2 < end1
        except (ValueError, AttributeError):
            return False

    def get_day_events(self, day: str) -> list[CalendarEvent]:
        """Berilgan kunning eventlari (vaqt bo'yicha tartiblangan)."""
        events = [e for e in self._events if e.day == day.lower()]
        return sorted(events, key=lambda e: e.time)

    def get_today_events(self) -> list[CalendarEvent]:
        """Bugungi eventlar."""
        today = datetime.now().strftime("%A").lower()
        return self.get_day_events(today)

    def get_weekly_view(self) -> dict[str, list[CalendarEvent]]:
        """
        Haftalik kalendar ko'rinishi.

        Returns:
            {"monday": [...], "tuesday": [...], ...}
        """
        days = [
            "monday", "tuesday", "wednesday", "thursday",
            "friday", "saturday", "sunday",
        ]
        return {day: self.get_day_events(day) for day in days}

    def format_weekly_view(self) -> str:
        """
        Chiroyli haftalik ko'rinish::

            📅 HAFTALIK KALENDAR
            ──────────────────────────────
            DUSHANBA
              09:00 Matematika darsi
              14:00 Do'stim bilan uchrashuv

            SESHANBA
              10:00 Fizika darsi
        """
        day_names = {
            "monday": "DUSHANBA",
            "tuesday": "SESHANBA",
            "wednesday": "CHORSHANBA",
            "thursday": "PAYSHANBA",
            "friday": "JUMA",
            "saturday": "SHANBA",
            "sunday": "YAKSHANBA",
        }
        weekly = self.get_weekly_view()
        lines: list[str] = ["📅 HAFTALIK KALENDAR", "─" * 30]
        for day, events in weekly.items():
            lines.append(f"\n{day_names[day]}")
            if events:
                for e in events:
                    end_str = f"-{e.end_time}" if e.end_time else ""
                    recurring_str = " 🔄" if e.recurring else ""
                    lines.append(f"  {e.time}{end_str} {e.title}{recurring_str}")
            else:
                lines.append("  — bo'sh —")
        return "\n".join(lines)

    def format_today_view(self) -> str:
        """Bugungi eventlarni formatlash."""
        events = self.get_today_events()
        today_name = datetime.now().strftime("%A").upper()
        if not events:
            return f"📅 {today_name} — bugun event yo'q"
        lines = [f"📅 {today_name}"]
        for e in events:
            end_str = f"-{e.end_time}" if e.end_time else ""
            lines.append(f"  {e.time}{end_str} {e.title}")
        return "\n".join(lines)

    def remove_event(self, event_id: str) -> bool:
        """Event o'chirish."""
        for i, e in enumerate(self._events):
            if e.id == event_id or e.id.startswith(event_id):
                self._events.pop(i)
                self._save()
                return True
        return False

    def get_upcoming_events(self, minutes: int = 15) -> list[CalendarEvent]:
        """Yaqin ``minutes`` daqiqa ichidagi eventlar (eslatma uchun)."""
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        today = now.strftime("%A").lower()

        upcoming = []
        for e in self._events:
            if e.day != today:
                continue
            try:
                event_hour, event_min = map(int, e.time.split(":"))
                curr_hour, curr_min = map(int, current_time.split(":"))
                diff = (event_hour * 60 + event_min) - (curr_hour * 60 + curr_min)
                if 0 < diff <= minutes:
                    upcoming.append(e)
            except (ValueError, AttributeError):
                continue
        return upcoming
