from datetime import datetime, timedelta

from life.daily_planner import DailyPlanner
from life.homework import HomeworkManager
from life.scheduler import SmartScheduler


class ReminderEngine:
    """Proaktiv eslatmalar tizimi."""

    def __init__(self):
        self.scheduler = SmartScheduler()
        self.homework_mgr = HomeworkManager()
        self.planner = DailyPlanner()

    def check_all(self) -> list[dict]:
        """Barcha eslatmalarni tekshirish va ro'yxatini qaytarish.

        Har bir eslatma formati::

            {
                "type": "pre_class" | "post_class" | "homework_due" |
                        "study_reminder" | "deadline_warning",
                "priority": "low" | "medium" | "high" | "urgent",
                "message": str,
                "action_required": bool,
                "data": dict
            }
        """
        reminders: list[dict] = []
        reminders.extend(self.check_pre_class_alerts())
        reminders.extend(self.check_post_class_prompts())
        reminders.extend(self.check_homework_deadlines())
        reminders.extend(self.check_overdue_tasks())
        reminders.extend(self.check_study_reminders())
        return reminders

    def check_pre_class_alerts(self) -> list[dict]:
        """15 daqiqa ichida boshlanadigan darslar uchun eslatma."""
        upcoming = self.scheduler.get_classes_needing_alert(minutes_before=15)
        reminders = []
        for cls in upcoming:
            loc_info = f" ({cls.location})" if cls.location else ""
            reminders.append(
                {
                    "type": "pre_class",
                    "priority": "high",
                    "message": (
                        f"⏰ {cls.name} darsi 15 daqiqadan boshlanadi!{loc_info}"
                    ),
                    "action_required": True,
                    "data": {"class_id": cls.id, "class_name": cls.name},
                }
            )
        return reminders

    def check_post_class_prompts(self) -> list[dict]:
        """Yaqinda tugagan darslar uchun homework so'rash."""
        ended = self.scheduler.get_just_ended_classes(minutes_ago=5)
        reminders = []
        for cls in ended:
            reminders.append(
                {
                    "type": "post_class",
                    "priority": "medium",
                    "message": f"📚 {cls.name} darsi tugadi. Uy vazifasi bormi?",
                    "action_required": True,
                    "data": {"class_id": cls.id, "class_name": cls.name},
                }
            )
        return reminders

    def check_homework_deadlines(self) -> list[dict]:
        """Muddati yaqinlashayotgan vazifalar uchun ogohlantirish.

        - Bugun tugaydiganlar → urgent
        - Ertaga tugaydiganlar → high
        - 3 kun ichida → medium
        """
        today = datetime.now().strftime("%Y-%m-%d")
        in_3_days = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        pending = self.homework_mgr.get_pending_homework()
        reminders = []
        for hw in pending:
            # Only homework with an explicit deadline can have deadline-based reminders
            if not hw.deadline:
                continue
            if hw.deadline == today:
                priority = "urgent"
                msg = f"🚨 {hw.subject}: '{hw.description}' — BUGUN muddati tugaydi!"
            elif hw.deadline == tomorrow:
                priority = "high"
                msg = f"⚠️ {hw.subject}: '{hw.description}' — ertaga muddati tugaydi."
            elif hw.deadline <= in_3_days:
                priority = "medium"
                msg = f"📅 {hw.subject}: '{hw.description}' — 3 kun ichida muddati tugaydi."
            else:
                continue
            reminders.append(
                {
                    "type": "homework_due",
                    "priority": priority,
                    "message": msg,
                    "action_required": priority in ("urgent", "high"),
                    "data": {"homework_id": hw.id, "subject": hw.subject},
                }
            )
        return reminders

    def check_overdue_tasks(self) -> list[dict]:
        """Muddati o'tgan vazifalar uchun eslatma."""
        overdue = self.homework_mgr.get_overdue_homework()
        reminders = []
        for hw in overdue:
            reminders.append(
                {
                    "type": "deadline_warning",
                    "priority": "urgent",
                    "message": (
                        f"⚠️ {hw.subject}: '{hw.description}' muddati o'tgan! "
                        "Zudlik bilan bajaring."
                    ),
                    "action_required": True,
                    "data": {"homework_id": hw.id, "subject": hw.subject},
                }
            )
        return reminders

    def check_study_reminders(self) -> list[dict]:
        """Barcha darslar tugagandan keyin o'qishni eslatish."""
        summary = self.scheduler.get_status_summary()
        if summary["remaining"] == 0 and summary["today_total"] > 0:
            pending_count = len(self.homework_mgr.get_pending_homework())
            if pending_count > 0:
                return [
                    {
                        "type": "study_reminder",
                        "priority": "medium",
                        "message": (
                            f"📖 Barcha darslar tugadi. {pending_count} ta uy vazifangiz "
                            "bor. O'qishni boshlang!"
                        ),
                        "action_required": False,
                        "data": {"pending_count": pending_count},
                    }
                ]
        return []

    def format_notifications(self, reminders: list[dict]) -> str:
        """Eslatmalarni chiroyli matn formatiga o'girish."""
        if not reminders:
            return "✅ Hozircha eslatmalar yo'q."

        priority_order = {"urgent": 0, "high": 1, "medium": 2, "low": 3}
        sorted_reminders = sorted(
            reminders, key=lambda r: priority_order.get(r["priority"], 4)
        )

        lines = []
        for r in sorted_reminders:
            lines.append(r["message"])
        return "\n".join(lines)
