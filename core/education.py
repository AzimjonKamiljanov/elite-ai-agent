"""
Smart Education System — Dars monitoring, homework AI, study tracking.
"""

from __future__ import annotations

import time
from datetime import datetime


class SmartEducation:
    """Aqlli ta'lim tizimi — dars monitoring va homework yordamchi."""

    def __init__(self) -> None:
        self._class_alert_minutes: int = 15
        self._study_sessions: list[dict] = []
        self._focus_start: float | None = None
        self._focus_duration: int = 25

    # === Class Monitoring ===

    def check_upcoming_class(self, scheduler) -> str | None:
        """Yaqinlashayotgan darsni tekshirish va ogohlantirish."""
        try:
            classes = scheduler.get_schedule()
            if not classes:
                return None
            now = datetime.now()
            for cls in classes:
                try:
                    class_time = datetime.strptime(
                        f"{now.strftime('%Y-%m-%d')} {cls.start_time}", "%Y-%m-%d %H:%M"
                    )
                    diff = (class_time - now).total_seconds() / 60
                    if 0 < diff <= self._class_alert_minutes:
                        return (
                            f"⏰ {cls.name} darsi {int(diff)} daqiqada boshlanadi!\n"
                            f"📍 Xona: {cls.location or 'Noma\u02bclum'}\n"
                            f"👨‍🏫 O\u02bcqituvchi: {cls.teacher or 'Noma\u02bclum'}"
                        )
                except (ValueError, AttributeError):
                    continue
        except Exception:
            pass
        return None

    def post_class_prompt(self, class_name: str) -> str:
        """Darsdan keyin homework so'rash."""
        return (
            f"📚 {class_name} darsi tugadi!\n"
            f"📝 Bu dars uchun uy vazifasi bormi?\n"
            f"Agar bor bo\u02bcsa, yozing va men uni saqlayaman."
        )

    # === Study Session Tracking ===

    def start_study_session(self, subject: str) -> str:
        """O'qish sessiyasini boshlash."""
        session = {
            "subject": subject,
            "start": time.time(),
            "end": None,
        }
        self._study_sessions.append(session)
        return f"📖 {subject} bo\u02bcyicha o\u02bcqish sessiyasi boshlandi! Muvaffaqiyat!"

    def end_study_session(self) -> str:
        """O'qish sessiyasini tugatish."""
        if not self._study_sessions or self._study_sessions[-1]["end"] is not None:
            return "⚠️ Faol o\u02bcqish sessiyasi yo\u02bcq."
        session = self._study_sessions[-1]
        session["end"] = time.time()
        duration = (session["end"] - session["start"]) / 60
        return (
            f"✅ O\u02bcqish sessiyasi tugadi!\n"
            f"📚 Fan: {session['subject']}\n"
            f"⏱ Davomiyligi: {int(duration)} daqiqa\n"
            f"💪 Yaxshi ish!"
        )

    def get_study_stats(self) -> dict:
        """O'qish statistikasini olish."""
        total_minutes = 0.0
        subject_minutes: dict[str, float] = {}
        for session in self._study_sessions:
            if session["end"]:
                duration = (session["end"] - session["start"]) / 60
                total_minutes += duration
                subj = session["subject"]
                subject_minutes[subj] = subject_minutes.get(subj, 0) + duration
        return {
            "total_sessions": len([s for s in self._study_sessions if s["end"]]),
            "total_minutes": round(total_minutes, 1),
            "total_hours": round(total_minutes / 60, 1),
            "by_subject": {k: round(v, 1) for k, v in subject_minutes.items()},
        }

    # === Focus Mode / Pomodoro ===

    def start_focus(self, minutes: int = 25) -> str:
        """Pomodoro / Focus sessiyani boshlash."""
        self._focus_start = time.time()
        self._focus_duration = minutes
        return (
            f"🔥 Focus mode yoqildi! {minutes} daqiqa.\n"
            f"🍅 Pomodoro taymer boshlandi.\n"
            f"📵 Distraksiyalarni bloklang!"
        )

    def check_focus(self) -> str | None:
        """Focus timer holatini tekshirish."""
        if self._focus_start is None:
            return None
        elapsed = (time.time() - self._focus_start) / 60
        remaining = self._focus_duration - elapsed
        if remaining <= 0:
            self._focus_start = None
            return (
                "🍅 Pomodoro tugadi! Yaxshi ish!\n"
                "☕ 5 daqiqa dam oling.\n"
                "Yana davom etasizmi? /focus"
            )
        return f"🔥 Focus: {int(remaining)} daqiqa qoldi"

    def end_focus(self) -> str:
        """Focus mode ni tugatish."""
        if self._focus_start is None:
            return "⚠️ Focus mode yoqilmagan."
        elapsed = (time.time() - self._focus_start) / 60
        self._focus_start = None
        return f"✅ Focus mode tugadi! {int(elapsed)} daqiqa ishlagan edingiz."

    # === Stress / Overload Detection ===

    def check_overload(self, homework_mgr) -> str | None:
        """Ish yukini tekshirish va ogohlantirish."""
        try:
            stats = homework_mgr.get_stats()
            pending = stats.get("pending_homework", 0) + stats.get("pending_tasks", 0)
            overdue = stats.get("overdue_homework", 0)

            if overdue > 2:
                return (
                    f"🚨 Sizda {overdue} ta muddati o\u02bcgan vazifa bor!\n"
                    f"Birinchi ularni hal qilish kerak."
                )
            if pending > 5:
                return (
                    f"⚠️ Sizda {pending} ta bajarilmagan vazifa bor.\n"
                    f"20 daqiqa dam oling va keyin eng muhimidan boshlang."
                )
        except Exception:
            pass
        return None

    # === Homework AI Help ===

    def homework_help_prompt(self, subject: str, description: str) -> str:
        """Uy vazifasi bo'yicha yordam so'rash uchun prompt."""
        return (
            f"Help me with this homework:\n"
            f"Subject: {subject}\n"
            f"Task: {description}\n\n"
            f"Please provide:\n"
            f"1. Clear explanation of the concept\n"
            f"2. Step-by-step solution approach\n"
            f"3. Example if applicable\n"
            f"4. Tips for similar problems"
        )
