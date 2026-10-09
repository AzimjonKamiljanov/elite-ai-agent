from datetime import datetime

from life.models import ClassSchedule, DayOfWeek
from life.storage import LifeStorage


class SmartScheduler:
    """Aqlli dars jadvali va monitoring tizimi."""

    def __init__(self):
        self.storage = LifeStorage()
        self._schedule: list[ClassSchedule] = []
        self._load_schedule()

    # === Jadval Boshqaruvi ===

    def _load_schedule(self) -> None:
        """Jadvallarni saqlashdan yuklash."""
        data = self.storage.load_schedule()
        self._schedule = [ClassSchedule(**item) for item in data]

    def _save_schedule(self) -> None:
        """Jadvallarni saqlash."""
        self.storage.save_schedule([item.model_dump() for item in self._schedule])

    def add_class(
        self,
        name: str,
        day: str,
        start_time: str,
        end_time: str,
        location: str = "",
        teacher: str = "",
    ) -> ClassSchedule:
        """Yangi dars qo'shish."""
        cls = ClassSchedule(
            name=name,
            day=DayOfWeek(day.lower()),
            start_time=start_time,
            end_time=end_time,
            location=location,
            teacher=teacher,
        )
        self._schedule.append(cls)
        self._save_schedule()
        return cls

    def remove_class(self, class_id: str) -> bool:
        """Darsni o'chirish."""
        before = len(self._schedule)
        self._schedule = [c for c in self._schedule if c.id != class_id]
        if len(self._schedule) < before:
            self._save_schedule()
            return True
        return False

    def update_class(self, class_id: str, **kwargs) -> ClassSchedule | None:
        """Darsni yangilash."""
        for i, cls in enumerate(self._schedule):
            if cls.id == class_id:
                data = cls.model_dump()
                data.update(kwargs)
                updated = ClassSchedule(**data)
                self._schedule[i] = updated
                self._save_schedule()
                return updated
        return None

    def get_schedule(self, day: str | None = None) -> list[ClassSchedule]:
        """Jadval olish. day=None bo'lsa bugungi jadval."""
        target_day = day.lower() if day else self._get_today_day_name()
        return sorted(
            [c for c in self._schedule if c.day.value == target_day],
            key=lambda c: self._time_str_to_minutes(c.start_time),
        )

    def get_weekly_schedule(self) -> dict[str, list[ClassSchedule]]:
        """Haftalik jadval."""
        result: dict[str, list[ClassSchedule]] = {}
        for day in DayOfWeek:
            result[day.value] = sorted(
                [c for c in self._schedule if c.day == day],
                key=lambda c: self._time_str_to_minutes(c.start_time),
            )
        return result

    # === Real-Time Monitoring ===

    def get_today_classes(self) -> list[ClassSchedule]:
        """Bugungi darslar ro'yxati, vaqt bo'yicha tartiblangan."""
        return self.get_schedule()

    def get_current_class(self) -> ClassSchedule | None:
        """Hozir davom etayotgan dars (agar bor bo'lsa)."""
        now = self._current_minutes()
        for cls in self.get_today_classes():
            start = self._time_str_to_minutes(cls.start_time)
            end = self._time_str_to_minutes(cls.end_time)
            if start <= now < end:
                return cls
        return None

    def get_next_class(self) -> tuple[ClassSchedule | None, int]:
        """Keyingi dars va unga qolgan daqiqalar.

        Returns:
            (class, minutes_until) yoki (None, -1)
        """
        now = self._current_minutes()
        for cls in self.get_today_classes():
            start = self._time_str_to_minutes(cls.start_time)
            if start > now:
                return cls, start - now
        return None, -1

    def get_classes_needing_alert(self, minutes_before: int = 15) -> list[ClassSchedule]:
        """Berilgan daqiqa ichida boshlanadigan darslar."""
        now = self._current_minutes()
        result = []
        for cls in self.get_today_classes():
            start = self._time_str_to_minutes(cls.start_time)
            if 0 < start - now <= minutes_before:
                result.append(cls)
        return result

    def get_just_ended_classes(self, minutes_ago: int = 5) -> list[ClassSchedule]:
        """Yaqinda tugagan darslar (homework so'rash uchun)."""
        now = self._current_minutes()
        result = []
        for cls in self.get_today_classes():
            end = self._time_str_to_minutes(cls.end_time)
            if 0 < now - end <= minutes_ago:
                result.append(cls)
        return result

    def get_status_summary(self) -> dict:
        """Bugungi holat xulosasi."""
        today = self.get_today_classes()
        now = self._current_minutes()
        completed = [
            c for c in today if self._time_str_to_minutes(c.end_time) < now
        ]
        current = self.get_current_class()
        next_cls, next_in = self.get_next_class()
        remaining = [
            c for c in today if self._time_str_to_minutes(c.start_time) > now
        ]
        return {
            "today_total": len(today),
            "completed": len(completed),
            "current": current.name if current else None,
            "next": next_cls.name if next_cls else None,
            "next_in_minutes": next_in,
            "remaining": len(remaining),
        }

    # === Yordamchi ===

    def find_class_by_prefix(self, id_prefix: str) -> ClassSchedule | None:
        """ID prefiksi bo'yicha darsni topish."""
        for cls in self._schedule:
            if cls.id.startswith(id_prefix):
                return cls
        return None

    def _get_today_day_name(self) -> str:
        """Bugungi hafta kunini qaytarish: 'monday', 'tuesday', ..."""
        return datetime.now().strftime("%A").lower()

    def _time_str_to_minutes(self, time_str: str) -> int:
        """'09:30' -> 570 daqiqa."""
        try:
            hours, minutes = map(int, time_str.split(":"))
            return hours * 60 + minutes
        except (ValueError, AttributeError):
            return 0

    def _current_minutes(self) -> int:
        """Hozirgi vaqtni daqiqalarda qaytarish."""
        now = datetime.now()
        return now.hour * 60 + now.minute
