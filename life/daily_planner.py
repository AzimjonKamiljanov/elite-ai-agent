from datetime import datetime

from life.homework import HomeworkManager
from life.models import DailyPlan
from life.scheduler import SmartScheduler
from life.storage import LifeStorage

_END_OF_DAY_TIME = "22:00"  # Kun oxiri vaqti (dam olish hisobi uchun)
_DAILY_PLAN_MAX_TASKS = 5   # Kundalik rejaga kiritilgan maksimal vazifalar soni


class DailyPlanner:
    """Aqlli kundalik reja generatori."""

    def __init__(self):
        self.scheduler = SmartScheduler()
        self.homework_mgr = HomeworkManager()
        self.storage = LifeStorage()

    def generate_daily_plan(self, wake_up: str = "07:00") -> DailyPlan:
        """Bugungi kun uchun optimal reja yaratish.

        Logika:
        1. Bugungi darslarni olish
        2. Bajarilmagan homework/tasks olish
        3. Darslar orasidagi bo'sh vaqtlarni aniqlash
        4. Study blocks yaratish (bo'sh vaqtlarda)
        5. Dam olish vaqtlarini qo'shish (har 90 daqiqada 15 daqiqa)
        6. Kundalik rejani qaytarish
        """
        today = datetime.now().strftime("%Y-%m-%d")
        today_classes = self.scheduler.get_today_classes()
        pending = self.homework_mgr.get_all_pending()

        classes_data = [c.model_dump() for c in today_classes]
        # Top _DAILY_PLAN_MAX_TASKS pending items are included to keep the daily plan concise
        tasks_data = [
            {"type": item["type"], **item["item"].model_dump()}
            for item in pending[:_DAILY_PLAN_MAX_TASKS]
        ]

        free_slots = self._find_free_slots(
            [{"start": c.start_time, "end": c.end_time} for c in today_classes]
        )

        study_blocks: list[dict] = []
        pending_copy = list(pending)
        for slot_start, slot_end in free_slots:
            suggestion = ""
            if pending_copy:
                top = pending_copy.pop(0)
                item = top["item"]
                if top["type"] == "homework":
                    suggestion = f"{item.subject} uy vazifasi"
                else:
                    suggestion = item.title
            study_blocks.append(
                {"start": slot_start, "end": slot_end, "suggestion": suggestion}
            )

        breaks: list[dict] = []
        start_min = self._time_str_to_minutes(wake_up)
        last_break = start_min
        interval = 90
        break_dur = 15
        end_of_day = self._time_str_to_minutes(_END_OF_DAY_TIME)
        while last_break + interval < end_of_day:
            break_start_min = last_break + interval
            break_end_min = break_start_min + break_dur
            breaks.append(
                {
                    "start": self._minutes_to_time_str(break_start_min),
                    "end": self._minutes_to_time_str(break_end_min),
                    "type": "dam olish",
                }
            )
            last_break = break_end_min

        plan = DailyPlan(
            date=today,
            wake_up_time=wake_up,
            classes=classes_data,
            study_blocks=study_blocks,
            tasks=tasks_data,
            breaks=breaks,
        )
        self.storage.save_daily_plan(plan.model_dump())
        return plan

    def get_morning_briefing(self) -> str:
        """Ertalabki xulosa matni."""
        today_str = datetime.now().strftime("%Y-%m-%d")
        day_name_uz = self._day_name_uz(datetime.now().strftime("%A").lower())

        today_classes = self.scheduler.get_today_classes()
        pending_count = len(self.homework_mgr.get_pending_homework())
        due_today = self.homework_mgr.get_due_today()

        lines = [f"🌅 Xayrli tong! Bugun {today_str}, {day_name_uz}.\n"]

        if today_classes:
            lines.append(f"📅 Bugun {len(today_classes)} ta darsingiz bor:")
            for c in today_classes:
                loc_info = f" ({c.location})" if c.location else ""
                lines.append(f"  {c.start_time}-{c.end_time} — {c.name}{loc_info}")
        else:
            lines.append("📅 Bugun dars yo'q.")

        lines.append("")
        lines.append(f"📝 Bajarilmagan vazifalar: {pending_count}")
        if due_today:
            lines.append(f"  ⚠️ {len(due_today)} ta vazifa bugun muddati tugaydi!")

        study_blocks = self.suggest_study_blocks()
        if study_blocks:
            first = study_blocks[0]
            lines.append("")
            suggestion_text = first["suggestion"] or "o'qishni"
            lines.append(
                f"💡 Tavsiya: Darslar orasida {first['start']}-{first['end']} da "
                f"{suggestion_text} bajaring."
            )

        return "\n".join(lines)

    def get_end_of_day_summary(self) -> str:
        """Kun oxiri xulosasi."""
        today_str = datetime.now().strftime("%Y-%m-%d")
        today_classes = self.scheduler.get_today_classes()
        stats = self.homework_mgr.get_stats()
        due_tomorrow = self.homework_mgr.get_due_tomorrow()

        lines = [f"📊 Kunlik xulosa — {today_str}\n"]
        lines.append(f"✅ O'tilgan darslar: {len(today_classes)}/{len(today_classes)}")
        lines.append(f"📝 Yangi uy vazifalari: {stats['pending_homework']}")
        lines.append(f"✅ Bajarilgan vazifalar: {stats['completed_homework'] + stats['completed_tasks']}")
        lines.append(f"⏳ Qolgan vazifalar: {stats['pending_homework'] + (stats['total_tasks'] - stats['completed_tasks'])}")

        if due_tomorrow:
            lines.append("\n📚 Ertaga tayyorlanish kerak:")
            for hw in due_tomorrow:
                lines.append(f"  - {hw.subject}: {hw.description} (muddati: ertaga)")

        lines.append("\n💪 Yaxshi ish! Ertaga ham shunday davom eting!")
        return "\n".join(lines)

    def suggest_study_blocks(self) -> list[dict]:
        """Darslar orasidagi bo'sh vaqtlarda o'qish bloklarini taklif qilish.

        Returns:
            [{"start": "10:30", "end": "11:00", "suggestion": "Matematika uy vazifasi"}]
        """
        today_classes = self.scheduler.get_today_classes()
        slots = self._find_free_slots(
            [{"start": c.start_time, "end": c.end_time} for c in today_classes]
        )
        pending = self.homework_mgr.get_all_pending()
        result = []
        for i, (slot_start, slot_end) in enumerate(slots):
            suggestion = ""
            if i < len(pending):
                item = pending[i]["item"]
                if pending[i]["type"] == "homework":
                    suggestion = f"{item.subject} uy vazifasi"
                else:
                    suggestion = item.title
            result.append({"start": slot_start, "end": slot_end, "suggestion": suggestion})
        return result

    def _find_free_slots(
        self, classes: list[dict], min_duration: int = 30
    ) -> list[tuple[str, str]]:
        """Darslar orasidagi bo'sh vaqtlarni topish (min 30 daqiqa)."""
        if not classes:
            return []

        sorted_classes = sorted(classes, key=lambda c: self._time_str_to_minutes(c["start"]))
        slots: list[tuple[str, str]] = []

        for i in range(len(sorted_classes) - 1):
            end_prev = self._time_str_to_minutes(sorted_classes[i]["end"])
            start_next = self._time_str_to_minutes(sorted_classes[i + 1]["start"])
            gap = start_next - end_prev
            if gap >= min_duration:
                slots.append(
                    (
                        self._minutes_to_time_str(end_prev),
                        self._minutes_to_time_str(start_next),
                    )
                )
        return slots

    def _time_str_to_minutes(self, time_str: str) -> int:
        """'09:30' -> 570."""
        try:
            hours, minutes = map(int, time_str.split(":"))
            return hours * 60 + minutes
        except (ValueError, AttributeError):
            return 0

    def _minutes_to_time_str(self, minutes: int) -> str:
        """570 -> '09:30'."""
        h = minutes // 60
        m = minutes % 60
        return f"{h:02d}:{m:02d}"

    def _day_name_uz(self, day_en: str) -> str:
        """Inglizcha hafta kunini o'zbekchaga o'girish."""
        mapping = {
            "monday": "Dushanba",
            "tuesday": "Seshanba",
            "wednesday": "Chorshanba",
            "thursday": "Payshanba",
            "friday": "Juma",
            "saturday": "Shanba",
            "sunday": "Yakshanba",
        }
        return mapping.get(day_en, day_en.capitalize())
